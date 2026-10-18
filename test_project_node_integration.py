from __future__ import annotations

import os
import sys
import tempfile
import time as wallclock
from threading import Event
from pathlib import Path
from unittest.mock import patch

import numpy as np
import cv2


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "engine"))

import core  # noqa: E402
import main as engine  # noqa: E402


FRAME = np.zeros((100, 100, 3), dtype=np.uint8)


def _det(cls: str, box=(20, 20, 10, 20), source="det"):
    return {"kind": "detection", "class": cls, "bbox": list(box), "score": 0.9, "sourceNodeId": source}


def _track(cls: str, track_id: str, box=(20, 20, 10, 20)):
    return {"kind": "detection", "class": cls, "bbox": list(box), "score": 0.9,
            "sourceNodeId": "tracker", "trackId": track_id}


def _node(node_id: str, node_type: str, **config):
    defaults = {"points": "0,0;1,0;1,1;0,1", "showOverlay": False}
    defaults.update(config)
    return {"id": node_id, "type": node_type, "config": defaults}


def _wf(nodes, edges):
    return {"nodes": nodes, "edges": [list(edge) for edge in edges]}


def test_shared_track_event_path_and_sparse_outputs():
    timer = _node("timer", "zone_activity_timer", confirmationSeconds=0)
    exit_node = _node("exit", "zone_exit_event", absenceGraceSeconds=0)
    alert = {"id": "alert", "type": "alert", "config": {}}
    webhook = {"id": "webhook", "type": "webhook_output", "config": {}}
    image = {"id": "image", "type": "image_output", "config": {}}
    database = {"id": "database", "type": "database_output", "config": {}}
    preview = {"id": "preview", "type": "preview", "config": {}}
    nodes = [
        {"id": "input", "type": "input", "config": {}},
        {"id": "det", "type": "detector", "config": {}},
        {"id": "tracker", "type": "tracker", "config": {}},
        timer, exit_node, alert, webhook, image, database, preview,
    ]
    edges = [
        ("input", "det"), ("det", "tracker"),
        ("tracker", "timer"), ("tracker", "exit"),
        ("timer", "alert"), ("timer", "webhook"),
        ("exit", "image"), ("exit", "database"),
        ("tracker", "preview"),
    ]
    workflow = _wf(nodes, edges)
    tracked = [_track("tire", "t1", (20, 20, 10, 20)), _track("person", "p1", (50, 20, 10, 20))]
    detections = [_det("tire", (20, 20, 10, 20)), _det("person", (50, 20, 10, 20))]

    event_runtime = {}
    logic_runtime = {}
    extra, _, _, _ = core._process_track_event_nodes(
        cv2, FRAME, workflow, detections.copy(), tracked, logic_runtime, event_runtime, 0.0,
    )
    assert any(item.get("kind") == "zone_activity" for item in extra)
    assert any(item.get("kind") == "zone_activity_event" for item in extra)
    assert all(item.get("sourceNodeId") in {"timer", "exit"} for item in extra)

    candidates = engine.results_for_node(workflow, "alert", extra, tracked)
    assert candidates and {item["kind"] for item in candidates} == {"zone_activity_event"}
    assert engine.results_for_node(workflow, "webhook", extra, tracked) == candidates
    assert engine.results_for_node(workflow, "image", extra, tracked) == []
    assert engine.results_for_node(workflow, "database", extra, tracked) == []

    preview_results = engine.results_for_node(workflow, "preview", detections, tracked)
    assert preview_results == tracked
    assert all(item["bbox"] for item in preview_results)

    mixed = tracked + extra + [{"kind": "zone_exit", "sourceNodeId": "exit"}]
    assert engine._object_detection_count(mixed) == len(tracked)

    disconnected = _wf(nodes, [
        ("input", "det"), ("det", "tracker"), ("tracker", "preview"),
    ])
    disabled = _wf([dict(node, enabled=False) if node["id"] == "timer" else node for node in nodes], edges)
    assert core._process_track_event_nodes(cv2, FRAME, disconnected, detections.copy(), tracked, {}, {}, 0.0)[0] == []
    assert core._process_track_event_nodes(cv2, FRAME, disabled, detections.copy(), tracked, {}, {}, 0.0)[0] == []


