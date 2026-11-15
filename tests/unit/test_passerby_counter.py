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
    assert not step(20, 4)
    assert state["p"]["passersby"] == state["p"]["visitors"] == 1
