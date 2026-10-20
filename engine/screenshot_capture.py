"""Screenshot & Snapshot Capture Node.

Captures visual frame evidence (Full Annotated, Raw Camera Frame, or Object Crop)
in-memory with optional disk storage and timestamp watermark.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


def render_detections_on_frame(
    frame: np.ndarray,
    detections: List[Dict[str, Any]],
    add_watermark: bool = True,
) -> np.ndarray:
    """Render bounding boxes, class labels, and confidence on a copy of the frame."""
    canvas = frame.copy()
    h, w = canvas.shape[:2]

    for det in detections:
        bbox = det.get("bbox") or det.get("box")
        xyxy = det.get("xyxy")

        if xyxy and len(xyxy) == 4:
            x1, y1, x2, y2 = [int(v) for v in xyxy]
        elif bbox and len(bbox) == 4:
            x1, y1, bw, bh = [int(v) for v in bbox]
            x2, y2 = x1 + bw, y1 + bh
        else:
            continue

        x1 = max(0, min(w - 1, x1))
        y1 = max(0, min(h - 1, y1))
        x2 = max(0, min(w - 1, x2))
        y2 = max(0, min(h - 1, y2))

        if x2 <= x1 or y2 <= y1:
            continue

        label = str(det.get("class", "object"))
        score = det.get("confidence") or det.get("score")
        if score is not None:
            label += f" {float(score):.2f}"

        # Draw box
        color = (34, 197, 94)  # Emerald green (BGR: 94, 197, 34 -> standard green in OpenCV)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (34, 197, 94), 2)

        # Draw label badge
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.5
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(label, font, scale, thickness)
        badge_y1 = max(0, y1 - th - 6)
        cv2.rectangle(canvas, (x1, badge_y1), (x1 + tw + 6, badge_y1 + th + 6), (34, 197, 94), -1)
        cv2.putText(canvas, label, (x1 + 3, badge_y1 + th + 1), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    if add_watermark:
        ts_text = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        cv2.putText(canvas, f"AFI VISION | {ts_text}", (16, h - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"AFI VISION | {ts_text}", (16, h - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    return canvas


def crop_first_detection(
    frame: np.ndarray,
    detections: List[Dict[str, Any]],
    padding_ratio: float = 0.15,
) -> Optional[np.ndarray]:
    """Crop the primary detection bounding box with safe boundary padding."""
    if not detections or frame is None:
        return None

    h, w = frame.shape[:2]
    det = detections[0]
    bbox = det.get("bbox") or det.get("box")
    xyxy = det.get("xyxy")

    if xyxy and len(xyxy) == 4:
        x1, y1, x2, y2 = [int(v) for v in xyxy]
    elif bbox and len(bbox) == 4:
        x1, y1, bw, bh = [int(v) for v in bbox]
        x2, y2 = x1 + bw, y1 + bh
    else:
        return None

    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    pad_x = int(box_w * padding_ratio)
    pad_y = int(box_h * padding_ratio)

    cx1 = max(0, x1 - pad_x)
    cy1 = max(0, y1 - pad_y)
    cx2 = min(w, x2 + pad_x)
    cy2 = min(h, y2 + pad_y)

    if cx2 > cx1 and cy2 > cy1:
        return frame[cy1:cy2, cx1:cx2].copy()
    return None


def capture_screenshot(
    frame: Optional[np.ndarray],
    detections: Optional[List[Dict[str, Any]]] = None,
    event: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute screenshot capture according to node configuration.

    Modes:
    - 'full_annotated': Full frame rendered with bounding boxes, labels, and timestamp.
    - 'raw_frame': Raw original camera frame without overlay.
    - 'crop_object': Focused crop on the triggering object bounding box.

    Returns:
        dict containing:
        - 'status': 'captured' | 'failed'
        - 'bytes': bytes | None
        - 'image': np.ndarray | None
        - 'mode': str
        - 'path': str | None (if saveToDisk enabled)
        - 'timestamp': float
    """
    if frame is None or not hasattr(frame, "shape"):
        return {
            "status": "failed",
            "error": "No valid frame provided",
            "bytes": None,
            "image": None,
            "mode": "none",
            "path": None,
            "timestamp": time.time(),
        }

    cfg = config or {}
    mode = str(cfg.get("captureMode") or "full_annotated").strip().lower()
    quality = max(30, min(100, int(cfg.get("jpegQuality", 85) or 85)))
    add_watermark = bool(cfg.get("addTimestampWatermark", True))
    save_to_disk = bool(cfg.get("saveToDisk", False))
    output_dir = str(cfg.get("outputDirectory") or "data/snapshots").strip()

    det_list = detections or []

    # Select target image based on mode
    if mode == "crop_object":
        captured_img = crop_first_detection(frame, det_list)
        if captured_img is None:
            # Fallback to annotated if no bounding box found
            captured_img = render_detections_on_frame(frame, det_list, add_watermark)
    elif mode == "raw_frame":
        captured_img = frame.copy()
        if add_watermark:
            h = captured_img.shape[0]
            ts_text = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            cv2.putText(captured_img, ts_text, (16, h - 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    else:  # 'full_annotated'
        captured_img = render_detections_on_frame(frame, det_list, add_watermark)

    # Encode to JPEG in-memory buffer
    success, buf = cv2.imencode(".jpg", captured_img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    jpeg_bytes = buf.tobytes() if success else None

    saved_path = None
    if save_to_disk and jpeg_bytes:
        try:
            os.makedirs(output_dir, exist_ok=True)
            ev_type = str(event.get("type", event.get("kind", "snapshot")) if event else "snapshot")
            clean_type = "".join(c for c in ev_type if c.isalnum() or c in ("-", "_"))
            filename = f"ss_{clean_type}_{int(time.time() * 1000)}.jpg"
            saved_path = os.path.join(output_dir, filename)
            with open(saved_path, "wb") as f:
                f.write(jpeg_bytes)
        except Exception:
            saved_path = None

    return {
        "status": "captured" if jpeg_bytes else "failed",
        "bytes": jpeg_bytes,
        "image": captured_img,
        "mode": mode,
        "path": saved_path,
        "timestamp": time.time(),
    }


def process_screenshot_node(
    project_node: Dict[str, Any],
    frame: Optional[np.ndarray],
    detections: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Execute Screenshot node on the current pipeline tick.

    Attaches captured screenshot bytes and image reference to each event packet
    so downstream nodes (e.g. Telegram) can directly forward the snapshot.
    """
    cfg = project_node.get("config", {})
    first_ev = events[0] if events else None

    result = capture_screenshot(frame, detections, first_ev, cfg)

    if result.get("bytes"):
        # Annotate all current events with snapshot payload
        for ev in events:
            ev["snapshot_bytes"] = result["bytes"]
            ev["snapshot_image"] = result["image"]
            ev["snapshot_mode"] = result["mode"]
            if result.get("path"):
                ev["snapshot_path"] = result["path"]

    return result
