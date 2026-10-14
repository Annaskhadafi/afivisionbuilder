"""Standalone integration checks for the custom Python script node.

Run sequentially with ``python webapp/test_python_script_integration.py``.
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from unittest.mock import patch

# Keep each spawned script worker small and keep imports pointed at this temp app.
for _name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"
_DATA = tempfile.TemporaryDirectory(prefix="visonode-python-script-")
os.environ["VISONODE_APP_DATA_DIR"] = _DATA.name

import cv2  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

from engine import core, main, node_catalog, workflow_store  # noqa: E402
from engine.python_script_runtime import (  # noqa: E402
    PythonScriptRunner,
    ScriptStopped,
    ScriptTimeout,
)


def _node(node_id, node_type, **config):
    return {"id": node_id, "type": node_type, "config": config}


def _workflow(nodes, edges):
    return {"nodes": nodes, "edges": edges}


def _frames(count=6):
    return [np.full((24, 32, 3), 10 + i, np.uint8) for i in range(count)]


def test_runner_contract_state_logs_and_source_isolation():
    code = """
def process(frame, state):
    state['count'] = state.get('count', 0) + 1
    print('count', state['count'])
    return 255 - frame
"""
    frame = np.full((24, 32, 3), 10, np.uint8)
    source = frame.copy()
    with PythonScriptRunner(code) as runner:
        results = [runner.run(frame) for _ in range(6)]
    assert all(result.frame.shape == frame.shape and result.frame.dtype == np.uint8 for result in results)
    assert results[-1].frame[0, 0, 0] == 245
    assert "count 6" in results[-1].logs
    np.testing.assert_array_equal(frame, source)


def test_runtime_timeout_stop_and_cleanup():
    runner = PythonScriptRunner("def process(frame, state):\n    while True: pass", timeout_ms=100)
    try:
        try:
            runner.run(np.zeros((2, 2, 3), np.uint8))
        except ScriptTimeout:
            pass
        else:
            raise AssertionError("infinite script did not time out")
    finally:
        runner.close()
    assert not runner._process.is_alive()

    stop = threading.Event()
    runner = PythonScriptRunner("def process(frame, state):\n    while True: pass", timeout_ms=60000, stop_event=stop)
    errors = []
    def invoke():
        try:
            runner.run(np.zeros((2, 2, 3), np.uint8))
        except ScriptStopped:
            return
        except BaseException as exc:  # pragma: no cover - diagnostic if contract regresses
            errors.append(exc)
    thread = threading.Thread(target=invoke)
    try:
        thread.start()
        time.sleep(0.1)
        stop.set()
        thread.join(2)
        assert not thread.is_alive(), "stop did not cancel a 60000ms wait"
        assert not errors, errors
    finally:
        runner.close()
    assert not runner._process.is_alive()


def test_validation_rejects_bad_configs_and_endpoint_does_not_execute_code():
    bad_values = (None, True, False, -1, 0, "bad", 1.5, 60001)
    for timeout in bad_values:
        workflow = _workflow([_node("input", "input"), _node("script", "python_script", code="def process(frame, state): return frame", timeoutMs=timeout)], [])
        try:
            main.normalize_workflow(workflow)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted timeoutMs={timeout!r}")
    for on_error in (None, "bad", True):
        workflow = _workflow([_node("input", "input"), _node("script", "python_script", code="def process(frame, state): return frame", onError=on_error)], [])
        try:
            main.normalize_workflow(workflow)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted onError={on_error!r}")
    for code in ("def process(frame, state) return frame", "print('missing')"):
        workflow = _workflow([_node("input", "input"), _node("script", "python_script", code=code)], [])
        try:
            main.normalize_workflow(workflow)
        except ValueError:
            pass
        else:
            raise AssertionError("accepted invalid script")

    import server
    from fastapi.testclient import TestClient
    sentinel = "raise RuntimeError('top-level must not execute')\ndef process(frame, state): return frame"
    with TestClient(server.app, base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/scripts/validate", json={"code": sentinel})
        assert response.status_code == 200, response.text
        assert response.json() == {"valid": True}
        assert client.post("/api/scripts/validate", json={"code": "def process(frame, state) return frame"}).status_code == 400


def test_catalog_defaults_and_saved_code_persists():
    assert "python_script" in node_catalog.NODE_BLUEPRINTS
    assert node_catalog.PYTHON_SCRIPT_DEFAULTS == {"code": node_catalog.PYTHON_SCRIPT_DEFAULTS["code"], "timeoutMs": 500, "onError": "stop"}
    node = workflow_store.make_node("python_script", id="script")
    assert node["config"]["timeoutMs"] == 500 and node["config"]["onError"] == "stop"
    import server
    from fastapi.testclient import TestClient
    code = "def process(frame, state): return frame"
    workflow = _workflow([_node("input", "input"), _node("script", "python_script", code=code), _node("preview", "preview")], [["input", "script"], ["script", "preview"]])
    with TestClient(server.app, base_url="http://127.0.0.1:8765") as client:
        created = client.post("/api/projects", json={"name": "script", "workflow": workflow})
        assert created.status_code == 200, created.text
        project_id = created.json()["project"]["id"]
        loaded = client.get(f"/api/projects/{project_id}").json()["workflow"]
        assert next(n for n in loaded["nodes"] if n["id"] == "script")["config"]["code"] == code


def test_sampler_gates_script_and_disabled_script_passthrough():
    workflow = _workflow([_node("input", "input"), _node("sam", "frame_sampler", targetFps=0.1), _node("script", "python_script", code="def process(frame, state): return 255-frame"), _node("preview", "preview")], [["input", "sam"], ["sam", "script"], ["script", "preview"]])
    runtime = {}
    first = core.sample_frame_workflow(workflow, runtime, 0)
    blocked = core.sample_frame_workflow(workflow, runtime, 0.01)
    assert main.active_image_processing_nodes_for_path(first, "input", "preview")[0]["id"] == "script"
    assert main.active_image_processing_nodes_for_path(blocked, "input", "preview") == []
    disabled = _workflow([_node("input", "input"), {**_node("script", "python_script", code="raise RuntimeError('must bypass')\ndef process(frame, state): return frame"), "enabled": False}, _node("preview", "preview")], [["input", "script"], ["script", "preview"]])
    assert main.active_image_processing_nodes_for_path(disabled, "input", "preview") == []


def test_runner_script_model_preview_reuses_script_result_once():
    class FakeSource:
        is_static = False
        fps = 20
        is_exhausted = False
        def __init__(self, _cv2, _config): self.frames = _frames()
        def open(self): return "fake", 32, 24
        def read(self):
            if not self.frames:
                self.is_exhausted = True
                return False, None
            return True, self.frames.pop(0)
        def close(self): pass
        release = close

    seen = []
    script = """
