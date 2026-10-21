"""
Dominant Color Inspection & Attribute Extractor Module:
- Analyzes dominant color (HSV/RGB) in detection bounding boxes or sub-regions (torso, helmet, full).
- High-visibility safety vest (hi-vis green, orange) and helmet color compliance verification.
- Enriches DetectionRecord with color attributes and emits compliance/violation events.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


# Standard industrial safety presets in OpenCV HSV [H: 0-179, S: 0-255, V: 0-255]
COLOR_PRESETS = {
    "hi_vis_green": {
        "hsv_min": (35, 70, 70),
        "hsv_max": (85, 255, 255),
        "hex": "#84cc16",
        "label": "Safety Green (Fluo)",
    },
    "hi_vis_orange": {
        "hsv_min": (5, 110, 110),
        "hsv_max": (22, 255, 255),
        "hex": "#f97316",
        "label": "Safety Orange",
    },
    "helmet_white": {
        "hsv_min": (0, 0, 160),
        "hsv_max": (180, 45, 255),
        "hex": "#f8fafc",
        "label": "White (Supervisor)",
    },
    "helmet_yellow": {
        "hsv_min": (22, 90, 120),
        "hsv_max": (36, 255, 255),
        "hex": "#eab308",
        "label": "Yellow (Operator)",
    },
    "helmet_red": {
        "hsv_min": (0, 120, 100),
        "hsv_max": (6, 255, 255),
        "hex": "#ef4444",
        "label": "Red (Safety Officer)",
    },
    "safety_blue": {
        "hsv_min": (95, 80, 80),
        "hsv_max": (130, 255, 255),
        "hex": "#3b82f6",
        "label": "Blue (Technician)",
    },
}


def _extract_sub_region(frame: np.ndarray, bbox: List[float], region_mode: str) -> Optional[np.ndarray]:
    """Crops specified sub-region of bbox to avoid background noise."""
    if frame is None or not hasattr(frame, "shape"):
        return None
    fh, fw = frame.shape[:2]
    x, y, w, h = bbox
    x1, y1 = max(0, int(round(x))), max(0, int(round(y)))
    x2, y2 = min(fw, int(round(x + w))), min(fh, int(round(y + h)))
    if x2 <= x1 or y2 <= y1:
        return None

    full_crop = frame[y1:y2, x1:x2]
    ch, cw = full_crop.shape[:2]
    if ch < 4 or cw < 4:
        return None

    mode = str(region_mode).strip().lower()
    if mode == "torso":
        # Upper chest & abdomen (avoid head and legs)
        ry1 = int(round(ch * 0.18))
        ry2 = int(round(ch * 0.65))
        rx1 = int(round(cw * 0.15))
        rx2 = int(round(cw * 0.85))
        crop = full_crop[ry1:ry2, rx1:rx2]
        return crop if crop.size > 0 else full_crop
    elif mode in ("head", "top_quarter"):
        # Upper 25% of bbox (ideal for helmet)
        ry2 = max(4, int(round(ch * 0.28)))
        rx1 = int(round(cw * 0.15))
        rx2 = int(round(cw * 0.85))
        crop = full_crop[0:ry2, rx1:rx2]
        return crop if crop.size > 0 else full_crop
    elif mode == "bottom_half":
        crop = full_crop[int(round(ch * 0.5)):ch, :]
        return crop if crop.size > 0 else full_crop
    return full_crop


def inspect_dominant_color(
    frame: np.ndarray,
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    now: Optional[float] = None,
    node_id: str = "dominant_color",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluates color composition in detection bounding boxes.

    Returns:
        (augmented_detections, color_events)
    """
    if state is None:
        state = {}
    if now is None:
        now = time.monotonic()

    target_class = str(config.get("targetClass", "person")).strip().lower()
    allowed_classes = [c.strip().lower() for c in target_class.split(",") if c.strip()]
    if not allowed_classes or "all" in allowed_classes:
        allowed_classes = []

    sub_region = str(config.get("subRegion", "torso")).strip().lower()
    min_match_percent = float(config.get("minMatchPercent", 15.0))
    require_match = bool(config.get("requireMatch", False))
    preset_target = str(config.get("targetPreset", "hi_vis_green")).strip().lower()
    attribute_key = str(config.get("attributeKey", "vest_color")).strip() or "vest_color"
    cooldown_seconds = float(config.get("alarmCooldownSeconds", 5.0))
    last_alarm_time = state.setdefault("_last_alarm_time", {})

    augmented = []
    events = []

    for det in detections:
        cls_name = str(det.get("class", "")).strip().lower()
        if allowed_classes and cls_name not in allowed_classes:
            augmented.append(det)
            continue

        bbox = det.get("bbox")
        if not bbox and "x" in det and "width" in det:
            bbox = [det["x"], det["y"], det["width"], det["height"]]
        if not bbox or len(bbox) < 4:
            augmented.append(det)
            continue

        crop = _extract_sub_region(frame, bbox, sub_region)
        if crop is None or crop.size == 0:
            augmented.append(det)
            continue

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        total_pixels = float(crop.shape[0] * crop.shape[1])

        # Evaluate against active preset or custom HSV
        preset_info = COLOR_PRESETS.get(preset_target)
        if preset_info:
            h_min, s_min, v_min = preset_info["hsv_min"]
            h_max, s_max, v_max = preset_info["hsv_max"]
            color_hex = preset_info["hex"]
            color_label = preset_info["label"]
        else:
            # Custom HSV parsing
            h_min = int(config.get("customHsvMinH", 35))
            s_min = int(config.get("customHsvMinS", 70))
            v_min = int(config.get("customHsvMinV", 70))
            h_max = int(config.get("customHsvMaxH", 85))
            s_max = int(config.get("customHsvMaxS", 255))
            v_max = int(config.get("customHsvMaxV", 255))
            color_hex = str(config.get("customHex", "#84cc16"))
            color_label = str(config.get("customLabel", "Custom Color"))

        mask = cv2.inRange(hsv, (h_min, s_min, v_min), (h_max, s_max, v_max))
        matching_pixels = float(cv2.countNonZero(mask))
        match_ratio = (matching_pixels / total_pixels) * 100.0 if total_pixels > 0 else 0.0
        is_matched = match_ratio >= min_match_percent

        det_copy = dict(det)
        attrs = dict(det_copy.get("attributes") or {})
        attrs[attribute_key] = color_label if is_matched else "none"
        attrs[f"{attribute_key}_hex"] = color_hex if is_matched else "#64748b"
        attrs[f"{attribute_key}_pct"] = round(match_ratio, 1)
        attrs[f"{attribute_key}_compliant"] = is_matched
        det_copy["attributes"] = attrs
        det_copy["dominantColorMatch"] = is_matched
        det_copy["dominantColorPct"] = round(match_ratio, 1)
        det_copy["dominantColorHex"] = color_hex if is_matched else "#64748b"
        augmented.append(det_copy)

        # Trigger compliance or violation event
        track_id = det_copy.get("track_id", det_copy.get("id", "obj"))
        alarm_key = f"{node_id}:{track_id}"
        if require_match and not is_matched:
            if now - last_alarm_time.get(alarm_key, 0) >= cooldown_seconds:
                last_alarm_time[alarm_key] = now
                events.append({
                    "event_type": "COLOR_NON_COMPLIANCE",
                    "type": "COLOR_NON_COMPLIANCE",
                    "severity": "WARNING",
                    "message": f"Pelanggaran K3: {cls_name} ID #{track_id} tidak mengenakan {color_label} ({match_ratio:.1f}% < {min_match_percent}%)",
                    "zoneName": "Color Inspection",
                    "track_id": track_id,
                    "target_color": color_label,
                    "actual_ratio": round(match_ratio, 1),
                    "timestamp": now,
                })
        elif not require_match and is_matched:
            # Informational match event
            if now - last_alarm_time.get(alarm_key, 0) >= cooldown_seconds:
                last_alarm_time[alarm_key] = now
                events.append({
                    "event_type": "COLOR_MATCH_DETECTED",
                    "type": "COLOR_MATCH_DETECTED",
                    "severity": "INFO",
                    "message": f"Terdeteksi {color_label} pada {cls_name} ID #{track_id} ({match_ratio:.1f}%)",
                    "zoneName": "Color Inspection",
                    "track_id": track_id,
                    "target_color": color_label,
                    "actual_ratio": round(match_ratio, 1),
                    "timestamp": now,
                })

    return augmented, events


def draw_dominant_color_badges(frame: np.ndarray, detections: List[Dict[str, Any]]) -> None:
    """Draws a compact color pill badge above detections."""
    if frame is None or not hasattr(frame, "shape"):
        return
    fh, fw = frame.shape[:2]
    for det in detections:
        pct = det.get("dominantColorPct")
        if pct is None:
            continue
        bbox = det.get("bbox")
        if not bbox and "x" in det and "width" in det:
            bbox = [det["x"], det["y"], det["width"], det["height"]]
        if not bbox or len(bbox) < 4:
            continue
        x, y, w, h = bbox
        x1, y1 = int(round(x)), int(round(y))
        matched = bool(det.get("dominantColorMatch", False))
        tag = f"{pct:.0f}%"
        color_bgr = (22, 163, 74) if matched else (100, 116, 139)  # Green or Slate
        badge_y = max(18, y1 - 4)
        cv2.rectangle(frame, (x1, badge_y - 14), (x1 + 38, badge_y), color_bgr, -1)
        cv2.putText(frame, tag, (x1 + 3, badge_y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)