def test_status_projects_stale_timer_as_unknown_without_mutating_runtime():
    timer = _node("timer", "zone_activity_timer", confirmationSeconds=0, maxObservationGapSeconds=5)
    workflow = _wf([{"id": "input", "type": "input", "config": {}}, timer], [("input", "timer")])
    tracked = [_track("tire", "t1"), _track("person", "p1", (50, 20, 10, 20))]
    runtime = {}
    base = wallclock.monotonic()
    core._process_track_event_nodes(cv2, FRAME, workflow, [], tracked, {}, runtime, base)
    runner = core.WorkflowRunner(native_preview=False)
    runner._event_runtime = runtime
    runner._active_workflow = workflow
    before = runner.status()["projectNodes"]["timer"]
    assert before["state"] == "WORKING"
    assert before["unknownSeconds"] == 0

    # Simulate the writer advancing mutable state before publishing its next
    # snapshot. Status must continue to project the copied WORKING snapshot.
    original_session = runtime["timer"]["sessionId"]
    original_last_frame = runtime["timer"]["lastFrame"]
    original_completed = runtime["timer"]["completed"]
    runtime["timer"].update(sessionId="future", lastFrame=base + 100, completed=True)
    original_monotonic = core.time.monotonic
    try:
        core.time.monotonic = lambda: base + 6
        stale = runner.status()["projectNodes"]["timer"]
    finally:
        core.time.monotonic = original_monotonic
    assert stale["state"] == "UNKNOWN"
    assert stale["unknownSeconds"] == 6
    assert stale["sessionId"] == before["sessionId"]
    assert runtime["timer"]["snapshot"]["state"] == "WORKING"
    assert runtime["timer"]["unknownSeconds"] == 0

    runtime["timer"].update(sessionId=original_session, lastFrame=original_last_frame, completed=original_completed)

    events, _, _, _ = core._process_track_event_nodes(
        cv2, FRAME, workflow, [], tracked, {}, runtime, base + 6.5,
    )
    assert runtime["timer"]["unknownSeconds"] == 6.5
    assert runtime["timer"]["snapshot"]["state"] == "UNKNOWN"
    assert any(event.get("kind") == "zone_activity_event" and event.get("state") == "UNKNOWN" for event in events)


def test_project_node_class_gate_is_applied_per_branch():
    timer = _node("timer", "zone_activity_timer", confirmationSeconds=0, requiredClasses="tire", triggerClasses="person")
    gate = {"id": "gate", "type": "class_detected_condition", "config": {"classes": "person", "match": "all"}}
    nodes = [
        {"id": "input", "type": "input", "config": {}},
        {"id": "det", "type": "detector", "config": {}},
        {"id": "tracker", "type": "tracker", "config": {}},
        timer, gate,
    ]
    workflow = _wf(nodes, [("input", "det"), ("det", "tracker"), ("tracker", "gate"), ("gate", "timer")])
    only_tire = [_track("tire", "t1")]
    result = core._process_track_event_nodes(cv2, FRAME, workflow, [], only_tire, {}, {}, 0.0)[0]
    assert result and all(item.get("state") == "EMPTY" and item.get("sessionId") is None for item in result)


def test_project_delivery_ledger_dispatches_sparse_events_once(tmp_path):
    exit_node = _node("exit", "zone_exit_event")
    image = {"id": "image", "type": "image_output", "config": {
        "outputDirectory": str(tmp_path), "format": "png", "burnWatermark": False,
    }}
    webhook = {"id": "webhook", "type": "webhook_output", "config": {"url": "http://local.test"}}
    database = {"id": "database", "type": "database_output", "config": {"saveEvents": True}}
    alert = {"id": "alert", "type": "alert", "config": {"message": "zone"}}
    workflow = _wf(
        [{"id": "input", "type": "input", "config": {}}, exit_node, image, webhook, database, alert],
        [("input", "exit"), ("exit", "image"), ("exit", "webhook"), ("exit", "database"), ("exit", "alert")],
    )
    events = [
        {"kind": "zone_exit", "sourceNodeId": "exit", "trackId": "a", "class": "truck", "score": 0.9, "bbox": [1, 1, 5, 5]},
        {"kind": "zone_exit", "sourceNodeId": "exit", "trackId": "b", "class": "truck", "score": 0.8, "bbox": [10, 10, 5, 5]},
    ]

    webhook_calls = []
    original_dispatch = core._dispatch_webhook_async
    core._dispatch_webhook_async = lambda config, candidates, frame=None: webhook_calls.append((config, candidates, frame))

    class Writer:
        def __init__(self):
            self.events = []

        def event(self, **payload):
            self.events.append(payload)

    writer = Writer()
    alerts = []
    try:
        runner = core.WorkflowRunner(on_event=lambda title, detail: alerts.append((title, detail)), native_preview=False)
        runner._database_outputs = [(database, writer)]
        runner._deliver_project_events(cv2, workflow, FRAME, events, {}, 1.0)
        runner._deliver_project_events(cv2, workflow, [], {}, {}, 2.0)
        # Serial-style delivery uses the same helper and must retain one dispatch per event batch.
        runner2 = core.WorkflowRunner(native_preview=False)
        runner2._database_outputs = [(database, writer)]
        runner2._deliver_project_events(cv2, workflow, FRAME, [events[0]], {}, 3.0)
    finally:
        core._dispatch_webhook_async = original_dispatch

    assert len(webhook_calls) == 2
    assert [len(call[1]) for call in webhook_calls] == [2, 1]
    assert all(call[2] is not None and np.array_equal(call[2], FRAME) for call in webhook_calls)
    assert len(writer.events) == 3 and all(item["title"] == "zone_exit" for item in writer.events)
    assert len(alerts) == 1 and all(title == "zone" for title, _ in alerts)

    snapshots = list(tmp_path.glob("*.png"))
    assert len(snapshots) == 3
    saved = cv2.imread(str(snapshots[0]), cv2.IMREAD_COLOR)
    assert saved is not None and saved.shape == FRAME.shape and np.array_equal(saved, FRAME)


