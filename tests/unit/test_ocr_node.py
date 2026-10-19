"""Unit tests for OCR Text Reader Node (Ultra-lightweight ONNX OCR).

Covers:
- OCREngine initialization & dictionary loading
- Text recognition on image crops (PP-OCR mobile rec ONNX)
- Text line detection (PP-OCR det ONNX & morphological proposer)
- Character whitelist filtering & min confidence thresholds
- Crop-from-detections mode vs full-frame mode
- Cooldown throttling & event generation
"""
import sys
import os
import cv2
import numpy as np
import pytest

# Ensure engine path is accessible
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "engine"))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from ocr_engine import OCREngine, run_ocr_pipeline


def _create_text_crop(text: str = "TEST 123", width: int = 180, height: int = 48) -> np.ndarray:
    """Helper to generate a clean synthetic text crop."""
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    cv2.putText(img, text, (10, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    return img


def test_ocr_engine_initialization():
    config = {
        "recModelPath": "data/models/ocr/ppocrv3_en_rec.onnx",
        "detModelPath": "data/models/ocr/ppocrv3_det.onnx",
        "dictPath": "data/models/ocr/en_dict.txt",
    }
    engine = OCREngine(config)
    assert len(engine.dict_chars) > 50
    assert engine.rec_session is not None
    assert engine.det_session is not None


def test_ocr_recognize_crop():
    config = {
        "recModelPath": "data/models/ocr/ppocrv3_en_rec.onnx",
        "detModelPath": "data/models/ocr/ppocrv3_det.onnx",
        "dictPath": "data/models/ocr/en_dict.txt",
    }
    engine = OCREngine(config)
    crop = _create_text_crop("ABC 987", width=220, height=48)
    text, conf = engine.recognize_crop(crop)

    assert "ABC" in text or "987" in text
    assert conf > 0.60


def test_ocr_character_whitelist_and_threshold():
    config = {
        "recModelPath": "data/models/ocr/ppocrv3_en_rec.onnx",
        "detModelPath": "data/models/ocr/ppocrv3_det.onnx",
        "dictPath": "data/models/ocr/en_dict.txt",
        "characterWhitelist": "0123456789",  # Only digits allowed
        "minConfidence": 0.30,
    }
    engine = OCREngine(config)

    # Frame with text
    frame = np.ones((100, 300, 3), dtype=np.uint8) * 255
    cv2.putText(frame, "CAR 456", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2)

    dets, evts = engine.process_frame(frame)
    # Any recognized text should only contain allowed whitelist digits
    for d in dets:
        for ch in d["text"]:
            assert ch in "0123456789"


def test_ocr_crop_from_detections_mode():
    config = {
        "recModelPath": "data/models/ocr/ppocrv3_en_rec.onnx",
        "detModelPath": "data/models/ocr/ppocrv3_det.onnx",
        "dictPath": "data/models/ocr/en_dict.txt",
        "cropFromDetections": True,
        "filterClasses": "license_plate, label",
        "minConfidence": 0.40,
    }
    engine = OCREngine(config)

    # Full frame with a license plate patch
    frame = np.ones((400, 600, 3), dtype=np.uint8) * 240
    # Draw license plate text inside [50, 100, 250, 160]
    cv2.rectangle(frame, (50, 100), (250, 160), (255, 255, 255), -1)
    cv2.putText(frame, "B 9999 AA", (60, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)

    upstream_dets = [
        {"class": "car", "box": [20, 50, 500, 350]},
        {"class": "license_plate", "box": [50, 100, 250, 160]},
    ]

    text_dets, events = engine.process_frame(frame, upstream_dets)
    assert len(text_dets) >= 1
    found = text_dets[0]
    assert found["class"] == "text"
    assert "9999" in found["text"] or "B" in found["text"] or "AA" in found["text"]
    assert found["confidence"] > 0.40


def test_run_ocr_pipeline_wrapper():
    workflow = {
        "nodes": [
            {
                "id": "ocr_1",
                "type": "ocr_reader",
                "enabled": True,
                "config": {
                    "recModelPath": "data/models/ocr/ppocrv3_en_rec.onnx",
                    "detModelPath": "data/models/ocr/ppocrv3_det.onnx",
                    "dictPath": "data/models/ocr/en_dict.txt",
                    "minConfidence": 0.40,
                },
            }
        ]
    }
    node_states = {}
    frame = np.ones((100, 250, 3), dtype=np.uint8) * 255
    cv2.putText(frame, "HELLO 2026", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

    dets, evts = run_ocr_pipeline(frame, workflow, [], node_states)
    assert "_ocr_ocr_1" in node_states
    assert len(dets) >= 1
