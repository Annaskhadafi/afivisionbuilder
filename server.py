from __future__ import annotations

import importlib.metadata
import importlib.util
import copy
import datetime
import hashlib
import json
import math
import os
import re
import shutil
import sys
import threading
import tempfile
import time
import uuid
from collections import deque
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

ROOT = Path(__file__).resolve().parent
APP = ROOT / "engine"
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("VISONODE_APP_DATA_DIR", str(ROOT / "data"))
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

try:
    import torch  # Warm up PyTorch runtime and C++ DLLs early to avoid virtual memory fragmentation
except Exception:
    pass
import cv2  # noqa: E402
import core  # noqa: E402
import node_catalog  # noqa: E402
import workflow_store as store  # noqa: E402

app = FastAPI(title="Afi Vision Builder")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
if (ROOT / "static").exists():
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
_outputs = ROOT / "data" / "outputs"
_outputs.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=_outputs), name="outputs")

_lock = threading.RLock()
_runner: core.WorkflowRunner | None = None
_runner_thread_ref: threading.Thread | None = None
_runner_project_id: str | None = None
_logs: deque[dict] = deque(maxlen=500)
_events: deque[dict] = deque(maxlen=500)
_previews: dict[str, bytes] = {}
_seq = 0
_uploads = Path(os.environ["VISONODE_APP_DATA_DIR"]) / "uploads"
_models = Path(os.environ["VISONODE_APP_DATA_DIR"]) / "models"
_MAX_UPLOAD = 200 * 1024 * 1024
_MAX_MODEL_UPLOAD = int(os.getenv("VISONODE_MODEL_UPLOAD_MAX_BYTES", str(1024 ** 3)))
_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".mp4", ".avi", ".mov", ".mkv", ".m4v"}
_MODEL_EXTENSIONS = {".pt", ".pth", ".ckpt", ".onnx", ".engine", ".plan", ".tflite", ".keras", ".h5"}
_MODEL_ENGINES = (
    {"id": "rfdetr", "label": "RF-DETR", "nodeTypes": ["detector", "segmenter"], "configKey": "rfdetrCheckpoint", "extensions": [".pt", ".pth", ".ckpt"], "requirement": "rfdetr and PyTorch; blank checkpoint uses the selected pretrained model."},
    {"id": "rfdetr_onnx", "label": "RF-DETR ONNX", "nodeTypes": ["detector", "segmenter"], "configKey": "rfdetrOnnxModel", "extensions": [".onnx"], "requirement": "rfdetr-onnx runtime and an ONNX model."},
    {"id": "rfdetr_tensorrt", "label": "RF-DETR TensorRT", "nodeTypes": ["detector", "segmenter"], "configKey": "rfdetrTensorRTEngine", "extensions": [".engine", ".plan"], "requirement": "NVIDIA CUDA and TensorRT."},
    {"id": "sam3", "label": "SAM 3", "nodeTypes": ["segmenter"], "configKey": "samCheckpoint", "extensions": [".pt", ".pth", ".ckpt"], "requirement": "SAM 3 runtime and a checkpoint, or the managed/default checkpoint."},
    {"id": "convnext", "label": "ConvNeXt", "nodeTypes": ["classifier"], "configKey": "convnextCheckpoint", "extensions": [".pt", ".pth", ".ckpt"], "requirement": "PyTorch; blank checkpoint uses the selected pretrained model."},
    {"id": "efficientad", "label": "EfficientAD", "nodeTypes": ["efficientad"], "configKey": "efficientadModel", "extensions": [".pt"], "requirement": "PyTorch and a trained EfficientAD deployment export."},
    {"id": "ultralytics_yolo", "label": "Ultralytics YOLO (best.pt)", "nodeTypes": ["detector", "segmenter", "classifier"], "configKey": "modelPath", "extensions": [".pt", ".pth"], "requirement": "Ultralytics YOLO PyTorch checkpoint."},
    {"id": "onnx_custom", "label": "Custom ONNX Runtime", "nodeTypes": ["detector", "segmenter", "classifier"], "configKey": "modelPath", "extensions": [".onnx"], "requirement": "ONNX Runtime model file; segmentation requires a YOLO export."},
    {"id": "custom_auto", "label": "Custom model (auto)", "nodeTypes": ["detector", "segmenter", "classifier"], "configKey": "modelPath", "extensions": [".pt", ".pth", ".onnx", ".tflite", ".keras", ".h5"], "requirement": "Runtime for the selected model format."},
    {"id": "tflite", "label": "TensorFlow Lite", "nodeTypes": ["detector", "classifier"], "configKey": "rfdetrCheckpoint", "extensions": [".tflite"], "requirement": "TensorFlow Lite model file."},
    {"id": "tensorflow_keras", "label": "TensorFlow / Keras", "nodeTypes": ["classifier", "detector"], "configKey": "rfdetrCheckpoint", "extensions": [".keras", ".h5"], "requirement": "TensorFlow/Keras model file."},
)


def _record(text: str) -> None:
    global _seq
    with _lock:
        _seq += 1
        _logs.append({"seq": _seq, "time": time.time(), "text": str(text)})


def _event(title: str, detail: str = "") -> None:
    with _lock:
        _events.append({"time": time.time(), "title": str(title), "detail": str(detail)})


def _frame(node_id: str, frame: Any, *_: Any) -> None:
    if frame is None or not hasattr(frame, "shape"):
        return
    h, w = frame.shape[:2]
    max_dim = 1280
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    if ok:
        data = encoded.tobytes()
        with _lock:
            _previews[str(node_id)] = data


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _check_finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_check_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_check_finite(item) for item in value)
    return True


def _default_workflow() -> dict:
    nodes = [
        store.make_node("input", id="input", x=80, y=180),
        store.make_node("color_convert", id="grayscale", x=320, y=180),
        store.make_node("resize", id="resize", x=540, y=180),
        store.make_node("preview", id="preview", x=760, y=180),
    ]
    return {"nodes": nodes, "edges": [["input", "grayscale"], ["grayscale", "resize"], ["resize", "preview"]]}


def validate_workflow(workflow: Any) -> dict:
    if not isinstance(workflow, dict) or not isinstance(workflow.get("nodes"), list) or not isinstance(workflow.get("edges"), list):
        raise HTTPException(400, "workflow must contain nodes and edges lists")
    nodes = workflow["nodes"]
    ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"]:
            raise HTTPException(400, "each node needs a non-empty id")
        if node["id"] in ids:
            raise HTTPException(400, f"duplicate node id: {node['id']}")
        ids.add(node["id"])
        if not isinstance(node.get("type"), str) or node["type"] not in node_catalog.NODE_BLUEPRINTS:
            raise HTTPException(400, f"unknown node type: {node.get('type')}")
        if "enabled" in node and not isinstance(node["enabled"], bool):
            raise HTTPException(400, f"node enabled must be boolean: {node['id']}")
        if not isinstance(node.get("config", {}), dict):
            raise HTTPException(400, f"node config must be an object: {node['id']}")
        if node["type"] in ("zone_activity_timer", "zone_exit_event"):
            from project_nodes import validate_project_config
            try:
                validate_project_config(node)
            except (ValueError, TypeError) as exc:
                raise HTTPException(400, f"node '{node['id']}': {exc}") from exc
        if node["type"] == "vlm_box_tracker":
            cfg = node.get("config", {})
            provider = str(cfg.get("provider", "openrouter")).lower().strip()
            if provider not in ("openrouter", "typesafe"):
                raise HTTPException(400, f"node '{node['id']}': provider must be 'openrouter' or 'typesafe'")
            q_interval = cfg.get("queryIntervalSeconds", 1.0)
            try:
                q_interval = float(q_interval)
                if not math.isfinite(q_interval) or q_interval < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise HTTPException(400, f"node '{node['id']}': queryIntervalSeconds must be a non-negative number")
            min_conf = cfg.get("minConfidence", 0.5)
            try:
                min_conf = float(min_conf)
                if not math.isfinite(min_conf) or not (0.0 <= min_conf <= 1.0):
                    raise ValueError()
            except (ValueError, TypeError):
                raise HTTPException(400, f"node '{node['id']}': minConfidence must be a number between 0.0 and 1.0")
        if node["type"] == "ai_agent":
            cfg = node.get("config", {})
            provider = str(cfg.get("provider", "openai")).lower().strip()
            if provider not in ("openai", "openrouter", "custom"):
                raise HTTPException(400, f"node '{node['id']}': provider must be 'openai', 'openrouter', or 'custom'")
            trigger_mode = str(cfg.get("triggerMode", "on_event")).lower().strip()
            if trigger_mode not in ("on_event", "periodic", "always"):
                raise HTTPException(400, f"node '{node['id']}': triggerMode must be 'on_event', 'periodic', or 'always'")
            task_mode = str(cfg.get("taskMode", "decision")).lower().strip()
            if task_mode not in ("decision", "analysis", "structured_json", "raw_text"):
                raise HTTPException(400, f"node '{node['id']}': taskMode must be 'decision', 'analysis', 'structured_json', or 'raw_text'")
            cooldown = cfg.get("cooldownSeconds", 5.0)
            try:
                cooldown = float(cooldown)
                if not math.isfinite(cooldown) or cooldown < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise HTTPException(400, f"node '{node['id']}': cooldownSeconds must be a non-negative number")
            if trigger_mode == "periodic":
                p_interval = cfg.get("periodicIntervalSeconds", 10.0)
                try:
                    p_interval = float(p_interval)
                    if not math.isfinite(p_interval) or p_interval <= 0:
                        raise ValueError()
                except (ValueError, TypeError):
                    raise HTTPException(400, f"node '{node['id']}': periodicIntervalSeconds must be greater than 0")
        if node["type"] == "frame_sampler":
            target_fps = node.get("config", {}).get("targetFps", 10)
            if isinstance(target_fps, bool):
                raise HTTPException(400, f"node '{node['id']}' Target FPS must be a finite number greater than or equal to 0")
            try:
                target_fps = float(target_fps)
            except (TypeError, ValueError):
                target_fps = -1
            if not math.isfinite(target_fps) or target_fps < 0:
                raise HTTPException(400, f"node '{node['id']}' Target FPS must be a finite number greater than or equal to 0")
        if node["type"] == "python_script":
            from python_script_runtime import validate_script
            config = {**node_catalog.PYTHON_SCRIPT_DEFAULTS, **node.get("config", {})}
            timeout = config["timeoutMs"]
            if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 60000:
                raise HTTPException(400, f"node '{node['id']}' timeoutMs must be an integer between 1 and 60000")
            if config["onError"] not in ("stop", "pass"):
                raise HTTPException(400, f"node '{node['id']}' onError must be 'stop' or 'pass'")
            if not isinstance(config["code"], str) or len(config["code"]) > 65536:
                raise HTTPException(400, f"node '{node['id']}' script must contain at most 65536 characters")
            try:
                validate_script(config["code"])
            except ValueError as exc:
                raise HTTPException(400, f"node '{node['id']}': {exc}") from exc
        for key in ("x", "y"):
            if key in node and not _finite(node[key]):
                raise HTTPException(400, f"node {key} must be finite")
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in ids}
    for edge in workflow["edges"]:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2 or not all(isinstance(item, str) for item in edge) or edge[0] not in ids or edge[1] not in ids:
            raise HTTPException(400, "edges must reference existing node ids")
        adjacency[edge[0]].append(edge[1])
    try:
        tuple(TopologicalSorter({node_id: set(children) for node_id, children in adjacency.items()}).static_order())
    except CycleError:
        raise HTTPException(400, "workflow graph contains a cycle")
    try:
        json.dumps(workflow, allow_nan=False)
    except (TypeError, ValueError):
        raise HTTPException(400, "workflow contains non-finite or non-JSON values")
    if not _check_finite(workflow):
        raise HTTPException(400, "workflow contains non-finite numbers")
    return workflow


