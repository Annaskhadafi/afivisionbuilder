import numpy as np
import pytest
from engine import node_catalog, workflow_store
from engine.custom_model_runtime import CustomModelRunner, custom_model_path, COCO_CLASSES


def test_detector_blueprint_defaults_to_yolov8n():
    bp = node_catalog.NODE_BLUEPRINTS["detector"]
    assert bp["title"] == "Object Detection"
    assert "YOLOv8n" in bp["subtitle"]
    cfg = bp["config"]
    assert cfg["engine"] == "ultralytics_yolo"
    assert cfg["modelPath"] == "yolov8n.pt"
    assert cfg["customModelPath"] == "yolov8n.pt"
    assert cfg["threshold"] == 0.45


def test_default_workflow_uses_yolov8n():
    wf = workflow_store.default_workflow()
    det = next(n for n in wf["nodes"] if n["type"] == "detector")
    assert det["config"]["engine"] == "ultralytics_yolo"
    assert det["config"]["modelPath"] == "yolov8n.pt"
    assert det["config"]["customModelPath"] == "yolov8n.pt"


def test_normalize_gui_defaults_missing_engine_to_yolov8n():
    raw_wf = {
        "nodes": [
            {"id": "in", "type": "input", "config": {}},
            {"id": "det", "type": "detector", "config": {}},
            {"id": "prev", "type": "preview", "config": {}},
        ],
        "edges": [["in", "det"], ["det", "prev"]],
    }
    normalized = workflow_store.normalize_gui(raw_wf)
    det = next(n for n in normalized["nodes"] if n["id"] == "det")
    assert det["config"]["engine"] == "ultralytics_yolo"
    assert det["config"]["modelPath"] == "yolov8n.pt"
    assert det["config"]["customModelPath"] == "yolov8n.pt"
    assert det["config"]["threshold"] == 0.45


def test_custom_model_path_fallback():
    assert custom_model_path({"engine": "ultralytics_yolo"}) == "yolov8n.pt"
    assert custom_model_path({"engine": "ultralytics_yolo", "modelPath": ""}) == "yolov8n.pt"
    assert custom_model_path({"engine": "ultralytics_yolo", "modelPath": "custom_yolo.pt"}) == "custom_yolo.pt"


def test_available_output_labels_suggests_coco_classes():
    wf = {
        "nodes": [
            {"id": "in", "type": "input", "enabled": True},
            {"id": "det", "type": "detector", "enabled": True, "config": {"engine": "ultralytics_yolo", "modelPath": "yolov8n.pt"}},
            {"id": "filter", "type": "filter", "enabled": True},
        ],
        "edges": [["in", "det"], ["det", "filter"]],
    }
    labels = node_catalog.available_output_labels(wf, "filter")
    label_names = {item[0] for item in labels}
    assert "person" in label_names
    assert "car" in label_names
    assert "motorcycle" in label_names
    assert len(label_names) >= 80


def test_yolov8n_runtime_inference():
    frame = np.zeros((320, 320, 3), dtype=np.uint8)
    node = {
        "id": "det",
        "type": "detector",
        "config": {
            "engine": "ultralytics_yolo",
            "modelPath": "yolov8n.pt",
            "threshold": 0.45,
        },
    }
    results = CustomModelRunner.run_frame(frame, node)
    assert isinstance(results, list)
