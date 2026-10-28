from __future__ import annotations

INPUT_NODE_ID = "input"
LEGACY_CAMERA_NODE_ID = "camera"

PYTHON_SCRIPT_DEFAULT_CODE = '''def process(frame, state):
    state["frames"] = state.get("frames", 0) + 1
    if state["frames"] % 30 == 0:
        print(f"python_script frames={state['frames']}")
    return frame.copy()
'''
PYTHON_SCRIPT_DEFAULTS = {
    "code": PYTHON_SCRIPT_DEFAULT_CODE,
    "timeoutMs": 500,
    "onError": "stop",
}

EFFICIENTAD_DEFAULTS = {
    "engine": "efficientad", "efficientadModel": "", "threshold": 0.0,
    "useModelThreshold": True, "anomalyThreshold": 0.1,
    "showHeatmap": True, "heatmapOpacity": 0.35,
    "device": "auto", "batchSize": 1,
    "detectEveryNFrames": 1, "maxDetectionFps": 0,
}


def normalize_efficientad_config(config: dict) -> dict:
    for key, value in EFFICIENTAD_DEFAULTS.items():
        config.setdefault(key, value)
    config["engine"] = "efficientad"
    return config


IMAGE_PROCESSING_NODE_TYPES = (
    "resize",
    "crop",
    "rotate_flip",
    "color_convert",
    "brightness_contrast",
    "blur_sharpen",
    "perspective",
    "undistort",
    "background_subtract",
    "python_script",
)
DRAWING_NODE_TYPES = ("overlay_annotate", "interactive_zoom")
LEGACY_DRAWING_NODE_TYPES = ("draw_text", "draw_boxes")
ALL_DRAWING_NODE_TYPES = DRAWING_NODE_TYPES + LEGACY_DRAWING_NODE_TYPES

OVERLAY_LAYER_DEFAULTS = {
    "bounding_boxes": {
        "type": "bounding_boxes",
        "enabled": True,
        "color": "#2563eb",
        "thickness": 2,
        "fillOpacity": 0.0,
        "classes": "",
    },
    "labels": {
        "type": "labels",
        "enabled": True,
        "color": "#22c55e",
        "template": "{detection.class}",
        "fontScale": 0.55,
        "position": "top",
        "classes": "",
    },
    "confidence": {
        "type": "confidence",
        "enabled": True,
        "color": "#7c3aed",
        "template": "{detection.confidence}",
        "fontScale": 0.55,
        "position": "below_label",
        "classes": "",
    },
    "result_icons": {
        "type": "result_icons",
        "enabled": False,
        "passClasses": "ok, pass, good",
        "passText": "OK",
        "failText": "X",
        "passColor": "#22c55e",
        "failColor": "#ef4444",
        "size": 0.65,
        "position": "top_right",
        "classes": "",
    },
    "custom_text": {
        "type": "custom_text",
        "enabled": False,
        "template": "{classification.class}  {classification.confidence}",
        "x": 24,
        "y": 48,
        "fontScale": 1.0,
        "thickness": 2,
        "color": "#ffffff",
        "background": True,
        "backgroundColor": "#111827",
        "position": "bottom_right",
        "classes": "",
    },
    "heatmap": {
        "type": "heatmap",
        "enabled": False,
        "opacity": 0.40,
        "decay": 0.98,
        "colormap": "jet",
    },
    "vector_arrow": {
        "type": "vector_arrow",
        "enabled": False,
        "color": "#38bdf8",
        "thickness": 2,
        "scale": 1.5,
    },
    "motion_trace": {
        "type": "motion_trace",
        "enabled": False,
        "color": "#a855f7",
        "thickness": 2,
        "historyLen": 20,
        "fadeAlpha": True,
        "classes": "",
    },
    "corner_bracket": {
        "type": "corner_bracket",
        "enabled": False,
        "color": "#22c55e",
        "thickness": 2,
        "bracketLength": 16,
        "glow": True,
        "classes": "",
    },
}

OVERLAY_LAYER_OPTIONS = (
    ("bounding_boxes", "Bounding box"),
    ("labels", "Label"),
    ("confidence", "Confidence"),
    ("result_icons", "Status badge"),
    ("heatmap", "Traffic Heatmap"),
    ("vector_arrow", "Direction Arrow Vector"),
    ("motion_trace", "Motion Trace / Tail"),
    ("corner_bracket", "Corner Bracket / Halo Glow"),
    ("custom_text", "Custom text"),
)


def make_overlay_layer(layer_type: str, index: int = 0) -> dict:
    """Create one independent overlay instruction with a stable ID."""
    defaults = OVERLAY_LAYER_DEFAULTS.get(layer_type, OVERLAY_LAYER_DEFAULTS["custom_text"])
    return {**defaults, "id": f"{layer_type}-{index + 1}"}


def default_overlay_layers() -> list[dict]:
    """Return the empty layer stack used by a new Overlay / Annotate node."""
    return []


def normalize_overlay_config(config: dict) -> dict:
    """Normalize the ordered, extensible overlay layer collection in place."""
    layers = config.get("layers")
    if not isinstance(layers, list):
        layers = default_overlay_layers()
    normalized = []
    used_ids: set[str] = set()
    for index, layer in enumerate(layers):
        if not isinstance(layer, dict):
            continue
        layer_type = str(layer.get("type") or "custom_text")
        if layer_type not in OVERLAY_LAYER_DEFAULTS:
            continue
        item = {**OVERLAY_LAYER_DEFAULTS[layer_type], **layer}
        item_id = str(item.get("id") or f"{layer_type}-{index + 1}")
        if item_id in used_ids:
            item_id = f"{layer_type}-{index + 1}"
        item["id"] = item_id
        used_ids.add(item_id)
        normalized.append(item)
    config["layers"] = normalized
    return config
DRAWING_VARIABLES_BY_NODE_TYPE = {
    "efficientad": (
        ("{anomaly.result}", "Inspection result (OK / NG)"),
        ("{anomaly.score}", "Anomaly score"),
        ("{anomaly.threshold}", "Anomaly decision threshold"),
    ),
    "input": (
        ("{image.width}", "Image width"),
        ("{image.height}", "Image height"),
    ),
    "pose_detector": (
        ("{detection.count}", "Person count"),
        ("{detection.posture}", "Detected posture (Berdiri/Duduk/Jatuh)"),
        ("{detection.confidence}", "Best detection confidence"),
        ("{detection.x}", "Detection left position"),
        ("{detection.y}", "Detection top position"),
    ),
    "detector": (
        ("{detection.count}", "Detection count"),
        ("{detection.class}", "Best detection class"),
        ("{detection.confidence}", "Best detection confidence"),
        ("{detection.x}", "Detection left position"),
        ("{detection.y}", "Detection top position"),
        ("{detection.width}", "Detection width"),
        ("{detection.height}", "Detection height"),
    ),
    "segmenter": (
        ("{detection.count}", "Segmentation count"),
        ("{detection.class}", "Best segmentation class"),
        ("{detection.confidence}", "Best segmentation confidence"),
    ),
    "classifier": (
        ("{classification.class}", "Classification class"),
        ("{classification.confidence}", "Classification confidence"),
    ),
    "tracker": (
        ("{track.id}", "Track ID"),
    ),
    "object_counter": (
        ("{count.total}", "Total object count"),
    ),
}


def upstream_node_ids(workflow: dict, target_id: str) -> set[str]:
    """Return enabled ancestors of a node, excluding the target itself."""
    nodes = {
        str(node.get("id") or ""): node
        for node in workflow.get("nodes", [])
        if node.get("enabled", True)
    }
    incoming: dict[str, list[str]] = {}
    for edge in workflow.get("edges", []):
        if len(edge) >= 2 and str(edge[0]) in nodes and str(edge[1]) in nodes:
            incoming.setdefault(str(edge[1]), []).append(str(edge[0]))
    found: set[str] = set()
    pending = list(incoming.get(str(target_id), []))
    while pending:
        node_id = pending.pop()
        if node_id in found:
            continue
        found.add(node_id)
        pending.extend(incoming.get(node_id, []))
    return found


