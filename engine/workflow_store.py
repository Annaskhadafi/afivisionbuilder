from __future__ import annotations

import copy
import json
import os
import platform
import re
import shutil
import uuid
import threading
from functools import wraps
from datetime import datetime, timezone
from pathlib import Path

from node_catalog import (
    INPUT_NODE_ID,
    LEGACY_CAMERA_NODE_ID,
    NODE_BLUEPRINTS,
    PYTHON_SCRIPT_DEFAULTS,
    RFDETR_NATIVE_IMAGE_SIZE,
    SAM3_DEFAULT_THRESHOLD,
    SAM3_IMAGE_SIZE,
    TRACKING_ALGORITHMS,
    TRACKER_CONFIG_DEFAULTS,
    migrate_tracker_config,
    normalize_overlay_config,
    normalize_efficientad_config,
)

ROOT = Path(__file__).resolve().parent
WORKFLOW_FILE = ROOT / "workflow.json"
_project_lock = threading.RLock()


def _project_transaction(function):
    """Keep background template commits and UI index updates indivisible."""
    @wraps(function)
    def locked(*args, **kwargs):
        with _project_lock:
            return function(*args, **kwargs)
    return locked


def get_app_data_dir() -> Path:
    override = os.environ.get("VISONODE_APP_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "VisoNode"
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "VisoNode"
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "visonode"


APP_DATA_DIR = get_app_data_dir()
PROJECTS_DIR = APP_DATA_DIR / "projects"
PROJECT_INDEX_FILE = APP_DATA_DIR / "projects.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _project_workflow_file(project_id: str) -> Path:
    return PROJECTS_DIR / project_id / "workflow.json"


def _read_index() -> dict:
    try:
        if PROJECT_INDEX_FILE.exists():
            data = json.loads(PROJECT_INDEX_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("projects"), list):
                data.setdefault("active_project_id", "")
                return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"active_project_id": "", "projects": []}


def _write_index(index: dict, *, strict: bool = False) -> None:
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        temporary = PROJECT_INDEX_FILE.with_suffix(".tmp")
        temporary.write_text(json.dumps(index, indent=2), encoding="utf-8")
        temporary.replace(PROJECT_INDEX_FILE)
    except OSError:
        if strict:
            raise


def _project_by_id(index: dict, project_id: str) -> dict | None:
    return next((p for p in index.get("projects", []) if p.get("id") == project_id), None)


def _clean_project_name(name: str) -> str:
    name = re.sub(r"\s+", " ", str(name or "").strip())
    return name or "Vision Workflow"


def _default_project_name(existing_count: int) -> str:
    return "Vision Workflow" if existing_count == 0 else f"Vision Workflow {existing_count + 1}"


def make_node(node_type: str, **overrides) -> dict:
    bp = NODE_BLUEPRINTS[node_type]
    config = copy.deepcopy(bp["config"])
    config.update(copy.deepcopy(overrides.get("config", {})))
    return {
        "id": overrides.get("id", node_type),
        "type": node_type,
        "title": bp["title"],
        "subtitle": bp["subtitle"],
        "x": overrides.get("x", bp["x"]),
        "y": overrides.get("y", bp["y"]),
        "enabled": overrides.get("enabled", True),
        "status": "idle",
        "config": config,
    }


def unique_node_id(workflow: dict, node_type: str) -> str:
    """Return a stable, human-readable ID for a new node instance."""
    existing_ids = {str(node.get("id") or "") for node in workflow.get("nodes", [])}
    if node_type not in existing_ids:
        return node_type
    suffix = 2
    while f"{node_type}-{suffix}" in existing_ids:
        suffix += 1
    return f"{node_type}-{suffix}"


def default_workflow() -> dict:
    return {
        "nodes": [
            make_node("input", x=80, y=180),
            make_node("detector", x=390, y=180),
            make_node("preview", x=700, y=180),
        ],
        "edges": [
            [INPUT_NODE_ID, "detector"],
            ["detector", "preview"],
        ],
    }


