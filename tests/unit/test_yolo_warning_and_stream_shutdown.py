import asyncio
from types import SimpleNamespace

import numpy as np
import pytest
from ultralytics import YOLO
from ultralytics.utils import LOGGER
from engine.custom_model_runtime import configure_nms_free, CustomModelRunner, resolve_model_file
import server


def test_yolov8_uses_supported_head_without_repeated_warnings(monkeypatch):
    warnings = []
    model_path = resolve_model_file('yolov8n.pt')
    if not model_path.is_file():
        pytest.skip('yolov8n.pt not found in local models')
    model = YOLO(str(model_path))
    monkeypatch.setattr(LOGGER, 'warning', lambda message, *args, **kwargs: warnings.append(str(message)))
    for requested in (None, True, True, False):
        assert configure_nms_free(model, requested, 'yolov8n.pt') is False
    assert not warnings
    node = {'id': 'det', 'type': 'detector', 'config': {'engine': 'ultralytics_yolo', 'modelPath': 'yolov8n.pt', 'nmsFree': True}}
    assert isinstance(CustomModelRunner.run_frame(np.zeros((64, 64, 3), np.uint8), node), list)
    assert not warnings


def test_preview_stream_closes_with_stale_frame_after_stop(monkeypatch):
    now = [0.0]
    async def sleep(_seconds):
        now[0] += 1
    monkeypatch.setattr(server, 'time', SimpleNamespace(monotonic=lambda: now[0]))
    monkeypatch.setattr(server.asyncio, 'sleep', sleep)
    monkeypatch.setattr(server, '_runner', SimpleNamespace(is_running=lambda: False))
    monkeypatch.setattr(server, '_previews', {'preview': b'frame'})
    monkeypatch.setattr(server, '_previews_480p', {})
    async def check():
        response = await server.preview_stream('preview')
        chunks = [chunk async for chunk in response.body_iterator]
        assert len(chunks) == 1 and b'frame' in chunks[0]
        assert now[0] >= 5
    asyncio.run(check())