def process(frame, state):
    state['count'] = state.get('count', 0) + 1
    print('count', state['count'])
    return 255 - frame
"""
    workflow = _workflow([_node("input", "input", sourceType="video", filePath="unused", loop=False, dropFrames=False), _node("script", "python_script", code=script), _node("det", "detector", engine="rfdetr"), _node("preview", "preview"), _node("raw", "preview")], [["input", "script"], ["script", "det"], ["det", "preview"], ["input", "raw"]])
    def fake_batch(batch, node):
        seen.extend(int(frame[0, 0, 0]) for frame in batch)
        return [[] for _ in batch]
    frames = []
    runner = core.WorkflowRunner(on_frame=lambda node_id, frame, shown: frames.append((node_id, frame.copy())))
    with patch.object(core.engine, "OpenCVInputSource", FakeSource), patch.object(core.engine, "load_rfdetr_model", return_value=object()), patch.object(core.engine, "run_rfdetr_batch", side_effect=fake_batch):
        runner.start(workflow)
        runner._thread.join(10)
    status = runner.status()
    assert status["error"] is None, status
    assert seen == [245, 244, 243, 242, 241, 240]
    assert [int(frame[0, 0, 0]) for node, frame in frames if node == "raw"] == [10, 11, 12, 13, 14, 15]
    assert [int(frame[0, 0, 0]) for node, frame in frames if node == "preview"] == seen
    assert status["pythonScripts"]["script"]["processedFrames"] == 6
    assert "count 6" in status["pythonScripts"]["script"]["logs"]
    assert not runner._python_context["runners"]


def test_runner_script_error_stop_and_pass_status():
    class FakeSource:
        is_static = False; fps = 20; is_exhausted = False
        def __init__(self, _cv2, _config): self.frames = _frames(1)
        def open(self): return "fake", 32, 24
        def read(self):
            if not self.frames: self.is_exhausted = True; return False, None
            return True, self.frames.pop(0)
        def close(self): pass
        release = close
    base = [_node("input", "input", sourceType="video", filePath="unused", loop=False), _node("script", "python_script", code="def process(frame, state): raise ValueError('bad pixel')"), _node("preview", "preview")]
    workflow = _workflow(base, [["input", "script"], ["script", "preview"]])
    runner = core.WorkflowRunner()
    with patch.object(core.engine, "OpenCVInputSource", FakeSource):
        runner.start(workflow); runner._thread.join(5)
    assert runner.status()["state"] == "error"
    assert runner.status()["pythonScripts"]["script"]["state"] == "error"
    passed = _workflow([base[0], {**base[1], "config": {**base[1]["config"], "onError": "pass"}}, base[2]], workflow["edges"])
    frames = []
    runner = core.WorkflowRunner(on_frame=lambda node_id, frame, shown: frames.append((node_id, frame.copy())))
    with patch.object(core.engine, "OpenCVInputSource", FakeSource):
        runner.start(passed); runner._thread.join(5)
    assert runner.status()["error"] is None
    assert runner.status()["pythonScripts"]["script"]["errorCount"] >= 1
    assert frames and int(frames[-1][1][0, 0, 0]) == 10


def main_test() -> None:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    try:
        for test in tests:
            test()
            print(f"PASS {test.__name__}")
    finally:
        _DATA.cleanup()


if __name__ == "__main__":
    main_test()