def detection_demo_workflow(source_type: str) -> dict:
    """Build the three-node RF-DETR Nano detection demo for an input source."""
    if source_type not in ("camera", "video"):
        raise ValueError(f"Unsupported detection demo source type: {source_type}")

    input_config = {"sourceType": source_type}
    if source_type == "video":
        input_config.update({"filePath": "", "loop": True})

    return {
        "nodes": [
            make_node("input", x=80, y=180, config=input_config),
            make_node(
                "detector",
                x=390,
                y=180,
                config={"engine": "rfdetr", "rfdetrModel": "rfdetr-nano"},
            ),
            make_node("preview", x=700, y=180),
        ],
        "edges": [
            [INPUT_NODE_ID, "detector"],
            ["detector", "preview"],
        ],
    }


def webcam_detection_demo_workflow() -> dict:
    return detection_demo_workflow("camera")


def video_detection_demo_workflow() -> dict:
    return detection_demo_workflow("video")


def input_subtitle(node: dict) -> str:
    source_type = node.get("config", {}).get("sourceType") or "camera"
    if source_type == "youtube":
        yt_url = str(node.get("config", {}).get("youtubeUrl") or "").strip()
        return f"YouTube: {yt_url[:28]}..." if len(yt_url) > 28 else (f"YouTube: {yt_url}" if yt_url else "YouTube stream source")
    if source_type == "image":
        return "Image file source"
    if source_type == "video":
        return "Video file source"
    if source_type == "file":
        return "File source"
    if source_type == "daheng":
        return "Daheng Imaging camera"
    return "Camera capture"


def node_by_id(workflow: dict, node_id: str) -> dict | None:
    return next((node for node in workflow.get("nodes", []) if node.get("id") == node_id), None)


def enabled_node(workflow: dict, node_id: str) -> dict | None:
    node = node_by_id(workflow, node_id)
    return node if node and node.get("enabled", True) else None


