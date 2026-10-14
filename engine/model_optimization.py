"""Model conversion in the isolated AI interpreter; imports commit only on success."""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def _class_labels(value) -> list[str]:
    """Normalize exported labels while retaining their numeric class positions."""
    if isinstance(value, dict):
        try:
            indexed = {int(key): str(label).strip() for key, label in value.items()}
        except (ValueError, TypeError) as exc:
            raise ValueError("Model class labels must use numeric class IDs.") from exc
        if any(index < 0 or index > 100000 for index in indexed):
            raise ValueError("Model class IDs are outside the supported range.")
        return [indexed.get(index) or str(index) for index in range(max(indexed, default=-1) + 1)]
    if isinstance(value, str):
        value = value.replace(",", "\n").splitlines()
    if isinstance(value, (list, tuple)):
        return [str(label).strip() if label is not None and str(label).strip() else str(index)
                for index, label in enumerate(value)]
    if value is None:
        return []
    raise ValueError("Model class labels must be text, a list, or a numeric ID mapping.")


def optimization_unavailable_reason(record: dict, target: str) -> str:
    if target not in ("cpu", "gpu"):
        return "Select CPU or GPU optimization."
    if not record.get("available", True) or not Path(record.get("path", "")).is_file():
        return "The source model file is unavailable."
    if record.get("node_type") not in ("detector", "segmenter"):
        return "Optimization currently supports RF-DETR detection and segmentation models."
    engine = record.get("engine")
    if engine == "rfdetr_onnx" and target == "cpu":
        return "This model is already in ONNX format for CPU inference."
    if engine == "rfdetr_tensorrt":
        return "Use the original PyTorch or ONNX model to create an optimized variant."
    if engine not in ("rfdetr", "rfdetr_onnx"):
        return "Optimization currently supports RF-DETR detection and segmentation models."
    return ""


def _rfdetr_export_class_labels(model) -> list[str]:
    names = getattr(model, "class_names", {}) or {}
    classes = _class_labels(names)
    args = getattr(getattr(model, "model", None), "args", None)
    # RF-DETR exposes 80 compact names for pretrained COCO, but exports logits
    # indexed by sparse category IDs 1..90. Match its predict() label mapping.
    if isinstance(names, (list, tuple)) and getattr(args, "num_classes", 0) > len(classes):
        from rfdetr.assets.coco_classes import COCO_CLASSES, COCO_CLASS_NAMES

        if classes == list(COCO_CLASS_NAMES):
            return _class_labels(COCO_CLASSES)
    return classes


