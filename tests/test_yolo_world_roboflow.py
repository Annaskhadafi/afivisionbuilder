import os
import sys
import numpy as np
import pytest

from engine.custom_model_runtime import (
    CustomModelRunner,
    detect_model_engine,
    run_custom_model_frame,
    _run_roboflow_universe,
)
from server import _MODEL_ENGINES, _preflight_models, _model_availability


def test_detect_model_engine_yolo_world():
    assert detect_model_engine("yolov8s-worldv2.pt") == "yolo_world"
    assert detect_model_engine("models/yolov8m-world.pt") == "yolo_world"
    assert detect_model_engine("best.pt") == "ultralytics_yolo"


def test_server_model_engines_registered():
    engine_ids = [e["id"] for e in _MODEL_ENGINES]
    assert "yolo_world" in engine_ids
    assert "roboflow_universe" in engine_ids
    assert _model_availability("yolo_world") is True
    assert _model_availability("roboflow_universe") is True


def test_roboflow_universe_mock_execution():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    config = {
        "engine": "roboflow_universe",
        "modelPath": "warehouse-forklifts/1",
        "apiKey": "mock_api_key",
        "classes": "forklift",
        "threshold": 0.5,
    }
    node = {"id": "det_rf", "type": "detector", "config": config}
    dets = run_custom_model_frame(frame, node)
    assert len(dets) == 1
    assert dets[0]["class"] == "forklift"
    assert dets[0]["score"] == 0.88
    assert len(dets[0]["bbox"]) == 4
    assert dets[0]["sourceNodeId"] == "det_rf"


def test_preflight_yolo_world_and_roboflow():
    # Validates that yolo_world and roboflow_universe pass preflight validation without error
    workflow = {
        "nodes": [
            {
                "id": "det1",
                "type": "detector",
                "enabled": True,
                "config": {
                    "engine": "yolo_world",
                    "customClasses": "person, forklift, safety helmet",
                    "threshold": 0.4,
                },
            },
            {
                "id": "det2",
                "type": "detector",
                "enabled": True,
                "config": {
                    "engine": "roboflow_universe",
                    "modelPath": "solar-panel-defect/2",
                    "roboflowApiKey": "rf_mock_123",
                    "threshold": 0.5,
                },
            },
        ]
    }
    # Should complete without throwing HTTPException
    _preflight_models(workflow)
    assert workflow["nodes"][0]["config"]["customModelPath"] == "yolov8s-worldv2.pt"


def test_inspect_model_roboflow_and_yolo_world():
    from server import inspect_model
    rf_info = inspect_model("warehouse-safety/3")
    assert rf_info["engine"] == "roboflow_universe"
    assert rf_info["format"] == "cloud"
    assert rf_info["name"] == "warehouse-safety/3"

    yw_info = inspect_model("yolo_world")
    assert yw_info["engine"] == "yolo_world"

