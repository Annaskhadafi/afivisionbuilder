"""Deterministic frame sampler regression checks.

Run from the repository root with ``python webapp/test_frame_sampler.py``.
"""
from __future__ import annotations
from pathlib import Path

import os
import sys
import tempfile
import time
from unittest.mock import patch

# Keep the standalone runner test bounded on developer machines that already
# have BLAS/OpenMP settings in their environment.
for _name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import cv2
import numpy as np

_TEST_DATA = tempfile.TemporaryDirectory(prefix="visonode-sampler-tests-")
os.environ.setdefault("VISONODE_APP_DATA_DIR", _TEST_DATA.name)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, os.path.join(str(Path(__file__).resolve().parents[2]), "engine"))

from engine import core, main, node_catalog, workflow_store  # noqa: E402


def _workflow(nodes, edges):
    return {"nodes": nodes, "edges": edges}


def _node(node_id, node_type, **config):
    return {"id": node_id, "type": node_type, "config": config}


def test_sampler_timing_and_stats() -> None:
    workflow = _workflow(
        [_node("input", "input"), _node("sam", "frame_sampler", targetFps=10), _node("preview", "preview")],
        [["input", "sam"], ["sam", "preview"]],
    )
    runtime = {}
    views = [core.sample_frame_workflow(workflow, runtime, t) for t in (0, .03, .06, .1)]
    assert [view["nodes"][-1].get("enabled", True) for view in views] == [True, False, False, True]
    assert runtime["sam"]["inputFrames"] == 4 and runtime["sam"]["outputFrames"] == 2
    stats = core.frame_sampler_stats(runtime, .2)["sam"]
    assert stats == {"inputFps": 15.0, "outputFps": 5.0, "inputFrames": 4, "outputFrames": 2, "droppedFrames": 2}
    # A large gap admits one frame only; it must not replay a burst.
    assert core.sample_frame_workflow(workflow, runtime, 10)["nodes"][-1].get("enabled", True)
    assert runtime["sam"]["outputFrames"] == 3

    unlimited = _workflow(
        [_node("input", "input"), _node("sam", "frame_sampler", targetFps=0), _node("preview", "preview")],
        [["input", "sam"], ["sam", "preview"]],
    )
    rt = {}
    for t in (0, .001, 99):
        assert core.sample_frame_workflow(unlimited, rt, t)["nodes"][-1].get("enabled", True)
    assert rt["sam"]["inputFrames"] == rt["sam"]["outputFrames"] == 3


def test_sampler_graph_pruning_nested_and_bypass() -> None:
    workflow = _workflow(
        [
            _node("input", "input"), _node("sam1", "frame_sampler", targetFps=10),
            _node("sam2", "frame_sampler", targetFps=10), _node("det", "detector"),
            _node("join", "preview"), _node("raw", "preview"), _node("dead", "resize"),
        ],
        [["input", "sam1"], ["sam1", "sam2"], ["sam2", "det"], ["det", "join"],
         ["input", "raw"]],
    )
    runtime = {}
    first = core.sample_frame_workflow(workflow, runtime, 0)
    second = core.sample_frame_workflow(workflow, runtime, .01)
    assert {node["id"] for node in main.active_inference_nodes(first)} == {"det"}
    assert main.has_active_path(second, "input", "raw")
    assert not main.has_active_path(second, "input", "join")
    assert second["nodes"][-1]["enabled"] is False
    assert runtime["sam2"]["inputFrames"] == 1  # nested sampler is not evaluated after sam1 blocks

    alternate = _workflow(
        [_node("input", "input"), _node("sam", "frame_sampler", targetFps=10), _node("det", "detector"), _node("join", "preview")],
        [["input", "sam"], ["sam", "det"], ["det", "join"], ["input", "join"]],
    )
    rt = {}
    core.sample_frame_workflow(alternate, rt, 0)
    blocked = core.sample_frame_workflow(alternate, rt, .01)
    assert main.has_active_path(blocked, "input", "join")


def test_sampler_processors_follow_sampled_branch() -> None:
    workflow = _workflow(
        [_node("input", "input"), _node("sam", "frame_sampler", targetFps=2),
         _node("resize", "resize", width=7, height=5), _node("sampled", "preview"),
         _node("raw", "preview")],
        [["input", "sam"], ["sam", "resize"], ["resize", "sampled"], ["input", "raw"]],
    )
    rt = {}
    core.sample_frame_workflow(workflow, rt, 0)
    blocked = core.sample_frame_workflow(workflow, rt, 0.1)
    assert main.active_image_processing_nodes_for_path(blocked, "input", "sampled") == []
    assert main.active_image_processing_nodes_for_path(blocked, "input", "raw") == []
    passed = core.sample_frame_workflow(workflow, rt, 0.5)
    assert [n["id"] for n in main.active_image_processing_nodes_for_path(passed, "input", "sampled")] == ["resize"]


