import pytest
import numpy as np
from engine.multi_zone_occupancy import (
    _inside_polygon,
    is_detection_in_zone,
    format_duration_human,
    process_multi_zone_occupancy,
    parse_zones_config,
)

def test_point_in_polygon():
    poly = [(100.0, 100.0), (500.0, 100.0), (500.0, 500.0), (100.0, 500.0)]
    assert _inside_polygon((300.0, 300.0), poly) is True
    assert _inside_polygon((700.0, 700.0), poly) is False
    assert _inside_polygon((50.0, 300.0), poly) is False

def test_detection_in_zone_person():
    poly = [(200.0, 200.0), (600.0, 200.0), (600.0, 600.0), (200.0, 600.0)]
    # Person with feet at (350, 350)
    # bbox: [x, y, w, h] -> [300, 100, 100, 250], feet = 100 + 250 = 350 (inside 200..600)
    det_inside = {"class": "person", "bbox": [300.0, 100.0, 100.0, 250.0]}
    assert is_detection_in_zone(det_inside, poly) is True

    # Person completely outside
    det_outside = {"class": "person", "bbox": [800.0, 800.0, 100.0, 150.0]}
    assert is_detection_in_zone(det_outside, poly) is False

def test_format_duration_human():
    assert format_duration_human(45) == "45s"
    assert format_duration_human(75) == "1m 15s"
    assert format_duration_human(3665) == "1h 01m"

def test_process_multi_zone_occupancy_lifecycle():
    node = {
        "id": "node_mzo_1",
        "type": "multi_zone_occupancy",
        "config": {
            "targetClasses": "person",
            "confirmationSeconds": 2.0,
            "graceSeconds": 3.0,
            "maxDwellMinutes": 1.0,  # 60 seconds
            "zones": [
                {
                    "id": "zone_1",
                    "name": "Meja 1",
                    "capacity": 2,
                    "points": "0.1,0.1; 0.5,0.1; 0.5,0.5; 0.1,0.5"
                },
                {
                    "id": "zone_2",
                    "name": "Meja 2",
                    "capacity": 4,
                    "points": "0.6,0.1; 0.9,0.1; 0.9,0.5; 0.6,0.5"
                }
            ]
        }
    }

    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    runtime = {}

    # Person inside Zone 1 (normalized ~0.25 -> pixel 320, 180)
    det_person_1 = [{"class": "person", "bbox": [300.0, 150.0, 60.0, 100.0]}]

    # Step 1: Person enters zone 1 at t=100.0 (First frame: starts confirmation)
    events_1 = process_multi_zone_occupancy(node, dummy_frame, det_person_1, runtime, now=100.0)
    assert len(events_1) == 0
    snap = runtime["node_mzo_1"]["snapshot"]
    assert snap["totalZones"] == 2
    assert snap["occupiedZones"] == 0

    # Step 2: Still at t=101.0 (< 2.0s confirmation)
    events_2 = process_multi_zone_occupancy(node, dummy_frame, det_person_1, runtime, now=101.0)
    assert len(events_2) == 0

    # Step 3: At t=102.5 (> 2.0s confirmation) -> transitions to OCCUPIED and emits zone_occupied
    events_3 = process_multi_zone_occupancy(node, dummy_frame, det_person_1, runtime, now=102.5)
    assert len(events_3) == 1
    assert events_3[0]["kind"] == "zone_occupied"
    assert events_3[0]["zoneId"] == "zone_1"
    assert events_3[0]["zoneName"] == "Meja 1"

    snap_3 = runtime["node_mzo_1"]["snapshot"]
    assert snap_3["occupiedZones"] == 1
    z1 = next(z for z in snap_3["zones"] if z["id"] == "zone_1")
    assert z1["status"] == "OCCUPIED"

    # Step 4: Add 2 more people (total 3 > capacity 2) -> OVER_CAPACITY
    det_3_people = [
        {"class": "person", "bbox": [200.0, 150.0, 50.0, 50.0]},
        {"class": "person", "bbox": [300.0, 150.0, 50.0, 50.0]},
        {"class": "person", "bbox": [400.0, 150.0, 50.0, 50.0]}
    ]
    process_multi_zone_occupancy(node, dummy_frame, det_3_people, runtime, now=110.0)
    z1_oc = next(z for z in runtime["node_mzo_1"]["snapshot"]["zones"] if z["id"] == "zone_1")
    assert z1_oc["status"] == "OVER_CAPACITY"

    # Step 5: Dwell time exceeds maxDwellMinutes (60s) -> emit zone_overstay
    events_overstay = process_multi_zone_occupancy(node, dummy_frame, det_person_1, runtime, now=165.0)
    overstay_evs = [e for e in events_overstay if e["kind"] == "zone_overstay"]
    assert len(overstay_evs) == 1
    assert overstay_evs[0]["zoneId"] == "zone_1"

    # Step 6: Empty zone at t=170.0 (grace=3.0s) -> PENDING_VACANT, no event yet
    events_vacate_1 = process_multi_zone_occupancy(node, dummy_frame, [], runtime, now=170.0)
    assert len(events_vacate_1) == 0

    # Step 7: At t=174.0 (> grace 3.0s) -> emit zone_vacated
    events_vacate_2 = process_multi_zone_occupancy(node, dummy_frame, [], runtime, now=174.0)
    vacated_evs = [e for e in events_vacate_2 if e["kind"] == "zone_vacated"]
    assert len(vacated_evs) == 1
    assert vacated_evs[0]["zoneId"] == "zone_1"
    assert vacated_evs[0]["durationSeconds"] >= 60.0
    assert vacated_evs[0]["turnoverIndex"] == 1

    # Verify reset to VACANT
    z1_vac = next(z for z in runtime["node_mzo_1"]["snapshot"]["zones"] if z["id"] == "zone_1")
    assert z1_vac["status"] == "VACANT"
    assert runtime["node_mzo_1"]["snapshot"]["occupiedZones"] == 0

def test_catalog_registration():
    from engine.node_catalog import NODE_BLUEPRINTS, OBJECT_EVENT_NODE_TYPES
    assert "multi_zone_occupancy" in OBJECT_EVENT_NODE_TYPES
    bp = NODE_BLUEPRINTS.get("multi_zone_occupancy")
    assert bp is not None
    assert bp["category"] == "Tracking & Analysis"
    assert "zones" in bp["config"]
