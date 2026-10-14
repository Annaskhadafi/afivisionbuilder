"""Backend engine for the VisoNode desktop GUI.

This module reuses the inference / capture / drawing helpers that already live in
``main.py`` and wraps them in a callback-driven
workflow runner. Status, events, and debug payloads are forwarded to plain Python
callbacks. Preview frames can either be forwarded to the GUI or shown directly
from the worker process with OpenCV.

The callbacks are invoked from the runner's worker thread, so the GUI is
expected to marshal them onto the Qt thread (e.g. by passing bound Qt
``Signal.emit`` methods as the callbacks).
"""

from __future__ import annotations

import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import math
import copy
import re
import time
import json
import traceback
from collections import deque
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from graphlib import TopologicalSorter
from threading import Condition, Event, Lock, RLock, Thread
from typing import Callable
from pathlib import Path

import main as engine
from detector_process import DetectorProcessStopped, TensorRTDetectorProcess
from visonode_database import DatabaseWriter
from python_script_runtime import ScriptError, ScriptStopped, ScriptTimeout, PythonScriptRunner


_torch_thread_scope_lock = Lock()


def _dispatch_webhook_async(config: dict, detections: list[dict], frame=None) -> None:
    url = str(config.get("url") or "").strip()
    if not url:
        return
    import threading
    def _worker():
        try:
            import json, urllib.request, base64, time
            payload_template = str(config.get("payloadTemplate") or "").strip()
            if payload_template:
                best_det = detections[0] if detections else {}
                rendered = payload_template
                rendered = rendered.replace("{timestamp}", str(time.time()))
                rendered = rendered.replace("{matches}", str(len(detections)))
                rendered = rendered.replace("{detection.class}", str(best_det.get("class", "")))
                rendered = rendered.replace("{detection.confidence}", f"{float(best_det.get('score', 0)):.2f}")
                rendered = rendered.replace("{track.id}", str(best_det.get("trackId", "")))
                try:
                    payload = json.loads(rendered)
                except Exception:
                    payload = {"raw": rendered, "matches": len(detections)}
            else:
                payload = {
                    "event": "VISION_EVENT",
                    "timestamp": time.time(),
                    "matches": len(detections),
                    "detections": detections,
                }
            if config.get("sendImage", True) and frame is not None:
                try:
                    import cv2
                    quality = int(config.get("imageQuality", 80) or 80)
                    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                    payload["imageBase64"] = base64.b64encode(buf).decode("utf-8")
                except Exception:
                    pass
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            method = str(config.get("method") or "POST").upper()
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header("Content-Type", "application/json")
            custom_headers = str(config.get("customHeaders") or "")
            for line in custom_headers.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    req.add_header(k.strip(), v.strip())
            retries = int(config.get("retryCount", 2) or 2)
            timeout = float(config.get("timeoutSeconds", 5.0) or 5.0)
            for attempt in range(retries + 1):
                try:
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        if resp.status < 400:
                            break
                except Exception:
                    if attempt < retries:
                        time.sleep(0.5 * (2 ** attempt))
                    else:
                        pass
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True).start()


