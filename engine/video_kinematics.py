"""
Video Kinematics Module:
- Velocity Calculator (Real-world speed estimation in km/h or m/s from tracked centroids)
- Path Deviation (Virtual lane / corridor deviation monitoring for AGVs, forklifts, vehicles)
"""

import math
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


def _extract_box(det: Dict[str, Any]) -> Optional[Tuple[float, float, float, float]]:
    """Extracts (x, y, w, h) from detection dictionary in any format."""
    box = det.get("bbox") or det.get("box")
    if box and len(box) >= 4:
        return float(box[0]), float(box[1]), float(box[2]), float(box[3])
    if all(k in det for k in ("x", "y", "width", "height")):
        return float(det["x"]), float(det["y"]), float(det["width"]), float(det["height"])
    xyxy = det.get("xyxy")
    if xyxy and len(xyxy) >= 4:
        x1, y1, x2, y2 = (float(v) for v in xyxy[:4])
        return x1, y1, max(1.0, x2 - x1), max(1.0, y2 - y1)
    return None


def _hex_to_bgr(hex_str: str, default_bgr: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Converts hex color (e.g. #10b981) to OpenCV BGR tuple."""
    if not isinstance(hex_str, str):
        return default_bgr
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 6:
        try:
            r = int(clean[0:2], 16)
            g = int(clean[2:4], 16)
            b = int(clean[4:6], 16)
            return (b, g, r)
        except ValueError:
            pass
    return default_bgr


def _match_or_assign_track_id(
    det: Dict[str, Any],
    box: Tuple[float, float, float, float],
    state: Dict[str, Any],
    now: float
) -> Any:
    """Gets existing trackId or auto-assigns ID via spatial proximity when untracked."""
    tid = det.get("trackId")
    if tid is None:
        tid = det.get("track_id")
    if tid is None:
        tid = det.get("id")
    if tid is not None:
        return tid

    auto_tracks = state.setdefault("_auto_tracks", {})
    bx, by, bw, bh = box
    bcx, bcy = bx + bw / 2.0, by + bh / 2.0

    best_id = None
    best_dist = 80.0  # max 80px centroid jump between consecutive frames
    for at_id, at_data in list(auto_tracks.items()):
        if now - at_data["last_seen"] > 1.5:
            continue
        p_cx, p_cy = at_data["last_center"]
        d = math.hypot(bcx - p_cx, bcy - p_cy)
        if d < best_dist:
            best_dist = d
            best_id = at_id

    if best_id is not None:
        auto_tracks[best_id]["last_seen"] = now
        auto_tracks[best_id]["last_center"] = (bcx, bcy)
        return best_id

    next_id = state.setdefault("_next_auto_id", 1)
    assigned = next_id
    state["_next_auto_id"] = next_id + 1
    auto_tracks[assigned] = {
        "first_seen": now,
        "last_seen": now,
        "last_center": (bcx, bcy)
    }
    return assigned


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
    node_id: Optional[str] = "velocity_calculator",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Calculates velocity for tracked objects based on spatial displacement over elapsed time.
    Enriches detections in-place with velocity metrics and emits overspeed alert events.
    
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
    smoothing_window = max(2, min(20, int(config.get("smoothingWindow", 5))))
    min_speed_kmh = float(config.get("minSpeedKmh", 0.5))
    trigger_alarm = bool(config.get("triggerAlarmOnSpeeding", True))
    alarm_cooldown = float(config.get("alarmCooldownSeconds", 3.0))
    show_overlay = bool(config.get("showOverlay", True))
    show_track_id = bool(config.get("showTrackId", True))
    badge_pos = str(config.get("badgePosition", "top")).strip().lower()
    normal_color = str(config.get("normalColor", "#10b981"))
    alert_color = str(config.get("alertColor", "#ef4444"))

    target_classes_raw = str(config.get("targetClasses", "")).strip().lower()
    target_classes = {c.strip() for c in target_classes_raw.split(",") if c.strip()} if target_classes_raw and target_classes_raw not in ("*", "all") else None

    # state["track_history"]: {track_id: [(timestamp, cx, cy), ...]}
    history = state.setdefault("track_history", {})
    last_alarm_times = state.setdefault("last_alarm_times", {})

    augmented = []
    events = []
    active_track_ids = set()

    for det in detections:
        box = _extract_box(det)
        if not box or box[2] <= 0 or box[3] <= 0:
            augmented.append(det)
            continue

        cls_name = str(det.get("class", "object")).strip()
        if target_classes and cls_name.lower() not in target_classes:
            augmented.append(det)
            continue

        track_id = _match_or_assign_track_id(det, box, state, now)
        active_track_ids.add(track_id)

        cx = box[0] + box[2] / 2.0
        cy = box[1] + box[3] / 2.0

        track_pts = history.setdefault(track_id, [])
        track_pts.append((now, cx, cy))
        if len(track_pts) > smoothing_window:
            track_pts.pop(0)

        speed_kmh = 0.0
        speed_mps = 0.0
        speed_mph = 0.0

        if len(track_pts) >= 2:
            prev_time, prev_x, prev_y = track_pts[0]
            dt = now - prev_time
            if dt > 0.02:  # at least ~1 frame duration
                dx = cx - prev_x
                dy = cy - prev_y
                dist_px = math.hypot(dx, dy)
                dist_meters = dist_px / pixel_per_meter
                speed_mps = dist_meters / dt
                speed_kmh = speed_mps * 3.6
                speed_mph = speed_kmh * 0.621371

        # Deadzone filter for stationary jitter
        if min_speed_kmh > 0 and speed_kmh < min_speed_kmh:
            speed_kmh = 0.0
            speed_mps = 0.0
            speed_mph = 0.0

        if speed_unit == "mps":
            speed_formatted = f"{round(speed_mps, 1)} m/s"
        elif speed_unit == "mph":
            speed_formatted = f"{round(speed_mph, 1)} mph"
        else:
            speed_formatted = f"{round(speed_kmh, 1)} km/h"

        is_overspeed = bool(speed_limit_kmh > 0 and speed_kmh > speed_limit_kmh)

        # Mutate / enrich detection in-place
        det["speed_kmh"] = round(speed_kmh, 1)
        det["speed_mps"] = round(speed_mps, 2)
        det["speed_mph"] = round(speed_mph, 1)
        det["speed_formatted"] = speed_formatted
        det["is_overspeed"] = is_overspeed
        det["showVelocityOverlay"] = show_overlay
        det["velocityConfig"] = {
            "speedLimitKmh": speed_limit_kmh,
            "speedUnit": speed_unit,
            "badgePosition": badge_pos,
            "showTrackId": show_track_id,
            "normalColor": normal_color,
            "alertColor": alert_color,
        }
        if "trackId" not in det and track_id is not None:
            det["trackId"] = track_id
        if "track_id" not in det and track_id is not None:
            det["track_id"] = track_id

        if is_overspeed and trigger_alarm:
            last_alarm = last_alarm_times.get(track_id, 0.0)
            if last_alarm == 0.0 or (now - last_alarm) >= alarm_cooldown:
                event_dict = {
                    "kind": "overspeed_detected",
                    "event_type": "overspeed_detected",
                    "type": "overspeed_detected",
                    "sourceNodeId": str(node_id or "velocity_calculator"),
                    "trackId": track_id,
                    "track_id": track_id,
                    "class": cls_name,
                    "speed_kmh": round(speed_kmh, 1),
                    "speed_mps": round(speed_mps, 2),
                    "speed_formatted": speed_formatted,
                    "speed_limit_kmh": speed_limit_kmh,
                    "threshold": speed_limit_kmh,
                    "severity": "critical" if speed_kmh > (speed_limit_kmh * 1.5) else "warning",
                    "message": f"Peringatan Kecepatan: {cls_name} (#{track_id}) melaju {speed_formatted} (Batas maksimal: {speed_limit_kmh:g} km/h)",
                    "timestamp": now,
                    "bbox": [box[0], box[1], box[2], box[3]],
                    "data": {
                        "track_id": track_id,
                        "trackId": track_id,
                        "class": cls_name,
                        "speed_kmh": round(speed_kmh, 1),
                        "speed_mps": round(speed_mps, 2),
                        "speed_formatted": speed_formatted,
                        "speed_limit_kmh": speed_limit_kmh,
                    },
                }
                events.append(event_dict)
                last_alarm_times[track_id] = now

        augmented.append(det)

    # Prune old tracks no longer in frame (retain up to 100 recent)
    if len(history) > 100:
        for tid in list(history.keys()):
            if tid not in active_track_ids:
                del history[tid]
                last_alarm_times.pop(tid, None)

    return augmented, events


def draw_single_velocity_badge(
    frame: Any,
    det: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """Draws a sleek, modern industrial velocity badge directly on the video frame."""
    if frame is None or not hasattr(frame, "shape"):
        return

    import cv2

    cfg = config or det.get("velocityConfig") or {}
    box = _extract_box(det)
    if not box:
        return

    x, y, w, h = box
    formatted = det.get("speed_formatted")
    if not formatted:
        return

    is_overspeed = bool(det.get("is_overspeed", False))
    track_id = det.get("trackId", det.get("track_id"))

    show_track_id = bool(cfg.get("showTrackId", True))
    badge_pos = str(cfg.get("badgePosition", "top")).strip().lower()

    if show_track_id and track_id is not None:
        tag_text = f"#{track_id} {formatted}"
    else:
        tag_text = formatted

    if is_overspeed:
        tag_text = f"{tag_text} OVERSPEED"

    normal_hex = str(cfg.get("normalColor", "#10b981"))
    alert_hex = str(cfg.get("alertColor", "#ef4444"))

    normal_bgr = _hex_to_bgr(normal_hex, (129, 185, 16))
    alert_bgr = _hex_to_bgr(alert_hex, (68, 68, 239))
    accent_color = alert_bgr if is_overspeed else normal_bgr

    font_scale = 0.42
    font_thick = 1
    text_size, _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thick)

    icon_gap = 16
    pad_x = 8
    pad_y = 5
    badge_w = text_size[0] + icon_gap + (pad_x * 2)
    badge_h = text_size[1] + (pad_y * 2)

    frame_h, frame_w = frame.shape[:2]

    if badge_pos == "bottom":
        bx = int(x + (w - badge_w) / 2)
        by = int(y + h + badge_h + 4)
    elif badge_pos == "inside":
        bx = int(x + 4)
        by = int(y + badge_h + 4)
    else:  # top
        bx = int(x + (w - badge_w) / 2)
        by = int(y - 6)

    # Clamp coordinates
    bx = max(2, min(frame_w - badge_w - 2, bx))
    by = max(badge_h + 2, min(frame_h - 4, by))

    top_left = (bx, by - badge_h)
    bottom_right = (bx + badge_w, by)

    # Dark slate background
    cv2.rectangle(frame, top_left, bottom_right, (15, 23, 42), -1)
    # Accent border
    cv2.rectangle(frame, top_left, bottom_right, accent_color, 1, cv2.LINE_AA)

    # Draw Speedometer / Alert icon
    icon_cx = bx + pad_x + 5
    icon_cy = by - (badge_h // 2)
    if is_overspeed:
        # Warning triangle icon
        tri_pts = np.array([
            [icon_cx, icon_cy - 5],
            [icon_cx - 5, icon_cy + 4],
            [icon_cx + 5, icon_cy + 4]
        ], np.int32)
        cv2.polylines(frame, [tri_pts], True, accent_color, 1, cv2.LINE_AA)
        cv2.line(frame, (icon_cx, icon_cy - 2), (icon_cx, icon_cy + 1), accent_color, 1, cv2.LINE_AA)
        cv2.circle(frame, (icon_cx, icon_cy + 3), 1, accent_color, -1, cv2.LINE_AA)
    else:
        # Speedometer arc + needle
        cv2.ellipse(frame, (icon_cx, icon_cy + 2), (5, 5), 0, 180, 360, accent_color, 1, cv2.LINE_AA)
        cv2.line(frame, (icon_cx, icon_cy + 2), (icon_cx + 3, icon_cy - 1), accent_color, 1, cv2.LINE_AA)

    # Render text
    text_x = bx + pad_x + icon_gap
    text_y = by - pad_y
    cv2.putText(
        frame,
        tag_text,
        (text_x, text_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        (255, 255, 255),
        font_thick,
        cv2.LINE_AA,
    )


def check_path_deviation(
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    frame_size: Optional[Tuple[int, int]] = None,
    now: Optional[float] = None,
    node_id: Optional[str] = "path_deviation",
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

        box = _extract_box(det_copy)
        if not box or box[2] <= 0 or box[3] <= 0:
            augmented.append(det_copy)
            continue

        # Use bottom center (ground contact)
        cx = box[0] + box[2] / 2.0
        cy = box[1] + box[3]

        deviation_meters = 0.0
        is_deviated = False

        if len(polyline) >= 2:
            dist_px = point_to_polyline_distance(cx, cy, polyline)
            deviation_meters = dist_px / pixel_per_meter
            is_deviated = deviation_meters > max_deviation_meters

        det_copy["deviation_meters"] = round(deviation_meters, 2)
        det_copy["is_path_deviated"] = is_deviated

        track_id = det_copy.get("trackId", det_copy.get("track_id", det_copy.get("id", "0")))
        if is_deviated and trigger_alarm:
            last_alarm = last_alarm_times.get(track_id, 0.0)
            if last_alarm == 0.0 or (now - last_alarm) >= alarm_cooldown:
                events.append({
                    "kind": "path_deviation_detected",
                    "event_type": "path_deviation_detected",
                    "type": "path_deviation_detected",
                    "sourceNodeId": str(node_id or "path_deviation"),
                    "trackId": track_id,
                    "track_id": track_id,
                    "class": cls_name,
                    "severity": "warning",
                    "message": f"Penyimpangan Jalur: {cls_name} (ID {track_id}) menyimpang sejauh {round(deviation_meters, 1)} m dari lintasan (Batas toleransi: {max_deviation_meters} m)",
                    "data": {
                        "track_id": track_id,
                        "trackId": track_id,
                        "class": cls_name,
                        "deviation_meters": round(deviation_meters, 2),
                        "max_allowed_meters": max_deviation_meters,
                    },
                    "timestamp": now,
                    "bbox": list(box),
                })
                last_alarm_times[track_id] = now

        augmented.append(det_copy)

    return augmented, events
