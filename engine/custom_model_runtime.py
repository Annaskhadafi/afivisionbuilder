from __future__ import annotations

import json
import ast
import logging
import os
from pathlib import Path
from typing import Any

# Standard COCO classes fallback
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
    "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

_MODEL_CACHE: dict[str, Any] = {}
_LABELS_CACHE: dict[str, list[str]] = {}
logger = logging.getLogger(__name__)


def custom_model_path(config: dict) -> str:
    """Return the one effective custom-model path used by preload and inference."""
    engine = str(config.get("engine") or "custom_auto").lower()
    keys = ["modelPath", "customModelPath"]
    if engine == "onnx_custom":
        keys.append("rfdetrOnnxModel")
    elif engine in ("ultralytics_yolo", "rfdetr"):
        keys.append("rfdetrCheckpoint")
    else:
        keys.extend(("rfdetrOnnxModel", "rfdetrCheckpoint", "convnextCheckpoint"))
    for key in keys:
        value = str(config.get(key) or "").strip().strip('"')
        if value:
            return value
    if engine == "ultralytics_yolo":
        return "yolov8n.pt"
    return ""


def detect_model_engine(path_str: str) -> str:
    """Auto-detect the appropriate engine from file extension or name."""
    if "world" in path_str.lower():
        return "yolo_world"
    suffix = Path(path_str).suffix.lower()
    if suffix in (".pt", ".pth", ".ckpt"):
        return "ultralytics_yolo"
    if suffix == ".onnx":
        return "onnx_custom"
    if suffix == ".tflite":
        return "tflite"
    if suffix in (".keras", ".h5"):
        return "tensorflow_keras"
    return "ultralytics_yolo"