def test_disabled_sampler_passthrough_and_auto_preview_sink() -> None:
    disabled = _workflow(
        [_node("input", "input"), {**_node("sam", "frame_sampler", targetFps=1), "enabled": False}, _node("preview", "preview")],
        [["input", "sam"], ["sam", "preview"]],
    )
    runtime = {}
    for t in (0, .01, 1):
        view = core.sample_frame_workflow(disabled, runtime, t)
        assert main.has_active_path(view, "input", "preview")
    assert runtime == {}

    workflow = _workflow(
        [_node("input", "input"), _node("sam", "frame_sampler", targetFps=10), _node("leaf", "resize")],
        [["input", "sam"], ["sam", "leaf"]],
    )
    runtime = {}
    assert core.sample_frame_workflow(workflow, runtime, 0)["nodes"][-1].get("enabled", True)
    blocked = core.sample_frame_workflow(workflow, runtime, .01)
    assert blocked["nodes"][-1]["enabled"] is False

    auto = _workflow(
        [_node("input", "input"), _node("sam", "frame_sampler", targetFps=10), _node("auto_preview", "preview")],
        [["input", "sam"], ["sam", "auto_preview"]],
    )
    rt = {}
    first = core.sample_frame_workflow(auto, rt, 0)
    second = core.sample_frame_workflow(auto, rt, .01)
    assert ("sam", "auto_preview") in first["edges"]
    assert ("sam", "auto_preview") not in second["edges"]


def test_sampler_normalization_rejects_missing_and_invalid_values() -> None:
    for value in (None, "", True, -1, "nan", "inf", "abc"):
        workflow = _workflow([_node("input", "input"), _node("sam", "frame_sampler", targetFps=value)], [])
        try:
            main.normalize_workflow(workflow)
        except ValueError:
            continue
        raise AssertionError(f"normalize_workflow accepted invalid targetFps={value!r}")


def test_runner_sampled_resize_does_not_process_blocked_frames() -> None:
    class FakeSource:
        is_static = False
        fps = 20
        is_exhausted = False

        def __init__(self, _cv2, _config):
            self.frames = [np.full((24, 32, 3), value, np.uint8) for value in range(20)]
        def open(self):
            return "finite fake", 32, 24
        def read(self):
            if not self.frames:
                self.is_exhausted = True
                return False, None
            time.sleep(0.01)
            return True, self.frames.pop(0)
        def release(self):
            pass

    workflow = _workflow(
        [_node("input", "input", sourceType="video", filePath="unused", loop=False, dropFrames=False),
         _node("sam", "frame_sampler", targetFps=2), _node("resize", "resize", width=7, height=5),
         _node("sampled", "preview"), _node("raw", "preview")],
        [["input", "sam"], ["sam", "resize"], ["resize", "sampled"], ["input", "raw"]],
    )
    frames = []
    processing_calls = []
    original = core.engine.apply_image_processing

    def spy(frame, wf, runtime, **kwargs):
        processing_calls.append([node["id"] for node in kwargs.get("processing_nodes", [])])
        return original(frame, wf, runtime, **kwargs)

    runner = core.WorkflowRunner(on_frame=lambda node_id, frame, shown: frames.append((node_id, frame.shape)))
    with patch.object(core.engine, "OpenCVInputSource", FakeSource), patch.object(core.engine, "apply_image_processing", side_effect=spy):
        runner.start(workflow)
        runner._thread.join(10)
    status = runner.status()
    assert status["error"] is None, status
    sampled = [shape for node, shape in frames if node == "sampled"]
    raw = [shape for node, shape in frames if node == "raw"]
    assert 1 <= len(sampled) <= 4 and all(shape[:2] == (5, 7) for shape in sampled)
    assert len(raw) == 20 and all(shape[:2] == (24, 32) for shape in raw)
    assert sum("resize" in call for call in processing_calls) == len(sampled)


