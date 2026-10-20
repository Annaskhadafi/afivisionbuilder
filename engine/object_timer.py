"""
Object Timer Module:
Tracks active duration for detected persons / objects across video frames.
Calculates elapsed presence time, attaches timer attributes to detections,
triggers alerts/events when duration exceeds a threshold, and renders sleek
industrial timer badges directly on or above detected objects in the video frame.
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Tuple


def format_timer(seconds: float, timer_format: str = "mm:ss") -> str:
    """Format duration in seconds into human-readable string."""
    seconds = max(0.0, float(seconds))
    fmt = str(timer_format or "mm:ss").strip().lower()
    if fmt == "seconds":
        return f"{seconds:.1f}s"
    if fmt == "hh:mm:ss":
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    # Default: "mm:ss"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def _box(det: Dict[str, Any]) -> Optional[Tuple[float, float, float, float]]:
    """Extract (x, y, w, h) from detection dictionary."""
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


def _calculate_iou(box_a: Tuple[float, float, float, float], box_b: Tuple[float, float, float, float]) -> float:
    """Calculate Intersection-over-Union between two boxes [x, y, w, h]."""
    ax, ay, aw, ah = box_a
    bx, by, bw, bh = box_b
    x1 = max(ax, bx)
    y1 = max(ay, by)
    x2 = min(ax + aw, bx + bw)
    y2 = min(ay + ah, by + bh)
    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h
    union_area = (aw * ah) + (bw * bh) - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def _hex_to_bgr(hex_str: str, default_bgr: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Convert hex color (e.g. #10b981 or #ef4444) to OpenCV BGR tuple."""
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