def optimize_model(store, record: dict, target: str, on_log=None) -> dict:
    """Blocking operation intended for a GUI worker, preserving the original model."""
    reason = optimization_unavailable_reason(record, target)
    if reason:
        raise ValueError(reason)
    from ai_process import ROOT, ensure_ai_python, _prepare_worker_source, _ai_subprocess_env, _ai_subprocess_cwd

    # Validate and repair the isolated runtime before launching the exporter.
    # Older environments may support inference but lack ONNX export libraries.
    python = ensure_ai_python(on_log=on_log)
    worker_root = _prepare_worker_source()
    with tempfile.TemporaryDirectory(prefix="visonode-optimize-") as temporary:
        directory = Path(temporary)
        script = directory / "model_optimization.py"
        shutil.copy2(ROOT / "model_optimization.py", script)
        request = directory / "request.json"
        request.write_text(json.dumps({"record": record, "target": target}), encoding="utf-8")
        bootstrap = (
            "import runpy,sys; "
            "i=next((i for i,p in enumerate(sys.path) if 'site-packages' in p),len(sys.path)); "
            f"sys.path.insert(i,{str(worker_root)!r}); "
            f"sys.argv=[{str(script)!r},{str(request)!r}]; "
            f"runpy.run_path({str(script)!r},run_name='__main__')"
        )
        process = subprocess.Popen(
            [str(python), "-I", "-u", "-c", bootstrap],
            cwd=_ai_subprocess_cwd(python), env=_ai_subprocess_env(),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        tail = deque(maxlen=100)
        try:
            while chunk := process.stdout.readline(4096):
                tail.append(chunk)
                if on_log and chunk.strip():
                    on_log(chunk.rstrip())
            returncode = process.wait()
        except BaseException:
            process.kill()
            process.wait()
            raise
        finally:
            process.stdout.close()
        if returncode:
            detail = "".join(tail).strip()[-4000:]
            raise RuntimeError("Model optimization failed. The original model is unchanged.\n" + detail)
        metadata = json.loads((directory / "result.json").read_text(encoding="utf-8"))
        artifact = directory / ("optimized.onnx" if target == "cpu" else "optimized.engine")
        if not artifact.is_file() or not artifact.stat().st_size:
            raise RuntimeError("Conversion did not produce a model.")
        engine = "rfdetr_onnx" if target == "cpu" else "rfdetr_tensorrt"
        key = "rfdetrOnnxClasses" if target == "cpu" else "rfdetrTensorRTClasses"
        optimized_config = {key: "\n".join(_class_labels(metadata["classes"])),
                            "optimizedFrom": record.get("id"), "optimizationTarget": target}
        if target == "gpu" and metadata.get("rfdetrTensorRTCudaGraph"):
            optimized_config["rfdetrTensorRTCudaGraph"] = True
        return store.import_model(
            artifact, name=f"{record['name']} · {'CPU ONNX' if target == 'cpu' else 'GPU TensorRT'}",
            node_type=record["node_type"], engine=engine, version=record.get("version", ""),
            config=optimized_config,
        )


def _build_tensorrt(onnx_path: Path, output: Path, *, aux_streams: int | None = None) -> None:
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("GPU optimization requires an NVIDIA GPU with CUDA and TensorRT installed.")
    import tensorrt as trt
    logger = trt.Logger(trt.Logger.WARNING)
    builder = trt.Builder(logger)
    # TensorRT 11 removed EXPLICIT_BATCH; all networks now use explicit batch.
    explicit_batch = getattr(trt.NetworkDefinitionCreationFlag, "EXPLICIT_BATCH", None)
    network = builder.create_network(0 if explicit_batch is None else 1 << int(explicit_batch))
    parser = trt.OnnxParser(network, logger)
    if not parser.parse_from_file(str(onnx_path)):
        raise RuntimeError("TensorRT could not parse the model: " + "\n".join(str(parser.get_error(i)) for i in range(parser.num_errors)))
    for index in range(network.num_inputs):
        if any(int(size) <= 0 for size in network.get_input(index).shape):
            raise ValueError("GPU optimization requires a fixed-shape ONNX model. Optimize the original PyTorch checkpoint instead.")
    config = builder.create_builder_config()
    if aux_streams is not None:
        config.max_aux_streams = aux_streams
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 2 << 30)
    # Keep FP32 by default: RF-DETR attention/normalization can lose accuracy in FP16.
    serialized = builder.build_serialized_network(network, config)
    if serialized is None:
        raise RuntimeError("TensorRT could not build this model for the current GPU.")
    runtime = trt.Runtime(logger)
    if runtime.deserialize_cuda_engine(serialized) is None:
        raise RuntimeError("TensorRT could not validate the converted engine.")
    output.write_bytes(bytes(serialized))