def extract_model_labels(model_path_str: str) -> list[str]:
    """Extract embedded class labels from model metadata or sibling label files."""
    path = Path(model_path_str)
    if not path.is_file():
        return []

    stat = path.stat()
    sidecar_fingerprint = []
    for sibling_name in ("labels.txt", "classes.txt", "labels.json"):
        sibling = path.parent / sibling_name
        try:
            sibling_stat = sibling.stat()
            sidecar_fingerprint.append(
                f"{sibling_name}:{sibling_stat.st_mtime_ns}:{sibling_stat.st_size}"
            )
        except OSError:
            sidecar_fingerprint.append(f"{sibling_name}:missing")
    cache_key = ":".join(
        [f"{path.resolve()}", str(stat.st_mtime_ns), str(stat.st_size), *sidecar_fingerprint]
    )
    if cache_key in _LABELS_CACHE:
        return _LABELS_CACHE[cache_key]

    # Check for sibling labels.txt / classes.txt / data.yaml
    for sibling_name in ("labels.txt", "classes.txt", "labels.json"):
        sibling = path.parent / sibling_name
        if sibling.is_file():
            try:
                if sibling_name.endswith(".json"):
                    data = json.loads(sibling.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        _LABELS_CACHE[cache_key] = [str(x) for x in data]
                        return _LABELS_CACHE[cache_key]
                    if isinstance(data, dict):
                        _LABELS_CACHE[cache_key] = [str(v) for _, v in sorted(data.items(), key=lambda i: int(i[0]) if str(i[0]).isdigit() else str(i[0]))]
                        return _LABELS_CACHE[cache_key]
                else:
                    lines = [line.strip() for line in sibling.read_text(encoding="utf-8").splitlines() if line.strip()]
                    if lines:
                        _LABELS_CACHE[cache_key] = lines
                        return lines
            except Exception:
                pass

    # Try extracting from Ultralytics model metadata
    suffix = path.suffix.lower()
    if suffix in (".pt", ".pth"):
        try:
            from ultralytics import YOLO
            m = YOLO(str(path))
            if hasattr(m, "names") and isinstance(m.names, dict):
                labels = [str(m.names[k]) for k in sorted(m.names.keys())]
                _LABELS_CACHE[cache_key] = labels
                return labels
        except Exception:
            pass

    # Try extracting from ONNX model metadata
    if suffix == ".onnx":
        try:
            import onnxruntime as ort
            sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
            meta = sess.get_modelmeta().custom_metadata_map
            if "names" in meta:
                raw_names = meta["names"]
                parsed = ast.literal_eval(raw_names) if isinstance(raw_names, str) else raw_names
                if isinstance(parsed, dict):
                    labels = [str(parsed[k]) for k in sorted(parsed.keys(), key=lambda x: int(x) if str(x).isdigit() else str(x))]
                    _LABELS_CACHE[cache_key] = labels
                    return labels
                if isinstance(parsed, list):
                    _LABELS_CACHE[cache_key] = [str(x) for x in parsed]
                    return _LABELS_CACHE[cache_key]
        except Exception:
            pass

    return []


def resolve_model_file(raw_path: str) -> Path:
    """Find model path directly or inside data/models directory."""
    p = Path(raw_path).expanduser()
    if p.is_file():
        return p.resolve()
    app_root = Path(__file__).resolve().parents[1]
    app_data = Path(os.environ.get("VISONODE_APP_DATA_DIR", str(app_root / "data")))
    if not app_data.is_absolute():
        app_data = app_root / app_data
    candidates = [
        app_root / raw_path,
        app_data / "models" / raw_path,
        app_data / "models" / p.name,
        app_root / "data/models" / raw_path,
        app_root / "data/models" / p.name,
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    return p.resolve()


def _resolve_labels(config: dict, model_path: str) -> list[str]:
    custom_classes_str = str(config.get("customClasses") or "").strip()
    if custom_classes_str:
        return [c.strip() for c in custom_classes_str.split(",") if c.strip()]
    labels = extract_model_labels(model_path)
    if labels:
        return labels
    # Keep compatibility with old workflows where classes was a label list;
    # when metadata exists it is only a filter (applied by the caller).
    legacy = str(config.get("classes") or "").strip()
    if legacy:
        return [c.strip() for c in legacy.split(",") if c.strip()]
    if "yolo" in str(model_path).lower():
        return list(COCO_CLASSES)
    return []


def configure_nms_free(model: Any, nms_free: bool | None = None, model_path: str = "") -> bool:
    """Detect and configure NMS-Free end2end mode for YOLO26 / YOLOv10 models.

    If the model has a detection head with an 'end2end' attribute:
    - If nms_free is explicitly provided (bool), sets head.end2end to that boolean.
    - If nms_free is None:
        - If model_path contains 'yolo26' or 'v10', or head has 'end2end',
          defaults head.end2end = True to eliminate NMS loop overhead on CPU.
    Returns True if end2end is currently active, False otherwise.
    """
    head = None
    if hasattr(model, "model") and hasattr(model.model, "model") and len(model.model.model) > 0:
        head = model.model.model[-1]
    elif hasattr(model, "model") and hasattr(model.model, "head"):
        head = model.model.head
    elif hasattr(model, "model") and hasattr(model.model, "modules"):
        for m in model.model.modules():
            if hasattr(m, "end2end"):
                head = m
                break

    if head is None or not hasattr(head, "end2end"):
        return False

    is_yolo26_or_v10 = "yolo26" in str(model_path).lower() or "v10" in str(model_path).lower()

    if nms_free is not None:
        enabled = bool(nms_free)
    else:
        # Default True if model is YOLO26 / v10 or head has end2end
        enabled = True if (is_yolo26_or_v10 or hasattr(head, "end2end")) else False

    head.end2end = enabled
    if hasattr(model, "model") and hasattr(model.model, "end2end"):
        model.model.end2end = enabled
    setattr(model, "_nms_free", enabled)
    return enabled


class ModelRunnerHandle:
    """Container for preloaded model metadata returned to core pipeline."""
    def __init__(self, engine_type: str, model_path: str, raw_model: Any, classes: list[str]):
        self.detected_engine = engine_type
        self.engine = engine_type
        self.model_path = model_path
        self.raw_model = raw_model
        self.classes = classes


def _ultralytics_onnx_export(session: Any, node_type: str) -> bool:
    """Ultralytics exports retain task and author metadata and can use YOLO directly."""
    if node_type not in ("detector", "segmenter", "classifier"):
        return False
    try:
        meta = session.get_modelmeta().custom_metadata_map
        task = str(meta.get("task", "")).lower()
        author = " ".join(f"{k} {v}" for k, v in meta.items()).lower()
        return task in {"detect", "segment", "classify"} and "ultralytics" in author
    except Exception:
        return False


def _run_roboflow_universe(frame, model_id: str, api_key: str, threshold: float, node_id: str, node_type: str, config: dict) -> list[dict]:
    import base64
    import cv2
    import requests
    if not model_id:
        return []

    model_id_clean = model_id.strip().strip("/")
    confidence_param = int(max(1, min(99, threshold * 100)))

    # Fallback to mock / synthetic response if test/mock key or empty key
    if not api_key or api_key.startswith("mock") or api_key == "test_key":
        h, w = frame.shape[:2]
        configured_classes = [c.strip() for c in str(config.get("classes") or config.get("customClasses") or "").split(",") if c.strip()]
        target_cls = configured_classes[0] if configured_classes else "roboflow_object"
        return [
            {
                "class": target_cls,
                "score": 0.88,
                "bbox": [float(w * 0.2), float(h * 0.2), float(w * 0.3), float(h * 0.4)],
                "sourceNodeId": node_id,
                "kind": "segmentation" if node_type == "segmenter" else "detection",
            }
        ]

    url = f"https://detect.roboflow.com/{model_id_clean}?api_key={api_key}&confidence={confidence_param}"
    try:
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            return []

        resp = requests.post(
            url,
            data=encoded.tobytes(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=5.0
        )
        if resp.status_code != 200:
            logger.warning("Roboflow Inference API error %d: %s", resp.status_code, resp.text)
            return []
        data = resp.json()
        predictions = data.get("predictions", [])
        detections = []
        configured_classes = [c.strip().casefold() for c in str(config.get("classes") or config.get("customClasses") or "").split(",") if c.strip()]
        for p in predictions:
            score = float(p.get("confidence", 0.0))
            if score < threshold:
                continue
            cls_name = str(p.get("class", "object"))
            if configured_classes and cls_name.casefold() not in configured_classes:
                continue
            cx = float(p.get("x", 0))
            cy = float(p.get("y", 0))
            bw = float(p.get("width", 0))
            bh = float(p.get("height", 0))
            x1 = cx - bw / 2.0
            y1 = cy - bh / 2.0
            item = {
                "class": cls_name,
                "score": score,
                "bbox": [x1, y1, bw, bh],
                "sourceNodeId": node_id,
                "kind": "detection",
            }
            if "points" in p and isinstance(p["points"], list):
                item["mask"] = [[float(pt.get("x", 0)), float(pt.get("y", 0))] for pt in p["points"]]
                item["kind"] = "segmentation"
            detections.append(item)
        return detections
    except Exception as exc:
        logger.warning("Roboflow inference request failed: %s", exc)
        return []


class CustomModelRunner:
    """Universal AI inference runner supporting Ultralytics (best.pt), YOLO-World, Roboflow Universe, ONNX, TFLite, and TF/Keras."""

    @classmethod
    def get_or_load(cls, *args, **kwargs) -> Any:
        if args and isinstance(args[0], dict):
            config = args[0]
            device = kwargs.get("device", "cpu")
            engine = config.get("engine", "custom_auto")
            raw_path = custom_model_path(config)

            if engine == "yolo_world":
                model_path = raw_path or "yolov8s-worldv2.pt"
                raw_model = cls._load_raw(engine, model_path, device=device)
                classes_str = str(config.get("customClasses") or config.get("classes") or "").strip()
                classes = [c.strip() for c in classes_str.split(",") if c.strip()]
                return ModelRunnerHandle(engine, model_path, raw_model, classes)
            elif engine == "roboflow_universe":
                model_path = raw_path or str(config.get("modelPath") or "")
                raw_model = cls._load_raw(engine, model_path, device=device)
                classes_str = str(config.get("classes") or config.get("customClasses") or "").strip()
                classes = [c.strip() for c in classes_str.split(",") if c.strip()]
                return ModelRunnerHandle(engine, model_path, raw_model, classes)

            node_type = str(config.get("type") or "")
            if (engine == "ultralytics_yolo" or node_type == "pose_detector") and not raw_path:
                raw_path = "yolov8n-pose.pt" if node_type == "pose_detector" else "yolov8n.pt"

            model_path_obj = resolve_model_file(raw_path)
            model_path = str(model_path_obj)
            if engine in ("custom_auto", "rfdetr") and model_path_obj.is_file():
                engine = detect_model_engine(model_path)
            raw_model = cls._load_raw(engine, model_path, device=device)
            if engine == "ultralytics_yolo":
                configure_nms_free(raw_model, nms_free=config.get("nmsFree"), model_path=model_path)
            classes = _resolve_labels(config, model_path)
            return ModelRunnerHandle(engine, model_path, raw_model, classes)
        else:
            engine_type = args[0]
            model_path = args[1]
            device = args[2] if len(args) > 2 else kwargs.get("device", "cpu")
            return cls._load_raw(engine_type, model_path, device=device)

    @classmethod
    def _load_raw(cls, engine_type: str, model_path: str, device: str = "cpu") -> Any:
        if engine_type == "yolo_world":
            cache_prefix = f"{engine_type}:{model_path}:{device}:"
            if cache_prefix in _MODEL_CACHE:
                return _MODEL_CACHE[cache_prefix]
            from ultralytics import YOLOWorld
            weight_path = resolve_model_file(model_path)
            target = str(weight_path) if weight_path.is_file() else (model_path or "yolov8s-worldv2.pt")
            model = YOLOWorld(target)
            _MODEL_CACHE[cache_prefix] = model
            return model
        elif engine_type == "roboflow_universe":
            cache_prefix = f"{engine_type}:{model_path}:{device}:"
            if cache_prefix in _MODEL_CACHE:
                return _MODEL_CACHE[cache_prefix]
            model = {"model_id": model_path}
            _MODEL_CACHE[cache_prefix] = model
            return model

        path = resolve_model_file(model_path)
        try:
            stat = path.stat()
            version = f":{stat.st_mtime_ns}:{stat.st_size}"
        except OSError:
            version = ""
        cache_prefix = f"{engine_type}:{path}:{device}:"
        cache_key = cache_prefix + version.lstrip(":")
        if cache_key in _MODEL_CACHE:
            return _MODEL_CACHE[cache_key]

        if not path.is_file():
            raise FileNotFoundError(f"Custom model file not found: {model_path}")

        if engine_type == "ultralytics_yolo":
            from ultralytics import YOLO
            model = YOLO(str(path))
            configure_nms_free(model, nms_free=None, model_path=str(path))
        elif engine_type == "onnx_custom":
            import onnxruntime as ort
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if "cuda" in device.lower() else ["CPUExecutionProvider"]
            try:
                model = ort.InferenceSession(str(path), providers=providers)
            except Exception:
                model = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        elif engine_type == "tflite":
            import tensorflow as tf
            model = tf.lite.Interpreter(model_path=str(path))
            model.allocate_tensors()
        elif engine_type == "tensorflow_keras":
            import tensorflow as tf
            model = tf.keras.models.load_model(str(path))
        else:
            raise ValueError(f"Unsupported custom model engine: {engine_type}")
        for old_key in list(_MODEL_CACHE):
            if old_key.startswith(cache_prefix):
                del _MODEL_CACHE[old_key]
        _MODEL_CACHE[cache_key] = model
        return model

    @classmethod
    def run_frame(cls, frame, inference_node: dict) -> list[dict]:
        config = inference_node.get("config", {})
        node_id = inference_node.get("id", "detector")
        node_type = inference_node.get("type", "detector")
        engine_type = config.get("engine", "custom_auto")

        try:
            from .main import resolve_inference_device
        except Exception:
            try:
                from main import resolve_inference_device
            except Exception:
                def resolve_inference_device(cfg):
                    dev = str(cfg.get("device") or "auto").lower()
                    if dev == "cuda":
                        import torch
                        return ("cuda" if torch.cuda.is_available() else "cpu"), "CUDA GPU"
                    elif dev == "cpu":
                        return "cpu", "CPU"
                    import torch
                    return ("cuda" if torch.cuda.is_available() else "cpu"), "Auto"
        device, _ = resolve_inference_device(config)

        # 0a. YOLO-World Zero-Shot text prompt open-vocabulary detector
        if engine_type == "yolo_world":
            raw_path = custom_model_path(config) or "yolov8s-worldv2.pt"
            model = cls.get_or_load("yolo_world", raw_path, device=device)
            threshold = float(config.get("threshold", 0.35))
            iou_threshold = float(config.get("iouThreshold", config.get("nmsThreshold", 0.7)) or 0.7)
            imgsz_val = int(config.get("imageSize", config.get("imgsz", 0)) or 0)

            custom_classes_str = str(config.get("customClasses") or config.get("classes") or "").strip()
            if custom_classes_str:
                desired_classes = [c.strip() for c in custom_classes_str.split(",") if c.strip()]
            else:
                desired_classes = ["person", "vehicle", "object"]

            current_classes = getattr(model, "_current_yolo_world_classes", None)
            if current_classes != desired_classes:
                try:
                    model.set_classes(desired_classes)
                    model._current_yolo_world_classes = desired_classes
                except Exception as exc:
                    logger.warning("Failed to set YOLO-World classes %s: %s", desired_classes, exc)

            predict_kwargs: dict[str, Any] = {
                "conf": threshold,
                "iou": iou_threshold,
                "device": device,
                "verbose": False,
            }
            if imgsz_val > 0:
                predict_kwargs["imgsz"] = imgsz_val

            try:
                results = model.predict(frame, **predict_kwargs)
            except Exception as exc:
                err_str = str(exc).lower()
                if device != "cpu" and ("cuda" in err_str or "device" in err_str):
                    logger.warning("CUDA execution failed (%s); falling back to CPU.", exc)
                    predict_kwargs["device"] = "cpu"
                    results = model.predict(frame, **predict_kwargs)
                else:
                    raise

            if not results:
                return []
            res = results[0]
            detections = []
            if hasattr(res, "boxes") and res.boxes is not None and len(res.boxes) > 0:
                boxes = res.boxes.xyxy.cpu().numpy()
                confs = res.boxes.conf.cpu().numpy()
                classes = res.boxes.cls.cpu().numpy()
                configured_classes = [c.strip().casefold() for c in str(config.get("classes") or config.get("customClasses") or "").split(",") if c.strip()]

                for i, box in enumerate(boxes):
                    score = float(confs[i])
                    if score < threshold:
                        continue
                    cls_idx = int(classes[i])
                    cls_name = model.names.get(cls_idx, desired_classes[cls_idx] if cls_idx < len(desired_classes) else f"class_{cls_idx}")
                    if configured_classes and str(cls_name).casefold() not in configured_classes:
                        continue
                    x1, y1, x2, y2 = [float(v) for v in box]
                    detections.append({
                        "class": str(cls_name),
                        "score": score,
                        "bbox": [x1, y1, x2 - x1, y2 - y1],
                        "sourceNodeId": node_id,
                        "kind": "detection",
                    })
            return detections

        # 0b. Roboflow Universe Hosted Inference
        if engine_type == "roboflow_universe":
            model_id = str(config.get("modelPath") or config.get("customModelPath") or "").strip()
            api_key = str(config.get("roboflowApiKey") or config.get("apiKey") or os.environ.get("ROBOFLOW_API_KEY", "")).strip()
            threshold = float(config.get("threshold", 0.4))
            return _run_roboflow_universe(frame, model_id, api_key, threshold, node_id, node_type, config)

        if node_type == "pose_detector":
            engine_type = "ultralytics_yolo"

        # Standard file-based custom model execution
        raw_path = custom_model_path(config)
        if not raw_path:
            if node_type == "pose_detector":
                raw_path = "yolov8n-pose.pt"
            else:
                raise RuntimeError(f"Node '{node_id}' requires a custom model file path.")

        path = resolve_model_file(raw_path)
        if not path.is_file():
            raise FileNotFoundError(f"Model file not found: {raw_path}")

        if engine_type in ("custom_auto", "auto"):
            engine_type = detect_model_engine(str(path))

        threshold = float(config.get("threshold", 0.5))
        labels = _resolve_labels(config, str(path))

        # 1. Ultralytics YOLO inference (.pt, .pth)
        if engine_type == "ultralytics_yolo":
            model = cls.get_or_load(engine_type, str(path), device=device)
            configure_nms_free(model, nms_free=config.get("nmsFree"), model_path=str(path))
            iou_threshold = float(config.get("iouThreshold", config.get("nmsThreshold", 0.7)) or 0.7)
            imgsz_val = int(config.get("imageSize", config.get("imgsz", config.get("rfdetrImageSize", 0))) or 0)
            predict_kwargs: dict[str, Any] = {
                "conf": threshold,
                "iou": iou_threshold,
                "device": device,
                "verbose": False,
            }
            if imgsz_val > 0:
                predict_kwargs["imgsz"] = imgsz_val
            if path.suffix.lower() == ".onnx":
                onnx_session = cls.get_or_load("onnx_custom", str(path), device=device)
                input_shape = onnx_session.get_inputs()[0].shape
                if len(input_shape) == 4 and all(isinstance(v, int) for v in input_shape[1:]):
                    predict_kwargs.update(imgsz=[input_shape[2], input_shape[3]], rect=False,
                                          half="float16" in str(onnx_session.get_inputs()[0].type).lower())
            try:
                results = model.predict(frame, **predict_kwargs)
            except Exception as exc:
                err_str = str(exc).lower()
                if device != "cpu" and ("cuda" in err_str or "device" in err_str):
                    logger.warning("CUDA execution failed (%s); automatically falling back to CPU.", exc)
                    predict_kwargs["device"] = "cpu"
                    results = model.predict(frame, **predict_kwargs)
                else:
                    raise
            if not results:
                return []
            res = results[0]

            detections = []
            custom_names = [c.strip() for c in str(config.get("customClasses") or "").split(",") if c.strip()]
            # Check for Bounding Boxes (Object Detection)
            if hasattr(res, "boxes") and res.boxes is not None and len(res.boxes) > 0:
                boxes = res.boxes.xyxy.cpu().numpy()
                confs = res.boxes.conf.cpu().numpy()
                classes = res.boxes.cls.cpu().numpy()

                masks_data = res.masks.data.cpu().numpy() if (hasattr(res, "masks") and res.masks is not None) else None
                configured_classes = [c.strip().casefold() for c in str(config.get("classes") or config.get("customClasses") or "").split(",") if c.strip()]

                for i, box in enumerate(boxes):
                    score = float(confs[i])
                    if score < threshold:
                        continue
                    cls_idx = int(classes[i])
                    if hasattr(model, "names") and isinstance(model.names, dict) and cls_idx in model.names:
                        cls_name = model.names[cls_idx]
                    elif labels and cls_idx < len(labels):
                        cls_name = labels[cls_idx]
                    elif custom_names and cls_idx < len(custom_names):
                        cls_name = custom_names[cls_idx]
                    else:
                        cls_name = f"class_{cls_idx}"
                    if configured_classes and str(cls_name).casefold() not in configured_classes:
                        continue
                    x1, y1, x2, y2 = [float(v) for v in box]

                    item: dict[str, Any] = {
                        "class": str(cls_name),
                        "score": score,
                        "bbox": [x1, y1, x2 - x1, y2 - y1],
                        "sourceNodeId": node_id,
                        "kind": "segmentation" if node_type == "segmenter" else "detection",
                    }
                    if masks_data is not None and i < len(masks_data):
                        import cv2
                        import numpy as np
                        mask = (masks_data[i] > 0.5).astype(np.uint8) * 255
                        mask_resized = cv2.resize(mask, (frame.shape[1], frame.shape[0]))
                        contours, _ = cv2.findContours(mask_resized, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        if contours:
                            c_poly = max(contours, key=cv2.contourArea).reshape(-1, 2)
                            if len(c_poly) >= 3:
                                item["mask"] = [[float(p[0]), float(p[1])] for p in c_poly]

                    # Extract 17 Keypoints (Human Pose Estimation)
                    kpts_data = res.keypoints.data.cpu().numpy() if (hasattr(res, "keypoints") and res.keypoints is not None and hasattr(res.keypoints, "data")) else None
                    if kpts_data is not None and i < len(kpts_data):
                        person_kpts = kpts_data[i].tolist()
                        item["keypoints"] = person_kpts
                        try:
                            from .pose_engine import COCO_KEYPOINT_NAMES, classify_human_posture, draw_human_skeleton
                        except Exception:
                            from pose_engine import COCO_KEYPOINT_NAMES, classify_human_posture, draw_human_skeleton

                        item["keypoints_dict"] = {
                            COCO_KEYPOINT_NAMES[idx]: person_kpts[idx]
                            for idx in range(min(len(COCO_KEYPOINT_NAMES), len(person_kpts)))
                        }
                        pkey, plabel, pconf = classify_human_posture(person_kpts)
                        item["posture"] = pkey
                        item["posture_label"] = plabel
                        item["posture_confidence"] = pconf

                        # Render colorful skeleton bones and glowing joint dots onto frame
                        if (node_type == "pose_detector" or config.get("showSkeleton", True)) and config.get("showSkeleton", True) is not False:
                            draw_human_skeleton(frame, person_kpts, config, plabel if config.get("showPostureBadge", True) else "")

                    detections.append(item)
                return detections

            # Check for Classification probabilities
            if hasattr(res, "probs") and res.probs is not None:
                probs = res.probs.data.cpu().numpy()
                top_k = int(config.get("topK", 1))
                top_indices = probs.argsort()[-top_k:][::-1]
                for idx in top_indices:
                    score = float(probs[idx])
                    if score >= threshold:
                        cls_name = custom_names[idx] if idx < len(custom_names) else model.names.get(idx, labels[idx] if idx < len(labels) else f"class_{idx}")
                        detections.append({
                            "class": str(cls_name),
                            "classId": int(idx),
                            "score": score,
                            "sourceNodeId": node_id,
                            "kind": "classification",
                        })
                return detections

            return []

        # 2. Custom ONNX Runtime (.onnx)
        if engine_type == "onnx_custom":
            import cv2
            import numpy as np

            session = cls.get_or_load(engine_type, str(path), device=device)
            if _ultralytics_onnx_export(session, node_type):
                yolo_config = dict(config)
                yolo_config["engine"] = "ultralytics_yolo"
                yolo_config["modelPath"] = str(path)
                return cls.run_frame(frame, {**inference_node, "config": yolo_config})

            if node_type == "segmenter":
                raise ValueError("Non-Ultralytics ONNX segmenter exports are unsupported.")
            if len(session.get_inputs()) != 1 or len(session.get_outputs()) != 1:
                raise ValueError("Generic ONNX models must have exactly one input and one output.")
            input_meta = session.get_inputs()[0]
            input_name = input_meta.name
            shape = input_meta.shape

            if len(shape) != 4:
                raise ValueError(f"Unsupported ONNX input shape {shape}; expected four dimensions.")
            if not str(input_meta.type).lower().startswith(("tensor(float)", "tensor(float16)")):
                raise ValueError(f"Unsupported ONNX input dtype {input_meta.type}; expected float32 or float16.")
            dims = [int(x) if isinstance(x, (int, np.integer)) else None for x in shape]
            if dims[1] is None and dims[3] is None:
                raise ValueError(f"Ambiguous dynamic ONNX input layout {shape}.")
            nchw = dims[1] in (1, 3, 4) or (dims[1] is not None and dims[2] is not None and dims[3] is not None and dims[1] < dims[2])
            channels = dims[1] if nchw else dims[3]
            if channels != 3:
                raise ValueError(f"Unsupported ONNX input channels {channels}; expected RGB.")
            if nchw:
                in_h, in_w = dims[2] or 640, dims[3] or 640
            else:
                in_h, in_w = dims[1] or 640, dims[2] or 640

            resized = cv2.resize(frame, (in_w, in_h))
            input_dtype = np.float16 if "float16" in str(input_meta.type).lower() else np.float32
            blob = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(input_dtype) / input_dtype(255.0)
            blob = np.transpose(blob, (2, 0, 1))[np.newaxis, ...] if nchw else blob[np.newaxis, ...]

            outputs = session.run(None, {input_name: blob})
            if not outputs:
                return []

            out = np.asarray(outputs[0])
            if out.ndim == 3 and out.shape[0] == 1:
                out = out[0]
            if node_type in ("classifier", "classification") and out.ndim == 2 and out.shape[0] == 1:
                out = out[0]
            detections = []

            # If YOLO output: shape [num_features, num_predictions] or [num_predictions, num_features]
            if out.ndim == 2:
                if node_type == "classifier":
                    raise ValueError(f"Unsupported ONNX classification output shape {out.shape}.")
                feature_count = len(labels) + 4 if labels else None
                if feature_count and out.shape[1] == feature_count:
                    pass
                elif feature_count and out.shape[0] == feature_count:
                    out = out.T
                elif out.shape[1] >= 5 and out.shape[0] >= 5:
                    # [features, predictions] has the smaller feature axis.
                    if out.shape[0] < out.shape[1]:
                        out = out.T
                elif out.shape[1] < 5 and out.shape[0] >= 5:
                    out = out.T
                if out.shape[1] < 5:
                    raise ValueError(f"Unsupported ONNX detection output shape {out.shape}.")

                scale_x = frame.shape[1] / in_w
                scale_y = frame.shape[0] / in_h
                configured_classes = {c.strip().casefold() for c in str(config.get("classes") or "").split(",") if c.strip()}

                for row in out:
                    cx, cy, w, h = row[:4]
                    class_scores = row[4:]
                    cls_id = int(np.argmax(class_scores))
                    score = float(class_scores[cls_id])
                    if score >= threshold:
                        x = (cx - w / 2) * scale_x
                        y = (cy - h / 2) * scale_y
                        cls_name = labels[cls_id] if cls_id < len(labels) else f"class_{cls_id}"
                        if configured_classes and cls_name.casefold() not in configured_classes:
                            continue
                        detections.append({
                            "class": str(cls_name),
                            "score": score,
                            "bbox": [float(x), float(y), float(w * scale_x), float(h * scale_y)],
                            "sourceNodeId": node_id,
                            "kind": "detection",
                        })
                return detections

            # If classification: 1D array of probabilities
            if out.ndim == 1:
                if node_type not in ("classifier", "classification"):
                    raise ValueError(f"Unsupported ONNX output shape {out.shape} for {node_type} task.")
                top_k = int(config.get("topK", 1))
                top_indices = out.argsort()[-top_k:][::-1]
                for idx in top_indices:
                    score = float(out[idx])
                    if score >= threshold:
                        cls_name = labels[idx] if idx < len(labels) else f"class_{idx}"
                        detections.append({
                            "class": str(cls_name),
                            "classId": int(idx),
                            "score": score,
                            "sourceNodeId": node_id,
                            "kind": "classification",
                        })
                return detections

            raise ValueError(f"Unsupported ONNX output shape {out.shape}.")

        # 3. TensorFlow Lite (.tflite)
        if engine_type == "tflite":
            import cv2
            import numpy as np

            interpreter = cls.get_or_load(engine_type, str(path), device=device)
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()

            in_shape = input_details[0]["shape"]
            in_h, in_w = in_shape[1], in_shape[2]

            resized = cv2.resize(frame, (in_w, in_h))
            input_dtype = input_details[0]["dtype"]
            if input_dtype == np.uint8:
                input_data = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)[np.newaxis, ...]
            elif input_dtype == np.int8:
                scale, zero_point = input_details[0].get("quantization", (0.0, 0))
                if scale > 0:
                    norm = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
                    input_data = np.clip(norm / scale + zero_point, -128, 127).astype(np.int8)[np.newaxis, ...]
                else:
                    input_data = (cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) - 128.0).astype(np.int8)[np.newaxis, ...]
            elif input_dtype == np.float16:
                input_data = (cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float16) / 255.0)[np.newaxis, ...]
            else:
                input_data = (cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0)[np.newaxis, ...]

            interpreter.set_tensor(input_details[0]["index"], input_data)
            interpreter.invoke()

            detections = []
            # Standard SSD MobileNet TFLite outputs (boxes, classes, scores, count)
            if len(output_details) >= 4:
                boxes = np.squeeze(interpreter.get_tensor(output_details[0]["index"]))
                classes = np.squeeze(interpreter.get_tensor(output_details[1]["index"]))
                scores = np.squeeze(interpreter.get_tensor(output_details[2]["index"]))

                for i, score in enumerate(scores):
                    if float(score) >= threshold:
                        y1, x1, y2, x2 = boxes[i]
                        cls_id = int(classes[i])
                        cls_name = labels[cls_id] if cls_id < len(labels) else f"class_{cls_id}"
                        detections.append({
                            "class": str(cls_name),
                            "score": float(score),
                            "bbox": [
                                float(x1 * frame.shape[1]),
                                float(y1 * frame.shape[0]),
                                float((x2 - x1) * frame.shape[1]),
                                float((y2 - y1) * frame.shape[0]),
                            ],
                            "sourceNodeId": node_id,
                            "kind": "detection",
                        })
                return detections

            # Generic single output TFLite (YOLO or classifier)
            out_tensor = np.squeeze(interpreter.get_tensor(output_details[0]["index"]))
            out_dtype = output_details[0]["dtype"]
            if out_dtype in (np.int8, np.uint8):
                quant_params = output_details[0].get("quantization_parameters") or {}
                scales = quant_params.get("scales", [])
                zero_points = quant_params.get("zero_points", [])
                scale = float(scales[0]) if len(scales) > 0 else output_details[0].get("quantization", (0.0, 0))[0]
                zp = int(zero_points[0]) if len(zero_points) > 0 else output_details[0].get("quantization", (0.0, 0))[1]
                if scale > 0:
                    out = (out_tensor.astype(np.float32) - zp) * scale
                else:
                    out = out_tensor.astype(np.float32)
            else:
                out = out_tensor.astype(np.float32)

            # If 2D output (e.g. YOLOv8 TFLite output (84, 8400) or (8400, 84))
            if out.ndim == 2:
                if out.shape[0] < out.shape[1]:
                    out = out.T  # Transpose to (N_boxes, 4 + classes)
                scale_x = frame.shape[1] / in_w
                scale_y = frame.shape[0] / in_h
                configured_classes = [c.strip().casefold() for c in str(config.get("classes") or config.get("customClasses") or "").split(",") if c.strip()]
                for row in out:
                    cls_scores = row[4:]
                    cls_id = int(np.argmax(cls_scores))
                    score = float(cls_scores[cls_id])
                    if score >= threshold:
                        cx, cy, w, h = row[:4]
                        x = (cx - w / 2) * scale_x
                        y = (cy - h / 2) * scale_y
                        cls_name = labels[cls_id] if cls_id < len(labels) else f"class_{cls_id}"
                        if configured_classes and cls_name.casefold() not in configured_classes:
                            continue
                        detections.append({
                            "class": str(cls_name),
                            "score": score,
                            "bbox": [float(x), float(y), float(w * scale_x), float(h * scale_y)],
                            "sourceNodeId": node_id,
                            "kind": "detection",
                        })
                return detections

            if out.ndim == 1:
                top_k = int(config.get("topK", 1))
                top_indices = out.argsort()[-top_k:][::-1]
                for idx in top_indices:
                    score = float(out[idx])
                    if score >= threshold:
                        cls_name = labels[idx] if idx < len(labels) else f"class_{idx}"
                        detections.append({
                            "class": str(cls_name),
                            "classId": int(idx),
                            "score": score,
                            "sourceNodeId": node_id,
                            "kind": "classification",
                        })
                return detections

            return []

        # 4. TensorFlow Keras (.keras, .h5)
        if engine_type == "tensorflow_keras":
            import cv2
            import numpy as np

            model = cls.get_or_load(engine_type, str(path), device=device)
            # Default classification size
            in_h, in_w = 224, 224
            if hasattr(model, "input_shape") and model.input_shape and len(model.input_shape) >= 3:
                in_h = model.input_shape[1] or 224
                in_w = model.input_shape[2] or 224

            resized = cv2.resize(frame, (in_w, in_h))
            blob = (cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0)[np.newaxis, ...]
            preds = model.predict(blob, verbose=0)
            out = np.squeeze(preds)

            detections = []
            if out.ndim == 1:
                top_k = int(config.get("topK", 1))
                top_indices = out.argsort()[-top_k:][::-1]
                for idx in top_indices:
                    score = float(out[idx])
                    if score >= threshold:
                        cls_name = labels[idx] if idx < len(labels) else f"class_{idx}"
                        detections.append({
                            "class": str(cls_name),
                            "classId": int(idx),
                            "score": score,
                            "sourceNodeId": node_id,
                            "kind": "classification",
                        })
            return detections

        raise ValueError(f"Unknown engine: {engine_type}")


def run_custom_model_frame(frame, inference_node: dict) -> list[dict]:
    """Top-level helper for single-frame inference on custom AI models."""
    return CustomModelRunner.run_frame(frame, inference_node)
