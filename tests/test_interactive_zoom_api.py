import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "engine"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

import numpy as np
import pytest
from starlette.testclient import TestClient

from server import app
from interactive_zoom import get_interactive_zoom_runtime


@pytest.fixture
def client():
    return TestClient(app, base_url="http://127.0.0.1:8765")


def test_catalog_contains_interactive_zoom(client):
    res = client.get("/api/catalog")
    assert res.status_code == 200
    data = res.json()
    assert "interactive_zoom" in data["catalog"]
    zoom_spec = data["catalog"]["interactive_zoom"]
    assert zoom_spec["title"] == "Interactive Object Zoom"
    assert zoom_spec["category"] == "Annotations & Drawing"


def test_interactive_zoom_endpoints(client):
    node_id = "test_zoom_api_node"
    rt = get_interactive_zoom_runtime(node_id)

    # Populate detections and frame
    frame = np.full((720, 1280, 3), 100, dtype=np.uint8)
    detections = [
        {"class": "car", "confidence": 0.94, "track_id": 77, "box": [100, 100, 400, 400]},
    ]
    rt.apply(frame, detections, {})

    # 1. Target endpoint initially idle
    res = client.get(f"/api/interactive-zoom/{node_id}/target")
    assert res.status_code == 200
    assert res.json()["state"]["status"] == "idle"

    # 2. Select by point (inside car box at 200, 200)
    norm_x = 200.0 / 1280.0
    norm_y = 200.0 / 720.0
    res_select = client.post(
        f"/api/interactive-zoom/{node_id}/select",
        json={"normX": norm_x, "normY": norm_y},
    )
    assert res_select.status_code == 200
    assert res_select.json()["ok"] is True
    assert res_select.json()["state"]["status"] == "locked"
    assert res_select.json()["state"]["trackId"] == 77

    # 3. Apply frame again to ensure crop is generated
    rt.apply(frame, detections, {})

    # 4. Fetch crop image
    res_crop = client.get(f"/api/interactive-zoom/{node_id}/crop")
    assert res_crop.status_code == 200
    assert res_crop.headers["content-type"] == "image/jpeg"
    assert len(res_crop.content) > 0

    # 5. Reset target
    res_reset = client.post(f"/api/interactive-zoom/{node_id}/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["state"]["status"] == "idle"


def test_interactive_zoom_resize_endpoint(client):
    node_id = "test_zoom_resize_api"
    res = client.post(f"/api/interactive-zoom/{node_id}/resize", json={"sizePercent": 40})
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert res.json()["pipSizePercent"] == 40

    # Test clamped to max 50%
    res_clamped = client.post(f"/api/interactive-zoom/{node_id}/resize", json={"sizePercent": 90})
    assert res_clamped.status_code == 200
    assert res_clamped.json()["pipSizePercent"] == 50