def process_object_timer(
    project_node: Dict[str, Any],
    frame: Any,
    detections: List[Dict[str, Any]],
    state: Dict[str, Any],
    now: float,
) -> List[Dict[str, Any]]:
    """
    Tracks elapsed presence time for detected objects matching targetClasses.
    Enriches each detection in-place with timer attributes and triggers alert events
    when an object has been present longer than alertThresholdSeconds.
    """
    config = project_node.get("config", {})
    node_id = str(project_node.get("id") or "object_timer")

    target_classes_raw = str(config.get("targetClasses", "person, face")).strip().lower()
    if target_classes_raw in ("*", "all", ""):
        target_classes = None
    else:
        target_classes = {c.strip() for c in target_classes_raw.split(",") if c.strip()}

    alert_threshold = float(config.get("alertThresholdSeconds", 10.0))
    grace_seconds = max(0.2, float(config.get("graceSeconds", 2.0)))
    timer_format = str(config.get("timerFormat", "mm:ss"))
    alert_mode = str(config.get("alertMode", "once")).strip().lower()
    alert_cooldown = max(1.0, float(config.get("alertCooldownSeconds", 5.0)))
    show_overlay = bool(config.get("showOverlay", True))
    min_duration = max(0.0, float(config.get("minDurationSeconds", 0.0)))

    # Internal state storage for active tracks
    tracks: Dict[str, Dict[str, Any]] = state.setdefault("tracks", {})
    next_auto_id: int = state.setdefault("next_auto_id", 1)

    matched_detections: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []

    def _is_target_match(det_item: Dict[str, Any]) -> bool:
        if target_classes is None:
            return True
        cls = str(det_item.get("class", "object")).strip().lower()
        base_cls = str(det_item.get("baseClass", "")).strip().lower()
        p_name = str(det_item.get("personName", "")).strip().lower()

        if cls in target_classes or (base_cls and base_cls in target_classes):
            return True

        # Face & Person interoperability: "person" target also accepts faces, and "face" accepts enrolled/tracked persons
        is_face = bool(cls == "face" or base_cls == "face" or "face" in cls or det_item.get("landmarks") is not None)
        is_person = bool(cls == "person" or base_cls == "person" or p_name or det_item.get("isEnrolled") is not None)

        if "person" in target_classes and (is_face or is_person):
            return True
        if "face" in target_classes and (is_face or is_person):
            return True
        if p_name and p_name in target_classes:
            return True
        return False

    # Map current detections to active tracks
    for det in detections:
        if not _is_target_match(det):
            continue

        cls_name = str(det.get("personName") or det.get("class", "object")).strip()

        box = _box(det)
        if box is None:
            continue

        track_id = det.get("trackId")
        if track_id is None:
            track_id = det.get("track_id")

        matched_key: Optional[str] = None

        if track_id is not None:
            track_key = f"{cls_name}:{track_id}"
            matched_key = track_key
        else:
            # Standalone fallback: match with existing active tracks by IoU
            best_iou = 0.0
            best_key = None
            for key, tr in tracks.items():
                if tr.get("class") == cls_name:
                    last_b = tr.get("lastBox")
                    if last_b:
                        iou = _calculate_iou(box, last_b)
                        if iou > best_iou and iou >= 0.3:
                            best_iou = iou
                            best_key = key
            if best_key is not None:
                matched_key = best_key
                track_id = tracks[best_key].get("trackId")
            else:
                track_id = next_auto_id
                state["next_auto_id"] = next_auto_id + 1
                matched_key = f"{cls_name}:auto_{track_id}"

        if matched_key not in tracks:
            tracks[matched_key] = {
                "firstSeen": now,
                "lastSeen": now,
                "alertEmitted": False,
                "lastAlertAt": 0.0,
                "trackId": track_id,
                "class": cls_name,
                "lastBox": box,
            }

        tr = tracks[matched_key]
        tr["lastSeen"] = now
        tr["lastBox"] = box
        elapsed = max(0.0, now - tr["firstSeen"])
        tr["elapsed"] = elapsed

        is_alert = bool(alert_threshold > 0.0 and elapsed >= alert_threshold)

        # Trigger event if threshold is exceeded
        if is_alert:
            should_emit = False
            if alert_mode == "once" and not tr.get("alertEmitted"):
                should_emit = True
                tr["alertEmitted"] = True
            elif alert_mode == "periodic" and (now - tr.get("lastAlertAt", 0.0) >= alert_cooldown):
                should_emit = True
                tr["lastAlertAt"] = now

            if should_emit:
                fmt_dur = format_timer(elapsed, timer_format)
                events.append({
                    "kind": "object_timer_alert",
                    "event_type": "object_timer_alert",
                    "sourceNodeId": node_id,
                    "trackId": track_id,
                    "class": cls_name,
                    "durationSeconds": round(elapsed, 1),
                    "thresholdSeconds": alert_threshold,
                    "formattedTimer": fmt_dur,
                    "timestamp": now,
                    "bbox": list(box),
                    "message": f"Objek '{cls_name}' (#{track_id}) telah terdeteksi selama {round(elapsed, 1)}s (melebihi ambang batas {alert_threshold:g}s)",
                })

        # Enrich detection
        det["timerSeconds"] = round(elapsed, 1)
        det["formattedTimer"] = format_timer(elapsed, timer_format)
        det["isTimerAlert"] = is_alert
        det["timerNodeId"] = node_id
        det["timerTrackId"] = track_id
        det["showTimerOverlay"] = show_overlay and (elapsed >= min_duration)
        det["timerConfig"] = {
            "badgePosition": config.get("badgePosition", "top"),
            "normalColor": config.get("normalColor", "#10b981"),
            "alertColor": config.get("alertColor", "#ef4444"),
            "showTrackId": bool(config.get("showTrackId", True)),
            "timerFormat": timer_format,
        }

        matched_detections.append(det)

    # Evict tracks that have been absent longer than grace_seconds
    stale_keys = [k for k, v in tracks.items() if (now - v.get("lastSeen", 0.0)) > grace_seconds]
    for k in stale_keys:
        del tracks[k]

    return events


