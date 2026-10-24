import numpy as np
import pytest
from engine.custom_model_runtime import CustomModelRunner, configure_nms_free, resolve_model_file
from ultralytics import YOLO


def test_yolo26n_auto_enables_end2end_nms_free():
    model_path = resolve_model_file("yolo26n.pt")
    if not model_path.is_file():
        pytest.skip("yolo26n.pt not found in local models")

    raw_model = YOLO(str(model_path))
    # Test auto detection
    is_nms_free = configure_nms_free(raw_model, nms_free=None, model_path=str(model_path))
    assert is_nms_free is True
    head = raw_model.model.model[-1]
    assert getattr(head, "end2end", False) is True


def test_yolo26n_respects_nms_free_config_flag():
    model_path = resolve_model_file("yolo26n.pt")
    if not model_path.is_file():
        pytest.skip("yolo26n.pt not found in local models")

    raw_model = YOLO(str(model_path))
    
    # Explicitly disable
    is_nms_free = configure_nms_free(raw_model, nms_free=False, model_path=str(model_path))
    assert is_nms_free is False
    head = raw_model.model.model[-1]
    assert getattr(head, "end2end", False) is False

    # Explicitly enable
    is_nms_free = configure_nms_free(raw_model, nms_free=True, model_path=str(model_path))
    assert is_nms_free is True
    assert getattr(head, "end2end", False) is True


def test_yolo26n_run_frame_inference_format():
    model_path = resolve_model_file("yolo26n.pt")
    if not model_path.is_file():
        pytest.skip("yolo26n.pt not found in local models")

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    node = {
        "id": "det_yolo26",
        "type": "detector",
        "config": {
            "engine": "ultralytics_yolo",
            "modelPath": "yolo26n.pt",
            "threshold": 0.45,
            "nmsFree": True,
        },
    }
    results = CustomModelRunner.run_frame(frame, node)
    assert isinstance(results, list)
    # Even if 0 detections on blank frame, format contract is verified
    for det in results:
        assert "class" in det
        assert "score" in det
        assert "bbox" in det
        assert len(det["bbox"]) == 4
        assert det["sourceNodeId"] == "det_yolo26"
        assert det["kind"] == "detection"
