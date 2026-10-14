from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import math
import os
import re
import sys
import threading
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
            if _runner is not None and _runner.is_running():
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
        current = _runner.status() if _runner else {"running": False, "state": "idle", "error": None}
        return {**current, "logs": list(_logs), "events": list(_events), "previews": list(_previews)}


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
    return {
        "path": str(target),
        "name": target.name,
        "engine": engine,
        "format": target.suffix.lower().lstrip("."),
        "task": task,
        "classes": classes,
        "classesCount": len(classes),
        "sizeBytes": target.stat().st_size
    }


def _model_listing() -> list[dict]:
    if not _models.is_dir():
        return []
    result = []
    for path in _models.iterdir():
        if path.is_file() and path.suffix.lower() in _MODEL_EXTENSIONS:
            result.append({"name": path.name, "path": str(path), "format": path.suffix.lower().lstrip("."), "sizeBytes": path.stat().st_size})
        elif path.is_dir():
            for subpath in path.iterdir():
                if subpath.is_file() and subpath.suffix.lower() in _MODEL_EXTENSIONS:
                    result.append({"name": f"{path.name}/{subpath.name}", "path": str(subpath), "format": subpath.suffix.lower().lstrip("."), "sizeBytes": subpath.stat().st_size})
    return sorted(result, key=lambda item: item["name"].lower())


@app.get("/api/models")
def models() -> dict:
    engines = [{**engine, "available": _model_availability(engine["id"])} for engine in _MODEL_ENGINES]
    options = {
        "rfdetr": [{"value": value, "label": label} for value, label in zip(core.engine.RFDETR_DETECTION_MODELS, ("RF-DETR nano", "RF-DETR small", "RF-DETR medium", "RF-DETR large"))],
        "rfdetr_seg": [{"value": value, "label": label} for value, label in zip(core.engine.RFDETR_SEGMENTATION_MODELS, ("RF-DETR-Seg nano", "RF-DETR-Seg small", "RF-DETR-Seg medium", "RF-DETR-Seg large"))],
        "convnext": [{"value": value, "label": value.split(".")[0].replace("_", " ").title()} for value in core.engine.CONVNEXT_MODELS],
    }
    return {"models": _model_listing(), "engines": engines, "options": options}


@app.post("/api/models/upload")
async def upload_model(request: Request, file: UploadFile = File(...)) -> dict:
    _write_allowed(request)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _MODEL_EXTENSIONS:
        raise HTTPException(400, f"unsupported model format. Supported: {', '.join(sorted(_MODEL_EXTENSIONS))}")
    _models.mkdir(parents=True, exist_ok=True)
    clean_name = re.sub(r"[^A-Za-z0-9_.-]", "_", file.filename or f"model{suffix}")
    target = _models / clean_name
    size = 0
    try:
        with target.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > _MAX_MODEL_UPLOAD:
                    raise HTTPException(413, "upload exceeds maximum model size")
                output.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return {"path": str(target), "name": clean_name, "format": suffix.lstrip("."), "sizeBytes": size}