def _project_payload(project_id: str) -> dict:
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    return {"project": project, "workflow": store.load_project_workflow(project_id)}


@app.get("/api/catalog")
def catalog() -> dict:
    deps = {}
    for package in ("fastapi", "uvicorn", "opencv-python", "numpy", "ultralytics", "rfdetr", "onnxruntime", "timm", "torch", "gxipy"):
        try:
            deps[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            deps[package] = None
    return {"version": "1.0.3-beta.127", "catalog": node_catalog.NODE_BLUEPRINTS, "defaults": _default_workflow(), "runtime": {"python": sys.version.split()[0], "dependencies": deps}}


@app.get("/api/projects")
def projects() -> dict:
    return {"projects": store.list_projects()}


@app.post("/api/projects")
def create_project(request: Request, body: dict) -> dict:
    _write_allowed(request)
    if "name" in body and not isinstance(body["name"], str):
        raise HTTPException(400, "project name must be a string")
    workflow = validate_workflow(body.get("workflow") or _default_workflow())
    try:
        with store._project_lock:
            project = store.import_project_workflow(str(body.get("name") or "Vision Workflow"), workflow)
    except Exception as exc:
        raise HTTPException(500, str(exc))
    return {"project": project, "workflow": workflow}


@app.get("/api/projects/{project_id}")
def get_project(project_id: str) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", project_id):
        raise HTTPException(404, "project not found")
    return _project_payload(project_id)


@app.put("/api/projects/{project_id}")
def update_project(project_id: str, request: Request, body: dict) -> dict:
    _write_allowed(request)
    if "name" in body and not isinstance(body["name"], str):
        raise HTTPException(400, "project name must be a string")
    with store._project_lock:
        payload = _project_payload(project_id)
        workflow = validate_workflow(body.get("workflow", payload["workflow"]))
    # The extracted writer intentionally swallows OSError; the HTTP API must
    # report a failed save and leave the previous document intact.
        path = store.PROJECTS_DIR / project_id / "workflow.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"workflow.{uuid.uuid4().hex}.tmp")
        try:
            temporary.write_text(json.dumps(workflow, indent=2, allow_nan=False), encoding="utf-8")
            temporary.replace(path)
            index = store._read_index()
            project = store._project_by_id(index, project_id)
            if project is None:
                raise HTTPException(404, "project not found")
            if "name" in body:
                project["name"] = store._clean_project_name(body["name"])
            project["modified_at"] = store._now_iso()
            store._write_index(index, strict=True)
        except HTTPException:
            temporary.unlink(missing_ok=True)
            raise
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise HTTPException(500, f"could not save workflow: {exc}")
        with _lock:
            if _runner is not None and _runner.is_running() and _runner_project_id == project_id:
                _runner.update_workflow(workflow)
        return _project_payload(project_id)


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str, request: Request) -> dict:
    _write_allowed(request)
    with store._project_lock:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", project_id) or not store.delete_project(project_id):
            raise HTTPException(404, "project not found")
        return {"ok": True}


@app.get("/api/status")
def status() -> dict:
    with _lock:
        current = _runner.status() if _runner else {"running": False, "state": "idle", "error": None, "nodeTelemetry": {}}
        return {**current, "projectId": _runner_project_id, "logs": list(_logs), "events": list(_events), "previews": list(_previews)}


@app.post("/api/scripts/validate")
def check_python_script(request: Request, body: dict) -> dict:
    _write_allowed(request)
    from python_script_runtime import validate_script
    code = body.get("code")
    if not isinstance(code, str) or len(code) > 65536:
        raise HTTPException(400, "Script must contain at most 65536 characters")
    try:
        validate_script(code)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"valid": True}


def _write_allowed(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin:
        return
    host = request.headers.get("host", "127.0.0.1:8765")
    port = host.rsplit(":", 1)[-1] if ":" in host else "8765"
    if origin not in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}:
        raise HTTPException(403, "cross-origin write rejected")


def _model_availability(engine_id: str) -> bool:
    packages = {
        "rfdetr": ("rfdetr", "torch"),
        "rfdetr_onnx": ("onnxruntime",),
        "rfdetr_tensorrt": ("tensorrt",),
        "sam3": ("torch",),
        "convnext": ("torch", "timm"),
        "efficientad": ("torch",),
        "ultralytics_yolo": ("ultralytics", "torch"),
        "onnx_custom": ("onnxruntime",),
        "tflite": ("tensorflow",),
        "tensorflow_keras": ("tensorflow",),
    }
    return all(importlib.util.find_spec(package) is not None for package in packages.get(engine_id, ()))


@app.get("/api/models/inspect")
def inspect_model(path: str) -> dict:
    try:
        import custom_model_runtime
    except ImportError:
        from engine import custom_model_runtime
    target = custom_model_runtime.resolve_model_file(path.strip().strip('"'))
    if not target.is_file():
        raise HTTPException(404, f"Model file not found: {path}")
    engine = custom_model_runtime.detect_model_engine(str(target))
    task = None
    if target.suffix.lower() in (".pt", ".pth", ".onnx"):
        try:
            handle = custom_model_runtime.CustomModelRunner.get_or_load(
                {"engine": engine, "modelPath": str(target)}, device="cpu",
            )
            classes = handle.classes
            task = getattr(handle.raw_model, "task", None)
            if engine == "onnx_custom":
                task = handle.raw_model.get_modelmeta().custom_metadata_map.get("task")
        except Exception as exc:
            raise HTTPException(400, f"Cannot load model '{target.name}': {exc}") from exc
    else:
        classes = custom_model_runtime.extract_model_labels(str(target))
    sha256 = _file_sha256(target)
    return {
        "path": str(target),
        "name": target.name,
        "engine": engine,
        "format": target.suffix.lower().lstrip("."),
        "task": task,
        "classes": classes,
        "classesCount": len(classes),
        "sizeBytes": target.stat().st_size,
        "sha256": sha256,
        "contentId": sha256,
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 ** 3):.1f} GB"
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


def _infer_model_type(name: str) -> str:
    lower = name.lower()
    if "-seg" in lower or "_seg" in lower or "segment" in lower:
        return "Segmentation"
    if "-pose" in lower or "_pose" in lower or "pose" in lower:
        return "Pose"
    if "-cls" in lower or "_cls" in lower or "classify" in lower or "convnext" in lower:
        return "Classification"
    if "defect" in lower or "anomaly" in lower or "efficientad" in lower or "inspection" in lower:
        return "Visual Inspection"
    if "vlm" in lower or "qwen" in lower or "florence" in lower:
        return "VLM / Multimodal"
    return "Detection"


def _infer_model_engine(name: str, format_str: str) -> str:
    lower = name.lower()
    if "rfdetr" in lower:
        return "RF-DETR"
    if "yolo" in lower:
        return "Ultralytics YOLO"
    if "convnext" in lower:
        return "ConvNeXt"
    if "efficientad" in lower:
        return "EfficientAD"
    if format_str == "onnx":
        return "Custom ONNX"
    if format_str in ("engine", "plan"):
        return "TensorRT"
    return "PyTorch / Custom"


def _infer_model_version(name: str) -> str:
    lower = name.lower()
    if "yolo11" in lower:
        return "v11.0"
    if "yolov8" in lower:
        return "v8.0"
    if "yolov5" in lower:
        return "v5.0"
    if "v2" in lower:
        return "v2.0"
    if "v3" in lower:
        return "v3.0"
    return "v1.0"


def _model_entry(path: Path, *, name: str | None = None, sha256: str | None = None, is_custom: bool = True) -> dict:
    human_name = name or path.name
    fingerprint = sha256[:8] if sha256 else None
    size_bytes = path.stat().st_size if path.exists() else 0
    format_str = path.suffix.lower().lstrip(".")
    mtype = _infer_model_type(human_name)
    engine = _infer_model_engine(human_name, format_str)
    version = _infer_model_version(human_name)
    mtime_str = "System Built-in"
    if is_custom and path.exists():
        try:
            mtime_str = datetime.datetime.fromtimestamp(path.stat().st_mtime, tz=datetime.timezone.utc).strftime("%b %d, %Y")
        except Exception:
            mtime_str = "Recent"

    return {
        "id": sha256 or human_name,
        "name": human_name,
        "label": f"{human_name} · {fingerprint}" if fingerprint else human_name,
        "path": str(path),
        "format": format_str,
        "sizeBytes": size_bytes,
        "sizeFormatted": _format_size(size_bytes),
        "sha256": sha256,
        "contentId": sha256 or human_name,
        "fingerprint": fingerprint,
        "type": mtype,
        "version": version,
        "status": "Ready",
        "added": mtime_str,
        "engine": engine,
        "isCustom": is_custom,
    }


def _system_models_listing() -> list[dict]:
    result = []
    seen_names = set()

    # 1. Built-in models in project root directory (yolov8n.pt, yolov8s.pt, etc.)
    root_dir = ROOT
    if root_dir.is_dir():
        for path in root_dir.iterdir():
            if path.is_file() and path.suffix.lower() in _MODEL_EXTENSIONS and "yolo" in path.name.lower():
                if path.name not in seen_names:
                    result.append(_model_entry(path, is_custom=False))
                    seen_names.add(path.name)

    # 2. RF-DETR Pretrained foundation models (registered available defaults)
    rfdetr_defaults = [
        {"name": "rfdetr_nano", "type": "Detection", "version": "v1.0", "sizeFormatted": "30.8 MB", "engine": "RF-DETR", "format": "pt"},
        {"name": "rfdetr_small", "type": "Detection", "version": "v1.0", "sizeFormatted": "64.2 MB", "engine": "RF-DETR", "format": "pt"},
        {"name": "rfdetr_seg_nano", "type": "Segmentation", "version": "v1.0", "sizeFormatted": "34.5 MB", "engine": "RF-DETR-Seg", "format": "pt"},
    ]
    for rf in rfdetr_defaults:
        if rf["name"] not in seen_names:
            result.append({
                "id": rf["name"],
                "name": rf["name"],
                "label": rf["name"],
                "path": rf["name"],
                "format": rf["format"],
                "sizeBytes": 32000000,
                "sizeFormatted": rf["sizeFormatted"],
                "sha256": None,
                "contentId": rf["name"],
                "fingerprint": None,
                "type": rf["type"],
                "version": rf["version"],
                "status": "Ready",
                "added": "System Built-in",
                "engine": rf["engine"],
                "isCustom": False,
            })
            seen_names.add(rf["name"])
    return result


def _model_listing() -> list[dict]:
    if not _models.is_dir():
        return []
    result = []
    for path in _models.iterdir():
        if path.is_file() and path.suffix.lower() in _MODEL_EXTENSIONS:
            result.append(_model_entry(path, is_custom=True))
        elif path.is_dir():
            sha256 = path.name if re.fullmatch(r"[0-9a-f]{64}", path.name) else None
            for subpath in path.iterdir():
                if subpath.is_file() and subpath.suffix.lower() in _MODEL_EXTENSIONS:
                    result.append(_model_entry(subpath, sha256=sha256, is_custom=True))
    return sorted(result, key=lambda item: item["name"].lower())


