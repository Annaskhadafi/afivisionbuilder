import time
import numpy as np
import pytest

from engine.video_kinematics import (
    point_to_segment_distance,
    point_to_polyline_distance,
    calculate_object_velocities,
    check_path_deviation,
)
from engine.advanced_logic import (
    compute_box_intersection_area,
    analyze_overlap,
    evaluate_delta_filter,
    route_switch_case,
)
from engine.project_nodes import _resolve_zone_polygon


def test_point_to_polyline_distance():
    polyline = [(0.0, 100.0), (200.0, 100.0)]
    # Point directly on line
    assert point_to_polyline_distance(100.0, 100.0, polyline) == 0.0
    # Point 50px above line
    assert point_to_polyline_distance(100.0, 50.0, polyline) == 50.0


def test_calculate_object_velocities():
    # 25 pixels per meter.
    # At t=10.0, forklift at (100, 100). At t=11.0, forklift moved 250 px (10 meters in 1s -> 10 m/s = 36 km/h)
    config = {
        "pixelPerMeter": 25.0,
        "speedLimitKmh": 20.0,
        "speedUnit": "kmh",
        "smoothingWindow": 5,
        "triggerAlarmOnSpeeding": True,
        "alarmCooldownSeconds": 1.0,
    }
    state = {}
    det1 = [{"class": "forklift", "track_id": 5, "bbox": [80, 80, 40, 40]}]
    calculate_object_velocities(det1, config, state, now=10.0)

    # Move by 250 px in 1 second
    det2 = [{"class": "forklift", "track_id": 5, "bbox": [330, 80, 40, 40]}]
    augmented, events = calculate_object_velocities(det2, config, state, now=11.0)

    assert len(augmented) == 1
    forklift = augmented[0]
    assert forklift["speed_mps"] == 10.0
    assert forklift["speed_kmh"] == 36.0
    assert forklift["is_overspeed"] is True

    assert len(events) == 1
    assert events[0]["event_type"] == "overspeed_detected"
    assert "36.0 km/h" in events[0]["message"]


def test_check_path_deviation():
    # Guide path polyline along y = 500 (across width 1000)
    config = {
        "guidePathPoints": "0,500; 1000,500",
        "maxAllowedDeviationMeters": 2.0,
        "pixelPerMeter": 10.0,  # 2.0 meters = 20 pixels
        "targetClasses": "forklift",
        "triggerAlarmOnDeviation": True,
    }
    state = {}

    # Forklift at y=510 (deviation 10px / 10 = 1.0m <= 2.0m -> compliant)
    det_ok = [{"class": "forklift", "track_id": 1, "bbox": [200, 490, 40, 20]}]  # bottom center y = 510
    aug_ok, ev_ok = check_path_deviation(det_ok, config, state, frame_size=(1000, 1000), now=1.0)
    assert aug_ok[0]["is_path_deviated"] is False
    assert len(ev_ok) == 0

    # Forklift at y=600 (deviation 100px / 10 = 10.0m > 2.0m -> deviated)
    det_dev = [{"class": "forklift", "track_id": 1, "bbox": [200, 580, 40, 20]}]  # bottom center y = 600
    aug_dev, ev_dev = check_path_deviation(det_dev, config, state, frame_size=(1000, 1000), now=2.0)
    assert aug_dev[0]["is_path_deviated"] is True
    assert len(ev_dev) == 1
    assert ev_dev[0]["event_type"] == "path_deviation_detected"


def test_analyze_overlap_ppe_compliance():
    # Person at [100, 100, 60, 120] -> top half is [100, 100, 60, 60]
    # Helmet at [110, 105, 40, 30] -> fully inside top half
    detections_compliant = [
        {"class": "person", "track_id": 1, "bbox": [100, 100, 60, 120]},
        {"class": "helmet", "track_id": 2, "bbox": [110, 105, 40, 30]},
    ]
    config = {
        "parentClass": "person",
        "childClass": "helmet",
        "minOverlapRatio": 0.5,
        "parentRegion": "top_half",
        "triggerAlarmOnNonCompliance": True,
    }
    state = {}
    aug, ev = analyze_overlap(detections_compliant, config, state, now=1.0)
    person = next(d for d in aug if d["class"] == "person")
    assert person["is_compliant"] is True
    assert len(ev) == 0

    # Person without helmet
    detections_violation = [
        {"class": "person", "track_id": 3, "bbox": [200, 100, 60, 120]}
    ]
    aug_v, ev_v = analyze_overlap(detections_violation, config, state, now=2.0)
    person_v = next(d for d in aug_v if d["class"] == "person")
    assert person_v["is_compliant"] is False
    assert len(ev_v) == 1
    assert ev_v[0]["event_type"] == "compliance_violation"


def test_evaluate_delta_filter():
    frame1 = np.ones((180, 320, 3), dtype=np.uint8) * 100
    config = {
        "deltaThreshold": 0.05,
        "heartbeatIntervalSeconds": 10.0,
    }
    state = {}

    # First frame always passes
    cont1, score1 = evaluate_delta_filter(frame1, config, state, now=1.0)
    assert cont1 is True

    # Identical frame -> throttled / skipped
    cont2, score2 = evaluate_delta_filter(frame1, config, state, now=2.0)
    assert cont2 is False
    assert score2 == 0.0

    # Sudden high motion -> passes
    frame_motion = frame1.copy()
    frame_motion[20:160, 50:280] = 250
    cont3, score3 = evaluate_delta_filter(frame_motion, config, state, now=3.0)
    assert cont3 is True
    assert score3 > 0.05

    # Heartbeat test when static
    cont4, _ = evaluate_delta_filter(frame_motion, config, state, now=15.0)
    assert cont4 is True  # forced by heartbeat!


def test_route_switch_case():
    items = [
        {"class": "person", "id": 1},
        {"class": "forklift", "id": 2},
        {"class": "unknown_box", "id": 3},
    ]
    config = {
        "evaluationField": "class",
        "cases": "person:port_workers, forklift:port_vehicles",
        "defaultPort": "port_misc",
    }
    routed = route_switch_case(items, config)
    assert len(routed["port_workers"]) == 1
    assert len(routed["port_vehicles"]) == 1
    assert len(routed["port_misc"]) == 1


def test_dynamic_zone_anchor():
    # Frame 1000x1000
    # Original polygon at (200, 200) to (400, 400) -> poly center = (300, 300)
    config = {
        "mode": "dynamic_anchor",
        "anchorClass": "truck",
        "points": "0.2,0.2; 0.4,0.2; 0.4,0.4; 0.2,0.4",
    }
    # Truck centered at (600, 600) -> [500, 500, 200, 200]
    detections = [
        {"class": "truck", "bbox": [500, 500, 200, 200]}
    ]
    polygon, w, h = _resolve_zone_polygon(config, {"width": 1000, "height": 1000}, detections)

    # The shifted polygon should have its centroid at (600, 600)
    poly_cx = sum(p[0] for p in polygon) / len(polygon)
    poly_cy = sum(p[1] for p in polygon) / len(polygon)
    assert abs(poly_cx - 600.0) < 1.0
    assert abs(poly_cy - 600.0) < 1.0
