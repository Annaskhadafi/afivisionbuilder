import time
import numpy as np
import pytest

from engine.interactive_zoom import InteractiveZoomRuntime


def test_interactive_zoom_selection():
    rt = InteractiveZoomRuntime("test_node")

    # Set up synthetic detections
    detections = [
        {"class": "car", "confidence": 0.95, "track_id": 101, "box": [100, 100, 300, 300]},
        {"class": "person", "confidence": 0.88, "track_id": 102, "box": [500, 200, 600, 500]},
    ]
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    # Apply frame once so runtime learns detections and frame dimensions
    out = rt.apply(frame, detections, {})
    assert out.shape == (720, 1280, 3)
    assert rt.status == "idle"

    # Click on the car at (200, 200) -> normalized (200/1280, 200/720)
    norm_x = 200.0 / 1280.0
    norm_y = 200.0 / 720.0
    state = rt.select_by_point(norm_x, norm_y)
    assert state is not None
    assert state["status"] == "locked"
    assert state["trackId"] == 101
    assert state["className"] == "car"

    # Next frame with target present: PiP rendered and status stays locked
    out2 = rt.apply(frame, detections, {"pipPosition": "top-right", "zoomScale": 2.0})
    assert out2 is not None
    assert rt.status == "locked"
    assert rt.get_latest_crop_jpeg() is not None

    # Test click on empty area -> should return None and not match
    miss = rt.select_by_point(0.01, 0.01)
    assert miss is None


def test_interactive_zoom_target_lost_and_reset():
    rt = InteractiveZoomRuntime("test_node_lost")
    detections = [
        {"class": "truck", "confidence": 0.92, "track_id": 42, "box": [200, 200, 400, 400]},
    ]
    frame = np.ones((720, 1280, 3), dtype=np.uint8) * 128

    rt.apply(frame, detections, {})
    rt.select_by_track_id(42)
    assert rt.status == "locked"

    # Next frame: detections are empty (object occluded)
    out = rt.apply(frame, [], {"targetLostHoldSeconds": 0.5})
    assert rt.status == "lost"
    assert out is not None

    # Wait beyond hold seconds -> status resets to idle
    time.sleep(0.6)
    out_after = rt.apply(frame, [], {"targetLostHoldSeconds": 0.5})
    assert rt.status == "idle"
    assert rt.selected_track_id is None

    # Manual reset test
    rt.select_by_track_id(42)
    assert rt.selected_track_id == 42
    rt.reset_target()
    assert rt.status == "idle"
    assert rt.selected_track_id is None


def test_interactive_zoom_resize():
    rt = InteractiveZoomRuntime("test_node_resize")
    detections = [{"class": "car", "confidence": 0.95, "track_id": 1, "box": [50, 50, 200, 200]}]
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    rt.apply(frame, detections, {})
    rt.select_by_track_id(1)

    # Default size (30%)
    out_default = rt.apply(frame.copy(), detections, {"pipSizePercent": 30})
    assert out_default is not None

    # Change to 50%
    new_size = rt.set_pip_size(50)
    assert new_size == 50
    out_large = rt.apply(frame.copy(), detections, {"pipSizePercent": 30})
    assert out_large is not None

    # Verify strict maximum cap at 50%
    clamped_size = rt.set_pip_size(75)
    assert clamped_size == 50


def test_interactive_zoom_hide_toggles():
    rt = InteractiveZoomRuntime("test_node_toggles")
    detections = [{"class": "person", "confidence": 0.89, "track_id": 99, "box": [100, 100, 250, 400]}]
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    rt.apply(frame, detections, {})
    rt.select_by_track_id(99)

    # Render with class and confidence hidden
    cfg = {
        "showClassName": False,
        "showConfidence": False,
        "showDownloadButton": False,
    }
    out = rt.apply(frame.copy(), detections, cfg)
    assert out is not None

    state = rt.get_state()
    assert state["showClassName"] is False
    assert state["showConfidence"] is False
    assert state["showDownloadButton"] is False


def test_interactive_zoom_headroom_anti_cut_face():
    rt = InteractiveZoomRuntime("test_node_headroom")
    # Simulate a person whose detector bbox only starts at collar (y=200..600)
    # The head is at y=100..200
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame[100:200, 500:600] = [0, 255, 0]  # Green head
    frame[200:600, 500:600] = [255, 0, 0]  # Blue body

    detections = [
        {"class": "orang", "originalClass": "person", "confidence": 0.88, "track_id": 4, "box": [500, 200, 600, 600]}
    ]
    rt.apply(frame, detections, {"pipSizeMode": "dynamic", "headroomPercent": 48})
    rt.select_by_track_id(4)
    rt.apply(frame, detections, {"pipSizeMode": "dynamic", "headroomPercent": 48})

    crop = rt.last_crop
    assert crop is not None
    # Verify green head pixels are present in crop
    has_head = np.any((crop[:, :, 1] > 200) & (crop[:, :, 0] < 50))
    assert bool(has_head) is True

    # Test set_headroom
    rt.set_headroom(65)
    assert rt.get_state()["headroomPercent"] == 65


def test_interactive_zoom_clean_crop_no_burned_reticle():
    rt = InteractiveZoomRuntime("test_clean_crop")
    frame = np.full((720, 1280, 3), 120, dtype=np.uint8)
    detections = [
        {"class": "orang", "originalClass": "person", "confidence": 0.85, "track_id": 5, "box": [400, 200, 500, 500]}
    ]
    rt.apply(frame, detections, {})
    rt.select_by_track_id(5)

    # Frame before apply
    clean_frame = np.full((720, 1280, 3), 120, dtype=np.uint8)
    # Target reticle color is Cyan (255, 229, 0)
    out = rt.apply(clean_frame, detections, {"showTargetBox": True, "pipSizeMode": "dynamic"})

    # Check that clean_frame has the reticle
    # But last_crop MUST be from the clean frame before reticle was drawn!
    crop = rt.last_crop
    assert crop is not None
    # All pixels in crop must be roughly the original background color (120, 120, 120), NOT cyan reticle!
    is_pure_background = np.all(crop == 120)
    assert is_pure_background, "Reticle or text was burned into the crop!"

    # And verify zoomScale for person is strictly 1.0 (Full View)
    assert rt.override_zoom_scale == 1.0
