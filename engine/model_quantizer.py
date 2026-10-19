"""Model Quantizer and Optimizer Engine for AFI Vision Builder.

Supports converting PyTorch (.pt), ONNX (.onnx), and Keras/TensorFlow models
into lightweight quantized formats:
  - TFLite INT8 (Post-training integer 8-bit quantization)
  - TFLite FP16 (Half-precision 16-bit float)
  - ONNX Dynamic INT8 (Quantized weights for high CPU throughput)
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Callable, Generator, Optional

logger = logging.getLogger("model_quantizer")

DATA_MODELS_DIR = Path(__file__).resolve().parent.parent / "data" / "models"


def resolve_model_path(raw_path: str) -> Path:
    p = Path(raw_path).expanduser()
    if p.is_file():
        return p.resolve()
    candidate = DATA_MODELS_DIR / raw_path
    if candidate.is_file():
        return candidate.resolve()
    # Try searching for filename in DATA_MODELS_DIR
    for item in DATA_MODELS_DIR.iterdir():
        if item.is_file() and item.name.lower() == Path(raw_path).name.lower():
            return item.resolve()
    raise FileNotFoundError(f"Model file not found: {raw_path}")


def generate_synthetic_calibration_dataset(
    image_size: int = 640, num_samples: int = 10
) -> Callable[[], Generator[list[Any], None, None]]:
    """Generates synthetic normalized image tensor generator for full integer INT8 calibration."""
    import numpy as np

    def representative_dataset():
        for _ in range(num_samples):
            # Normal distribution with pixel range 0.0 - 1.0 (RGB)
            data = np.random.uniform(0.0, 1.0, size=(1, image_size, image_size, 3)).astype(np.float32)
            yield [data]

    return representative_dataset


def quantize_onnx_model(
    source_path: Path, output_path: Path, target_format: str = "onnx_int8"
) -> Path:
    """Quantize an ONNX model to INT8 using ONNX Runtime quantization."""
    from onnxruntime.quantization import QuantType, quantize_dynamic

    output_path.parent.mkdir(parents=True, exist_ok=True)
    quantize_dynamic(
        model_input=str(source_path),
        model_output=str(output_path),
        weight_type=QuantType.QInt8,
    )
    return output_path


def quantize_ultralytics_model(
    source_path: Path,
    output_dir: Path,
    target_format: str = "tflite_int8",
    image_size: int = 640,
) -> Path:
    """Export and quantize Ultralytics YOLO models to TFLite INT8/FP16 or ONNX INT8."""
    from ultralytics import YOLO

    model = YOLO(str(source_path))
    stem = source_path.stem

    if target_format == "tflite_int8":
        exported = model.export(format="tflite", int8=True, imgsz=image_size)
        target_name = f"{stem}_int8.tflite"
    elif target_format == "tflite_fp16":
        exported = model.export(format="tflite", half=True, imgsz=image_size)
        target_name = f"{stem}_fp16.tflite"
    elif target_format == "onnx_int8":
        exported_onnx = model.export(format="onnx", imgsz=image_size)
        exported_path = Path(str(exported_onnx))
        target_file = output_dir / f"{stem}_int8.onnx"
        return quantize_onnx_model(exported_path, target_file, target_format="onnx_int8")
    else:
        raise ValueError(f"Unsupported target format: {target_format}")

    # Locate the produced .tflite file from the export result
    exp_path = Path(str(exported))
    found_tflite: Optional[Path] = None

    if exp_path.is_file() and exp_path.suffix.lower() == ".tflite":
        found_tflite = exp_path
    elif exp_path.is_dir():
        # Search inside directory (Ultralytics sometimes saves in <stem>_saved_model/)
        tflite_files = list(exp_path.glob("*.tflite"))
        if tflite_files:
            # Pick the int8/fp16 file or latest
            found_tflite = tflite_files[0]
            for f in tflite_files:
                if "int8" in f.name.lower() and "int8" in target_format:
                    found_tflite = f
                    break
                elif ("half" in f.name.lower() or "float16" in f.name.lower()) and "fp16" in target_format:
                    found_tflite = f
                    break
    if not found_tflite or not found_tflite.is_file():
        # Search adjacent directory
        candidate_dir = source_path.parent / f"{stem}_saved_model"
        if candidate_dir.is_dir():
            tflites = list(candidate_dir.glob("*.tflite"))
            if tflites:
                found_tflite = tflites[0]

    if not found_tflite or not found_tflite.is_file():
        raise RuntimeError(f"Export completed but .tflite file could not be located from {exported}")

    dest_file = output_dir / target_name
    shutil.copy2(str(found_tflite), str(dest_file))
    return dest_file


def quantize_keras_model(
    source_path: Path,
    output_path: Path,
    target_format: str = "tflite_int8",
    image_size: int = 640,
) -> Path:
    """Convert and quantize Keras/TensorFlow model to TFLite."""
    import tensorflow as tf

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.suffix.lower() in (".keras", ".h5"):
        model = tf.keras.models.load_model(str(source_path))
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
    elif source_path.is_dir():
        converter = tf.lite.TFLiteConverter.from_saved_model(str(source_path))
    else:
        raise ValueError(f"Cannot load TF/Keras model from {source_path}")

    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    if target_format == "tflite_fp16":
        converter.target_spec.supported_types = [tf.float16]
    elif target_format == "tflite_int8":
        converter.representative_dataset = generate_synthetic_calibration_dataset(image_size)
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.uint8
        converter.inference_output_type = tf.uint8

    tflite_quant_model = converter.convert()
    with open(output_path, "wb") as f:
        f.write(tflite_quant_model)
    return output_path


def quantize_model(
    source_model_path: str,
    target_format: str = "tflite_int8",
    image_size: int = 640,
    output_dir: Optional[str] = None,
) -> dict[str, Any]:
    """Universal model quantizer entry point.

    Args:
        source_model_path: Path to .pt, .onnx, or .keras file.
        target_format: 'tflite_int8', 'tflite_fp16', or 'onnx_int8'.
        image_size: Model input spatial resolution (default 640).
        output_dir: Destination directory (default data/models).

    Returns:
        Dictionary with compression metrics and output metadata.
    """
    target_format = target_format.lower().strip()
    if target_format not in ("tflite_int8", "tflite_fp16", "onnx_int8"):
        raise ValueError(f"Invalid targetFormat '{target_format}'. Choose tflite_int8, tflite_fp16, or onnx_int8.")

    source_path = resolve_model_path(source_model_path)
    out_dir = Path(output_dir).resolve() if output_dir else DATA_MODELS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    orig_size = source_path.stat().st_size
    suffix = source_path.suffix.lower()
    stem = source_path.stem

    logger.info("Starting quantization: %s -> %s (imgsz=%d)", source_path.name, target_format, image_size)

    if suffix in (".pt", ".pth"):
        target_file = quantize_ultralytics_model(
            source_path, out_dir, target_format=target_format, image_size=image_size
        )
    elif suffix == ".onnx":
        if target_format == "onnx_int8":
            target_name = f"{stem}_int8.onnx"
            target_file = quantize_onnx_model(source_path, out_dir / target_name, target_format)
        else:
            # ONNX to TFLite: try converting via ONNX or fallback
            raise ValueError(f"Converting .onnx to {target_format} is not supported directly. Use onnx_int8.")
    elif suffix in (".keras", ".h5") or source_path.is_dir():
        ext = ".tflite" if "tflite" in target_format else ".onnx"
        fmt_suffix = "int8" if "int8" in target_format else "fp16"
        target_file = quantize_keras_model(
            source_path, out_dir / f"{stem}_{fmt_suffix}{ext}", target_format, image_size
        )
    else:
        raise ValueError(f"Unsupported input model format '{suffix}'. Supported: .pt, .onnx, .keras, .h5")

    quant_size = target_file.stat().st_size
    saved_bytes = max(0, orig_size - quant_size)
    saved_percent = round((saved_bytes / orig_size) * 100, 1) if orig_size > 0 else 0.0
    ratio = f"{(orig_size / quant_size):.1f}x" if quant_size > 0 else "1.0x"

    engine = "tflite" if target_file.suffix.lower() == ".tflite" else "onnx_custom"

    result = {
        "success": True,
        "sourcePath": str(source_path),
        "sourceName": source_path.name,
        "targetPath": str(target_file),
        "targetName": target_file.name,
        "targetFormat": target_format,
        "engine": engine,
        "format": target_file.suffix.lower().lstrip("."),
        "imageSize": image_size,
        "originalSizeBytes": orig_size,
        "quantizedSizeBytes": quant_size,
        "savedBytes": saved_bytes,
        "savedPercent": saved_percent,
        "compressionRatio": ratio,
        "originalSizeFormatted": f"{orig_size / (1024 * 1024):.1f} MB",
        "quantizedSizeFormatted": f"{quant_size / (1024 * 1024):.1f} MB",
    }
    logger.info(
        "Quantization successful: %s (%s) -> %s (%s, %s saved)",
        source_path.name,
        result["originalSizeFormatted"],
        target_file.name,
        result["quantizedSizeFormatted"],
        f"-{saved_percent}%",
    )
    return result
