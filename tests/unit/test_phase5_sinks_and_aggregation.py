"""Unit tests for Phase 5: Cloud Sinks, Aggregation, and Hardware PTZ.

Covers:
- Data Aggregator (rolling window rollup metrics: count, sum_duration, avg_duration, max_occupancy)
- CSV Formatter (tabular formatting, delimiter support, alias mapping, file export)
- S3 Cloud Sink (image compression, simulated/live S3 URL generation, payload verification)
- Notification Dispatcher (multi-channel routing, template formatting, cooldown throttling)
- PTZ Controller (centroid extraction, normalized error, deadzone filtering, pan/tilt continuous velocity)
"""
import sys
import os
import time
import numpy as np
import pytest

# Ensure engine path is accessible
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "engine"))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from data_aggregation import DataAggregator, aggregate_events, format_events_as_csv
from cloud_sinks import upload_to_s3, dispatch_notification
from ptz_controller import calculate_ptz_velocity, _extract_centroid


def test_data_aggregator_rolling_window():
    config = {"windowMinutes": 1.0}  # 60 seconds
    agg = DataAggregator(config)
    now = 1000.0

    # Add 3 events
    agg.add_event({"type": "zone_work", "durationSeconds": 10.0, "occupancy": 2}, timestamp=now - 40.0)
    agg.add_event({"type": "zone_work", "durationSeconds": 20.0, "occupancy": 5}, timestamp=now - 20.0)
    agg.add_event({"type": "zone_work", "durationSeconds": 30.0, "occupancy": 3}, timestamp=now)

    summary = agg.compute_summary(now=now)
    assert summary["totalRecords"] == 3
    assert summary["metrics"]["count"] == 3
    assert summary["metrics"]["sumDurationSeconds"] == 60.0
    assert summary["metrics"]["avgDurationSeconds"] == 20.0
    assert summary["metrics"]["maxOccupancy"] == 5

    # Move time forward by 30 seconds (cutoff = 1030 - 60 = 970; event 1 at 960 is pruned, events 2 & 3 remain)
    future = now + 30.0
    future_summary = agg.compute_summary(now=future)
    assert future_summary["totalRecords"] == 2
    assert future_summary["metrics"]["count"] == 2
    assert future_summary["metrics"]["sumDurationSeconds"] == 50.0
    assert future_summary["metrics"]["avgDurationSeconds"] == 25.0


def test_aggregate_events_wrapper():
    state = {}
    config = {"windowMinutes": 5}
    events = [{"durationSeconds": 15.0, "item_count": 4}]
    res = aggregate_events(events, config, state, now=500.0)
    assert res["totalRecords"] == 1
    assert res["metrics"]["sumDurationSeconds"] == 15.0
    assert "_aggregator" in state


def test_format_events_as_csv(tmp_path):
    events = [
        {"timestamp": "2026-10-19 12:00:00", "zoneName": "Bay-1", "type": "exit", "durationSeconds": 45.5, "itemCount": 2},
        {"timestamp": "2026-10-19 12:05:00", "zoneName": "Bay-2", "type": "entry", "durationSeconds": 12.0, "itemCount": 1},
    ]
    out_file = str(tmp_path / "events.csv")
    config = {
        "columns": "timestamp,zone_name,type,working_seconds,item_count",
        "delimiter": ",",
        "outputFilePath": out_file,
    }
    csv_str, written_path = format_events_as_csv(events, config)
    assert written_path == out_file
    assert "Bay-1" in csv_str
    assert "Bay-2" in csv_str
    assert "45.5" in csv_str

    # Verify file content
    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "2026-10-19 12:00:00,Bay-1,exit,45.5,2" in content


def test_upload_to_s3_mock():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    config = {
        "endpointUrl": "https://s3.ap-southeast-1.amazonaws.com",
        "bucketName": "chitra-cctv-records",
        "objectPrefix": "workshop_events",
        "imageQuality": 90,
    }
    meta = {"zone": "Welding", "event": "violation"}
    res = upload_to_s3(img, None, meta, config)

    assert res["status"] in ("mock_uploaded", "simulated_uploaded")
    assert res["bucket"] == "chitra-cctv-records"
    assert "workshop_events" in res["key"]
    assert res["s3Url"].startswith("https://s3.ap-southeast-1.amazonaws.com/chitra-cctv-records/")
    assert res["bytesCount"] > 0
    assert res["metadata"] == meta


def test_dispatch_notification_cooldown():
    node_state = {}
    config = {
        "channel": "telegram",
        "destinationId": "-100987654321",
        "botToken": "123456:FAKE_TOKEN_XYZ",
        "messageTemplate": "Alert {event.type} in {event.zoneName}",
        "cooldownSeconds": 10.0,
        "attachImage": False,
    }
    event = {"type": "fire_hazard", "zoneName": "Paint Shop"}

    # First dispatch -> mock_dispatched, dispatched, or dispatched_local_fallback
    res1 = dispatch_notification(event, None, config, node_state)
    assert res1["status"] in ("mock_dispatched", "dispatched", "simulated_dispatched", "dispatched_local_fallback")
    assert res1["channel"] == "telegram"
    assert "fire_hazard" in res1["message"]

    # Second dispatch immediately -> should throttle due to cooldown
    res2 = dispatch_notification(event, None, config, node_state)
    assert res2["status"] == "throttled"
    assert res2["cooldownRemaining"] > 0


def test_ptz_controller_centroid_and_velocity():
    # Centered target in a 640x480 frame
    dets_centered = [{"box": [270, 190, 370, 290], "class": "forklift", "track_id": "T1"}]
    # Centroid: cx = 320, cy = 240 (perfect center)
    cx, cy = _extract_centroid(dets_centered[0])
    assert cx == 320.0
    assert cy == 240.0

    state = {}
    config = {
        "cameraIp": "192.168.1.55",
        "targetClass": "forklift",
        "deadzonePercent": 0.15,
        "panSpeed": 0.8,
        "tiltSpeed": 0.8,
    }

    res_centered = calculate_ptz_velocity(dets_centered, (640, 480), config, state)
    assert res_centered["status"] == "centered"
    assert res_centered["pan"] == 0.0
    assert res_centered["tilt"] == 0.0

    # Target far to the right (cx = 600, well outside 15% deadzone)
    dets_right = [{"box": [550, 190, 650, 290], "class": "forklift", "track_id": "T1"}]
    res_right = calculate_ptz_velocity(dets_right, (640, 480), config, state)
    assert res_right["pan"] > 0.0  # Must pan right (positive)

    # Target far to the left (cx = 40)
    dets_left = [{"box": [0, 190, 80, 290], "class": "forklift", "track_id": "T1"}]
    res_left = calculate_ptz_velocity(dets_left, (640, 480), config, state)
    assert res_left["pan"] < 0.0  # Must pan left (negative)

    # Idle when no target matches
    res_idle = calculate_ptz_velocity([], (640, 480), config, state)
    assert res_idle["status"] == "idle"
    assert res_idle["pan"] == 0.0
    assert res_idle["tilt"] == 0.0
