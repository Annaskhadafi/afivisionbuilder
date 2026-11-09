from __future__ import annotations

import numpy as np
import supervision as sv

from engine.node_catalog import TRACKER_CONFIG_DEFAULTS, migrate_tracker_config
from engine.roboflow_tracker import RoboflowTracker
from engine.workflow_export import _determine_required_packages


class FakeReIDModel:
    def __init__(self):
        self.calls = 0

    def extract_embeddings(self, detections, frame, batch_size=16):
        self.calls += 1
        vector = [1.0, 0.0] if int(frame[0, 0, 0]) == 0 else [0.0, 1.0]
        return np.tile(vector, (len(detections), 1))


def _det(x: int, label: str = "tire") -> dict:
    return {"bbox": [x, 10, 20, 20], "score": 0.9, "class": label}


def _track_after_gap(*, x: int = 30, label: str = "tire", different_appearance: bool = False):
    tracker = RoboflowTracker({
        "algorithm": "bytetrack",
        "enableReid": True,
        "reidAppearanceThreshold": 0.75,
        "trackBuffer": 90,
        "minimumConsecutiveFrames": 1,
    })
    fake = FakeReIDModel()
    tracker._reid_model = fake
    blank = np.zeros((120, 600, 3), dtype=np.uint8)
    other = np.full_like(blank, 255) if different_appearance else blank

    first = tracker.update([_det(10)], blank, frame_id=1, timestamp=1 / 30)[0]
    tracker.update([], blank, frame_id=2, timestamp=2 / 30)
    tracker.update([_det(x, label)], other, frame_id=3, timestamp=3 / 30)
    final = tracker.update([_det(x + 1, label)], other, frame_id=4, timestamp=4 / 30)[0]
    return first, final, fake.calls


def test_reid_reuses_id_after_gap_for_same_class_and_appearance():
    first, final, calls = _track_after_gap()

    assert first["trackId"] == final["trackId"]
    # Smart ReID only runs on new tracks (frame 1) and reappearance after gap (frame 3).
    # Continuous active track (frame 4) skips redundant inference to eliminate stream latency.
    assert calls == 2


def test_reid_rejects_different_appearance_class_and_spatial_match():
    first, different_appearance, _ = _track_after_gap(different_appearance=True)
    assert first["trackId"] != different_appearance["trackId"]

    first, different_class, _ = _track_after_gap(label="truck")
    assert first["trackId"] != different_class["trackId"]

    first, far_away, _ = _track_after_gap(x=500)
    assert first["trackId"] != far_away["trackId"]


def test_reid_disabled_preserves_tracker_path_and_export_dependency_is_conditional():
    tracker = RoboflowTracker({"algorithm": "bytetrack"})
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    first = tracker.update([_det(10)], frame, frame_id=1, timestamp=1 / 30)[0]
    second = tracker.update([_det(11)], frame, frame_id=2, timestamp=2 / 30)[0]
    assert tracker._reid_model is None
    assert first["trackId"] == second["trackId"]

    base = _determine_required_packages({"nodes": [{"type": "tracker", "config": {}}]})
    reid = _determine_required_packages({"nodes": [{"type": "tracker", "config": {"enableReid": True}}]})
    assert "reid" not in base
    assert {"reid", "torch", "torchvision"} <= reid


def test_tracker_config_keeps_and_bounds_reid_options():
    config = dict(TRACKER_CONFIG_DEFAULTS)
    config.update({"enableReid": True, "reidAppearanceThreshold": 1.5, "reidDevice": "invalid"})
    migrate_tracker_config(config)

    assert config["enableReid"] is True
    assert config["reidAppearanceThreshold"] == 0.75
    assert config["reidDevice"] == "cpu"
    assert config["reidModel"] == "osnet_x1_0_msmt17_combineall"