def _convert(request_path: Path) -> None:
    import onnx
    import onnxruntime as ort
    request = json.loads(request_path.read_text(encoding="utf-8"))
    record, target = request["record"], request["target"]
    directory = request_path.parent
    source = Path(record["path"])
    classes = _class_labels(record.get("config", {}).get("rfdetrOnnxClasses", []))
    if record["engine"] == "rfdetr":
        from main import load_rfdetr_model
        settings = record.get("config", {})
        model = load_rfdetr_model(
            settings.get("rfdetrModel", "rfdetr-nano"), device="cpu", checkpoint_path=source,
            inference_size=settings.get("rfdetrImageSize", 0), half_precision=False,
            expected_node_type=record["node_type"],
        )
        classes = _rfdetr_export_class_labels(model)
        print("Exporting full RF-DETR model to ONNX...", flush=True)
        model.export(output_dir=str(directory), backbone_only=False, batch_size=1, dynamic_batch=False)
        candidates = list(directory.glob("*.onnx"))
        if len(candidates) != 1:
            raise RuntimeError("RF-DETR did not produce a unique ONNX artifact.")
        source = candidates[0]
    graph = onnx.load(str(source), load_external_data=True)
    onnx.checker.check_model(graph)
    metadata = {item.key: item.value for item in graph.metadata_props}
    if not classes and metadata.get("visonode.classes"):
        classes = _class_labels(json.loads(metadata["visonode.classes"]))
    metadata.update({"visonode.task": record["node_type"], "visonode.classes": json.dumps(classes)})
    onnx.helper.set_model_props(graph, metadata)
    output = directory / "optimized.onnx"
    onnx.save_model(graph, str(output), save_as_external_data=False)
    # Verify compatibility with the actual CPU execution provider before import.
    session = ort.InferenceSession(str(output), providers=["CPUExecutionProvider"])
    import numpy as np
    inputs = session.get_inputs()
    if len(inputs) != 1 or len(inputs[0].shape) != 4 or any(not isinstance(size, int) or size <= 0 for size in inputs[0].shape):
        raise ValueError("Optimization requires a fixed-shape, single-input RF-DETR ONNX graph.")
    dtype = {"tensor(float)": np.float32, "tensor(float16)": np.float16}.get(inputs[0].type)
    if dtype is None:
        raise ValueError("Unsupported ONNX input type.")
    outputs = session.run(None, {inputs[0].name: np.zeros(inputs[0].shape, dtype=dtype)})
    names = {value.name for value in session.get_outputs()}
    required = {"dets", "labels", "masks"} if record["node_type"] == "segmenter" else {"dets", "labels"}
    if not required.issubset(names):
        raise ValueError("The exported graph is missing RF-DETR task outputs: " + ", ".join(sorted(required - names)))
    if not all(np.isfinite(value).all() for value in outputs):
        raise RuntimeError("Converted model produced non-finite predictions during validation.")
    if target == "gpu":
        from rfdetr_onnx_optimization import fold_rfdetr_spatial_shapes
        folded, folding = fold_rfdetr_spatial_shapes(graph)
        if folding["folded"]:
            print("Folding constant RF-DETR spatial shapes to remove GPU/CPU shape synchronization...", flush=True)
            validation_options = ort.SessionOptions()
            validation_options.intra_op_num_threads = 2
            folded_session = ort.InferenceSession(folded.SerializeToString(), sess_options=validation_options,
                                                  providers=["CPUExecutionProvider"])
            # Validate exact CPU predictions before building a new GPU engine.
            # The dependency proof establishes constancy; inputs guard integration.
            samples = [np.zeros(inputs[0].shape, dtype=dtype),
                       np.random.default_rng(42).random(inputs[0].shape).astype(dtype)]
            for sample in samples:
                reference = session.run(None, {inputs[0].name: sample})
                optimized = folded_session.run(None, {inputs[0].name: sample})
                if len(reference) != len(optimized) or any(not np.array_equal(a, b) for a, b in zip(reference, optimized)):
                    raise RuntimeError("RF-DETR spatial-shape folding changed CPU predictions; conversion cancelled.")
            onnx.save_model(folded, str(output), save_as_external_data=False)
        print("Building TensorRT engine for the current GPU...", flush=True)
        _build_tensorrt(output, directory / "optimized.engine", aux_streams=0 if folding["folded"] else None)
    result = {"classes": classes}
    if target == "gpu":
        result.update(spatialShapeOptimization=folding, rfdetrTensorRTCudaGraph=folding["folded"])
    (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")


if __name__ == "__main__":
    try:
        _convert(Path(sys.argv[1]))
    except ImportError as exc:
        raise RuntimeError("Model export dependencies are missing. Install or repair AI Libraries (RF-DETR ONNX export, ONNX Runtime; TensorRT for GPU). " + str(exc)) from exc
