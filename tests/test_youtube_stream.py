import pytest
import sys
from pathlib import Path

# Add project root and engine to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "engine"))

from engine.main import is_youtube_url, resolve_youtube_stream_url, OpenCVInputSource
import engine.workflow_store as store
from server import _templates


def test_is_youtube_url():
    assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True
    assert is_youtube_url("http://youtube.com/live/123456") is True
    assert is_youtube_url("https://example.com/video.mp4") is False
    assert is_youtube_url("rtsp://192.168.1.1:554/live") is False
    assert is_youtube_url("") is False


def test_templates_have_youtube_inputs():
    templates = _templates()
    template_ids = [t["id"] for t in templates]
    
    assert "traffic_flow_counter" in template_ids
    assert "restaurant_table_occupancy" in template_ids
    assert "assembly_workshop_cycle_timer" in template_ids
    assert "warehouse_forklift_safety_guard" in template_ids
    assert "retail_checkout_queue_monitor" in template_ids

    traffic = next(t for t in templates if t["id"] == "traffic_flow_counter")
    input_node = next(n for n in traffic["workflow"]["nodes"] if n["id"] == "input")
    assert input_node["config"]["sourceType"] == "youtube"
    assert "youtube.com" in input_node["config"]["youtubeUrl"]
    assert input_node["config"]["autoReconnect"] is True

    restaurant = next(t for t in templates if t["id"] == "restaurant_table_occupancy")
    rest_input = next(n for n in restaurant["workflow"]["nodes"] if n["id"] == "input")
    assert rest_input["config"]["sourceType"] == "youtube"

    assembly = next(t for t in templates if t["id"] == "assembly_workshop_cycle_timer")
    assembly_input = next(n for n in assembly["workflow"]["nodes"] if n["id"] == "input")
    assert assembly_input["config"]["sourceType"] == "youtube"

    warehouse = next(t for t in templates if t["id"] == "warehouse_forklift_safety_guard")
    wh_input = next(n for n in warehouse["workflow"]["nodes"] if n["id"] == "input")
    assert wh_input["config"]["sourceType"] == "youtube"

    retail = next(t for t in templates if t["id"] == "retail_checkout_queue_monitor")
    retail_input = next(n for n in retail["workflow"]["nodes"] if n["id"] == "input")
    assert retail_input["config"]["sourceType"] == "youtube"


def test_resolve_youtube_stream_url_mocked(monkeypatch):
    class MockYDL:
        def __init__(self, opts):
            self.opts = opts
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def extract_info(self, url, download=False):
            return {
                "title": "Mock YouTube Stream",
                "url": "https://googlevideo.mock/stream.mp4",
                "is_live": False,
            }

    import yt_dlp
    monkeypatch.setattr(yt_dlp, "YoutubeDL", MockYDL)

    stream_url, is_live, title = resolve_youtube_stream_url("https://www.youtube.com/watch?v=mock123", "720p")
    assert stream_url == "https://googlevideo.mock/stream.mp4"
    assert is_live is False
    assert title == "Mock YouTube Stream"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