def test_existing_track_id_is_reserved_before_reid_for_new_track():
    for tracker_ids, source_indices in (([2, 1], [0, 1]), ([1, 2], [1, 0])):
        tracker = RoboflowTracker({"enableReid": True, "reidMaxCenterDistance": 8})
        tracker._reid_model = FakeReIDModel()
        scope = "__all__"
        tracker._global_ids[(scope, 1)] = 1
        tracker._next_global_id = 2
        tracker._reid_gallery[1] = {
            "scope": scope, "class": "tire", "embedding": np.array([1.0, 0.0]),
            "box": [10.0, 10.0, 30.0, 30.0], "timestamp": 1 / 30, "frame_id": 1,
        }

        class Runtime:
            tracks = []

            def update(self, _detections, frame=None):
                boxes = [[11, 10, 31, 30] if source == 0 else [10, 10, 30, 30] for source in source_indices]
                return sv.Detections(
                    xyxy=np.array(boxes, dtype=np.float32),
                    confidence=np.array([0.9, 0.9], dtype=np.float32),
                    tracker_id=np.array(tracker_ids),
                    data={"visonode_source_index": np.array(source_indices)},
                )

        tracker._runtimes[scope] = Runtime()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        outputs = tracker.update([_det(11), _det(10)], frame, frame_id=2, timestamp=2 / 30)

        assert outputs[0]["trackId"] != outputs[1]["trackId"]
        assert outputs[1]["trackId"] == 1


def test_reid_gallery_clears_on_source_reset_and_uses_tracker_buffer_units():
    tracker = RoboflowTracker({"algorithm": "bytetrack", "enableReid": True})
    tracker._reid_model = FakeReIDModel()
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    first = tracker.update([_det(10)], frame, frame_id=1, timestamp=1.0)[0]
    restarted = tracker.update([_det(10)], frame, frame_id=1, timestamp=1.1)[0]
    assert restarted["trackId"] != first["trackId"]
    assert len(tracker._reid_gallery) == 1

    ocsort = RoboflowTracker({
        "algorithm": "ocsort", "enableReid": True, "ocSortMaxAge": 6,
        "trackerFrameRate": 60,
    })
    entry = next(iter(tracker._reid_gallery.values()))
    assert ocsort._reid_entry_is_fresh(entry, 1.29, 2)
    assert not ocsort._reid_entry_is_fresh(entry, 1.31, 2)

def test_reid_safe_fallback_when_frame_is_none_or_corrupt():
    # Tracker must not raise ValueError or crash when frame is None or corrupt
    tracker = RoboflowTracker({"algorithm": "bytetrack", "enableReid": True})
    tracker._reid_model = FakeReIDModel()
    
    # None frame
    res_none = tracker.update([_det(10)], frame=None, frame_id=1, timestamp=1 / 30)
    assert len(res_none) == 1
    assert "trackId" in res_none[0]
    
    # Empty 0-size frame
    res_empty = tracker.update([_det(11)], frame=np.empty((0, 0, 3), dtype=np.uint8), frame_id=2, timestamp=2 / 30)
    assert len(res_empty) == 1
    
    # Degenerate 0-width bbox
    degenerate_det = {"bbox": [10, 10, 1, 1], "score": 0.9, "class": "tire"}
    res_degen = tracker.update([degenerate_det], frame=np.zeros((100, 100, 3), dtype=np.uint8), frame_id=3, timestamp=3 / 30)
    assert len(res_degen) == 1


def test_reid_refresh_interval_controls_periodic_extraction():
    tracker = RoboflowTracker({
        "algorithm": "bytetrack",
        "enableReid": True,
        "reidRefreshInterval": 3,
        "minimumConsecutiveFrames": 1,
    })
    fake = FakeReIDModel()
    tracker._reid_model = fake
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    # Frame 1: initial track -> call 1
    tracker.update([_det(10)], frame, frame_id=1, timestamp=1 / 30)
    assert fake.calls == 1

    # Frame 2: active track, delta=1 < 3 -> no new call
    tracker.update([_det(11)], frame, frame_id=2, timestamp=2 / 30)
    assert fake.calls == 1

    # Frame 3: active track, delta=2 < 3 -> no new call
    tracker.update([_det(12)], frame, frame_id=3, timestamp=3 / 30)
    assert fake.calls == 1

    # Frame 4: active track, delta=3 >= 3 -> refresh triggered -> call 2
    tracker.update([_det(13)], frame, frame_id=4, timestamp=4 / 30)
    assert fake.calls == 2
