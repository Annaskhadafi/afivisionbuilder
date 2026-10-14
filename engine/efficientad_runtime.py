"""VisoNode's fixed-shape EfficientAD deployment contract (no Anomalib dependency).

Exports contain embedded metadata and TorchScript weights. Only load artifacts
from trusted training runs. Dense outputs use a JSON-safe representation so the
existing worker, logic and database interfaces retain structured results.
"""
from __future__ import annotations

import base64
import json
import math
import zipfile
from pathlib import Path
from threading import Lock

FORMAT = "visonode.efficientad.torchscript.v1"
ARTIFACT_VERSION = 1
METADATA_FILE = "visonode.json"
INPUT_SIZE = (256, 256)
_cache: dict = {}
_cache_lock = Lock()


def model_path(config: dict) -> Path:
    raw = str(config.get("efficientadModel") or "").strip().strip('"')
    if not raw:
        raise RuntimeError("Select a trained EfficientAD deployment model (.pt) exported from VisoLabel's Visual Inspection project.")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise RuntimeError("EfficientAD model path must be absolute; select it with the model file picker.")
    if path.suffix.lower() != ".pt":
        raise RuntimeError("EfficientAD requires a deployment .pt export. Use Export Model in VisoLabel's Visual Inspection project and select model.pt.")
    if not path.is_file():
        raise RuntimeError(f"EfficientAD model was not found at {path}.")
    return path.resolve()