def test_project_filter_regressions_and_template_contract():
    timer = _node("timer", "zone_activity_timer", requiredClasses="person", triggerClasses="person", confirmationSeconds=0)
    workflow = _wf(
        [{"id": "input", "type": "input", "config": {}}, {"id": "tracker", "type": "tracker", "config": {}}, timer],
        [("input", "tracker"), ("tracker", "timer")],
    )
    result = core._process_track_event_nodes(cv2, FRAME, workflow, [], [_track("tire", "t1")], {}, {}, 0.0)[0]
    assert result and result[0]["requiredCount"] == 0 and result[0]["sessionId"] is None

    exit_node = _node("exit", "zone_exit_event", classes="person")
    workflow = _wf(
        [{"id": "input", "type": "input", "config": {}}, {"id": "tracker", "type": "tracker", "config": {}}, exit_node],
        [("input", "tracker"), ("tracker", "exit")],
    )
    assert core._process_track_event_nodes(cv2, FRAME, workflow, [], [_track("truck", "t1")], {}, {}, 0.0)[0] == []

    with tempfile.TemporaryDirectory() as data_dir:
        os.environ["VISONODE_APP_DATA_DIR"] = data_dir
        sys.modules.pop("server", None)
        import server
        from fastapi.testclient import TestClient

        with TestClient(server.app, base_url="http://127.0.0.1:8765") as client:
            templates = client.get("/api/templates")
            assert templates.status_code == 200
            custom = {item["id"]: item for item in templates.json()["templates"] if item["id"].startswith("custom-")}
            assert {"custom-workshop-zone", "custom-warehouse-exit"} <= custom.keys()
            for item in custom.values():
                detector = next(node for node in item["workflow"]["nodes"] if node["type"] == "detector")
                assert {"modelPath", "customModelPath"} <= detector["config"].keys()
                assert detector["config"]["modelPath"] == ""

            invalid = [
                _node("timer", "zone_activity_timer", countFromStart="yes"),
                _node("timer", "zone_activity_timer", confirmationSeconds=True),
                _node("timer", "zone_activity_timer", maxSessionDurationSeconds=-1),
                _node("timer", "zone_activity_timer", points="0,0;1,0;2,0"),
            ]
            for node in invalid:
                assert client.post("/api/projects", json={"workflow": {"nodes": [node], "edges": []}}).status_code == 400


def test_same_source_filter_bypass_emits_once():
    exit_node = _node("exit", "zone_exit_event")
    person_filter = {"id": "filter", "type": "filter", "config": {"classes": "person"}}
    alert = {"id": "alert", "type": "alert", "config": {"message": "event"}}
    workflow = _wf(
        [{"id": "input", "type": "input", "config": {}}, exit_node, person_filter, alert],
        [("input", "exit"), ("exit", "filter"), ("filter", "alert"), ("exit", "alert")],
    )
    event = {"kind": "zone_exit", "sourceNodeId": "exit", "trackId": "truck-1", "class": "truck", "score": 0.9, "bbox": [1, 1, 5, 5]}
    alerts = []
    runner = core.WorkflowRunner(on_event=lambda title, detail: alerts.append((title, detail)), native_preview=False)
    runner._deliver_project_events(__import__("cv2"), workflow, FRAME, [event], {}, 1.0)
    assert len(alerts) == 1 and '"trackId": "truck-1"' in alerts[0][1]


