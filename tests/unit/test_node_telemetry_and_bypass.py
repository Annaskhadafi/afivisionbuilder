"""Unit tests for n8n-style Node Activation (Toggle On/Off/Bypass) and Live Execution Telemetry.

Covers:
- Bypass pass-through mode: Intermediate disabled nodes forward graph streams without breaking reachability.
- WorkflowRunner telemetry storage: Recording per-node status, latency, item count, and payloads.
- Status API exposure: nodeTelemetry dictionary correctly returned in runner.status().
- Error tracking: Recording runtime exceptions in telemetry.
"""
import sys
import os
import time
import pytest

ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "engine"))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import main as engine
import core


def test_bypass_pass_through_reachability():
    """Verify that disabled intermediate nodes do not break downstream reachability."""
    # Linear graph: input -> resize (disabled) -> detector -> preview
    workflow = {
        "nodes": [
            {"id": "input", "type": "input", "enabled": True},
            {"id": "resize", "type": "resize", "enabled": False},
            {"id": "detector", "type": "detector", "enabled": True},
            {"id": "preview", "type": "preview", "enabled": True},
        ],
        "edges": [
            ["input", "resize"],
            ["resize", "detector"],
            ["detector", "preview"],
        ],
    }

    # Input cannot reach disabled resize directly as an active target
    assert not engine.has_active_path(workflow, "input", "resize")
    # But input CAN reach detector by passing through the bypassed resize node!
    assert engine.has_active_path(workflow, "input", "detector")
    # And input can reach preview
    assert engine.has_active_path(workflow, "input", "preview")


def test_bypass_intermediate_tracker_path():
    """Verify tracker continuous path allows traversing bypassed intermediate nodes."""
    workflow = {
        "nodes": [
            {"id": "input", "type": "input", "enabled": True},
            {"id": "detector", "type": "detector", "enabled": True},
            {"id": "tracker", "type": "tracker", "enabled": True},
            {"id": "filter", "type": "filter", "enabled": False}, # Bypassed filter
            {"id": "counter", "type": "object_counter", "enabled": True},
        ],
        "edges": [
            ["input", "detector"],
            ["detector", "tracker"],
            ["tracker", "filter"],
            ["filter", "counter"],
        ],
    }

    # Tracking stream can reach counter through the bypassed filter
    tracked_sample = [{"trackId": 1, "class": "person", "score": 0.9}]
    res = engine.results_for_node(workflow, "counter", detections=[], tracked=tracked_sample)
    assert len(res) == 1
    assert res[0]["trackId"] == 1


def test_workflow_runner_record_node_telemetry():
    """Verify recording and querying node telemetry."""
    runner = core.WorkflowRunner()

    # Record success telemetry
    runner.record_node_telemetry(
        "detector_1",
        status="success",
        latency_ms=14.8,
        item_count=5,
        last_input={"batchSize": 1, "shape": [640, 640, 3]},
        last_output={"detections": 5, "classes": ["person", "car"]},
    )

    # Record bypassed telemetry
    runner.record_node_telemetry(
        "filter_1",
        status="bypassed",
        latency_ms=0.0,
        item_count=5,
        last_input={"candidates": 5},
        last_output={"bypassed": True},
    )

    # Record error telemetry
    runner.record_node_telemetry(
        "webhook_1",
        status="error",
        latency_ms=50.2,
        item_count=0,
        error="Connection refused: 127.0.0.1:9099",
    )

    status = runner.status()
    assert "nodeTelemetry" in status
    telemetry = status["nodeTelemetry"]

    assert "detector_1" in telemetry
    assert telemetry["detector_1"]["status"] == "success"
    assert telemetry["detector_1"]["latencyMs"] == 14.8
    assert telemetry["detector_1"]["itemCount"] == 5
    assert telemetry["detector_1"]["lastOutput"]["detections"] == 5

    assert "filter_1" in telemetry
    assert telemetry["filter_1"]["status"] == "bypassed"
    assert telemetry["filter_1"]["latencyMs"] == 0.0

    assert "webhook_1" in telemetry
    assert telemetry["webhook_1"]["status"] == "error"
    assert "Connection refused" in telemetry["webhook_1"]["error"]