def finite_number(value, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise RuntimeError(f"EfficientAD {name} must be a finite number.") from exc
    if not math.isfinite(result):
        raise RuntimeError(f"EfficientAD {name} must be a finite number.")
    return result


def validate_metadata(metadata: dict) -> dict:
    if not isinstance(metadata, dict):
        raise RuntimeError("EfficientAD model metadata must be a JSON object.")
    if "format" not in metadata:
        raise RuntimeError("EfficientAD model metadata is missing required field: format.")
    if metadata["format"] != FORMAT:
        raise RuntimeError("Unsupported EfficientAD model format. Select a VisoLabel or VisoNode deployment export.")
    version = metadata.get("artifact_version", ARTIFACT_VERSION)
    if type(version) is not int or version != ARTIFACT_VERSION:
        raise RuntimeError(f"Unsupported EfficientAD artifact version: {version!r}. Supported version: {ARTIFACT_VERSION}.")
    aliases = {"model_type": "efficientad", "task": "anomaly_detection"}
    for key, expected_value in aliases.items():
        if key in metadata and metadata[key] != expected_value:
            raise RuntimeError(f"Incompatible EfficientAD {key}: expected {expected_value!r}.")
    expected = {
        "algorithm": "efficientad", "input_size": list(INPUT_SIZE),
        "color_space": "RGB", "input_range": [0, 1],
        "resize": "bilinear_antialias", "normalization": "inside_model",
        "score_scale": "raw_quantile", "batch_size": 1,
    }
    missing = [key for key in (*expected, "image_threshold", "map_min", "map_max") if key not in metadata]
    if missing:
        raise RuntimeError(f"EfficientAD model metadata is missing required fields: {', '.join(missing)}.")
    if (any(metadata[key] != value for key, value in expected.items())
            or type(metadata["batch_size"]) is not int
            or any(type(value) not in (int, float) for value in metadata["input_range"])):
        raise RuntimeError("Incompatible EfficientAD preprocessing/output contract. Re-export the trained model.")
    for key in ("image_threshold", "map_min", "map_max"):
        if type(metadata[key]) not in (int, float):
            raise RuntimeError(f"EfficientAD metadata {key} must be a finite JSON number.")
    if "model_variant" in metadata and metadata["model_variant"] not in ("small", "medium"):
        raise RuntimeError("Incompatible EfficientAD model_variant: expected 'small' or 'medium'.")
    if "provenance" in metadata and not isinstance(metadata["provenance"], dict):
        raise RuntimeError("EfficientAD model provenance must be a JSON object.")
    threshold = finite_number(metadata.get("image_threshold"), "model threshold")
    low = finite_number(metadata.get("map_min"), "heatmap minimum")
    high = finite_number(metadata.get("map_max"), "heatmap maximum")
    if high <= low:
        raise RuntimeError("EfficientAD heatmap range must have a positive width.")
    return {**metadata, "artifact_version": version, **aliases,
            "image_threshold": threshold, "map_min": low, "map_max": high}


def read_metadata(path: str | Path) -> dict:
    """Read the embedded deployment contract without importing any ML packages.

    This checks the manifest only; the inference loader also validates the graph.
    TorchScript stores extra files beneath its archive root's ``extra/`` folder.
    """
    try:
        with zipfile.ZipFile(path) as archive:
            entries = [info for info in archive.infolist()
                       if info.filename == f"extra/{METADATA_FILE}"
                       or info.filename.endswith(f"/extra/{METADATA_FILE}")]
            if not entries:
                raise RuntimeError(f"EfficientAD model is missing embedded metadata ({METADATA_FILE}). Select a deployment export.")
            if len(entries) != 1:
                raise RuntimeError("EfficientAD model contains conflicting embedded metadata files.")
            try:
                metadata = json.loads(archive.read(entries[0]))
            except (ValueError, UnicodeError) as exc:
                raise RuntimeError(f"EfficientAD embedded metadata ({METADATA_FILE}) is not valid JSON.") from exc
        return validate_metadata(metadata)
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise RuntimeError(f"Could not read EfficientAD model {path}: missing or corrupt deployment file ({exc}).") from exc


def preprocess(frame, device: str = "cpu"):
    import numpy as np
    import torch
    from torchvision.transforms.functional import resize
    from torchvision.transforms import InterpolationMode

    if not isinstance(frame, np.ndarray) or frame.dtype != np.uint8 or frame.size == 0:
        raise RuntimeError("EfficientAD expects a nonempty uint8 BGR or grayscale image.")
    if frame.ndim == 2:
        frame = np.repeat(frame[:, :, None], 3, axis=2)
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise RuntimeError("EfficientAD expects three BGR channels or a grayscale image.")
    # Convert color and dtype in one allocation. These small per-crop operations
    # are faster in NumPy than dispatching separate Torch CPU worker-pool jobs.
    # Use division, not reciprocal multiplication: the latter changes float32
    # rounding for some uint8 values and would alter the export preprocessing.
    rgb = np.ascontiguousarray(frame[:, :, ::-1], dtype=np.float32)
    rgb /= np.float32(255.0)
    tensor = torch.from_numpy(rgb).permute(2, 0, 1)
    tensor = resize(tensor, list(INPUT_SIZE), InterpolationMode.BILINEAR, antialias=True)
    return tensor.unsqueeze(0).to(device)


def validate_prediction(prediction):
    import torch

    if not isinstance(prediction, (tuple, list)) or len(prediction) != 2:
        raise RuntimeError("EfficientAD model must return (anomaly score, anomaly map).")
    score, anomaly_map = prediction
    if (not isinstance(score, torch.Tensor) or score.numel() != 1
            or not isinstance(anomaly_map, torch.Tensor)
            or tuple(anomaly_map.shape) != (1, 1, *INPUT_SIZE)):
        raise RuntimeError("EfficientAD model returned an unsupported score/map shape.")
    # Results must reach the CPU for their JSON-safe map/heatmap payload anyway.
    # Validate after those transfers so each reduction/boolean check does not
    # launch a GPU kernel and synchronize the inference stream independently.
    # Keep the original dtype through validation (notably the score/map tolerance).
    score = score.detach().to(device="cpu")
    anomaly_map = anomaly_map.detach().to(device="cpu")
    if not torch.isfinite(score).all() or not torch.isfinite(anomaly_map).all():
        raise RuntimeError("EfficientAD produced non-finite results; check the model's training/calibration.")
    if not torch.isclose(score.reshape(()), anomaly_map.amax(), rtol=1e-4, atol=1e-6):
        raise RuntimeError("EfficientAD score does not match its anomaly map. Re-export the model.")
    return float(score.item()), anomaly_map.to(dtype=torch.float32)[0, 0].numpy()


class EfficientADRuntime:
    def __init__(self, path: Path, device: str):
        import torch

        extra = {METADATA_FILE: ""}
        try:
            self.metadata = read_metadata(path)
            # TorchScript archives include float64 scalar constants even for an
            # FP32 graph. Loading directly onto MPS transfers those constants,
            # which Metal cannot represent. Load on CPU and move parameters and
            # buffers afterwards; scalar graph constants stay portable.
            self.model = torch.jit.load(str(path), map_location="cpu", _extra_files=extra).to(device).eval()
            if validate_metadata(json.loads(extra[METADATA_FILE])) != self.metadata:
                raise RuntimeError("EfficientAD model metadata changed while loading. Select the model again.")
            self.device = device
            with torch.inference_mode():
                validate_prediction(self.model(torch.zeros((1, 3, *INPUT_SIZE), device=device)))
        except Exception as exc:
            raise RuntimeError(f"Could not load EfficientAD model {path}: {exc}") from exc

    def predict(self, frame):
        import torch

        tensor = preprocess(frame, self.device)
        try:
            with torch.inference_mode():
                return validate_prediction(self.model(tensor))
        except Exception as exc:
            raise RuntimeError(f"EfficientAD inference failed on {self.device}: {exc}") from exc


def load_model(config: dict, device: str = "cpu") -> EfficientADRuntime:
    path = model_path(config)
    stat = path.stat()
    key = (str(path), stat.st_mtime_ns, stat.st_size, device)
    with _cache_lock:
        if key not in _cache:
            runtime = EfficientADRuntime(path, device)
            # Evict older revisions of this path/device without retaining their GPU memory.
            for previous in list(_cache):
                if previous[0] == str(path) and previous[-1] == device:
                    del _cache[previous]
            _cache[key] = runtime
        return _cache[key]


def encode_map(anomaly_map) -> dict:
    import numpy as np

    array = np.asarray(anomaly_map, dtype="<f4")
    return {
        "encoding": "base64", "dtype": "float32-le", "shape": list(array.shape),
        "data": base64.b64encode(array.tobytes()).decode("ascii"),
    }


def decode_map(payload: dict):
    """Return a numerical HxW map for downstream consumers (model coordinates)."""
    import numpy as np

    if (payload.get("encoding") != "base64" or payload.get("dtype") != "float32-le"
            or payload.get("shape") != list(INPUT_SIZE)):
        raise RuntimeError("Unsupported EfficientAD anomaly map encoding.")
    raw = base64.b64decode(payload["data"], validate=True)
    return np.frombuffer(raw, dtype="<f4").reshape(INPUT_SIZE)


def heatmap_image(anomaly_map, metadata: dict):
    import cv2
    import numpy as np

    scaled = (anomaly_map - metadata["map_min"]) / (metadata["map_max"] - metadata["map_min"])
    return cv2.applyColorMap((np.clip(scaled, 0, 1) * 255).astype(np.uint8), cv2.COLORMAP_JET)


def run_batch(frames: list, node: dict, device: str) -> list[list[dict]]:
    import cv2

    if not frames:
        return []
    config = node.get("config", {})
    runtime = load_model(config, device)
    metadata = runtime.metadata
    threshold = metadata["image_threshold"] if config.get("useModelThreshold", True) else finite_number(
        config.get("anomalyThreshold"), "threshold",
    )
    opacity = finite_number(config.get("heatmapOpacity", 0.35), "heatmap opacity")
    if not 0 <= opacity <= 1:
        raise RuntimeError("EfficientAD heatmap opacity must be between 0 and 1.")
    results = []
    # The deployment graph deliberately supports one image at a time. The runner
    # may still group frames; never drop or reuse predictions within a group.
    for frame in frames:
        score, anomaly_map = runtime.predict(frame)
        is_anomaly = score >= threshold
        heatmap = heatmap_image(anomaly_map, metadata)
        encoded, png = cv2.imencode(".png", heatmap)
        if not encoded:
            raise RuntimeError("EfficientAD could not encode its heatmap.")
        results.append([{
            "kind": "anomaly", "sourceNodeId": str(node.get("id") or "efficientad"),
            "class": "NG" if is_anomaly else "OK", "classId": int(is_anomaly),
            "result": "NG" if is_anomaly else "OK", "isAnomaly": is_anomaly,
            "score": score, "anomalyScore": score, "threshold": threshold,
            "scoreScale": "raw_quantile", "imageShape": list(frame.shape[:2]),
            "anomalyMap": encode_map(anomaly_map),
            "heatmap": {"encoding": "base64-png", "data": base64.b64encode(png).decode("ascii")},
            "mapRange": [metadata["map_min"], metadata["map_max"]],
            "showHeatmap": bool(config.get("showHeatmap", True)), "heatmapOpacity": opacity,
        }])
    return results


def draw_result(frame, result: dict, *, show_labels: bool, y: int = 12,
                show_boxes: bool = True, show_track_ids: bool = True) -> int:
    import cv2

    bounds = result.get("cropBounds")
    x0, y0, width, height = 0, 0, frame.shape[1], frame.shape[0]
    if bounds is not None:
        # Crop coordinates refer to the actual padded/squared model input, not
        # the detector's (potentially smaller) object bounding box.
        try:
            x0, y0, width, height = (int(value) for value in bounds)
        except (TypeError, ValueError, OverflowError):
            return y
        if width <= 0 or height <= 0:
            return y
    left, top = max(0, x0), max(0, y0)
    right, bottom = min(frame.shape[1], x0 + width), min(frame.shape[0], y0 + height)
    if right <= left or bottom <= top:
        return y
    roi = frame[top:bottom, left:right]
    if result.get("showHeatmap", True):
        heatmap = heatmap_image(decode_map(result["anomalyMap"]), {
            "map_min": result["mapRange"][0], "map_max": result["mapRange"][1],
        })
        heatmap = cv2.resize(heatmap, (width, height), interpolation=cv2.INTER_LINEAR)
        heatmap = heatmap[top - y0:bottom - y0, left - x0:right - x0]
        opacity = result["heatmapOpacity"]
        cv2.addWeighted(heatmap, opacity, roi, 1 - opacity, 0, dst=roi)
    color = (40, 50, 230) if result["isAnomaly"] else (40, 180, 40)
    if bounds is not None and show_boxes:
        # Draw inside the crop so adjacent objects/background remain untouched.
        cv2.rectangle(roi, (0, 0), (roi.shape[1] - 1, roi.shape[0] - 1), color, 1)
    if show_labels:
        label = f"{result['result']}  anomaly {result['anomalyScore']:.4f}  threshold {result['threshold']:.4f}"
        if bounds is not None:
            identity = result.get("trackId")
            if show_track_ids and identity is not None:
                label = f"#{identity} {label}"
            size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(roi, (0, 0), (min(roi.shape[1] - 1, size[0] + 8), size[1] + 10), color, -1)
            cv2.putText(roi, label, (4, size[1] + 3), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            return y
        size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.rectangle(frame, (8, y), (min(frame.shape[1] - 1, size[0] + 20), y + size[1] + 14), color, -1)
        cv2.putText(frame, label, (12, y + size[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        y += size[1] + 22
    return y