def test_project_event_branches_preserve_direct_source_and_snapshot_payload(tmp_path):
    exit_a = _node("exit_a", "zone_exit_event")
    exit_b = _node("exit_b", "zone_exit_event")
    person_filter = {"id": "person_filter", "type": "filter", "config": {"classes": "person"}}
    alert = {"id": "alert", "type": "alert", "config": {"message": "event"}}
    database = {"id": "database", "type": "database_output", "config": {"saveEvents": True}}
    image = {"id": "image", "type": "image_output", "config": {
        "outputDirectory": str(tmp_path), "format": "png", "burnWatermark": False,
    }}
    workflow = _wf(
        [{"id": "input", "type": "input", "config": {}}, exit_a, exit_b,
         person_filter, alert, database, image],
        [("input", "exit_a"), ("input", "exit_b"),
         ("exit_a", "person_filter"), ("person_filter", "alert"),
         ("exit_b", "alert"), ("exit_b", "database"), ("exit_b", "image")],
    )
    events = [
        {"kind": "zone_exit", "sourceNodeId": "exit_a", "trackId": "a", "class": "truck", "score": 0.9, "bbox": [1, 1, 5, 5]},
        {"kind": "zone_exit", "sourceNodeId": "exit_b", "trackId": "b", "class": "truck", "score": 0.8, "bbox": [10, 10, 5, 5]},
    ]

    class Writer:
        def __init__(self):
            self.events = []

        def event(self, **payload):
            self.events.append(payload)

    writer = Writer()
    alerts = []
    runner = core.WorkflowRunner(on_event=lambda title, detail: alerts.append((title, detail)), native_preview=False)
    runner._database_outputs = [(database, writer)]
    runner._deliver_project_events(cv2, workflow, FRAME, events, {}, 1.0)

    assert len(alerts) == 1
    assert '"trackId": "b"' in alerts[0][1]
    assert '"trackId": "a"' not in alerts[0][1]
    assert len(writer.events) == 1
    payload = __import__("json").loads(writer.events[0]["detail"])
    assert payload["trackId"] == "b"
    assert payload.get("snapshotPath")
    assert Path(payload["snapshotPath"]).exists()


def test_finite_runner_processes_project_event_without_model_or_duplicate_output():
    class FakeSource:
        is_static = False
        fps = 20
        is_exhausted = False

        def __init__(self, _cv2, _config):
            self.frames = [np.full((100, 100, 3), value, np.uint8) for value in range(8)]

        def open(self):
            return "finite synthetic", 100, 100

        def read(self):
            if not self.frames:
                self.is_exhausted = True
                return False, None
            return True, self.frames.pop(0)

        def close(self):
            pass

        release = close

    class FakeTracker:
        def __init__(self, _node):
            pass

        def status_label(self):
            return "fake"

        def update(self, detections, frame=None, **kwargs):
            return [{**item, "sourceNodeId": "tracker", "trackId": item["class"]} for item in detections]

    def fake_batch(batch, _node):
        return [[
            {"kind": "detection", "class": "tire", "score": 0.9, "bbox": [20, 20, 10, 20], "sourceNodeId": "det"},
            {"kind": "detection", "class": "person", "score": 0.9, "bbox": [50, 20, 10, 20], "sourceNodeId": "det"},
        ] for _ in batch]

    def fake_frame(_frame, _node):
        return fake_batch([_frame], _node)[0]

    timer = _node("timer", "zone_activity_timer", confirmationSeconds=0)
    alert = {"id": "alert", "type": "alert", "config": {"message": "zone"}}
    webhook = {"id": "webhook", "type": "webhook_output", "config": {"url": "http://local.test"}}
    workflow = _wf(
        [{"id": "input", "type": "input", "config": {"sourceType": "video", "filePath": "synthetic", "loop": False, "dropFrames": False}},
         {"id": "det", "type": "detector", "config": {"engine": "rfdetr"}},
         {"id": "tracker", "type": "tracker", "config": {}}, timer, alert, webhook,
         {"id": "preview", "type": "preview", "config": {}}],
        [("input", "det"), ("det", "tracker"), ("tracker", "timer"), ("timer", "alert"),
         ("timer", "webhook"), ("tracker", "preview")],
    )
    alerts = []
    webhooks = []
    frames = []
    dispatch = lambda config, candidates, frame=None: webhooks.append((config, candidates, frame))
    patches = [
        patch.object(core.engine, "OpenCVInputSource", FakeSource),
        patch.object(core.engine, "load_rfdetr_model", return_value=object()),
        patch.object(core.engine, "run_rfdetr_batch", side_effect=fake_batch),
        patch.object(core.engine, "run_rfdetr_frame", side_effect=fake_frame),
        patch.object(core.engine, "ObjectTracker", FakeTracker),
        patch.object(core, "_dispatch_webhook_async", side_effect=dispatch),
    ]
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        runner = core.WorkflowRunner(
            on_event=lambda title, detail: alerts.append((title, detail)),
            on_frame=lambda node_id, frame, shown: frames.append((node_id, frame.copy())),
            native_preview=False,
        )
        runner.start(workflow)
        runner._thread.join(10)
        assert not runner._thread.is_alive()
        assert runner.status()["error"] is None, runner.status()
        assert any(node_id == "preview" for node_id, _ in frames)
        assert any(node_id == "raw" for node_id, _ in frames) is False
        assert sum(title == "zone" for title, _ in alerts) == 1
        assert len(webhooks) == 1 and len(webhooks[0][1]) == 1
        assert all(item["kind"] == "zone_activity_event" for item in webhooks[0][1])

        serial_alerts = []
        serial = core.WorkflowRunner(on_event=lambda title, detail: serial_alerts.append((title, detail)), native_preview=False)
        serial._stop_event = Event()
        serial._python_context = {}
        serial._run_serial(workflow)
        assert serial.status()["error"] is None, serial.status()
        assert sum(title == "zone" for title, _ in serial_alerts) == 1
        assert len(webhooks) == 2 and len(webhooks[1][1]) == 1
        assert all(item["kind"] == "zone_activity_event" for item in webhooks[1][1])