def test_running_update_keeps_mixed_sampler_batch_masks_per_frame() -> None:
    class FakeSource:
        is_static = False
        fps = 30
        is_exhausted = False

        def __init__(self, _cv2, _config):
            self.frames = [np.full((24, 32, 3), value, np.uint8) for value in range(60)]
        def open(self):
            return "finite fake", 32, 24
        def read(self):
            if not self.frames:
                self.is_exhausted = True
                return False, None
            time.sleep(0.003)
            return True, self.frames.pop(0)
        def release(self):
            pass

    initial = _workflow(
        [_node("input", "input", sourceType="video", filePath="unused", loop=False, dropFrames=False, frameQueueSize=64),
         _node("det", "detector", engine="rfdetr", batchSize=8), _node("tracker", "tracker", batchSize=4),
         _node("preview", "preview"), _node("raw", "preview")],
        [["input", "det"], ["det", "tracker"], ["tracker", "preview"], ["input", "raw"]],
    )
    updated = _workflow(
        [_node("input", "input", sourceType="video", filePath="unused", loop=False, dropFrames=False, frameQueueSize=64),
         _node("sam", "frame_sampler", targetFps=2), _node("det", "detector", engine="rfdetr", batchSize=8),
         _node("tracker", "tracker", batchSize=4), _node("preview", "preview"), _node("raw", "preview")],
        [["input", "sam"], ["sam", "det"], ["det", "tracker"], ["tracker", "preview"], ["input", "raw"]],
    )
    model_indices = []
    eligible_indices = []
    tracker_indices = []
    frames = []
    runner_ref = []
    sample_call_index = [0]
    original_sampler = core.sample_frame_workflow

    def sample_spy(workflow, runtime, now):
        frame_index = sample_call_index[0]
        sample_call_index[0] += 1
        view = original_sampler(workflow, runtime, now)
        if not any(node.get("id") == "sam" for node in workflow.get("nodes", [])):
            eligible_indices.append(frame_index)
        else:
            active = {node.get("id") for node in main.active_inference_nodes(view)}
            if "det" in active:
                eligible_indices.append(frame_index)
        return view

    class FakeModel:
        pass

    class FakeTracker:
        def __init__(self, node):
            pass
        def status_label(self):
            return "fake"
        def update(self, detections, frame=None, **kwargs):
            tracker_indices.append(int(frame[0, 0, 0]))
            return detections

    def fake_batch(batch, node):
        model_indices.extend(int(frame[0, 0, 0]) for frame in batch)
        if not runner_ref[0]._active_workflow.get("nodes")[1].get("type") == "frame_sampler":
            runner_ref[0].update_workflow(updated)
        return [[{"class": "object", "score": 0.9, "x": 3, "y": 3, "width": 5, "height": 5}] for _ in batch]

    runner = core.WorkflowRunner(on_frame=lambda node_id, frame, shown: frames.append((node_id, frame.shape)))
    runner_ref.append(runner)
    with patch.object(core.engine, "OpenCVInputSource", FakeSource), patch.object(core.engine, "load_rfdetr_model", return_value=FakeModel()), patch.object(core.engine, "run_rfdetr_batch", side_effect=fake_batch), patch.object(core.engine, "ObjectTracker", FakeTracker), patch.object(core, "sample_frame_workflow", side_effect=sample_spy):
        runner.start(initial)
        runner._thread.join(12)
    status = runner.status()
    assert status["error"] is None, status
    assert model_indices == eligible_indices, (model_indices, eligible_indices)
    assert tracker_indices == model_indices
    assert len([node for node, _ in frames if node == "raw"]) == 60
    assert len([node for node, _ in frames if node == "preview"]) == len(model_indices)


def test_catalog_and_store_defaults() -> None:
    assert "frame_sampler" in node_catalog.NODE_BLUEPRINTS
    assert node_catalog.NODE_BLUEPRINTS["frame_sampler"]["config"]["targetFps"] == 10
    node = workflow_store.make_node("frame_sampler", id="sam")
    assert node["config"]["targetFps"] == 10


def test_server_rejects_invalid_sampler_fps_and_persists_valid_config() -> None:
    with tempfile.TemporaryDirectory(prefix="visonode-sampler-") as data_dir:
        os.environ["VISONODE_APP_DATA_DIR"] = data_dir
        import server
        from fastapi.testclient import TestClient

        base = {"nodes": [_node("input", "input"), _node("sam", "frame_sampler", targetFps=2), _node("preview", "preview")], "edges": [["input", "sam"], ["sam", "preview"]]}
        with TestClient(server.app, base_url="http://127.0.0.1:8765") as client:
            for value in (-1, "nan", "inf", True, "abc"):
                bad = {**base, "nodes": [base["nodes"][0], {**base["nodes"][1], "config": {"targetFps": value}}, base["nodes"][2]]}
                assert client.post("/api/projects", json={"workflow": bad}).status_code == 400
            created = client.post("/api/projects", json={"workflow": base})
            assert created.status_code == 200, created.text
            project_id = created.json()["project"]["id"]
            loaded = client.get(f"/api/projects/{project_id}").json()["workflow"]
            assert loaded["nodes"][1]["config"]["targetFps"] == 2
            catalog = client.get("/api/catalog").json()
            assert catalog["catalog"]["frame_sampler"]["config"]["targetFps"] == 10
        os.environ["VISONODE_APP_DATA_DIR"] = _TEST_DATA.name


