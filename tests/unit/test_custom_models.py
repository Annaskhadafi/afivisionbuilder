import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np

webapp_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(webapp_dir))

from fastapi import HTTPException
from fastapi.testclient import TestClient

import server
from engine.custom_model_runtime import (
    CustomModelRunner,
    _MODEL_CACHE,
    _resolve_labels,
    detect_model_engine,
    extract_model_labels,
)
from server import app


def _onnx_model(path: Path, *, output_shape=(1, 5, 1), input_type="float32"):
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    dtype = TensorProto.FLOAT16 if input_type == "float16" else TensorProto.FLOAT
    input_info = helper.make_tensor_value_info("image", dtype, [1, 3, 4, 4])
    output_info = helper.make_tensor_value_info("pred", TensorProto.FLOAT, list(output_shape))
    values = np.zeros(output_shape, dtype=np.float32)
    values.reshape(-1)[4] = 0.95
    if len(output_shape) == 3 and output_shape[-1] > 1:
        values[0, 4, :] = 0.95
    if len(output_shape) == 3 and output_shape[1] > 5 and output_shape[-1] == 5:
        values[0, :, 4] = 0.95
    constant = helper.make_node("Constant", [], ["pred"], value=numpy_helper.from_array(values))
    graph = helper.make_graph([constant], "synthetic", [input_info], [output_info])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 11)])
    model.metadata_props.add(key="names", value="{0: \"owner's label\"}")
    model.metadata_props.add(key="task", value="detect")
    onnx.save(model, path)
    return path


def test_engine_detection():
    assert detect_model_engine("weights/best.pt") == "ultralytics_yolo"
    assert detect_model_engine("yolov8n.pth") == "ultralytics_yolo"
    assert detect_model_engine("models/detector.onnx") == "onnx_custom"
    assert detect_model_engine("models/classifier.tflite") == "tflite"
    assert detect_model_engine("model.keras") == "tensorflow_keras"
    assert detect_model_engine("weights.h5") == "tensorflow_keras"


def test_label_extraction_sibling():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "labels.txt").write_text("cat\ndog\nbird\n", encoding="utf-8")
        model_file = tmp / "test_model.onnx"
        model_file.write_bytes(b"dummy_model_bytes")
        assert extract_model_labels(str(model_file)) == ["cat", "dog", "bird"]


def test_server_inspect_rejects_invalid_model():
    with tempfile.TemporaryDirectory() as tmpdir, patch.object(server, "_models", Path(tmpdir)):
        invalid = Path(tmpdir) / "broken.pt"
        invalid.write_bytes(b"fake pt weights for testing")
        with TestClient(app, base_url="http://127.0.0.1:8765") as client:
            response = client.get("/api/models/inspect", params={"path": str(invalid)})
    assert response.status_code == 400, response.text
    assert "cannot load" in response.text.lower()


def test_inspect_reports_embedded_onnx_metadata():
    with tempfile.TemporaryDirectory() as tmpdir, patch.object(server, "_models", Path(tmpdir)):
        model = _onnx_model(Path(tmpdir) / "detector.onnx")
        with TestClient(app, base_url="http://127.0.0.1:8765") as client:
            response = client.get("/api/models/inspect", params={"path": str(model)})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["engine"] == "onnx_custom"
        assert data["classes"] == ["owner's label"]
        assert data["task"] == "detect"
        assert data["format"] == "onnx"
        assert data["sizeBytes"] == model.stat().st_size


def test_canonical_model_path_wins_for_preflight_and_load():
    with tempfile.TemporaryDirectory() as tmpdir, patch.object(server, "_models", Path(tmpdir)):
        canonical = Path(tmpdir) / "canonical.onnx"
        legacy = Path(tmpdir) / "legacy.onnx"
        canonical.write_bytes(b"canonical")
        legacy.write_bytes(b"legacy")
        config = {"engine": "custom_auto", "modelPath": str(canonical), "customModelPath": str(legacy), "rfdetrOnnxModel": str(legacy)}
        with patch.object(server, "_model_availability", return_value=True):
            server._preflight_models({"nodes": [{"id": "det", "type": "detector", "config": config}]})
        loaded = []
        with patch.object(CustomModelRunner, "_load_raw", side_effect=lambda engine, path, device="cpu": loaded.append((engine, path)) or object()):
            CustomModelRunner.get_or_load(config)
        assert Path(loaded[0][1]).resolve() == canonical.resolve()