def test_project_api_rejects_invalid_and_persists_valid_config():
    with tempfile.TemporaryDirectory() as data_dir:
        os.environ["VISONODE_APP_DATA_DIR"] = data_dir
        sys.modules.pop("server", None)
        import server
        from fastapi.testclient import TestClient

        bad = {"nodes": [_node("timer", "zone_activity_timer", points="0,0;1,0;2,0")], "edges": []}
        crossing = {"nodes": [_node("timer", "zone_activity_timer", points="0,0;1,1;0,1;1,0;0.8,0")], "edges": []}
        good = {"nodes": [_node("timer", "zone_activity_timer")], "edges": []}
        # core imports workflow_store before this test sets the temporary data dir.
        # Keep this API round-trip entirely inside the test directory.
        with (patch.object(server.store, "APP_DATA_DIR", Path(data_dir)),
              patch.object(server.store, "PROJECTS_DIR", Path(data_dir) / "projects"),
              patch.object(server.store, "PROJECT_INDEX_FILE", Path(data_dir) / "projects.json"),
              TestClient(server.app, base_url="http://127.0.0.1:8765") as client):
            assert client.post("/api/projects", json={"workflow": bad}).status_code == 400
            assert client.post("/api/projects", json={"workflow": crossing}).status_code == 400
            response = client.post("/api/projects", json={"name": "integration", "workflow": good})
            assert response.status_code == 200
            project_id = response.json()["project"]["id"]
            loaded = client.get(f"/api/projects/{project_id}")
            assert loaded.status_code == 200
            assert loaded.json()["workflow"]["nodes"][0]["config"]["points"] == good["nodes"][0]["config"]["points"]


def test_direct_runner_rejects_invalid_zone_before_stopping():
    runner = core.WorkflowRunner()
    bad = _wf(
        [{"id": "input", "type": "input", "config": {}},
         _node("timer", "zone_activity_timer", points="0,0;1,1;0,1;1,0;0.8,0")],
        [("input", "timer")],
    )
    with patch.object(runner, "stop") as stop:
        try:
            runner.start(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("direct runner accepted a self-intersecting zone")
        stop.assert_not_called()


def main():
    test_shared_track_event_path_and_sparse_outputs()
    test_project_node_class_gate_is_applied_per_branch()
    with tempfile.TemporaryDirectory() as snapshots:
        test_project_delivery_ledger_dispatches_sparse_events_once(Path(snapshots))
    test_project_filter_regressions_and_template_contract()
    test_same_source_filter_bypass_emits_once()
    with tempfile.TemporaryDirectory() as snapshots:
        test_project_event_branches_preserve_direct_source_and_snapshot_payload(Path(snapshots))
    test_finite_runner_processes_project_event_without_model_or_duplicate_output()
    test_project_api_rejects_invalid_and_persists_valid_config()
    test_direct_runner_rejects_invalid_zone_before_stopping()
    print("project node integration checks passed")


if __name__ == "__main__":
    main()
