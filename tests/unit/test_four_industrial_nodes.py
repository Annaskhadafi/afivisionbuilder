"""Unit tests for the 4 new industrial nodes:
1. incident_video_recorder
2. mqtt_publisher
3. crowd_density_heatmap
4. ppe_compliance_matrix
"""

import os
import shutil
import time
import numpy as np
import pytest

from engine.incident_recorder import IncidentVideoRecorder, process_incident_video_recorder
from engine.mqtt_gateway import MqttPublisherClient, process_mqtt_publisher
from engine.crowd_heatmap import CrowdDensityHeatmap, process_crowd_density_heatmap
from engine.ppe_compliance import (
    PPEComplianceMatrix,
    draw_ppe_compliance_badges,
    process_ppe_compliance_matrix,
    _bbox_intersection_ratio,
    _get_anatomical_subzone
)


# ============================================================================
# 1. Tests for incident_video_recorder
# ============================================================================

def test_incident_video_recorder_rolling_buffer_and_trigger():
    test_dir = "data/test_recordings"
    os.makedirs(test_dir, exist_ok=True)
    try:
        config = {
            "outputDirectory": test_dir,
            "preBufferSeconds": 0.5,
            "postBufferSeconds": 0.5,
            "fps": 10.0,
            "cooldownSeconds": 1.0,
            "triggerMode": "on_detection",
            "targetClass": "person",
        }
        node = {"id": "test_recorder_1", "config": config}
        recorder = IncidentVideoRecorder.get_instance("test_recorder_1", config)

        # Feed 10 neutral frames (no trigger)
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        state = {}
        now = 1000.0

        for i in range(10):
            status, events = process_incident_video_recorder(
                node, frame, [], state, now + i * 0.1
            )
            assert status["is_recording"] is False

        # Feed frame with trigger (person detected)
        person_det = [{"class": "person", "confidence": 0.9, "bbox": [50, 50, 60, 120]}]
        status, events = process_incident_video_recorder(
            node, frame, person_det, state, now + 1.0
        )
        assert status["is_recording"] is True

        # Continue feeding frames until post-buffer completes
        completed_event = None
        for i in range(12):
            status, events = process_incident_video_recorder(
                node, frame, [], state, now + 1.1 + i * 0.1
            )
            if events:
                completed_event = events[0]
                break

        assert completed_event is not None
        assert completed_event["event_type"] == "incident_clip_recorded"
        assert "video_path" in completed_event
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)


# ============================================================================
# 2. Tests for mqtt_publisher
# ============================================================================

def test_mqtt_publisher_payload_and_template(monkeypatch):
    monkeypatch.setattr(MqttPublisherClient, "publish", lambda *args, **kwargs: True)
    node = {
        "id": "mqtt_pub_1",
        "config": {
            "brokerHost": "127.0.0.1",
            "brokerPort": 1883,
            "topic": "factory/alerts",
            "publishMode": "always",
            "payloadFormat": "custom",
            "customTemplate": "ALERT:{class}:COUNT={count}",
            "minPublishIntervalSeconds": 0.0,
        }
    }
    state = {}
    candidates = [
        {"class": "forklift", "confidence": 0.95, "track_id": 1, "bbox": [10, 10, 80, 80]},
        {"class": "forklift", "confidence": 0.88, "track_id": 2, "bbox": [100, 10, 80, 80]}
    ]
    status, events = process_mqtt_publisher(node, candidates, state, now=2000.0)
    assert status["topic"] == "factory/alerts"
    assert status["total_published"] >= 1
    assert len(events) == 1
    assert events[0]["topic"] == "factory/alerts"
    assert events[0]["count"] == 2


def test_mqtt_publisher_json_mode(monkeypatch):
    monkeypatch.setattr(MqttPublisherClient, "publish", lambda *args, **kwargs: True)
    node = {
        "id": "mqtt_pub_2",
        "config": {
            "topic": "factory/json",
            "publishMode": "on_detection",
            "payloadFormat": "json",
            "minPublishIntervalSeconds": 0.0,
        }
    }
    state = {}
    candidates = [{"class": "worker", "confidence": 0.99, "bbox": [0, 0, 50, 100]}]
    status, events = process_mqtt_publisher(node, candidates, state, now=2000.0)
    assert status["published"] is True
    assert len(events) == 1


