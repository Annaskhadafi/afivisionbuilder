import numpy as np
import pytest
from engine.video_kinematics import (
    calculate_object_velocities,
    draw_single_velocity_badge,
    _extract_box,
)
from engine.main import results_for_node


def test_velocity_calculator_with_tracker_track_id():
    """Verify velocity calculation works when input uses Roboflow/ByteTrack 'trackId'."""
    config = {
        "pixelPerMeter": 20.0,
        "speedLimitKmh": 25.0,
        "speedUnit": "kmh",
        "smoothingWindow": 5,
        "triggerAlarmOnSpeeding": True,
        "alarmCooldownSeconds": 2.0,
    }
    state = {}
    
    # Frame 1 at t=0.0s: Car at (100, 100)
    dets1 = [{"class": "car", "trackId": 12, "bbox": [100, 100, 50, 30]}]
    aug1, ev1 = calculate_object_velocities(dets1, config, state, now=0.0, node_id="vel_1")
    assert len(aug1) == 1
    assert aug1[0]["speed_kmh"] == 0.0
    assert aug1[0]["speed_formatted"] == "0.0 km/h"
    assert aug1[0]["is_overspeed"] is False
    assert len(ev1) == 0

    # Frame 2 at t=1.0s: Car moved by 200px (10 meters in 1s = 10 m/s = 36 km/h > 25 km/h)
    dets2 = [{"class": "car", "trackId": 12, "bbox": [300, 100, 50, 30]}]
    aug2, ev2 = calculate_object_velocities(dets2, config, state, now=1.0, node_id="vel_1")
    assert len(aug2) == 1
    assert aug2[0]["speed_mps"] == 10.0
    assert aug2[0]["speed_kmh"] == 36.0
    assert aug2[0]["speed_formatted"] == "36.0 km/h"
    assert aug2[0]["is_overspeed"] is True
    assert aug2[0]["showVelocityOverlay"] is True

    # Check event structure for downstream alerts
    assert len(ev2) == 1
    event = ev2[0]
    assert event["kind"] == "overspeed_detected"
    assert event["event_type"] == "overspeed_detected"
    assert event["sourceNodeId"] == "vel_1"
    assert event["trackId"] == 12
    assert event["speed_kmh"] == 36.0
    assert "36.0 km/h" in event["message"]


def test_velocity_calculator_untracked_auto_fallback():
    """Verify velocity calculates even if no tracker node is in pipeline (auto-tracks via spatial proximity)."""
    config = {
        "pixelPerMeter": 10.0,
        "speedLimitKmh": 50.0,
        "speedUnit": "kmh",
    }
    state = {}

    # Frame 1: Untracked person
    dets1 = [{"class": "person", "bbox": [50, 50, 30, 60]}]
    aug1, ev1 = calculate_object_velocities(dets1, config, state, now=10.0)
    assert len(aug1) == 1
    auto_id = aug1[0].get("trackId")
    assert auto_id is not None  # Auto-assigned ID

    # Frame 2: Person moved slightly
    dets2 = [{"class": "person", "bbox": [70, 50, 30, 60]}]
    aug2, ev2 = calculate_object_velocities(dets2, config, state, now=10.5)
    assert aug2[0].get("trackId") == auto_id
    assert aug2[0]["speed_mps"] > 0.0


def test_velocity_calculator_deadzone_filter():
    """Verify jitter below minSpeedKmh is suppressed to 0.0 km/h."""
    config = {
        "pixelPerMeter": 100.0,
        "minSpeedKmh": 1.0,
        "speedUnit": "kmh",
    }
    state = {}

    # Jitter of 1 pixel in 1 second = 0.01 m/s = 0.036 km/h (< 1.0 km/h)
    dets1 = [{"class": "forklift", "trackId": 3, "bbox": [200, 200, 50, 50]}]
    calculate_object_velocities(dets1, config, state, now=0.0)

    dets2 = [{"class": "forklift", "trackId": 3, "bbox": [201, 200, 50, 50]}]
    aug2, _ = calculate_object_velocities(dets2, config, state, now=1.0)
    assert aug2[0]["speed_kmh"] == 0.0
    assert aug2[0]["speed_formatted"] == "0.0 km/h"


def test_draw_single_velocity_badge():
    """Verify visual rendering on image buffer does not crash and alters pixels."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    det_normal = {
        "bbox": [100, 100, 80, 60],
        "speed_formatted": "12.4 km/h",
        "is_overspeed": False,
        "trackId": 7,
        "velocityConfig": {"badgePosition": "top", "normalColor": "#10b981"}
    }
    draw_single_velocity_badge(frame, det_normal)
    # Ensure drawing happened
    assert np.any(frame != 0)

    # Test overspeed badge
    frame_alert = np.zeros((480, 640, 3), dtype=np.uint8)
    det_alert = {
        "bbox": [100, 100, 80, 60],
        "speed_formatted": "32.0 km/h",
        "is_overspeed": True,
        "trackId": 7,
        "velocityConfig": {"badgePosition": "bottom", "alertColor": "#ef4444"}
    }
    draw_single_velocity_badge(frame_alert, det_alert)
    assert np.any(frame_alert != 0)


def test_velocity_downstream_event_routing():
    """Verify results_for_node correctly passes overspeed_detected events to alert node."""
    workflow = {
        "nodes": [
            {"id": "input_1", "type": "input", "enabled": True},
            {"id": "det_1", "type": "detector", "enabled": True},
            {"id": "vel_1", "type": "velocity_calculator", "enabled": True},
            {"id": "alert_1", "type": "alert", "enabled": True},
        ],
        "edges": [
            ["input_1", "det_1"],
            ["det_1", "vel_1"],
            ["vel_1", "alert_1"],
        ]
    }
    detections = [
        {
            "kind": "overspeed_detected",
            "sourceNodeId": "vel_1",
            "trackId": 5,
            "speed_kmh": 40.0,
            "message": "Speeding alert"
        }
    ]
    routed = results_for_node(workflow, "alert_1", detections)
    assert len(routed) == 1
    assert routed[0]["kind"] == "overspeed_detected"