def test_onnx_singleton_and_transposed_outputs():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        one = _onnx_model(tmp / "one.onnx", output_shape=(1, 5, 1))
        _MODEL_CACHE.clear()
        frame = np.zeros((8, 12, 3), dtype=np.uint8)
        config = {"engine": "onnx_custom", "modelPath": str(one), "threshold": 0.5}
        result = CustomModelRunner.run_frame(frame, {"id": "det", "type": "detector", "config": config})
        assert result and result[0]["class"] == "owner's label"
        many = _onnx_model(tmp / "many.onnx", output_shape=(1, 5, 6))
        config["modelPath"] = str(many)
        result = CustomModelRunner.run_frame(frame, {"id": "det", "type": "detector", "config": config})
        assert len(result) == 6
        prediction_first = _onnx_model(tmp / "prediction-first.onnx", output_shape=(1, 6, 5))
        config["modelPath"] = str(prediction_first)
        result = CustomModelRunner.run_frame(frame, {"id": "det", "type": "detector", "config": config})
        assert len(result) == 6


def test_onnx_float16_input():
    with tempfile.TemporaryDirectory() as tmpdir:
        model = _onnx_model(Path(tmpdir) / "half.onnx", input_type="float16")
        result = CustomModelRunner.run_frame(np.zeros((8, 12, 3), dtype=np.uint8), {"id": "det", "type": "detector", "config": {"engine": "onnx_custom", "modelPath": str(model)}})
        assert result and result[0]["class"] == "owner's label"


def test_yolo_retries_cpu_after_cuda_failure():
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "best.pt"
        model_path.write_bytes(b"weights")
        calls = []

        class FakeModel:
            names = {0: "label"}

            def predict(self, frame, **kwargs):
                calls.append(kwargs["device"])
                if kwargs["device"] != "cpu":
                    raise RuntimeError("CUDA out of memory")
                return []

        with patch("engine.main.resolve_inference_device", return_value=("cuda:0", None)), patch.object(CustomModelRunner, "get_or_load", return_value=FakeModel()):
            assert CustomModelRunner.run_frame(np.zeros((4, 4, 3), dtype=np.uint8), {"id": "det", "type": "detector", "config": {"engine": "ultralytics_yolo", "modelPath": str(model_path)}}) == []
        assert calls == ["cuda:0", "cpu"]


def test_model_cache_reloads_after_overwrite():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "reload.onnx"
        path.write_bytes(b"one")
        first, second = object(), object()
        with patch("onnxruntime.InferenceSession", side_effect=[first, second]) as loader:
            _MODEL_CACHE.clear()
            assert CustomModelRunner._load_raw("onnx_custom", str(path)) is first
            path.write_bytes(b"two-two")
            assert CustomModelRunner._load_raw("onnx_custom", str(path)) is second
        assert loader.call_count == 2
        assert list(_MODEL_CACHE.values()) == [second]


def test_onnx_label_override_and_filter():
    with tempfile.TemporaryDirectory() as tmpdir:
        model = _onnx_model(Path(tmpdir) / "labels.onnx")
        frame = np.zeros((8, 12, 3), dtype=np.uint8)
        override = {"engine": "onnx_custom", "modelPath": str(model), "customClasses": "override"}
        result = CustomModelRunner.run_frame(frame, {"id": "det", "type": "detector", "config": override})
        assert result and result[0]["class"] == "override"
        filtered = {**override, "classes": "different"}
        assert CustomModelRunner.run_frame(frame, {"id": "det", "type": "detector", "config": filtered}) == []


def test_missing_best_pt_fails_preflight():
    with tempfile.TemporaryDirectory() as tmpdir, patch.object(server, "_models", Path(tmpdir)):
        workflow = {"nodes": [{"id": "det", "type": "detector", "config": {"engine": "custom_auto", "modelPath": "best.pt"}}]}
        try:
            server._preflight_models(workflow)
        except HTTPException as exc:
            assert exc.status_code == 400
            assert "not found" in str(exc.detail).lower()
        else:
            raise AssertionError("missing best.pt unexpectedly passed preflight")


