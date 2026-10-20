"""Unit tests for Screenshot Capture and Telegram Notification nodes."""
import os
import shutil
import time
import numpy as np
import pytest

from engine.screenshot_capture import (
    capture_screenshot,
    crop_first_detection,
    process_screenshot_node,
    render_detections_on_frame,
)
from engine.telegram_sink import (
    build_multipart_form_data,
    dispatch_telegram_alert,
    format_telegram_caption,
)
from engine.node_catalog import NODE_BLUEPRINTS


@pytest.fixture
def sample_frame():
    """Create a dummy 640x480 RGB image."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[100:200, 100:200] = [0, 255, 0]  # green square
    return img


@pytest.fixture
def sample_detections():
    return [
        {
            "class": "forklift",
            "confidence": 0.92,
            "bbox": [100, 100, 100, 100],
            "track_id": 42,
        }
    ]


@pytest.fixture
def sample_event():
    return {
        "type": "ZONE_ENTRY",
        "zoneName": "Loading Bay 1",
        "message": "Forklift entered active zone",
        "class": "forklift",
        "confidence": 0.92,
        "track_id": 42,
    }


# -------------------------------------------------------------------------
# Test Screenshot Capture
# -------------------------------------------------------------------------

def test_screenshot_catalog_registration():
    """Verify screenshot_capture and telegram_notification are in catalog."""
    assert "screenshot_capture" in NODE_BLUEPRINTS
    assert "telegram_notification" in NODE_BLUEPRINTS

    ss_cfg = NODE_BLUEPRINTS["screenshot_capture"]["config"]
    assert "captureMode" in ss_cfg
    assert "jpegQuality" in ss_cfg
    assert "addTimestampWatermark" in ss_cfg
    assert "saveToDisk" in ss_cfg

    tg_cfg = NODE_BLUEPRINTS["telegram_notification"]["config"]
    assert "botToken" in tg_cfg
    assert "chatId" in tg_cfg
    assert "messageCaption" in tg_cfg
    assert "cooldownSeconds" in tg_cfg


def test_screenshot_full_annotated(sample_frame, sample_detections):
    """Test full annotated screenshot capture."""
    res = capture_screenshot(
        sample_frame,
        detections=sample_detections,
        config={"captureMode": "full_annotated", "jpegQuality": 85, "saveToDisk": False},
    )
    assert res["status"] == "captured"
    assert res["bytes"] is not None
    assert len(res["bytes"]) > 100
    assert res["path"] is None  # in-memory only by default
    assert res["mode"] == "full_annotated"
    assert res["image"] is not None


def test_screenshot_raw_frame(sample_frame):
    """Test raw camera frame screenshot capture without annotations."""
    res = capture_screenshot(
        sample_frame,
        config={"captureMode": "raw_frame", "addTimestampWatermark": False, "saveToDisk": False},
    )
    assert res["status"] == "captured"
    assert res["mode"] == "raw_frame"
    assert res["bytes"] is not None


def test_screenshot_crop_object(sample_frame, sample_detections):
    """Test cropping target object bounding box."""
    res = capture_screenshot(
        sample_frame,
        detections=sample_detections,
        config={"captureMode": "crop_object", "saveToDisk": False},
    )
    assert res["status"] == "captured"
    assert res["mode"] == "crop_object"
    # Cropped image should have smaller dimensions than original 640x480
    assert res["image"].shape[0] < 480
    assert res["image"].shape[1] < 640


def test_screenshot_save_to_disk(sample_frame, tmp_path):
    """Test optional disk saving when enabled."""
    out_dir = str(tmp_path / "test_snapshots")
    res = capture_screenshot(
        sample_frame,
        config={"saveToDisk": True, "outputDirectory": out_dir},
    )
    assert res["status"] == "captured"
    assert res["path"] is not None
    assert os.path.isfile(res["path"])
    assert os.path.getsize(res["path"]) > 0


def test_process_screenshot_node_enriches_events(sample_frame, sample_detections, sample_event):
    """Verify that process_screenshot_node enriches event records with snapshot payload."""
    events = [sample_event]
    node = {
        "id": "ss_1",
        "type": "screenshot_capture",
        "config": {"captureMode": "full_annotated", "saveToDisk": False},
    }

    result = process_screenshot_node(node, sample_frame, sample_detections, events)
    assert result["status"] == "captured"
    assert "snapshot_bytes" in events[0]
    assert events[0]["snapshot_bytes"] == result["bytes"]
    assert "snapshot_image" in events[0]


# -------------------------------------------------------------------------
# Test Telegram Notification
# -------------------------------------------------------------------------

def test_telegram_caption_interpolation(sample_event):
    """Test template token replacement in Telegram captions."""
    tpl = "Alert: {event.type} in {event.zoneName} for {class} (#{track_id})"
    formatted = format_telegram_caption(tpl, sample_event)
    assert "ZONE_ENTRY" in formatted
    assert "Loading Bay 1" in formatted
    assert "forklift" in formatted
    assert "#42" in formatted


def test_telegram_multipart_builder():
    """Verify multipart/form-data encoding structure."""
    fields = {"chat_id": "12345678", "caption": "Hello world", "parse_mode": "HTML"}
    files = {"photo": ("test.jpg", b"\xff\xd8\xff\xe0dummy_jpeg", "image/jpeg")}

    body, content_type = build_multipart_form_data(fields, files)
    assert "multipart/form-data; boundary=" in content_type
    assert b'name="chat_id"' in body
    assert b"12345678" in body
    assert b'filename="test.jpg"' in body
    assert b"dummy_jpeg" in body


def test_telegram_simulated_dispatch_without_tokens(sample_event, sample_frame):
    """Test dispatch fallback when botToken and chatId are not set."""
    node_state = {}
    config = {
        "botToken": "",
        "chatId": "",
        "messageCaption": "Test: {event.type}",
        "cooldownSeconds": 5.0,
    }

    res = dispatch_telegram_alert(sample_event, sample_frame, config, node_state)
    assert res["status"] == "simulated_delivered"
    assert "Test: ZONE_ENTRY" in res["caption"]
    assert res["hasPhoto"] is True
    assert "last_telegram_time" in node_state


def test_telegram_cooldown_throttling(sample_event, sample_frame):
    """Test anti-spam cooldown throttling."""
    node_state = {}
    config = {"cooldownSeconds": 10.0}

    # First dispatch succeeds
    res1 = dispatch_telegram_alert(sample_event, sample_frame, config, node_state)
    assert res1["status"] == "simulated_delivered"

    # Second immediate dispatch should be throttled
    res2 = dispatch_telegram_alert(sample_event, sample_frame, config, node_state)
    assert res2["status"] == "throttled"
    assert "cooldownRemaining" in res2
    assert res2["cooldownRemaining"] > 0


def test_telegram_consumes_upstream_screenshot_bytes(sample_event):
    """Test dual topology: Telegram uses snapshot_bytes attached by Screenshot Node."""
    sample_event["snapshot_bytes"] = b"\xff\xd8\xff\xe0mock_snapshot"
    node_state = {}
    config = {"cooldownSeconds": 2.0}

    # Frame is None, but snapshot_bytes is in event
    res = dispatch_telegram_alert(sample_event, None, config, node_state)
    assert res["status"] == "simulated_delivered"
    assert res["hasPhoto"] is True