@contextmanager
def _torch_thread_scope(workflow):
    """Apply an explicit workflow CPU budget and restore the worker's setting."""
    config = (engine.active_input_node(workflow) or {}).get("config", {})
    requested = int(config.get("torchCpuThreads", 0) or 0)
    if requested == 0:
        requested = min(4, max(1, (os.cpu_count() or 4) // 2))
    if not 1 <= requested <= 64:
        raise ValueError("Torch CPU threads must be between 0 (automatic) and 64")
    import torch

    # Torch's setting belongs to the process. Serialize explicit scopes so an
    # older runner cannot restore its value over a newly started runner's value.
    with _torch_thread_scope_lock:
        previous = torch.get_num_threads()
        try:
            torch.set_num_threads(requested)
            yield
        finally:
            torch.set_num_threads(previous)


def _load_tensorrt_for_run(config, processes, stop_event):
    if not config.get("rfdetrTensorRTProcess", False):
        return engine.load_rfdetr_tensorrt(config)
    key = (str(engine.rfdetr_tensorrt_engine_path(config)),
           str(config.get("device", "auto")), bool(config.get("rfdetrTensorRTCudaGraph", False)))
    if key not in processes:
        processes[key] = TensorRTDetectorProcess(config, stop_event)
    return processes[key]


def _run_tensorrt_for_run(frames, node, processes, stop_event):
    config = node.get("config", {})
    if config.get("rfdetrTensorRTProcess", False):
        return _load_tensorrt_for_run(config, processes, stop_event).run_batch(frames, node)
    return engine.run_rfdetr_tensorrt_batch(frames, node)


def _close_detector_processes(processes):
    for process in processes.values():
        try:
            process.close()
        except Exception:
            # Continue closing the other children and normal workflow resources.
            traceback.print_exc()
    processes.clear()


def _presentation_capacity(input_config, *, is_static, drop_frames):
    if is_static:
        return 0
    if input_config.get("asyncPreview", False):
        return 1
    return 3 if drop_frames else 0


def _preview_display_due(preview, now, last_display_at):
    limit = max(0.0, float(preview.get("config", {}).get("maxPreviewFps", 0) or 0))
    preview_id = str(preview.get("id") or "")
    previous = last_display_at.get(preview_id)
    if limit and previous is not None and now - previous < 1.0 / limit:
        return False
    last_display_at[preview_id] = now
    return True

# Re-export the pieces the GUI needs so it only has to import from ``core``.
APP_VERSION = engine.APP_VERSION
VERSION_INFO = engine.VERSION_INFO
INPUT_NODE_ID = engine.INPUT_NODE_ID
RFDETR_DETECTION_MODELS = engine.RFDETR_DETECTION_MODELS
RFDETR_SEGMENTATION_MODELS = engine.RFDETR_SEGMENTATION_MODELS
SAM3_MODELS = engine.SAM3_MODELS
TRACKING_ALGORITHMS = engine.TRACKING_ALGORITHMS

git_version_info = engine.git_version_info
runtime_devices = engine.runtime_devices


LogCallback = Callable[[str], None]
EventCallback = Callable[[str, str], None]
StatusCallback = Callable[[dict], None]
FrameCallback = Callable[[str, object, bool], None]
NodeDebugCallback = Callable[[dict], None]


def _noop(*_args, **_kwargs) -> None:
    pass


def _eligible_crop_frame_indices(
    node: dict,
    detections_by_index: list[list[dict]],
    frames_seen_by_node: dict[str, int],
    last_inference_by_node: dict[str, float],
    now: float,
    *,
    schedule_id: str | None = None,
) -> list[int]:
    """Apply a crop inference node's cadence in both desktop execution modes."""
    node_id = schedule_id or str(node.get("id") or node.get("type") or "classifier")
    config = node.get("config", {})
    every = max(1, int(config.get("detectEveryNFrames", 1) or 1))
    max_fps = max(0.0, float(config.get("maxDetectionFps", 0) or 0))
    seen = frames_seen_by_node.get(node_id, 0)
    frames_seen_by_node[node_id] = seen + len(detections_by_index)
    last = last_inference_by_node.get(node_id)
    if max_fps and last is not None and now - last < 1.0 / max_fps:
        return []
    return [
        index for index, detections in enumerate(detections_by_index)
        if (seen + index) % every == 0 and detections
    ]


def _crop_schedule_id(crop_node: dict, inference_node: dict) -> str:
    # A node may inspect multiple crop branches in the same source frame.
    # Each binding needs its own clock so the first branch cannot throttle the rest.
    return json.dumps([crop_node.get("id"), inference_node.get("id")])


def _parse_per_class_thresholds(val) -> dict[str, float]:
    if isinstance(val, dict):
        return {str(k).strip().lower(): float(v) for k, v in val.items()}
    if not isinstance(val, str) or not val.strip():
        return {}
    res = {}
    for part in val.split(","):
        if ":" in part:
            k, v = part.split(":", 1)
            try:
                res[k.strip().lower()] = float(v.strip())
            except ValueError:
                pass
    return res


def _parse_class_remap(val) -> dict[str, str]:
    if isinstance(val, dict):
        return {str(k).strip().lower(): str(v).strip() for k, v in val.items()}
    if not isinstance(val, str) or not val.strip():
        return {}
    res = {}
    for part in val.split(","):
        sep = "->" if "->" in part else (":" if ":" in part else None)
        if sep:
            k, v = part.split(sep, 1)
            res[k.strip().lower()] = v.strip()
    return res


def _filter_and_remap_detections(
    node_detections: list[dict],
    default_threshold: float,
    tracking_threshold: float,
    is_tracking_eligible: bool,
    per_class_map: dict[str, float],
    class_remap_map: dict[str, str],
) -> tuple[list[dict], list[dict]]:
    kept = []
    tracking = []
    for raw_item in node_detections:
        if raw_item.get("kind") == "anomaly":
            kept.append(raw_item)
            continue
        c_label = str(raw_item.get("class", "")).strip().lower()
        req_thresh = per_class_map.get(c_label, default_threshold)
        score = float(raw_item.get("score", 0))

        item = raw_item
        if c_label in class_remap_map:
            item = dict(raw_item)
            item["originalClass"] = item.get("class")
            item["class"] = class_remap_map[c_label]

        if score >= req_thresh:
            kept.append(item)
        if is_tracking_eligible and score >= tracking_threshold:
            tracking.append(item)
    return kept, tracking


def _frame_inference_plan(workflow: dict, nodes: list[dict]) -> list[tuple[dict, float, float, dict]]:
    """Resolve fixed tracker thresholds once for this normalized workflow run.

    Keep display thresholds separate from the lower inference threshold required
    by tracking. A new run builds a new plan after workflow edits.
    """
    plan = []
    for node in nodes:
        threshold = float(node.get("config", {}).get("threshold", 0.55))
        tracking_threshold = engine.tracking_input_threshold(workflow, node)
        plan.append((node, threshold, tracking_threshold,
                     engine.inference_node_with_threshold(node, tracking_threshold)))
    return plan


def _node_title(node: dict) -> str:
    return str(node.get("customTitle") or node.get("title") or node.get("type") or "Node")


def _frame_summary(frame) -> dict:
    if frame is None:
        return {"kind": "frame", "status": "none"}
    shape = getattr(frame, "shape", None)
    if not shape or len(shape) < 2:
        return {"kind": "frame", "status": "unknown"}
    height, width = int(shape[0]), int(shape[1])
    channels = int(shape[2]) if len(shape) > 2 else 1
    return {
        "kind": "frame",
        "width": width,
        "height": height,
        "channels": channels,
        "dtype": str(getattr(frame, "dtype", "")),
    }


def _detection_sample(detections: list[dict], limit: int = 3) -> list[dict]:
    sample = []
    for item in detections[:limit]:
        compact = {
            "class": str(item.get("class", "object")),
            "score": round(float(item.get("score", 0)), 4),
        }
        if item.get("trackId") is not None:
            compact["trackId"] = item.get("trackId")
        if item.get("sourceNodeId"):
            compact["sourceNodeId"] = item.get("sourceNodeId")
        if item.get("kind") == "anomaly":
            compact.update({"kind": "anomaly", "result": item["result"],
                            "anomalyScore": item["anomalyScore"], "threshold": item["threshold"],
                            "mapShape": item["anomalyMap"]["shape"]})
        for key in ("bbox", "box", "xyxy"):
            value = item.get(key)
            if isinstance(value, (list, tuple)) and len(value) >= 4:
                compact["bbox"] = [round(float(v), 2) for v in value[:4]]
                break
        sample.append(compact)
    return sample


def _detections_summary(detections: list[dict]) -> dict:
    classes: dict[str, int] = {}
    for item in detections:
        label = str(item.get("class", "object"))
        classes[label] = classes.get(label, 0) + 1
    return {
        "kind": "detections",
        "count": len(detections),
        "classes": classes,
        "sample": _detection_sample(detections),
    }


def _active_preview_nodes(workflow: dict, source_id: str) -> list[dict]:
    explicit = [
        node for node in workflow.get("nodes", [])
        if node.get("type") == "preview"
        and node.get("enabled", True)
        and engine.has_active_path(workflow, source_id, str(node.get("id") or ""))
    ]
    if explicit:
        return explicit
    active = [
        node for node in workflow.get("nodes", [])
        if node.get("enabled", True)
        and engine.has_active_path(workflow, source_id, str(node.get("id") or ""))
    ]
    if active:
        return [{
            "id": "auto_preview",
            "type": "preview",
            "title": "Live Preview",
            "config": {
                "showTrackIds": True,
                "showTrails": True,
                "cropGridMaxItems": 16,
                "cropGridColumns": 0,
                "cropGridGap": 8,
                "holdLastEvent": True
            }
        }]
    return []


def _downstream_nodes(workflow: dict, source_id: str, node_type: str) -> list[dict]:
    return [
        node for node in workflow.get("nodes", [])
        if node.get("type") == node_type
        and node.get("enabled", True)
        and engine.has_active_path(workflow, source_id, str(node.get("id") or ""))
    ]


def _save_inspection_crop(cv2_module, crop: dict, output_node: dict) -> str:
    """Persist one crop with a collision-resistant, metadata-based filename."""
    config = output_node.get("config", {})
    output_dir = str(config.get("outputDirectory") or "").strip()
    directory = Path(output_dir).expanduser() if output_dir else engine.ROOT / "outputs" / "snapshots"
    directory.mkdir(parents=True, exist_ok=True)
    detection = crop.get("detection", {})
    extension = str(config.get("format", "jpg")).lower()
    extension = "png" if extension == "png" else "jpg"
    values = {
        "timestamp": int(time.time() * 1000),
        "track_id": detection.get("trackId", "unknown"),
        "class": detection.get("class", "object"),
        "node_id": output_node.get("id", "image_output"),
    }
    template = str(config.get("filenameTemplate") or "{timestamp}_{track_id}_{class}")
    try:
        stem = template.format(**values)
    except (KeyError, ValueError):
        stem = f"{values['timestamp']}_{values['track_id']}_{values['class']}"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip(".-") or str(values["timestamp"])
    path = directory / f"{stem}.{extension}"
    suffix = 2
    while path.exists():
        path = directory / f"{stem}-{suffix}.{extension}"
        suffix += 1
    img_to_save = crop["frame"].copy()
    if bool(config.get("burnWatermark", True)) and hasattr(img_to_save, "shape"):
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S")
        tid = detection.get("trackId")
        det_info = f"#{tid} " if tid is not None else ""
        det_info += f"{detection.get('class', 'object')} {round(float(detection.get('score', 0)) * 100)}%"
        watermark = f"{ts_str} | {det_info}".strip()
        h, w = img_to_save.shape[:2]
        if h > 20 and w > 40:
            scale = max(0.35, min(0.65, w / 600.0))
            cv2_module.putText(img_to_save, watermark, (8, h - 8), cv2_module.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 2, cv2_module.LINE_AA)
            cv2_module.putText(img_to_save, watermark, (8, h - 8), cv2_module.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2_module.LINE_AA)

    parameters = []
    if extension == "jpg":
        parameters = [int(cv2_module.IMWRITE_JPEG_QUALITY), max(1, min(100, int(config.get("jpegQuality", 95) or 95)))]
    ok, encoded = cv2_module.imencode(f".{extension}", img_to_save, parameters)
    if not ok:
        raise RuntimeError(f"Unable to encode inspection image for {path}")
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(encoded.tobytes())
    temporary.replace(path)

    # FIFO Disk Retention cleanup
    retention_max = int(config.get("maxFilesRetention", 1000) or 1000)
    if retention_max > 0:
        try:
            files = sorted(directory.glob(f"*.{extension}"), key=lambda p: p.stat().st_mtime)
            if len(files) > retention_max:
                for old_f in files[:-retention_max]:
                    old_f.unlink(missing_ok=True)
        except Exception:
            pass

    return str(path)


def _save_detection_crop_outputs(
    cv2_module,
    workflow: dict,
    crop_batches: dict[str, list[dict]],
) -> list[str]:
    """Persist crop batches connected to enabled Save Images nodes."""
    saved_paths: list[str] = []
    for crop_id, crops in crop_batches.items():
        image_outputs = _downstream_nodes(workflow, crop_id, "image_output")
        for crop in crops:
            for image_output in image_outputs:
                saved_paths.append(
                    _save_inspection_crop(cv2_module, crop, image_output)
                )
    return saved_paths


def _event_crop_annotations(crop_items: list[dict]) -> list[dict]:
    """Return the drawing data that belongs to a rendered event crop."""
    annotations: list[dict] = []
    for crop in crop_items:
        detection = crop.get("detection")
        if isinstance(detection, dict):
            annotations.append(detection)
        annotations.extend(
            item for item in crop.get("classifications", [])
            if isinstance(item, dict)
        )
    return annotations


def _retain_event_preview(
    preview_id: str,
    crop_items: list[dict],
    preview_detections: list[dict],
    held_crops: dict[str, list[dict]],
    held_annotations: dict[str, list[dict]],
) -> tuple[list[dict], list[dict]]:
    """Keep a held inspection image and its overlay values in sync."""
    if crop_items:
        held_crops[preview_id] = crop_items
        annotations = _event_crop_annotations(crop_items)
        normalized = annotations or list(preview_detections)
        held_annotations[preview_id] = normalized
        # Use the same crop-linked values immediately and on held frames so
        # captions do not jump after the first displayed frame.
        return crop_items, normalized
    return (
        held_crops.get(preview_id, []),
        held_annotations.get(preview_id, preview_detections),
    )


def _render_held_crop_grid(frame, crop_items, preview, cache, *, workflow=None):
    """Reuse the contact sheet of an owned, immutable held event snapshot.

    Keep the crop list itself alive so a later event cannot reuse its identity.
    Return a copy because downstream drawing nodes modify the display frame.
    """
    preview_id = str(preview.get("id") or "")
    config = preview.get("config", {})
    settings = tuple(config.get(key) for key in (
        "cropGridMaxItems", "cropGridGap", "cropGridColumns", "showLabels", "showBoxes",
    ))
    geometry = (frame.shape, frame.dtype.str)
    drawing_state = None
    if workflow is not None:
        plan_key = ("drawing_plan", preview_id)
        plan = cache.get(plan_key)
        if not isinstance(workflow, engine._RuntimeWorkflow) or plan is None or plan[0] is not workflow:
            plan = (workflow, engine.active_drawing_nodes_for_target(workflow, preview_id))
            cache[plan_key] = plan
        # Compare small dictionaries directly instead of serializing configs on
        # every frame. Deep copies are made only when the cached image changes.
        drawing_state = [(node.get("id"), node.get("type"), node.get("config", {})) for node in plan[1]]
    annotation_state = [(item.get("detection"), item.get("classifications", [])) for item in crop_items]
    previous = cache.get(preview_id)
    if (previous is None or previous[0] is not crop_items
            or previous[1] != geometry or previous[2] != settings
            or previous[5] != drawing_state or previous[6] != annotation_state):
        canvas = engine.render_detection_crop_grid(frame, crop_items, preview)
        if workflow is not None:
            canvas = engine.apply_drawing_nodes(
                canvas, workflow, preview_id, engine.crop_grid_drawing_detections(crop_items),
                copy_frame=False,
            )
        bounds = [tuple(item["_previewBounds"]) if "_previewBounds" in item else None
                  for item in crop_items]
        previous = (crop_items, geometry, settings, canvas, bounds,
                    copy.deepcopy(drawing_state), copy.deepcopy(annotation_state))
        cache[preview_id] = previous
    # Several previews may retain the same event objects with different grids.
    # Restore this grid's coordinates, including items hidden by its item limit.
    for item, bounds in zip(crop_items, previous[4]):
        if bounds is None:
            item.pop("_previewBounds", None)
        else:
            item["_previewBounds"] = list(bounds)
    return previous[3].copy()


def _process_track_event_nodes(
    cv2_module,
    frame,
    workflow: dict,
    detections: list[dict],
    tracked: list[dict],
    logic_runtime: dict,
    event_runtime: dict,
    now: float,
    *,
    logic_lock=None,
) -> tuple[list[dict], dict[str, list[dict]], list[dict], list[dict]]:
    """Run stateful per-track inspection and counting after tracking."""
    extra_results: list[dict] = []
    crop_batches: dict[str, list[dict]] = {}
    object_records: list[dict] = []
    count_records: list[dict] = []

    for snapshot_node in engine.active_track_snapshot_nodes(workflow):
        snapshot_id = str(snapshot_node.get("id") or "track_snapshot")
        candidates = engine.results_for_node(workflow, snapshot_id, detections, tracked)
        candidates = engine.observe_track_ages(
            snapshot_node, candidates, event_runtime, now,
        )
        with logic_lock if logic_lock is not None else nullcontext():
            candidates = engine.apply_logic_nodes(
                workflow, snapshot_id, candidates, logic_runtime, now,
            )
        linked_crops: list[tuple[dict, bool]] = []
        for crop_node in engine.track_driven_detection_crop_nodes(workflow):
            crop_id = str(crop_node.get("id") or "detection_crop")
            snapshot_before_crop = engine.has_active_path(workflow, snapshot_id, crop_id)
            crop_before_snapshot = engine.has_active_path(workflow, crop_id, snapshot_id)
            if snapshot_before_crop or crop_before_snapshot:
                linked_crops.append((crop_node, crop_before_snapshot))

        # Do not consume a track ID until it is actually eligible for at least
        # one linked crop. This includes Detection Crop class filters and any
        # Crop/Region nodes on the branch, so an object first seen outside the
        # inspection area can still emit when it later enters that area.
        if linked_crops:
            eligible_by_track: dict[tuple[str, str], dict] = {}
            for crop_node, _crop_before_snapshot in linked_crops:
                crop_id = str(crop_node.get("id") or "detection_crop")
                # Logic nodes immediately upstream of Detection Crop (most
                # importantly Region of Interest) select detections but do not
                # alter the source frame or clamp the eventual object crop.
                with logic_lock if logic_lock is not None else nullcontext():
                    crop_candidates = engine.apply_logic_nodes(
                        workflow, crop_id, candidates, logic_runtime, now,
                    )
                # Eligibility only needs bounds and identity. Preserve ranking
                # and maxCrops while avoiding image copies on every tracked frame.
                for crop in engine.detection_crops(
                    frame, workflow, crop_candidates, crop_node,
                    materialize=False,
                ):
                    detection = crop.get("detection", {})
                    track_id = detection.get("trackId")
                    if track_id is not None:
                        source_id = str(
                            detection.get("sourceNodeId")
                            or detection.get("parentSourceNodeId")
                            or "tracker"
                        )
                        eligible_by_track[(source_id, str(track_id))] = detection
            candidates = list(eligible_by_track.values())
        snapshot_events = engine.emit_track_snapshots(
            snapshot_node, candidates, event_runtime, now,
        )
        if not snapshot_events:
            continue
        extra_results.extend(snapshot_events)
        snapshot_classifications: list[dict] = []
        for crop_node, crop_before_snapshot in linked_crops:
            crop_id = str(crop_node.get("id") or "detection_crop")
            # Detection Crop validates each detection's source path.  When the
            # visual gate is drawn after the crop, use the original tracker
            # source for extraction while retaining the snapshot event and ID.
            crop_inputs = snapshot_events
            if crop_before_snapshot:
                crop_inputs = [
                    {
                        **event,
                        "sourceNodeId": str(
                            event.get("parentSourceNodeId") or "tracker"
                        ),
                    }
                    for event in snapshot_events
                ]
            crops = engine.detection_crops(frame, workflow, crop_inputs, crop_node)
            crop_batches[crop_id] = crops
            image_outputs = _downstream_nodes(workflow, crop_id, "image_output")
            paths_by_track: dict[str, str] = {}
            for crop in crops:
                for image_output in image_outputs:
                    path = _save_inspection_crop(cv2_module, crop, image_output)
                    paths_by_track[str(crop["detection"].get("trackId"))] = path
            for event in snapshot_events:
                path = paths_by_track.get(str(event.get("trackId")))
                if path:
                    event["snapshotPath"] = path

            classifications: list[dict] = []
            inspection_nodes = (
                _downstream_nodes(workflow, crop_id, "classifier")
                + _downstream_nodes(workflow, crop_id, "efficientad")
            )
            for classifier in inspection_nodes:
                classified = engine.run_detection_crop_classifier(
                    frame, crop_inputs, workflow, crop_node, classifier,
                )
                for item in classified:
                    path = paths_by_track.get(str(item.get("trackId")))
                    if path:
                        item["snapshotPath"] = path
                classifications.extend(classified)
            extra_results.extend(classifications)
            snapshot_classifications.extend(classifications)

        by_track: dict[str, list[dict]] = {}
        for item in snapshot_classifications:
            by_track.setdefault(str(item.get("trackId")), []).append(item)
        for event in snapshot_events:
            matches = sorted(
                by_track.get(str(event.get("trackId")), []),
                key=lambda item: float(item.get("score", 0.0)),
                reverse=True,
            )
            best = matches[0] if matches else {}
            object_records.append({
                **event,
                "classificationClass": best.get("class"),
                "classificationConfidence": best.get("score"),
                "snapshotPath": event.get("snapshotPath", ""),
            })

    for counter_node in engine.active_object_counter_nodes(workflow):
        counter_id = str(counter_node.get("id") or "object_counter")
        candidates = engine.results_for_node(workflow, counter_id, detections, tracked)
        with logic_lock if logic_lock is not None else nullcontext():
            candidates = engine.apply_logic_nodes(
                workflow, counter_id, candidates, logic_runtime, now,
            )
        events = engine.emit_object_count_events(
            counter_node, candidates, event_runtime, now,
        )
        extra_results.extend(events)
        count_records.extend(events)

    # Process Roboflow Line Counters (Directional IN / OUT)
    line_events = _process_line_counters(workflow, frame, detections, tracked, event_runtime, now)
    extra_results.extend(line_events)
    count_records.extend(line_events)

    # Process Roboflow Dwell Time / Loitering Zones
    dwell_events = _process_dwell_zones(workflow, frame, tracked, event_runtime, now)
    extra_results.extend(dwell_events)

    # Process Roboflow Barcode & QR Code Reader
    barcode_dets = _process_barcode_reading(workflow, frame, detections)
    extra_results.extend(barcode_dets)
    detections.extend(barcode_dets)

    return extra_results, crop_batches, object_records, count_records


def _generate_slicer_tiles(frame, slicer_node: dict):
    if frame is None or not hasattr(frame, "shape"):
        return []
    h, w = frame.shape[:2]
    config = slicer_node.get("config", {})
    sw = max(128, int(config.get("sliceWidth", 640) or 640))
    sh = max(128, int(config.get("sliceHeight", 640) or 640))
    overlap = max(0.0, min(0.8, float(config.get("overlapRatio", 0.2) or 0.2)))
    step_x = max(64, int(sw * (1.0 - overlap)))
    step_y = max(64, int(sh * (1.0 - overlap)))

    tiles = []
    for y in range(0, max(1, h - sh + 1), step_y):
        for x in range(0, max(1, w - sw + 1), step_x):
            actual_w = min(sw, w - x)
            actual_h = min(sh, h - y)
            tiles.append((frame[y:y+actual_h, x:x+actual_w], x, y, actual_w, actual_h))
    return tiles


def _merge_slicer_detections(all_tile_detections: list[dict], iou_threshold: float = 0.45) -> list[dict]:
    import cv2
    if not all_tile_detections:
        return []
    boxes = [[int(d.get("x", 0)), int(d.get("y", 0)), int(d.get("width", 0)), int(d.get("height", 0))] for d in all_tile_detections]
    scores = [float(d.get("score", 0.0)) for d in all_tile_detections]
    indices = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=0.01, nms_threshold=iou_threshold)
    if len(indices) == 0:
        return []
    indices = [int(i[0] if hasattr(i, "__iter__") else i) for i in indices]
    return [all_tile_detections[i] for i in indices]


def _parse_point(val, w: int, h: int) -> tuple[int, int]:
    if not val:
        return 0, 0
    if isinstance(val, dict):
        x, y = float(val.get("x", 0.0)), float(val.get("y", 0.0))
    elif isinstance(val, (list, tuple)):
        if len(val) >= 2:
            x, y = float(val[0]), float(val[1])
        elif len(val) == 1:
            x, y = float(val[0]), float(val[0])
        else:
            return 0, 0
    else:
        try:
            parts = [float(p.strip()) for p in str(val).split(",") if p.strip()]
            if len(parts) >= 2:
                x, y = parts[0], parts[1]
            elif len(parts) == 1:
                x, y = parts[0], parts[0]
            else:
                return 0, 0
        except (ValueError, TypeError):
            return 0, 0
    if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
        return int(round(x * w)), int(round(y * h))
    return int(round(x)), int(round(y))


def _parse_polygon(val, w: int, h: int):
    import numpy as np
    pts = []
    if isinstance(val, (list, tuple)):
        for item in val:
            pts.append(_parse_point(item, w, h))
    else:
        for seg in str(val).split(";"):
            seg = seg.strip()
            if seg:
                pts.append(_parse_point(seg, w, h))
    if len(pts) < 3:
        pts = [(int(w * 0.2), int(h * 0.2)), (int(w * 0.8), int(h * 0.2)), (int(w * 0.8), int(h * 0.8)), (int(w * 0.2), int(h * 0.8))]
    return np.array(pts, dtype=np.int32)


def _extract_detection_box(det: dict) -> tuple[float, float, float, float] | None:
    for key in ("bbox", "box"):
        b = det.get(key)
        if isinstance(b, (list, tuple)) and len(b) >= 4:
            try:
                x, y, w, h = float(b[0]), float(b[1]), float(b[2]), float(b[3])
                if w > 0 and h > 0:
                    return x, y, w, h
            except (TypeError, ValueError):
                pass
    xyxy = det.get("xyxy")
    if isinstance(xyxy, (list, tuple)) and len(xyxy) >= 4:
        try:
            x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
            if x2 > x1 and y2 > y1:
                return x1, y1, x2 - x1, y2 - y1
        except (TypeError, ValueError):
            pass
    if "x" in det and "y" in det:
        try:
            x = float(det["x"])
            y = float(det["y"])
            w = float(det.get("width", det.get("w", 0)))
            h = float(det.get("height", det.get("h", 0)))
            if w > 0 and h > 0:
                return x, y, w, h
        except (TypeError, ValueError):
            pass
    return None


def _get_anchor_point(det: dict, anchor_mode: str) -> tuple[float, float] | None:
    box = _extract_detection_box(det)
    if not box:
        trail = det.get("trail")
        if trail and len(trail) > 0 and isinstance(trail[-1], (list, tuple)) and len(trail[-1]) >= 2:
            return float(trail[-1][0]), float(trail[-1][1])
        return None
    bx, by, bw, bh = box
    mode = str(anchor_mode or "bottom_center").strip().lower()
    if mode in ("center", "centroid"):
        return (bx + bw / 2.0, by + bh / 2.0)
    elif mode in ("top_center", "top"):
        return (bx + bw / 2.0, by)
    elif mode in ("bottom_center", "bottom"):
        return (bx + bw / 2.0, by + bh)
    elif mode == "bottom_left":
        return (bx, by + bh)
    elif mode == "bottom_right":
        return (bx + bw, by + bh)
    elif mode == "top_left":
        return (bx, by)
    elif mode == "top_right":
        return (bx + bw, by)
    return (bx + bw / 2.0, by + bh)


def _normalize_line_counter_config(config: dict) -> list[dict]:
    """Return a normalized list of line objects supporting both multi-line and legacy single line."""
    raw_lines = config.get("lines")
    lines = []
    if isinstance(raw_lines, list) and len(raw_lines) > 0:
        for idx, item in enumerate(raw_lines):
            if not isinstance(item, dict):
                continue
            lid = str(item.get("id") or f"line_{idx + 1}")
            lines.append({
                "id": lid,
                "name": str(item.get("name") or f"Line {idx + 1}"),
                "startPoint": str(item.get("startPoint") or "").strip(),
                "endPoint": str(item.get("endPoint") or "").strip(),
                "invertDirection": bool(item.get("invertDirection", False)),
                "countMode": str(item.get("countMode", "both")).lower(),
                "lineColor": str(item.get("lineColor") or "#22c55e"),
                "lineWidth": max(1, int(item.get("lineWidth", config.get("lineWidth", 2)) or 2)),
                "inLabel": str(item.get("inLabel", config.get("inLabel", "IN")) or "IN").strip(),
                "outLabel": str(item.get("outLabel", config.get("outLabel", "OUT")) or "OUT").strip(),
            })
    if not lines:
        sp = str(config.get("startPoint") or "").strip()
        ep = str(config.get("endPoint") or "").strip()
        lines.append({
            "id": "line_1",
            "name": "Line 1",
            "startPoint": sp,
            "endPoint": ep,
            "invertDirection": bool(config.get("invertDirection", False)),
            "countMode": str(config.get("countMode", "both")).lower(),
            "lineColor": str(config.get("lineColor") or "#22c55e"),
            "lineWidth": max(1, int(config.get("lineWidth", 2) or 2)),
            "inLabel": str(config.get("inLabel", "IN") or "IN").strip(),
            "outLabel": str(config.get("outLabel", "OUT") or "OUT").strip(),
        })
    return lines


def _check_line_crossing(p1: tuple[int, int], p2: tuple[int, int], q1: tuple[float, float], q2: tuple[float, float], invert_direction: bool = False) -> str | None:
    """
    Check if track segment q1->q2 crosses line segment p1->p2.
    Returns: 'IN', 'OUT', or None.
    Uses 2D cross product sign changes and parametric projection along the line.
    """
    Px = float(p2[0] - p1[0])
    Py = float(p2[1] - p1[1])
    line_len_sq = Px * Px + Py * Py
    if line_len_sq < 1.0:
        return None

    Qx = float(q2[0] - q1[0])
    Qy = float(q2[1] - q1[1])
    move_len_sq = Qx * Qx + Qy * Qy
    if move_len_sq < 0.25:
        return None

    # 2D cross product: cross(P1P2, P1Q)
    s1 = Px * float(q1[1] - p1[1]) - Py * float(q1[0] - p1[0])
    s2 = Px * float(q2[1] - p1[1]) - Py * float(q2[0] - p1[0])

    # Check if endpoints lie on opposite sides of the line (or one lies on the line)
    if (s1 * s2 <= 0) and (s1 != 0 or s2 != 0):
        total_side = abs(s1) + abs(s2)
        if total_side > 1e-6:
            frac = abs(s1) / total_side
            ix = float(q1[0]) + frac * Qx
            iy = float(q1[1]) + frac * Qy
            # Project crossing point onto P1->P2 to ensure it passed through the line segment
            t = ((ix - p1[0]) * Px + (iy - p1[1]) * Py) / line_len_sq
            # Allow 20% tolerance beyond endpoints
            if -0.20 <= t <= 1.20:
                direction = "IN" if (s1 < 0 or (s1 == 0 and s2 > 0)) else "OUT"
                if invert_direction:
                    direction = "OUT" if direction == "IN" else "IN"
                return direction
    return None


def _process_line_counters(
    workflow: dict,
    frame,
    detections: list[dict],
    tracked: list[dict],
    event_runtime: dict,
    now: float,
) -> list[dict]:
    if frame is None or not hasattr(frame, "shape"):
        return []
    h, w = frame.shape[:2]
    new_events = []

    for node in workflow.get("nodes", []):
        if node.get("type") != "line_counter" or not node.get("enabled", True):
            continue
        node_id = str(node.get("id") or "line_counter")
        config = node.get("config", {})

        # Resolve candidate detections for this node
        candidates = engine.results_for_node(workflow, node_id, detections, tracked)
        if not candidates:
            candidates = tracked if tracked else detections

        lines = _normalize_line_counter_config(config)
        # Check if at least one line has valid coordinates
        has_active_line = any(
            line.get("startPoint") and line.get("endPoint")
            and line["startPoint"] != "0,0" and line["endPoint"] != "0,0"
            for line in lines
        )
        if not has_active_line:
            continue

        anchor_mode = str(config.get("triggerAnchor", "center"))
        classes_raw = str(config.get("classes", "")).strip()
        wanted_classes = []
        if classes_raw and not classes_raw.lower().startswith("e.g."):
            wanted_classes = [c.strip().casefold() for c in classes_raw.split(",") if c.strip() and not c.strip().lower().startswith("e.g.")]

        state = event_runtime.setdefault(node_id, {
            "count_in": 0,
            "count_out": 0,
            "total_in": 0,
            "total_out": 0,
            "lines": {},
            "auto_tracks": {},
            "_next_auto_id": 1,
            "last_crossing_timestamp": 0.0,
        })

        # Ensure all detections have a consistent trackId (auto-track if no tracker node is in pipeline)
        processed_candidates = []
        for det in candidates:
            cls_name = str(det.get("class", "object")).strip()
            if wanted_classes and cls_name.casefold() not in wanted_classes:
                continue

            curr_anchor = _get_anchor_point(det, anchor_mode)
            if curr_anchor is None:
                continue

            # Multi-anchor candidates for robust line crossing (upper-body, center, or feet)
            candidate_anchors = {"primary": curr_anchor}
            center_anchor = _get_anchor_point(det, "center")
            if center_anchor is not None:
                candidate_anchors["center"] = center_anchor
            bottom_anchor = _get_anchor_point(det, "bottom_center")
            if bottom_anchor is not None:
                candidate_anchors["bottom_center"] = bottom_anchor
            top_anchor = _get_anchor_point(det, "top_center")
            if top_anchor is not None:
                candidate_anchors["top_center"] = top_anchor

            item = dict(det)
            item["_orig_det"] = det
            tid = item.get("trackId")
            if tid is None:
                # Auto-associate detection using spatial proximity
                ax, ay = curr_anchor
                best_id = None
                min_dist = float("inf")
                max_track_dist = max(180.0, max(w, h) * 0.25)
                auto_tracks = state.setdefault("auto_tracks", {})
                for at_id, at_info in list(auto_tracks.items()):
                    if now - at_info.get("last_seen", 0.0) > 1.5:
                        continue
                    oax, oay = at_info["anchor"]
                    dist = math.hypot(ax - oax, ay - oay)
                    if dist < max_track_dist and dist < min_dist:
                        min_dist = dist
                        best_id = at_id

                if best_id is None:
                    next_id = state.get("_next_auto_id", 1)
                    best_id = f"auto_{next_id}"
                    state["_next_auto_id"] = next_id + 1

                auto_tracks[best_id] = {
                    "anchor": curr_anchor,
                    "last_seen": now,
                    "class": cls_name,
                }
                item["trackId"] = best_id
                det["trackId"] = best_id

            item["_anchor"] = curr_anchor
            item["_candidate_anchors"] = candidate_anchors
            processed_candidates.append(item)

        # Cleanup stale auto tracks
        auto_tracks = state.setdefault("auto_tracks", {})
        stale_auto = [aid for aid, ainfo in auto_tracks.items() if now - ainfo.get("last_seen", 0.0) > 4.0]
        for aid in stale_auto:
            auto_tracks.pop(aid, None)

        # Process each configured counting line
        for line in lines:
            sp_raw = line.get("startPoint")
            ep_raw = line.get("endPoint")
            if not sp_raw or not ep_raw or sp_raw == "0,0" or ep_raw == "0,0":
                continue

            p1 = _parse_point(sp_raw, w, h)
            p2 = _parse_point(ep_raw, w, h)
            if p1 == p2:
                continue

            lid = line["id"]
            line_name = line["name"]
            invert_dir = line["invertDirection"]
            count_mode = line["countMode"]

            line_state = state.setdefault("lines", {}).setdefault(lid, {
                "count_in": 0,
                "count_out": 0,
                "positions": {},
                "last_seen": {},
                "last_event": {},
                "last_event_time": {},
                "last_crossing_timestamp": 0.0,
            })

            for det in processed_candidates:
                tid = det["trackId"]
                curr_anchors = det["_candidate_anchors"]

                prev_entry = line_state["positions"].get(tid)
                last_seen = line_state["last_seen"].get(tid, 0.0)
                line_state["positions"][tid] = curr_anchors
                line_state["last_seen"][tid] = now

                if prev_entry is not None and (now - last_seen) < 2.5:
                    prev_anchors = prev_entry if isinstance(prev_entry, dict) else {"primary": prev_entry}

                    # Test candidate anchor trajectories (primary first, then center, bottom_center, top_center)
                    direction = None
                    for anchor_key in ("primary", "center", "bottom_center", "top_center"):
                        prev_pt = prev_anchors.get(anchor_key)
                        curr_pt = curr_anchors.get(anchor_key)
                        if prev_pt and curr_pt:
                            detected_dir = _check_line_crossing(p1, p2, prev_pt, curr_pt, invert_direction=invert_dir)
                            if detected_dir:
                                direction = detected_dir
                                break

                    if direction:
                        if count_mode == "in_only" and direction != "IN":
                            continue
                        if count_mode == "out_only" and direction != "OUT":
                            continue

                        last_event = line_state["last_event"].get(tid)
                        last_event_time = line_state["last_event_time"].get(tid, 0.0)

                        if (now - last_event_time >= 0.7) or (last_event != direction):
                            line_state["last_event"][tid] = direction
                            line_state["last_event_time"][tid] = now
                            line_state["last_crossing_timestamp"] = now
                            state["last_crossing_timestamp"] = now

                            if direction == "IN":
                                line_state["count_in"] += 1
                                state["total_in"] = state.get("total_in", 0) + 1
                            else:
                                line_state["count_out"] += 1
                                state["total_out"] = state.get("total_out", 0) + 1

                            state["count_in"] = state["total_in"]
                            state["count_out"] = state["total_out"]

                            evt = dict(det)
                            evt.pop("_anchor", None)
                            evt.pop("_candidate_anchors", None)
                            evt.pop("_orig_det", None)
                            evt.update({
                                "kind": "line_crossing",
                                "direction": direction,
                                "sourceNodeId": node_id,
                                "lineCounterId": node_id,
                                "lineId": lid,
                                "lineName": line_name,
                                "countIn": line_state["count_in"],
                                "countOut": line_state["count_out"],
                                "totalCountIn": state["total_in"],
                                "totalCountOut": state["total_out"],
                            })
                            new_events.append(evt)

                # Set dynamic bounding box color and direction tag based on crossing state
                last_dir = line_state["last_event"].get(tid)
                if last_dir:
                    # BGR colors: Vibrant Green for IN (34, 197, 94), Coral Red for OUT (68, 68, 239)
                    box_color = (34, 197, 94) if last_dir == "IN" else (68, 68, 239)
                    det["boxColor"] = box_color
                    det["lineDirection"] = last_dir
                    orig = det.get("_orig_det")
                    if isinstance(orig, dict):
                        orig["boxColor"] = box_color
                        orig["lineDirection"] = last_dir

            # Cleanup inactive tracks for this line
            stale_line_tracks = [t for t, t_seen in list(line_state["last_seen"].items()) if now - t_seen > 12.0]
            for t in stale_line_tracks:
                line_state["positions"].pop(t, None)
                line_state["last_seen"].pop(t, None)
                line_state["last_event"].pop(t, None)
                line_state["last_event_time"].pop(t, None)

    return new_events


def _process_dwell_zones(workflow: dict, frame, tracked: list[dict], event_runtime: dict, now: float) -> list[dict]:
    import cv2
    if frame is None or not hasattr(frame, "shape"):
        return []
    h, w = frame.shape[:2]
    new_events = []
    for node in workflow.get("nodes", []):
        if node.get("type") != "dwell_time" or not node.get("enabled", True):
            continue
        node_id = str(node.get("id") or "dwell_time")
        config = node.get("config", {})
        poly = _parse_polygon(config.get("points", "0.2,0.2; 0.8,0.2; 0.8,0.8; 0.2,0.8"), w, h)
        if len(poly) < 3:
            continue
        threshold = float(config.get("thresholdSeconds", 5.0) or 5.0)
        classes_raw = str(config.get("classes", "")).strip()
        wanted_classes = []
        if classes_raw and not classes_raw.lower().startswith("e.g."):
            wanted_classes = [c.strip().casefold() for c in classes_raw.split(",") if c.strip() and not c.strip().lower().startswith("e.g.")]

        state = event_runtime.setdefault(node_id, {
            "entered_at": {},
            "loitering_alerted": set(),
        })

        active_tracks = set()
        for det in tracked:
            tid = det.get("trackId")
            if tid is None:
                continue
            cls_name = str(det.get("class", "object")).strip()
            if wanted_classes and cls_name.casefold() not in wanted_classes:
                continue

            active_tracks.add(tid)
            anchor = _get_anchor_point(det, "bottom_center")
            if anchor is None:
                continue
            cx, cy = anchor

            dist = cv2.pointPolygonTest(poly, (float(cx), float(cy)), False)
            if dist >= 0:
                t0 = state["entered_at"].setdefault(tid, now)
                dwell_sec = now - t0
                det["dwellSeconds"] = round(dwell_sec, 1)
                det["dwellZoneId"] = node_id
                if dwell_sec >= threshold:
                    det["isLoitering"] = True
                    if tid not in state["loitering_alerted"]:
                        state["loitering_alerted"].add(tid)
                        evt = dict(det)
                        evt.update({
                            "kind": "loitering_alert",
                            "sourceNodeId": node_id,
                            "dwellZoneId": node_id,
                            "dwellSeconds": round(dwell_sec, 1),
                        })
                        new_events.append(evt)
            else:
                state["entered_at"].pop(tid, None)
                state["loitering_alerted"].discard(tid)

        stale = [t for t in state["entered_at"] if t not in active_tracks]
        for t in stale:
            state["entered_at"].pop(t, None)
            state["loitering_alerted"].discard(t)

    return new_events


def _process_barcode_reading(workflow: dict, frame, detections: list[dict]) -> list[dict]:
    import cv2
    new_detections = []
    has_barcode = any(n.get("type") == "barcode_reader" and n.get("enabled", True) for n in workflow.get("nodes", []))
    if not has_barcode or frame is None:
        return new_detections

    try:
        qr_detector = cv2.QRCodeDetector()
        ok, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(frame)
        if ok and decoded_info:
            for text, pts in zip(decoded_info, points):
                text_clean = str(text or "").strip()
                if not text_clean or len(pts) < 4:
                    continue
                x_coords = pts[:, 0]
                y_coords = pts[:, 1]
                x1, y1 = float(x_coords.min()), float(y_coords.min())
                w, h = float(x_coords.max() - x1), float(y_coords.max() - y1)
                new_detections.append({
                    "class": "QR/Barcode",
                    "score": 1.0,
                    "x": x1,
                    "y": y1,
                    "width": w,
                    "height": h,
                    "qr_text": text_clean,
                    "sourceNodeId": "barcode_reader",
                })
    except Exception:
        pass
    return new_detections


def _parse_bgr_color(val: object, fallback: tuple[int, int, int] = (34, 197, 94)) -> tuple[int, int, int]:
    text = str(val or "").strip().lstrip("#")
    if len(text) == 6:
        try:
            r, g, b = int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
            return (b, g, r)
        except ValueError:
            pass
    return fallback


def _apply_privacy_blur(workflow: dict, frame, detections: list[dict]) -> None:
    import cv2
    if frame is None or not hasattr(frame, "shape"):
        return
    h, w = frame.shape[:2]
    for node in workflow.get("nodes", []):
        if node.get("type") != "blur_anonymizer" or not node.get("enabled", True):
            continue
        config = node.get("config", {})
        wanted_classes = [c.strip().casefold() for c in str(config.get("classes", "")).split(",") if c.strip()]
        mode = str(config.get("mode", "gaussian")).strip().lower()
        k_size = int(config.get("kernelSize", 35) or 35)
        if k_size % 2 == 0:
            k_size += 1
        block_size = max(2, int(config.get("pixelateBlock", 16) or 16))

        for det in detections:
            cls_name = str(det.get("class", "")).strip().casefold()
            if wanted_classes and cls_name not in wanted_classes:
                continue
            box = _extract_detection_box(det)
            if not box:
                continue
            bx, by, bw, bh = box
            x1 = max(0, min(w - 1, int(round(bx))))
            y1 = max(0, min(h - 1, int(round(by))))
            x2 = max(0, min(w, int(round(bx + bw))))
            y2 = max(0, min(h, int(round(by + bh))))
            rw, rh = x2 - x1, y2 - y1
            if rw > 4 and rh > 4:
                roi = frame[y1:y2, x1:x2]
                if mode == "pixelate":
                    small = cv2.resize(roi, (max(1, rw // block_size), max(1, rh // block_size)), interpolation=cv2.INTER_LINEAR)
                    pixelated = cv2.resize(small, (rw, rh), interpolation=cv2.INTER_NEAREST)
                    frame[y1:y2, x1:x2] = pixelated
                else:
                    frame[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (k_size, k_size), 0)


def _draw_roboflow_workflow_overlays(frame, workflow: dict, event_runtime: dict) -> None:
    import cv2
    import math
    import time
    if frame is None or not hasattr(frame, "shape"):
        return
    h, w = frame.shape[:2]

    # 1. Draw Line Counters (Multi-Line support)
    for node in workflow.get("nodes", []):
        if node.get("type") != "line_counter" or not node.get("enabled", True):
            continue
        node_id = str(node.get("id") or "line_counter")
        config = node.get("config", {})
        if not config.get("showOverlay", True):
            continue

        lines = _normalize_line_counter_config(config)
        state = event_runtime.get(node_id, {})
        now_mono = time.monotonic()

        for line in lines:
            sp_raw = line.get("startPoint")
            ep_raw = line.get("endPoint")
            if not sp_raw or not ep_raw or sp_raw == "0,0" or ep_raw == "0,0":
                # Line is deleted or empty: do not draw anything
                continue

            p1 = _parse_point(sp_raw, w, h)
            p2 = _parse_point(ep_raw, w, h)
            if p1 == p2:
                continue

            lid = line["id"]
            line_name = line["name"]
            line_color = _parse_bgr_color(line.get("lineColor"), (34, 197, 94))
            line_width = max(1, int(line.get("lineWidth", 2) or 2))
            invert_dir = line["invertDirection"]
            in_lbl = line["inLabel"]
            out_lbl = line["outLabel"]

            # Main crossing line
            cv2.line(frame, p1, p2, line_color, line_width, cv2.LINE_AA)

            # Endpoint circles
            cv2.circle(frame, p1, line_width + 4, line_color, -1, cv2.LINE_AA)
            cv2.circle(frame, p1, max(1, line_width + 1), (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, p2, line_width + 4, line_color, -1, cv2.LINE_AA)
            cv2.circle(frame, p2, max(1, line_width + 1), (255, 255, 255), -1, cv2.LINE_AA)

            # Directional guide arrows (normal to line)
            pdx = float(p2[0] - p1[0])
            pdy = float(p2[1] - p1[1])
            line_len = math.hypot(pdx, pdy)
            mid_x = (p1[0] + p2[0]) // 2
            mid_y = (p1[1] + p2[1]) // 2

            if line_len > 15:
                # Unit normal pointing towards IN direction
                nx = -pdy / line_len
                ny = pdx / line_len
                if invert_dir:
                    nx, ny = -nx, -ny

                arrow_len = 22
                in_color = (34, 197, 94)    # Green for IN
                out_color = (68, 68, 239)   # Red/Coral for OUT

                # IN arrow (pointing into IN side)
                in_tip_x = int(round(mid_x + nx * arrow_len))
                in_tip_y = int(round(mid_y + ny * arrow_len))
                cv2.arrowedLine(frame, (mid_x, mid_y), (in_tip_x, in_tip_y), in_color, max(1, line_width), tipLength=0.35)
                cv2.putText(frame, in_lbl, (in_tip_x + int(nx * 8) - 10, in_tip_y + int(ny * 8) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.38, in_color, 1, cv2.LINE_AA)

                # OUT arrow (pointing into OUT side)
                out_tip_x = int(round(mid_x - nx * arrow_len))
                out_tip_y = int(round(mid_y - ny * arrow_len))
                cv2.arrowedLine(frame, (mid_x, mid_y), (out_tip_x, out_tip_y), out_color, max(1, line_width), tipLength=0.35)
                cv2.putText(frame, out_lbl, (out_tip_x - int(nx * 8) - 14, out_tip_y - int(ny * 8) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.38, out_color, 1, cv2.LINE_AA)

            # Counter HUD badge per line
            line_state = state.get("lines", {}).get(lid, {})
            in_c = line_state.get("count_in", state.get("count_in", 0) if len(lines) == 1 else 0)
            out_c = line_state.get("count_out", state.get("count_out", 0) if len(lines) == 1 else 0)
            label_text = f"[{line_name}] {in_lbl} {in_c} | {out_lbl} {out_c}"

            (tw, th), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.40, 1)
            pad_x, pad_y = 8, 5
            bx1 = max(0, mid_x - tw // 2 - pad_x)
            by1 = max(0, mid_y - th // 2 - pad_y)
            bx2 = min(w, mid_x + tw // 2 + pad_x)
            by2 = min(h, mid_y + th // 2 + pad_y)

            # Draw badge background
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), (17, 24, 39), -1)

            # Draw border (highlight on recent crossing event)
            recent_cross = (now_mono - float(line_state.get("last_crossing_timestamp", 0.0))) < 0.6
            border_color = (0, 255, 255) if recent_cross else line_color
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), border_color, 1, cv2.LINE_AA)

            # Badge text
            cv2.putText(
                frame,
                label_text,
                (bx1 + pad_x, by2 - pad_y + 1),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.40,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    # 2. Draw Dwell Time Zones
    for node in workflow.get("nodes", []):
        if node.get("type") != "dwell_time" or not node.get("enabled", True):
            continue
        node_id = str(node.get("id") or "dwell_time")
        config = node.get("config", {})
        if not config.get("showOverlay", True):
            continue
        poly = _parse_polygon(config.get("points", "0.2,0.2; 0.8,0.2; 0.8,0.8; 0.2,0.8"), w, h)
        if len(poly) < 3:
            continue
        state = event_runtime.get(node_id, {})
        is_alert = len(state.get("loitering_alerted", set())) > 0
        zone_color = (239, 68, 68) if is_alert else (245, 158, 11)

        overlay = frame.copy()
        cv2.fillPoly(overlay, [poly], zone_color)
        cv2.addWeighted(overlay, 0.22, frame, 0.78, 0, frame)
        cv2.polylines(frame, [poly], True, zone_color, 2, cv2.LINE_AA)

        lx, ly = poly[0][0], max(20, poly[0][1] - 8)
        tag = "LOITERING DETECTED!" if is_alert else f"DWELL ZONE ({config.get('thresholdSeconds', 5)}s max)"
        cv2.rectangle(frame, (lx, ly - 14), (lx + len(tag) * 8 + 10, ly + 4), (17, 24, 39), -1)
        cv2.putText(frame, tag, (lx + 5, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)


class NativePreviewDisplay:
    """Owns OpenCV HighGUI windows for worker-process preview display."""

    def __init__(self, cv2_module) -> None:
        self.cv2 = cv2_module
        self._windows: dict[str, str] = {}
        self._window_frame_sizes: dict[str, tuple[int, int]] = {}
        self._window_sizes: dict[str, tuple[int, int]] = {}

    def show(self, preview_id: str, preview: dict, frame) -> None:
        # In the webapp context, frames are delivered via HTTP MJPEG stream; do not open desktop HighGUI windows.
        return

    def _unique_window_name(self, preview_id: str, preview: dict) -> str:
        """Return a HighGUI identity that cannot collapse another Preview node."""
        base_name = self._window_name(preview_id, preview)
        used_names = set(self._windows.values())
        if base_name not in used_names:
            return base_name
        candidate = f"{base_name} ({preview_id})"
        suffix = 2
        while candidate in used_names:
            candidate = f"{base_name} ({preview_id}-{suffix})"
            suffix += 1
        return candidate

    def _arrange_windows(self) -> None:
        """Tile multiple native previews instead of stacking them in one spot."""
        if len(self._windows) < 2:
            return
        move_window = getattr(self.cv2, "moveWindow", None)
        if move_window is None:
            return
        screen_size = self._screen_size()
        if screen_size is None:
            for index, window_name in enumerate(self._windows.values()):
                move_window(window_name, 40 + index * 56, 40 + index * 56)
            return

        screen_width, screen_height = screen_size
        count = len(self._windows)
        columns = min(
            count,
            max(1, int(math.ceil(math.sqrt(count * screen_width / max(1, screen_height))))),
        )
        rows = int(math.ceil(count / columns))
        margin = 16
        cell_width = max(1, (screen_width - margin * (columns + 1)) // columns)
        cell_height = max(1, (screen_height - margin * (rows + 1)) // rows)
        for index, (preview_id, window_name) in enumerate(self._windows.items()):
            frame_width, frame_height = self._window_frame_sizes.get(preview_id, (cell_width, cell_height))
            scale = min(
                cell_width / max(1, frame_width),
                (cell_height - 40) / max(1, frame_height),
            )
            window_width = max(1, int(frame_width * scale))
            window_height = max(1, int(frame_height * scale))
            row, column = divmod(index, columns)
            x = margin + column * cell_width + max(0, (cell_width - window_width) // 2)
            y = margin + row * cell_height + max(0, (cell_height - window_height) // 2)
            self.cv2.resizeWindow(window_name, window_width, window_height)
            move_window(window_name, x, y)
            self._window_sizes[preview_id] = (window_width, window_height)

    @staticmethod
    def _screen_size() -> tuple[int, int] | None:
        try:
            import ctypes

            user32 = ctypes.windll.user32
            width = int(user32.GetSystemMetrics(0))
            height = int(user32.GetSystemMetrics(1))
            return (width, height) if width > 0 and height > 0 else None
        except (AttributeError, OSError):
            return None

    def poll_stop_requested(self) -> bool:
        # pollKey pumps HighGUI events without waitKey's >=1ms sleep per frame.
        poll = getattr(self.cv2, "pollKey", None)
        key = (poll() if poll is not None else self.cv2.waitKey(1)) & 0xFF
        self._constrain_window_aspect_ratios()
        return key in (27, ord("q")) or self._window_was_closed()

    def _window_was_closed(self) -> bool:
        """Return whether the user closed any managed HighGUI window."""
        get_property = getattr(self.cv2, "getWindowProperty", None)
        visible_property = getattr(self.cv2, "WND_PROP_VISIBLE", None)
        if get_property is None or visible_property is None:
            return False
        for window_name in list(self._windows.values()):
            try:
                if float(get_property(window_name, visible_property)) < 1:
                    return True
            except Exception:  # noqa: BLE001 - closed windows may no longer be queryable
                return True
        return False

    def close(self) -> None:
        for window_name in list(self._windows.values()):
            try:
                self.cv2.destroyWindow(window_name)
            except Exception:  # noqa: BLE001 - OpenCV window cleanup is best effort
                pass
        self._windows.clear()
        self._window_frame_sizes.clear()
        self._window_sizes.clear()
        try:
            self.cv2.waitKey(1)
        except Exception:  # noqa: BLE001
            pass

    def _configure_window(self, window_name: str, frame_size: tuple[int, int]) -> None:
        width, height = frame_size
        if width <= 0 or height <= 0:
            return
        try:
            self.cv2.setWindowProperty(
                window_name,
                self.cv2.WND_PROP_ASPECT_RATIO,
                getattr(self.cv2, "WINDOW_KEEPRATIO", 0),
            )
        except Exception:  # noqa: BLE001 - backend support varies by OpenCV build
            pass
        self.cv2.resizeWindow(window_name, width, height)

    def _constrain_window_aspect_ratios(self) -> None:
        """Keep HighGUI window resizing locked to each preview frame's ratio.

        ``WINDOW_KEEPRATIO`` preserves the image on some HighGUI backends, but
        the Win32 backend ignores it and stretches the frame.  Reading the live
        image area after the event pump lets us correct either resize axis while
        the user drags the window.
        """
        get_rect = getattr(self.cv2, "getWindowImageRect", None)
        if get_rect is None:
            return
        for preview_id, window_name in list(self._windows.items()):
            frame_size = self._window_frame_sizes.get(preview_id, (0, 0))
            try:
                rect = get_rect(window_name)
            except Exception:  # noqa: BLE001 - a user may close a native window
                continue
            if not rect or len(rect) < 4:
                continue
            current_size = (int(rect[2]), int(rect[3]))
            previous_size = self._window_sizes.get(preview_id, frame_size)
            constrained_size = self._aspect_constrained_size(
                current_size,
                previous_size,
                frame_size,
            )
            if constrained_size != current_size:
                try:
                    self.cv2.resizeWindow(window_name, *constrained_size)
                except Exception:  # noqa: BLE001 - backend support varies
                    continue
            self._window_sizes[preview_id] = constrained_size

    @staticmethod
    def _aspect_constrained_size(
        current_size: tuple[int, int],
        previous_size: tuple[int, int],
        frame_size: tuple[int, int],
    ) -> tuple[int, int]:
        current_width, current_height = current_size
        previous_width, previous_height = previous_size
        frame_width, frame_height = frame_size
        if min(current_width, current_height, frame_width, frame_height) <= 0:
            return current_size

        expected_height = round(current_width * frame_height / frame_width)
        if abs(current_height - expected_height) <= 1:
            return current_size

        width_change = abs(current_width - previous_width) / max(previous_width, 1)
        height_change = abs(current_height - previous_height) / max(previous_height, 1)
        if width_change >= height_change:
            return current_width, max(1, expected_height)
        expected_width = round(current_height * frame_width / frame_height)
        return max(1, expected_width), current_height

    @staticmethod
    def _frame_size(frame) -> tuple[int, int]:
        shape = getattr(frame, "shape", None)
        if not shape or len(shape) < 2:
            return 0, 0
        return int(shape[1]), int(shape[0])

    @staticmethod
    def _window_name(preview_id: str, preview: dict) -> str:
        title = str(preview.get("customTitle") or preview.get("title") or preview_id or "Preview")
        return f"VisoNode - {title}"


def wait_for_static_preview_close(
    native_preview: NativePreviewDisplay,
    stop_event: Event,
    *,
    poll_interval: float = 0.05,
) -> None:
    """Keep a rendered static preview responsive until the user closes it."""
    while not stop_event.is_set():
        if native_preview.poll_stop_requested():
            stop_event.set()
            return
        stop_event.wait(poll_interval)


@dataclass
class FramePacket:
    frame_id: int
    frame: object
    timestamp: float  # capture time (time.monotonic), carried through the pipeline
    duration_ms: float = 0.0
    source_label: str = ""
    workflow: dict | None = None
    script_frames: dict = field(default_factory=dict)


@dataclass
class DetectionPacket:
    frame_id: int
    frame: object
    detections: list[dict]
    tracking_detections: list[dict]
    filtered: list[dict]
    crop_batches: dict[str, list[dict]]
    timestamp: float  # capture time of the underlying frame
    workflow: dict | None = None
    script_frames: dict = field(default_factory=dict)


@dataclass
class TrackingPacket:
    frame_id: int
    frame: object
    detections: list[dict]
    tracked: list[dict]
    filtered: list[dict]
    crop_batches: dict[str, list[dict]]
    object_records: list[dict]
    count_records: list[dict]
    timestamp: float  # capture time of the underlying frame
    workflow: dict | None = None
    script_frames: dict = field(default_factory=dict)


def _sampler_target_fps(node: dict) -> float:
    raw = node.get("config", {}).get("targetFps", 10)
    if isinstance(raw, bool):
        raise ValueError("Frame sampler targetFps must be a finite number >= 0")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError("Frame sampler targetFps must be a finite number >= 0") from None
    if not math.isfinite(value) or value < 0:
        raise ValueError("Frame sampler targetFps must be a finite number >= 0")
    return value


def sample_frame_workflow(workflow: dict, runtime: dict, now: float) -> dict:
    """Return this frame's graph view after frame-sampler gates are evaluated."""
    nodes = list(workflow.get("nodes", []))
    node_by_id = {str(node.get("id")): node for node in nodes}
    source_id = str(engine.source_node_id(workflow))
    sampler_ids = {
        node_id for node_id, node in node_by_id.items()
        if node.get("type") == "frame_sampler"
    }
    if not sampler_ids:
        return workflow

    edges = list(dict.fromkeys(
        (str(edge[0]), str(edge[1])) for edge in workflow.get("edges", []) if len(edge) >= 2
    ))
    incoming = {node_id: [] for node_id in node_by_id}
    for source, target in edges:
        if source in node_by_id and target in node_by_id:
            incoming[target].append(source)
    # Workflows are editor DAGs; this order also makes nested samplers count
    # only frames that actually arrive through an upstream passing sampler.
    order = TopologicalSorter(incoming).static_order()

    reachable = {source_id}
    blocked = set()
    for node_id in order:
        if node_id == source_id:
            continue
        arrived = any(parent in reachable for parent in incoming[node_id])
        node = node_by_id[node_id]
        if not node.get("enabled", True) and node.get("type") != "frame_sampler":
            arrived = False
        if not arrived:
            continue
        if node_id in sampler_ids and node.get("enabled", True):
            state = runtime.setdefault(node_id, {"inputFrames": 0, "outputFrames": 0, "lastPass": None, "startedAt": now})
            state["inputFrames"] = int(state.get("inputFrames", 0)) + 1
            fps = _sampler_target_fps(node)
            last_pass = state.get("lastPass")
            passed = fps <= 0 or last_pass is None or now - float(last_pass) >= (1.0 / fps) - 1e-9
            if passed:
                state["lastPass"] = now
                state["outputFrames"] = int(state.get("outputFrames", 0)) + 1
            else:
                blocked.add(node_id)
                continue
        reachable.add(node_id)

    view = copy.copy(workflow)
    view["edges"] = [edge for edge in edges if str(edge[0]) not in blocked]
    view["nodes"] = [dict(node) for node in nodes]
    reachable_ids = set(engine._reachable_node_ids(
        frozenset(
            str(node.get("id")) for node in nodes
            if node.get("enabled", True) or node.get("type") == "frame_sampler"
        ),
        tuple(view["edges"]),
        source_id,
    ))
    for node in view["nodes"]:
        if str(node.get("id")) not in reachable_ids and node.get("enabled", True):
            node["enabled"] = False
    view = engine.prepare_runtime_workflow(view)
    view.common_processing_ids = {
        str(node.get("id") or "")
        for node in engine.active_image_processing_nodes(workflow)
    }
    original_reachable = {
        str(node.get("id")) for node in nodes
        if node.get("enabled", True)
        and engine.has_active_path(workflow, source_id, str(node.get("id")))
    }
    original_leaves = {
        node_id for node_id in original_reachable
        if not any(target in original_reachable for source, target in edges if source == node_id)
    }
    if not original_leaves:
        view.auto_preview_enabled = True
    else:
        view.auto_preview_enabled = any(
            node_id in reachable_ids
            and node_id not in blocked
            for node_id in original_leaves
        )
    return view


def frame_sampler_stats(runtime: dict, now: float) -> dict:
    result = {}
    for node_id, state in runtime.items():
        input_frames = int(state.get("inputFrames", 0))
        output_frames = int(state.get("outputFrames", 0))
        started = state.setdefault("startedAt", now)
        elapsed = max(0.0, now - float(started))
        output_rate_count = max(0, output_frames - 1)
        result[str(node_id)] = {
            "inputFps": round(max(0, input_frames - 1) / elapsed, 3) if elapsed else 0.0,
            "outputFps": round(output_rate_count / elapsed, 3) if elapsed else 0.0,
            "inputFrames": input_frames,
            "outputFrames": output_frames,
            "droppedFrames": max(0, input_frames - output_frames),
        }
    return result


class StageQueue:
    """Bounded FIFO queue that can be closed to wake waiting stage threads.

    With ``drop_oldest=True`` a full queue discards its oldest item instead of
    blocking the producer, keeping live sources at bounded latency.
    """

    def __init__(self, maxsize: int, *, drop_oldest: bool = False) -> None:
        self._maxsize = max(1, int(maxsize or 1))
        self._items = deque()
        self._condition = Condition()
        self._closed = False
        self._drop_oldest = bool(drop_oldest)
        self._dropped = 0

    def put(self, value, stop_event: Event, timeout: float = 0.1) -> bool:
        with self._condition:
            if self._drop_oldest:
                if self._closed or stop_event.is_set():
                    return False
                while len(self._items) >= self._maxsize:
                    self._items.popleft()
                    self._dropped += 1
                self._items.append(value)
                self._condition.notify_all()
                return True
            while (
                len(self._items) >= self._maxsize
                and not self._closed
                and not stop_event.is_set()
            ):
                self._condition.wait(timeout)
            if self._closed or stop_event.is_set():
                return False
            self._items.append(value)
            self._condition.notify_all()
            return True

    def get(self, stop_event: Event, timeout: float = 0.1):
        with self._condition:
            while not self._items and not self._closed and not stop_event.is_set():
                self._condition.wait(timeout)
            if not self._items:
                return None
            value = self._items.popleft()
            self._condition.notify_all()
            return value

    def get_latest(self, stop_event: Event, timeout: float = 0.1):
        """Return the newest queued item, counting older ones as dropped."""
        with self._condition:
            while not self._items and not self._closed and not stop_event.is_set():
                self._condition.wait(timeout)
            if not self._items:
                return None
            self._dropped += len(self._items) - 1
            value = self._items[-1]
            self._items.clear()
            self._condition.notify_all()
            return value

    def get_latest_batch(
        self,
        stop_event: Event,
        max_items: int,
        *,
        timeout: float = 0.1,
        collect_timeout: float = 0.015,
    ) -> list:
        """Return at most ``max_items`` of the freshest queued values.

        Live inference can be slower than capture.  Keeping the newest batch
        preserves useful batching while discarding work that is already stale.
        """
        max_items = max(1, int(max_items or 1))
        first = self.get(stop_event, timeout=timeout)
        if first is None:
            return []
        batch = [first]
        deadline = time.monotonic() + max(0.0, collect_timeout)
        with self._condition:
            while len(batch) < max_items and not self._closed and not stop_event.is_set():
                while self._items and len(batch) < max_items:
                    batch.append(self._items.popleft())
                if len(batch) >= max_items:
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(min(remaining, timeout))

            combined = batch + list(self._items)
            if len(combined) > max_items:
                self._dropped += len(combined) - max_items
                combined = combined[-max_items:]
            self._items.clear()
            self._condition.notify_all()
            return combined

    def get_batch(
        self,
        stop_event: Event,
        max_items: int,
        *,
        timeout: float = 0.1,
        collect_timeout: float = 0.015,
    ) -> list:
        first = self.get(stop_event, timeout=timeout)
        if first is None:
            return []
        batch = [first]
        max_items = max(1, int(max_items or 1))
        deadline = time.monotonic() + max(0.0, collect_timeout)
        with self._condition:
            while len(batch) < max_items:
                while self._items and len(batch) < max_items:
                    batch.append(self._items.popleft())
                if len(batch) >= max_items or self._closed or stop_event.is_set():
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(min(remaining, timeout))
            self._condition.notify_all()
        return batch

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    @property
    def closed(self) -> bool:
        with self._condition:
            return self._closed

    @property
    def dropped(self) -> int:
        with self._condition:
            return self._dropped

    def qsize(self) -> int:
        with self._condition:
            return len(self._items)


def _is_live_source(input_config: dict) -> bool:
    """Live sources produce frames on their own clock, so backlog means latency.

    RTSP/HTTP stream URLs arrive with sourceType "camera" (see
    engine.normalize_camera_source), so they are covered by the camera branch.
    """
    source_type = str(input_config.get("sourceType", "camera") or "camera").lower()
    return source_type in ("camera", "daheng")


class LatestSlot:
    """Thread-safe latest-value slot with stale-value overwrite semantics."""

    def __init__(self) -> None:
        self._condition = Condition()
        self._seq = 0
        self._value = None
        self._closed = False

    def put(self, value) -> int:
        with self._condition:
            self._seq += 1
            self._value = value
            self._condition.notify_all()
            return self._seq

    def get_after(self, last_seq: int, stop_event: Event, timeout: float = 0.1):
        with self._condition:
            while self._seq <= last_seq and not self._closed and not stop_event.is_set():
                self._condition.wait(timeout)
            if self._seq > last_seq and not stop_event.is_set():
                return self._seq, self._value
            if self._seq <= last_seq or self._closed or stop_event.is_set():
                return last_seq, None
            return self._seq, self._value

    def snapshot(self):
        with self._condition:
            return self._seq, self._value

    @property
    def closed(self) -> bool:
        with self._condition:
            return self._closed

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()


class PresentationBuffer:
    """Small per-preview jitter buffer consumed as quickly as frames arrive."""

    def __init__(self, maxsize: int = 3) -> None:
        self._maxsize = max(1, int(maxsize or 1))
        self._condition = Condition()
        self._frames: dict[str, deque] = {}
        self._closed = False
        self._dropped = 0

    def put(self, preview_id: str, frame) -> bool:
        with self._condition:
            if self._closed:
                return False
            frames = self._frames.setdefault(preview_id, deque())
            while len(frames) >= self._maxsize:
                frames.popleft()
                self._dropped += 1
            frames.append(frame)
            self._condition.notify_all()
            return True

    def take(self, preview_id: str):
        with self._condition:
            frames = self._frames.get(preview_id)
            if not frames:
                return None
            return frames.popleft()

    def wait(self, timeout: float) -> None:
        with self._condition:
            if not self._closed:
                self._condition.wait(max(0.0, timeout))

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    @property
    def dropped(self) -> int:
        with self._condition:
            return self._dropped

    def qsize(self) -> int:
        with self._condition:
            return sum(len(frames) for frames in self._frames.values())


class CCTVStreamWatchdog:
    """Stream liveness and tamper watchdog for IP Camera and live RTSP feeds."""

    def __init__(self, config: dict, input_node: dict, emit_log_fn, emit_debug_fn) -> None:
        self.config = config
        self.input_node = input_node
        self.emit_log = emit_log_fn
        self.emit_debug = emit_debug_fn
        self.is_live_cctv = bool(config.get("streamUrl")) or input_node.get("type") == "ip_camera"
        self.detect_freeze = bool(config.get("detectFreeze", True))
        self.freeze_threshold = max(1.0, float(config.get("freezeThresholdSeconds", 3.0) or 3.0))
        self.detect_tamper = bool(config.get("detectTamper", True))
        self.tamper_dark_thresh = float(config.get("tamperDarkThreshold", 6.0) or 6.0)
        self.tamper_bright_thresh = float(config.get("tamperBrightThreshold", 248.0) or 248.0)
        self.last_thumb = None
        self.last_motion_time = time.monotonic()
        self.freeze_alert_active = False
        self.tamper_dark_active = False
        self.tamper_bright_active = False

    def check(self, frame) -> None:
        if not self.is_live_cctv or frame is None or not getattr(frame, "shape", None) or len(frame.shape) < 2:
            return
        now_sec = time.monotonic()
        try:
            import cv2
            import numpy as np
            thumb_gray = cv2.cvtColor(
                cv2.resize(frame, (160, 120), interpolation=cv2.INTER_NEAREST),
                cv2.COLOR_BGR2GRAY
            )
            if self.detect_tamper:
                mean_lum = float(np.mean(thumb_gray))
                if mean_lum < self.tamper_dark_thresh:
                    if not self.tamper_dark_active:
                        self.tamper_dark_active = True
                        self.emit_log(f"WARNING: IP Camera tamper alert! Lens covered/dark (luminance {mean_lum:.1f} < {self.tamper_dark_thresh:.1f})")
                        self.emit_debug(self.input_node, state="warning", message=f"Camera tamper: lens covered/dark ({mean_lum:.1f})", force=True)
                else:
                    if self.tamper_dark_active:
                        self.tamper_dark_active = False
                        self.emit_log(f"INFO: IP Camera normal lighting restored ({mean_lum:.1f})")

                if mean_lum > self.tamper_bright_thresh:
                    if not self.tamper_bright_active:
                        self.tamper_bright_active = True
                        self.emit_log(f"WARNING: IP Camera tamper alert! Lens blinded/glare (luminance {mean_lum:.1f} > {self.tamper_bright_thresh:.1f})")
                        self.emit_debug(self.input_node, state="warning", message=f"Camera tamper: lens blinded ({mean_lum:.1f})", force=True)
                else:
                    if self.tamper_bright_active:
                        self.tamper_bright_active = False

            if self.detect_freeze:
                if self.last_thumb is not None:
                    diff = float(np.mean(np.abs(thumb_gray.astype(np.float32) - self.last_thumb.astype(np.float32))))
                    if diff > 0.15:
                        self.last_motion_time = now_sec
                        if self.freeze_alert_active:
                            self.freeze_alert_active = False
                            self.emit_log("INFO: IP Camera video stream resumed motion.")
                    else:
                        if not self.freeze_alert_active and (now_sec - self.last_motion_time) >= self.freeze_threshold:
                            self.freeze_alert_active = True
                            self.emit_log(f"WARNING: IP Camera stream frozen! Identical frames for >{self.freeze_threshold:.1f}s")
                            self.emit_debug(self.input_node, state="warning", message=f"Stream frozen for >{self.freeze_threshold:.1f}s", force=True)
                self.last_thumb = thumb_gray
        except Exception:
            pass


class StageFailure:
    def __init__(self) -> None:
        self._lock = Lock()
        self.error: BaseException | None = None
        self.traceback_text = ""

    def set(self, exc: BaseException) -> None:
        with self._lock:
            if self.error is None:
                self.error = exc
                self.traceback_text = traceback.format_exc()

    def get(self) -> BaseException | None:
        with self._lock:
            return self.error


def performance_status_snapshot(
    stats: dict,
    previous: dict,
    queues: dict[str, object],
    elapsed: float,
) -> dict:
    """Report completed packets separately from inference calls and previews.

    ``processedFps`` counts each packet once after tracking, classification and
    output submission, even when a workflow has several models or previews.
    """
    elapsed = max(float(elapsed or 0.0), 1e-9)
    preview_frames = int(stats.get("preview_frames", 0) or 0)
    captured = int(stats.get("captured", 0) or 0)
    detected = int(stats.get("detected", 0) or 0)
    latency_sum = float(stats.get("latency_ms_sum", 0.0) or 0.0)
    latency_frames = int(stats.get("latency_frames", 0) or 0)

    last_preview_frames = int(previous.get("preview_frames", 0) or 0)
    last_captured = int(previous.get("captured", 0) or 0)
    last_detected = int(previous.get("detected", 0) or 0)
    last_latency_sum = float(previous.get("latency_ms_sum", 0.0) or 0.0)
    last_latency_frames = int(previous.get("latency_frames", 0) or 0)
    last_dropped = int(previous.get("dropped", 0) or 0)

    queue_sizes = {}
    queue_drops = {}
    for name, queue in queues.items():
        dropped = int(getattr(queue, "dropped", 0) or 0)
        try:
            size = int(queue.qsize())
        except Exception:  # noqa: BLE001 - metric collection should not break a run
            size = 0
        queue_sizes[name] = size
        queue_drops[name] = dropped

    total_dropped = sum(queue_drops.values())
    interval_latency_frames = latency_frames - last_latency_frames
    latency_ms = (
        (latency_sum - last_latency_sum) / interval_latency_frames
        if interval_latency_frames > 0
        else 0.0
    )
    capture_fps = (captured - last_captured) / elapsed
    detection_fps = (detected - last_detected) / elapsed
    preview_fps = (preview_frames - last_preview_frames) / elapsed
    dropped_per_sec = (total_dropped - last_dropped) / elapsed

    return {
        "captureFps": round(capture_fps, 1),
        "detectionFps": round(detection_fps, 1),
        "processedFps": round(interval_latency_frames / elapsed, 1),
        "previewFps": round(preview_fps, 1),
        "latencyMs": round(latency_ms),
        "droppedPerSec": round(dropped_per_sec, 1),
        "totalDropped": total_dropped,
        "queueSizes": queue_sizes,
        "queueDrops": queue_drops,
        "fps": round(preview_fps),
    }


class WorkflowRunner:
    """Runs a workflow on a background thread and reports through callbacks.

    Mirrors the control flow of ``main.WorkflowRunner`` but is decoupled from the
    HTTP server and from ``cv2.imshow``. Frames are handed to ``on_frame`` so the
    GUI can paint them; logs, events, and status go to their respective
    callbacks.
    """

    def __init__(
        self,
        on_log: LogCallback | None = None,
        on_event: EventCallback | None = None,
        on_status: StatusCallback | None = None,
        on_frame: FrameCallback | None = None,
        on_node_debug: NodeDebugCallback | None = None,
        *,
        native_preview: bool = False,
    ) -> None:
        self._on_log = on_log or _noop
        self._on_event = on_event or _noop
        self._on_status = on_status or _noop
        self._on_frame = on_frame or _noop
        self._on_node_debug = on_node_debug or _noop
        self._native_preview = native_preview

        self._lock = Lock()
        self._stop_event = Event()
        self._python_last_errors = {}
        self._thread: Thread | None = None
        self._debug_enabled = False
        self._node_debug_last_emit: dict[str, float] = {}
        self._database_outputs: list[tuple[dict, DatabaseWriter]] = []
        self._status = {
            "running": False,
            "state": "idle",
            "fps": 0,
            "objectCount": 0,
            "captureFps": 0,
            "detectionFps": 0,
            "processedFps": 0,
            "previewFps": 0,
            "latencyMs": 0,
            "droppedPerSec": 0,
            "totalDropped": 0,
            "queueSizes": {},
            "queueDrops": {},
            "model": None,
            "device": "CPU",
            "error": None,
            "frameSamplers": {},
            "pythonScripts": {},
        }

    def _python_script_context(self, workflow: dict) -> dict:
        statuses = {}
        for node in workflow.get("nodes", []):
            if node.get("type") != "python_script":
                continue
            node_id = str(node.get("id") or "python_script")
            enabled = bool(node.get("enabled", True))
            statuses[node_id] = {
                "state": "idle" if enabled else "bypassed",
                "processedFrames": 0,
                "errorCount": 0,
                "lastDurationMs": 0,
                "lastRunAt": None,
                "error": None,
                "logs": "",
            }
        context = {
            "runners": {},
            "errors": {},
            "lock": RLock(),
            "stop_event": self._stop_event,
            "statuses": statuses,
            "last_errors": {},
            "callback": self._python_script_notify,
        }
        self._set_status(pythonScripts=copy.deepcopy(statuses))
        return context

    def _python_script_notify(self, node, **fields) -> None:
        node_id = str(node.get("id") or node.get("type") or "python_script")
        with self._lock:
            scripts = self._status.setdefault("pythonScripts", {})
            status = scripts.setdefault(node_id, {
                "state": "idle", "processedFrames": 0, "errorCount": 0,
                "lastDurationMs": 0, "lastRunAt": None, "error": None, "logs": "",
            })
            state = fields.get("state")
            if state:
                status["state"] = state
            elif not fields.get("error"):
                status["state"] = "success"
                status["processedFrames"] += 1
            if fields.get("error"):
                status["errorCount"] += 1
                status["error"] = str(fields["error"])
            elif state in ("running", "starting"):
                status["error"] = None
            if "logs" in fields:
                status["logs"] = str(fields.get("logs") or "")[-4096:]
            if "durationMs" in fields:
                status["lastDurationMs"] = round(float(fields.get("durationMs") or 0), 2)
            if state in ("success", "error", "timeout") or (not state and not fields.get("error")):
                status["lastRunAt"] = time.time()
            snapshot = copy.deepcopy(scripts)
        self._set_status(pythonScripts=snapshot)
        error = fields.get("error")
        if error:
            previous = getattr(self, "_python_last_errors", {}).get(node_id)
            if previous != str(error):
                self._python_last_errors = getattr(self, "_python_last_errors", {})
                self._python_last_errors[node_id] = str(error)
                self._emit_log(f"[Python {node_id}] {error}")
        elif fields.get("logs"):
            self._emit_log(f"[Python {node_id}] {str(fields['logs'])[-4096:]}")

    @staticmethod
    def _close_python_scripts(context: dict) -> None:
        for runner in list((context or {}).get("runners", {}).values()):
            try:
                runner[1].close()
            except Exception:
                traceback.print_exc()
        if context:
            context.get("runners", {}).clear()

    # -- public control -------------------------------------------------
    def is_running(self) -> bool:
        with self._lock:
            return bool(self._status["running"])

    def start(self, workflow: dict, *, debug: bool = False) -> None:
        self.stop()
        workflow = engine.prepare_runtime_workflow(engine.normalize_workflow(workflow))
        if not engine.active_input_node(workflow):
            raise ValueError("Input node is disabled.")

        self._stop_event = Event()
        self._debug_enabled = debug
        self._node_debug_last_emit = {}
        self._database_outputs = []
        self._set_status(
            running=True,
            state="starting",
            fps=0,
            objectCount=0,
            captureFps=0,
            detectionFps=0,
            processedFps=0,
            previewFps=0,
            latencyMs=0,
            droppedPerSec=0,
            totalDropped=0,
            queueSizes={},
            queueDrops={},
            model=None,
            device="CPU",
            error=None,
            errorTraceback="",
            frameSamplers={},
            pythonScripts={},
        )
        self._python_context = self._python_script_context(workflow)
        self._emit_log("Workflow launched from desktop Run button")
        self._emit_log("Starting workflow runner")
        self._thread = Thread(target=self._run, args=(workflow,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        thread = self._thread
        if thread and thread.is_alive():
            self._stop_event.set()
            thread.join(timeout=5)
        self._thread = None
        with self._lock:
            if self._status["state"] != "error":
                self._status.update(
                    {
                        "running": False,
                        "state": "stopped",
                        "fps": 0,
                        "objectCount": 0,
                        "captureFps": 0,
                        "detectionFps": 0,
                        "processedFps": 0,
                        "previewFps": 0,
                        "latencyMs": 0,
                        "droppedPerSec": 0,
                    }
                )
                snapshot = dict(self._status)
        # emit outside the lock to avoid re-entrancy
        if not (thread and thread.is_alive()):
            self._on_status(self.status())

    def status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def update_workflow(self, workflow: dict) -> None:
        """Update node configurations dynamically on the running pipeline."""
        if not isinstance(workflow, dict):
            return
        if hasattr(self, "_active_workflow") and isinstance(self._active_workflow, dict):
            self._active_workflow["nodes"] = workflow.get("nodes", [])
            self._active_workflow["edges"] = workflow.get("edges", [])

    def reset_counter(self, node_id: str | None = None, line_id: str | None = None) -> None:
        """Reset object or line counter counts."""
        rt = getattr(self, "_event_runtime", None)
        if isinstance(rt, dict):
            if node_id:
                state = rt.get(node_id)
                if isinstance(state, dict):
                    if line_id and "lines" in state and line_id in state["lines"]:
                        l_state = state["lines"][line_id]
                        l_state["count_in"] = 0
                        l_state["count_out"] = 0
                        l_state["positions"] = {}
                        l_state["last_seen"] = {}
                        l_state["last_event"] = {}
                        l_state["last_event_time"] = {}
                        state["total_in"] = sum(l.get("count_in", 0) for l in state["lines"].values())
                        state["total_out"] = sum(l.get("count_out", 0) for l in state["lines"].values())
                        state["count_in"] = state["total_in"]
                        state["count_out"] = state["total_out"]
                    else:
                        state["count_in"] = 0
                        state["count_out"] = 0
                        state["total_in"] = 0
                        state["total_out"] = 0
                        state["total_count"] = 0
                        state["class_counts"] = {}
                        state["positions"] = {}
                        state["last_seen"] = {}
                        state["last_event"] = {}
                        state["last_event_time"] = {}
                        state["counted"] = {}
                        state["auto_tracks"] = {}
                        state["_next_auto_id"] = 1
                        for l_state in state.get("lines", {}).values():
                            l_state["count_in"] = 0
                            l_state["count_out"] = 0
                            l_state["positions"] = {}
                            l_state["last_seen"] = {}
                            l_state["last_event"] = {}
                            l_state["last_event_time"] = {}
            else:
                for state in rt.values():
                    if isinstance(state, dict):
                        state["count_in"] = 0
                        state["count_out"] = 0
                        state["total_in"] = 0
                        state["total_out"] = 0
                        state["total_count"] = 0
                        state["class_counts"] = {}
                        state["positions"] = {}
                        state["last_seen"] = {}
                        state["last_event"] = {}
                        state["last_event_time"] = {}
                        state["counted"] = {}
                        state["auto_tracks"] = {}
                        state["_next_auto_id"] = 1
                        for l_state in state.get("lines", {}).values():
                            l_state["count_in"] = 0
                            l_state["count_out"] = 0
                            l_state["positions"] = {}
                            l_state["last_seen"] = {}
                            l_state["last_event"] = {}
                            l_state["last_event_time"] = {}

    # -- worker ---------------------------------------------------------
    def _run(self, workflow: dict) -> None:
        try:
            with _torch_thread_scope(workflow):
                self._run_pipeline(workflow)
        except Exception as exc:
            # Include invalid thread settings and scope setup/restore errors in
            # the same GUI error reporting as pipeline initialization failures.
            error = engine.exception_message(exc)
            self._set_status(running=False, state="error", error=error,
                             errorTraceback=traceback.format_exc())
            self._emit_event("Workflow error", error)
            self._emit_log(f"ERROR: {error}")

    def _run_pipeline(self, workflow: dict) -> None:
        import cv2

        try:
            # Processing, tracking, and preview threads all run cv2 ops
            # concurrently; the default per-op pool oversubscribes the CPU
            # against torch and the stage threads themselves.
            cv2.setNumThreads(2)
        except Exception:  # noqa: BLE001 - tuning only, never fatal
            pass

        input_source = None
        source_id = engine.source_node_id(workflow)
        input_config = (engine.active_input_node(workflow) or {}).get("config", {})
        frame_queue_size = max(1, min(512, int(input_config.get("frameQueueSize", 64) or 64)))
        drop_frames = _is_live_source(input_config) and bool(input_config.get("dropFrames", True))
        if drop_frames:
            # Bound worst-case pipeline depth; also overrides stale saved
            # workflows that still carry the old frameQueueSize default of 64.
            frame_queue_size = min(frame_queue_size, 8)
        raw_queue = StageQueue(frame_queue_size, drop_oldest=drop_frames)
        processed_queue = StageQueue(frame_queue_size, drop_oldest=drop_frames)
        detection_queue = StageQueue(frame_queue_size, drop_oldest=drop_frames)
        tracking_queue = StageQueue(frame_queue_size, drop_oldest=drop_frames)
        presentation_buffer: PresentationBuffer | None = None
        stage_failure = StageFailure()
        stage_threads: list[Thread] = []
        video_outputs: dict[str, engine.OpenCVVideoOutput] = {}
        native_preview = NativePreviewDisplay(cv2) if self._native_preview else None
        database_outputs: list[tuple[dict, DatabaseWriter]] = []
        run_status = "stopped"
        stats_lock = Lock()
        stats = {
            "preview_frames": 0,
            "object_count": 0,
            "captured": 0,
            "detected": 0,
            "latency_ms_sum": 0.0,
            "latency_frames": 0,
        }
        sampler_runtime: dict = {}
        base_workflow = workflow
        logic_runtime: dict = {}
        event_runtime: dict = {}
        self._event_runtime = event_runtime
        self._active_workflow = workflow
        logic_lock = Lock()
        preview_processing_runtime: dict = {"__python_scripts": self._python_context}
        detector_processes: dict = {}

        def fail_safe(name: str, target) -> None:
            try:
                target()
            except DetectorProcessStopped:
                # User stop interrupts pending IPC/model loading; it is not a
                # failed workflow. The owning run closes all processes below.
                return
            except Exception as exc:  # noqa: BLE001 - propagated to the runner thread
                stage_failure.set(exc)
                self._emit_log(f"ERROR: {name} thread failed: {engine.exception_message(exc)}")
                self._stop_event.set()
                raw_queue.close()
                processed_queue.close()
                detection_queue.close()
                tracking_queue.close()

        def start_stage(name: str, target) -> None:
            thread = Thread(target=lambda: fail_safe(name, target), name=f"visonode-{name}", daemon=True)
            stage_threads.append(thread)
            thread.start()

        def on_logic_debug(node, input_items, output_items, duration_ms, passed, target_id) -> None:
            self._emit_node_debug(
                node,
                state="success" if passed else "blocked",
                input_summary=_detections_summary(input_items),
                output_summary=_detections_summary(output_items),
                duration_ms=duration_ms,
                sample={
                    "targetNodeId": target_id,
                    "passed": passed,
                    "input": _detection_sample(input_items),
                    "output": _detection_sample(output_items),
                },
                message="Condition passed" if passed else "Condition blocked this frame",
            )

        try:
            input_node = engine.active_input_node(workflow)
            input_source = engine.OpenCVInputSource(cv2, input_node.get("config", {}))
            source_label, actual_width, actual_height = input_source.open()
            self._emit_log(f"Opened {source_label} ({actual_width}x{actual_height})")
            preview_nodes = _active_preview_nodes(workflow, source_id)
            presentation_capacity = _presentation_capacity(
                input_config, is_static=input_source.is_static, drop_frames=drop_frames,
            )
            if presentation_capacity and preview_nodes:
                presentation_buffer = PresentationBuffer(maxsize=presentation_capacity)
                if input_config.get("asyncPreview", False):
                    self._emit_log(
                        "Asynchronous preview enabled: display may skip frames. "
                        + ("Source processing remains FIFO without dropping frames."
                           if not drop_frames else "Live-source frame dropping follows the input setting.")
                    )
            database_outputs = self._open_database_outputs(workflow, source_id)
            self._database_outputs = database_outputs

            inference_nodes = engine.active_inference_nodes(workflow)
            frame_inference_nodes = engine.active_frame_inference_nodes(workflow)
            frame_inference_plan = _frame_inference_plan(workflow, frame_inference_nodes)
            detection_crop_bindings = engine.active_pretracking_detection_crop_bindings(workflow)
            loaded_models = []
            device_labels = []
            if inference_nodes:
                for inference_node in inference_nodes:
                    config = inference_node.get("config", {})
                    eng = config.get("engine", "rfdetr")
                    if eng not in ("sam3", "rfdetr", "rfdetr_tensorrt", "rfdetr_onnx", "convnext", "efficientad", "ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                        raise RuntimeError(
                            f"Backend runtime does not support inference engine '{eng}'."
                        )
                    if eng == "sam3" and inference_node.get("type") != "segmenter":
                        raise RuntimeError(
                            "SAM 3 is available only on the Object Segmentation node."
                        )
                    if eng == "rfdetr" and inference_node.get("type") not in ("detector", "segmenter"):
                        raise RuntimeError(
                            "RF-DETR is available only on Object Detection and Object Segmentation nodes."
                        )
                    if eng in ("rfdetr_tensorrt", "rfdetr_onnx") and inference_node.get("type") not in ("detector", "segmenter"):
                        raise RuntimeError(
                            "RF-DETR optimized models are available only on Object Detection and Object Segmentation nodes."
                        )
                    if eng == "efficientad" and inference_node.get("type") != "efficientad":
                        raise RuntimeError("EfficientAD is available only on the Anomaly Detection node.")
                    if eng == "convnext" and inference_node.get("type") != "classifier":
                        raise RuntimeError(
                            "ConvNeXt is available only on the Image Classification node."
                        )
                    model_name = engine.inference_model_name(inference_node)
                    device, device_label = engine.resolve_inference_device(config)
                    task_labels = {"segmenter": "segmentation", "classifier": "classification", "efficientad": "EfficientAD anomaly inspection"}
                    task_label = task_labels.get(inference_node.get("type"), "detector")
                    if eng == "sam3":
                        task_label = f"SAM 3 {task_label}"
                    elif eng == "rfdetr":
                        task_label = f"RF-DETR {task_label}"
                    elif eng == "rfdetr_onnx":
                        task_label = f"RF-DETR ONNX {task_label}"
                    elif eng == "rfdetr_tensorrt":
                        task_label = f"RF-DETR TensorRT {task_label}"
                    elif eng == "convnext":
                        task_label = f"ConvNeXt {task_label}"
                    elif eng in ("ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                        task_label = f"Custom Model ({eng}) {task_label}"
                    self._emit_log(f"Loading {task_label} model {model_name}")
                    self._emit_log(f"Using inference device {device_label}")
                    load_started_at = time.monotonic()
                    if eng == "sam3":
                        concepts = ", ".join(engine.sam3_concepts(config))
                        self._emit_log(f"SAM 3 concept prompt(s): {concepts}")
                        engine.load_sam3_processor(config, device)
                    elif eng == "rfdetr":
                        rfdetr_model_name = config.get("rfdetrModel") or engine.default_rfdetr_model(inference_node.get("type", "detector"))
                        loaded_model = engine.load_rfdetr_model(
                            rfdetr_model_name,
                            device,
                            engine.rfdetr_checkpoint_path(config),
                            config.get("rfdetrImageSize", engine.RFDETR_NATIVE_IMAGE_SIZE),
                            bool(config.get("rfdetrHalfPrecision", True)),
                            expected_node_type=inference_node.get("type"),
                        )
                        optimization_error = getattr(
                            loaded_model, "_visonode_optimization_error", None
                        )
                        if optimization_error:
                            self._emit_log(
                                "RF-DETR optimization was unavailable; using regular "
                                f"inference: {optimization_error}"
                            )
                        else:
                            resolution = getattr(
                                getattr(loaded_model, "model", None), "resolution", "native"
                            )
                            precision = getattr(loaded_model, "_visonode_precision", "FP32")
                            self._emit_log(
                                "RF-DETR inference optimized and warmed up "
                                f"(JIT {precision}, {resolution}x{resolution})"
                            )
                    elif eng == "rfdetr_onnx":
                        loaded_model = engine.load_rfdetr_onnx(config)
                        self._emit_log("RF-DETR ONNX Runtime model loaded")
                    elif eng == "rfdetr_tensorrt":
                        loaded_model = _load_tensorrt_for_run(config, detector_processes, self._stop_event)
                        self._emit_log(
                            "RF-DETR TensorRT engine loaded "
                            f"({loaded_model.input_shape[2]}x{loaded_model.input_shape[3]})"
                        )
                    elif eng == "efficientad":
                        engine.load_efficientad_model(config, device)
                    elif eng in ("ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                        try:
                            from .custom_model_runtime import CustomModelRunner
                        except ImportError:
                            from custom_model_runtime import CustomModelRunner
                        runner = CustomModelRunner.get_or_load(config, device=device)
                        self._emit_log(f"Custom model loaded ({runner.detected_engine}, classes: {len(runner.classes)})")
                    else:
                        loaded_model = engine.load_convnext_model(config, device)
                        self._emit_log(
                            (
                                "ConvNeXt ImageNet pretrained model loaded "
                                if loaded_model._visonode_pretrained
                                else "ConvNeXt checkpoint loaded "
                            )
                            + f"({len(loaded_model._visonode_classes)} classes, "
                            f"{loaded_model._visonode_image_size}x{loaded_model._visonode_image_size}, "
                            f"{loaded_model._visonode_precision})"
                        )
                    _, effective_device_label = engine.resolve_inference_device(config)
                    if effective_device_label != device_label:
                        self._emit_log(
                            f"{model_name}: GPU execution failed; continuing on {effective_device_label}"
                        )
                    device_label = effective_device_label
                    load_seconds = time.monotonic() - load_started_at
                    loaded_models.append(model_name)
                    device_labels.append(device_label)
                    self._emit_log(f"Loaded {task_label} model {model_name} in {load_seconds:.1f}s")
                    self._emit_node_debug(
                        inference_node,
                        state="ready",
                        output_summary={"kind": "model", "name": model_name, "device": device_label},
                        duration_ms=load_seconds * 1000,
                        message="Model loaded",
                        force=True,
                    )
                device_status = (
                    device_labels[0] if len(set(device_labels)) == 1 else "Mixed devices"
                )
                self._set_status(
                    state="running", model=", ".join(loaded_models), device=device_status
                )
                self._refresh_inference_device_status(inference_nodes, device_labels)
            else:
                self._set_status(state="running")
                self._emit_log("No inference node is active; streaming input frames only")

            self._emit_event(
                "Workflow running",
                "Python is loading, processing, and displaying frames with a threaded pipeline.",
            )
            preview_mode = "native OpenCV preview" if native_preview else "GUI preview transport"
            self._emit_log(
                "Workflow running with threaded capture, processing, inference, tracking, "
                f"and preview stages ({preview_mode})"
            )
            if inference_nodes:
                configured_detection_batch = max(
                    1,
                    min(
                        frame_queue_size,
                        max(
                            int(node.get("config", {}).get("batchSize", 1) or 1)
                            for node in inference_nodes
                        ),
                    ),
                )
                tracker_node_for_log = engine.active_tracking_node(workflow)
                configured_tracking_batch = max(
                    1,
                    min(
                        frame_queue_size,
                        int((tracker_node_for_log or {}).get("config", {}).get("batchSize", 1) or 1),
                    ),
                )
                queue_mode = " (live source: dropping oldest frames to stay real-time)" if drop_frames else ""
                self._emit_log(
                    f"Frame queue limit {frame_queue_size}{queue_mode}; detection batch size "
                    f"{configured_detection_batch}; tracking batch size {configured_tracking_batch}"
                )
            else:
                queue_mode = " (live source: dropping oldest frames to stay real-time)" if drop_frames else ""
                self._emit_log(f"Frame queue limit {frame_queue_size}{queue_mode}")

            def capture_stage() -> None:
                frame_id = 0
                first_frame_logged = False
                watchdog = CCTVStreamWatchdog(input_config, input_node, self._emit_log, self._emit_node_debug)
                while not self._stop_event.is_set():
                    read_started_at = time.monotonic()
                    ok, frame = input_source.read()
                    duration_ms = (time.monotonic() - read_started_at) * 1000
                    if not ok:
                        if input_source.is_exhausted:
                            self._emit_log("Finite video input completed")
                            break
                        self._emit_node_debug(
                            input_node,
                            state="error",
                            message="Input frame could not be read.",
                            duration_ms=duration_ms,
                            force=True,
                        )
                        raise RuntimeError("Input frame could not be read.")
                    watchdog.check(frame)
                    frame_id += 1
                    packet = FramePacket(
                        frame_id=frame_id,
                        frame=frame,
                        timestamp=time.monotonic(),
                        duration_ms=duration_ms,
                        source_label=source_label,
                    )
                    with stats_lock:
                        stats["captured"] += 1
                    if not raw_queue.put(packet, self._stop_event):
                        break
                    if self._debug_enabled:
                        frame_summary = _frame_summary(frame)
                        self._emit_node_debug(
                            input_node,
                            input_summary={"kind": "source", "label": source_label},
                            output_summary=frame_summary,
                            duration_ms=duration_ms,
                            sample={"frame": frame_summary},
                        )
                    if not first_frame_logged:
                        first_frame_logged = True
                    if input_source.is_static:
                        if not bool(input_config.get("loop", True)):
                            break
                        # Pacing and backpressure for static image loop: wait if queue already has pending frames
                        while raw_queue.qsize() >= 2 and not self._stop_event.is_set():
                            time.sleep(0.04)
                        loop_fps = max(1.0, min(30.0, float(input_config.get("dahengFrameRate", 0) or 8.0)))
                        time.sleep(1.0 / loop_fps)
                raw_queue.close()

            def processing_stage() -> None:
                processing_runtime: dict = {"__python_scripts": self._python_context}
                last_sampler_status_at = 0.0

                def on_processing_debug(node, before_frame, after_frame, duration_ms) -> None:
                    self._emit_node_debug(
                        node,
                        input_summary=_frame_summary(before_frame),
                        output_summary=_frame_summary(after_frame),
                        duration_ms=duration_ms,
                        sample={
                            "inputFrame": _frame_summary(before_frame),
                            "outputFrame": _frame_summary(after_frame),
                        },
                    )

                while not self._stop_event.is_set():
                    packet = (
                        raw_queue.get_latest(self._stop_event)
                        if drop_frames
                        else raw_queue.get(self._stop_event)
                    )
                    if packet is None:
                        break
                    started_at = time.monotonic()
                    packet_workflow = sample_frame_workflow(base_workflow, sampler_runtime, time.monotonic())
                    frame = engine.apply_image_processing(
                        packet.frame,
                        packet_workflow,
                        processing_runtime,
                        processing_nodes=engine.active_image_processing_nodes(packet_workflow),
                        script_frames=packet.script_frames,
                        debug_callback=on_processing_debug if self._debug_enabled else None,
                    )
                    if not processed_queue.put(FramePacket(
                        frame_id=packet.frame_id,
                        frame=frame,
                        timestamp=packet.timestamp,
                        duration_ms=(time.monotonic() - started_at) * 1000,
                        source_label=packet.source_label,
                        workflow=packet_workflow,
                        script_frames=packet.script_frames,
                    ), self._stop_event):
                        break
                    status_now = time.monotonic()
                    if status_now - last_sampler_status_at >= 0.5:
                        last_sampler_status_at = status_now
                        self._set_status(frameSamplers=frame_sampler_stats(sampler_runtime, status_now))
                self._set_status(frameSamplers=frame_sampler_stats(sampler_runtime, time.monotonic()))
                processed_queue.close()

            def detection_stage() -> None:
                workflow = base_workflow
                inference_nodes = engine.active_inference_nodes(base_workflow)
                frame_inference_plan = _frame_inference_plan(base_workflow, engine.active_frame_inference_nodes(base_workflow))
                detection_crop_bindings = engine.active_pretracking_detection_crop_bindings(base_workflow)
                if not inference_nodes:
                    detection_queue.close()
                    return
                first_inference_logged = False
                last_slow_inference_at = 0.0
                last_terminal_detection_at = 0.0
                last_inference_by_node: dict[str, float] = {}
                frames_seen_by_node: dict[str, int] = {}
                detector_batch_size = max(
                    1,
                    min(
                        frame_queue_size,
                        max(
                            int(node.get("config", {}).get("batchSize", 1) or 1)
                            for node in inference_nodes
                        ),
                    ),
                )
                if any(node.get("type") == "frame_sampler" for node in base_workflow.get("nodes", [])):
                    detector_batch_size = 1  # ponytail: group by sampler mask later if batching matters.
                remaining_batch = []
                while not self._stop_event.is_set():
                    get_detection_batch = (
                        processed_queue.get_latest_batch if drop_frames else processed_queue.get_batch
                    )
                    if remaining_batch:
                        batch, remaining_batch = remaining_batch[:1], remaining_batch[1:]
                    else:
                        batch = get_detection_batch(
                            self._stop_event,
                            detector_batch_size,
                            timeout=0.1,
                            collect_timeout=0.02,
                        )
                        # A live edit can introduce sampling while this batch is collected.
                        if len(batch) > 1 and any(packet.workflow is not base_workflow for packet in batch):
                            batch, remaining_batch = batch[:1], batch[1:]
                    if not batch:
                        break
                    packet_workflow = batch[0].workflow or base_workflow
                    if packet_workflow is not workflow:
                        workflow = packet_workflow
                        inference_nodes = engine.active_inference_nodes(workflow)
                        frame_inference_plan = _frame_inference_plan(workflow, engine.active_frame_inference_nodes(workflow))
                        detection_crop_bindings = engine.active_pretracking_detection_crop_bindings(workflow)
                    now = time.monotonic()
                    detections_by_index: list[list[dict]] = [[] for _ in batch]
                    tracking_detections_by_index: list[list[dict]] = [
                        [] for _ in batch
                    ]
                    for inference_node, threshold, tracking_threshold, runtime_inference_node in frame_inference_plan:
                        config = inference_node.get("config", {})
                        node_id = str(inference_node.get("id") or inference_node.get("type") or "inference")
                        detect_every = max(1, int(config.get("detectEveryNFrames", 1) or 1))
                        max_fps = max(0.0, float(config.get("maxDetectionFps", 0) or 0))
                        if max_fps > 0:
                            min_interval = 1.0 / max_fps
                            if now - last_inference_by_node.get(node_id, 0.0) < min_interval:
                                continue
                        # Count frames seen per node instead of using frame_id:
                        # dropped frames leave gaps in frame_id, which would make
                        # the modulo skip irregularly.
                        seen = frames_seen_by_node.get(node_id, 0)
                        eligible_indices = []
                        for index in range(len(batch)):
                            if seen % detect_every == 0:
                                eligible_indices.append(index)
                            seen += 1
                        frames_seen_by_node[node_id] = seen
                        if not eligible_indices:
                            continue
                        branch_script_nodes = [
                            node for node in engine.active_image_processing_nodes_for_path(
                                workflow, engine.source_node_id(workflow), node_id,
                            ) if node.get("type") == "python_script"
                        ]
                        inference_frames = [batch[index].frame for index in eligible_indices]
                        if branch_script_nodes:
                            inference_frames = [
                                engine.apply_image_processing(
                                    batch[index].frame, workflow, processing_runtime,
                                    processing_nodes=branch_script_nodes,
                                    script_frames=batch[index].script_frames,
                                ) for index in eligible_indices
                            ]
                        eng = config.get("engine", "rfdetr")
                        inference_started_at = time.monotonic()
                        if eng == "sam3":
                            node_results = [
                                engine.run_sam3_frame(
                                    inference_frames[position],
                                    runtime_inference_node,
                                )
                                for position, index in enumerate(eligible_indices)
                            ]
                        elif eng == "rfdetr":
                            node_results = engine.run_rfdetr_batch(
                                inference_frames,
                                runtime_inference_node,
                            )
                        elif eng == "rfdetr_onnx":
                            node_results = engine.run_rfdetr_onnx_batch(
                                inference_frames,
                                runtime_inference_node,
                            )
                        elif eng == "rfdetr_tensorrt":
                            node_results = _run_tensorrt_for_run(
                                inference_frames,
                                runtime_inference_node,
                                detector_processes, self._stop_event,
                            )
                        elif eng == "efficientad":
                            node_results = engine.run_efficientad_batch(
                                inference_frames,
                                runtime_inference_node,
                            )
                        elif eng == "convnext":
                            node_results = engine.run_convnext_batch(
                                inference_frames,
                                runtime_inference_node,
                            )
                        elif eng in ("ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                            try:
                                from .custom_model_runtime import run_custom_model_frame
                            except ImportError:
                                from custom_model_runtime import run_custom_model_frame
                            node_results = [
                                run_custom_model_frame(inference_frames[position], runtime_inference_node)
                                for position, index in enumerate(eligible_indices)
                            ]
                        else:
                            raise RuntimeError(
                                f"Backend runtime does not support inference engine '{eng}'."
                            )

                        slicer_nodes = [n for n in workflow.get("nodes", []) if n.get("type") == "slicer" and n.get("enabled", True)]
                        if slicer_nodes and inference_node.get("type") in ("detector", "segmenter") and eng in ("ultralytics_yolo", "onnx_custom", "custom_auto"):
                            slicer = slicer_nodes[0]
                            iou_th = float(slicer.get("config", {}).get("iouThreshold", 0.45) or 0.45)
                            for r_idx, b_idx in enumerate(eligible_indices):
                                tiles = _generate_slicer_tiles(
                                    inference_frames[eligible_indices.index(b_idx)], slicer
                                )
                                if tiles:
                                    accumulated = list(node_results[r_idx])
                                    for tile_img, ox, oy, _, _ in tiles:
                                        t_dets = run_custom_model_frame(tile_img, runtime_inference_node)
                                        for td in t_dets:
                                            shifted = dict(td)
                                            shifted["x"] = float(shifted.get("x", 0)) + ox
                                            shifted["y"] = float(shifted.get("y", 0)) + oy
                                            accumulated.append(shifted)
                                    node_results[r_idx] = _merge_slicer_detections(accumulated, iou_th)

                        self._refresh_inference_device_status(inference_nodes, device_labels)
                        last_inference_by_node[node_id] = time.monotonic()
                        inference_seconds = time.monotonic() - inference_started_at
                        with stats_lock:
                            stats["detected"] += len(eligible_indices)
                        if not first_inference_logged:
                            first_inference_logged = True
                            self._emit_log(
                                f"First inference batch completed in {inference_seconds:.2f}s "
                                f"({len(eligible_indices)} frame(s))"
                            )
                        elif inference_seconds >= 2.0 and now - last_slow_inference_at >= 5:
                            last_slow_inference_at = now
                            self._emit_log(
                                f"Slow inference batch: {inference_seconds:.2f}s "
                                f"({len(eligible_indices)} frame(s))"
                            )
                        per_frame_ms = (inference_seconds * 1000) / max(1, len(eligible_indices))
                        inf_cfg = inference_node.get("config", {})
                        per_class_map = _parse_per_class_thresholds(inf_cfg.get("perClassThresholds", ""))
                        class_remap_map = _parse_class_remap(inf_cfg.get("classRemap", ""))
                        is_track_elig = inference_node.get("type") in ("detector", "segmenter")
                        for result_index, packet_index in enumerate(eligible_indices):
                            node_detections = node_results[result_index] if result_index < len(node_results) else []
                            kept_detections, tracking_detections = _filter_and_remap_detections(
                                node_detections,
                                threshold,
                                tracking_threshold,
                                is_track_elig,
                                per_class_map,
                                class_remap_map,
                            )
                            detections_by_index[packet_index].extend(kept_detections)
                            tracking_detections_by_index[packet_index].extend(
                                tracking_detections
                            )
                            if self._debug_enabled:
                                packet = batch[packet_index]
                                self._emit_node_debug(
                                    inference_node,
                                    input_summary=_frame_summary(packet.frame),
                                    output_summary=_detections_summary(kept_detections),
                                    duration_ms=per_frame_ms,
                                    sample={
                                        "threshold": threshold,
                                        "batchSize": len(eligible_indices),
                                        "detections": _detection_sample(kept_detections),
                                    },
                                )
                    crop_batches_by_index = [
                        engine.detection_crop_batches(
                            packet.frame, workflow, detections_by_index[index],
                        )
                        for index, packet in enumerate(batch)
                    ]
                    if self._debug_enabled:
                        for packet_index, crop_batches in enumerate(crop_batches_by_index):
                            for crop_node in engine.active_detection_crop_nodes(workflow):
                                crop_id = str(crop_node.get("id") or "detection_crop")
                                source_detections = [
                                    item for item in detections_by_index[packet_index]
                                    if item.get("kind") in ("detection", "segmentation")
                                ]
                                self._emit_node_debug(
                                    crop_node,
                                    input_summary=_detections_summary(source_detections),
                                    output_summary={
                                        "kind": "crops",
                                        "count": len(crop_batches.get(crop_id, [])),
                                    },
                                    duration_ms=0.0,
                                )
                    for crop_node, classifier_node in detection_crop_bindings:
                        classifier_id = _crop_schedule_id(crop_node, classifier_node)
                        eligible_indices = _eligible_crop_frame_indices(
                            classifier_node, detections_by_index,
                            frames_seen_by_node, last_inference_by_node, now,
                            schedule_id=classifier_id,
                        )
                        if not eligible_indices:
                            continue
                        inference_started_at = time.monotonic()
                        crop_results = engine.run_detection_crop_classifier_batch(
                            [batch[index].frame for index in eligible_indices],
                            [detections_by_index[index] for index in eligible_indices],
                            workflow,
                            crop_node,
                            classifier_node,
                            crops_by_frame=[
                                crop_batches_by_index[index].get(
                                    str(crop_node.get("id") or "detection_crop"), [],
                                )
                                for index in eligible_indices
                            ],
                        )
                        self._refresh_inference_device_status(inference_nodes, device_labels)
                        last_inference_by_node[classifier_id] = time.monotonic()
                        inference_seconds = time.monotonic() - inference_started_at
                        per_frame_ms = (inference_seconds * 1000) / max(1, len(eligible_indices))
                        for result_index, packet_index in enumerate(eligible_indices):
                            object_classifications = (
                                crop_results[result_index]
                                if result_index < len(crop_results)
                                else []
                            )
                            detections_by_index[packet_index].extend(object_classifications)
                            if self._debug_enabled:
                                self._emit_node_debug(
                                    classifier_node,
                                    input_summary={
                                        "kind": "crops",
                                        "count": len(object_classifications),
                                    },
                                    output_summary=_detections_summary(object_classifications),
                                    duration_ms=per_frame_ms,
                                    sample={
                                        "classifications": _detection_sample(object_classifications),
                                    },
                                )
                    for index, packet in enumerate(batch):
                        detections = detections_by_index[index]
                        if detections and now - last_terminal_detection_at >= 1:
                            last_terminal_detection_at = now
                            labels = ", ".join(
                                f"{item.get('class', 'object')}:{float(item.get('score', 0)):.2f}"
                                for item in detections[:6]
                            )
                            if len(detections) > 6:
                                labels = f"{labels}, +{len(detections) - 6} more"
                            self._emit_log(f"Detected {len(detections)} object(s): {labels}")
                        if not detection_queue.put(DetectionPacket(
                            frame_id=packet.frame_id,
                            frame=packet.frame,
                            detections=detections,
                            tracking_detections=tracking_detections_by_index[index],
                            filtered=detections,
                            crop_batches=crop_batches_by_index[index],
                            timestamp=packet.timestamp,
                            workflow=workflow,
                            script_frames=packet.script_frames,
                        ), self._stop_event):
                            return
                detection_queue.close()

            def tracking_stage() -> None:
                workflow = base_workflow
                if not inference_nodes:
                    tracking_queue.close()
                    return
                tracker_runtime: engine.ObjectTracker | None = None
                tracker_signature: str | None = None
                while not self._stop_event.is_set():
                    tracker_node = engine.active_tracking_node(workflow)
                    tracker_batch_size = max(
                        1,
                        min(
                            frame_queue_size,
                            int((tracker_node or {}).get("config", {}).get("batchSize", 1) or 1),
                        ),
                    )
                    get_tracking_batch = (
                        detection_queue.get_latest_batch if drop_frames else detection_queue.get_batch
                    )
                    batch = get_tracking_batch(
                        self._stop_event,
                        tracker_batch_size,
                        timeout=0.1,
                        collect_timeout=0.01,
                    )
                    if not batch:
                        break
                    for packet in batch:
                        workflow = packet.workflow or base_workflow
                        tracker_node = engine.active_tracking_node(workflow)
                        now = time.monotonic()
                        detections = packet.detections
                        tracking_detections = packet.tracking_detections
                        tracked: list[dict] = []
                        if tracker_node:
                            tracker_config = tracker_node.get("config", {})
                            signature = json.dumps(tracker_config, sort_keys=True)
                            if tracker_runtime is None or tracker_signature != signature:
                                tracker_runtime = engine.ObjectTracker(tracker_node)
                                tracker_signature = signature
                                self._emit_log(
                                    f"Object tracking enabled with {tracker_runtime.status_label()}"
                                )
                            tracker_id = str(tracker_node.get("id") or "tracker")
                            with logic_lock:
                                track_candidates = engine.apply_logic_nodes(
                                    workflow,
                                    tracker_id,
                                    engine.results_for_node(
                                        workflow,
                                        tracker_id,
                                        tracking_detections,
                                    ),
                                    logic_runtime,
                                    now,
                                    debug_callback=on_logic_debug if self._debug_enabled else None,
                                )
                            tracking_started_at = time.monotonic()
                            tracked = tracker_runtime.update(
                                track_candidates,
                                packet.frame,
                                frame_id=packet.frame_id,
                                timestamp=packet.timestamp,
                            )
                            if self._debug_enabled:
                                self._emit_node_debug(
                                    tracker_node,
                                    input_summary=_detections_summary(track_candidates),
                                    output_summary=_detections_summary(tracked),
                                    duration_ms=(time.monotonic() - tracking_started_at) * 1000,
                                    sample={"tracked": _detection_sample(tracked)},
                                )
                        # Keep tracker state warm while a sampler blocks this branch.

                        # Regular Detection Crop branches are materialized in
                        # the detection stage. Persist them here, alongside the
                        # event-driven crop writer below, before a later live
                        # pipeline stage can drop the frame.
                        _save_detection_crop_outputs(
                            cv2, workflow, packet.crop_batches,
                        )
                        # Only logic state is shared with previews. GPU inspection,
                        # crop copies and disk writes must not hold the preview lock.
                        event_results, event_crops, object_records, count_records = _process_track_event_nodes(
                            cv2,
                            packet.frame,
                            workflow,
                            detections,
                            tracked,
                            logic_runtime,
                            event_runtime,
                            now,
                            logic_lock=logic_lock,
                        )
                        detections.extend(event_results)
                        packet.crop_batches.update(event_crops)
                        logic_runtime["_event_runtime"] = event_runtime

                        filter_candidates = (
                            engine.results_for_node(workflow, "filter", detections, tracked)
                            if engine.active_filter_node(workflow)
                            else detections
                        )
                        filter_node = engine.active_filter_node(workflow)
                        if filter_node:
                            with logic_lock:
                                filter_candidates = engine.apply_logic_nodes(
                                    workflow,
                                    "filter",
                                    filter_candidates,
                                    logic_runtime,
                                    now,
                                    debug_callback=on_logic_debug if self._debug_enabled else None,
                                )
                        filter_started_at = time.monotonic()
                        f_shape = (packet.frame.shape[1], packet.frame.shape[0]) if hasattr(packet.frame, "shape") else None
                        filtered = engine.filter_detections(workflow, filter_candidates, frame_size=f_shape)
                        if filter_node and self._debug_enabled:
                            self._emit_node_debug(
                                filter_node,
                                input_summary=_detections_summary(filter_candidates),
                                output_summary=_detections_summary(filtered),
                                duration_ms=(time.monotonic() - filter_started_at) * 1000,
                                sample={"filtered": _detection_sample(filtered)},
                            )
                        if not tracking_queue.put(TrackingPacket(
                            frame_id=packet.frame_id,
                            frame=packet.frame,
                            detections=detections,
                            tracked=tracked,
                            filtered=filtered,
                            crop_batches=packet.crop_batches,
                            object_records=object_records,
                            count_records=count_records,
                            timestamp=packet.timestamp,
                            workflow=workflow,
                            script_frames=packet.script_frames,
                        ), self._stop_event):
                            return
                tracking_queue.close()

            def preview_stage() -> None:
                total_frame_index = 0
                last_alert_at = 0.0
                last_webhook_at: dict[str, float] = {}
                held_event_crops: dict[str, list[dict]] = {}
                held_event_annotations: dict[str, list[dict]] = {}
                held_crop_grids: dict = {}
                last_display_at: dict = {}
                video_output_initialized = False
                # Non-live file inputs display directly. Live inputs submit to
                # the separate presentation thread so slow display calls cannot
                # block the rest of the processing pipeline.
                last_poll_at = 0.0
                rolling_frame_buffer: deque[bytes] = deque(maxlen=90)
                recorded_loiter_tracks: set = set()

                while not self._stop_event.is_set():
                    if inference_nodes:
                        # Live sources show the newest completed frame; older
                        # queued frames count as dropped (also skipped in any
                        # saved video, which is inherently variable-rate live).
                        if drop_frames:
                            packet = tracking_queue.get_latest(self._stop_event, timeout=0.1)
                        else:
                            packet = tracking_queue.get(self._stop_event, timeout=0.1)
                        if packet is None:
                            break
                        frame = packet.frame
                        workflow = packet.workflow or base_workflow
                        frame_detections = packet.detections
                        frame_tracked = packet.tracked
                        frame_filtered = packet.filtered
                        frame_crop_batches = packet.crop_batches
                        frame_object_records = packet.object_records
                        frame_count_records = packet.count_records
                    else:
                        if drop_frames:
                            packet = processed_queue.get_latest(self._stop_event, timeout=0.1)
                        else:
                            packet = processed_queue.get(self._stop_event, timeout=0.1)
                        if packet is None:
                            break
                        frame = packet.frame
                        workflow = packet.workflow or base_workflow
                        frame_detections = []
                        frame_tracked = []
                        frame_filtered = []
                        frame_crop_batches = {}
                        frame_object_records = []
                        frame_count_records = []

                    if not video_output_initialized:
                        video_output_initialized = True
                        for preview_node in preview_nodes:
                            preview_id = str(preview_node.get("id") or "")
                            video_config = dict(preview_node.get("config", {}))
                            if (
                                len(preview_nodes) > 1
                                and video_config.get("saveVideo", False)
                                and not str(video_config.get("outputPath") or "").strip()
                            ):
                                safe_id = "".join(
                                    ch if ch.isalnum() or ch in "-_" else "-"
                                    for ch in preview_id
                                ) or "preview"
                                video_config["outputPath"] = str(
                                    engine.ROOT / "outputs" / f"visonode-output-{safe_id}-{time.strftime('%Y%m%d-%H%M%S')}.mp4"
                                )
                            video_output = engine.OpenCVVideoOutput(
                                cv2, video_config, frame.shape[1], frame.shape[0], input_source.fps,
                            )
                            opened_output = video_output.open()
                            if opened_output:
                                video_outputs[preview_id] = video_output
                                output_path, output_fps = opened_output
                                self._emit_log(
                                    f"Saving {preview_node.get('title', preview_id)} video to {output_path} at {output_fps:g} fps"
                                )

                    now = time.monotonic()
                    display_frame_for_outputs = frame
                    preview_counts: list[int] = []
                    incident_detections: list[dict] = []
                    displayed = False
                    for preview in preview_nodes:
                        preview_id = str(preview.get("id") or "")
                        if not preview.get("enabled", True) or not engine.has_active_path(workflow, source_id, preview_id):
                            continue
                        display_due = _preview_display_due(preview, now, last_display_at)
                        video_output = video_outputs.get(preview_id)
                        render_needed = display_due or video_output is not None or self._debug_enabled
                        with logic_lock:
                            preview_detections = engine.detections_for_node(
                                workflow, preview_id, frame_detections, frame_filtered, frame_tracked
                            )
                            preview_detections = engine.apply_logic_nodes(
                                workflow,
                                preview_id,
                                preview_detections,
                                logic_runtime,
                                now,
                                debug_callback=on_logic_debug if self._debug_enabled else None,
                                crossing_passthrough=True,
                            )
                        crop_items = engine.detection_crop_items_for_target(
                            workflow,
                            preview_id,
                            frame_crop_batches,
                            frame_detections,
                        )
                        hold_crop_grid = (
                            crop_items is not None
                            and engine.object_event_upstream_of(workflow, preview_id)
                            and preview.get("config", {}).get("holdLastEvent", True)
                        )
                        if hold_crop_grid:
                            crop_items, preview_detections = _retain_event_preview(
                                preview_id,
                                crop_items,
                                preview_detections,
                                held_event_crops,
                                held_event_annotations,
                            )
                        preview_frame, preview_detections = engine.apply_preview_image_processing(
                            frame,
                            workflow,
                            preview_id,
                            preview_detections,
                            preview_processing_runtime,
                        )
                        incident_detections.extend(preview_detections)
                        # Database frame metadata still describes this preview's
                        # processed dimensions even when display rendering waits.
                        display_frame_for_outputs = preview_frame
                        if render_needed:
                            # Preserve the source for other previews and outputs.
                            if crop_items is not None:
                                display_frame = (
                                    _render_held_crop_grid(preview_frame, crop_items, preview, held_crop_grids, workflow=workflow)
                                    if hold_crop_grid else engine.render_detection_crop_grid(
                                        preview_frame, crop_items, preview,
                                    )
                                )
                                drawing_detections = [] if hold_crop_grid else engine.crop_grid_drawing_detections(crop_items)
                            else:
                                drawing_detections = preview_detections
                                display_frame = preview_frame.copy()
                                _apply_privacy_blur(workflow, display_frame, preview_detections)
                                with logic_lock:
                                    engine.draw_roi_overlays(display_frame, workflow, preview_id, logic_runtime)
                                _draw_roboflow_workflow_overlays(display_frame, workflow, event_runtime)
                        with logic_lock:
                            roi_count = engine.roi_crossing_count_for_target(workflow, logic_runtime, preview_id)
                        if render_needed:
                            preview_started_at = time.monotonic()
                            if crop_items is None:
                                counter_state = None
                                for c_node in engine.active_object_counter_nodes(workflow):
                                    c_id = str(c_node.get("id") or "object_counter")
                                    if c_id in event_runtime:
                                        counter_state = event_runtime[c_id]
                                        break
                                engine.draw_detections(
                                    display_frame,
                                    preview_detections,
                                    engine.preview_style_before_drawing_nodes(
                                        workflow, preview_id, preview,
                                    ),
                                    counter_state=counter_state,
                                )
                                for det in preview_detections:
                                    dx, dy = int(round(det.get("x", 0))), int(round(det.get("y", 0)))
                                    dw, dh = int(round(det.get("width", 0))), int(round(det.get("height", 0)))
                                    if "dwellSeconds" in det:
                                        dwell_sec = det["dwellSeconds"]
                                        is_loit = det.get("isLoitering", False)
                                        tag = f"{dwell_sec:.1f}s LOITERING" if is_loit else f"{dwell_sec:.1f}s"
                                        pill_color = (0, 0, 220) if is_loit else (0, 165, 255)
                                        cv2.rectangle(display_frame, (dx, max(16, dy - 22)), (dx + len(tag) * 7 + 10, max(32, dy - 6)), pill_color, -1)
                                        cv2.putText(display_frame, tag, (dx + 4, max(28, dy - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
                                    if "qr_text" in det:
                                        tag = f"QR: {det['qr_text'][:20]}"
                                        cv2.rectangle(display_frame, (dx, dy + dh + 4), (dx + len(tag) * 7 + 10, dy + dh + 18), (16, 185, 129), -1)
                                        cv2.putText(display_frame, tag, (dx + 4, dy + dh + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
                            if not hold_crop_grid:
                                display_frame = engine.apply_drawing_nodes(
                                    display_frame, workflow, preview_id, drawing_detections,
                                    copy_frame=False,
                                )
                            display_frame_for_outputs = display_frame
                            if video_output is not None:
                                video_output.write(display_frame)
                            if self._debug_enabled:
                                self._emit_node_debug(
                                    preview,
                                    input_summary=_detections_summary(preview_detections),
                                    output_summary={
                                        "kind": "preview",
                                        "shown": display_due,
                                        "paced": presentation_buffer is not None,
                                        "frame": _frame_summary(display_frame),
                                        "detections": len(preview_detections),
                                    },
                                    duration_ms=(time.monotonic() - preview_started_at) * 1000,
                                    sample={"visibleDetections": _detection_sample(preview_detections)},
                                )
                            if display_due:
                                if presentation_buffer is not None:
                                    presentation_buffer.put(preview_id, display_frame)
                                else:
                                    displayed = True
                                    self._on_frame(preview_id, display_frame, True)
                                    if native_preview is not None:
                                        native_preview.show(preview_id, preview, display_frame)
                                    with stats_lock:
                                        stats["preview_frames"] += 1
                        preview_counts.append(
                            len(crop_items)
                            if crop_items is not None
                            else (roi_count if roi_count is not None else len(preview_detections))
                        )

                    if display_frame_for_outputs is not None:
                        try:
                            dh, dw = display_frame_for_outputs.shape[:2]
                            if max(dh, dw) > 960:
                                sc = 960 / max(dh, dw)
                                b_frame = cv2.resize(display_frame_for_outputs, (int(dw * sc), int(dh * sc)), interpolation=cv2.INTER_AREA)
                            else:
                                b_frame = display_frame_for_outputs
                            ok_e, enc_j = cv2.imencode(".jpg", b_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                            if ok_e:
                                rolling_frame_buffer.append(enc_j.tobytes())
                        except Exception:
                            pass

                    # HighGUI still needs its event queue pumped between displayed
                    # frames so windows stay responsive to drag/close/keys.
                    if (
                        presentation_buffer is None
                        and native_preview is not None
                        and (displayed or now - last_poll_at >= 0.05)
                    ):
                        last_poll_at = now
                        if native_preview.poll_stop_requested():
                            self._stop_event.set()

                    with logic_lock:
                        alert_detections = engine.detections_for_node(
                            workflow, "alert", frame_detections, frame_filtered, frame_tracked
                        )
                        alert_detections = engine.apply_logic_nodes(
                            workflow,
                            "alert",
                            alert_detections,
                            logic_runtime,
                            now,
                            debug_callback=on_logic_debug if self._debug_enabled else None,
                        )
                    alert_node = engine.enabled_node(workflow, "alert")
                    alert_emitted = False
                    if (
                        alert_node
                        and alert_detections
                        and engine.has_active_path(workflow, source_id, "alert")
                    ):
                        cooldown = max(
                            0, float(alert_node.get("config", {}).get("cooldownSeconds", 5))
                        )
                        if now - last_alert_at >= cooldown:
                            last_alert_at = now
                            labels = ", ".join(
                                item.get("class", "object") for item in alert_detections
                            )
                            self._emit_event(
                                str(
                                    alert_node.get("config", {}).get("message")
                                    or "Detected target object"
                                ),
                                f"{len(alert_detections)} match(es): {labels}",
                            )
                            self._emit_log(
                                f"Alert emitted for {len(alert_detections)} match(es): {labels}"
                            )
                            alert_emitted = True
                            if alert_node.get("config", {}).get("recordClip", True) and len(rolling_frame_buffer) >= 5:
                                self._save_incident_clip_async(list(rolling_frame_buffer), "alert", labels)

                    # Loitering automatic incident recording
                    if len(rolling_frame_buffer) >= 5:
                        for det in incident_detections:
                            if det.get("isLoitering") and det.get("trackId") is not None and det.get("trackId") not in recorded_loiter_tracks:
                                recorded_loiter_tracks.add(det.get("trackId"))
                                self._save_incident_clip_async(
                                    list(rolling_frame_buffer),
                                    "loitering",
                                    f"track #{det.get('trackId')} {det.get('class', 'object')}"
                                )
                    if (
                        self._debug_enabled
                        and alert_node
                        and engine.has_active_path(workflow, source_id, "alert")
                    ):
                        self._emit_node_debug(
                            alert_node,
                            input_summary=_detections_summary(alert_detections),
                            output_summary={
                                "kind": "alert",
                                "emitted": alert_emitted,
                                "matches": len(alert_detections),
                            },
                            duration_ms=0,
                            sample={"matches": _detection_sample(alert_detections)},
                            message="Alert emitted" if alert_emitted else "No alert emitted for this frame",
                        )

                    # Webhook output execution
                    for wh_node in workflow.get("nodes", []):
                        if wh_node.get("type") == "webhook_output" and wh_node.get("enabled", True):
                            wh_id = str(wh_node.get("id") or "")
                            with logic_lock:
                                wh_detections = engine.detections_for_node(
                                    workflow, wh_id, frame_detections, frame_filtered, frame_tracked
                                )
                                wh_detections = engine.apply_logic_nodes(
                                    workflow,
                                    wh_id,
                                    wh_detections,
                                    logic_runtime,
                                    now,
                                    debug_callback=on_logic_debug if self._debug_enabled else None,
                                )
                            if wh_detections and engine.has_active_path(workflow, source_id, wh_id):
                                wh_config = wh_node.get("config", {})
                                cooldown = max(0.1, float(wh_config.get("cooldownSeconds", 2.0) or 2.0))
                                if now - last_webhook_at.get(wh_id, 0.0) >= cooldown:
                                    last_webhook_at[wh_id] = now
                                    _dispatch_webhook_async(wh_config, wh_detections, display_frame_for_outputs)
                                    self._emit_log(f"Webhook dispatched to {wh_config.get('url')} ({len(wh_detections)} detection(s))")


                    if database_outputs:
                        timestamp_ms = int(time.time() * 1000)
                        for database_node, database_writer in database_outputs:
                            database_started_at = time.monotonic()
                            database_config = database_node.get("config", {})
                            database_id = str(database_node.get("id") or "")
                            if not database_node.get("enabled", True) or not engine.has_active_path(workflow, source_id, database_id):
                                continue
                            event_objects_only = (
                                database_config.get("eventObjectsOnly", True)
                                and engine.object_event_upstream_of(workflow, database_id)
                            )
                            sample_every = max(1, int(database_config.get("sampleEvery", 1) or 1))
                            sample_due = total_frame_index % sample_every == 0
                            with logic_lock:
                                database_detections = engine.detections_for_node(
                                    workflow,
                                    str(database_node.get("id") or ""),
                                    frame_detections,
                                    frame_filtered,
                                    frame_tracked,
                                )
                                database_detections = engine.apply_logic_nodes(
                                    workflow,
                                    str(database_node.get("id") or ""),
                                    database_detections,
                                    logic_runtime,
                                    now,
                                )
                            if sample_due and database_config.get("saveFrames", False):
                                database_writer.frame(
                                    frame_index=total_frame_index,
                                    timestamp_ms=timestamp_ms,
                                    fps=self._status.get("fps"),
                                    object_count=len(database_detections),
                                    width=int(display_frame_for_outputs.shape[1]) if getattr(display_frame_for_outputs, "shape", None) is not None else None,
                                    height=int(display_frame_for_outputs.shape[0]) if getattr(display_frame_for_outputs, "shape", None) is not None else None,
                                )
                            if (
                                sample_due
                                and database_config.get("saveDetections", True)
                                and not event_objects_only
                            ):
                                database_writer.detections(
                                    frame_index=total_frame_index,
                                    timestamp_ms=timestamp_ms,
                                    node_id=str(database_node.get("id") or ""),
                                    detections=database_detections,
                                )
                            for record in frame_object_records:
                                if engine.has_active_path(
                                    workflow,
                                    str(record.get("sourceNodeId") or ""),
                                    database_id,
                                ):
                                    database_writer.object_record(
                                        timestamp_ms=timestamp_ms,
                                        record=record,
                                    )
                            for count_record in frame_count_records:
                                if engine.has_active_path(
                                    workflow,
                                    str(count_record.get("sourceNodeId") or ""),
                                    database_id,
                                ):
                                    database_writer.count_event(
                                        timestamp_ms=timestamp_ms,
                                        event=count_record,
                                    )
                            if self._debug_enabled:
                                self._emit_node_debug(
                                    database_node,
                                    input_summary=_detections_summary(database_detections),
                                    output_summary={
                                        "kind": "database",
                                        "savedFrames": bool(database_config.get("saveFrames", False)),
                                        "savedDetections": bool(
                                            database_config.get("saveDetections", True)
                                            and not event_objects_only
                                        ),
                                        "eventObjectsOnly": bool(event_objects_only),
                                        "queuedRows": getattr(database_writer, "queued_count", None),
                                    },
                                    duration_ms=(time.monotonic() - database_started_at) * 1000,
                                    sample={
                                        "frameIndex": total_frame_index,
                                        "detections": len(database_detections),
                                    },
                                )

                    total_frame_index += 1
                    latency_ms = (time.monotonic() - packet.timestamp) * 1000
                    with stats_lock:
                        stats["object_count"] = (preview_counts[0] if preview_counts else 0) or len(alert_detections)
                        stats["latency_ms_sum"] += latency_ms
                        stats["latency_frames"] += 1
                if input_source is not None and input_source.is_static and not bool(input_config.get("loop", True)):
                    if native_preview is not None and preview_nodes:
                        self._emit_log(
                            "Static image preview ready; close its window or press Q/Esc to stop"
                        )
                        wait_for_static_preview_close(native_preview, self._stop_event)
                    self._stop_event.set()

            def presentation_stage() -> None:
                if presentation_buffer is None:
                    return

                self._emit_log("Live preview display is uncapped (3-frame jitter buffer)")

                last_poll_at = 0.0
                while not self._stop_event.is_set():
                    displayed = False
                    for preview in preview_nodes:
                        preview_id = str(preview.get("id") or "")
                        frame = presentation_buffer.take(preview_id)
                        if frame is not None:
                            self._on_frame(preview_id, frame, True)
                            if native_preview is not None:
                                native_preview.show(preview_id, preview, frame)
                            displayed = True
                            with stats_lock:
                                stats["preview_frames"] += 1

                    now = time.monotonic()
                    if native_preview is not None and (displayed or now - last_poll_at >= 0.05):
                        last_poll_at = now
                        if native_preview.poll_stop_requested():
                            self._stop_event.set()
                            break
                    if not displayed:
                        presentation_buffer.wait(0.05)

            start_stage("capture", capture_stage)
            start_stage("processing", processing_stage)
            start_stage("detection", detection_stage)
            start_stage("tracking", tracking_stage)
            start_stage("preview", preview_stage)
            if presentation_buffer is not None:
                start_stage("presentation", presentation_stage)

            last_fps_at = time.monotonic()
            previous_perf = {
                "preview_frames": 0,
                "captured": 0,
                "detected": 0,
                "latency_ms_sum": 0.0,
                "latency_frames": 0,
                "dropped": 0,
            }
            metric_queues = {
                "raw": raw_queue,
                "processed": processed_queue,
                "detection": detection_queue,
                "tracking": tracking_queue,
            }
            if presentation_buffer is not None:
                metric_queues["presentation"] = presentation_buffer
            last_summary_at = time.monotonic()
            while not self._stop_event.is_set():
                failure = stage_failure.get()
                if failure is not None:
                    raise failure
                pipeline_threads = [thread for thread in stage_threads if thread.name != "visonode-presentation"]
                if pipeline_threads and all(not thread.is_alive() for thread in pipeline_threads):
                    self._stop_event.set()
                    break
                now = time.monotonic()
                elapsed = now - last_fps_at
                if elapsed >= 1:
                    with stats_lock:
                        preview_frames = stats["preview_frames"]
                        object_count = stats["object_count"]
                        captured = stats["captured"]
                        detected = stats["detected"]
                        latency_sum = stats["latency_ms_sum"]
                        latency_frames = stats["latency_frames"]
                    current_perf = {
                        "preview_frames": preview_frames,
                        "captured": captured,
                        "detected": detected,
                        "latency_ms_sum": latency_sum,
                        "latency_frames": latency_frames,
                    }
                    perf = performance_status_snapshot(
                        current_perf,
                        previous_perf,
                        metric_queues,
                        elapsed,
                    )
                    self._set_status(
                        state="running",
                        objectCount=object_count,
                        **perf,
                    )
                    if now - last_summary_at >= 5:
                        last_summary_at = now
                        self._emit_log(
                            f"pipeline: capture {perf['captureFps']:.1f} fps, "
                            f"detect {perf['detectionFps']:.1f} fps, "
                            f"processed {perf['processedFps']:.1f} fps, "
                            f"preview {perf['previewFps']:.1f} fps, "
                            f"latency {perf['latencyMs']:.0f} ms, "
                            f"dropped {perf['droppedPerSec']:.1f}/s"
                        )
                    previous_perf = {
                        **current_perf,
                        "dropped": int(perf["totalDropped"]),
                    }
                    last_fps_at = now
                time.sleep(0.05)

            failure = stage_failure.get()
            if failure is not None:
                raise failure
        except DetectorProcessStopped:
            run_status = "stopped"
        except Exception as exc:  # noqa: BLE001 - surfaced to the GUI
            run_status = "error"
            if stage_failure.traceback_text:
                print(stage_failure.traceback_text, end="")
            else:
                traceback.print_exception(type(exc), exc, exc.__traceback__)
            error = engine.exception_message(exc)
            self._set_status(running=False, state="error", error=error,
                             errorTraceback=stage_failure.traceback_text or traceback.format_exc())
            self._emit_event("Workflow error", error)
            self._emit_log(f"ERROR: {error}")
        finally:
            self._stop_event.set()
            raw_queue.close()
            processed_queue.close()
            detection_queue.close()
            tracking_queue.close()
            if presentation_buffer is not None:
                presentation_buffer.close()
            for thread in stage_threads:
                if thread.is_alive():
                    thread.join(timeout=2)
            _close_detector_processes(detector_processes)
            for preview_id, video_output in video_outputs.items():
                video_output.release()
                if video_output.opened and video_output.path is not None:
                    self._emit_log(f"Saved {preview_id} video to {video_output.path}")
            if input_source is not None:
                input_source.release()
            if native_preview is not None:
                native_preview.close()
            if self._stop_event.is_set() and run_status != "error":
                run_status = "stopped"
                self._set_status(
                    running=False,
                    state="stopped",
                    fps=0,
                    objectCount=0,
                    captureFps=0,
                    detectionFps=0,
                    processedFps=0,
                    previewFps=0,
                    latencyMs=0,
                    droppedPerSec=0,
                )
                self._emit_event(
                    "Workflow stopped", "Python runtime stopped and released the input source."
                )
                self._emit_log("Workflow stopped")
            self._close_database_outputs(database_outputs, run_status)

    def _run_serial(self, workflow: dict) -> None:
        if any(node.get("type") == "frame_sampler" for node in workflow.get("nodes", [])):
            return self._run_pipeline(workflow)
        import cv2

        input_source = None
        video_outputs: dict[str, engine.OpenCVVideoOutput] = {}
        native_preview = NativePreviewDisplay(cv2) if self._native_preview else None
        database_outputs: list[tuple[dict, DatabaseWriter]] = []
        run_status = "stopped"
        last_fps_at = time.monotonic()
        frame_count = 0
        total_frame_index = 0
        last_alert_at = 0.0
        last_webhook_at: dict[str, float] = {}
        last_terminal_detection_at = 0.0
        last_slow_inference_at = 0.0
        first_frame_logged = False
        first_inference_logged = False
        detections: list[dict] = []
        tracked: list[dict] = []
        filtered: list[dict] = []
        tracker_runtime: engine.ObjectTracker | None = None
        tracker_signature: str | None = None
        processing_runtime: dict = {"__python_scripts": self._python_context}
        logic_runtime: dict = {}
        event_runtime: dict = {}
        self._event_runtime = event_runtime
        self._active_workflow = workflow
        crop_frames_seen: dict[str, int] = {}
        last_crop_inference: dict[str, float] = {}
        video_output_initialized = False
        held_event_crops: dict[str, list[dict]] = {}
        held_event_annotations: dict[str, list[dict]] = {}
        held_crop_grids: dict = {}
        last_display_at: dict = {}
        source_id = engine.source_node_id(workflow)
        detector_processes: dict = {}
        try:
            input_node = engine.active_input_node(workflow)
            input_source = engine.OpenCVInputSource(cv2, input_node.get("config", {}))
            source_label, actual_width, actual_height = input_source.open()
            self._emit_log(f"Opened {source_label} ({actual_width}x{actual_height})")
            preview_nodes = _active_preview_nodes(workflow, source_id)
            database_outputs = self._open_database_outputs(workflow, source_id)
            self._database_outputs = database_outputs

            inference_nodes = engine.active_inference_nodes(workflow)
            frame_inference_nodes = engine.active_frame_inference_nodes(workflow)
            frame_inference_plan = _frame_inference_plan(workflow, frame_inference_nodes)
            detection_crop_bindings = engine.active_pretracking_detection_crop_bindings(workflow)
            if inference_nodes:
                loaded_models = []
                device_labels = []
                for inference_node in inference_nodes:
                    config = inference_node.get("config", {})
                    eng = config.get("engine", "rfdetr")
                    if eng not in ("sam3", "rfdetr", "rfdetr_tensorrt", "rfdetr_onnx", "convnext", "efficientad", "ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                        raise RuntimeError(
                            f"Backend runtime does not support inference engine '{eng}'."
                        )
                    if eng == "sam3" and inference_node.get("type") != "segmenter":
                        raise RuntimeError(
                            "SAM 3 is available only on the Object Segmentation node."
                        )
                    if eng == "rfdetr" and inference_node.get("type") not in ("detector", "segmenter"):
                        raise RuntimeError(
                            "RF-DETR is available only on Object Detection and Object Segmentation nodes."
                        )
                    if eng in ("rfdetr_tensorrt", "rfdetr_onnx") and inference_node.get("type") not in ("detector", "segmenter"):
                        raise RuntimeError(
                            "RF-DETR optimized models are available only on Object Detection and Object Segmentation nodes."
                        )
                    if eng == "efficientad" and inference_node.get("type") != "efficientad":
                        raise RuntimeError("EfficientAD is available only on the Anomaly Detection node.")
                    if eng == "convnext" and inference_node.get("type") != "classifier":
                        raise RuntimeError(
                            "ConvNeXt is available only on the Image Classification node."
                        )
                    model_name = engine.inference_model_name(inference_node)
                    device, device_label = engine.resolve_inference_device(config)
                    task_labels = {"segmenter": "segmentation", "classifier": "classification", "efficientad": "EfficientAD anomaly inspection"}
                    task_label = task_labels.get(inference_node.get("type"), "detector")
                    if eng == "sam3":
                        task_label = f"SAM 3 {task_label}"
                    elif eng == "rfdetr":
                        task_label = f"RF-DETR {task_label}"
                    elif eng == "rfdetr_onnx":
                        task_label = f"RF-DETR ONNX {task_label}"
                    elif eng == "rfdetr_tensorrt":
                        task_label = f"RF-DETR TensorRT {task_label}"
                    elif eng == "convnext":
                        task_label = f"ConvNeXt {task_label}"
                    elif eng in ("ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                        task_label = f"Custom Model ({eng}) {task_label}"
                    self._emit_log(f"Loading {task_label} model {model_name}")
                    self._emit_log(f"Using inference device {device_label}")
                    load_started_at = time.monotonic()
                    if eng == "sam3":
                        concepts = ", ".join(engine.sam3_concepts(config))
                        self._emit_log(f"SAM 3 concept prompt(s): {concepts}")
                        engine.load_sam3_processor(config, device)
                    elif eng == "rfdetr":
                        rfdetr_model_name = config.get("rfdetrModel") or engine.default_rfdetr_model(inference_node.get("type", "detector"))
                        loaded_model = engine.load_rfdetr_model(
                            rfdetr_model_name,
                            device,
                            engine.rfdetr_checkpoint_path(config),
                            config.get("rfdetrImageSize", engine.RFDETR_NATIVE_IMAGE_SIZE),
                            bool(config.get("rfdetrHalfPrecision", True)),
                            expected_node_type=inference_node.get("type"),
                        )
                        optimization_error = getattr(
                            loaded_model, "_visonode_optimization_error", None
                        )
                        if optimization_error:
                            self._emit_log(
                                "RF-DETR optimization was unavailable; using regular "
                                f"inference: {optimization_error}"
                            )
                        else:
                            resolution = getattr(
                                getattr(loaded_model, "model", None), "resolution", "native"
                            )
                            precision = getattr(loaded_model, "_visonode_precision", "FP32")
                            self._emit_log(
                                "RF-DETR inference optimized and warmed up "
                                f"(JIT {precision}, {resolution}x{resolution})"
                            )
                    elif eng == "rfdetr_onnx":
                        loaded_model = engine.load_rfdetr_onnx(config)
                        self._emit_log("RF-DETR ONNX Runtime model loaded")
                    elif eng == "rfdetr_tensorrt":
                        loaded_model = _load_tensorrt_for_run(config, detector_processes, self._stop_event)
                        self._emit_log(
                            "RF-DETR TensorRT engine loaded "
                            f"({loaded_model.input_shape[2]}x{loaded_model.input_shape[3]})"
                        )
                    elif eng == "efficientad":
                        engine.load_efficientad_model(config, device)
                    elif eng in ("ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                        try:
                            from .custom_model_runtime import CustomModelRunner
                        except ImportError:
                            from custom_model_runtime import CustomModelRunner
                        runner = CustomModelRunner.get_or_load(config, device=device)
                        self._emit_log(f"Custom model loaded ({runner.detected_engine}, classes: {len(runner.classes)})")
                    else:
                        loaded_model = engine.load_convnext_model(config, device)
                        self._emit_log(
                            (
                                "ConvNeXt ImageNet pretrained model loaded "
                                if loaded_model._visonode_pretrained
                                else "ConvNeXt checkpoint loaded "
                            )
                            + f"({len(loaded_model._visonode_classes)} classes, "
                            f"{loaded_model._visonode_image_size}x{loaded_model._visonode_image_size}, "
                            f"{loaded_model._visonode_precision})"
                        )
                    _, effective_device_label = engine.resolve_inference_device(config)
                    if effective_device_label != device_label:
                        self._emit_log(
                            f"{model_name}: GPU execution failed; continuing on {effective_device_label}"
                        )
                    device_label = effective_device_label
                    load_seconds = time.monotonic() - load_started_at
                    loaded_models.append(model_name)
                    device_labels.append(device_label)
                    self._emit_log(f"Loaded {task_label} model {model_name} in {load_seconds:.1f}s")
                    self._emit_node_debug(
                        inference_node,
                        state="ready",
                        output_summary={"kind": "model", "name": model_name, "device": device_label},
                        duration_ms=load_seconds * 1000,
                        message="Model loaded",
                        force=True,
                    )
                device_status = (
                    device_labels[0] if len(set(device_labels)) == 1 else "Mixed devices"
                )
                self._set_status(
                    state="running", model=", ".join(loaded_models), device=device_status
                )
                self._refresh_inference_device_status(inference_nodes, device_labels)
            else:
                self._set_status(state="running")
                self._emit_log("No inference node is active; streaming input frames only")

            self._emit_event(
                "Workflow running",
                "Python is loading, processing, and displaying frames natively.",
            )
            preview_mode = "native OpenCV preview" if native_preview else "GUI preview transport"
            self._emit_log(f"Workflow running ({preview_mode})")
            watchdog = CCTVStreamWatchdog(input_config, input_node, self._emit_log, self._emit_node_debug)

            while not self._stop_event.is_set():
                read_started_at = time.monotonic()
                ok, frame = input_source.read()
                if not ok:
                    if input_source.is_exhausted:
                        self._emit_log("Finite video input completed")
                        break
                    self._emit_node_debug(
                        input_node,
                        state="error",
                        message="Input frame could not be read.",
                        duration_ms=(time.monotonic() - read_started_at) * 1000,
                        force=True,
                    )
                    raise RuntimeError("Input frame could not be read.")
                watchdog.check(frame)
                if self._debug_enabled:
                    frame_summary = _frame_summary(frame)
                    self._emit_node_debug(
                        input_node,
                        input_summary={"kind": "source", "label": source_label},
                        output_summary=frame_summary,
                        duration_ms=(time.monotonic() - read_started_at) * 1000,
                        sample={"frame": frame_summary},
                    )
                if not first_frame_logged:
                    first_frame_logged = True
                    self._emit_log(f"Read first input frame ({frame.shape[1]}x{frame.shape[0]})")

                def on_processing_debug(node, before_frame, after_frame, duration_ms) -> None:
                    self._emit_node_debug(
                        node,
                        input_summary=_frame_summary(before_frame),
                        output_summary=_frame_summary(after_frame),
                        duration_ms=duration_ms,
                        sample={"inputFrame": _frame_summary(before_frame), "outputFrame": _frame_summary(after_frame)},
                    )

                script_frames = {}
                frame = engine.apply_image_processing(
                    frame,
                    workflow,
                    processing_runtime,
                    debug_callback=on_processing_debug if self._debug_enabled else None,
                    script_frames=script_frames,
                )
                if not video_output_initialized:
                    video_output_initialized = True
                    for preview_node in preview_nodes:
                        preview_id = str(preview_node.get("id") or "")
                        video_config = dict(preview_node.get("config", {}))
                        if (
                            len(preview_nodes) > 1
                            and video_config.get("saveVideo", False)
                            and not str(video_config.get("outputPath") or "").strip()
                        ):
                            safe_id = "".join(
                                ch if ch.isalnum() or ch in "-_" else "-"
                                for ch in preview_id
                            ) or "preview"
                            video_config["outputPath"] = str(
                                engine.ROOT / "outputs" / f"visonode-output-{safe_id}-{time.strftime('%Y%m%d-%H%M%S')}.mp4"
                            )
                        video_output = engine.OpenCVVideoOutput(
                            cv2, video_config, frame.shape[1], frame.shape[0], input_source.fps,
                        )
                        opened_output = video_output.open()
                        if opened_output:
                            video_outputs[preview_id] = video_output
                            output_path, output_fps = opened_output
                            self._emit_log(
                                f"Saving {preview_node.get('title', preview_id)} video to {output_path} at {output_fps:g} fps"
                            )

                frame_detections = detections if input_source.is_static else []
                frame_tracked = tracked if input_source.is_static else []
                frame_filtered = filtered if input_source.is_static else []
                frame_object_records: list[dict] = []
                frame_count_records: list[dict] = []
                frame_event_crops: dict[str, list[dict]] = {}
                inference_nodes = engine.active_inference_nodes(workflow)
                now = time.monotonic()
                def on_logic_debug(node, input_items, output_items, duration_ms, passed, target_id) -> None:
                    self._emit_node_debug(
                        node,
                        state="success" if passed else "blocked",
                        input_summary=_detections_summary(input_items),
                        output_summary=_detections_summary(output_items),
                        duration_ms=duration_ms,
                        sample={
                            "targetNodeId": target_id,
                            "passed": passed,
                            "input": _detection_sample(input_items),
                            "output": _detection_sample(output_items),
                        },
                        message="Condition passed" if passed else "Condition blocked this frame",
                    )

                if inference_nodes:
                    detections = []
                    tracking_detections = []
                    for inference_node, threshold, tracking_threshold, runtime_inference_node in frame_inference_plan:
                        config = inference_node.get("config", {})
                        inference_frame = frame
                        branch_script_nodes = [
                            node for node in engine.active_image_processing_nodes_for_path(
                                workflow, engine.source_node_id(workflow),
                                str(inference_node.get("id") or ""),
                            ) if node.get("type") == "python_script"
                        ]
                        if branch_script_nodes:
                            inference_frame = engine.apply_image_processing(
                                frame, workflow, processing_runtime,
                                processing_nodes=branch_script_nodes,
                                script_frames=script_frames,
                            )
                        eng = config.get("engine", "rfdetr")
                        if eng == "sam3":
                            inference_started_at = time.monotonic()
                            node_detections = engine.run_sam3_frame(
                                inference_frame,
                                runtime_inference_node,
                            )
                        elif eng == "rfdetr":
                            inference_started_at = time.monotonic()
                            node_detections = engine.run_rfdetr_frame(
                                inference_frame,
                                runtime_inference_node,
                            )
                        elif eng == "rfdetr_onnx":
                            inference_started_at = time.monotonic()
                            node_detections = engine.run_rfdetr_onnx_frame(
                                inference_frame, runtime_inference_node,
                            )
                        elif eng == "rfdetr_tensorrt":
                            inference_started_at = time.monotonic()
                            node_detections = _run_tensorrt_for_run(
                                [inference_frame],
                                runtime_inference_node,
                                detector_processes, self._stop_event,
                            )[0]
                        elif eng == "efficientad":
                            inference_started_at = time.monotonic()
                            node_detections = engine.run_efficientad_frame(inference_frame, runtime_inference_node)
                        elif eng == "convnext":
                            inference_started_at = time.monotonic()
                            node_detections = engine.run_convnext_frame(
                                inference_frame,
                                runtime_inference_node,
                            )
                        elif eng in ("ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                            inference_started_at = time.monotonic()
                            try:
                                from .custom_model_runtime import run_custom_model_frame
                            except ImportError:
                                from custom_model_runtime import run_custom_model_frame
                            node_detections = run_custom_model_frame(inference_frame, runtime_inference_node)
                        else:
                            raise RuntimeError(
                                f"Backend runtime does not support inference engine '{eng}'."
                            )
                        self._refresh_inference_device_status(inference_nodes, device_labels)
                        inference_seconds = time.monotonic() - inference_started_at
                        if not first_inference_logged:
                            first_inference_logged = True
                            self._emit_log(f"First inference completed in {inference_seconds:.2f}s")
                        elif inference_seconds >= 2.0 and now - last_slow_inference_at >= 5:
                            last_slow_inference_at = now
                            self._emit_log(f"Slow inference: {inference_seconds:.2f}s")
                        inf_cfg = inference_node.get("config", {})
                        per_class_map = _parse_per_class_thresholds(inf_cfg.get("perClassThresholds", ""))
                        class_remap_map = _parse_class_remap(inf_cfg.get("classRemap", ""))
                        is_track_elig = inference_node.get("type") in ("detector", "segmenter")
                        kept_detections, track_dets = _filter_and_remap_detections(
                            node_detections,
                            threshold,
                            tracking_threshold,
                            is_track_elig,
                            per_class_map,
                            class_remap_map,
                        )
                        detections.extend(kept_detections)
                        tracking_detections.extend(track_dets)
                        if self._debug_enabled:
                            self._emit_node_debug(
                                inference_node,
                                input_summary=_frame_summary(frame),
                                output_summary=_detections_summary(kept_detections),
                                duration_ms=inference_seconds * 1000,
                                sample={
                                    "threshold": threshold,
                                    "detections": _detection_sample(kept_detections),
                                },
                            )
                    for crop_node, classifier_node in detection_crop_bindings:
                        classifier_id = _crop_schedule_id(crop_node, classifier_node)
                        if not _eligible_crop_frame_indices(
                            classifier_node, [detections], crop_frames_seen,
                            last_crop_inference, now,
                            schedule_id=classifier_id,
                        ):
                            continue
                        crop_started_at = time.monotonic()
                        object_classifications = engine.run_detection_crop_classifier(
                            frame,
                            detections,
                            workflow,
                            crop_node,
                            classifier_node,
                        )
                        self._refresh_inference_device_status(inference_nodes, device_labels)
                        crop_seconds = time.monotonic() - crop_started_at
                        last_crop_inference[classifier_id] = time.monotonic()
                        detections.extend(object_classifications)
                        if self._debug_enabled:
                            self._emit_node_debug(
                                crop_node,
                                input_summary=_detections_summary([
                                    item for item in detections
                                    if item.get("kind") in ("detection", "segmentation")
                                ]),
                                output_summary={
                                    "kind": "crops",
                                    "count": len(object_classifications),
                                },
                                duration_ms=crop_seconds * 1000,
                            )
                            self._emit_node_debug(
                                classifier_node,
                                input_summary={
                                    "kind": "crops",
                                    "count": len(object_classifications),
                                },
                                output_summary=_detections_summary(object_classifications),
                                duration_ms=crop_seconds * 1000,
                            )
                    tracker_node = engine.active_tracking_node(workflow)
                    if tracker_node:
                        tracker_config = tracker_node.get("config", {})
                        signature = json.dumps(tracker_config, sort_keys=True)
                        if tracker_runtime is None or tracker_signature != signature:
                            tracker_runtime = engine.ObjectTracker(tracker_node)
                            tracker_signature = signature
                            self._emit_log(
                                f"Object tracking enabled with {tracker_runtime.status_label()}"
                            )
                        track_candidates = engine.apply_logic_nodes(
                            workflow,
                            "tracker",
                            engine.results_for_node(
                                workflow,
                                "tracker",
                                tracking_detections,
                            ),
                            logic_runtime,
                            now,
                            debug_callback=on_logic_debug if self._debug_enabled else None,
                        )
                        tracking_started_at = time.monotonic()
                        tracked = tracker_runtime.update(
                            track_candidates,
                            frame,
                            frame_id=total_frame_index + 1,
                            timestamp=now,
                        )
                        if self._debug_enabled:
                            self._emit_node_debug(
                                tracker_node,
                                input_summary=_detections_summary(track_candidates),
                                output_summary=_detections_summary(tracked),
                                duration_ms=(time.monotonic() - tracking_started_at) * 1000,
                                sample={"tracked": _detection_sample(tracked)},
                            )
                    else:
                        tracked = []
                        tracker_runtime = None
                        tracker_signature = None
                    event_results, frame_event_crops, frame_object_records, frame_count_records = _process_track_event_nodes(
                        cv2,
                        frame,
                        workflow,
                        detections,
                        tracked,
                        logic_runtime,
                        event_runtime,
                        now,
                    )
                    detections.extend(event_results)
                    logic_runtime["_event_runtime"] = event_runtime
                    filter_candidates = (
                        engine.results_for_node(workflow, "filter", detections, tracked)
                        if engine.active_filter_node(workflow)
                        else detections
                    )
                    filter_node = engine.active_filter_node(workflow)
                    if filter_node:
                        filter_candidates = engine.apply_logic_nodes(
                            workflow,
                            "filter",
                            filter_candidates,
                            logic_runtime,
                            now,
                            debug_callback=on_logic_debug if self._debug_enabled else None,
                        )
                    filter_started_at = time.monotonic()
                    f_shape = (frame.shape[1], frame.shape[0]) if hasattr(frame, "shape") else None
                    filtered = engine.filter_detections(workflow, filter_candidates, frame_size=f_shape)
                    if filter_node and self._debug_enabled:
                        self._emit_node_debug(
                            filter_node,
                            input_summary=_detections_summary(filter_candidates),
                            output_summary=_detections_summary(filtered),
                            duration_ms=(time.monotonic() - filter_started_at) * 1000,
                            sample={"filtered": _detection_sample(filtered)},
                        )
                    frame_detections = detections
                    frame_tracked = tracked
                    frame_filtered = filtered

                    if detections and now - last_terminal_detection_at >= 1:
                        last_terminal_detection_at = now
                        labels = ", ".join(
                            f"{item.get('class', 'object')}:{float(item.get('score', 0)):.2f}"
                            for item in detections[:6]
                        )
                        if len(detections) > 6:
                            labels = f"{labels}, +{len(detections) - 6} more"
                        self._emit_log(f"Detected {len(detections)} object(s): {labels}")

                display_frame_for_outputs = frame
                preview_counts: list[int] = []
                crop_batches = engine.detection_crop_batches(frame, workflow, frame_detections)
                _save_detection_crop_outputs(cv2, workflow, crop_batches)
                crop_batches.update(frame_event_crops)
                for preview in preview_nodes:
                    preview_id = str(preview.get("id") or "")
                    display_due = _preview_display_due(preview, now, last_display_at)
                    video_output = video_outputs.get(preview_id)
                    render_needed = display_due or video_output is not None or self._debug_enabled
                    preview_detections = engine.detections_for_node(
                        workflow, preview_id, frame_detections, frame_filtered, frame_tracked
                    )
                    preview_detections = engine.apply_logic_nodes(
                        workflow,
                        preview_id,
                        preview_detections,
                        logic_runtime,
                        now,
                        debug_callback=on_logic_debug if self._debug_enabled else None,
                        crossing_passthrough=True,
                    )
                    preview_started_at = time.monotonic()
                    crop_items = engine.detection_crop_items_for_target(
                        workflow, preview_id, crop_batches, frame_detections,
                    )
                    hold_crop_grid = (
                        crop_items is not None
                        and engine.object_event_upstream_of(workflow, preview_id)
                        and preview.get("config", {}).get("holdLastEvent", True)
                    )
                    if hold_crop_grid:
                        crop_items, preview_detections = _retain_event_preview(
                            preview_id,
                            crop_items,
                            preview_detections,
                            held_event_crops,
                            held_event_annotations,
                        )
                    preview_frame, preview_detections = engine.apply_preview_image_processing(
                        frame,
                        workflow,
                        preview_id,
                        preview_detections,
                        processing_runtime,
                        script_frames=script_frames,
                    )
                    display_frame_for_outputs = preview_frame
                    if render_needed:
                        if crop_items is not None:
                            display_frame = (
                                _render_held_crop_grid(preview_frame, crop_items, preview, held_crop_grids, workflow=workflow)
                                if hold_crop_grid else engine.render_detection_crop_grid(preview_frame, crop_items, preview)
                            )
                            drawing_detections = [] if hold_crop_grid else engine.crop_grid_drawing_detections(crop_items)
                        else:
                            display_frame = preview_frame.copy()
                            _apply_privacy_blur(workflow, display_frame, preview_detections)
                            engine.draw_roi_overlays(display_frame, workflow, preview_id, logic_runtime)
                            counter_state = None
                            for c_node in engine.active_object_counter_nodes(workflow):
                                c_id = str(c_node.get("id") or "object_counter")
                                if c_id in event_runtime:
                                    counter_state = event_runtime[c_id]
                                    break
                            engine.draw_detections(
                                display_frame,
                                preview_detections,
                                engine.preview_style_before_drawing_nodes(
                                    workflow, preview_id, preview,
                                ),
                                counter_state=counter_state,
                            )
                        if not hold_crop_grid:
                            display_frame = engine.apply_drawing_nodes(
                                display_frame, workflow, preview_id, drawing_detections,
                                copy_frame=False,
                            )
                        _draw_roboflow_workflow_overlays(display_frame, workflow, event_runtime)
                        display_frame_for_outputs = display_frame
                        if video_output is not None:
                            video_output.write(display_frame)
                        if self._debug_enabled:
                            self._emit_node_debug(
                                preview,
                                input_summary=_detections_summary(preview_detections),
                                output_summary={
                                    "kind": "preview",
                                    "shown": display_due,
                                    "frame": _frame_summary(display_frame),
                                    "detections": len(preview_detections),
                                },
                                duration_ms=(time.monotonic() - preview_started_at) * 1000,
                                sample={"visibleDetections": _detection_sample(preview_detections)},
                            )
                        if display_due:
                            self._on_frame(preview_id, display_frame, True)
                            if native_preview is not None:
                                native_preview.show(preview_id, preview, display_frame)
                    roi_count = engine.roi_crossing_count_for_target(workflow, logic_runtime, preview_id)
                    preview_counts.append(
                        len(crop_items)
                        if crop_items is not None
                        else (roi_count if roi_count is not None else len(preview_detections))
                    )

                if native_preview is not None and native_preview.poll_stop_requested():
                    self._stop_event.set()

                alert_detections = engine.detections_for_node(
                    workflow, "alert", frame_detections, frame_filtered, frame_tracked
                )
                alert_detections = engine.apply_logic_nodes(
                    workflow,
                    "alert",
                    alert_detections,
                    logic_runtime,
                    now,
                    debug_callback=on_logic_debug if self._debug_enabled else None,
                )
                alert_node = engine.enabled_node(workflow, "alert")
                alert_emitted = False
                if (
                    alert_node
                    and alert_detections
                    and engine.has_active_path(workflow, source_id, "alert")
                ):
                    cooldown = max(
                        0, float(alert_node.get("config", {}).get("cooldownSeconds", 5))
                    )
                    if now - last_alert_at >= cooldown:
                        last_alert_at = now
                        labels = ", ".join(
                            item.get("class", "object") for item in alert_detections
                        )
                        self._emit_event(
                            str(
                                alert_node.get("config", {}).get("message")
                                or "Detected target object"
                            ),
                            f"{len(alert_detections)} match(es): {labels}",
                        )
                        self._emit_log(
                            f"Alert emitted for {len(alert_detections)} match(es): {labels}"
                        )
                        alert_emitted = True
                if (
                    self._debug_enabled
                    and alert_node
                    and engine.has_active_path(workflow, source_id, "alert")
                ):
                    self._emit_node_debug(
                        alert_node,
                        input_summary=_detections_summary(alert_detections),
                        output_summary={
                            "kind": "alert",
                            "emitted": alert_emitted,
                            "matches": len(alert_detections),
                        },
                        duration_ms=0,
                        sample={"matches": _detection_sample(alert_detections)},
                        message="Alert emitted" if alert_emitted else "No alert emitted for this frame",
                    )

                if database_outputs:
                    timestamp_ms = int(time.time() * 1000)
                    for database_node, database_writer in database_outputs:
                        database_config = database_node.get("config", {})
                        database_id = str(database_node.get("id") or "")
                        event_objects_only = (
                            database_config.get("eventObjectsOnly", True)
                            and engine.object_event_upstream_of(workflow, database_id)
                        )
                        sample_every = max(1, int(database_config.get("sampleEvery", 1) or 1))
                        sample_due = total_frame_index % sample_every == 0
                        database_detections = engine.detections_for_node(
                            workflow,
                            str(database_node.get("id") or ""),
                            frame_detections,
                            frame_filtered,
                            frame_tracked,
                        )
                        database_detections = engine.apply_logic_nodes(
                            workflow,
                            str(database_node.get("id") or ""),
                            database_detections,
                            logic_runtime,
                            now,
                        )
                        if sample_due and database_config.get("saveFrames", False):
                            database_writer.frame(
                                frame_index=total_frame_index,
                                timestamp_ms=timestamp_ms,
                                fps=self._status.get("fps"),
                                object_count=len(database_detections),
                                width=int(display_frame_for_outputs.shape[1]) if getattr(display_frame_for_outputs, "shape", None) is not None else None,
                                height=int(display_frame_for_outputs.shape[0]) if getattr(display_frame_for_outputs, "shape", None) is not None else None,
                            )
                        if (
                            sample_due
                            and database_config.get("saveDetections", True)
                            and not event_objects_only
                        ):
                            database_writer.detections(
                                frame_index=total_frame_index,
                                timestamp_ms=timestamp_ms,
                                node_id=str(database_node.get("id") or ""),
                                detections=database_detections,
                            )
                        for record in frame_object_records:
                            if engine.has_active_path(
                                workflow,
                                str(record.get("sourceNodeId") or ""),
                                database_id,
                            ):
                                database_writer.object_record(
                                    timestamp_ms=timestamp_ms,
                                    record=record,
                                )
                        for count_record in frame_count_records:
                            if engine.has_active_path(
                                workflow,
                                str(count_record.get("sourceNodeId") or ""),
                                database_id,
                            ):
                                database_writer.count_event(
                                    timestamp_ms=timestamp_ms,
                                    event=count_record,
                                )

                total_frame_index += 1
                frame_count += 1
                elapsed = now - last_fps_at
                if elapsed >= 1:
                    visible_count = (preview_counts[0] if preview_counts else 0) or len(alert_detections)
                    self._set_status(
                        state="running",
                        fps=round(frame_count / elapsed),
                        objectCount=visible_count,
                    )
                    frame_count = 0
                    last_fps_at = now
        except DetectorProcessStopped:
            run_status = "stopped"
        except Exception as exc:  # noqa: BLE001 - surfaced to the GUI
            run_status = "error"
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            error = engine.exception_message(exc)
            self._set_status(running=False, state="error", error=error,
                             errorTraceback=traceback.format_exc())
            self._emit_event("Workflow error", error)
            self._emit_log(f"ERROR: {error}")
        finally:
            _close_detector_processes(detector_processes)
            for preview_id, video_output in video_outputs.items():
                video_output.release()
                if video_output.opened and video_output.path is not None:
                    self._emit_log(f"Saved {preview_id} video to {video_output.path}")
            if input_source is not None:
                input_source.release()
            if native_preview is not None:
                native_preview.close()
            if self._stop_event.is_set():
                run_status = "stopped"
                self._set_status(running=False, state="stopped", fps=0, objectCount=0)
                self._emit_event(
                    "Workflow stopped", "Python runtime stopped and released the input source."
                )
                self._emit_log("Workflow stopped")
            self._close_database_outputs(database_outputs, run_status)

    def _refresh_inference_device_status(self, inference_nodes, device_labels) -> None:
        """Publish CPU recovery immediately, including crop-only classifiers.

        Device resolution uses the runtime's cached probe and failed-device
        registry. Keep the configured device intact so saved workflows retain
        their GPU preference on the next worker launch.
        """
        effective_labels = [
            engine.resolve_inference_device(node.get("config", {}))[1]
            for node in inference_nodes
        ]
        if effective_labels == device_labels:
            return
        for node, previous, current in zip(inference_nodes, device_labels, effective_labels):
            if previous != current:
                self._emit_log(
                    f"{engine.inference_model_name(node)}: inference device changed "
                    f"from {previous} to {current} after GPU fallback"
                )
                self._emit_node_debug(
                    node, state="ready",
                    output_summary={"kind": "model", "device": current},
                    message=f"Inference continuing on {current} after GPU fallback",
                    force=True,
                )
        device_labels[:] = effective_labels
        if effective_labels:
            self._set_status(device=(effective_labels[0]
                                    if len(set(effective_labels)) == 1 else "Mixed devices"))

    # -- emit helpers ---------------------------------------------------
    def _set_status(self, **updates) -> None:
        with self._lock:
            self._status.update(updates)
            snapshot = dict(self._status)
        self._on_status(snapshot)

    def _emit_log(self, line: str) -> None:
        self._on_log(line)

    def _emit_event(self, title: str, detail: str) -> None:
        timestamp_ms = int(time.time() * 1000)
        for node, writer in self._database_outputs:
            if node.get("config", {}).get("saveEvents", True):
                writer.event(timestamp_ms=timestamp_ms, title=title, detail=detail)
        self._on_event(title, detail)

    def _save_incident_clip_async(
        self,
        buffer_frames: list[bytes],
        event_kind: str,
        tag: str,
        fps: float = 15.0,
    ) -> None:
        if not buffer_frames:
            return

        def worker():
            try:
                import cv2
                import numpy as np
                from pathlib import Path
                import time

                out_dir = Path(__file__).resolve().parent.parent / "data" / "outputs" / "events"
                out_dir.mkdir(parents=True, exist_ok=True)
                ts = time.strftime("%Y%m%d_%H%M%S")
                safe_kind = "".join(c if c.isalnum() or c in "-_" else "_" for c in event_kind)
                filename = f"incident_{ts}_{safe_kind}.mp4"
                filepath = out_dir / filename

                first_frame = cv2.imdecode(np.frombuffer(buffer_frames[0], dtype=np.uint8), cv2.IMREAD_COLOR)
                if first_frame is None:
                    return
                h, w = first_frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(filepath), fourcc, fps, (w, h))
                if not writer.isOpened():
                    return
                writer.write(first_frame)
                for jf in buffer_frames[1:]:
                    f = cv2.imdecode(np.frombuffer(jf, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if f is not None:
                        if f.shape[:2] != (h, w):
                            f = cv2.resize(f, (w, h))
                        writer.write(f)
                writer.release()
                self._emit_log(f"Recorded incident video clip: {filename} ({len(buffer_frames)} frames)")
                self._emit_event("Incident Clip Saved", f"{filename} ({tag})")
            except Exception as exc:
                self._emit_log(f"Failed to save incident clip: {exc}")

        Thread(target=worker, daemon=True).start()

    def _emit_node_debug(
        self,
        node: dict | None,
        *,
        state: str = "success",
        input_summary: dict | None = None,
        output_summary: dict | None = None,
        duration_ms: float | None = None,
        sample: object | None = None,
        message: str = "",
        force: bool = False,
    ) -> None:
        if not self._debug_enabled or not node:
            return
        node_id = str(node.get("id") or node.get("type") or "")
        if not node_id:
            return
        now = time.monotonic()
        if not force and now - self._node_debug_last_emit.get(node_id, 0.0) < 0.5:
            return
        self._node_debug_last_emit[node_id] = now
        payload = {
            "nodeId": node_id,
            "type": str(node.get("type") or ""),
            "title": _node_title(node),
            "state": state,
            "input": input_summary or {},
            "output": output_summary or {},
            "durationMs": round(float(duration_ms), 2) if duration_ms is not None else None,
            "sample": sample,
            "message": message,
            "timestamp": time.time(),
        }
        for node, writer in self._database_outputs:
            if node.get("config", {}).get("saveDebug", False):
                writer.node_debug(payload)
        self._on_node_debug(payload)

    def _open_database_outputs(self, workflow: dict, source_id: str) -> list[tuple[dict, DatabaseWriter]]:
        outputs: list[tuple[dict, DatabaseWriter]] = []
        for node in workflow.get("nodes", []):
            if node.get("type") != "database_output" or not node.get("enabled", True):
                continue
            node_id = str(node.get("id") or "")
            if not node_id or not engine.has_active_path(workflow, source_id, node_id):
                continue
            config = node.get("config", {})
            writer = DatabaseWriter(
                config.get("databasePath") or None,
                batch_size=int(config.get("batchSize", 128) or 128),
                flush_interval=float(config.get("flushIntervalMs", 500) or 500) / 1000,
                max_queue=int(config.get("maxQueue", 10000) or 10000),
                retention_days=int(config.get("retentionDays", 14) or 14),
                aggregate_hourly=bool(config.get("aggregateHourly", True)),
            )
            writer.start(workflow)
            outputs.append((node, writer))
            self._emit_log(f"Database output enabled at {writer.path}")
            self._emit_node_debug(
                node,
                state="ready",
                output_summary={"kind": "database", "path": str(writer.path), "runId": writer.run_id},
                message="Database writer started",
                force=True,
            )
        return outputs

    def _close_database_outputs(self, outputs: list[tuple[dict, DatabaseWriter]], status: str) -> None:
        for node, writer in outputs:
            writer.stop(status)
            if writer.dropped_rows:
                self._emit_log(
                    f"WARNING: Database output {node.get('id', '')} dropped {writer.dropped_rows} row(s)."
                )
        if outputs:
            self._database_outputs = []