# ============================================================================
# 3. Tests for crowd_density_heatmap
# ============================================================================

def test_crowd_density_heatmap_generation():
    node = {
        "id": "heat_1",
        "config": {
            "targetClass": "person",
            "colormap": "jet",
            "opacity": 0.5,
            "kernelRadiusPx": 16,
            "decayFactor": 0.9,
            "minDensityThreshold": 0.05,
        }
    }
    state = {}
    frame = np.full((300, 400, 3), 100, dtype=np.uint8)
    candidates = [
        {"class": "person", "bbox": [150, 100, 40, 100]},
        {"class": "person", "bbox": [160, 110, 40, 100]},
    ]

    out_frame, meta = process_crowd_density_heatmap(node, frame, candidates, state, now=10.0)
    assert out_frame.shape == frame.shape
    assert out_frame.dtype == np.uint8
    assert meta["max_density"] > 0.0

    # Feeding subsequent frame with no detections should decay density
    initial_density = meta["max_density"]
    out_frame2, meta2 = process_crowd_density_heatmap(node, frame, [], state, now=11.0)
    assert meta2["max_density"] < initial_density


# ============================================================================
# 4. Tests for ppe_compliance_matrix
# ============================================================================

def test_ppe_compliance_full_compliance():
    node = {
        "id": "ppe_1",
        "config": {
            "requiredPPE": ["helmet", "vest"],
            "minComplianceScore": 70.0,
            "showBadgeOverlay": True,
        }
    }
    state = {}
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Worker at [100, 100, 80, 200]
    # Helmet at top zone: [110, 90, 60, 50]
    # Vest at torso zone: [105, 150, 70, 90]
    candidates = [
        {"class": "person", "track_id": 101, "bbox": [100, 100, 80, 200]},
        {"class": "helmet", "bbox": [110, 95, 60, 45]},
        {"class": "vest", "bbox": [105, 145, 70, 85]}
    ]

    aug_dets, events = process_ppe_compliance_matrix(node, frame, candidates, state, now=500.0)
    worker = next(d for d in aug_dets if d.get("class") == "person")
    assert worker["ppeScore"] == 100.0
    assert worker["ppeStatus"] == "COMPLIANT"
    assert "helmet" in worker["detectedPPE"]
    assert "vest" in worker["detectedPPE"]
    assert len(worker["missingPPE"]) == 0
    assert len(events) == 0


def test_ppe_compliance_violation():
    node = {
        "id": "ppe_2",
        "config": {
            "requiredPPE": ["helmet", "vest"],
            "minComplianceScore": 70.0,
            "alarmCooldownSeconds": 1.0,
            "showBadgeOverlay": True,
        }
    }
    state = {}
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Worker with NO helmet (only vest)
    candidates = [
        {"class": "person", "track_id": 102, "bbox": [200, 100, 80, 200]},
        {"class": "vest", "bbox": [205, 145, 70, 85]}
    ]

    aug_dets, events = process_ppe_compliance_matrix(node, frame, candidates, state, now=500.0)
    worker = next(d for d in aug_dets if d.get("class") == "person")
    assert worker["ppeScore"] == 50.0
    assert worker["ppeStatus"] == "VIOLATION"
    assert "helmet" in worker["missingPPE"]
    assert len(events) == 1
    assert events[0]["event_type"] == "ppe_safety_violation"
    assert events[0]["track_id"] == "102"


def test_ppe_badges_drawing():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dets = [
        {
            "class": "person",
            "bbox": [50, 50, 100, 200],
            "ppeScore": 100.0,
            "ppeStatus": "COMPLIANT",
            "missingPPE": []
        },
        {
            "class": "person",
            "bbox": [250, 50, 100, 200],
            "ppeScore": 0.0,
            "ppeStatus": "VIOLATION",
            "missingPPE": ["helmet", "vest"]
        }
    ]
    # Drawing shouldn't raise any errors
    draw_ppe_compliance_badges(frame, dets)
    assert np.any(frame > 0)