@app.get("/api/models")
def models(include_system: bool = False) -> dict:
    custom_list = _model_listing()
    system_list = _system_models_listing()
    all_list = custom_list + system_list
    all_list.sort(key=lambda item: (not item.get("isCustom", False), item["name"].lower()))

    engines = [{**engine, "available": _model_availability(engine["id"])} for engine in _MODEL_ENGINES]
    options = {
        "rfdetr": [{"value": value, "label": label} for value, label in zip(core.engine.RFDETR_DETECTION_MODELS, ("RF-DETR nano", "RF-DETR small", "RF-DETR medium", "RF-DETR large"))],
        "rfdetr_seg": [{"value": value, "label": label} for value, label in zip(core.engine.RFDETR_SEGMENTATION_MODELS, ("RF-DETR-Seg nano", "RF-DETR-Seg small", "RF-DETR-Seg medium", "RF-DETR-Seg large"))],
        "convnext": [{"value": value, "label": value.split(".")[0].replace("_", " ").title()} for value in core.engine.CONVNEXT_MODELS],
    }
    return {
        "models": all_list if include_system else custom_list,
        "customModels": custom_list,
        "systemModels": system_list,
        "allModels": all_list,
        "engines": engines,
        "options": options,
    }


@app.delete("/api/models/{model_id}")
def delete_model(model_id: str, request: Request) -> dict:
    _write_allowed(request)
    deleted = False
    if _models.is_dir():
        for path in list(_models.iterdir()):
            if path.is_file() and (path.name == model_id or path.stem == model_id):
                path.unlink(missing_ok=True)
                deleted = True
                break
            elif path.is_dir():
                if path.name == model_id:
                    shutil.rmtree(path, ignore_errors=True)
                    deleted = True
                    break
                for subpath in list(path.iterdir()):
                    if subpath.is_file() and (subpath.name == model_id or subpath.stem == model_id or (subpath.name in model_id)):
                        subpath.unlink(missing_ok=True)
                        if not any(path.iterdir()):
                            shutil.rmtree(path, ignore_errors=True)
                        deleted = True
                        break
    if not deleted:
        raise HTTPException(404, f"Custom model '{model_id}' not found or cannot be deleted")
    return {"ok": True, "deleted": model_id}


@app.post("/api/models/upload")
async def upload_model(request: Request, file: UploadFile = File(...)) -> dict:
    _write_allowed(request)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _MODEL_EXTENSIONS:
        raise HTTPException(400, f"unsupported model format. Supported: {', '.join(sorted(_MODEL_EXTENSIONS))}")
    _models.mkdir(parents=True, exist_ok=True)
    clean_name = re.sub(r"[^A-Za-z0-9_.-]", "_", file.filename or f"model{suffix}")
    temporary_name = None
    try:
        # Keep staging on the model volume so os.replace remains atomic on Windows.
        fd, temporary_name = tempfile.mkstemp(prefix="model-upload-", suffix=".tmp", dir=str(_models))
        os.close(fd)
        temporary = Path(temporary_name)
        digest = hashlib.sha256()
        size = 0
        with temporary.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > _MAX_MODEL_UPLOAD:
                    raise HTTPException(413, "upload exceeds maximum model size")
                digest.update(chunk)
                output.write(chunk)
        sha256 = digest.hexdigest()
        target = _models / sha256 / clean_name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if _file_sha256(target) != sha256:
                raise HTTPException(409, "model content address collision")
            temporary.unlink(missing_ok=True)
        else:
            os.replace(temporary, target)
    except Exception:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
        raise
    return {"path": str(target), "name": clean_name, "format": suffix.lstrip("."), "sizeBytes": size, "sha256": sha256, "contentId": sha256}