def normalize_workflow(workflow: dict) -> dict:
    renamed_ids = {}
    for node in workflow.get("nodes", []):
        if node.get("type") == LEGACY_CAMERA_NODE_ID:
            node["type"] = INPUT_NODE_ID
            if node.get("id") == LEGACY_CAMERA_NODE_ID and not node_by_id(workflow, INPUT_NODE_ID):
                node["id"] = INPUT_NODE_ID
                renamed_ids[LEGACY_CAMERA_NODE_ID] = INPUT_NODE_ID
        if node.get("type") == INPUT_NODE_ID:
            config = node.setdefault("config", {})
            config.setdefault("sourceType", "camera")
            if config.get("sourceType") not in ("camera", "daheng", "file", "image", "video", "youtube"):
                config["sourceType"] = "camera"
            if "source" not in config:
                config["source"] = config.get("cameraIndex", config.get("deviceId", 0))
            config.setdefault("frameQueueSize", 64)
            config.setdefault("dropFrames", True)
            config.setdefault("youtubeUrl", "")
            config.setdefault("youtubeQuality", "720p")
        if node.get("type") == "detector":
            config = node.setdefault("config", {})
            valid_detector_engines = (
                "rfdetr", "rfdetr_tensorrt", "rfdetr_onnx",
                "ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"
            )
            if config.get("engine") not in valid_detector_engines:
                config["engine"] = "rfdetr"
            config.setdefault("rfdetrModel", "rfdetr-nano")
            config.setdefault("rfdetrCheckpoint", "")
            config.setdefault("rfdetrImageSize", RFDETR_NATIVE_IMAGE_SIZE)
            config.setdefault("rfdetrHalfPrecision", True)
            config.setdefault("rfdetrTensorRTEngine", "")
            config.setdefault("rfdetrTensorRTClasses", "")
            config.setdefault("rfdetrOnnxModel", "")
            config.setdefault("rfdetrOnnxClasses", "")
            config.setdefault("customModelPath", "")
            config.setdefault("customClasses", "")
            config.setdefault("iouThreshold", 0.45)
            config.setdefault("detectEveryNFrames", 1)
            config.setdefault("maxDetectionFps", 0)
            config.setdefault("batchSize", 32)
        if node.get("type") == "segmenter":
            config = node.setdefault("config", {})
            valid_segmenter_engines = (
                "sam3", "rfdetr", "rfdetr_tensorrt", "rfdetr_onnx",
                "ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"
            )
            if config.get("engine") not in valid_segmenter_engines:
                config["engine"] = "rfdetr"
            if config.get("engine") == "sam3":
                config["imgsz"] = SAM3_IMAGE_SIZE
                if float(config.get("threshold", 0.55)) == 0.55:
                    config["threshold"] = SAM3_DEFAULT_THRESHOLD
            config.setdefault("rfdetrModel", "rfdetr-seg-nano")
            config.setdefault("rfdetrCheckpoint", "")
            config.setdefault("rfdetrImageSize", RFDETR_NATIVE_IMAGE_SIZE)
            config.setdefault("rfdetrTensorRTEngine", "")
            config.setdefault("rfdetrTensorRTClasses", "")
            config.setdefault("rfdetrOnnxModel", "")
            config.setdefault("rfdetrOnnxClasses", "")
            config.setdefault("customModelPath", "")
            config.setdefault("customClasses", "")
            config.setdefault("iouThreshold", 0.45)
            config.setdefault("detectEveryNFrames", 1)
            config.setdefault("maxDetectionFps", 0)
            config.setdefault("batchSize", 32)
        if node.get("type") == "efficientad":
            normalize_efficientad_config(node.setdefault("config", {}))
        if node.get("type") == "classifier":
            config = node.setdefault("config", {})
            valid_classifier_engines = (
                "convnext",
                "ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"
            )
            if config.get("engine") not in valid_classifier_engines:
                config["engine"] = "convnext"
            config.setdefault("threshold", 0.0)
            config.setdefault("convnextModel", "convnext_tiny.fb_in22k_ft_in1k")
            config.setdefault("convnextCheckpoint", "")
            config.setdefault("convnextClasses", "")
            config.setdefault("convnextImageSize", 224)
            config.setdefault("convnextHalfPrecision", True)
            config.setdefault("customModelPath", "")
            config.setdefault("customClasses", "")
            config.setdefault("topK", 1)
            config.setdefault("detectEveryNFrames", 1)
            config.setdefault("maxDetectionFps", 0)
            config.setdefault("batchSize", 32)
        if node.get("type") == "detection_crop":
            config = node.setdefault("config", {})
            config.setdefault("classes", "")
            config.setdefault("paddingPercent", 0.0)
            config.setdefault("square", False)
            config.setdefault("minSize", 1)
            config.setdefault("maxCrops", 32)
        if node.get("type") == "track_snapshot":
            config = node.setdefault("config", {})
            config.setdefault("trackIds", "")
            config.setdefault("classes", "")
            config.setdefault("minimumConfidence", 0.0)
            config.setdefault("minimumTrackAgeFrames", 1)
            config.setdefault("retentionSeconds", 3600)
            config.setdefault("snapshotQuality", "best_frame")
        if node.get("type") == "object_counter":
            config = node.setdefault("config", {})
            config.setdefault("classes", "")
            config.setdefault("countOncePerTrack", True)
            config.setdefault("retentionSeconds", 3600)
            config.setdefault("countMode", "bidirectional")
        if node.get("type") == "tracker":
            config = node.setdefault("config", {})
            migrate_tracker_config(config)
            if config.get("algorithm") not in TRACKING_ALGORITHMS:
                config["algorithm"] = "bytetrack"
            for key, value in TRACKER_CONFIG_DEFAULTS.items():
                if key != "batchSize":
                    config.setdefault(key, value)
            config.setdefault("batchSize", 32)
        if node.get("type") == "preview":
            config = node.setdefault("config", {})
            config.pop("useFilter", None)
            config.pop("displayFps", None)
            config.setdefault("showTrackIds", True)
            config.setdefault("showTrails", True)
            config.setdefault("cropGridMaxItems", 16)
            config.setdefault("cropGridColumns", 0)
            config.setdefault("cropGridGap", 8)
            config.setdefault("holdLastEvent", True)
            config.setdefault("saveVideo", False)
            config.setdefault("outputPath", "")
            config.setdefault("outputFps", 0)
        if node.get("type") == "frame_sampler":
            config = node.setdefault("config", {})
            config.setdefault("targetFps", 10)
        if node.get("type") == "python_script":
            config = node.setdefault("config", {})
            for key, value in PYTHON_SCRIPT_DEFAULTS.items():
                config.setdefault(key, value)
        if node.get("type") == "draw_text":
            config = node.setdefault("config", {})
            config.setdefault("textTemplate", "{classification.class}  {classification.confidence}")
            config.setdefault("x", 24)
            config.setdefault("y", 48)
            config.setdefault("fontScale", 1.0)
            config.setdefault("thickness", 2)
            config.setdefault("color", "#ffffff")
            config.setdefault("background", True)
            config.setdefault("backgroundColor", "#111827")
        if node.get("type") == "draw_boxes":
            config = node.setdefault("config", {})
            config.setdefault("labelTemplate", "{detection.class}  {detection.confidence}")
            config.setdefault("color", "#22c55e")
            config.setdefault("thickness", 2)
            config.setdefault("showLabel", True)
            config.setdefault("fillOpacity", 0.0)
        if node.get("type") == "overlay_annotate":
            normalize_overlay_config(node.setdefault("config", {}))
        if node.get("type") == "database_output":
            config = node.setdefault("config", {})
            config.setdefault("databasePath", "")
            config.setdefault("saveDetections", True)
            config.setdefault("eventObjectsOnly", True)
            config.setdefault("saveFrames", False)
            config.setdefault("saveEvents", True)
            config.setdefault("saveDebug", False)
            config.setdefault("sampleEvery", 1)
            config.setdefault("batchSize", 128)
            config.setdefault("flushIntervalMs", 500)
            config.setdefault("maxQueue", 10000)
        if node.get("type") == "image_output":
            config = node.setdefault("config", {})
            config.setdefault("outputDirectory", "")
            config.setdefault("format", "jpg")
            config.setdefault("jpegQuality", 95)
            config.setdefault("filenameTemplate", "{timestamp}_{track_id}_{class}")
        if node.get("type") == "roi_filter":
            config = node.setdefault("config", {})
            if config.get("shape") not in ("rectangle", "polygon"):
                config["shape"] = "rectangle"
            config.setdefault("x", 0)
            config.setdefault("y", 0)
            config.setdefault("width", 640)
            config.setdefault("height", 480)
            if not isinstance(config.get("points"), list):
                config["points"] = []
        if node.get("type") == "webhook_output":
            config = node.setdefault("config", {})
            config.setdefault("url", "")
            config.setdefault("method", "POST")
            config.setdefault("headers", "")
            config.setdefault("includeImage", True)
            config.setdefault("jpegQuality", 80)
            config.setdefault("batchIntervalMs", 200)

    for edge in workflow.get("edges", []):
        if len(edge) < 2:
            continue
        edge[0] = renamed_ids.get(edge[0], edge[0])
        edge[1] = renamed_ids.get(edge[1], edge[1])
    return workflow