def test_runner_finite_video_routes_raw_and_sampled_work() -> None:
    class FakeSource:
        is_static = False
        fps = 20
        is_exhausted = False

        def __init__(self, _cv2, _config):
            self.frames = [np.full((24, 32, 3), value, np.uint8) for value in range(20)]

        def open(self):
            return "finite fake", 32, 24

        def read(self):
            if not self.frames:
                self.is_exhausted = True
                return False, None
            time.sleep(0.01)
            return True, self.frames.pop(0)

        def close(self):
            pass

        release = close

    workflow = _workflow(
        [_node("input", "input", sourceType="video", filePath="unused", loop=False, dropFrames=False, frameQueueSize=64),
         _node("sam", "frame_sampler", targetFps=2), _node("det", "detector", engine="rfdetr"),
         _node("tracker", "tracker"), _node("sampled", "preview"), _node("raw", "preview")],
        [["input", "sam"], ["sam", "det"], ["det", "tracker"], ["tracker", "sampled"], ["input", "raw"]],
    )
    frames = []
    tracker_calls = []

    class FakeModel:
        pass

    class FakeTracker:
        def __init__(self, node):
            pass
        def status_label(self):
            return "fake"
        def update(self, detections, frame=None, **kwargs):
            tracker_calls.append(kwargs.get("frame_id"))
            return detections

    def fake_batch(batch, node):
        return [[{"class": "object", "score": 0.9, "x": 3, "y": 3, "width": 5, "height": 5}] for _ in batch]

    runner = core.WorkflowRunner(on_frame=lambda node_id, frame, shown: frames.append((node_id, frame.shape)), native_preview=False)
    with patch.object(core.engine, "OpenCVInputSource", FakeSource), patch.object(core.engine, "load_rfdetr_model", return_value=FakeModel()), patch.object(core.engine, "run_rfdetr_batch", side_effect=fake_batch), patch.object(core.engine, "ObjectTracker", FakeTracker):
        runner.start(workflow)
        runner._thread.join(10)
    status = runner.status()
    assert status["error"] is None, status
    assert len([node for node, _ in frames if node == "raw"]) == 20
    assert 1 <= len([node for node, _ in frames if node == "sampled"]) <= 4
    assert len(tracker_calls) == len([node for node, _ in frames if node == "sampled"])
    sampler = status["frameSamplers"]["sam"]
    assert sampler["inputFrames"] == 20 and sampler["outputFrames"] == len(tracker_calls)
    assert sampler["droppedFrames"] == 20 - sampler["outputFrames"]


def test_preview_incidents_use_only_current_active_branches() -> None:
    class FakeSource:
        is_static = False
        fps = 20
        is_exhausted = False

        def __init__(self, _cv2, _config):
            self.remaining = 8
        def open(self):
            return "finite fake", 32, 24
        def read(self):
            if not self.remaining:
                self.is_exhausted = True
                return False, None
            self.remaining -= 1
            return True, np.zeros((24, 32, 3), np.uint8)
        def release(self):
            pass

    workflow = _workflow(
        [_node("input", "input", sourceType="video", filePath="unused", loop=False, dropFrames=False),
         _node("sam", "frame_sampler", targetFps=2),
         _node("first", "preview"), _node("last", "preview")],
        [["input", "sam"], ["sam", "first"], ["sam", "last"]],
    )
    original_sampler = core.sample_frame_workflow
    times = iter((.01, .02, .03, .04, .05, .5, .51, 1.0))

    def sampled(wf, runtime, now):
        if not runtime:
            original_sampler(wf, runtime, 0)
        view = original_sampler(wf, runtime, next(times))
        view["testFrame"] = runtime["sam"]["inputFrames"] - 1
        return view

    def detections(wf, target, *_args):
        return [{"class": "person", "score": .9, "x": 1, "y": 1,
                 "width": 5, "height": 5, "isLoitering": True,
                 "trackId": wf["testFrame"]}] if target == "first" else []

    runner = core.WorkflowRunner(native_preview=False)
    with patch.object(core.engine, "OpenCVInputSource", FakeSource), \
         patch.object(core, "sample_frame_workflow", side_effect=sampled), \
         patch.object(core.engine, "detections_for_node", side_effect=detections), \
         patch.object(runner, "_save_incident_clip_async") as save_clip:
        runner.start(workflow)
        runner._thread.join(10)
    assert not runner._thread.is_alive()
    assert runner.status()["error"] is None, runner.status()
    assert [call.args[2] for call in save_clip.call_args_list] == [
        "track #6 person", "track #8 person",
    ]


def main_test() -> None:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    try:
        for test in tests:
            test()
            print(f"PASS {test.__name__}")
    finally:
        _TEST_DATA.cleanup()


if __name__ == "__main__":
    main_test()
