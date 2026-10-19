"""
Video Kinematics Module:
- Velocity Calculator (Real-world speed estimation in km/h or m/s from tracked centroids)
- Path Deviation (Virtual lane / corridor deviation monitoring for AGVs, forklifts, vehicles)
"""

import math
import time
from typing import Any, Dict, List, Optional, Tuple


def point_to_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculates perpendicular Euclidean distance from point (px, py) to line segment (x1, y1)-(x2, y2)."""
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)

    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def point_to_polyline_distance(px: float, py: float, polyline: List[Tuple[float, float]]) -> float:
    """Calculates minimum perpendicular Euclidean distance from point (px, py) to a sequence of polyline vertices."""
    if not polyline:
        return 0.0
    if len(polyline) == 1:
        return math.hypot(px - polyline[0][0], py - polyline[0][1])

    min_dist = float("inf")
    for i in range(len(polyline) - 1):
        x1, y1 = polyline[i]
        x2, y2 = polyline[i + 1]
        dist = point_to_segment_distance(px, py, x1, y1, x2, y2)
        if dist < min_dist:
            min_dist = dist
    return min_dist


def calculate_object_velocities(
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    now: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Calculates velocity for tracked objects based on spatial displacement over elapsed time.
    
    Returns:
        (augmented_detections, speeding_events)
    """
    if state is None:
        state = {}
    if now is None:
        now = time.monotonic()

    pixel_per_meter = float(config.get("pixelPerMeter", 25.0))
    if pixel_per_meter <= 0:
        pixel_per_meter = 25.0

    speed_limit_kmh = float(config.get("speedLimitKmh", 15.0))
    speed_unit = str(config.get("speedUnit", "kmh")).strip().lower()
    smoothing_window = max(2, int(config.get("smoothingWindow", 5)))
    trigger_alarm = bool(config.get("triggerAlarmOnSpeeding", True))
    alarm_cooldown = float(config.get("alarmCooldownSeconds", 3.0))

    # state["track_history"]: {track_id: [(timestamp, cx, cy), ...]}
    history = state.setdefault("track_history", {})
    last_alarm_times = state.setdefault("last_alarm_times", {})

    augmented = []
    events = []

    active_track_ids = set()

    for det in detections:
        det_copy = dict(det)
        track_id = det_copy.get("track_id")
        bbox = det_copy.get("bbox")

        if track_id is None or not bbox or len(bbox) < 4:
            augmented.append(det_copy)
            continue

        active_track_ids.add(track_id)
        cx = bbox[0] + bbox[2] / 2.0
        cy = bbox[1] + bbox[3] / 2.0

        track_pts = history.setdefault(track_id, [])
        track_pts.append((now, cx, cy))
        if len(track_pts) > smoothing_window:
            track_pts.pop(0)

        speed_kmh = 0.0
        speed_mps = 0.0

        if len(track_pts) >= 2:
            prev_time, prev_x, prev_y = track_pts[0]
            dt = now - prev_time
            if dt > 0.03:  # at least ~1 frame duration
                dx = cx - prev_x
                dy = cy - prev_y
                dist_px = math.hypot(dx, dy)
                dist_meters = dist_px / pixel_per_meter
                speed_mps = dist_meters / dt
                speed_kmh = speed_mps * 3.6

        det_copy["speed_kmh"] = round(speed_kmh, 1)
        det_copy["speed_mps"] = round(speed_mps, 2)
        det_copy["speed_formatted"] = f"{round(speed_kmh, 1)} km/h" if speed_unit == "kmh" else f"{round(speed_mps, 1)} m/s"

        is_overspeed = speed_kmh > speed_limit_kmh
        det_copy["is_overspeed"] = is_overspeed

        if is_overspeed and trigger_alarm:
            last_alarm = last_alarm_times.get(track_id, 0.0)
            if last_alarm == 0.0 or (now - last_alarm) >= alarm_cooldown:
                cls_name = det_copy.get("class", "object")
                events.append({
                    "event_type": "overspeed_detected",
                    "severity": "critical" if speed_kmh > (speed_limit_kmh * 1.5) else "warning",
                    "message": f"Peringatan Kecepatan: {cls_name} (ID {track_id}) melaju {round(speed_kmh, 1)} km/h (Batas maksimal: {speed_limit_kmh} km/h)",
                    "data": {
                        "track_id": track_id,
                        "class": cls_name,
                        "speed_kmh": round(speed_kmh, 1),
                        "speed_mps": round(speed_mps, 2),
                        "speed_limit_kmh": speed_limit_kmh,
                    },
                    "timestamp": now,
                })
                last_alarm_times[track_id] = now

        augmented.append(det_copy)

    # Prune old tracks no longer in frame (retain up to 100 recent)
    if len(history) > 100:
        for tid in list(history.keys()):
            if tid not in active_track_ids:
                del history[tid]
                last_alarm_times.pop(tid, None)

    return augmented, events


