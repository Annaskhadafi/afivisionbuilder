import json
import os
import sys
from pathlib import Path

# Add webapp directory to path
webapp_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(webapp_dir))

from engine.custom_model_runtime import (
    detect_model_engine,
    extract_model_labels,
    CustomModelRunner,
    COCO_CLASSES,
)
from fastapi.testclient import TestClient
from server import app


def test_engine_detection():
    assert detect_model_engine("weights/best.pt") == "ultralytics_yolo"
    assert detect_model_engine("yolov8n.pth") == "ultralytics_yolo"
    assert detect_model_engine("models/detector.onnx") == "onnx_custom"
    assert detect_model_engine("models/classifier.tflite") == "tflite"
    assert detect_model_engine("model.keras") == "tensorflow_keras"
    assert detect_model_engine("weights.h5") == "tensorflow_keras"
    print("PASS: test_engine_detection")


def test_label_extraction_sibling(tmp_path_factory=None):
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        labels_file = tmp / "labels.txt"
        labels_file.write_text("cat\ndog\nbird\n", encoding="utf-8")
        
        model_file = tmp / "test_model.onnx"
        model_file.write_bytes(b"dummy_model_bytes")
        
        extracted = extract_model_labels(str(model_file))
        assert extracted == ["cat", "dog", "bird"], f"Expected ['cat', 'dog', 'bird'], got {extracted}"
    print("PASS: test_label_extraction_sibling")


def test_server_inspect_api():
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        # Test upload mock model
        dummy_content = b"fake pt weights for testing"
        files = {"file": ("my_detector.pt", dummy_content, "application/octet-stream")}
        res = client.post("/api/models/upload", files=files)
        assert res.status_code == 200, res.text
        data = res.json()
        assert "my_detector.pt" in data["name"]
        assert "my_detector.pt" in data["path"]
        
        # Test inspect API
        inspect_res = client.get("/api/models/inspect", params={"path": data["path"]})
        assert inspect_res.status_code == 200, inspect_res.text
        inspect_data = inspect_res.json()
        assert inspect_data["engine"] == "ultralytics_yolo"
        assert "classes" in inspect_data
        assert isinstance(inspect_data["classes"], list)
        assert inspect_data["sizeBytes"] == len(dummy_content)
        
        # Test templates API
        templates_res = client.get("/api/templates")
        assert templates_res.status_code == 200
        templates_data = templates_res.json()
        assert "templates" in templates_data
        assert len(templates_data["templates"]) >= 5
        
        # Clean up uploaded test model
        try:
            p = Path(data["path"])
            if p.exists():
                p.unlink()
        except Exception:
            pass
        
    print("PASS: test_server_inspect_api")


def test_custom_runner_formatting():
    import numpy as np
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    config = {
        "engine": "ultralytics_yolo",
        "customModelPath": "models/fake.pt",
        "customClasses": "widget, bolt, nut",
        "threshold": 0.5
    }
    from engine.custom_model_runtime import _resolve_labels
    labels = _resolve_labels(config, "models/fake.pt")
    assert labels == ["widget", "bolt", "nut"], f"Expected ['widget', 'bolt', 'nut'], got {labels}"
    print("PASS: test_custom_runner_formatting")


def test_phase1_enhancements():
    from engine import node_catalog
    assert "webhook_output" in node_catalog.NODE_BLUEPRINTS
    assert "iouThreshold" in node_catalog.NODE_BLUEPRINTS["detector"]["config"]
    assert "direction" in node_catalog.NODE_BLUEPRINTS["object_counter"]["config"]
    assert "captureMode" in node_catalog.NODE_BLUEPRINTS["track_snapshot"]["config"]

    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        rec_res = client.get("/api/database/records")
        assert rec_res.status_code == 200
        rec_data = rec_res.json()
        assert "records" in rec_data

    print("PASS: test_phase1_enhancements")


if __name__ == "__main__":
    test_engine_detection()
    test_label_extraction_sibling()
    test_server_inspect_api()
    test_custom_runner_formatting()
    test_phase1_enhancements()
    print("All custom model tests PASSED successfully!")
