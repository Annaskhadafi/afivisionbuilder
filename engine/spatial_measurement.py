"""
Spatial Measurement Module:
- Distance Measurement (2D Euclidean / Axis distance between detected objects with safety threshold alert)
- Size Measurement (Physical width, height, area calculation with tolerance check)
"""

import math
import time
from typing import Any, Dict, List, Optional, Tuple


def calculate_centroid(bbox: List[float]) -> Tuple[float, float]:
    """Calculate center point (cx, cy) from bbox [x, y, w, h]."""
    x, y, w, h = bbox
    return x + w / 2.0, y + h / 2.0


def calculate_bottom_center(bbox: List[float]) -> Tuple[float, float]:
    """Calculate bottom center point (cx, bottom_y) from bbox [x, y, w, h] for ground plane proximity."""
    x, y, w, h = bbox
    return x + w / 2.0, y + h


def measure_distance_between_objects(
    frame: Any,
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Measures physical distance (cm/m) between instances of objectAClass and objectBClass.
    
    Returns:
        (measurements_list, events_list)
    """
    if state is None:
        state = {}

    obj_a_class = str(config.get("objectAClass", "person")).strip().lower()
    obj_b_class = str(config.get("objectBClass", "forklift")).strip().lower()
    axis = str(config.get("measurementAxis", "euclidean")).strip().lower()
    pixel_ratio = float(config.get("pixelRatio", 10.0))  # pixels per cm
    if pixel_ratio <= 0:
        pixel_ratio = 10.0

    min_distance_threshold = float(config.get("minDistanceThreshold", 150.0))  # in cm
    trigger_alarm = bool(config.get("triggerAlarmOnProximity", True))
    cooldown_seconds = float(config.get("alarmCooldownSeconds", 3.0))
    anchor_mode = str(config.get("anchorMode", "bottom_center")).strip().lower()

    # Filter candidates
    instances_a = []
    instances_b = []

    for det in detections:
        cls_name = str(det.get("class", "")).strip().lower()
        bbox = det.get("bbox")
        if not bbox or len(bbox) < 4:
            continue
        if cls_name == obj_a_class:
            instances_a.append(det)
        if cls_name == obj_b_class:
            instances_b.append(det)

    # If objectAClass == objectBClass, we compare pairs within the same class (without self-comparison)
    same_class = obj_a_class == obj_b_class

    measurements = []
    events = []
    now = time.monotonic()
    last_alarm_time = state.get("last_distance_alarm_ts", 0.0)

    for i, a in enumerate(instances_a):
        bbox_a = a["bbox"]
        pt_a = calculate_bottom_center(bbox_a) if anchor_mode == "bottom_center" else calculate_centroid(bbox_a)
        id_a = a.get("trackId", a.get("track_id", a.get("id", f"a_{i}")))

        b_list = instances_b[i + 1:] if same_class else instances_b
        for j, b in enumerate(b_list):
            id_b = b.get("trackId", b.get("track_id", b.get("id", f"b_{j}")))
            if id_a == id_b:
                continue

            bbox_b = b["bbox"]
            pt_b = calculate_bottom_center(bbox_b) if anchor_mode == "bottom_center" else calculate_centroid(bbox_b)

            dx = abs(pt_b[0] - pt_a[0])
            dy = abs(pt_b[1] - pt_a[1])

            if axis == "horizontal":
                dist_px = dx
            elif axis == "vertical":
                dist_px = dy
            else:  # euclidean
                dist_px = math.sqrt(dx * dx + dy * dy)

            dist_cm = dist_px / pixel_ratio
            is_violation = dist_cm < min_distance_threshold

            item = {
                "object_a": {"class": a.get("class"), "id": id_a, "point": pt_a},
                "object_b": {"class": b.get("class"), "id": id_b, "point": pt_b},
                "distance_px": round(dist_px, 1),
                "distance_cm": round(dist_cm, 1),
                "threshold_cm": min_distance_threshold,
                "is_violation": is_violation,
            }
            measurements.append(item)

            if is_violation and trigger_alarm:
                if (now - last_alarm_time) >= cooldown_seconds:
                    events.append({
                        "event_type": "proximity_violation",
                        "severity": "warning" if dist_cm > (min_distance_threshold * 0.5) else "critical",
                        "message": f"Peringatan jarak dekat: {a.get('class')} (ID {id_a}) dan {b.get('class')} (ID {id_b}) terdeteksi berjarak {round(dist_cm, 1)} cm (batas aman: {min_distance_threshold} cm)",
                        "data": item,
                        "timestamp": now,
                    })
                    state["last_distance_alarm_ts"] = now
                    last_alarm_time = now

    return measurements, events


def measure_object_dimensions(
    frame: Any,
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Measures physical dimensions (width, height, area) for detections matching targetClass.
    
    Returns:
        (augmented_detections, events_list)
    """
    target_class = str(config.get("targetClass", "all")).strip().lower()
    pixel_per_unit = float(config.get("pixelPerUnit", 10.0))
    if pixel_per_unit <= 0:
        pixel_per_unit = 10.0

    unit_name = str(config.get("unitName", "cm")).strip().lower()
    min_w = float(config.get("minAllowedWidth", 0.0))
    max_w = float(config.get("maxAllowedWidth", 0.0))
    min_h = float(config.get("minAllowedHeight", 0.0))
    max_h = float(config.get("maxAllowedHeight", 0.0))
    trigger_alarm = bool(config.get("triggerAlarmOnToleranceViolation", False))

    augmented_detections = []
    events = []

    for det in detections:
        det_copy = dict(det)
        cls_name = str(det_copy.get("class", "")).strip().lower()

        if target_class in ("all", "*", "") or cls_name == target_class:
            bbox = det_copy.get("bbox", [0, 0, 0, 0])
            w_px = float(bbox[2]) if len(bbox) > 2 else 0.0
            h_px = float(bbox[3]) if len(bbox) > 3 else 0.0

            w_phys = w_px / pixel_per_unit
            h_phys = h_px / pixel_per_unit
            area_phys = w_phys * h_phys

            is_valid = True
            reasons = []

            if min_w > 0 and w_phys < min_w:
                is_valid = False
                reasons.append(f"width {round(w_phys, 1)} < min {min_w}")
            if max_w > 0 and w_phys > max_w:
                is_valid = False
                reasons.append(f"width {round(w_phys, 1)} > max {max_w}")
            if min_h > 0 and h_phys < min_h:
                is_valid = False
                reasons.append(f"height {round(h_phys, 1)} < min {min_h}")
            if max_h > 0 and h_phys > max_h:
                is_valid = False
                reasons.append(f"height {round(h_phys, 1)} > max {max_h}")

            measurements_dict = {
                "width": round(w_phys, 2),
                "height": round(h_phys, 2),
                "area": round(area_phys, 2),
                "unit": unit_name,
                "is_within_tolerance": is_valid,
                "reasons": reasons,
            }
            det_copy["measurements"] = measurements_dict

            if not is_valid and trigger_alarm:
                events.append({
                    "event_type": "dimension_tolerance_violation",
                    "severity": "warning",
                    "message": f"Dimensi objek {cls_name} di luar batas toleransi: {', '.join(reasons)} ({unit_name})",
                    "data": {
                        "class": cls_name,
                        "track_id": det_copy.get("track_id"),
                        "measurements": measurements_dict,
                    },
                    "timestamp": time.monotonic(),
                })

        augmented_detections.append(det_copy)

    return augmented_detections, events


def draw_distance_measurement_overlay(frame: Any, measurements: List[Dict[str, Any]]) -> None:
    """Draws measurement line connecting object pairs and distance label badge."""
    if frame is None or not hasattr(frame, "shape"):
        return
    import cv2
    for m in measurements:
        pt_a = m.get("object_a", {}).get("point")
        pt_b = m.get("object_b", {}).get("point")
        if not pt_a or not pt_b:
            continue
        p1 = (int(pt_a[0]), int(pt_a[1]))
        p2 = (int(pt_b[0]), int(pt_b[1]))
        is_viol = m.get("is_violation", False)
        color = (0, 0, 230) if is_viol else (0, 200, 50)  # Red if violation, green if safe

        cv2.line(frame, p1, p2, color, 2, cv2.LINE_AA)
        cv2.circle(frame, p1, 4, color, -1)
        cv2.circle(frame, p2, 4, color, -1)

        mx, my = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
        label = f"{m.get('distance_cm', 0):.1f} cm"
        cv2.putText(frame, label, (mx - 25, my - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, label, (mx - 25, my - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

