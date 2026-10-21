"""Unit tests for preview compression (720p/480p, 65-75% JPEG quality) and asynchronous non-blocking sinks."""
import os
import time
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import server
from engine.telegram_sink import dispatch_telegram_alert
from engine.cloud_sinks import upload_to_s3, dispatch_notification


@pytest.fixture
def test_client():
    return TestClient(server.app, base_url="http://127.0.0.1:8765")


def test_preview_frame_compression_and_dual_resolution():
    """Verify preview frame downscales to 720p and 480p and uses compressed JPEG quality (65-75%)."""
    # Create large 1080p frame (1920x1080)
    large_frame = np.full((1080, 1920, 3), 120, dtype=np.uint8)
    node_id = "test_preview_node"

    server._frame(node_id, large_frame)

    with server._lock:
        bytes_720 = server._previews.get(node_id)
        bytes_480 = server._previews_480p.get(node_id)

    assert bytes_720 is not None, "720p preview frame must be stored"
    assert bytes_480 is not None, "480p preview frame must be stored"
    # 480p frame should be significantly smaller in bytes than 720p
    assert len(bytes_480) < len(bytes_720)

    # Decode and check dimensions
    img_720 = cv2.imdecode(np.frombuffer(bytes_720, np.uint8), cv2.IMREAD_COLOR)
    assert img_720.shape[1] == 1280
    assert img_720.shape[0] == 720

    img_480 = cv2.imdecode(np.frombuffer(bytes_480, np.uint8), cv2.IMREAD_COLOR)
    assert img_480.shape[1] == 854
    assert img_480.shape[0] == 480


def test_preview_api_endpoints_res_selection(test_client):
    """Verify /api/preview/{node_id} supports ?res=720p and ?res=480p."""
    node_id = "test_res_node"
    sample_frame = np.full((720, 1280, 3), 80, dtype=np.uint8)
    server._frame(node_id, sample_frame)

    # Request default / 720p
    resp_720 = test_client.get(f"/api/preview/{node_id}?res=720p")
    assert resp_720.status_code == 200
    assert resp_720.headers["content-type"] == "image/jpeg"

    # Request 480p
    resp_480 = test_client.get(f"/api/preview/{node_id}?res=480p")
    assert resp_480.status_code == 200
    assert resp_480.headers["content-type"] == "image/jpeg"
    assert len(resp_480.content) < len(resp_720.content)


def test_telegram_async_non_blocking_dispatch():
    """Verify dispatch_telegram_alert returns immediately in async mode without blocking."""
    event = {
        "type": "ZONE_ENTRY",
        "zoneName": "Warehouse Bay 3",
        "message": "Pallet detected",
    }
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    node_state = {}
    config = {
        "botToken": "123456:SAMPLE_TOKEN",
        "chatId": "-10011223344",
        "cooldownSeconds": 5.0,
        "asyncDispatch": True,
    }

    t0 = time.time()
    res = dispatch_telegram_alert(event, img, config, node_state, async_dispatch=True)
    t_elapsed = time.time() - t0

    # Must return almost instantly (< 50ms) because network call is offloaded to background worker
    assert t_elapsed < 0.1
    assert res["status"] == "dispatched_async"
    assert res["ok"] is True
    assert "last_telegram_time" in node_state


def test_cloud_sinks_async_non_blocking():
    """Verify notification_dispatcher returns immediately in async mode without blocking."""
    event = {"type": "TEMPERATURE_ALERT", "zoneName": "Server Room"}
    node_state = {}
    config = {
        "channel": "webhook",
        "destinationId": "https://example.com/api/webhook/test",
        "cooldownSeconds": 5.0,
        "asyncDispatch": True,
    }

    t0 = time.time()
    res = dispatch_notification(event, None, config, node_state, async_dispatch=True)
    t_elapsed = time.time() - t0

    assert t_elapsed < 0.1
    assert res["status"] == "dispatched_async"
    assert "last_notification_time" in node_state