def _templates() -> list[dict]:
    templates = [
        {
            "id": "preprocessing",
            "name": "Image Preprocessing",
            "description": "Camera input with grayscale conversion and resizing for preview.",
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
    yolo_tests = [
        ("01-detection", "Deteksi & Overlay", "YOLOv8: bounding box, label, dan preview.", ["overlay_annotate"]),
        ("02-filter-count", "Filter Kelas & Hitung", "YOLOv8: filter person, occupancy counter, teks hitungan.", ["filter", "object_counter", "draw_text"]),
        ("03-tracking-line", "Tracking & Garis IN/OUT", "YOLOv8: tracker, snapshot per track, line counter.", ["tracker", "track_snapshot", "line_counter"]),
        ("04-dwell-privacy", "Durasi & Privasi", "YOLOv8: dwell time, blur privasi, gambar kotak.", ["tracker", "dwell_time", "blur_anonymizer", "draw_boxes"]),
        ("05-segmentation", "Segmentasi YOLOv8", "YOLOv8n-seg: segmentasi objek dan overlay.", ["segmenter", "overlay_annotate"]),
        ("06-crop-classify", "Crop & Klasifikasi", "YOLOv8: crop deteksi lalu klasifikasi YOLOv8n-cls dan simpan ke database.", ["detection_crop", "classifier", "database_output"]),
        ("07-if-else", "Cabang If / Else & Alert", "YOLOv8: dua jalur komplementer berdasarkan jumlah objek.", ["if_else", "alert"]),
        ("08-roi", "Zona ROI", "YOLOv8: filter deteksi berdasarkan area ROI.", ["roi_filter", "draw_boxes"]),
        ("09-conditions", "Kondisi Kelas & Logika", "YOLOv8: class condition, compare, object count, confidence, AND/OR.", ["class_detected_condition", "object_count_condition", "compare_value", "confidence_threshold", "and_or_logic"]),
        ("10-transform", "Transformasi Frame", "YOLOv8 dengan pengujian resize, crop, dan rotasi frame.", ["resize", "crop", "rotate_flip"]),
        ("11-enhance", "Warna & Peningkatan Gambar", "YOLOv8 dengan pengujian konversi warna, brightness/contrast, blur/sharpen.", ["color_convert", "brightness_contrast", "blur_sharpen"]),
        ("12-calibration", "Koreksi Perspektif & Lensa", "YOLOv8 dengan pengujian koreksi perspektif dan undistort.", ["perspective", "undistort"]),
        ("13-motion", "Motion + YOLOv8", "Background subtraction dan deteksi YOLOv8.", ["background_subtract"]),
        ("14-sampling-slicer", "Sampling & Small Object Slicer", "Batasi FPS lalu deteksi objek kecil dengan slicer YOLOv8.", ["frame_sampler", "slicer"]),
        ("15-barcode", "QR / Barcode", "Baca barcode atau QR, lalu preview dan catat alert.", ["barcode_reader", "alert"]),
        ("16-event-controls", "Timer & Kontrol Event", "Uji confidence threshold, timer, debounce, rate limiter, trigger once.", ["confidence_threshold", "timer_delay", "debounce", "rate_limiter", "trigger_once", "alert"]),
        ("17-python-script", "Custom Python Script", "YOLOv8 dengan script default pass-through dan Draw Text.", ["python_script", "draw_text"]),
        ("18-output", "Penyimpanan & Webhook", "YOLOv8: simpan gambar, hasil ke SQLite, dan HTTP webhook.", ["image_output", "database_output", "webhook_output"]),
        ("19-ip-camera", "IP Camera + YOLOv8", "Streaming CCTV lalu deteksi; isi alamat dan kredensial kamera Anda.", ["ip_camera"]),
        ("20-inspection", "Inspeksi Visual + YOLOv8", "Uji node anomali bersama YOLOv8; Visual Inspection memerlukan model EfficientAD.", ["efficientad", "draw_boxes"]),
    ]
    for index, (template_id, name, description, steps) in enumerate(yolo_tests):
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
                "id": f"yolov8-test-{template_id}",
                "name": f"YOLOv8 Test {index + 1:02d} — {name}",
                "description": description,
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
            "id": f"yolov8-test-{template_id}",
            "name": f"YOLOv8 Test {index + 1:02d} — {name}",
            "description": description,
            "workflow": {"nodes": nodes, "edges": [[a, b] for a, b in zip(chain, chain[1:])]},
        })
    return templates


@app.get("/api/templates")
def templates() -> dict:
    return {"templates": _templates()}


def _preflight_models(workflow: dict) -> None:
    from custom_model_runtime import custom_model_path, resolve_model_file
    allowed = {engine["id"]: engine for engine in _MODEL_ENGINES}
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
        if not raw and engine_id in ("rfdetr", "convnext"):
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
        global _runner, _runner_thread_ref
        with _lock:
            alive = bool(_runner_thread_ref and _runner_thread_ref.is_alive())
            if _runner is not None and (_runner.is_running() or alive):
                raise HTTPException(409, "workflow already running")
            _previews.clear(); _logs.clear(); _events.clear()
            _runner = core.WorkflowRunner(on_log=_record, on_event=_event, on_frame=_frame, native_preview=False)
            try:
                _runner.start(workflow)
                _runner_thread_ref = _runner._thread
            except ValueError as exc:
                raise HTTPException(400, str(exc))
        return _runner.status()
    except HTTPException as exc:
        _record(f"ERROR: {exc.detail}")
        _event("Run Error", str(exc.detail))
        raise
    except Exception as exc:
        _record(f"ERROR: {exc}")
        _event("Run Error", str(exc))
        raise


@app.post("/api/stop")
def stop(request: Request) -> dict:
    _write_allowed(request)
    with _lock:
        runner = _runner
    if runner:
        runner.stop()
        return runner.status()
    return {"running": False, "state": "idle", "error": None}


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
        with _lock:
            runner = _runner
        if runner and runner.is_running():
            runner.update_workflow(wf)
            return {"ok": True, "updated": True}
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
        except Exception:
            pass
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
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("VISONODE_WEB_PORT", "8765")))
