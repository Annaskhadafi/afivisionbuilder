"""Focused smoke checks: python webapp/test_server.py"""
from __future__ import annotations

import os
import tempfile
import threading
import time

import cv2
import numpy as np
from fastapi.testclient import TestClient


def main() -> None:
    temp_dir = tempfile.TemporaryDirectory(prefix="visonode-test-")
    os.environ["VISONODE_APP_DATA_DIR"] = temp_dir.name
    import server

    with TestClient(server.app, base_url="http://127.0.0.1:8765") as client:
        workflow = {
            "nodes": [
                {"id": "input", "type": "input", "config": {}},
                {"id": "preview", "type": "preview", "config": {}},
            ],
            "edges": [["input", "preview"]],
        }
        assert client.get("/", headers={"host": "attacker.example"}).status_code == 400
        created = client.post("/api/projects", json={"name": "Smoke", "workflow": workflow})
        assert created.status_code == 200, created.text
        project_id = created.json()["project"]["id"]
        bad_origin = {"origin": "http://attacker.example"}
        assert client.post("/api/projects", json={"workflow": workflow}, headers=bad_origin).status_code == 403
        assert client.put(f"/api/projects/{project_id}", json={"workflow": workflow}, headers=bad_origin).status_code == 403
        assert client.delete(f"/api/projects/{project_id}", headers=bad_origin).status_code == 403
        assert client.post("/api/run", json={"workflow": workflow}, headers=bad_origin).status_code == 403
        assert client.post("/api/stop", headers=bad_origin).status_code == 403
        assert client.post("/api/upload", files={"file": ("x.png", b"x", "image/png")}, headers=bad_origin).status_code == 403
        loaded = client.get(f"/api/projects/{project_id}").json()["workflow"]
        assert [node["id"] for node in loaded["nodes"]] == ["input", "preview"]
        assert loaded["edges"] == workflow["edges"]
        assert client.put(f"/api/projects/{project_id}", json={"name": "Renamed", "workflow": workflow}).json()["project"]["name"] == "Renamed"
        assert client.post("/api/projects", json={"workflow": {"nodes": [{"id": "x", "type": "input"}], "edges": [["x", "missing"]]}}).status_code == 400
        invalid = [
            {"nodes": workflow["nodes"], "edges": [["input", "preview"], ["preview", "input"]]},
            {"nodes": workflow["nodes"], "edges": [["input", ["preview"]]]},
            {"nodes": [{"id": "input", "type": "unknown", "config": {}}], "edges": []},
            {"nodes": [{"id": "", "type": "input", "config": {}}], "edges": []},
        ]
        for bad in invalid:
            assert client.post("/api/projects", json={"workflow": bad}).status_code == 400
        empty = {"nodes": [{"id": "input", "type": "input", "config": {"sourceType": "image", "filePath": ""}}, {"id": "preview", "type": "preview", "config": {}}], "edges": [["input", "preview"]]}
        disabled = {**empty, "nodes": [{**empty["nodes"][0], "enabled": False}, empty["nodes"][1]]}
        assert client.post("/api/run", json={"workflow": empty}).status_code == 400
        assert client.post("/api/run", json={"workflow": disabled}).status_code == 400

        results = []
        def update(i):
            results.append(client.put(f"/api/projects/{project_id}", json={"name": f"n{i}", "workflow": workflow}))
        threads = [threading.Thread(target=update, args=(i,)) for i in range(8)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        assert all(result.status_code == 200 for result in results)
        assert client.get(f"/api/projects/{project_id}").json()["workflow"]["edges"] == workflow["edges"]
        assert client.get("/api/projects/../secret").status_code in (404, 400)

        ok, encoded = cv2.imencode(".png", np.dstack([np.full((20, 30), 10, np.uint8), np.full((20, 30), 80, np.uint8), np.full((20, 30), 200, np.uint8)]))
        assert ok
        upload = client.post("/api/upload", files={"file": ("input.png", encoded.tobytes(), "image/png")})
        assert upload.status_code == 200, upload.text
        workflow["nodes"][0]["config"] = {"sourceType": "image", "filePath": upload.json()["path"]}
        workflow["nodes"].insert(1, {"id": "gray", "type": "color_convert", "config": {"mode": "gray"}})
        workflow["nodes"].insert(2, {"id": "scaled", "type": "resize", "config": {"width": 7, "height": 5}})
        workflow["edges"] = [["input", "gray"], ["gray", "scaled"], ["scaled", "preview"]]
        assert client.post("/api/run", json={"workflow": workflow}).status_code == 200
        for _ in range(50):
            if client.get("/api/status").json()["previews"]:
                break
            time.sleep(0.1)
        preview = client.get("/api/preview/preview")
        assert preview.headers["content-type"] == "image/jpeg"
        decoded = cv2.imdecode(np.frombuffer(preview.content, dtype=np.uint8), cv2.IMREAD_COLOR)
        assert decoded is not None and decoded.shape == (5, 7, 3) and np.ptp(decoded, axis=2).max() == 0
        assert client.post("/api/stop").status_code == 200

        video_path = os.path.join(temp_dir.name, "finite.avi")
        writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (32, 24))
        for value in (20, 100, 200):
            writer.write(np.full((24, 32, 3), value, np.uint8))
        writer.release()
        with open(video_path, "rb") as video_file:
            upload = client.post("/api/upload", files={"file": ("finite.avi", video_file, "video/x-msvideo")})
        assert upload.status_code == 200
        video_workflow = {"nodes": [{"id": "input", "type": "input", "config": {"sourceType": "video", "filePath": upload.json()["path"], "loop": False}}, {"id": "preview", "type": "preview", "config": {}}], "edges": [["input", "preview"]]}
        assert client.post("/api/run", json={"workflow": video_workflow}).status_code == 200
        for _ in range(100):
            status = client.get("/api/status").json()
            if not status["running"]:
                break
            time.sleep(0.05)
        assert not status["running"] and status["error"] is None and "preview" in status["previews"]
        templates = client.get("/api/templates").json()
        assert "templates" in templates and len(templates["templates"]) >= 5
        model_upload = client.post("/api/models/upload", files={"file": ("dummy.onnx", b"ONNX...", "application/octet-stream")})
        assert model_upload.status_code == 200 and model_upload.json()["name"] == "dummy.onnx"
        models_list = client.get("/api/models").json()
        assert any(m["name"] == "dummy.onnx" for m in models_list["models"])
        db_records = client.get("/api/database/records").json()
        assert "records" in db_records
    temp_dir.cleanup()
    print("server smoke checks passed")


if __name__ == "__main__":
    main()
