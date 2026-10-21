import numpy as np
import pytest

from engine.uniface_runtime import (
    UniFaceManager,
    get_uniface_manager,
    process_face_detector_node,
    process_face_crop_node,
    draw_face_landmarks_overlay,
)


def test_uniface_manager_initialization():
    mgr = get_uniface_manager()
    assert mgr is not None
    # Check that spoofer and quality estimator can be accessed
    spoofer = mgr.get_spoofer()
    assert spoofer is not None
    estimator = mgr.get_quality_estimator()
    assert estimator is not None


def test_anti_spoof_prediction():
    mgr = get_uniface_manager()
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    bbox = [100, 100, 250, 250]
    is_real, conf = mgr.predict_anti_spoof(dummy_img, bbox)
    assert isinstance(is_real, bool)
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0


def test_face_quality_prediction():
    mgr = get_uniface_manager()
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    landmarks = np.array([
        [130.0, 140.0],
        [170.0, 140.0],
        [150.0, 170.0],
        [135.0, 200.0],
        [165.0, 200.0],
    ], dtype=np.float32)
    score = mgr.predict_face_quality(dummy_img, landmarks)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_face_alignment():
    mgr = get_uniface_manager()
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    landmarks = np.array([
        [130.0, 140.0],
        [170.0, 140.0],
        [150.0, 170.0],
        [135.0, 200.0],
        [165.0, 200.0],
    ], dtype=np.float32)
    aligned = mgr.align_face(dummy_img, landmarks, size=112)
    assert aligned is not None
    assert aligned.shape == (112, 112, 3)


def test_process_face_detector_spoof_filtering(monkeypatch):
    mgr = get_uniface_manager()

    # Mock detect_faces to return 2 dummy faces
    mock_faces = [
        {"x": 100, "y": 100, "width": 80, "height": 80, "landmarks": [[120, 120], [150, 120], [135, 140], [125, 160], [145, 160]]},
        {"x": 300, "y": 100, "width": 80, "height": 80, "landmarks": [[320, 120], [350, 120], [335, 140], [325, 160], [345, 160]]},
    ]
    monkeypatch.setattr(mgr, "detect_faces", lambda frame, conf_thresh=0.45: list(mock_faces))

    # Face 1 is real (is_real=True, conf=0.98), Face 2 is spoof (is_real=False, conf=0.95)
    def mock_predict_anti_spoof(img, bbox):
        if bbox[0] < 200:
            return True, 0.98
        else:
            return False, 0.95

    monkeypatch.setattr(mgr, "predict_anti_spoof", mock_predict_anti_spoof)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Test Case A: filterSpoof = True (default) -> Face 2 is dropped
    node_filter_on = {
        "id": "face_det_1",
        "type": "face_detector",
        "config": {
            "enableAntiSpoofing": True,
            "antiSpoofThreshold": 0.60,
            "filterSpoof": True,
        },
    }
    filtered, events = process_face_detector_node(node_filter_on, frame)
    assert len(filtered) == 1
    assert filtered[0]["x"] == 100
    assert filtered[0]["isReal"] is True
    assert len(events) == 1
    assert events[0]["kind"] == "face_spoof_detected"
    assert events[0]["confidence"] == 0.95

    # Test Case B: filterSpoof = False -> Both faces kept, Face 2 marked as spoof
    node_filter_off = {
        "id": "face_det_2",
        "type": "face_detector",
        "config": {
            "enableAntiSpoofing": True,
            "antiSpoofThreshold": 0.60,
            "filterSpoof": False,
        },
    }
    filtered_all, events_all = process_face_detector_node(node_filter_off, frame)
    assert len(filtered_all) == 2
    assert filtered_all[0]["isReal"] is True
    assert filtered_all[1]["isReal"] is False
    assert filtered_all[1]["antiSpoofStatus"] == "spoof"


def test_process_face_crop_node(monkeypatch):
    mgr = get_uniface_manager()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Mock predict_face_quality
    monkeypatch.setattr(mgr, "predict_face_quality", lambda img, lm: 0.78)

    detections = [
        {
            "class": "face",
            "x": 100,
            "y": 100,
            "width": 80,
            "height": 80,
            "bbox": [100, 100, 80, 80],
            "landmarks": [[120, 120], [150, 120], [135, 140], [125, 160], [145, 160]],
        }
    ]

    crop_node = {
        "id": "face_crop_1",
        "type": "face_crop",
        "config": {
            "alignFaces": True,
            "paddingPercent": 0.15,
            "assessQuality": True,
            "minQualityScore": 0.40,
            "filterLowQuality": False,
            "maxCrops": 8,
            "showQualityChip": True,
        },
    }

    crops, events = process_face_crop_node(crop_node, frame, detections)
    assert len(crops) == 1
    assert crops[0]["qualityScore"] == 0.78
    assert crops[0]["frame"].shape == (112, 112, 3)
    assert detections[0]["faceQualityScore"] == 0.78

    # Test filterLowQuality
    crop_node_strict = {
        "id": "face_crop_strict",
        "type": "face_crop",
        "config": {
            "alignFaces": True,
            "assessQuality": True,
            "minQualityScore": 0.85,  # higher than 0.78
            "filterLowQuality": True,
        },
    }
    strict_crops, _ = process_face_crop_node(crop_node_strict, frame, detections)
    assert len(strict_crops) == 0


def test_draw_face_landmarks_overlay():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = [
        {
            "class": "face",
            "x": 100,
            "y": 100,
            "width": 80,
            "height": 80,
            "bbox": [100, 100, 80, 80],
            "landmarks": [[120, 120], [150, 120], [135, 140], [125, 160], [145, 160]],
            "faceQualityScore": 0.75,
            "personName": "Alex",
            "isEnrolled": True,
            "similarity": 0.92,
        },
        {
            "class": "face",
            "x": 300,
            "y": 100,
            "width": 80,
            "height": 80,
            "bbox": [300, 100, 80, 80],
            "isReal": False,
            "antiSpoofStatus": "spoof",
            "antiSpoofConfidence": 0.96,
        },
    ]

    # Must draw without throwing any exception
    draw_face_landmarks_overlay(frame, detections)
    # Check that frame has been modified
    assert np.any(frame > 0)
