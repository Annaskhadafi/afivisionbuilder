"""Contract checks for binding a running workflow to the selected project."""
from __future__ import annotations

import os
import tempfile

from fastapi.testclient import TestClient


class FakeRunner:
    instances: list["FakeRunner"] = []

    def __init__(self, **_: object) -> None:
        self.running = False
        self.updates: list[dict] = []
        self.started: dict | None = None
        FakeRunner.instances.append(self)

    def is_running(self) -> bool:
        return self.running

    def start(self, workflow: dict) -> None:
        self.started = workflow
        self.running = True

    def update_workflow(self, workflow: dict) -> None:
        self.updates.append(workflow)

    def stop(self) -> None:
        self.running = False

    def status(self) -> dict:
        return {"running": self.running, "state": "running" if self.running else "stopped", "error": None}

    @property
    def _thread(self) -> "FakeRunner":
        return self

    def is_alive(self) -> bool:
        return self.running


def workflow(marker: str) -> dict:
    return {
        "nodes": [
            {"id": "input", "type": "input", "config": {"marker": marker}},
            {"id": "preview", "type": "preview", "config": {}},
        ],
        "edges": [["input", "preview"]],
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="visonode-binding-") as data_dir:
        os.environ["VISONODE_APP_DATA_DIR"] = data_dir
        import server

        server.core.WorkflowRunner = FakeRunner
        server._runner = None
        server._runner_thread_ref = None
        FakeRunner.instances.clear()

        with TestClient(server.app, base_url="http://127.0.0.1:8765") as client:
            project_a = client.post("/api/projects", json={"name": "A", "workflow": workflow("a")})
            project_b = client.post("/api/projects", json={"name": "B", "workflow": workflow("b")})
            assert project_a.status_code == 200, project_a.text
            assert project_b.status_code == 200, project_b.text
            project_a_id = project_a.json()["project"]["id"]
            project_b_id = project_b.json()["project"]["id"]

            running = client.post("/api/run", json={"projectId": project_a_id, "workflow": workflow("a-run")})
            assert running.status_code == 200, running.text
            runner = FakeRunner.instances[-1]

            foreign_stop = client.post("/api/stop", json={"projectId": project_b_id})
            assert foreign_stop.status_code == 200
            assert runner.running, "project B must not stop project A's runner"

            assert client.put(f"/api/projects/{project_b_id}", json={"workflow": workflow("b-save")}).status_code == 200
            assert len(runner.updates) == 0, "saving project B must not update a run bound to project A"

            assert client.post("/api/workflow/live-update", json={"projectId": project_b_id, "workflow": workflow("b-live")}).status_code == 200
            assert len(runner.updates) == 0, "live update for project B must not update project A run"

            assert client.put(f"/api/projects/{project_a_id}", json={"workflow": workflow("a-save")}).status_code == 200
            assert len(runner.updates) == 1
            assert runner.updates[-1]["nodes"][0]["config"]["marker"] == "a-save"

            assert client.post("/api/workflow/live-update", json={"projectId": project_a_id, "workflow": workflow("a-live")}).status_code == 200
            assert len(runner.updates) == 2
            assert runner.updates[-1]["nodes"][0]["config"]["marker"] == "a-live"

            assert client.post("/api/run", json={"projectId": "missing", "workflow": workflow("bad")}).status_code == 400

            stopped = client.post("/api/stop")
            assert stopped.status_code == 200
            assert stopped.json()["projectId"] == project_a_id
            assert client.get("/api/status").json()["projectId"] == project_a_id
            legacy = client.post("/api/run", json={"workflow": workflow("legacy")})
            assert legacy.status_code == 200, legacy.text
            legacy_runner = FakeRunner.instances[-1]
            assert client.put(f"/api/projects/{project_a_id}", json={"workflow": workflow("unbound-save")}).status_code == 200
            assert len(legacy_runner.updates) == 0, "project save must not implicitly update a legacy unbound run"
            assert client.post("/api/workflow/live-update", json={"workflow": workflow("legacy-live")}).status_code == 200
            assert len(legacy_runner.updates) == 1
            assert legacy_runner.updates[-1]["nodes"][0]["config"]["marker"] == "legacy-live"

            assert client.post("/api/stop").status_code == 200
            fresh = client.post("/api/run", json={"projectId": project_b_id, "workflow": workflow("fresh")})
            assert fresh.status_code == 200, fresh.text
            assert FakeRunner.instances[-1] is not legacy_runner
            assert client.post("/api/workflow/live-update", json={"projectId": project_b_id, "workflow": workflow("fresh-live")}).status_code == 200
            assert FakeRunner.instances[-1].updates[-1]["nodes"][0]["config"]["marker"] == "fresh-live"

    print("project binding contract checks passed")


if __name__ == "__main__":
    main()