def _templates() -> list[dict]:
    templates = [
        {
            "id": "workshop_bay_activity",
            "name": "Workshop Bay Activity Monitoring",
            "description": "Pengawasan aktivitas mekanik dan ban di bay bengkel: stream RTSP CCTV IP Camera, deteksi YOLOv8 person & tire, ByteTrack tracker, Zone Activity Timer untuk pencatatan durasi sesi kerja, dan penyimpanan event database.",
            "tags": ["Workshop", "RTSP CCTV", "Zone Timer"],
            "badge": "Operations",
            "modelSize": "Includes models · 6.2 MB",
            "workflow": {
                "nodes": [
                    store.make_node("ip_camera", id="rtsp_cam", x=60, y=140, config={"streamUrl": "rtsp://192.168.1.101:554/live", "autoReconnect": True}),
                    store.make_node("detector", id="detector", x=280, y=140, config={"threshold": 0.35, "modelPath": "yolov8n.pt"}),
                    store.make_node("tracker", id="tracker", x=500, y=140, config={"algorithm": "bytetrack"}),
                    store.make_node("zone_activity_timer", id="zone_timer", x=720, y=140, config={"classes": "person", "confirmationSeconds": 5, "absenceGraceSeconds": 15, "points": "0.15,0.18;0.85,0.18;0.80,0.85;0.20,0.85"}),
                    store.make_node("overlay_annotate", id="annotate", x=940, y=140),
                    store.make_node("database_output", id="db_out", x=1160, y=80, config={"table": "events"}),
                    store.make_node("preview", id="preview", x=1160, y=220),
                ],
                "edges": [
                    ["rtsp_cam", "detector"],
                    ["detector", "tracker"],
                    ["tracker", "zone_timer"],
                    ["zone_timer", "annotate"],
                    ["annotate", "db_out"],
                    ["annotate", "preview"],
                ],
            },
        },
        {
            "id": "warehouse_gate_exit",
            "name": "Warehouse Gate Exit Monitoring",
            "description": "Pengawasan insiden perlintasan gerbang gudang: stream RTSP CCTV IP Camera, deteksi YOLOv8 kendaraan & ban, ByteTrack tracker, Zone Exit Event untuk mendeteksi perpindahan dari dalam ke luar gerbang, dan notifikasi alert/ERP webhook.",
            "tags": ["Warehouse", "RTSP CCTV", "Zone Exit"],
            "badge": "Operations",
            "modelSize": "Includes models · 6.2 MB",
            "workflow": {
                "nodes": [
                    store.make_node("ip_camera", id="rtsp_cam", x=60, y=140, config={"streamUrl": "rtsp://192.168.1.201:554/live", "autoReconnect": True}),
                    store.make_node("detector", id="detector", x=280, y=140, config={"threshold": 0.35, "modelPath": "yolov8n.pt"}),
                    store.make_node("tracker", id="tracker", x=500, y=140, config={"algorithm": "bytetrack"}),
                    store.make_node("zone_exit_event", id="zone_exit", x=720, y=140, config={"classes": "truck,car", "points": "0.20,0.20;0.80,0.20;0.75,0.85;0.25,0.85", "crossingDirection": "inside_to_outside"}),
                    store.make_node("overlay_annotate", id="annotate", x=940, y=140),
                    store.make_node("alert", id="alert_out", x=1160, y=80, config={"message": "Objek keluar melewati gerbang gudang!"}),
                    store.make_node("preview", id="preview", x=1160, y=220),
                ],
                "edges": [
                    ["rtsp_cam", "detector"],
                    ["detector", "tracker"],
                    ["tracker", "zone_exit"],
                    ["zone_exit", "annotate"],
                    ["annotate", "alert_out"],
                    ["annotate", "preview"],
                ],
            },
        },
        {
            "id": "restaurant_table_occupancy",
            "name": "Restaurant Table Occupancy & Dining Dwell Tracker",
            "description": "Pemantauan okupansi meja restoran dan durasi tamu duduk (dwell time): input kamera CCTV, deteksi orang (person), ByteTrack tracker, Multi-Zone Occupancy & Activity Tracker untuk menghitung berapa lama setiap meja terisi (Meja 01 s/d Meja 04), visual HUD overlay timer meja, deteksi overstay, dan pencatatan event turnover ke database.",
            "tags": ["Restaurant", "Table Tracker", "Dwell Time", "Multi-Zone"],
            "badge": "Hospitality",
            "modelSize": "Includes models · 6.2 MB",
            "workflow": {
                "nodes": [
                    store.make_node("input", id="input", x=60, y=140, config={"sourceType": "video", "filePath": "D:/CCTV-EATON-Cafe-SnapYT.App.mp4", "loop": True}),
                    store.make_node("detector", id="detector", x=280, y=140, config={"threshold": 0.20, "modelPath": "yolov8n.pt"}),
                    store.make_node("tracker", id="tracker", x=500, y=140, config={"algorithm": "bytetrack"}),
                    store.make_node(
                        "multi_zone_occupancy",
                        id="table_tracker",
                        x=720,
                        y=140,
                        config={
                            "targetClasses": "person",
                            "confirmationSeconds": 2.0,
                            "graceSeconds": 10.0,
                            "maxDwellMinutes": 30.0,
                            "labelPosition": "center",
                            "compactLabel": True,
                            "showHudOverlay": True,
                            "showSummaryCard": True,
                            "zones": [
                                {
                                    "id": "meja_01",
                                    "name": "Meja 01 (Tengah)",
                                    "capacity": 2,
                                    "points": "0.42,0.28; 0.62,0.28; 0.62,0.62; 0.42,0.62"
                                },
                                {
                                    "id": "meja_02",
                                    "name": "Meja 02 (Kiri Depan)",
                                    "capacity": 4,
                                    "points": "0.15,0.54; 0.41,0.54; 0.41,0.98; 0.15,0.98"
                                },
                                {
                                    "id": "meja_03",
                                    "name": "Meja 03 (Kiri Belakang)",
                                    "capacity": 6,
                                    "points": "0.07,0.17; 0.40,0.17; 0.40,0.52; 0.07,0.52"
                                },
                                {
                                    "id": "meja_04",
                                    "name": "Meja 04 (Kanan Depan)",
                                    "capacity": 4,
                                    "points": "0.63,0.47; 0.98,0.47; 0.98,0.98; 0.63,0.98"
                                }
                            ]
                        }
                    ),
                    store.make_node("overlay_annotate", id="annotate", x=940, y=140),
                    store.make_node("database_output", id="db_out", x=1160, y=80, config={"table": "restaurant_table_events"}),
                    store.make_node("preview", id="preview", x=1160, y=220),
                ],
                "edges": [
                    ["input", "detector"],
                    ["detector", "tracker"],
                    ["tracker", "table_tracker"],
                    ["table_tracker", "annotate"],
                    ["annotate", "db_out"],
                    ["annotate", "preview"],
                ],
            },
        },
        {
            "id": "bottle_visual_inspection",
            "name": "Bottle Visual Inspection",
            "description": "Detect bottles and classify each one as OK or DEFECT using a visual inspection workflow. This template shows a typical manufacturing pipeline with bottle detection, ROI cropping, anomaly inspection, and result visualization.",
            "tags": ["Manufacturing", "CPU friendly"],
            "badge": "Manufacturing",
            "modelSize": "Includes models · 30.8 MB download",
            "workflow": {
                "nodes": [
                    store.make_node("input", id="input", x=60, y=140),
                    store.make_node("detector", id="detector", x=280, y=140, config={"threshold": 0.5, "modelPath": "yolov8n.pt"}),
                    store.make_node("detection_crop", id="crop", x=500, y=140),
                    store.make_node("classifier", id="classifier", x=720, y=140, config={"modelPath": "yolov8n-cls.pt"}),
                    store.make_node("overlay_annotate", id="annotate", x=940, y=140),
                    store.make_node("preview", id="preview", x=1160, y=140),
                ],
                "edges": [
                    ["input", "detector"],
                    ["detector", "crop"],
                    ["crop", "classifier"],
                    ["classifier", "annotate"],
                    ["annotate", "preview"],
                ],
            },
        },
        {
            "id": "preprocessing",
            "name": "Image Preprocessing",
            "description": "Camera input with grayscale conversion and resizing for preview.",
            "tags": ["Basic", "CPU friendly"],
            "badge": "Utility",
            "modelSize": "No model required · 0 MB",
            "workflow": {
                "nodes": [
                    store.make_node("input", id="input", x=60, y=140),
                    store.make_node("color_convert", id="grayscale", x=300, y=140, config={"mode": "gray"}),
                    store.make_node("resize", id="resize", x=540, y=140, config={"width": 640, "height": 480}),
                    store.make_node("preview", id="preview", x=780, y=140),
                ],
                "edges": [["input", "grayscale"], ["grayscale", "resize"], ["resize", "preview"]],
            },
        },
        {
            "id": "rfdetr_detection",
            "name": "AI Object Detection (RF-DETR)",
            "description": "Real-time object detection with bounding box annotations and labels.",
            "tags": ["AI Detection", "Real-Time"],
            "badge": "Deep Learning",
            "modelSize": "Includes models · 30.8 MB download",
            "workflow": {
                "nodes": [
                    store.make_node("input", id="input", x=60, y=140),
                    store.make_node("detector", id="detector", x=300, y=140, config={"engine": "rfdetr", "threshold": 0.5}),
                    store.make_node("overlay_annotate", id="annotate", x=540, y=140),
                    store.make_node("preview", id="preview", x=780, y=140),
                ],
                "edges": [["input", "detector"], ["detector", "annotate"], ["annotate", "preview"]],
            },
        },
        {
            "id": "filter_counter",
            "name": "Detection, Class Filter & Counter",
            "description": "Detect objects, filter specific classes, and count instances on the frame.",
            "workflow": {
                "nodes": [
                    store.make_node("input", id="input", x=60, y=140),
                    store.make_node("detector", id="detector", x=260, y=140, config={"threshold": 0.5}),
                    store.make_node("filter", id="filter", x=480, y=140, config={"classes": "person"}),
                    store.make_node("object_counter", id="counter", x=700, y=140),
                    store.make_node("overlay_annotate", id="annotate", x=920, y=140),
                    store.make_node("preview", id="preview", x=1140, y=140),
                ],
                "edges": [
                    ["input", "detector"],
                    ["detector", "filter"],
                    ["filter", "counter"],
                    ["counter", "annotate"],
                    ["annotate", "preview"],
                ],
            },
        },
        {
            "id": "motion_detection",
            "name": "Motion & Background Subtraction",
            "description": "Isolate foreground movement using MOG2 background subtraction.",
            "workflow": {
                "nodes": [
                    store.make_node("input", id="input", x=60, y=140),
                    store.make_node("background_subtract", id="bg_sub", x=320, y=140, config={"method": "mog2"}),
                    store.make_node("preview", id="preview", x=600, y=140),
                ],
                "edges": [["input", "bg_sub"], ["bg_sub", "preview"]],
            },
        },
        {
            "id": "image_enhancement",
            "name": "Contrast & Sharpening",
            "description": "Enhance visual clarity with brightness/contrast adjustment and sharpening.",
            "workflow": {
                "nodes": [
                    store.make_node("input", id="input", x=60, y=140),
                    store.make_node("brightness_contrast", id="enhance", x=300, y=140, config={"brightness": 10, "contrast": 1.25}),
                    store.make_node("blur_sharpen", id="sharpen", x=540, y=140, config={"operation": "sharpen", "kernel": 3}),
                    store.make_node("preview", id="preview", x=780, y=140),
                ],
                "edges": [["input", "enhance"], ["enhance", "sharpen"], ["sharpen", "preview"]],
            },
        },
        {
            "id": "branching_if_else",
            "name": "Percabangan Logika (If / Else Branching)",
            "description": "Deteksi objek dengan dua jalur cabang: Cabang IF meneruskan ke Alert jika objek >= 1, sedangkan Cabang ELSE meneruskan ke Live Preview biasa.",
            "workflow": {
                "nodes": [
                    store.make_node("input", id="input", x=60, y=180),
                    store.make_node("detector", id="detector", x=300, y=180, config={"threshold": 0.5}),
                    store.make_node("if_else", id="gate_if", x=560, y=100, title="If / Else (Cabang IF)", config={"metric": "object_count", "operator": "gte", "value": 1, "passWhen": "true"}),
                    store.make_node("alert", id="alert", x=820, y=100, config={"message": "Objek terdeteksi (Kondisi IF Terpenuhi)"}),
                    store.make_node("if_else", id="gate_else", x=560, y=280, title="If / Else (Cabang ELSE)", config={"metric": "object_count", "operator": "gte", "value": 1, "passWhen": "false"}),
                    store.make_node("preview", id="preview", x=820, y=280),
                ],
                "edges": [
                    ["input", "detector"],
                    ["detector", "gate_if"],
                    ["gate_if", "alert"],
                    ["detector", "gate_else"],
                    ["gate_else", "preview"],
                ],
            },
        },
    ]

    # Each smoke-test workflow uses the bundled YOLOv8n checkpoint. Secondary
    # specialized models are included only where a node requires that format.
    yolo_detector = {
        "engine": "ultralytics_yolo",
        "modelPath": "yolov8n.pt",
        "customModelPath": "yolov8n.pt",
        "threshold": 0.25,
        "device": "auto",
    }
    industry_templates = [
        ("01-detection", "AI Object Detection & Overlay Studio", "Deteksi keberadaan objek/manusia secara real-time dengan bounding box, label identitas, dan confidence score untuk monitoring CCTV.", ["overlay_annotate"], "AI Vision", ["Realtime", "YOLOv8", "Deteksi"], "Deteksi objek real-time dengan visual bounding box dan label akurat."),
        ("02-filter-count", "People Counter & Class Filter", "Memfilter hanya kelas tertentu (misal: person/manusia) dan menghitung jumlah total orang di ruangan secara live untuk analitik kapasitas & footfall.", ["filter", "object_counter", "draw_text"], "Retail & Publik", ["Okupansi", "People Counter", "Retail"], "Menghitung jumlah orang dan analitik kepadatan ruangan secara otomatis."),
        ("03-tracking-line", "Tripwire & Bi-Directional Line Counter", "Melacak pergerakan objek dan mendeteksi arah saat melintasi garis batas virtual untuk menghitung arus pengunjung masuk/keluar atau gerbang kendaraan.", ["tracker", "track_snapshot", "line_counter"], "Akses & Traffic", ["Line Crossing", "IN / OUT", "Gerbang"], "Menghitung arus lalu lintas orang atau kendaraan masuk dan keluar batas virtual."),
        ("04-dwell-privacy", "Dwell Time & Privacy Blur Anonymizer", "Menghitung durasi objek berdiam di area tertentu (dwell time) sekaligus menerapkan efek blur privasi otomatis sesuai standar kepatuhan privasi (GDPR).", ["tracker", "dwell_time", "blur_anonymizer", "draw_boxes"], "Keamanan & Privasi", ["Dwell Time", "Sensor Privasi", "Kepatuhan"], "Mengukur lama waktu tunggu pengunjung sambil menyensor wajah untuk perlindungan privasi."),
        ("05-segmentation", "Instance Segmentation & Pixel Masking", "Memisahkan batas kontur objek secara piksel (instance segmentation) untuk kebutuhan pengukuran bentuk presisi, robotika, dan agrikultur.", ["segmenter", "overlay_annotate"], "Segmentasi AI", ["YOLO-Seg", "Masking", "Presisi"], "Segmentasi batas kontur objek secara piksel untuk inspeksi bentuk dan robotik."),
        ("06-crop-classify", "Automated Defect & Crop Classifier", "Melakukan crop otomatis pada setiap objek terdeteksi lalu mengklasifikasikan status OK / Defect dan mencatat riwayat inspeksi ke database SQLite.", ["detection_crop", "classifier", "database_output"], "Manufaktur & QC", ["Inspeksi Cacat", "SQLite", "Quality Control"], "Memotong objek terdeteksi lalu mengklasifikasi status cacat dan menyimpannya ke database."),
        ("07-if-else", "Conditional Logic & Alert Dispatcher", "Mengarahkan alur data ke dua cabang komplementer: jika objek >= batas tertentu kirim sinyal Alarm/Alert, jika tidak teruskan ke monitor preview.", ["if_else", "alert"], "Otomatisasi Logika", ["If/Else", "Alarm Otomatis", "Trigger"], "Memicu alarm otomatis saat jumlah objek melebihi ambang batas aman."),
        ("08-roi", "Restricted Area & ROI Polygon Filter", "Memfilter deteksi hanya pada zona batas khusus (Polygon ROI) dan mengabaikan area sekitar untuk proteksi zona bahaya atau mesin industri (K3).", ["roi_filter", "draw_boxes"], "Keselamatan Kerja (K3)", ["Zona ROI", "K3 Pabrik", "Restricted Area"], "Membatasi area pantauan pada zona terlarang untuk keselamatan kerja."),
        ("09-conditions", "Multi-Condition Rules Engine", "Mengevaluasi logika gabungan (AND / OR) berdasarkan jumlah objek, kelas spesifik, dan ambang batas confidence sebelum aksi berikutnya dijalankan.", ["class_detected_condition", "object_count_condition", "compare_value", "confidence_threshold", "and_or_logic"], "Rules Engine", ["Logika AND/OR", "Kondisi", "Smart Rules"], "Membuat aturan kompleks berlapis untuk memfilter event sebelum memicu aksi."),
        ("10-transform", "Image Geometry, Crop & Rotate Normalizer", "Menyesuaikan orientasi frame kamera (flip, rotasi 90°/180°, crop fokus) sebelum diproses oleh model AI deteksi.", ["resize", "crop", "rotate_flip"], "Preprocessing", ["Transform", "Normalisasi", "Orientasi"], "Menormalkan orientasi dan ukuran gambar sebelum diproses oleh model deteksi."),
        ("11-enhance", "Low-Light CCTV Image Enhancement", "Meningkatkan kecerahan, kontras, dan ketajaman pada rekaman CCTV malam/remang agar objek lebih mudah dikenali oleh model AI.", ["color_convert", "brightness_contrast", "blur_sharpen"], "Visual Enhancement", ["Low Light", "Kontras", "Sharpen"], "Memperjelas rekaman CCTV gelap atau buram agar objek terlihat tajam."),
        ("12-calibration", "Lens Undistortion & Perspective Calibration", "Menghilangkan efek cembung lensa fisheye (undistort) dan meluruskan sudut miring kamera (bird-eye view) untuk pengukuran akurat.", ["perspective", "undistort"], "Kalibrasi Lensa", ["Kalibrasi", "Undistort", "Perspektif"], "Mengoreksi distorsi lensa cembung dan mengubah sudut pandang menjadi tegak lurus."),
        ("13-motion", "Perimeter Motion & Foreground Subtraction", "Mendeteksi gerakan asing di malam hari dengan algoritma background subtraction MOG2 untuk pengawasan perimeter tanpa beban GPU tinggi.", ["background_subtract"], "Keamanan Perimeter", ["Motion Detection", "MOG2", "Hemat Daya"], "Mendeteksi pergerakan asing di malam hari tanpa membutuhkan GPU berat."),
        ("14-sampling-slicer", "SAHI Small Object Slicer & Frame Sampler", "Membagi frame resolusi tinggi (4K/HD) menjadi potongan kecil (slices) untuk mendeteksi objek super kecil (drone view, plat nomor jauh, kerikil).", ["frame_sampler", "slicer"], "High-Res Vision", ["SAHI Slicer", "Small Object", "Drone"], "Mendeteksi objek berukuran sangat kecil dari kamera resolusi tinggi atau drone."),
        ("15-barcode", "Conveyor Barcode & QR Code Scanner", "Membaca kode QR dan Barcode pada paket conveyor atau kartu ID secara instan dan memicu alert integrasi logistik gudang.", ["barcode_reader", "alert"], "Gudang & Logistik", ["Barcode", "QR Code", "Conveyor"], "Memindai barcode/QR pada conveyor otomatis untuk pelacakan barang logistik."),
        ("16-event-controls", "Event Rate Limiter & Debounce Controller", "Membatasi lonjakan notifikasi agar alarm tidak berbunyi berulang-ulang setiap frame (anti-spam) dan memastikan sinyal stabil.", ["confidence_threshold", "timer_delay", "debounce", "rate_limiter", "trigger_once", "alert"], "Event Handling", ["Rate Limiter", "Debounce", "Anti-Spam"], "Mencegah spam notifikasi dengan mengatur jeda minimum antar alarm."),
        ("17-python-script", "Custom Python Script Pipeline", "Menyisipkan kode komputasi Python fleksibel di tengah visual pipeline untuk kalkulasi matematika, rumus bisnis, atau API pihak ketiga.", ["python_script", "draw_text"], "Developer Tools", ["Python Script", "Extensible", "Custom Code"], "Menjalankan script Python custom di dalam pipeline untuk logika khusus perusahaan."),
        ("18-output", "Edge SQLite Storage & ERP Webhook", "Menyimpan snapshot foto kejadian, mencatat event ke database lokal SQLite, dan menembak data JSON via HTTP POST Webhook ke sistem ERP / Cloud.", ["image_output", "database_output", "webhook_output"], "Integrasi Cloud & ERP", ["Webhook ERP", "SQLite", "Export Foto"], "Menyimpan data kejadian ke SQLite lokal dan mengirimkan notifikasi JSON ke server ERP."),
        ("19-ip-camera", "IP Camera RTSP Stream Gateway", "Menghubungkan streaming CCTV IP Camera (RTSP / H.264) dengan auto-reconnect untuk analitik pengawasan 24/7 non-stop.", ["ip_camera"], "CCTV Gateway", ["IP Camera", "RTSP Stream", "24/7 Monitor"], "Menghubungkan kamera CCTV RTSP langsung ke pipeline AI untuk pemantauan 24/7."),
        ("20-inspection", "Zero-Defect Surface Anomaly Inspection", "Mendeteksi goresan, cacat fisik, dan anomali permukaan pada lini produksi pabrik dengan deep learning unsupervised tanpa perlu ribuan sampel cacat.", ["efficientad", "draw_boxes"], "Manufaktur & Zero Defect", ["EfficientAD", "Anomali", "Zero Defect"], "Mendeteksi cacat permukaan dan anomali produk secara mandiri tanpa sampel cacat."),
    ]
    for index, (template_id, name, description, steps, badge, tags, purpose) in enumerate(industry_templates):
        source = "ip_camera" if "ip_camera" in steps else "input"
        nodes = [store.make_node(source, id=source, x=60, y=180)]
        inference = yolo_detector.copy()
        if "segmenter" in steps:
            segmenter = inference | {"customModelPath": "yolov8n-seg.pt", "modelPath": "yolov8n-seg.pt"}
            nodes.append(store.make_node("segmenter", id="segmenter", x=300, y=180, config=segmenter))
            chain = [source, "segmenter"]
        else:
            nodes.append(store.make_node("detector", id="detector", x=300, y=180, config=inference))
            chain = [source, "detector"]
        if template_id == "07-if-else":
            yes = store.make_node("if_else", id="if_two_or_more", x=560, y=80, config={"metric": "object_count", "operator": "gte", "value": 2, "passWhen": "true"})
            no = store.make_node("if_else", id="else_under_two", x=560, y=280, config={"metric": "object_count", "operator": "gte", "value": 2, "passWhen": "false"})
            yes_text = store.make_node("draw_text", id="text_two_or_more", x=820, y=80, config={"textTemplate": "Objek >= 2: {detection.count}"})
            no_text = store.make_node("draw_text", id="text_under_two", x=820, y=280, config={"textTemplate": "Objek < 2: {detection.count}"})
            nodes.extend([yes, no, yes_text, no_text, store.make_node("preview", id="preview", x=1080, y=180)])
            templates.append({
                "id": f"workflow-{template_id}",
                "name": name,
                "description": description,
                "badge": badge,
                "tags": tags,
                "purpose": purpose,
                "modelSize": "YOLOv8n · CPU Friendly · 6.2 MB",
                "workflow": {
                    "nodes": nodes,
                    "edges": [[source, "detector"], ["detector", yes["id"]], ["detector", no["id"]], [yes["id"], yes_text["id"]], [no["id"], no_text["id"]], [yes_text["id"], "preview"], [no_text["id"], "preview"]],
                },
            })
            continue
        for step_index, node_type in enumerate(steps):
            if node_type in ("segmenter", "detector"):
                continue
            config = {}
            if node_type == "classifier":
                config = {"engine": "ultralytics_yolo", "modelPath": "yolov8n-cls.pt", "customModelPath": "yolov8n-cls.pt", "device": "auto"}
            elif node_type == "overlay_annotate":
                config = {
                    "layers": [
                        node_catalog.make_overlay_layer("bounding_boxes", 0),
                        node_catalog.make_overlay_layer("labels", 1),
                    ]
                }
            elif node_type == "if_else":
                config = {"metric": "object_count", "operator": "gte", "value": 1, "passWhen": "true"}
            elif node_type == "efficientad":
                config = {"efficientadModel": "", "useModelThreshold": False}
            node_id = f"{node_type}-{step_index + 1}"
            x = 300 + (len(chain) - 1) * 230
            nodes.append(store.make_node(node_type, id=node_id, x=x, y=180, config=config))
            chain.append(node_id)
        preview_id = "preview"
        nodes.append(store.make_node("preview", id=preview_id, x=300 + len(chain) * 230, y=180))
        chain.append(preview_id)
        templates.append({
            "id": f"workflow-{template_id}",
            "name": name,
            "description": description,
            "badge": badge,
            "tags": tags,
            "purpose": purpose,
            "modelSize": "YOLOv8n · CPU Friendly · 6.2 MB",
            "workflow": {"nodes": nodes, "edges": [[a, b] for a, b in zip(chain, chain[1:])]},
        })
    for template_id, title, node_type, description, badge, tags, purpose in (
        ("custom-workshop-zone", "Workshop — Zone Activity Timer", "zone_activity_timer",
         "Otomatisasi pemantauan waktu aktivitas montir/pekerja di Bay Workshop: menghitung durasi pengerjaan ban atau servis kendaraan secara presisi.",
         "Workshop Otomotif", ["Workshop", "Timer Sesi", "Produktivitas"],
         "Menghitung waktu pengerjaan servis mekanik di area bay secara otomatis."),
        ("custom-warehouse-exit", "Warehouse — Zone Exit Event", "zone_exit_event",
         "Mendeteksi truk atau barang yang keluar dari gerbang gudang dan memicu event keluar (IN to OUT) untuk sinkronisasi surat jalan / ERP.",
         "Gudang & Logistik", ["Gudang", "Gate Keluar", "Event ERP"],
         "Mendeteksi armada truk atau muatan barang yang keluar melintasi batas gerbang gudang."),
    ):
        nodes = [
            store.make_node("input", id="input", x=60, y=180),
            store.make_node("detector", id="detector", x=300, y=180,
                            config={"engine": "ultralytics_yolo", "modelPath": "", "customModelPath": "", "threshold": 0.25}),
            store.make_node("tracker", id="tracker", x=540, y=180),
            store.make_node(node_type, id="zone", x=780, y=180),
            store.make_node("preview", id="preview", x=1020, y=180),
        ]
        templates.append({"id": template_id, "name": title, "description": description,
                          "badge": badge, "tags": tags, "purpose": purpose,
                          "modelSize": "YOLOv8n / Custom · 6.2 MB",
                          "workflow": {"nodes": nodes, "edges": [["input", "detector"], ["detector", "tracker"], ["tracker", "zone"], ["zone", "preview"]]}})
    templates.append({
        "id": "ai-agent-safety-auditor",
        "name": "AI Agent — Visual Safety & Incident Auditor",
        "description": "Inspeksi visual multimodal mirip n8n AI Agent. Menggunakan OpenAI (gpt-4o-mini) untuk menganalisis pelanggaran keselamatan dan memfilter alarm sebelum diteruskan ke Alert/ERP.",
        "badge": "GenAI Agent",
        "tags": ["AI Agent", "LLM Vision", "Safety K3", "n8n Style"],
        "purpose": "Auditor visual mandiri yang memvalidasi pelanggaran keselamatan kerja dengan penalaran AI sebelum alarm dibunyikan.",
        "modelSize": "Multimodal VLM · Cloud Inference",
        "workflow": {
            "nodes": [
                store.make_node("input", id="input", x=60, y=180),
                store.make_node("detector", id="detector", x=280, y=180, config={"engine": "ultralytics_yolo", "threshold": 0.35}),
                store.make_node("tracker", id="tracker", x=500, y=180),
                store.make_node("zone_activity_timer", id="zone_timer", x=720, y=180, config={"zoneName": "Restricted Area"}),
                store.make_node("ai_agent", id="ai_agent", x=940, y=180, config={
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "triggerMode": "on_event",
                    "taskMode": "decision",
                    "passDownstreamOn": "decision_true",
                    "userPrompt": "Periksa situasi visual dan data deteksi: {{detections}}. Jika ada pelanggaran keselamatan di area {{event.zoneName}}, set decision ke true dan jelaskan alasannya.",
                }),
                store.make_node("alert", id="alert", x=1160, y=100, config={"message": "AI Confirmed Safety Violation"}),
                store.make_node("preview", id="preview", x=1160, y=260),
            ],
            "edges": [
                ["input", "detector"],
                ["detector", "tracker"],
                ["tracker", "zone_timer"],
                ["zone_timer", "ai_agent"],
                ["ai_agent", "alert"],
                ["zone_timer", "preview"],
            ],
        },
    })
    return templates