def source_node_id(workflow: dict) -> str:
    input_node = next(
        (node for node in workflow.get("nodes", []) if node.get("type") == INPUT_NODE_ID),
        None,
    )
    if input_node:
        return input_node["id"]
    return LEGACY_CAMERA_NODE_ID


def has_active_path(workflow: dict, from_id: str, to_id: str) -> bool:
    if not enabled_node(workflow, from_id) or not enabled_node(workflow, to_id):
        return False
    if from_id == to_id:
        return True

    visited = set()
    queue = [from_id]
    edges = workflow.get("edges", [])
    while queue:
        current_id = queue.pop(0)
        if current_id == to_id:
            return True
        if current_id in visited:
            continue
        visited.add(current_id)
        for edge_from_id, edge_to_id in edges:
            if (
                edge_from_id == current_id
                and edge_to_id not in visited
                and enabled_node(workflow, edge_to_id)
            ):
                queue.append(edge_to_id)
    return False


def normalize_gui(workflow: dict) -> dict:
    """Apply blueprint defaults / titles so older saved files stay valid."""
    normalize_workflow(workflow)
    workflow["nodes"] = [
        node for node in workflow.get("nodes", []) if node.get("type") in NODE_BLUEPRINTS
    ]
    seen_ids: set[str] = set()
    for node in workflow["nodes"]:
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id or node_id in seen_ids:
            node["id"] = unique_node_id(
                {"nodes": [{"id": item_id} for item_id in seen_ids]},
                node["type"],
            )
        seen_ids.add(node["id"])
    valid_ids = seen_ids
    workflow["edges"] = [
        edge
        for edge in workflow.get("edges", [])
        if len(edge) >= 2 and edge[0] in valid_ids and edge[1] in valid_ids
    ]
    for node in workflow.get("nodes", []):
        bp = NODE_BLUEPRINTS.get(node["type"])
        if not bp:
            continue
        node["title"] = node.get("customTitle") or bp["title"]
        config = copy.deepcopy(bp["config"])
        config.update(copy.deepcopy(node.get("config") or {}))
        node["config"] = config
        node["subtitle"] = input_subtitle(node) if node["type"] == "input" else bp["subtitle"]
        node.setdefault("enabled", True)
        node.setdefault("status", "idle")
    return workflow