def check_path_deviation(
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    frame_size: Optional[Tuple[int, int]] = None,
    now: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Checks if tracked objects deviate from a reference corridor/guide path.
    
    Returns:
        (augmented_detections, deviation_events)
    """
    if state is None:
        state = {}
    if now is None:
        now = time.monotonic()

    guide_path_str = str(config.get("guidePathPoints", "")).strip()
    max_deviation_meters = float(config.get("maxAllowedDeviationMeters", 1.5))
    pixel_per_meter = float(config.get("pixelPerMeter", 25.0))
    if pixel_per_meter <= 0:
        pixel_per_meter = 25.0

    target_classes_str = str(config.get("targetClasses", "forklift, vehicle")).strip().lower()
    target_classes = [c.strip() for c in target_classes_str.split(",") if c.strip()]
    trigger_alarm = bool(config.get("triggerAlarmOnDeviation", True))
    alarm_cooldown = float(config.get("alarmCooldownSeconds", 3.0))

    last_alarm_times = state.setdefault("last_deviation_alarms", {})

    # Parse polyline
    fw, fh = frame_size if frame_size else (1920, 1080)
    polyline = []
    if guide_path_str:
        raw_pairs = [p.strip() for p in guide_path_str.replace("\n", ";").split(";") if p.strip()]
        for pair in raw_pairs:
            parts = pair.split(",")
            if len(parts) >= 2:
                try:
                    x = float(parts[0].strip())
                    y = float(parts[1].strip())
                    if x <= 1.0 and y <= 1.0:
                        x = x * fw
                        y = y * fh
                    polyline.append((x, y))
                except ValueError:
                    continue

    augmented = []
    events = []

    for det in detections:
        det_copy = dict(det)
        cls_name = str(det_copy.get("class", "")).strip().lower()

        if target_classes and cls_name not in target_classes:
            augmented.append(det_copy)
            continue

        bbox = det_copy.get("bbox")
        if not bbox or len(bbox) < 4:
            augmented.append(det_copy)
            continue

        # Use bottom center (ground contact)
        cx = bbox[0] + bbox[2] / 2.0
        cy = bbox[1] + bbox[3]

        deviation_meters = 0.0
        is_deviated = False

        if len(polyline) >= 2:
            dist_px = point_to_polyline_distance(cx, cy, polyline)
            deviation_meters = dist_px / pixel_per_meter
            is_deviated = deviation_meters > max_deviation_meters

        det_copy["deviation_meters"] = round(deviation_meters, 2)
        det_copy["is_path_deviated"] = is_deviated

        track_id = det_copy.get("track_id", det_copy.get("id", "0"))
        if is_deviated and trigger_alarm:
            last_alarm = last_alarm_times.get(track_id, 0.0)
            if last_alarm == 0.0 or (now - last_alarm) >= alarm_cooldown:
                events.append({
                    "event_type": "path_deviation_detected",
                    "severity": "warning",
                    "message": f"Penyimpangan Jalur: {cls_name} (ID {track_id}) menyimpang sejauh {round(deviation_meters, 1)} m dari lintasan (Batas toleransi: {max_deviation_meters} m)",
                    "data": {
                        "track_id": track_id,
                        "class": cls_name,
                        "deviation_meters": round(deviation_meters, 2),
                        "max_allowed_meters": max_deviation_meters,
                    },
                    "timestamp": now,
                })
                last_alarm_times[track_id] = now

        augmented.append(det_copy)

    return augmented, events