def test_upload_same_basename_versions_content_without_overwrite():
    with tempfile.TemporaryDirectory() as tmpdir, patch.object(server, "_models", Path(tmpdir)):
        with TestClient(app, base_url="http://127.0.0.1:8765") as client:
            first = client.post("/api/models/upload", files={"file": ("same.onnx", b"one", "application/octet-stream")})
            second = client.post("/api/models/upload", files={"file": ("same.onnx", b"two-two", "application/octet-stream")})
        assert first.status_code == second.status_code == 200
        assert first.json()["path"] != second.json()["path"]
        assert first.json()["sha256"] != second.json()["sha256"]
        assert Path(first.json()["path"]).read_bytes() == b"one"
        assert Path(second.json()["path"]).read_bytes() == b"two-two"


def test_upload_identical_content_is_idempotent_and_listing_has_fingerprint():
    with tempfile.TemporaryDirectory() as tmpdir, patch.object(server, "_models", Path(tmpdir)):
        with TestClient(app, base_url="http://127.0.0.1:8765") as client:
            first = client.post("/api/models/upload", files={"file": ("same.onnx", b"one", "application/octet-stream")})
            second = client.post("/api/models/upload", files={"file": ("same.onnx", b"one", "application/octet-stream")})
            listing = client.get("/api/models").json()["models"]
        assert first.json()["path"] == second.json()["path"]
        assert len(listing) == 1
        assert listing[0]["sha256"] == first.json()["sha256"]
        assert listing[0]["fingerprint"] == first.json()["sha256"][:8]
        assert listing[0]["label"].startswith("same.onnx · ")


def test_upload_preserves_legacy_model_and_inspect_reports_checksum():
    with tempfile.TemporaryDirectory() as tmpdir, patch.object(server, "_models", Path(tmpdir)):
        legacy = Path(tmpdir) / "legacy.onnx"
        legacy.write_bytes(b"legacy")
        with TestClient(app, base_url="http://127.0.0.1:8765") as client:
            uploaded = client.post("/api/models/upload", files={"file": ("new.tflite", b"new", "application/octet-stream")})
            inspected = client.get("/api/models/inspect", params={"path": uploaded.json()["path"]})
            listing = client.get("/api/models").json()["models"]
        assert legacy.read_bytes() == b"legacy"
        assert inspected.status_code == 200
        assert inspected.json()["sha256"] == uploaded.json()["sha256"]
        assert any(item["path"] == str(legacy) and item["sha256"] is None and item["fingerprint"] is None for item in listing)


def test_oversize_upload_cleans_staging_and_publish_files():
    with tempfile.TemporaryDirectory() as tmpdir, patch.object(server, "_models", Path(tmpdir)), patch.object(server, "_MAX_MODEL_UPLOAD", 2):
        legacy = Path(tmpdir) / "existing.pt"
        legacy.write_bytes(b"keep")
        with TestClient(app, base_url="http://127.0.0.1:8765") as client:
            response = client.post("/api/models/upload", files={"file": ("too.pt", b"three", "application/octet-stream")})
        assert response.status_code == 413
        assert legacy.read_bytes() == b"keep"
        assert not list(Path(tmpdir).rglob("*.tmp"))
        assert not any(path.is_file() and path.name != "existing.pt" for path in Path(tmpdir).rglob("*"))


def test_custom_runner_formatting():
    assert _resolve_labels({"customClasses": "widget, bolt, nut"}, "models/fake.pt") == ["widget", "bolt", "nut"]


def test_phase1_enhancements():
    from engine import node_catalog

    assert "webhook_output" in node_catalog.NODE_BLUEPRINTS
    assert "iouThreshold" in node_catalog.NODE_BLUEPRINTS["detector"]["config"]
    assert "direction" in node_catalog.NODE_BLUEPRINTS["object_counter"]["config"]
    assert "captureMode" in node_catalog.NODE_BLUEPRINTS["track_snapshot"]["config"]
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        response = client.get("/api/database/records")
    assert response.status_code == 200
    assert "records" in response.json()


if __name__ == "__main__":
    for name, value in list(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("All custom model tests PASSED successfully!")