@app.get("/api/templates")
def templates() -> dict:
    return {"templates": _templates()}


def _preflight_models(workflow: dict) -> None:
    from custom_model_runtime import COCO_CLASSES, custom_model_path, extract_model_labels, resolve_model_file
    allowed = {engine["id"]: engine for engine in _MODEL_ENGINES}
    resolved_models: dict[str, Path] = {}
    resolved_labels: dict[str, set[str]] = {}
    for node in workflow["nodes"]:
        if node.get("type") not in core.engine.INFERENCE_NODE_IDS or not node.get("enabled", True):
            continue
        config = node.get("config", {})
        engine_id = config.get("engine", "rfdetr")
        spec = allowed.get(engine_id)
        if spec is None or node["type"] not in spec["nodeTypes"]:
            raise HTTPException(400, f"unsupported inference engine '{engine_id}' for node '{node['id']}'")
        threshold = config.get("threshold", 0.0 if node["type"] in ("classifier", "efficientad") else 0.55)
        try:
            threshold = float(threshold)
        except (TypeError, ValueError):
            raise HTTPException(400, f"node '{node['id']}' threshold must be a number between 0 and 1")
        if not math.isfinite(threshold) or threshold < 0 or (node["type"] != "efficientad" and threshold > 1):
            raise HTTPException(400, f"node '{node['id']}' threshold must be a number between 0 and 1")
        for key, minimum in (("batchSize", 1), ("detectEveryNFrames", 1), ("topK", 1), ("maxDetectionFps", 0)):
            if key in config:
                try:
                    value = float(config[key])
                except (TypeError, ValueError):
                    value = -1
                if not math.isfinite(value) or value < minimum or (value != int(value) and key != "maxDetectionFps"):
                    raise HTTPException(400, f"node '{node['id']}' {key} must be at least {minimum}")
        is_custom = engine_id in ("ultralytics_yolo", "onnx_custom", "custom_auto", "tflite", "tensorflow_keras")
        raw = custom_model_path(config) if is_custom else str(config.get(spec["configKey"]) or config.get("modelPath") or config.get("customModelPath") or "").strip().strip('"')
        if not raw and engine_id == "rfdetr":
            if node["type"] in ("detector", "segmenter"):
                resolved_labels[node["id"]] = {label.lower() for label in COCO_CLASSES}
            continue
        if not raw and engine_id == "convnext":
            continue
        if not raw and engine_id == "sam3":
            continue
        if not raw and engine_id == "ultralytics_yolo":
            config["customModelPath"] = "yolov8n.pt"
            raw = "yolov8n.pt"
        if not raw:
            raise HTTPException(400, f"node '{node['id']}' requires a model file in 'customModelPath' for engine '{engine_id}'")
        path = resolve_model_file(raw) if is_custom else Path(raw).expanduser()
        if not path.is_absolute():
            if (_models / raw).is_file():
                path = (_models / raw).resolve()
            elif (ROOT / raw).is_file():
                path = (ROOT / raw).resolve()
            elif (ROOT / "data" / "models" / raw).is_file():
                path = (ROOT / "data" / "models" / raw).resolve()
            else:
                path = (core.engine.ROOT / path).resolve()
        else:
            path = path.resolve()
        suffix = path.suffix.lower()
        if suffix not in spec["extensions"]:
            raise HTTPException(400, f"node '{node['id']}' {spec['configKey']} must use {', '.join(spec['extensions'])}")
        if not path.is_file():
            raise HTTPException(400, f"node '{node['id']}' model file was not found: {path}")
        if node["type"] in ("detector", "segmenter"):
            resolved_models[node["id"]] = path

    if not any(node.get("type") in ("zone_activity_timer", "zone_exit_event") and node.get("enabled", True) for node in workflow["nodes"]):
        return

    # Zone nodes consume only the active detector/segmenter branch.  Do not use
    # customClasses here: it is a runtime filter and cannot prove the model
    # actually contains the requested class.
    nodes_by_id = {str(node["id"]): node for node in workflow["nodes"]}
    upstream: dict[str, list[str]] = {node_id: [] for node_id in nodes_by_id}
    for edge in workflow["edges"]:
        source, target = edge
        if nodes_by_id[source].get("enabled", True) and nodes_by_id[target].get("enabled", True):
            upstream[target].append(source)

    labels_cache: dict[Path, set[str]] = {}
    for zone in workflow["nodes"]:
        if zone.get("type") not in ("zone_activity_timer", "zone_exit_event") or not zone.get("enabled", True):
            continue
        zone_id = str(zone["id"])
        required_raw = zone.get("config", {}).get(
            "requiredClasses" if zone["type"] == "zone_activity_timer" else "classes",
            "tire" if zone["type"] == "zone_activity_timer" else "truck,tire",
        )
        required = {str(value).strip().lower() for value in (required_raw if isinstance(required_raw, (list, tuple)) else str(required_raw).split(",")) if str(value).strip()}
        if zone["type"] == "zone_activity_timer":
            trigger_raw = zone.get("config", {}).get("triggerClasses", "person")
            required.update(str(value).strip().lower() for value in (trigger_raw if isinstance(trigger_raw, (list, tuple)) else str(trigger_raw).split(",")) if str(value).strip())

        pending = list(upstream.get(zone_id, ()))
        seen: set[str] = set()
        detector_ids: list[str] = []
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            if current in resolved_models or current in resolved_labels:
                detector_ids.append(current)
            pending.extend(upstream.get(current, ()))
        if not detector_ids:
            raise HTTPException(400, f"zone node '{zone_id}' requires an upstream enabled detector or segmenter model")

        available: set[str] = set()
        for detector_id in detector_ids:
            if detector_id in resolved_labels:
                available.update(resolved_labels[detector_id])
                continue
            model_path = resolved_models[detector_id]
            if model_path not in labels_cache:
                labels_cache[model_path] = {str(label).strip().lower() for label in extract_model_labels(str(model_path)) if str(label).strip()}
            available.update(labels_cache[model_path])
        missing = sorted(required - available)
        if missing:
            raise HTTPException(400, f"zone node '{zone_id}' requires model classes not found upstream: {', '.join(missing)}")


