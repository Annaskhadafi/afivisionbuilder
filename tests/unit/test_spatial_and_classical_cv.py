import math
import numpy as np
import pytest
import cv2

from engine.spatial_measurement import (
    measure_distance_between_objects,
    measure_object_dimensions,
    calculate_centroid,
    calculate_bottom_center,
    draw_distance_measurement_overlay,
)
from engine.classical_cv import (
    compute_camera_focus_score,
    auto_rotate_edges,
    parse_roi_points,
)


def test_centroid_and_bottom_center():
    bbox = [100.0, 100.0, 50.0, 80.0]  # x, y, w, h
    cx, cy = calculate_centroid(bbox)
    assert cx == 125.0
    assert cy == 140.0

    bc_x, bc_y = calculate_bottom_center(bbox)
    assert bc_x == 125.0
    assert bc_y == 180.0


def test_measure_distance_between_objects():
    # Person at bottom (100, 200), Forklift at bottom (100, 300) -> 100 px distance
    # With pixelRatio = 10.0, distance = 10 cm
    detections = [
        {"class": "person", "track_id": 1, "bbox": [80, 100, 40, 100]},     # bottom_center = (100, 200)
        {"class": "forklift", "track_id": 2, "bbox": [80, 200, 40, 100]},   # bottom_center = (100, 300)
    ]
    config = {
        "objectAClass": "person",
        "objectBClass": "forklift",
        "measurementAxis": "euclidean",
        "pixelRatio": 10.0,
        "minDistanceThreshold": 50.0,  # 50 cm -> 10 cm will trigger violation
        "triggerAlarmOnProximity": True,
        "anchorMode": "bottom_center",
    }
    state = {}
    measurements, events = measure_distance_between_objects(None, detections, config, state)

    assert len(measurements) == 1
    m = measurements[0]
    assert m["distance_px"] == 100.0
    assert m["distance_cm"] == 10.0
    assert m["is_violation"] is True

    assert len(events) == 1
    assert events[0]["event_type"] == "proximity_violation"
    assert "Peringatan jarak dekat" in events[0]["message"]

    # Verify horizontal axis calculation
    config["measurementAxis"] = "horizontal"
    measurements_h, _ = measure_distance_between_objects(None, detections, config, {})
    assert measurements_h[0]["distance_px"] == 0.0
    assert measurements_h[0]["distance_cm"] == 0.0


def test_measure_object_dimensions():
    # Box 100x200 px with pixelPerUnit = 10.0 -> 10x20 cm, area 200 cm2
    detections = [
        {"class": "box", "track_id": 10, "bbox": [50, 50, 100, 200]},
        {"class": "person", "track_id": 11, "bbox": [200, 50, 50, 150]},
    ]
    config = {
        "targetClass": "box",
        "pixelPerUnit": 10.0,
        "unitName": "cm",
        "minAllowedWidth": 8.0,
        "maxAllowedWidth": 12.0,  # 10 is within [8, 12]
        "minAllowedHeight": 25.0,  # 20 is LESS than 25 -> violation!
        "maxAllowedHeight": 0.0,
        "triggerAlarmOnToleranceViolation": True,
    }
    augmented, events = measure_object_dimensions(None, detections, config)

    assert len(augmented) == 2
    box_det = augmented[0]
    assert "measurements" in box_det
    meas = box_det["measurements"]
    assert meas["width"] == 10.0
    assert meas["height"] == 20.0
    assert meas["area"] == 200.0
    assert meas["unit"] == "cm"
    assert meas["is_within_tolerance"] is False

    assert len(events) == 1
    assert events[0]["event_type"] == "dimension_tolerance_violation"
    assert "height 20.0 < min 25.0" in events[0]["message"]


def test_camera_focus_score_sharp_vs_blur():
    # Sharp image with high contrast checkerboard pattern
    sharp = np.zeros((200, 200, 3), dtype=np.uint8)
    sharp[::20, :] = 255
    sharp[:, ::20] = 255

    # Blur image with heavy Gaussian blur
    blurred = cv2.GaussianBlur(sharp, (31, 31), 10.0)

    config = {
        "blurThreshold": 50.0,
        "checkIntervalSeconds": 0.0,
        "enableAlarm": True,
    }
    state_sharp = {}
    score_sharp, is_blur_sharp, events_sharp = compute_camera_focus_score(sharp, config, state_sharp)
    assert score_sharp > 50.0
    assert is_blur_sharp is False
    assert len(events_sharp) == 0

    state_blur = {}
    score_blur, is_blur_blurred, events_blur = compute_camera_focus_score(blurred, config, state_blur)
    assert score_blur < score_sharp
    assert is_blur_blurred is True
    assert len(events_blur) == 1
    assert events_blur[0]["event_type"] == "camera_blur_detected"


def test_parse_roi_points():
    pts = parse_roi_points("0.1,0.1; 0.9,0.1; 0.9,0.9; 0.1,0.9", width=1000, height=500)
    assert pts is not None
    assert len(pts) == 4
    assert np.array_equal(pts[0], [100, 50])
    assert np.array_equal(pts[2], [900, 450])


def test_auto_rotate_edges():
    # Create an image with an intentionally skewed high-contrast white rectangle
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    rect_pts = np.array([[100, 150], [250, 120], [270, 220], [120, 250]], dtype=np.int32)
    cv2.fillPoly(img, [rect_pts], (255, 255, 255))

    config = {
        "maxAngleLimit": 45.0,
        "minAngleThreshold": 0.5,
        "borderMode": "black_constant",
    }
    rotated, angle = auto_rotate_edges(img, config)
    assert rotated.shape == img.shape
    assert angle != 0.0
    assert abs(angle) <= 45.0


def test_draw_distance_measurement_overlay():
    frame = np.zeros((300, 300, 3), dtype=np.uint8)
    measurements = [
        {
            "object_a": {"point": (50, 50)},
            "object_b": {"point": (150, 150)},
            "distance_cm": 25.4,
            "is_violation": True,
        }
    ]
    draw_distance_measurement_overlay(frame, measurements)
    # Frame should no longer be completely black
    assert np.any(frame > 0)
