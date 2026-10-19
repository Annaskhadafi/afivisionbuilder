import os
import shutil
import tempfile
from pathlib import Path
import numpy as np
import pytest

from engine.model_quantizer import (
    generate_synthetic_calibration_dataset,
    quantize_onnx_model,
    quantize_model,
)
from engine.custom_model_runtime import run_custom_model_frame


def test_generate_synthetic_calibration_dataset():
    gen_func = generate_synthetic_calibration_dataset(image_size=320, num_samples=3)
    samples = list(gen_func())
    assert len(samples) == 3
    assert len(samples[0]) == 1
    tensor = samples[0][0]
    assert tensor.shape == (1, 320, 320, 3)
    assert tensor.dtype == np.float32
    assert tensor.min() >= 0.0 and tensor.max() <= 1.0


def test_quantize_onnx_dynamic_integration():
    import onnx
    from onnx import helper, TensorProto

    # Create a tiny dummy ONNX model (MatMul + Add)
    X = helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 16])
    Y = helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 16])

    weight_data = np.random.randn(16, 16).astype(np.float32)
    weight_init = helper.make_tensor(
        name="W",
        data_type=TensorProto.FLOAT,
        dims=[16, 16],
        vals=weight_data.tobytes(),
        raw=True,
    )

    node_def = helper.make_node("MatMul", ["input", "W"], ["output"])
    graph_def = helper.make_graph([node_def], "dummy_graph", [X], [Y], [weight_init])
    model_def = helper.make_model(graph_def, producer_name="afi_test")

    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = Path(tmpdir) / "dummy.onnx"
        out_path = Path(tmpdir) / "dummy_int8.onnx"
        onnx.save(model_def, str(src_path))

        assert src_path.is_file()
        orig_size = src_path.stat().st_size

        quantize_onnx_model(src_path, out_path)
        assert out_path.is_file()
        assert out_path.stat().st_size > 0


def test_quantize_model_api_contract():
    import onnx
    from onnx import helper, TensorProto

    X = helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 8])
    Y = helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 8])
    W = helper.make_tensor("W", TensorProto.FLOAT, [8, 8], np.ones((8, 8), dtype=np.float32).tobytes(), raw=True)
    graph = helper.make_graph([helper.make_node("MatMul", ["input", "W"], ["output"])], "g", [X], [Y], [W])
    model = helper.make_model(graph)

    with tempfile.TemporaryDirectory() as tmpdir:
        src_onnx = Path(tmpdir) / "sample.onnx"
        onnx.save(model, str(src_onnx))

        res = quantize_model(
            source_model_path=str(src_onnx),
            target_format="onnx_int8",
            image_size=320,
            output_dir=tmpdir,
        )

        assert res["success"] is True
        assert res["targetFormat"] == "onnx_int8"
        assert res["engine"] == "onnx_custom"
        assert res["format"] == "onnx"
        assert "quantizedSizeBytes" in res
        assert Path(res["targetPath"]).is_file()
