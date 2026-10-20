import numpy as np
import pytest
import cv2

from engine.object_timer import (
    format_timer,
    process_object_timer,
    draw_object_timer_overlay,
    draw_single_object_timer_badge,
)
from engine.node_catalog import NODE_BLUEPRINTS, OBJECT_EVENT_NODE_TYPES


def test_format_timer():
    assert format_timer(15.2, "seconds") == "15.2s"
    assert format_timer(0.0, "mm:ss") == "00:00"
    assert format_timer(65.0, "mm:ss") == "01:05"
    assert format_timer(3665.0, "hh:mm:ss") == "01:01:05"


def test_catalog_registration():
    assert "object_timer" in OBJECT_EVENT_NODE_TYPES
    assert "object_timer" in NODE_BLUEPRINTS
    bp = NODE_BLUEPRINTS["object_timer"]
    assert bp["title"] == "Object Timer"
    assert "targetClasses" in bp["config"]
    assert "alertThresholdSeconds" in bp["config"]


def test_process_object_timer_with_tracks():
    project_node = {
        "id": "timer_test",
        "type": "object_timer",
        "config": {
            "targetClasses": "person",
            "alertThresholdSeconds": 5.0,
            "graceSeconds": 2.0,
            "timerFormat": "mm:ss",
            "showOverlay": True,
            "showTrackId": True,
            "alertMode": "once",
        },
    }
    state = {}
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Frame 1: Person 1 first seen at t=100.0
    det_t1 = [{"class": "person", "trackId": 1, "bbox": [100, 100, 50, 100]}]
    events1 = process_object_timer(project_node, frame, det_t1, state, now=100.0)
    assert len(events1) == 0
    assert det_t1[0]["timerSeconds"] == 0.0
    assert det_t1[0]["formattedTimer"] == "00:00"
    assert det_t1[0]["isTimerAlert"] is False

    # Frame 2: Person 1 at t=103.5 (3.5s elapsed)
    det_t2 = [{"class": "person", "trackId": 1, "bbox": [102, 100, 50, 100]}]
    events2 = process_object_timer(project_node, frame, det_t2, state, now=103.5)
    assert len(events2) == 0
    assert det_t2[0]["timerSeconds"] == 3.5
    assert det_t2[0]["formattedTimer"] == "00:03"
    assert det_t2[0]["isTimerAlert"] is False

    # Frame 3: Person 1 at t=106.0 (6.0s elapsed -> exceeds 5.0s threshold)
    det_t3 = [{"class": "person", "trackId": 1, "bbox": [105, 100, 50, 100]}]
    events3 = process_object_timer(project_node, frame, det_t3, state, now=106.0)
    assert len(events3) == 1
    ev = events3[0]
    assert ev["kind"] == "object_timer_alert"
    assert ev["trackId"] == 1
    assert ev["class"] == "person"
    assert ev["durationSeconds"] == 6.0
    assert ev["thresholdSeconds"] == 5.0
    assert det_t3[0]["isTimerAlert"] is True

    # Frame 4: Next frame should NOT re-trigger alert since alertMode is "once"
    det_t4 = [{"class": "person", "trackId": 1, "bbox": [105, 100, 50, 100]}]
    events4 = process_object_timer(project_node, frame, det_t4, state, now=107.0)
    assert len(events4) == 0
    assert det_t4[0]["timerSeconds"] == 7.0
    assert det_t4[0]["isTimerAlert"] is True


def test_target_class_filtering():
    project_node = {
        "id": "timer_test",
        "type": "object_timer",
        "config": {
            "targetClasses": "person",
            "alertThresholdSeconds": 10.0,
        },
    }
    state = {}
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    dets = [
        {"class": "car", "trackId": 99, "bbox": [200, 200, 100, 80]},
        {"class": "person", "trackId": 1, "bbox": [100, 100, 40, 80]},
    ]
    process_object_timer(project_node, frame, dets, state, now=50.0)

    # Car should not be tracked or enriched
    assert "timerSeconds" not in dets[0]
    # Person should be tracked and enriched
    assert dets[1]["timerSeconds"] == 0.0


def test_grace_period_and_eviction():
    project_node = {
        "id": "timer_test",
        "type": "object_timer",
        "config": {
            "targetClasses": "person",
            "graceSeconds": 2.0,
        },
    }
    state = {}
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Person 1 present at t=10.0
    det1 = [{"class": "person", "trackId": 1, "bbox": [100, 100, 50, 100]}]
    process_object_timer(project_node, frame, det1, state, now=10.0)

    # Absent at t=11.0 (1.0s gap, less than graceSeconds=2.0)
    process_object_timer(project_node, frame, [], state, now=11.0)
    assert "person:1" in state["tracks"]

    # Re-appears at t=11.5 (timer preserved: 11.5 - 10.0 = 1.5s)
    det2 = [{"class": "person", "trackId": 1, "bbox": [100, 100, 50, 100]}]
    process_object_timer(project_node, frame, det2, state, now=11.5)
    assert det2[0]["timerSeconds"] == 1.5

    # Absent at t=14.0 (gap of 2.5s > graceSeconds) -> track should be evicted
    process_object_timer(project_node, frame, [], state, now=14.0)
    assert "person:1" not in state["tracks"]


def test_overlay_drawing():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    initial_sum = int(np.sum(frame))

    det = {
        "class": "person",
        "bbox": [100, 100, 60, 120],
        "timerSeconds": 15.4,
        "formattedTimer": "00:15",
        "isTimerAlert": False,
        "timerTrackId": 1,
        "showTimerOverlay": True,
    }

    draw_single_object_timer_badge(frame, det, {"showTrackId": True, "badgePosition": "top"})

    # Frame should have been drawn upon
    assert int(np.sum(frame)) > initial_sum

    # Test alert badge
    det["isTimerAlert"] = True
    draw_single_object_timer_badge(frame, det, {"showTrackId": True, "badgePosition": "bottom"})


def test_timer_config_and_inside_positioning():
    project_node = {
        "id": "timer_test",
        "type": "object_timer",
        "config": {
            "targetClasses": "person",
            "badgePosition": "inside",
            "normalColor": "#10b981",
            "alertColor": "#ef4444",
            "showTrackId": False,
        },
    }
    state = {}
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    initial_sum = int(np.sum(frame))

    dets = [{"class": "person", "trackId": 1, "bbox": [100, 100, 80, 150]}]
    process_object_timer(project_node, frame, dets, state, now=10.0)

    # 1. Verification: process_object_timer does NOT burn pixels directly into raw inference frame
    assert int(np.sum(frame)) == initial_sum

    # 2. Verification: det has timerConfig attached with badgePosition="inside"
    assert "timerConfig" in dets[0]
    assert dets[0]["timerConfig"]["badgePosition"] == "inside"
    assert dets[0]["timerConfig"]["showTrackId"] is False

    # 3. Verification: draw_single_object_timer_badge reads timerConfig when config=None
    display_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    draw_single_object_timer_badge(display_frame, dets[0])
    assert int(np.sum(display_frame)) > 0

    # Inside position check: pixels drawn inside bbox (y >= 100 and y <= 250)
    inside_region = display_frame[100:250, 100:180]
    assert int(np.sum(inside_region)) > 0
    # Above region (y < 100) should be untouched because badge is "inside"
    above_region = display_frame[70:100, 100:180]
    assert int(np.sum(above_region)) == 0
