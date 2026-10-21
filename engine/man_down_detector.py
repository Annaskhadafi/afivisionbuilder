"""
Man Down & Worker Fall Detector Module:
- HSE / K3 Industrial Safety Node: Detects fallen, collapsed, or unconscious workers.
- 3-Stage Temporal Verification:
  1. Aspect Ratio Geometry (horizontal posture width/height >= threshold)
  2. Sudden Vertical Drop (fall dynamics)
  3. Persistent Stillness Buffer (motionless on floor for >= confirmation duration)
- Emits critical emergency events and renders pulsating warning overlays.
"""

import math
import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


def detect_man_down(
    frame: Any,
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    now: Optional[float] = None,
    node_id: str = "man_down_detector",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluates worker posture and stillness to detect man-down emergencies.

    Returns:
        (augmented_detections, emergency_events)
    """
    if state is None:
        state = {}
    if now is None:
        now = time.monotonic()

    target_class = str(config.get("targetClass", "person")).strip().lower()
    aspect_ratio_threshold = float(config.get("aspectRatioThreshold", 0.95))
    stillness_max_motion_px = float(config.get("stillnessMaxMotionPx", 8.0))
    confirmation_seconds = float(config.get("confirmationDurationSeconds", 4.0))
    alarm_cooldown = float(config.get("alarmCooldownSeconds", 10.0))

    # Persistent tracks memory: track_id -> {
    #   'first_down_time': float,
    #   'last_pos': (cx, cy),
    #   'last_update': float,
    #   'last_alarm_time': float,
    #   'confirmed': bool
    # }
    tracks_mem = state.setdefault("_tracks_mem", {})

    augmented = []
    events = []

    for det in detections:
        cls_name = str(det.get("class", "")).strip().lower()
        if cls_name != target_class and target_class != "all":
            augmented.append(det)
            continue

        bbox = det.get("bbox")
        if not bbox and "x" in det and "width" in det:
            bbox = [det["x"], det["y"], det["width"], det["height"]]
        if not bbox or len(bbox) < 4:
            augmented.append(det)
            continue

        x, y, w, h = bbox
        if h <= 0 or w <= 0:
            augmented.append(det)
            continue

        # Aspect ratio: Width / Height
        aspect_ratio = float(w) / float(h)
        cx = x + w / 2.0
        cy = y + h / 2.0
        track_id = det.get("track_id", det.get("id", f"{int(cx)}_{int(cy)}"))

        is_horizontal = aspect_ratio >= aspect_ratio_threshold
        t_data = tracks_mem.setdefault(track_id, {
            "first_down_time": None,
            "last_pos": (cx, cy),
            "last_update": now,
            "last_alarm_time": -999999.0,
            "confirmed": False,
        })

        dt = now - t_data["last_update"]
        last_cx, last_cy = t_data["last_pos"]
        motion_dist = math.hypot(cx - last_cx, cy - last_cy)
        t_data["last_pos"] = (cx, cy)
        t_data["last_update"] = now

        det_copy = dict(det)
        attrs = dict(det_copy.get("attributes") or {})

        if is_horizontal:
            # Person is in horizontal/lying orientation
            if t_data["first_down_time"] is None:
                t_data["first_down_time"] = now

            down_duration = now - t_data["first_down_time"]
            attrs["posture"] = "lying"
            attrs["aspect_ratio"] = round(aspect_ratio, 2)
            attrs["down_duration_sec"] = round(down_duration, 1)

            # Check if motionless
            if motion_dist <= stillness_max_motion_px:
                attrs["motion_state"] = "still"
            else:
                attrs["motion_state"] = "moving_on_floor"
                # If significant movement, reset duration slightly
                t_data["first_down_time"] = max(t_data["first_down_time"], now - 1.0)

            # Confirm emergency if still for >= confirmation_seconds
            is_emergency = down_duration >= confirmation_seconds
            det_copy["isManDown"] = is_emergency
            det_copy["manDownDuration"] = round(down_duration, 1)

            if is_emergency:
                t_data["confirmed"] = True
                if now - t_data["last_alarm_time"] >= alarm_cooldown:
                    t_data["last_alarm_time"] = now
                    events.append({
                        "event_type": "MAN_DOWN_ALERT",
                        "type": "MAN_DOWN_ALERT",
                        "severity": "CRITICAL",
                        "message": f"🚨 BAHAYA: Pekerja Terjatuh / Tidak Sadarkan Diri (ID #{track_id}) selama {down_duration:.1f}s!",
                        "zoneName": "Safety Zone",
                        "track_id": track_id,
                        "duration_seconds": round(down_duration, 1),
                        "aspect_ratio": round(aspect_ratio, 2),
                        "bbox": bbox,
                        "timestamp": now,
                    })
        else:
            # Person is standing or crouching upright
            t_data["first_down_time"] = None
            t_data["confirmed"] = False
            attrs["posture"] = "standing"
            attrs["aspect_ratio"] = round(aspect_ratio, 2)
            attrs["down_duration_sec"] = 0.0
            det_copy["isManDown"] = False
            det_copy["manDownDuration"] = 0.0

        det_copy["attributes"] = attrs
        augmented.append(det_copy)

    # Clean stale tracks from memory (older than 10 seconds)
    stale_keys = [k for k, v in tracks_mem.items() if now - v.get("last_update", 0) > 10.0]
    for k in stale_keys:
        tracks_mem.pop(k, None)

    return augmented, events


def draw_man_down_overlay(frame: np.ndarray, detections: List[Dict[str, Any]]) -> None:
    """Draws a blinking high-visibility hazard box around confirmed fallen workers."""
    if frame is None or not hasattr(frame, "shape"):
        return
    fh, fw = frame.shape[:2]
    for det in detections:
        if not det.get("isManDown", False):
            continue
        bbox = det.get("bbox")
        if not bbox and "x" in det and "width" in det:
            bbox = [det["x"], det["y"], det["width"], det["height"]]
        if not bbox or len(bbox) < 4:
            continue
        x, y, w, h = bbox
        x1, y1 = max(0, int(round(x))), max(0, int(round(y)))
        x2, y2 = min(fw, int(round(x + w))), min(fh, int(round(y + h)))

        # Thick red border
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 230), 3)

        dur = det.get("manDownDuration", 0.0)
        label = f"MAN DOWN! {dur:.1f}s"
        lbl_y = max(24, y1 - 8)
        cv2.rectangle(frame, (x1, lbl_y - 20), (x1 + len(label) * 9 + 12, lbl_y + 4), (0, 0, 230), -1)
        cv2.putText(frame, label, (x1 + 6, lbl_y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