def available_drawing_variables(workflow: dict, target_id: str) -> list[tuple[str, str]]:
    """Describe template variables produced by connected upstream nodes."""
    ancestors = upstream_node_ids(workflow, target_id)
    available: list[tuple[str, str]] = []
    seen: set[str] = set()
    for node in workflow.get("nodes", []):
        if str(node.get("id") or "") not in ancestors:
            continue
        for token, description in DRAWING_VARIABLES_BY_NODE_TYPE.get(node.get("type"), ()):
            if token not in seen:
                seen.add(token)
                available.append((token, description))
    return available


def _configured_output_labels(value) -> list[str]:
    """Normalize the class-name formats accepted by the inference settings."""
    if isinstance(value, dict):
        def sort_key(item):
            try:
                return 0, int(item[0])
            except (TypeError, ValueError):
                return 1, str(item[0])

        raw = [label for _key, label in sorted(value.items(), key=sort_key)]
    elif isinstance(value, (list, tuple)):
        raw = value
    else:
        raw = str(value or "").replace(",", "\n").splitlines()
    return [str(label).strip() for label in raw if label is not None and str(label).strip()]


def available_output_labels(workflow: dict, target_id: str) -> list[tuple[str, str]]:
    """Return known class/result labels from enabled upstream nodes.

    Some model formats carry their labels only at runtime, so this deliberately
    lists only values that the workflow can know without loading a model.
    """
    ancestors = upstream_node_ids(workflow, target_id)
    available: list[tuple[str, str]] = []
    seen: set[str] = set()
    for node in workflow.get("nodes", []):
        if str(node.get("id") or "") not in ancestors:
            continue
        node_type = str(node.get("type") or "")
        config = node.get("config", {})
        labels: list[str] = []
        if node_type == "efficientad":
            labels = ["OK", "NG"]
        elif node_type == "classifier":
            labels = _configured_output_labels(config.get("classes", config.get("customClasses", config.get("convnextClasses", ""))))
        elif node_type == "pose_detector":
            labels = ["person"]
        elif node_type in ("detector", "segmenter"):
            engine = str(config.get("engine") or "")
            if engine == "sam3":
                labels = _configured_output_labels(config.get("concepts", "person"))
            elif engine == "rfdetr_onnx":
                labels = _configured_output_labels(config.get("rfdetrOnnxClasses", ""))
            elif engine == "rfdetr_tensorrt":
                labels = _configured_output_labels(config.get("rfdetrTensorRTClasses", ""))
            elif engine in ("ultralytics_yolo", "yolo_world", "roboflow_universe", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                labels = _configured_output_labels(config.get("classes", config.get("customClasses", "")))
                if not labels and engine == "ultralytics_yolo":
                    model_path = str(config.get("modelPath") or config.get("customModelPath") or "yolov8n.pt")
                    if "yolo" in model_path.lower():
                        try:
                            from .custom_model_runtime import COCO_CLASSES
                        except ImportError:
                            from custom_model_runtime import COCO_CLASSES
                        labels = list(COCO_CLASSES)
        elif node_type == "filter":
            labels = _configured_output_labels(config.get("classes", ""))

        source = str(node.get("title") or node_type.replace("_", " ").title())
        for label in labels:
            key = label.casefold()
            if key not in seen:
                seen.add(key)
                available.append((label, source))
    return available
LOGIC_NODE_TYPES = (
    "if_else",
    "compare_value",
    "roi_filter",
    "object_count_condition",
    "class_detected_condition",
    "confidence_threshold",
    "timer_delay",
    "debounce",
    "rate_limiter",
    "and_or_logic",
    "trigger_once",
    "switch_case",
    "class_replacement",
)
OBJECT_EVENT_NODE_TYPES = (
    "track_snapshot",
    "object_counter",
    "zone_activity_timer",
    "zone_exit_event",
    "multi_zone_occupancy",
    "vlm_box_tracker",
    "ai_agent",
    "distance_measurement",
    "size_measurement",
    "camera_focus",
    "overlap_analysis",
    "velocity_calculator",
    "path_deviation",
    "object_timer",
    "face_detector",
    "face_analyzer",
    "face_tracker",
    "face_crop",
    "dominant_color",
    "man_down_detector",
    "lpr_license_plate",
    "overstack_detector",
    "ppe_compliance_matrix",
    "crowd_density_heatmap",
)
OUTPUT_NODE_TYPES = (
    "preview",
    "alert",
    "image_output",
    "database_output",
    "dashboard_sink",
    "incident_video_recorder",
    "mqtt_publisher",
)
RFDETR_DETECTION_MODEL_OPTIONS = [
    ("rfdetr-nano", "RF-DETR nano"),
    ("rfdetr-small", "RF-DETR small"),
    ("rfdetr-medium", "RF-DETR medium"),
    ("rfdetr-large", "RF-DETR large"),
]
RFDETR_SEGMENTATION_MODEL_OPTIONS = [
    ("rfdetr-seg-nano", "RF-DETR-Seg nano"),
    ("rfdetr-seg-small", "RF-DETR-Seg small"),
    ("rfdetr-seg-medium", "RF-DETR-Seg medium"),
    ("rfdetr-seg-large", "RF-DETR-Seg large"),
]
CONVNEXT_MODEL_OPTIONS = [
    ("convnext_tiny.fb_in22k_ft_in1k", "ConvNeXt Tiny"),
    ("convnext_small.fb_in22k_ft_in1k", "ConvNeXt Small"),
    ("convnext_base.fb_in22k_ft_in1k", "ConvNeXt Base"),
    ("convnext_large.fb_in22k_ft_in1k", "ConvNeXt Large"),
]
TRACKING_ALGORITHMS = (
    "tracktrack",
    "fasttrack",
    "deepocsort",
    "bytetrack",
    "botsort",
    "ocsort",
    "cbiou",
)
TRACKING_ALGORITHM_OPTIONS = [
    ("tracktrack", "TrackTrack (CVPR — Multi-Cue & TAI, Default Baru)"),
    ("fasttrack", "FastTracker (Anti-Oklusi & Rollback Kalman, Hemat CPU)"),
    ("deepocsort", "Deep OC-SORT (Observation-Centric + ReID & GMC)"),
    ("bytetrack", "ByteTrack"),
    ("botsort", "BoT-SORT"),
    ("ocsort", "OC-SORT"),
    ("cbiou", "C-BIoU (Buffered Motion)"),
]
BOT_SORT_CMC_OPTIONS = [
    ("sparseOptFlow", "Sparse optical flow"),
    ("orb", "ORB features"),
    ("sift", "SIFT features"),
    ("ecc", "ECC alignment"),
]
TRACKER_CONFIG_VERSION = 3
OBSOLETE_TRACKER_CONFIG_KEYS = (
    "proximityThreshold",
    "appearanceThreshold",
    "withReid",
    "reidModel",
    "reidModelPath",
    "reidDevice",
    "reidHalfPrecision",
    "reidBatchSize",
    "reidAppearanceThreshold",
    "botSortMatchThreshold",
    "botSortSecondMatchThreshold",
    "botSortUnconfirmedThreshold",
    "botSortFuseScore",
    "ocSortUseByte",
    "ocSortLowThreshold",
)
TRACKER_CONFIG_DEFAULTS = {
    "trackerConfigVersion": TRACKER_CONFIG_VERSION,
    "algorithm": "bytetrack",
    # Roboflow ByteTrack and BoT-SORT confidence/lifecycle settings.
    "trackHighThreshold": 0.45,
    "trackLowThreshold": 0.1,
    "newTrackThreshold": 0.5,
    "matchThreshold": 0.1,
    "trackBuffer": 90,
    "minimumConsecutiveFrames": 1,
    "trackerFrameRate": 30,
    # Roboflow BoT-SORT association and camera-motion settings.
    "botSortFirstIouThreshold": 0.2,
    "botSortSecondIouThreshold": 0.5,
    "botSortUnconfirmedIouThreshold": 0.3,
    "botSortGmc": True,
    "botSortCmcMethod": "sparseOptFlow",
    "botSortCmcDownscale": 2,
    # Roboflow OC-SORT settings.
    "ocSortDetectionThreshold": 0.45,
    "ocSortIouThreshold": 0.3,
    "ocSortMaxAge": 90,
    "ocSortMinHits": 1,
    "ocSortDeltaT": 3,
    "ocSortInertia": 0.2,
    # Track stabilization & class consistency
    "enableClassLock": True,
    "classLockWindow": 10,
    "enableSmoothing": True,
    "smoothingAlpha": 0.7,
    # Settings shared by every tracker.
    "batchSize": 1,
    "classAgnostic": False,
    "showLostTracks": False,
}


def migrate_tracker_config(config: dict) -> None:
    """Migrate saved tracker settings to Roboflow's parameter semantics."""
    try:
        version = int(config.get("trackerConfigVersion", 0))
    except (TypeError, ValueError):
        version = 0
    if version < 2:
        legacy_default_updates = {
            "trackHighThreshold": (0.5, 0.6),
            "newTrackThreshold": (0.6, 0.7),
            "matchThreshold": (0.45, 0.1),
            "ocSortDetectionThreshold": (0.5, 0.6),
        }
        for key, (legacy_default, roboflow_default) in legacy_default_updates.items():
            if config.get(key) == legacy_default:
                config[key] = roboflow_default
    if version < 3:
        for key, old_default in {
            "trackHighThreshold": 0.6, "newTrackThreshold": 0.7,
            "trackBuffer": 30, "minimumConsecutiveFrames": 2,
            "ocSortDetectionThreshold": 0.6, "ocSortMaxAge": 30,
            "ocSortMinHits": 3,
        }.items():
            if config.get(key) == old_default:
                config[key] = TRACKER_CONFIG_DEFAULTS[key]
    if "enableClassLock" not in config:
        config["enableClassLock"] = TRACKER_CONFIG_DEFAULTS["enableClassLock"]
    if "classLockWindow" not in config:
        config["classLockWindow"] = TRACKER_CONFIG_DEFAULTS["classLockWindow"]
    if "enableSmoothing" not in config:
        config["enableSmoothing"] = TRACKER_CONFIG_DEFAULTS["enableSmoothing"]
    if "smoothingAlpha" not in config:
        config["smoothingAlpha"] = TRACKER_CONFIG_DEFAULTS["smoothingAlpha"]
    for key in OBSOLETE_TRACKER_CONFIG_KEYS:
        config.pop(key, None)
    config["trackerConfigVersion"] = TRACKER_CONFIG_VERSION
SAM3_IMAGE_SIZE = 1008
SAM3_DEFAULT_THRESHOLD = 0.1
RFDETR_NATIVE_IMAGE_SIZE = 0

NODE_BLUEPRINTS = {
    "export_code": {
        "title": "Export Code",
        "subtitle": "Menghasilkan paket Python mandiri dari alur kerja aktif",
        "category": "Outputs & Export",
        "x": 910,
        "y": 740,
        "config": {"packageName": "", "version": "1.0.0", "includeModels": False},
    },
    "input": {
        "title": "Input",
        "subtitle": "Sumber kamera USB/webcam, Daheng, YouTube stream, gambar, atau file video",
        "category": "Sources",
        "x": 40,
        "y": 60,
        "config": {
            "sourceType": "camera",
            "source": 0,
            "youtubeUrl": "",
            "youtubeQuality": "720p",
            "autoReconnect": True,
            "width": 0,
            "height": 0,
            "dahengOpenMode": "index",
            "dahengIdentifier": "1",
            "dahengTimeoutMs": 1000,
            "dahengFrameRate": 0,
            "dahengExposureUs": 0,
            "dahengGain": 0,
            "filePath": "",
            "loop": True,
            "frameQueueSize": 8,
            "torchCpuThreads": 0,
            "asyncPreview": False,
            "dropFrames": True,
        },
    },
    "ip_camera": {
        "title": "IP Camera / CCTV",
        "subtitle": "Menerima aliran RTSP/HTTP CCTV atau Media Gateway (go2rtc/NVR/Ezviz/Tapo/IP Publik) dengan proteksi liveness",
        "category": "Sources",
        "x": 40,
        "y": 180,
        "config": {
            "connectionMode": "direct",
            "streamUrl": "rtsp://192.168.1.100:554/stream1",
            "username": "",
            "password": "",
            "transport": "tcp",
            "gatewayUrl": "http://127.0.0.1:1984",
            "gatewayRtspBase": "rtsp://127.0.0.1:8554",
            "selectedStream": "",
            "cameraBrand": "ezviz",
            "networkType": "lan",
            "host": "",
            "port": 554,
            "streamQuality": "main",
            "autoReconnect": True,
            "reconnectDelaySeconds": 2.0,
            "detectFreeze": True,
            "freezeThresholdSeconds": 3.0,
            "detectTamper": True,
            "tamperDarkThreshold": 6.0,
            "tamperBrightThreshold": 248.0,
            "frameQueueSize": 4,
            "dropFrames": True,
            "asyncPreview": True,
        },
    },
    "pose_detector": {
        "title": "Human Pose Estimator",
        "subtitle": "Mendeteksi pose tubuh manusia, 17 titik sendi, dan kerangka visual langsung memakai YOLO Pose",
        "category": "AI Vision Models",
        "x": 330,
        "y": 140,
        "config": {
            "engine": "ultralytics_yolo",
            "modelPath": "yolov8n-pose.pt",
            "customModelPath": "yolov8n-pose.pt",
            "threshold": 0.45,
            "keypointThreshold": 0.35,
            "iouThreshold": 0.45,
            "device": "auto",
            "showSkeleton": True,
            "showJoints": True,
            "showFaceLines": False,
            "showBoundingBox": False,
            "showPostureBadge": True,
            "skeletonThickness": 2,
            "jointRadius": 4,
            "detectEveryNFrames": 1,
            "maxDetectionFps": 0,
        },
    },
    "hand_skeleton": {
        "title": "Hand Tracking & Gestures",
        "subtitle": "Pelacakan 21 titik sendi kerangka tangan 3D & pengenal gestur interaktif (Pinch, Fist, Peace, Pointing)",
        "category": "AI Vision Models",
        "x": 330,
        "y": 210,
        "config": {
            "numHands": 2,
            "threshold": 0.45,
            "showSkeleton": True,
            "showJoints": True,
            "showGestureBadge": True,
            "hideUnknownGesture": False,
            "skeletonThickness": 2,
            "jointRadius": 4,
            "detectPinch": True,
            "pinchThreshold": 32.0,
        },
    },
    "detector": {
        "title": "Object Detection",
        "subtitle": "Mendeteksi objek langsung memakai YOLO26 NMS-Free (hemat CPU), YOLOv8n, atau RF-DETR",
        "category": "AI Vision Models",
        "x": 330,
        "y": 60,
        "config": {
            "engine": "ultralytics_yolo",
            "modelPath": "yolov8n.pt",
            "customModelPath": "yolov8n.pt",
            "threshold": 0.45,
            "iouThreshold": 0.45,
            "device": "auto",
            "customClasses": "",
            "detectEveryNFrames": 1,
            "maxDetectionFps": 0,
            "batchSize": 1,
            "rfdetrModel": "rfdetr-nano",
            "rfdetrCheckpoint": "",
            "rfdetrImageSize": RFDETR_NATIVE_IMAGE_SIZE,
            "rfdetrHalfPrecision": True,
            "rfdetrTensorRTEngine": "",
            "rfdetrTensorRTClasses": "",
            "rfdetrTensorRTCudaGraph": False,
            "rfdetrTensorRTProcess": False,
            "rfdetrOnnxModel": "",
            "rfdetrOnnxClasses": "",
            "perClassThresholds": "",
            "classRemap": "",
        },
    },
    "slicer": {
        "title": "Small Object Slicer",
        "subtitle": "Inferensi berpetak (SAHI) untuk objek kecil pada resolusi tinggi",
        "category": "Image Preprocessing",
        "x": 330,
        "y": 145,
        "config": {
            "sliceWidth": 640,
            "sliceHeight": 640,
            "overlapRatio": 0.2,
            "iouThreshold": 0.45,
        },
    },
    "camera_focus": {
        "title": "Camera Focus Health",
        "subtitle": "Memantau ketajaman fokus lensa kamera memakai varians Laplacian",
        "category": "Image Preprocessing",
        "x": 330,
        "y": 230,
        "config": {
            "blurThreshold": 100.0,
            "checkIntervalSeconds": 5.0,
            "enableAlarm": True,
            "roi": "",
        },
    },
    "auto_rotate_edges": {
        "title": "Auto Rotate Edges",
        "subtitle": "Mendeteksi sudut kemiringan dominan dan meluruskan orientasi bingkai otomatis",
        "category": "Image Preprocessing",
        "x": 330,
        "y": 315,
        "config": {
            "maxAngleLimit": 45.0,
            "minAngleThreshold": 0.5,
            "borderMode": "black_constant",
        },
    },
    "delta_filter": {
        "title": "Delta Motion Filter",
        "subtitle": "Menghemat beban komputasi dengan melewati bingkai ketika area pantau diam",
        "category": "Image Preprocessing",
        "x": 330,
        "y": 400,
        "config": {
            "deltaThreshold": 0.03,
            "heartbeatIntervalSeconds": 15.0,
            "minContourArea": 500.0,
        },
    },
    "segmenter": {
        "title": "Object Segmentation",
        "subtitle": "Segmentasi dan penopengan piksel objek memakai YOLO, RF-DETR, atau SAM 3",
        "category": "AI Vision Models",
        "x": 620,
        "y": 60,
        "config": {
            "engine": "ultralytics_yolo",
            "threshold": 0.45,
            "customModelPath": "data/models/yolov8n-seg.pt",
            "customClasses": "",
            "rfdetrModel": "rfdetr-seg-nano",
            "rfdetrCheckpoint": "",
            "rfdetrImageSize": RFDETR_NATIVE_IMAGE_SIZE,
            "rfdetrHalfPrecision": True,
            "rfdetrTensorRTEngine": "",
            "rfdetrTensorRTClasses": "",
            "rfdetrTensorRTCudaGraph": False,
            "rfdetrTensorRTProcess": False,
            "rfdetrOnnxModel": "",
            "rfdetrOnnxClasses": "",
            "detectEveryNFrames": 1,
            "maxDetectionFps": 0,
            "batchSize": 1,
            "samCheckpoint": "",
            "concepts": "person",
            "device": "auto",
            "imgsz": SAM3_IMAGE_SIZE,
            "perClassThresholds": "",
            "classRemap": "",
        },
    },
    "efficientad": {
        "title": "Visual Inspection",
        "subtitle": "Deteksi anomali cacat visual tanpa sampel cacat dengan EfficientAD",
        "category": "AI Vision Models",
        "x": 620, "y": 145,
        "config": dict(EFFICIENTAD_DEFAULTS),
    },
    "classifier": {
        "title": "Image Classification",
        "subtitle": "Klasifikasi kategori gambar dengan model ConvNeXt atau kustom",
        "category": "AI Vision Models",
        "x": 620,
        "y": 145,
        "config": {
            "engine": "convnext",
            "threshold": 0.0,
            "convnextModel": "convnext_tiny.fb_in22k_ft_in1k",
            "convnextCheckpoint": "",
            "convnextClasses": "",
            "convnextImageSize": 224,
            "convnextHalfPrecision": True,
            "topK": 1,
            "detectEveryNFrames": 1,
            "maxDetectionFps": 0,
            "batchSize": 1,
            "iouThreshold": 0.45,
            "device": "auto",
            "customModelPath": "",
            "customClasses": "",
        },
    },
    "detection_crop": {
        "title": "Detection Crop",
        "subtitle": "Potong setiap objek hasil deteksi untuk klasifikasi atau inspeksi",
        "category": "AI Vision Models",
        "x": 620,
        "y": 230,
        "config": {
            "classes": "",
            "contextPaddingPercent": 0.15,
            "paddingPercent": 0.0,
            "square": False,
            "padColor": "#000000",
            "minCropWidth": 32,
            "minCropHeight": 32,
            "minSize": 1,
            "maxCrops": 32,
        },
    },
    "barcode_reader": {
        "title": "Barcode & QR Reader",
        "subtitle": "Pemindai kode QR & barcode bawaan OpenCV",
        "category": "AI Vision Models",
        "x": 620,
        "y": 315,
        "config": {
            "cropFromDetections": False,
            "classes": "qrcode, barcode, label",
            "showOverlay": True,
            "cooldownSeconds": 2.0,
        },
    },
    "ocr_reader": {
        "title": "OCR Text Reader (ONNX)",
        "subtitle": "Pembaca teks & nomor plat/label otomatis berbasis model ultra-ringan ONNX",
        "category": "AI Vision Models",
        "x": 620,
        "y": 315,
        "config": {
            "recModelPath": "data/models/ocr/ppocrv3_en_rec.onnx",
            "detModelPath": "data/models/ocr/ppocrv3_det.onnx",
            "dictPath": "data/models/ocr/en_dict.txt",
            "cropFromDetections": False,
            "filterClasses": "license_plate, container, box, label, text",
            "minConfidence": 0.35,
            "characterWhitelist": "",
            "emitEvents": True,
            "cooldownSeconds": 1.0,
        },
    },
    "ai_agent": {
        "title": "AI Agent",
        "subtitle": "Penalaran multimodal cerdas (OpenAI, OpenRouter, Ollama) untuk verifikasi SOP dan analisis visual",
        "category": "AI Vision Models",
        "x": 620,
        "y": 315,
        "config": {
            "provider": "openai",
            "apiKey": "",
            "baseUrl": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "triggerMode": "on_event",
            "periodicIntervalSeconds": 10.0,
            "cooldownSeconds": 5.0,
            "taskMode": "decision",
            "includeImage": True,
            "imageQuality": 80,
            "imageMaxDimension": 720,
            "systemPrompt": "You are an industrial safety & operations AI auditor. Evaluate the situation accurately.",
            "userPrompt": "Analyze the visual scene and detection data: {{detections}}. Are there any violations or critical events? Respond in JSON with keys: decision (bool), reason (str), and severity (str).",
            "jsonSchema": "",
            "temperature": 0.2,
            "maxTokens": 500,
            "passDownstreamOn": "decision_true",
        },
    },
    "tracker": {
        "title": "Object Tracking",
        "subtitle": "Pelacakan identitas objek secara konsisten memakai TrackTrack, FastTracker (anti-oklusi), ByteTrack, atau BoT-SORT",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 230,
        "config": dict(TRACKER_CONFIG_DEFAULTS),
    },
    "detections_consensus": {
        "title": "Detections Consensus",
        "subtitle": "Konsensus beberapa model AI untuk menekan deteksi positif palsu di area industri",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 280,
        "config": {
            "requiredVotes": 2,
            "iouThreshold": 0.5,
            "confidenceAggregation": "average",
            "classAware": True,
            "boxAggregation": "highest_confidence",
        },
    },
    "distance_measurement": {
        "title": "Distance Measurement",
        "subtitle": "Mengukur jarak fisik dua dimensi antar-objek dan membunyikan alarm batas aman",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 340,
        "config": {
            "objectAClass": "person",
            "objectBClass": "forklift",
            "measurementAxis": "euclidean",
            "pixelRatio": 10.0,
            "minDistanceThreshold": 150.0,
            "anchorMode": "bottom_center",
            "triggerAlarmOnProximity": True,
            "alarmCooldownSeconds": 3.0,
        },
    },
    "size_measurement": {
        "title": "Size Measurement",
        "subtitle": "Ukur dimensi fisik lebar, tinggi, dan luas objek dengan toleransi min/max",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 400,
        "config": {
            "targetClass": "all",
            "pixelPerUnit": 10.0,
            "unitName": "cm",
            "minAllowedWidth": 0.0,
            "maxAllowedWidth": 0.0,
            "minAllowedHeight": 0.0,
            "maxAllowedHeight": 0.0,
            "triggerAlarmOnToleranceViolation": False,
        },
    },
    "overlap_analysis": {
        "title": "Overlap Analysis",
        "subtitle": "Inspeksi relasi spasial parent-child (misal: person memakai helmet)",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 460,
        "config": {
            "parentClass": "person",
            "childClass": "helmet",
            "minOverlapRatio": 0.5,
            "parentRegion": "top_half",
            "triggerAlarmOnNonCompliance": True,
            "alarmCooldownSeconds": 3.0,
        },
    },
    "velocity_calculator": {
        "title": "Velocity Calculator",
        "subtitle": "Hitung kecepatan objek dalam km/jam atau m/s dari perpindahan centroid",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 520,
        "config": {
            "targetClasses": "",
            "pixelPerMeter": 25.0,
            "speedLimitKmh": 15.0,
            "speedUnit": "kmh",
            "smoothingWindow": 5,
            "minSpeedKmh": 0.5,
            "showOverlay": True,
            "showTrackId": True,
            "badgePosition": "top",
            "triggerAlarmOnSpeeding": True,
            "alarmCooldownSeconds": 3.0,
            "normalColor": "#10b981",
            "alertColor": "#ef4444",
        },
    },
    "dominant_color": {
        "title": "Dominant Color Inspector",
        "subtitle": "Inspeksi kepatuhan warna APD (rompi/helm) & palet warna dominan objek",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 640,
        "config": {
            "targetClass": "person",
            "subRegion": "torso",
            "targetPreset": "hi_vis_green",
            "minMatchPercent": 15.0,
            "requireMatch": True,
            "attributeKey": "vest_color",
            "alarmCooldownSeconds": 5.0,
        },
    },
    "class_replacement": {
        "title": "Class Replacement",
        "subtitle": "Hierarchical cascade relabeler: ganti label kelas awal dengan classifier sekunder",
        "category": "Logic & Flow Control",
        "x": 620,
        "y": 1410,
        "config": {
            "sourceClass": "*",
            "replacementMode": "direct_mapping",
            "mappingTable": "vehicle:forklift, person:worker",
            "attributeKey": "sub_class",
            "minClassifierConfidence": 0.50,
            "fallbackAction": "keep_original",
            "preserveOriginalClass": True,
        },
    },
    "man_down_detector": {
        "title": "Man Down & Fall Detector",
        "subtitle": "K3 Keselamatan Kerja: Deteksi pekerja terjatuh, pingsan, atau tidak sadarkan diri",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 700,
        "config": {
            "targetClass": "person",
            "aspectRatioThreshold": 0.95,
            "stillnessMaxMotionPx": 8.0,
            "confirmationDurationSeconds": 4.0,
            "alarmCooldownSeconds": 10.0,
        },
    },
    "lpr_license_plate": {
        "title": "License Plate Reader (LPR)",
        "subtitle": "ANPR Khusus Kendaraan & Kontrol Akses Gerbang (Whitelist/Blacklist)",
        "category": "AI Vision Models",
        "x": 620,
        "y": 760,
        "config": {
            "vehicleClasses": "truck, car, pickup, vehicle",
            "whitelist": "B1234XYZ, KT8888AA",
            "blacklist": "B6666BAD",
            "temporalVotingFrames": 5,
            "minConfidence": 0.65,
            "gateCooldownSeconds": 10.0,
        },
    },
    "overstack_detector": {
        "title": "Overstack Clearance Detector",
        "subtitle": "Pantau batas ketinggian aman tumpukan pallet/kargo di gudang logistik",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 820,
        "config": {
            "targetClasses": "pallet, box, cargo, tire, stack",
            "ceilingY": 220.0,
            "pixelPerMeter": 50.0,
            "persistenceDurationSeconds": 2.5,
            "alarmCooldownSeconds": 15.0,
        },
    },
    "path_deviation": {
        "title": "Path Deviation Monitor",
        "subtitle": "Pantau penyimpangan rute lintasan fisik (virtual corridor) kendaraan/orang",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 580,
        "config": {
            "guidePathPoints": "0.1,0.5; 0.5,0.5; 0.9,0.5",
            "maxAllowedDeviationMeters": 1.5,
            "pixelPerMeter": 25.0,
            "targetClasses": "forklift, vehicle",
            "triggerAlarmOnDeviation": True,
            "alarmCooldownSeconds": 3.0,
        },
    },
    "track_snapshot": {
        "title": "Once Per Track",
        "subtitle": "Kirim satu event inspeksi terbaik untuk setiap objek terlacak",
        "category": "Tracking & Analysis",
        "x": 910,
        "y": 230,
        "config": {
            "trackIds": "",
            "classes": "",
            "minimumConfidence": 0.0,
            "minimumTrackAgeFrames": 1,
            "captureMode": "best_frame",
            "retentionSeconds": 3600,
        },
    },
    "object_counter": {
        "title": "Object Counter",
        "subtitle": "Hitung okupansi langsung atau total akumulasi objek terlacak",
        "category": "Tracking & Analysis",
        "x": 910,
        "y": 315,
        "config": {
            "classes": "",
            "mode": "occupancy",
            "countOncePerTrack": True,
            "direction": "both",
            "retentionSeconds": 3600,
            "maxCapacity": 0,
            "alertOnCapacityExceeded": True,
        },
    },
    "line_counter": {
        "title": "Line Counter",
        "subtitle": "Hitung objek melintasi garis (IN / OUT, Multi-Line)",
        "category": "Tracking & Analysis",
        "x": 910,
        "y": 360,
        "config": {
            "lines": [
                {
                    "id": "line_1",
                    "name": "Line 1",
                    "startPoint": "",
                    "endPoint": "",
                    "invertDirection": False,
                    "countMode": "both",
                    "lineColor": "#22c55e",
                    "inLabel": "IN",
                    "outLabel": "OUT",
                }
            ],
            "startPoint": "",
            "endPoint": "",
            "triggerAnchor": "center",
            "classes": "",
            "showOverlay": True,
            "lineColor": "#22c55e",
            "lineWidth": 2,
            "inLabel": "IN",
            "outLabel": "OUT",
            "invertDirection": False,
            "countMode": "both",
            "hysteresisDistance": 15.0,
            "reArmCooldown": 1.5,
        },
    },
    "dwell_time": {
        "title": "Dwell Time / Loitering",
        "subtitle": "Ukur durasi waktu objek berada di dalam zona tertentu",
        "category": "Tracking & Analysis",
        "x": 910,
        "y": 425,
        "config": {
            "points": "0.2,0.2; 0.8,0.2; 0.8,0.8; 0.2,0.8",
            "thresholdSeconds": 5.0,
            "classes": "",
            "showOverlay": True,
            "showTimer": True,
            "zoneColor": "#f59e0b",
            "alertOnExceed": True,
        },
    },
    "object_timer": {
        "title": "Object Timer",
        "subtitle": "Hitung durasi dan tampilkan timer langsung di atas setiap orang atau objek yang terdeteksi secara real-time",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 420,
        "config": {
            "targetClasses": "person, face",
            "alertThresholdSeconds": 10.0,
            "graceSeconds": 2.0,
            "timerFormat": "mm:ss",
            "showOverlay": True,
            "showTrackId": True,
            "badgePosition": "top",
            "minDurationSeconds": 0.0,
            "alertMode": "once",
            "alertCooldownSeconds": 5.0,
            "normalColor": "#10b981",
            "alertColor": "#ef4444",
        },
    },
    "face_detector": {
        "title": "Face Detector (UniFace)",
        "subtitle": "Deteksi wajah dan 5-titik facial landmark berakurasi tinggi menggunakan model ONNX UniFace",
        "category": "AI Vision Models",
        "x": 390,
        "y": 260,
        "config": {
            "model": "retinaface",
            "confidenceThreshold": 0.45,
            "nmsThreshold": 0.4,
            "minFaceSize": 20.0,
            "detectLandmarks": True,
            "enableAntiSpoofing": True,
            "antiSpoofThreshold": 0.60,
            "filterSpoof": True,
        },
    },
    "face_analyzer": {
        "title": "Face Analyzer (UniFace)",
        "subtitle": "Deteksi wajah terpadu dengan estimasi umur, jenis kelamin, ekspresi emosi, dan ringkasan HUD pojok layar",
        "category": "AI Vision Models",
        "x": 420,
        "y": 280,
        "config": {
            "confidenceThreshold": 0.45,
            "minFaceSize": 20.0,
            "detectLandmarks": True,
            "estimateAgeGender": True,
            "classifyEmotion": True,
            "showFaceBadges": True,
            "showCornerHUD": True,
            "hudPosition": "top-left",
            "hudScalePercent": 100,
            "ageGrouping": "bracket",
        },
    },
    "face_crop": {
        "title": "Face Crop & Quality (UniFace)",
        "subtitle": "Potong wajah terdeteksi, evaluasi kualitas (eDifFIQA), dan sajikan preview chip",
        "category": "AI Vision Models",
        "x": 620,
        "y": 260,
        "config": {
            "alignFaces": True,
            "paddingPercent": 0.15,
            "assessQuality": True,
            "minQualityScore": 0.40,
            "filterLowQuality": False,
            "maxCrops": 16,
            "showQualityChip": True,
        },
    },
    "face_tracker": {
        "title": "Face Re-ID Tracker (UniFace)",
        "subtitle": "Lacak dan kenali identitas orang berdasarkan embedding wajah ArcFace yang terhubung dengan Database Wajah",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 260,
        "config": {
            "recognitionModel": "arcface",
            "similarityThreshold": 0.48,
            "unknownPrefix": "Tamu",
            "maxMissingSeconds": 5.0,
            "showLandmarks": True,
            "showNameBadge": True,
        },
    },
    "zone_activity_timer": {
        "title": "Zone Activity Timer",
        "subtitle": "Ukur aktivitas objek di dalam zona tanpa memerlukan ID track per objek",
        "category": "Tracking & Analysis",
        "x": 910,
        "y": 490,
        "config": {
            "zoneName": "Workshop Area",
            "points": "0.2,0.2; 0.8,0.2; 0.8,0.8; 0.2,0.8",
            "requiredClasses": "tire",
            "requiredCount": 1,
            "triggerClasses": "person",
            "triggerCount": 1,
            "confirmationSeconds": 10,
            "countFromStart": True,
            "personGraceSeconds": 3,
            "requiredGraceSeconds": 15,
            "maxObservationGapSeconds": 5,
            "maxSessionDurationSeconds": 0,
            "showOverlay": True,
        },
    },
    "zone_exit_event": {
        "title": "Zone Exit Event",
        "subtitle": "Kirim event saat objek terlacak keluar dari zona setelah sebelumnya terlihat di dalam",
        "category": "Tracking & Analysis",
        "x": 910,
        "y": 555,
        "config": {
            "zoneName": "Warehouse Exit",
            "points": "0.2,0.2; 0.8,0.2; 0.8,0.8; 0.2,0.8",
            "classes": "truck,tire",
            "absenceGraceSeconds": 2,
            "maxObservationGapSeconds": 5,
            "showOverlay": True,
        },
    },
    "multi_zone_occupancy": {
        "title": "Multi-Zone Occupancy & Activity Tracker",
        "subtitle": "Pantau keterisian banyak zona/meja/slot sekaligus, timer durasi, kapasitas, dan status Vacant/Occupied",
        "category": "Tracking & Analysis",
        "x": 920,
        "y": 520,
        "config": {
            "targetClasses": "person, face",
            "confirmationSeconds": 3.0,
            "graceSeconds": 10.0,
            "maxDwellMinutes": 0.0,
            "labelPosition": "center",
            "compactLabel": True,
            "showHudOverlay": True,
            "showSummaryCard": True,
            "zones": [
                {
                    "id": "zone_1",
                    "name": "Zona A",
                    "capacity": 4,
                    "points": "0.15,0.20; 0.45,0.20; 0.45,0.80; 0.15,0.80"
                },
                {
                    "id": "zone_2",
                    "name": "Zona B",
                    "capacity": 2,
                    "points": "0.55,0.20; 0.85,0.20; 0.85,0.80; 0.55,0.80"
                }
            ],
        },
    },
    "vlm_box_tracker": {
        "title": "VLM Box Tracker",
        "subtitle": "Pelacakan objek real-time via TypeSafe Jev / OpenRouter VLM dengan Optical Flow & Kalman Filter",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 230,
        "config": {
            "provider": "openrouter",
            "apiKey": "",
            "model": "google/gemini-2.0-flash-001",
            "objectPrompt": "tire, person",
            "queryIntervalSeconds": 1.0,
            "minConfidence": 0.5,
            "opticalFlowEnabled": True,
            "showOpticalFlowPoints": False,
            "historySeconds": 5.0,
            "trackWidth": 480,
            "sendWidth": 640,
        },
    },
    "filter": {
        "title": "Detection & Geometry Filter",
        "subtitle": "Filter berdasarkan nama kelas, ukuran luas, rasio, dan margin batas",
        "category": "Tracking & Analysis",
        "x": 330,
        "y": 230,
        "config": {
            "classes": "person, car, dog, cat, bottle",
            "minCount": 1,
            "minArea": 0,
            "maxArea": 0,
            "minAspectRatio": 0.0,
            "maxAspectRatio": 0.0,
            "excludeBorderMargin": 0,
            "perClassConfidence": "",
            "defaultConfidence": 0.0,
            "paddingPercent": 0,
            "paddingMode": "aspect_ratio_preserve",
        },
    },
    "preview": {
        "title": "Live Preview",
        "subtitle": "Jendela tampilan streaming video hasil pemrosesan",
        "category": "Outputs & Export",
        "x": 40,
        "y": 400,
        "config": {
            "showBoxes": True,
            "showLabels": True,
            "showMasks": True,
            "showTrackIds": True,
            "showTrails": True,
            "showCounts": True,
            "maskOpacity": 0.35,
            "cropGridMaxItems": 16,
            "cropGridColumns": 0,
            "cropGridGap": 8,
            "holdLastEvent": True,
            "maxPreviewFps": 0,
            "saveVideo": False,
            "outputPath": "",
            "outputFps": 0,
        },
    },
    "alert": {
        "title": "Alert Output",
        "subtitle": "Catat riwayat log event dan rekam klip video alarm",
        "category": "Outputs & Export",
        "x": 330,
        "y": 400,
        "config": {
            "cooldownSeconds": 5,
            "message": "Detected target object",
            "recordClip": True,
            "clipDurationSeconds": 5,
        },
    },
    "image_output": {
        "title": "Save Images",
        "subtitle": "Simpan gambar inspeksi dengan rotasi pembersihan otomatis (FIFO)",
        "category": "Outputs & Export",
        "x": 620,
        "y": 485,
        "config": {
            "outputDirectory": "",
            "format": "jpg",
            "jpegQuality": 95,
            "filenameTemplate": "{timestamp}_{track_id}_{class}",
            "captureMode": "crop_only",
            "maxFilesRetention": 1000,
            "burnWatermark": True,
        },
    },
    "draw_text": {
        "title": "Draw Text",
        "subtitle": "Gambarkan teks & variabel ke dalam frame gambar",
        "category": "Annotations & Drawing",
        "x": 330,
        "y": 570,
        "config": {
            "textTemplate": "{classification.class}  {classification.confidence}",
            "x": 24,
            "y": 48,
            "fontScale": 1.0,
            "thickness": 2,
            "color": "#ffffff",
            "background": True,
            "backgroundColor": "#111827",
        },
    },
    "draw_boxes": {
        "title": "Draw Boxes",
        "subtitle": "Gambarkan kotak deteksi dan label variabel ke dalam frame",
        "category": "Annotations & Drawing",
        "x": 620,
        "y": 570,
        "config": {
            "labelTemplate": "{detection.class}  {detection.confidence}",
            "color": "#22c55e",
            "thickness": 2,
            "showLabel": True,
            "fillOpacity": 0.0,
        },
    },
    # Legacy drawing blueprints remain loadable so existing projects keep
    # working. Only Overlay / Annotate is exposed in the node library.
    "overlay_annotate": {
        "title": "Overlay / Annotate",
        "subtitle": "Gambarkan seluruh anotasi (kotak, label, ikon, heatmap) di satu tempat",
        "category": "Annotations & Drawing",
        "x": 620,
        "y": 570,
        "config": {"layers": default_overlay_layers()},
    },
    "interactive_zoom": {
        "title": "Interactive Object Zoom",
        "subtitle": "Klik objek pada live video untuk zoom crop interaktif & Picture-in-Picture (PiP)",
        "category": "Annotations & Drawing",
        "x": 620,
        "y": 640,
        "config": {
            "pipSizeMode": "dynamic",
            "pipPosition": "top-right",
            "pipSizePercent": 30,
            "pipAspectRatio": "auto",
            "focusPoint": "auto",
            "zoomScale": 1.0,
            "headroomPercent": 48,
            "borderColor": "#00e5ff",
            "borderThickness": 2,
            "showCrosshair": True,
            "showLabel": True,
            "showClassName": True,
            "showConfidence": True,
            "showDownloadButton": True,
            "showTargetBox": True,
            "targetLostHoldSeconds": 5.0,
        },
    },
    "database_output": {
        "title": "Database Output",
        "subtitle": "Simpan hasil deteksi dan log event ke database lokal SQLite",
        "category": "Outputs & Export",
        "x": 620,
        "y": 400,
        "config": {
            "databasePath": "",
            "saveDetections": True,
            "eventObjectsOnly": True,
            "saveFrames": False,
            "saveEvents": True,
            "saveDebug": False,
            "sampleEvery": 1,
            "batchSize": 128,
            "flushIntervalMs": 500,
            "maxQueue": 10000,
            "retentionDays": 14,
            "aggregateHourly": True,
        },
    },
    "webhook_output": {
        "title": "Webhook / HTTP Outbound",
        "subtitle": "Kirim data event ke REST API endpoint eksternal",
        "category": "Outputs & Export",
        "x": 620,
        "y": 485,
        "config": {
            "url": "http://127.0.0.1:8000/webhook",
            "method": "POST",
            "cooldownSeconds": 2.0,
            "sendImage": True,
            "imageQuality": 80,
            "customHeaders": "Content-Type: application/json",
            "payloadTemplate": "",
            "retryCount": 2,
            "timeoutSeconds": 5.0,
        },
    },
    "resize": {
        "title": "Resize",
        "subtitle": "Ubah ukuran resolusi frame ke dimensi tetap",
        "category": "Image Preprocessing",
        "x": 330,
        "y": 570,
        "config": {"width": 1280, "height": 720, "interpolation": "linear"},
    },
    "frame_sampler": {
        "title": "Frame Sampler",
        "subtitle": "Batasi FPS pemrosesan per cabang",
        "category": "Image Preprocessing",
        "x": 330,
        "y": 635,
        "config": {"targetFps": 10},
    },
    "python_script": {
        "title": "Custom Python Script",
        "subtitle": "Jalankan process(frame, state) pada frame BGR uint8 tanpa mengubah dimensinya",
        "category": "Image Preprocessing",
        "x": 620,
        "y": 700,
        "config": dict(PYTHON_SCRIPT_DEFAULTS),
    },
    "crop": {
        "title": "Crop / Region of Interest",
        "subtitle": "Pangkas dan pertahankan area persegi panjang tertentu",
        "category": "Image Preprocessing",
        "x": 620,
        "y": 570,
        "config": {"x": 0, "y": 0, "width": 640, "height": 480},
    },
    "rotate_flip": {
        "title": "Rotate / Flip",
        "subtitle": "Atur orientasi sudut putaran dan pembalikan frame gambar",
        "category": "Image Preprocessing",
        "x": 910,
        "y": 570,
        "config": {"rotation": "0", "flip": "none"},
    },
    "color_convert": {
        "title": "Color Conversion",
        "subtitle": "Konversi ruang warna gambar (Grayscale, HSV, dll)",
        "category": "Image Preprocessing",
        "x": 330,
        "y": 700,
        "config": {"mode": "gray"},
    },
    "brightness_contrast": {
        "title": "Brightness / Contrast",
        "subtitle": "Atur intensitas cahaya & penglihatan malam (Night Vision CLAHE)",
        "category": "Image Preprocessing",
        "x": 620,
        "y": 700,
        "config": {
            "brightness": 0,
            "contrast": 1.0,
            "useClahe": False,
            "autoLowLight": True,
            "lowLightThreshold": 65.0,
            "clipLimit": 2.5,
            "tileGridSize": 8,
        },
    },
    "blur_sharpen": {
        "title": "Blur / Sharpen",
        "subtitle": "Haluskan noise atau pertajam detail ketajaman gambar",
        "category": "Image Preprocessing",
        "x": 910,
        "y": 700,
        "config": {"operation": "blur", "kernel": 5, "strength": 1.0},
    },
    "perspective": {
        "title": "Perspective Correction",
        "subtitle": "Luruskan area 4 titik sudut pandang miring",
        "category": "Image Preprocessing",
        "x": 330,
        "y": 830,
        "config": {"points": "0,0; 100,0; 100,100; 0,100", "width": 0, "height": 0},
    },
    "undistort": {
        "title": "Camera Undistortion",
        "subtitle": "Terapkan kalibrasi lensa untuk koreksi distorsi cembung",
        "category": "Image Preprocessing",
        "x": 620,
        "y": 830,
        "config": {"calibrationPath": "", "alpha": 0.0},
    },
    "background_subtract": {
        "title": "Background Subtraction",
        "subtitle": "Ekstrak objek bergerak dari latar belakang diam",
        "category": "Image Preprocessing",
        "x": 910,
        "y": 830,
        "config": {
            "method": "mog2",
            "history": 500,
            "threshold": 16,
            "detectShadows": True,
        },
    },
    "blur_anonymizer": {
        "title": "Privacy Blur",
        "subtitle": "Sensor privasi wajah atau plat nomor dengan blur/pixelate",
        "category": "Annotations & Drawing",
        "x": 910,
        "y": 895,
        "config": {
            "classes": "person, face, license_plate",
            "mode": "gaussian",
            "kernelSize": 35,
            "pixelateBlock": 16,
            "insideBbox": True,
        },
    },
    "if_else": {
        "title": "If / Else",
        "subtitle": "Percabangan alur: Loloskan data jika kondisi Benar (IF) atau Salah (ELSE)",
        "category": "Logic & Flow Control",
        "x": 330,
        "y": 960,
        "config": {
            "metric": "object_count",
            "operator": "gte",
            "value": 1,
            "passWhen": "true",
            "classes": "",
        },
    },
    "compare_value": {
        "title": "Compare Value",
        "subtitle": "Bandingkan jumlah objek, confidence, atau hitungan garis dengan ambang batas",
        "category": "Logic & Flow Control",
        "x": 620,
        "y": 960,
        "config": {
            "metric": "object_count",
            "operator": "gte",
            "value": 1,
            "classes": "",
        },
    },
    "roi_filter": {
        "title": "ROI Filter",
        "subtitle": "Hanya teruskan deteksi di dalam / luar area zona tertentu",
        "category": "Logic & Flow Control",
        "x": 910,
        "y": 960,
        "config": {
            "shape": "rectangle",
            "x": 0,
            "y": 0,
            "width": 640,
            "height": 480,
            "points": [],
            "mode": "inside",
            "invertZone": False,
            "triggerAnchor": "bottom_center",
            "match": "bottom_center",
            "crossingDirection": "enter",
            "showOverlay": True,
        },
    },
    "object_count_condition": {
        "title": "Object Count Condition",
        "subtitle": "Loloskan data jika jumlah objek memenuhi kondisi syarat",
        "category": "Logic & Flow Control",
        "x": 330,
        "y": 1090,
        "config": {"operator": "gte", "count": 1},
    },
    "class_detected_condition": {
        "title": "Class Detected Condition",
        "subtitle": "Loloskan data jika kelas target tertentu terdeteksi",
        "category": "Logic & Flow Control",
        "x": 620,
        "y": 1090,
        "config": {"classes": "person", "match": "any"},
    },
    "confidence_threshold": {
        "title": "Confidence Threshold",
        "subtitle": "Loloskan data jika akurasi model memenuhi ambang batas minimal",
        "category": "Logic & Flow Control",
        "x": 910,
        "y": 1090,
        "config": {"operator": "gte", "threshold": 0.55, "match": "any"},
    },
    "timer_delay": {
        "title": "Timer / Delay",
        "subtitle": "Tahan dan stabilkan sinyal selama durasi detik tertentu",
        "category": "Logic & Flow Control",
        "x": 910,
        "y": 1090,
        "config": {"seconds": 1.0},
    },
    "debounce": {
        "title": "Debounce",
        "subtitle": "Cegah pemicuan berulang dari deteksi yang berkedip",
        "category": "Logic & Flow Control",
        "x": 330,
        "y": 1220,
        "config": {"seconds": 0.5},
    },
    "rate_limiter": {
        "title": "Rate Limiter",
        "subtitle": "Batasi frekuensi event dengan jeda waktu pendingin (cooldown)",
        "category": "Logic & Flow Control",
        "x": 620,
        "y": 1220,
        "config": {"seconds": 5.0},
    },
    "alarm_cooldown_gate": {
        "title": "Alarm Cooldown Gate",
        "subtitle": "Peredam badai alarm: cegah spam beruntun dengan masa hening, eskalasi bertahap, dan re-arm otomatis",
        "category": "Logic & Flow Control",
        "x": 620,
        "y": 1285,
        "config": {
            "cooldownSeconds": 30.0,
            "mode": "suppress",
            "escalateIntervalSeconds": 60.0,
            "clearHoldSeconds": 3.0,
        },
    },
    "and_or_logic": {
        "title": "AND / OR Logic",
        "subtitle": "Kombinasikan beberapa status sinyal logika alur pemrosesan",
        "category": "Logic & Flow Control",
        "x": 910,
        "y": 1220,
        "config": {"operator": "and", "enabledValue": True},
    },
    "trigger_once": {
        "title": "Trigger Once",
        "subtitle": "Hanya loloskan pemicu satu kali hingga kondisi kembali normal",
        "category": "Logic & Flow Control",
        "x": 330,
        "y": 1350,
        "config": {"resetOnClear": True},
    },
    "switch_case": {
        "title": "Switch Case Router",
        "subtitle": "Mengarahkan aliran alur multi-cabang berdasarkan kelas atau atribut",
        "category": "Logic & Flow Control",
        "x": 620,
        "y": 1350,
        "config": {
            "evaluationField": "class",
            "cases": "person:port_1, forklift:port_2",
            "defaultPort": "default",
        },
    },
    "model_comparison": {
        "title": "Model Comparison Diff",
        "subtitle": "Bandingkan hasil dua model AI secara side-by-side atau diff overlay",
        "category": "AI Vision Models",
        "x": 620,
        "y": 640,
        "config": {
            "modelAName": "Model A (YOLO)",
            "modelBName": "Model B (RF-DETR)",
            "renderMode": "side_by_side",
            "iouThreshold": 0.50,
            "showStatsHeader": True,
        },
    },
    "detections_difference": {
        "title": "Detections Difference",
        "subtitle": "Deteksi objek baru yang muncul atau hilang dibandingkan baseline",
        "category": "Spatial & Advanced Logic",
        "x": 620,
        "y": 720,
        "config": {
            "matchIoU": 0.50,
            "filterClasses": "",
            "triggerSnapshot": False,
            "cooldownSeconds": 3.0,
            "alarmOnDifference": True,
        },
    },
    "data_aggregator": {
        "title": "Data Aggregator (Rollup)",
        "subtitle": "Agregasi metrik sesi berkala per jendela waktu (count, duration, max occupancy)",
        "category": "Outputs & Export",
        "x": 910,
        "y": 400,
        "config": {
            "windowMinutes": 60,
            "metricTypes": ["count", "sum_duration", "avg_duration", "max_occupancy"],
        },
    },
    "csv_formatter": {
        "title": "CSV Formatter",
        "subtitle": "Format baris CSV tabular dari riwayat event sesi kerja siap ekspor",
        "category": "Outputs & Export",
        "x": 910,
        "y": 485,
        "config": {
            "columns": "timestamp,zone_name,type,working_seconds,item_count",
            "delimiter": ",",
            "outputFilePath": "",
        },
    },
    "s3_sink": {
        "title": "S3 Cloud Sink",
        "subtitle": "Unggah foto bukti visual atau crop event ke AWS S3 / MinIO Object Storage",
        "category": "Outputs & Export",
        "x": 910,
        "y": 570,
        "config": {
            "endpointUrl": "https://s3.amazonaws.com",
            "bucketName": "afi-vision-records",
            "objectPrefix": "events/",
            "credentialsSecretRef": "AWS_ACCESS_KEY_ID",
            "imageQuality": 85,
        },
    },
    "notification_dispatcher": {
        "title": "Notification Dispatcher",
        "subtitle": "Kirim notifikasi instan dan foto bukti ke Telegram, Slack, atau Webhook",
        "category": "Outputs & Export",
        "x": 910,
        "y": 655,
        "config": {
            "channel": "telegram",
            "destinationId": "",
            "botToken": "",
            "messageTemplate": "🚨 Alert: {event.type} pada {event.zoneName}!",
            "attachImage": True,
            "cooldownSeconds": 5.0,
        },
    },
    "ptz_controller": {
        "title": "PTZ Controller (ONVIF)",
        "subtitle": "Kontroler auto-following kamera PTZ fisik menjaga target tetap di tengah",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 800,
        "config": {
            "cameraIp": "192.168.1.100",
            "onvifPort": 80,
            "targetClass": "person",
            "targetTrackId": "",
            "deadzonePercent": 0.15,
            "panSpeed": 0.6,
            "tiltSpeed": 0.6,
        },
    },
    "screenshot_capture": {
        "title": "Screenshot Capture",
        "subtitle": "Ambil tangkapan layar full annotated, raw frame, atau crop objek ke memori",
        "category": "Outputs & Export",
        "x": 910,
        "y": 740,
        "config": {
            "captureMode": "full_annotated",
            "jpegQuality": 85,
            "addTimestampWatermark": True,
            "saveToDisk": False,
            "outputDirectory": "data/snapshots",
        },
    },
    "telegram_notification": {
        "title": "Telegram Alert",
        "subtitle": "Kirim foto tangkapan layar dan pesan peringatan langsung ke bot Telegram",
        "category": "Outputs & Export",
        "x": 910,
        "y": 825,
        "config": {
            "botToken": "",
            "chatId": "",
            "messageCaption": "🚨 <b>PERINGATAN SISTEM VISI</b>\n\n📌 <b>Kejadian:</b> {event.type}\n📍 <b>Zona:</b> {event.zoneName}\n🕒 <b>Waktu:</b> {timestamp}\n🔍 <b>Detail:</b> {event.message}",
            "parseMode": "HTML",
            "cooldownSeconds": 5.0,
            "disableNotification": False,
        },
    },
    "dashboard_sink": {
        "title": "Dashboard Output",
        "subtitle": "Salurkan metrik angka, status alert, dan event ke Dashboard Builder & Grafana",
        "category": "Outputs & Export",
        "x": 910,
        "y": 910,
        "config": {
            "metricKey": "total_count",
            "metricLabel": "Total Deteksi",
            "metricSource": "count",
            "unit": "Objek",
            "warningThreshold": 10.0,
            "dangerThreshold": 20.0,
            "cameraLabel": "Kamera 01",
            "streamId": "cam_01",
            "enableAlert": True,
            "alertMessage": "Ambang batas deteksi terlampaui",
            "flushIntervalSeconds": 1.0,
        },
    },
    "incident_video_recorder": {
        "title": "Incident Video Recorder",
        "subtitle": "Rekam klip MP4 otomatis dengan rolling buffer RAM (pre & post buffer insiden)",
        "category": "Outputs & Export",
        "x": 910,
        "y": 980,
        "config": {
            "triggerMode": "on_detection",
            "targetClass": "person",
            "preBufferSeconds": 5.0,
            "postBufferSeconds": 10.0,
            "fps": 20.0,
            "cooldownSeconds": 15.0,
            "outputDirectory": "data/recordings",
        },
    },
    "mqtt_publisher": {
        "title": "MQTT Publisher",
        "subtitle": "Publikasikan telemetri & event K3 ke MQTT Broker (PLC, SCADA, Home Assistant)",
        "category": "Outputs & Export",
        "x": 910,
        "y": 1050,
        "config": {
            "brokerHost": "localhost",
            "brokerPort": 1883,
            "topic": "afivision/alerts",
            "qos": 0,
            "retain": False,
            "publishMode": "on_event",
            "payloadFormat": "json",
            "customTemplate": "",
            "minPublishIntervalSeconds": 1.0,
        },
    },
    "crowd_density_heatmap": {
        "title": "Crowd Density Heatmap",
        "subtitle": "Akumulasi spasial jejak mobilitas & kepadatan kerumunan 2D Gaussian",
        "category": "Visualisasi & Anotasi",
        "x": 910,
        "y": 420,
        "config": {
            "targetClass": "person",
            "colormap": "jet",
            "opacity": 0.45,
            "kernelRadiusPx": 24,
            "decayFactor": 0.985,
            "minDensityThreshold": 0.08,
            "resolutionScale": 0.5,
        },
    },
    "ppe_compliance_matrix": {
        "title": "PPE Compliance Matrix",
        "subtitle": "Evaluasi komposit kelengkapan APD K3 (Helm, Rompi, Sepatu) per pekerja",
        "category": "Tracking & Analysis",
        "x": 620,
        "y": 760,
        "config": {
            "requiredPPE": ["helmet", "vest"],
            "minComplianceScore": 70.0,
            "alarmCooldownSeconds": 5.0,
            "showBadgeOverlay": True,
        },
    },
}
