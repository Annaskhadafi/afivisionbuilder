# tests/unit/test_face_integration_with_all_nodes.py
import time
import numpy as np
import pytest
from engine.object_timer import process_object_timer
from engine.multi_zone_occupancy import process_multi_zone_occupancy
from engine.project_nodes import process_project_node

def test_face_detector_with_object_timer():
    """Verify Object Timer accurately tracks faces directly from Face Detector."""
    face_det = {
        "class": "face",
        "baseClass": "face",
        "x": 100.0,
        "y": 100.0,
        "width": 80.0,
        "height": 80.0,
        "bbox": [100.0, 100.0, 80.0, 80.0],
        "confidence": 0.95,
        "score": 0.95,
        "kind": "detection",
        "landmarks": [[120, 120], [160, 120], [140, 140], [125, 160], [155, 160]]
    }

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    timer_node = {
        "id": "timer_node_1",
        "type": "object_timer",
        "config": {
            "targetClasses": "person, face",
            "alertThresholdSeconds": 3.0,
            "timerFormat": "mm:ss",
            "showOverlay": True
        }
    }

    timer_state = {}
    t0 = 1000.0

    # Frame 1 at t0
    events_1 = process_object_timer(timer_node, dummy_frame, [face_det], timer_state, now=t0)
    assert len(events_1) == 0  # Below 3s threshold
    assert face_det.get("timerSeconds") == 0.0
    assert face_det.get("formattedTimer") == "00:00"
    assert face_det.get("showTimerOverlay") is True

    # Frame 2 at t0 + 4s (threshold exceeded)
    t1 = t0 + 4.0
    events_2 = process_object_timer(timer_node, dummy_frame, [face_det], timer_state, now=t1)
    assert len(events_2) == 1
    alert = events_2[0]
    assert alert["kind"] == "object_timer_alert"
    assert alert["durationSeconds"] >= 4.0
    assert face_det.get("isTimerAlert") is True

def test_face_tracker_identified_person_with_object_timer():
    """Verify Object Timer tracks identified enrolled persons from Face Re-ID Tracker."""
    tracked_person_face = {
        "class": "Annas Khadafi",
        "baseClass": "face",
        "personName": "Annas Khadafi",
        "isEnrolled": True,
        "trackId": 7,
        "x": 200.0,
        "y": 150.0,
        "width": 90.0,
        "height": 90.0,
        "bbox": [200.0, 150.0, 90.0, 90.0],
        "confidence": 0.98,
        "score": 0.98,
        "kind": "detection"
    }

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    timer_node = {
        "id": "timer_node_2",
        "type": "object_timer",
        "config": {
            "targetClasses": "person",  # Should cross-match person with personName/face
            "alertThresholdSeconds": 5.0
        }
    }

    timer_state = {}
    now = time.time()
    events = process_object_timer(timer_node, dummy_frame, [tracked_person_face], timer_state, now=now)
    assert tracked_person_face.get("formattedTimer") == "00:00"
    assert tracked_person_face.get("trackId") == 7

def test_face_detector_with_multi_zone_occupancy():
    """Verify Multi-Zone Occupancy detects faces inside zones."""
    face_det = {
        "class": "face",
        "x": 120.0,
        "y": 120.0,
        "width": 50.0,
        "height": 50.0,
        "bbox": [120.0, 120.0, 50.0, 50.0],
        "kind": "detection"
    }

    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    zone_node = {
        "id": "zone_node_1",
        "type": "multi_zone_occupancy",
        "config": {
            "targetClasses": "person",
            "confirmationSeconds": 0.0,
            "zones": [
                {
                    "id": "zone_1",
                    "name": "Meja 1",
                    "capacity": 2,
                    "points": [[100, 100], [250, 100], [250, 250], [100, 250]]
                }
            ]
        }
    }

    runtime_state = {}
    now = time.time()
    events = process_multi_zone_occupancy(zone_node, dummy_frame, [face_det], runtime_state, now=now)
    # Zone must be recognized as occupied by face
    assert len(events) >= 1
    assert events[0]["zoneId"] == "zone_1"
    assert events[0]["currentCount"] == 1
    assert events[0]["status"] in ("OCCUPIED", "CONFIRMING")

def test_face_detector_with_zone_activity_timer():
    """Verify Workshop Zone Activity Timer triggers when face is present in bay."""
    face_det = {
        "class": "face",
        "x": 150.0,
        "y": 150.0,
        "width": 60.0,
        "height": 60.0,
        "bbox": [150.0, 150.0, 60.0, 60.0],
        "kind": "detection"
    }
    tire_det = {
        "class": "tire",
        "x": 160.0,
        "y": 160.0,
        "width": 80.0,
        "height": 80.0,
        "bbox": [160.0, 160.0, 80.0, 80.0],
        "kind": "detection"
    }

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    node = {
        "id": "ws_bay_1",
        "type": "zone_activity_timer",
        "config": {
            "requiredClasses": "tire",
            "triggerClasses": "person",  # Should trigger with face
            "polygon": [[100, 100], [300, 100], [300, 300], [100, 300]],
            "mode": "fixed_polygon"
        }
    }

    runtime = {"ws_bay_1": {}}
    t0 = 100.0
    process_project_node(node, dummy_frame, [tire_det, face_det], runtime, now=t0)
    # Active session should be started
    node_state = runtime["ws_bay_1"]
    assert node_state.get("sessionId") is not None
    assert node_state.get("completed") is False
