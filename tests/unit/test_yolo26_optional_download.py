from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture
def isolated_model_store(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    monkeypatch.setattr(server, "_models", model_dir)
    model_dir.mkdir()
    return model_dir


def test_yolo26_download_rejects_unapproved_model_before_downloader(monkeypatch, isolated_model_store):
    from ultralytics.utils import downloads

    calls = []
    monkeypatch.setattr(downloads, "attempt_download_asset", lambda *args, **kwargs: calls.append((args, kwargs)))
    with TestClient(server.app, base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/models/download-yolo26", json={"model": "https://example.com/evil.pt"})

    assert response.status_code == 400
    assert calls == []
    assert list(isolated_model_store.rglob("*.pt")) == []


def test_yolo26_download_is_explicit_content_addressed_and_idempotent(monkeypatch, isolated_model_store):
    from ultralytics.utils import downloads

    weight_bytes = b"test fixture only; not a real model checkpoint"
    calls = []

    def fake_download_asset(file, *, repo, release):
        calls.append((repo, release))
        target = Path(file)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(weight_bytes)
        return str(target)

    monkeypatch.setattr(downloads, "attempt_download_asset", fake_download_asset)
    expected_digest = hashlib.sha256(weight_bytes).hexdigest()
    with TestClient(server.app, base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/models/download-yolo26", json={"model": "yolo26n.pt"})
        assert response.status_code == 200, response.text
        result = response.json()
        stored_path = Path(result["path"])
        assert stored_path == isolated_model_store / expected_digest / "yolo26n.pt"
        assert stored_path.read_bytes() == weight_bytes
        assert result["sha256"] == expected_digest
        assert result["sizeBytes"] == len(weight_bytes)

        again = client.post("/api/models/download-yolo26", json={"model": "yolo26n.pt"})
        assert again.status_code == 200, again.text
        assert again.json()["path"] == result["path"]

    assert calls == [("ultralytics/assets", "v8.4.0")]
    assert list(isolated_model_store.rglob("*.pt")) == [isolated_model_store / expected_digest / "yolo26n.pt"]