def draw_object_timer_overlay(
    frame: Any,
    detections: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """Renders timer pill badges on all matching detections in the frame."""
    if frame is None or not hasattr(frame, "shape"):
        return

    cfg = config or {}
    for det in detections:
        if not det.get("showTimerOverlay", True):
            continue
        if det.get("timerSeconds") is None:
            continue
        draw_single_object_timer_badge(frame, det, cfg)


def draw_single_object_timer_badge(
    frame: Any,
    det: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """Draws a sleek, modern industrial timer badge on a single detection."""
    if frame is None or not hasattr(frame, "shape"):
        return

    import cv2

    cfg = config or det.get("timerConfig") or {}
    box = _box(det)
    if not box:
        return

    x, y, w, h = box
    formatted = det.get("formattedTimer", "00:00")
    is_alert = bool(det.get("isTimerAlert", False))
    track_id = det.get("timerTrackId", det.get("trackId", det.get("track_id")))

    show_track_id = bool(cfg.get("showTrackId", True))
    badge_pos = str(cfg.get("badgePosition", "top")).strip().lower()

    # Label text
    if show_track_id and track_id is not None:
        tag_text = f"#{track_id} {formatted}"
    else:
        tag_text = formatted

    if is_alert:
        tag_text = f"{tag_text} OVERTIME"

    # Color configuration: Alert vs Normal
    normal_hex = str(cfg.get("normalColor", "#10b981"))
    alert_hex = str(cfg.get("alertColor", "#ef4444"))

    # BGR tuples: normal (emerald) vs alert (crimson)
    normal_bgr = _hex_to_bgr(normal_hex, (129, 185, 16))
    alert_bgr = _hex_to_bgr(alert_hex, (68, 68, 239))
    accent_color = alert_bgr if is_alert else normal_bgr

    font_scale = 0.42
    font_thick = 1
    text_size, _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thick)

    icon_gap = 18  # space reserved for vector stopwatch icon
    pad_x = 8
    pad_y = 5
    badge_w = text_size[0] + icon_gap + (pad_x * 2)
    badge_h = text_size[1] + (pad_y * 2)

    frame_h, frame_w = frame.shape[:2]

    # Calculate Badge Position
    if badge_pos == "bottom":
        bx = int(x + (w - badge_w) / 2)
        by = int(y + h + badge_h + 4)
    elif badge_pos == "inside":
        bx = int(x + 4)
        by = int(y + badge_h + 4)
    else:  # top (above box, aligned with top edge)
        bx = int(x + (w - badge_w) / 2)
        by = int(y - 6)

    # Clamp coordinates inside frame boundaries
    bx = max(2, min(frame_w - badge_w - 2, bx))
    by = max(badge_h + 2, min(frame_h - 4, by))

    top_left = (bx, by - badge_h)
    bottom_right = (bx + badge_w, by)

    # Background card with slight shadow / border
    cv2.rectangle(frame, top_left, bottom_right, (15, 23, 42), -1)  # dark slate fill
    cv2.rectangle(frame, top_left, bottom_right, accent_color, 1, cv2.LINE_AA)  # crisp border

    # Vector Stopwatch Icon
    icon_cx = bx + pad_x + 6
    icon_cy = by - (badge_h // 2)
    radius = 5
    cv2.circle(frame, (icon_cx, icon_cy), radius, accent_color, 1, cv2.LINE_AA)
    # Clock hands: 12 o'clock and 2 o'clock
    cv2.line(frame, (icon_cx, icon_cy), (icon_cx, icon_cy - 3), accent_color, 1, cv2.LINE_AA)
    cv2.line(frame, (icon_cx, icon_cy), (icon_cx + 2, icon_cy - 1), accent_color, 1, cv2.LINE_AA)
    # Top pin
    cv2.line(frame, (icon_cx, icon_cy - radius), (icon_cx, icon_cy - radius - 1), accent_color, 1, cv2.LINE_AA)

    # Text rendering
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
