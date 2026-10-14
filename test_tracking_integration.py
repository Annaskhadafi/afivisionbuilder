"""Small tracking integration checks.

Run from this directory with ``python test_tracking_integration.py``.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from unittest.mock import patch

for _name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

from engine import core, main, node_catalog, workflow_store  # noqa: E402


def _node(node_id: str, node_type: str, **config: object) -> dict:
    return {"id": node_id, "type": node_type, "config": config}


def test_tracker_defaults_and_v2_migration() -> None:
    defaults = node_catalog.TRACKER_CONFIG_DEFAULTS
    assert main.TRACKER_CONFIG_DEFAULTS == defaults
    assert node_catalog.TRACKER_CONFIG_VERSION == 3
    assert {key: defaults[key] for key in (
        "trackHighThreshold", "newTrackThreshold", "trackBuffer", "minimumConsecutiveFrames"
    )} == {
        "trackHighThreshold": 0.45,
        "newTrackThreshold": 0.5,
        "trackBuffer": 90,
        "minimumConsecutiveFrames": 1,
    }

    legacy = _node(
        "tracker", "tracker", trackerConfigVersion=2,
        trackHighThreshold=0.6, newTrackThreshold=0.7,
        trackBuffer=30, minimumConsecutiveFrames=2,
    )
    workflow = {"nodes": [legacy], "edges": []}
    main.normalize_workflow(workflow)
    config = workflow["nodes"][0]["config"]
    assert {key: config[key] for key in (
        "trackerConfigVersion", "trackHighThreshold", "newTrackThreshold",
        "trackBuffer", "minimumConsecutiveFrames",
    )} == {
        "trackerConfigVersion": 3,
        "trackHighThreshold": 0.45,
        "newTrackThreshold": 0.5,
        "trackBuffer": 90,
        "minimumConsecutiveFrames": 1,
    }

    custom = _node(
        "tracker", "tracker", algorithm="cbiou", trackerConfigVersion=2,
        trackHighThreshold=0.62, newTrackThreshold=0.71,
        trackBuffer=17, minimumConsecutiveFrames=4,
    )
    saved = {"nodes": [custom], "edges": []}
    workflow_store.normalize_workflow(saved)
    custom_config = saved["nodes"][0]["config"]
    assert {key: custom_config[key] for key in (
        "trackHighThreshold", "newTrackThreshold", "trackBuffer", "minimumConsecutiveFrames"
    )} == {"trackHighThreshold": 0.62, "newTrackThreshold": 0.71, "trackBuffer": 17, "minimumConsecutiveFrames": 4}
    assert custom_config["algorithm"] == "cbiou"


def test_cbiou_native_mode_and_low_score_are_real_tracker_inputs() -> None:
    node = _node(
        "tracker", "tracker", algorithm="cbiou", trackHighThreshold=0.45,
        newTrackThreshold=0.5, trackBuffer=90, minimumConsecutiveFrames=1,
    )
    tracker = main.ObjectTracker(node)
    outputs = []
    for frame_id in range(1, 5):
        outputs.append(tracker.update(
            [{"class": "person", "score": 0.9 if frame_id == 1 else 0.2,
              "bbox": [10 + frame_id, 10, 20, 20]}],
            np.zeros((80, 100, 3), dtype=np.uint8),
            frame_id=frame_id,
            timestamp=frame_id / 30,
        ))
    assert outputs[0] and abs(outputs[0][0]["score"] - 0.9) < 1e-5
    assert all(batch and abs(batch[0]["score"] - 0.2) < 1e-5 for batch in outputs[1:])
    track_ids = [batch[0].get("trackId") for batch in outputs[1:]]
    assert len({track_id for track_id in track_ids if track_id is not None}) == 1, track_ids


def test_threaded_sampler_detector_real_tracker_tracks_only_sampled_packets() -> None:
    class FakeSource:
        is_static = False
        fps = 30
        is_exhausted = False

        def __init__(self, _cv2, _config):
            self.frames = [np.full((48, 64, 3), value, np.uint8) for value in range(40)]

        def open(self):
            return "finite fake", 64, 48

        def read(self):
            if not self.frames:
                self.is_exhausted = True
                return False, None
            time.sleep(0.001)
            return True, self.frames.pop(0)

        def release(self):
            pass

        close = release

    workflow = {
        "nodes": [
            _node("input", "input", sourceType="video", filePath="unused", loop=False, dropFrames=False, frameQueueSize=64),
            _node("sam", "frame_sampler", targetFps=2),
            _node("det", "detector", engine="rfdetr", batchSize=1),
            _node("tracker", "tracker", algorithm="cbiou", batchSize=1),
            _node("preview", "preview"),
        ],
        "edges": [["input", "sam"], ["sam", "det"], ["det", "tracker"], ["tracker", "preview"]],
    }
    sampled_times = iter(index / 30 for index in range(40))
    sampled_frame_ids: list[int] = []
    tracked_batches: list[list[dict]] = []
    original_sampler = core.sample_frame_workflow
    original_update = core.engine.ObjectTracker.update

    def deterministic_sampler(workflow_arg, runtime, _now):
        view = original_sampler(workflow_arg, runtime, next(sampled_times))
        if any(node.get("id") == "det" for node in main.active_inference_nodes(view)):
            sampled_frame_ids.append(runtime["sam"]["inputFrames"])
        return view

    def update_spy(self, detections, frame=None, **kwargs):
        tracked = original_update(self, detections, frame, **kwargs)
        tracked_batches.append(tracked)
        return tracked

    inference_calls = [0]

    def fake_batch(batch, _node):
        score = 0.9 if inference_calls[0] == 0 else 0.2
        inference_calls[0] += 1
        return [[{"class": "person", "score": score, "sourceNodeId": "det", "bbox": [12, 10, 20, 20],
                  "x": 12, "y": 10, "width": 20, "height": 20}] for _ in batch]

    runner = core.WorkflowRunner(native_preview=False)
    with patch.object(core.engine, "OpenCVInputSource", FakeSource), \
         patch.object(core.engine, "load_rfdetr_model", return_value=object()), \
         patch.object(core.engine, "run_rfdetr_batch", side_effect=fake_batch), \
         patch.object(core, "sample_frame_workflow", side_effect=deterministic_sampler), \
         patch.object(core.engine.ObjectTracker, "update", update_spy):
        runner.start(workflow)
        runner._thread.join(15)

    status = runner.status()
    assert status["error"] is None, status
    assert len(sampled_frame_ids) >= 3, sampled_frame_ids
    assert len(tracked_batches) == len(sampled_frame_ids), (runner.status(), len(tracked_batches), sampled_frame_ids)
    track_ids = [batch[0].get("trackId") for batch in tracked_batches if batch]
    assert len(track_ids) >= 3 and len(set(track_ids)) == 1, track_ids
    assert abs(tracked_batches[0][0]["score"] - 0.9) < 1e-5
    assert any(batch and abs(batch[0]["score"] - 0.2) < 1e-5 for batch in tracked_batches[1:])
    assert status["frameSamplers"]["sam"]["inputFrames"] == 40


def main_test() -> None:
    for name, test in globals().items():
        if name.startswith("test_") and callable(test):
            test()
            print(f"PASS {name}")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="visonode-tracking-tests-") as data_dir:
        os.environ["VISONODE_APP_DATA_DIR"] = data_dir
        main_test()