def load_workflow() -> dict:
    project_id = get_active_project_id()
    if project_id:
        return load_project_workflow(project_id)
    try:
        if WORKFLOW_FILE.exists():
            data = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
            if isinstance(data.get("nodes"), list) and isinstance(data.get("edges"), list):
                return normalize_gui(data)
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    return normalize_gui(default_workflow())


@_project_transaction
def save_workflow(workflow: dict) -> None:
    project_id = get_active_project_id()
    if project_id:
        save_project_workflow(project_id, workflow)
        return
    try:
        WORKFLOW_FILE.write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    except OSError:
        pass


@_project_transaction
def ensure_projects() -> list[dict]:
    """Return known projects, migrating the legacy workflow file if needed."""
    is_clean_install = not PROJECT_INDEX_FILE.exists() and not WORKFLOW_FILE.exists()
    index = _read_index()
    projects = [p for p in index.get("projects", []) if isinstance(p, dict) and p.get("id")]
    index["projects"] = projects
    if projects:
        _write_index(index)
        return list_projects()

    if is_clean_install:
        create_project(
            "Video Object Detection Demo",
            video_detection_demo_workflow(),
            set_active_project=False,
        )
        create_project(
            "Webcam Object Detection Demo",
            webcam_detection_demo_workflow(),
            set_active_project=True,
        )
        return list_projects()

    if not WORKFLOW_FILE.exists():
        _write_index(index)
        return []

    try:
        data = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
        if not isinstance(data.get("nodes"), list) or not isinstance(data.get("edges"), list):
            return []
    except (OSError, json.JSONDecodeError):
        return []

    project = create_project("Vision Workflow", normalize_gui(data), set_active_project=True)
    return [project]


@_project_transaction
def list_projects() -> list[dict]:
    projects = ensure_projects() if not PROJECT_INDEX_FILE.exists() and WORKFLOW_FILE.exists() else _read_index().get("projects", [])
    normalized = [dict(project) for project in projects if isinstance(project, dict) and project.get("id")]
    normalized.sort(key=lambda item: str(item.get("modified_at") or item.get("created_at") or ""), reverse=True)
    return normalized


@_project_transaction
def get_project(project_id: str) -> dict | None:
    project = _project_by_id(_read_index(), project_id)
    return dict(project) if project else None