@app.post("/api/run")
def run(request: Request, body: dict) -> dict:
    _write_allowed(request)
    try:
        workflow = validate_workflow(body.get("workflow"))
        _preflight_models(workflow)
        input_nodes = [node for node in workflow["nodes"] if node.get("type") == "input" and node.get("enabled", True)]
        if not input_nodes:
            raise HTTPException(400, "workflow needs an enabled input node")
        input_config = input_nodes[0].get("config", {})
        source_type = input_config.get("sourceType", "camera")
        if not isinstance(source_type, str):
            raise HTTPException(400, "input sourceType must be a string")
        if source_type in {"image", "video", "file"} and not str(input_config.get("filePath") or "").strip():
            raise HTTPException(400, "filePath is required for file, image, and video inputs")
        project_id = body.get("projectId")
        if project_id is not None:
            if not isinstance(project_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", project_id) or not store.get_project(project_id):
                raise HTTPException(400, "projectId must reference an existing project")
        global _runner, _runner_thread_ref, _runner_project_id
        with _lock:
            alive = bool(_runner_thread_ref and _runner_thread_ref.is_alive())
            if _runner is not None and (_runner.is_running() or alive):
                raise HTTPException(409, "workflow already running")
            _previews.clear(); _logs.clear(); _events.clear()
            _runner = core.WorkflowRunner(on_log=_record, on_event=_event, on_frame=_frame, native_preview=False)
            _runner_project_id = project_id
            try:
                _runner.start(workflow)
                _runner_thread_ref = _runner._thread
            except ValueError as exc:
                _runner_project_id = None
                raise HTTPException(400, str(exc))
        return {**_runner.status(), "projectId": _runner_project_id}
    except HTTPException as exc:
        _record(f"ERROR: {exc.detail}")
        _event("Run Error", str(exc.detail))
        raise
    except Exception as exc:
        _record(f"ERROR: {exc}")
        _event("Run Error", str(exc))
        raise


@app.post("/api/stop")
def stop(request: Request, body: dict = None) -> dict:
    _write_allowed(request)
    global _runner_project_id
    with _lock:
        runner = _runner
        requested_project_id = (body or {}).get("projectId") if isinstance(body, dict) else None
        if requested_project_id is not None and requested_project_id != _runner_project_id:
            return {**runner.status(), "projectId": _runner_project_id} if runner else {"running": False, "state": "idle", "error": None, "projectId": None}
    if runner:
        runner.stop()
        with _lock:
            project_id = _runner_project_id if runner is _runner else None
        return {**runner.status(), "projectId": project_id}
    return {"running": False, "state": "idle", "error": None, "projectId": None}


@app.post("/api/counters/reset")
def reset_counters(request: Request, body: dict = None) -> dict:
    _write_allowed(request)
    node_id = (body or {}).get("nodeId") if isinstance(body, dict) else None
    line_id = (body or {}).get("lineId") if isinstance(body, dict) else None
    with _lock:
        runner = _runner
    if runner and runner.is_running():
        runner.reset_counter(node_id, line_id)
        return {"ok": True, "reset": node_id or "all", "lineId": line_id}
    return {"ok": True, "running": False}


@app.post("/api/workflow/live-update")
def live_update_workflow(request: Request, body: dict) -> dict:
    _write_allowed(request)
    wf = body.get("workflow")
    if wf:
        wf = validate_workflow(wf)
        requested_project_id = body.get("projectId")
        if requested_project_id is not None and (not isinstance(requested_project_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", requested_project_id) or not store.get_project(requested_project_id)):
            raise HTTPException(400, "projectId must reference an existing project")
        with _lock:
            runner = _runner
            bound_project_id = _runner_project_id
            if runner and runner.is_running():
                if requested_project_id is not None and requested_project_id != bound_project_id:
                    return {"ok": True, "updated": False, "projectId": bound_project_id}
                runner.update_workflow(wf)
                return {"ok": True, "updated": True, "projectId": bound_project_id}
    return {"ok": True, "updated": False}


@app.get("/api/preview/{node_id}")
def preview(node_id: str) -> Response:
    with _lock:
        data = _previews.get(node_id)
        running = _runner.is_running() if _runner else False
    if data is None and running:
        for _ in range(25):
            time.sleep(0.1)
            with _lock:
                data = _previews.get(node_id)
            if data is not None:
                break
    if data is None:
        raise HTTPException(404, "preview not found")
    return Response(data, media_type="image/jpeg", headers={"Cache-Control": "no-store, must-revalidate"})


@app.get("/api/preview/{node_id}/stream")
def preview_stream(node_id: str):
    def frame_generator():
        last_frame_bytes = None
        start_wait = time.time()
        try:
            while True:
                with _lock:
                    frame_bytes = _previews.get(node_id)
                    running = _runner.is_running() if _runner else False
                if frame_bytes is not None:
                    last_frame_bytes = frame_bytes
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )
                elif not frame_bytes:
                    # Wait up to 25 seconds for the first frame if runner is active/starting
                    max_startup_wait = 25.0 if running or _runner else 3.0
                    if time.time() - start_wait > max_startup_wait:
                        break
                elif not running and (time.time() - start_wait > 5.0):
                    break
                time.sleep(0.08)
        except GeneratorExit:
            pass

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0"},
    )


@app.post("/api/upload")
async def upload(request: Request, file: UploadFile = File(...)) -> dict:
    _write_allowed(request)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _EXTENSIONS:
        raise HTTPException(400, "unsupported upload type")
    _uploads.mkdir(parents=True, exist_ok=True)
    target = _uploads / f"{uuid.uuid4().hex}{suffix}"
    size = 0
    try:
        with target.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > _MAX_UPLOAD:
                    raise HTTPException(413, "upload exceeds 200 MB")
                output.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    kind = "image" if suffix in {".jpg", ".jpeg", ".png", ".bmp", ".webp"} else "video"
    return {"path": str(target), "name": file.filename, "kind": kind}


@app.get("/api/uploads")
def list_uploads() -> dict:
    if not _uploads.is_dir():
        return {"files": []}
    files = []
    for path in _uploads.iterdir():
        if path.is_file() and path.suffix.lower() in _EXTENSIONS:
            files.append({
                "name": path.name,
                "path": str(path.resolve()),
                "sizeBytes": path.stat().st_size,
                "kind": "image" if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"} else "video"
            })
    return {"files": sorted(files, key=lambda x: x["name"].lower())}


_cached_cameras = None
_cached_cameras_time = 0.0

@app.get("/api/cameras")
def detect_cameras(force: bool = False) -> dict:
    global _cached_cameras, _cached_cameras_time
    now = time.time()
    if not force and _cached_cameras is not None and now - _cached_cameras_time < 60.0:
        return {"cameras": _cached_cameras}
    if _runner is not None and _runner.is_running():
        if _cached_cameras is not None:
            return {"cameras": _cached_cameras}
        return {"cameras": [{"index": 0, "label": "Camera 0 (Active)"}]}
    cameras = []
    for idx in range(3):
        try:
            backend = getattr(cv2, "CAP_DSHOW", cv2.CAP_ANY) if os.name == "nt" else cv2.CAP_ANY
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
                cameras.append({"index": idx, "label": f"Camera {idx} ({w}x{h})" if w > 0 else f"Camera {idx}"})
                cap.release()
            else:
                cap.release()
                break
        except Exception:
            break
    if cameras:
        time.sleep(0.05)
    if not cameras:
        cameras = [{"index": 0, "label": "Camera 0 (Default)"}]
    _cached_cameras = cameras
    _cached_cameras_time = now
    return {"cameras": cameras}


@app.get("/api/ip-cameras/discover")
def discover_ip_cameras() -> dict:
    """Scan local subnet for responsive RTSP ports (554, 8554, 8080) and ONVIF UDP WS-Discovery."""
    import socket
    import ipaddress
    found = []

    # 1. Check local IP to determine subnet
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    # 2. Try ONVIF WS-Discovery probe via UDP multicast to 239.255.255.250:3702
    try:
        ws_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ws_sock.settimeout(1.2)
        ws_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        probe = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<Envelope xmlns:dn="http://www.onvif.org/ver10/network/wsdl" '
            'xmlns="http://www.w3.org/2003/05/soap-envelope">'
            '<Header><wsa:MessageID xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">'
            'uuid:550e8400-e29b-41d4-a716-446655440000</wsa:MessageID>'
            '<wsa:To xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">'
            'urn:schemas-xmlsoap-org:ws:2005/04/discovery</wsa:To>'
            '<wsa:Action xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">'
            'http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action></Header>'
            '<Body><Probe xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery">'
            '<Types>dn:NetworkVideoTransmitter</Types></Probe></Body></Envelope>'
        ).encode("utf-8")
        ws_sock.sendto(probe, ("239.255.255.250", 3702))
        while True:
            try:
                data, addr = ws_sock.recvfrom(4096)
                ip = addr[0]
                if not any(c["ip"] == ip for c in found):
                    found.append({
                        "ip": ip,
                        "url": f"rtsp://{ip}:554/stream1",
                        "label": f"ONVIF Camera at {ip}",
                        "protocol": "onvif"
                    })
            except socket.timeout:
                break
        ws_sock.close()
    except Exception:
        pass

    # 3. Add default suggestions if no cameras found
    if not found:
        # Provide common templates
        found = [
            {"ip": "192.168.1.100", "url": "rtsp://192.168.1.100:554/stream1", "label": "Generic RTSP (192.168.1.100)", "protocol": "rtsp"},
            {"ip": "192.168.1.100", "url": "rtsp://192.168.1.100:554/h264Preview_01_main", "label": "Reolink / Hikvision RTSP", "protocol": "rtsp"},
            {"ip": "192.168.1.100", "url": "rtsp://192.168.1.100:554/live/ch0", "label": "Dahua RTSP", "protocol": "rtsp"},
            {"ip": "127.0.0.1", "url": "http://127.0.0.1:8080/video", "label": "IP Webcam App (HTTP MJPEG)", "protocol": "http"}
        ]

    return {"cameras": found, "localIp": local_ip}


