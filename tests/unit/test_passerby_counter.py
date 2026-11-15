import numpy as np
from engine.core import _check_line_crossing, _process_line_counters


def test_crossing_and_unique_passerby():
    assert _check_line_crossing((20, 50), (80, 50), (10, 40), (10, 60)) is None
    node = {"id": "p", "type": "passerby_counter", "config": {"classes": "person", "triggerAnchor": "center", "hysteresisDistance": 1, "lines": [{"id": "passing", "startPoint": "20,40", "endPoint": "80,40"}, {"id": "store", "startPoint": "20,70", "endPoint": "80,70"}]}}
    state = {}
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    def step(y, now):
        detections = [{"trackId": 1, "class": "person", "bbox": [45, y - 5, 10, 10]}]
        return _process_line_counters({"nodes": [node], "edges": []}, frame, detections, detections, state, now)
    assert not step(20, 1)
    assert len(step(50, 2)) == 1
    assert len(step(80, 3)) == 1
    assert state["p"]["passersby"] == state["p"]["visitors"] == 1
    assert len(step(20, 4)) == 1  # passing line: return after its cooldown
    assert len(step(80, 5)) == 0
    assert len(step(20, 6)) == 1  # store line: return after its cooldown
    assert state["p"]["passersby"] == state["p"]["visitors"] == 1


def test_slow_crossing_confirms_once_and_respects_segment_and_gaps():
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    node = {"id": "line", "type": "line_counter", "config": {"startPoint": "20,100", "endPoint": "180,100", "hysteresisDistance": 15}}
    workflow = {"nodes": [node], "edges": []}
    state = {}
    def step(track, x, y, now):
        det = [{"trackId": track, "class": "person", "bbox": [x-5, y-5, 10, 10]}]
        return _process_line_counters(workflow, frame, det, det, state, now)
    assert not step(1, 80, 94, 1.0)
    assert not step(1, 80, 98, 1.1)
    assert not step(1, 80, 102, 1.2)
    assert not step(1, 80, 106, 1.3)
    assert len(step(1, 80, 114, 1.4)) == 1
    assert not step(1, 80, 80, 1.5)
    assert len(step(1, 80, 80, 3.0)) == 1
    assert not step(1, 80, 120, 4.6)
    assert not step(2, 10, 90, 2.0)
    assert not step(2, 10, 110, 2.1)
    assert not step(3, 80, 98, 3.0)
    assert not step(3, 80, 102, 3.1)
    assert not step(3, 80, 120, 7.0)
    assert state["line"]["total_in"] == state["line"]["total_out"] == 1


def test_custom_anchor_and_both_directions():
    from engine.core import _get_anchor_point, _draw_roboflow_workflow_overlays
    det = {"trackId": 9, "class": "person", "bbox": [40, 50, 40, 80]}
    assert _get_anchor_point(det, "custom", {"anchorXPercent": 25, "anchorYPercent": 75}) == (50, 110)
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    node = {"id": "lc", "type": "line_counter", "config": {"startPoint": "80,20", "endPoint": "80,180", "triggerAnchor": "custom", "anchorXPercent": 25, "anchorYPercent": 75, "showAnchor": True, "hysteresisDistance": 1, "reArmCooldown": 0}}
    workflow = {"nodes": [node], "edges": []}
    state = {}
    def step(x, now):
        item = {"trackId": 9, "class": "person", "bbox": [x, 50, 40, 80]}
        return _process_line_counters(workflow, frame, [item], [item], state, now)
    import time
    now = time.monotonic()
    assert not step(40, now)
    _draw_roboflow_workflow_overlays(frame, workflow, state)
    assert frame[110, 50].any()
    assert len(step(80, now + 0.1)) == 1
    assert len(step(40, now + 0.2)) == 1
    assert not step(80, now + 0.3)
    assert state["lc"]["total_in"] == state["lc"]["total_out"] == 1