@_project_transaction
def get_active_project_id() -> str:
    index = _read_index()
    project_id = str(index.get("active_project_id") or "")
    return project_id if _project_by_id(index, project_id) else ""


@_project_transaction
def set_active_project(project_id: str | None) -> None:
    index = _read_index()
    index["active_project_id"] = str(project_id or "") if _project_by_id(index, str(project_id or "")) else ""
    _write_index(index)


@_project_transaction
def create_project(
    name: str = "",
    workflow: dict | None = None,
    *,
    set_active_project: bool = True,
) -> dict:
    index = _read_index()
    project_id = uuid.uuid4().hex
    now = _now_iso()
    project = {
        "id": project_id,
        "name": _clean_project_name(name or _default_project_name(len(index.get("projects", [])))),
        "created_at": now,
        "modified_at": now,
    }
    index.setdefault("projects", []).insert(0, project)
    if set_active_project:
        index["active_project_id"] = project_id
    _write_index(index)
    save_project_workflow(project_id, workflow or default_workflow(), touch_index=False)
    return dict(project)


@_project_transaction
def import_project_workflow(name: str, workflow: dict) -> dict:
    """Persist a new inactive project, surfacing failures without indexing partial imports."""
    index = _read_index()
    project_id = uuid.uuid4().hex
    now = _now_iso()
    project = {
        "id": project_id, "name": _clean_project_name(name),
        "created_at": now, "modified_at": now,
    }
    path = _project_workflow_file(project_id)
    # The exclusive directory creation prevents overwriting even on an ID collision.
    path.parent.mkdir(parents=True, exist_ok=False)
    try:
        path.write_text(json.dumps(workflow, indent=2, allow_nan=False), encoding="utf-8")
        index.setdefault("projects", []).insert(0, project)
        _write_index(index, strict=True)
    except Exception:
        path.unlink(missing_ok=True)
        path.parent.rmdir()
        raise
    return dict(project)


@_project_transaction
def rename_project(project_id: str, name: str) -> dict | None:
    index = _read_index()
    project = _project_by_id(index, project_id)
    if not project:
        return None
    project["name"] = _clean_project_name(name)
    project["modified_at"] = _now_iso()
    _write_index(index)
    return dict(project)


@_project_transaction
def delete_project(project_id: str) -> bool:
    """Delete a project from the index and remove its saved workflow files."""
    project_id = str(project_id or "")
    index = _read_index()
    if not _project_by_id(index, project_id):
        return False

    try:
        projects_root = PROJECTS_DIR.resolve()
        project_dir = PROJECTS_DIR / project_id
        project_parent = project_dir.parent.resolve()
    except OSError:
        return False

    # Project IDs come from the index, so guard against a malformed index ever
    # turning this operation into a deletion outside the projects directory.
    if project_parent != projects_root:
        return False

    try:
        if project_dir.is_symlink():
            project_dir.unlink()
        elif project_dir.exists():
            if not project_dir.is_dir():
                return False
            shutil.rmtree(project_dir)
    except OSError:
        return False

    index["projects"] = [
        project
        for project in index.get("projects", [])
        if project.get("id") != project_id
    ]
    if index.get("active_project_id") == project_id:
        index["active_project_id"] = ""
    _write_index(index)
    return _project_by_id(_read_index(), project_id) is None


@_project_transaction
def load_project_workflow(project_id: str) -> dict:
    try:
        path = _project_workflow_file(project_id)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data.get("nodes"), list) and isinstance(data.get("edges"), list):
                return normalize_gui(data)
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    return normalize_gui(default_workflow())


@_project_transaction
def save_project_workflow(project_id: str, workflow: dict, *, touch_index: bool = True) -> None:
    try:
        path = _project_workflow_file(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    except OSError:
        return

    if not touch_index:
        return
    index = _read_index()
    project = _project_by_id(index, project_id)
    if project:
        project["modified_at"] = _now_iso()
        _write_index(index)