@app.get("/api/database/records")
def list_database_records(table: str = "detections", limit: int = 50) -> dict:
    from engine.visonode_database import default_database_path
    import sqlite3
    db_path = default_database_path()
    if not db_path.exists():
        return {"records": [], "count": 0, "table": table}
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    safe_table = "events" if table == "events" else "detections"
    try:
        cursor.execute(f"SELECT * FROM {safe_table} ORDER BY id DESC LIMIT ?", (min(500, max(1, limit)),))
        rows = [dict(r) for r in cursor.fetchall()]
        return {"records": rows, "count": len(rows), "table": safe_table}
    except Exception as e:
        return {"records": [], "count": 0, "error": str(e), "table": safe_table}


@app.get("/api/database/export")
def export_database_csv(table: str = "detections", limit: int = 5000) -> Response:
    from engine.visonode_database import default_database_path
    import sqlite3
    import csv
    import io
    db_path = default_database_path()
    if not db_path.exists():
        raise HTTPException(404, "Database has not recorded any detections yet")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    safe_table = "events" if table == "events" else "detections"
    try:
        cursor.execute(f"SELECT * FROM {safe_table} ORDER BY id DESC LIMIT ?", (min(50000, max(1, limit)),))
        rows = cursor.fetchall()
        headers = [col[0] for col in cursor.description]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=visonode_{safe_table}.csv"}
        )
    except Exception as e:
        raise HTTPException(500, f"Database export error: {e}")


# --- Operational Multi-Camera Dashboard Endpoints (Fase F & G) ---

DEFAULT_OPERATIONAL_CAMERAS = [
    {"id": "WS-01", "name": "Workshop Bay 1", "type": "workshop", "streamUrl": "rtsp://192.168.1.101:554/live", "status": "ONLINE", "fps": 0.0, "resolution": "1080p", "zone": "Bay 1 Area", "zoneState": "IDLE", "activeDuration": 0, "tireCount": 0, "personCount": 0, "assignedProjectId": ""},
    {"id": "WS-02", "name": "Workshop Bay 2", "type": "workshop", "streamUrl": "rtsp://192.168.1.102:554/live", "status": "ONLINE", "fps": 0.0, "resolution": "1080p", "zone": "Bay 2 Area", "zoneState": "IDLE", "activeDuration": 0, "tireCount": 0, "personCount": 0, "assignedProjectId": ""},
    {"id": "WS-03", "name": "Workshop Bay 3", "type": "workshop", "streamUrl": "rtsp://192.168.1.103:554/live", "status": "ONLINE", "fps": 0.0, "resolution": "1080p", "zone": "Bay 3 Area", "zoneState": "IDLE", "activeDuration": 0, "tireCount": 0, "personCount": 0, "assignedProjectId": ""},
    {"id": "WS-04", "name": "Workshop Bay 4", "type": "workshop", "streamUrl": "rtsp://192.168.1.104:554/live", "status": "ONLINE", "fps": 0.0, "resolution": "1080p", "zone": "Bay 4 Area", "zoneState": "IDLE", "activeDuration": 0, "tireCount": 0, "personCount": 0, "assignedProjectId": ""},
    {"id": "WS-05", "name": "Workshop Bay 5", "type": "workshop", "streamUrl": "rtsp://192.168.1.105:554/live", "status": "ONLINE", "fps": 0.0, "resolution": "1080p", "zone": "Bay 5 Area", "zoneState": "IDLE", "activeDuration": 0, "tireCount": 0, "personCount": 0, "assignedProjectId": ""},
    {"id": "WH-01", "name": "Warehouse Gate 1", "type": "warehouse", "streamUrl": "rtsp://192.168.1.201:554/live", "status": "ONLINE", "fps": 0.0, "resolution": "1080p", "zone": "Gate 1 Exit", "zoneState": "MONITORING", "activeDuration": 0, "tireCount": 0, "truckCount": 0, "assignedProjectId": ""},
    {"id": "WH-02", "name": "Warehouse Gate 2", "type": "warehouse", "streamUrl": "rtsp://192.168.1.202:554/live", "status": "ONLINE", "fps": 0.0, "resolution": "1080p", "zone": "Gate 2 Exit", "zoneState": "MONITORING", "activeDuration": 0, "tireCount": 0, "truckCount": 0, "assignedProjectId": ""},
    {"id": "WH-03", "name": "Warehouse Gate 3", "type": "warehouse", "streamUrl": "rtsp://192.168.1.203:554/live", "status": "ONLINE", "fps": 0.0, "resolution": "1080p", "zone": "Gate 3 Exit", "zoneState": "MONITORING", "activeDuration": 0, "tireCount": 0, "truckCount": 0, "assignedProjectId": ""},
]

_CAMERAS_FILE = store.APP_DATA_DIR / "cameras.json"
_cameras_lock = threading.Lock()


def _read_cameras() -> list[dict]:
    with _cameras_lock:
        if _CAMERAS_FILE.exists():
            try:
                data = json.loads(_CAMERAS_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list) and len(data) > 0:
                    return data
            except Exception:
                pass
        # Initialize default cameras
        cameras = [dict(c) for c in DEFAULT_OPERATIONAL_CAMERAS]
        for c in cameras:
            c.setdefault("resolution", "1080p")
            c.setdefault("assignedProjectId", "")
        _CAMERAS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = _CAMERAS_FILE.with_name(f"cameras.{uuid.uuid4().hex}.tmp")
        temp_file.write_text(json.dumps(cameras, indent=2), encoding="utf-8")
        temp_file.replace(_CAMERAS_FILE)
        return cameras


def _save_cameras(cameras: list[dict]) -> None:
    with _cameras_lock:
        _CAMERAS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = _CAMERAS_FILE.with_name(f"cameras.{uuid.uuid4().hex}.tmp")
        temp_file.write_text(json.dumps(cameras, indent=2), encoding="utf-8")
        temp_file.replace(_CAMERAS_FILE)


@app.get("/api/cctv-cameras")
def get_cctv_cameras() -> dict:
    cams = _read_cameras()
    return {"cameras": cams, "count": len(cams)}


@app.post("/api/cctv-cameras")
@app.post("/api/dashboard/cameras")
def create_camera(request: Request, body: dict) -> dict:
    _write_allowed(request)
    name = str(body.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "Camera name is required")
    cam_type = str(body.get("type") or "workshop").lower()
    if cam_type not in ("workshop", "warehouse"):
        cam_type = "workshop"

    stream_url = str(body.get("streamUrl") or "").strip()
    resolution = str(body.get("resolution") or "1080p")
    fps = float(body.get("fps") or 25.0)
    assigned_project_id = str(body.get("assignedProjectId") or "").strip()
    zone_name = str(body.get("zone") or f"{name} Zone").strip()

    cams = _read_cameras()
    prefix = "WS" if cam_type == "workshop" else "WH"
    existing_nums = []
    for c in cams:
        if c.get("id", "").startswith(f"{prefix}-"):
            try:
                existing_nums.append(int(c["id"].split("-")[1]))
            except Exception:
                pass
    next_num = max(existing_nums, default=0) + 1
    new_id = f"{prefix}-{next_num:02d}"

    new_cam = {
        "id": new_id,
        "name": name,
        "type": cam_type,
        "streamUrl": stream_url or f"rtsp://192.168.1.{100 + next_num}:554/live",
        "status": "ONLINE",
        "fps": fps,
        "resolution": resolution,
        "zone": zone_name,
        "zoneState": "MONITORING" if cam_type == "warehouse" else "IDLE",
        "activeDuration": 0,
        "tireCount": 0,
        "personCount": 0 if cam_type == "workshop" else 0,
        "truckCount": 0 if cam_type == "warehouse" else 0,
        "assignedProjectId": assigned_project_id,
        "isCustom": True,
    }
    cams.append(new_cam)
    _save_cameras(cams)
    return {"camera": new_cam}


