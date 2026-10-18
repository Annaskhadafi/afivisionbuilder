"""Integration tests for VLM Box Tracker with workflow graph and downstream nodes."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "engine"))

import core  # noqa: E402
import main as engine  # noqa: E402
from vlm_box_tracker import VLMBoxTrackerRuntime  # noqa: E402


FRAME = np.zeros((120, 160, 3), dtype=np.uint8)


def _wf(nodes, edges):
    return {"nodes": nodes, "edges": [list(edge) for edge in edges]}


def test_vlm_box_tracker_graph_resolution():
    nodes = [
        {"id": "input", "type": "input", "config": {}},
        {
            "id": "vlm_tracker",
            "type": "vlm_box_tracker",
            "config": {
                "provider": "openrouter",
                "objectPrompt": "tire, worker",
                "apiKey": "test_key",
            },
        },
        {"id": "overlay", "type": "overlay_annotate", "config": {}},
        {"id": "timer", "type": "zone_activity_timer", "config": {"points": "0,0;1,0;1,1;0,1", "confirmationSeconds": 0}},
        {"id": "preview", "type": "preview", "config": {}},
    ]
    edges = [
        ("input", "vlm_tracker"),
        ("vlm_tracker", "overlay"),
        ("overlay", "timer"),
        ("vlm_tracker", "preview"),
    ]
    workflow = _wf(nodes, edges)

    # 1. active_vlm_box_tracker_node should be resolved
    active_vlm = engine.active_vlm_box_tracker_node(workflow)
    assert active_vlm is not None
    assert active_vlm["id"] == "vlm_tracker"

    # 2. Downstream nodes should receive tracked results
    tracked = [
        {
            "id": "vlm_1",
            "trackId": 1,
            "class": "tire",
            "score": 0.95,
            "confidence": 0.95,
            "bbox": [20, 20, 40, 40],
            "kind": "detection",
            "sourceNodeId": "vlm_tracker",
        }
    ]
    results_overlay = engine.results_for_node(workflow, "overlay", [], tracked)
    assert len(results_overlay) == 1
    assert results_overlay[0]["class"] == "tire"

    results_timer = engine.results_for_node(workflow, "timer", [], tracked)
    assert len(results_timer) == 1
    assert results_timer[0]["trackId"] == 1

    results_preview = engine.results_for_node(workflow, "preview", [], tracked)
    assert len(results_preview) == 1


def test_vlm_box_tracker_downstream_zone_timer():
    nodes = [
        {"id": "input", "type": "input", "config": {}},
        {"id": "vlm_tracker", "type": "vlm_box_tracker", "config": {"objectPrompt": "tire, person"}},
        {"id": "timer", "type": "zone_activity_timer", "config": {"points": "0,0;1,0;1,1;0,1", "confirmationSeconds": 0}},
        {"id": "alert", "type": "alert", "config": {}},
    ]
    edges = [
        ("input", "vlm_tracker"),
        ("vlm_tracker", "timer"),
        ("timer", "alert"),
    ]
    workflow = _wf(nodes, edges)

    # Simulate VLM tracker emitting tire and person
    tracked = [
        {"id": "vlm_1", "trackId": 1, "class": "tire", "score": 0.9, "bbox": [20, 20, 30, 30], "kind": "detection", "sourceNodeId": "vlm_tracker"},
        {"id": "vlm_2", "trackId": 2, "class": "person", "score": 0.85, "bbox": [50, 50, 20, 40], "kind": "detection", "sourceNodeId": "vlm_tracker"},
    ]
    event_runtime = {}
    logic_runtime = {}
    now = 100.0

    extra_events, _, _, _ = core._process_track_event_nodes(
        cv2, FRAME, workflow, tracked.copy(), tracked, logic_runtime, event_runtime, now,
    )
    # Zone activity timer should confirm activity
    assert any(ev.get("kind") == "zone_activity" for ev in extra_events)
    assert any(ev.get("kind") == "zone_activity_event" and ev.get("state") in ("WORKING", "CONFIRMING") for ev in extra_events)

    # Downstream alert should receive zone_activity_event
    alert_events = engine.results_for_node(workflow, "alert", extra_events, tracked)
    assert any(ev.get("kind") == "zone_activity_event" for ev in alert_events)


def test_vlm_box_tracker_runtime_integration():
    cfg = {
        "provider": "openrouter",
        "objectPrompt": "tire, worker",
        "apiKey": "mock_api_key",
        "queryIntervalSeconds": 0.5,
    }
    runtime = VLMBoxTrackerRuntime("vlm_test_node", cfg)
    try:
        # Pre-seed detection response
        with runtime.lock:
            runtime.latest_detections = [
                {"class": "tire", "box": (0.1, 0.1, 0.4, 0.4), "confidence": 0.92}
            ]
            runtime.latest_result_frame_id = 1
            runtime.result_seq = 1

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        # Add texture in box
        frame[10:40, 10:40] = 200

        res1 = runtime.update(frame, timestamp=1.0)
        assert len(res1) == 1
        assert res1[0]["class"] == "tire"
        assert res1[0]["trackId"] == 1
        assert res1[0]["sourceNodeId"] == "vlm_test_node"

        # Next frame
        res2 = runtime.update(frame, timestamp=1.05)
        assert len(res2) == 1
        assert res2[0]["trackId"] == 1
    finally:
        runtime.close()


if __name__ == "__main__":
    test_vlm_box_tracker_graph_resolution()
    test_vlm_box_tracker_downstream_zone_timer()
    test_vlm_box_tracker_runtime_integration()
    print("All VLM box tracker integration tests passed successfully!")