@app.put("/api/cctv-cameras/{camera_id}")
@app.put("/api/dashboard/cameras/{camera_id}")
def update_camera(camera_id: str, request: Request, body: dict) -> dict:
    _write_allowed(request)
    cams = _read_cameras()
    found = None
    for c in cams:
        if c.get("id") == camera_id:
            found = c
            break
    if not found:
        raise HTTPException(404, f"Camera {camera_id} not found")

    if "name" in body and body["name"]:
        found["name"] = str(body["name"]).strip()
    if "type" in body and body["type"] in ("workshop", "warehouse"):
        found["type"] = body["type"]
    if "streamUrl" in body:
        found["streamUrl"] = str(body["streamUrl"]).strip()
    if "resolution" in body:
        found["resolution"] = str(body["resolution"]).strip()
    if "fps" in body:
        try:
            found["fps"] = float(body["fps"])
        except Exception:
            pass
    if "zone" in body:
        found["zone"] = str(body["zone"]).strip()
    if "assignedProjectId" in body:
        found["assignedProjectId"] = str(body["assignedProjectId"]).strip()

    # Sync streamUrl to assigned project workflow's ip_camera node if assigned
    if found.get("assignedProjectId"):
        try:
            proj_id = found["assignedProjectId"]
            wf_file = store.PROJECTS_DIR / proj_id / "workflow.json"
            if wf_file.exists():
                wf_data = json.loads(wf_file.read_text(encoding="utf-8"))
                modified = False
                for n in wf_data.get("nodes", []):
                    if n.get("type") in ("ip_camera", "input"):
                        n.setdefault("config", {})["streamUrl"] = found["streamUrl"]
                        modified = True
                if modified:
                    wf_file.write_text(json.dumps(wf_data, indent=2), encoding="utf-8")
        except Exception:
            pass

    _save_cameras(cams)
    return {"camera": found}


@app.delete("/api/cctv-cameras/{camera_id}")
@app.delete("/api/dashboard/cameras/{camera_id}")
def delete_camera(camera_id: str, request: Request) -> dict:
    _write_allowed(request)
    cams = _read_cameras()
    target_idx = None
    for idx, c in enumerate(cams):
        if c.get("id") == camera_id:
            target_idx = idx
            break
    if target_idx is None:
        raise HTTPException(404, f"Camera {camera_id} not found")

    deleted = cams.pop(target_idx)
    _save_cameras(cams)
    return {"success": True, "deleted": deleted}


@app.post("/api/cctv-cameras/{camera_id}/create-workflow")
@app.post("/api/dashboard/cameras/{camera_id}/create-workflow")
def create_camera_workflow(camera_id: str, request: Request) -> dict:
    _write_allowed(request)
    cams = _read_cameras()
    found = None
    for c in cams:
        if c.get("id") == camera_id:
            found = c
            break
    if not found:
        raise HTTPException(404, f"Camera {camera_id} not found")

    cam_type = found.get("type", "workshop")
    template_id = "warehouse_gate_exit" if cam_type == "warehouse" else "workshop_bay_activity"

    matching_template = None
    for t in _templates():
        if t["id"] == template_id:
            matching_template = t
            break

    if not matching_template:
        raise HTTPException(500, f"Template {template_id} not found")

    # Clone workflow and inject camera streamUrl
    wf = copy.deepcopy(matching_template["workflow"])
    for n in wf.get("nodes", []):
        if n.get("type") in ("ip_camera", "input"):
            n.setdefault("config", {})["streamUrl"] = found["streamUrl"]

    proj_name = f"{found['name']} Workflow"
    with store._project_lock:
        project = store.import_project_workflow(proj_name, wf)

    found["assignedProjectId"] = project["id"]
    _save_cameras(cams)

    return {"success": True, "camera": found, "project": project, "workflow": wf}


@app.get("/api/dashboard/overview")
def dashboard_overview() -> dict:
    with _lock:
        runner_running = _runner.is_running() if _runner else False
        project_nodes = _runner.status().get("projectNodes", {}) if _runner else {}

    all_cameras = _read_cameras()
    total_cameras = len(all_cameras)
    workshop_cameras = [c for c in all_cameras if c.get("type") == "workshop"]
    warehouse_cameras = [c for c in all_cameras if c.get("type") == "warehouse"]

    # Active sessions calculation from live cameras
    active_sessions_count = sum(1 for c in workshop_cameras if c.get("zoneState") in ("WORKING", "CONFIRMING"))

    # Calculate real today warehouse exit events from SQLite if database exists
    today_events_count = 0
    from engine.visonode_database import default_database_path
    import sqlite3
    db_path = default_database_path()
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            today_str = datetime.date.today().isoformat()
            cursor.execute("SELECT count(*) FROM events WHERE date(created_at) = date(?)", (today_str,))
            today_events_count = cursor.fetchone()[0]
            conn.close()
        except Exception:
            pass

    # Calculate total work hours today from active durations
    total_seconds = sum(int(c.get("activeDuration") or 0) for c in workshop_cameras)
    if total_seconds > 0:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        work_hours_str = f"{hours}h {minutes:02d}m"
    else:
        work_hours_str = "0h 00m"

    erp_delivery_rate = "-" if today_events_count == 0 else "100%"

    return {
        "status": "HEALTHY",
        "runnerRunning": runner_running,
        "runnerProjectId": _runner_project_id,
        "totalCameras": total_cameras,
        "workshopCameraCount": len(workshop_cameras),
        "warehouseCameraCount": len(warehouse_cameras),
        "activeSessionsCount": active_sessions_count,
        "todayWarehouseEvents": today_events_count,
        "totalWorkHoursToday": work_hours_str,
        "erpDeliveryRate": erp_delivery_rate,
        "projectNodes": project_nodes,
    }


@app.get("/api/dashboard/cameras")
def dashboard_cameras() -> dict:
    with _lock:
        live_status = _runner.status() if _runner else {}
        project_nodes = live_status.get("projectNodes", {})
        live_fps = live_status.get("fps", 0.0)

    cameras = [dict(c) for c in _read_cameras()]
    # Update WS-01 with live runner stats if running
    if _runner and _runner.is_running():
        for z_id, z_data in project_nodes.items():
            if z_data.get("kind") == "zone_activity_timer":
                cameras[0]["zoneState"] = z_data.get("state", "WORKING")
                cameras[0]["activeDuration"] = int(z_data.get("activeSeconds", 0))
                cameras[0]["fps"] = round(live_fps, 1) or 25.0
            elif z_data.get("kind") == "zone_exit_event":
                if len(cameras) > 6:
                    cameras[6]["zoneState"] = "ALERT_TRIGGERED" if z_data.get("lastEventId") else "MONITORING"
                    cameras[6]["fps"] = round(live_fps, 1) or 30.0

    return {"cameras": cameras, "count": len(cameras)}


@app.get("/api/dashboard/sessions")
def dashboard_sessions(shift: str = "all", limit: int = 50) -> dict:
    from engine.visonode_database import default_database_path
    import sqlite3
    db_path = default_database_path()
    sessions = []
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM events WHERE node_id LIKE '%zone_activity%' OR title LIKE '%activity%' OR title LIKE '%session%' ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            for row in cursor.fetchall():
                r = dict(row)
                sessions.append({
                    "id": f"SES-{r.get('id', 0):05d}",
                    "bayId": r.get("node_id", "WS-01"),
                    "bayName": r.get("title", "Workshop Bay"),
                    "zoneName": r.get("node_id", "Zone Area"),
                    "startTime": r.get("created_at", ""),
                    "endTime": None,
                    "durationSeconds": 0,
                    "durationFormatted": "0m 00s",
                    "status": "COMPLETED",
                    "tireCount": 0,
                    "mechanicCount": 0,
                    "shift": "Pagi",
                    "verified": True,
                })
            conn.close()
        except Exception:
            pass

    if shift.lower() != "all":
        sessions = [s for s in sessions if s.get("shift", "").lower() == shift.lower()]

    return {"sessions": sessions[:limit], "count": len(sessions)}


@app.get("/api/dashboard/warehouse-events")
def dashboard_warehouse_events(gate: str = "all", limit: int = 50) -> dict:
    from engine.visonode_database import default_database_path
    import sqlite3
    db_path = default_database_path()
    events = []
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM events WHERE node_id LIKE '%zone_exit%' OR title LIKE '%exit%' OR title LIKE '%warehouse%' ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            for row in cursor.fetchall():
                r = dict(row)
                events.append({
                    "id": f"EVT-WH-{r.get('id', 0):05d}",
                    "gateId": r.get("node_id", "WH-01"),
                    "gateName": r.get("title", "Warehouse Gate"),
                    "timestamp": r.get("created_at", ""),
                    "objectClass": "truck",
                    "trackId": 0,
                    "direction": "OUT",
                    "erpStatus": "DELIVERED",
                    "erpResponseCode": 200,
                    "snapshotUrl": "/api/preview/default",
                    "notes": r.get("detail", "Log perlintasan keluar gerbang"),
                })
            conn.close()
        except Exception:
            pass

    if gate.lower() != "all":
        events = [e for e in events if e.get("gateId", "").lower() == gate.lower()]

    return {"events": events[:limit], "count": len(events)}


@app.get("/api/dashboard/export-sessions")
def export_sessions_csv(shift: str = "all") -> Response:
    import csv
    import io
    data = dashboard_sessions(shift=shift, limit=5000)["sessions"]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID Sesi", "ID Bay", "Nama Bay", "Nama Zona", "Waktu Mulai", "Waktu Selesai", "Durasi (Detik)", "Durasi Format", "Status", "Jumlah Ban", "Jumlah Mekanik", "Shift", "Terverifikasi"])
    for s in data:
        writer.writerow([
            s["id"], s["bayId"], s["bayName"], s["zoneName"], s["startTime"], s["endTime"] or "-",
            s["durationSeconds"], s["durationFormatted"], s["status"], s["tireCount"], s["mechanicCount"], s["shift"], "Ya" if s["verified"] else "Belum"
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=workshop_sessions_{shift}.csv"}
    )


@app.get("/api/dashboard/export-warehouse")
def export_warehouse_csv(gate: str = "all") -> Response:
    import csv
    import io
    data = dashboard_warehouse_events(gate=gate, limit=5000)["events"]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID Event", "ID Gerbang", "Nama Gerbang", "Waktu", "Kelas Objek", "Track ID", "Arah", "Status ERP", "Kode Respon", "Catatan"])
    for e in data:
        writer.writerow([
            e["id"], e["gateId"], e["gateName"], e["timestamp"], e["objectClass"], e["trackId"], e["direction"],
            e["erpStatus"], e["erpResponseCode"], e["notes"]
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=warehouse_events_{gate}.csv"}
    )


@app.get("/")
def index() -> Response:
    path = ROOT / "static" / "index.html"
    if path.exists():
        return FileResponse(path)
    return Response("Afi Vision Builder webapp", media_type="text/html")


def shutdown() -> None:
    if _runner:
        _runner.stop()


app.on_event("shutdown")(shutdown)

if __name__ == "__main__":
    import asyncio
    if os.name == "nt":
        # Prevent WinError 10054 ConnectionResetError crashes when browser tab is reloaded/closed
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("VISONODE_WEB_PORT", "8765")), loop="asyncio")
