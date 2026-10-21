"""
Warehouse Overstack & Pallet Stack Height Violation Detector:
- Logistics & Warehouse Safety Node: Monitors cargo stacks, pallets, and tire piles.
- Detects items exceeding virtual ceiling clearance limit to prevent collapse hazards.
- Uses calibrated pixels-per-meter for real-world physical height telemetry.
- Temporal debounce filter to avoid false triggers during momentary forklift transit.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


def detect_overstack_violations(
    frame: Any,
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    now: Optional[float] = None,
    node_id: str = "overstack_detector",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluates stacked pallets/cargo against virtual ceiling height limit.

    Returns:
        (augmented_detections, overstack_events)
    """
    if state is None:
        state = {}
    if now is None:
        now = time.monotonic()

    target_classes = str(config.get("targetClasses", "pallet, box, cargo, tire, stack")).strip().lower()
    allowed_classes = [c.strip().lower() for c in target_classes.split(",") if c.strip()]
    if not allowed_classes or "all" in allowed_classes:
        allowed_classes = []

    # Virtual ceiling line [[x1, y1], [x2, y2]] or horizontal ceiling Y
    raw_ceiling = config.get("ceilingBoundaryLine")
    ceiling_y = float(config.get("ceilingY", 200.0))
    p1, p2 = (0.0, ceiling_y), (1920.0, ceiling_y)
    if isinstance(raw_ceiling, (list, tuple)) and len(raw_ceiling) >= 2:
        try:
            p1 = (float(raw_ceiling[0][0]), float(raw_ceiling[0][1]))
            p2 = (float(raw_ceiling[1][0]), float(raw_ceiling[1][1]))
        except Exception:
            pass

    pixel_per_meter = max(1.0, float(config.get("pixelPerMeter", 50.0)))
    persistence_seconds = float(config.get("persistenceDurationSeconds", 2.5))
    alarm_cooldown = float(config.get("alarmCooldownSeconds", 15.0))

    # Tracks memory: track_id -> {
    #   'first_breach_time': float,
    #   'last_seen': float,
    #   'last_alarm': float,
    #   'max_height_m': float
    # }
    tracks_mem = state.setdefault("_overstack_tracks", {})

    augmented = []
    events = []

    def get_interpolated_ceiling_y(x_eval: float) -> float:
        if abs(p2[0] - p1[0]) < 1e-4:
            return p1[1]
        slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
        return p1[1] + slope * (x_eval - p1[0])

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

        x, y, w, h = bbox
        if h <= 0 or w <= 0:
            augmented.append(det)
            continue

        x_center = x + w / 2.0
        y_top = y
        y_bottom = y + h
        limit_y = get_interpolated_ceiling_y(x_center)

        # In image coordinates, y=0 is at top, so y_top <= limit_y means higher than limit
        is_breaching = y_top <= limit_y
        stack_height_meters = round(float(h) / pixel_per_meter, 2)
        excess_px = max(0.0, limit_y - y_top)
        excess_meters = round(excess_px / pixel_per_meter, 2)

        track_id = det.get("track_id", det.get("id", f"{int(x_center)}_{int(y_top)}"))
        t_data = tracks_mem.setdefault(track_id, {
            "first_breach_time": None,
            "last_seen": now,
            "last_alarm": -999999.0,
            "max_height_m": stack_height_meters,
        })
        t_data["last_seen"] = now
        t_data["max_height_m"] = max(t_data["max_height_m"], stack_height_meters)

        det_copy = dict(det)
        det_copy["isOverstack"] = False
        det_copy["stackHeightM"] = stack_height_meters
        attrs = dict(det_copy.get("attributes") or {})
        attrs["stack_height_m"] = stack_height_meters
        attrs["is_overstack"] = False

        if is_breaching:
            if t_data["first_breach_time"] is None:
                t_data["first_breach_time"] = now

            breach_dur = now - t_data["first_breach_time"]
            attrs["breach_duration_sec"] = round(breach_dur, 1)
            attrs["excess_height_m"] = excess_meters

            # Persistent violation confirmation
            if breach_dur >= persistence_seconds:
                attrs["is_overstack"] = True
                det_copy["isOverstack"] = True
                det_copy["stackHeightM"] = stack_height_meters
                det_copy["excessHeightM"] = excess_meters

                if now - t_data.get("last_alarm", 0) >= alarm_cooldown:
                    t_data["last_alarm"] = now
                    events.append({
                        "event_type": "OVERSTACK_HAZARD",
                        "type": "OVERSTACK_HAZARD",
                        "severity": "WARNING",
                        "message": f"⚠️ BAHAYA OVERSTACK: Tumpukan {cls_name} ID #{track_id} ({stack_height_meters}m) melebihi batas aman setinggi {excess_meters}m!",
                        "zoneName": "Storage Stacking",
                        "track_id": track_id,
                        "stack_height_meters": stack_height_meters,
                        "excess_meters": excess_meters,
                        "timestamp": now,
                    })
        else:
            t_data["first_breach_time"] = None
            det_copy["isOverstack"] = False
            det_copy["stackHeightM"] = stack_height_meters

        det_copy["attributes"] = attrs
        augmented.append(det_copy)

    # Clean stale entries
    stale = [k for k, v in tracks_mem.items() if now - v.get("last_seen", 0) > 10.0]
    for k in stale:
        tracks_mem.pop(k, None)

    return augmented, events


def draw_overstack_overlay(
    frame: np.ndarray,
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> None:
    """Draws the virtual ceiling guideline and overstack violation badges."""
    if frame is None or not hasattr(frame, "shape"):
        return
    fh, fw = frame.shape[:2]

    # Draw ceiling line
    raw_ceiling = config.get("ceilingBoundaryLine")
    ceiling_y = float(config.get("ceilingY", 200.0))
    p1 = (0, int(round(ceiling_y)))
    p2 = (fw, int(round(ceiling_y)))
    if isinstance(raw_ceiling, (list, tuple)) and len(raw_ceiling) >= 2:
        try:
            p1 = (int(round(raw_ceiling[0][0])), int(round(raw_ceiling[0][1])))
            p2 = (int(round(raw_ceiling[1][0])), int(round(raw_ceiling[1][1])))
        except Exception:
            pass

    # Draw dashed ceiling warning line
    cv2.line(frame, p1, p2, (0, 165, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "MAX STACK CLEARANCE CEILING", (p1[0] + 16, max(24, p1[1] - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1, cv2.LINE_AA)

    # Draw badges on overstack detections
    for det in detections:
        if not det.get("isOverstack", False):
            continue
        bbox = det.get("bbox")
        if not bbox and "x" in det and "width" in det:
            bbox = [det["x"], det["y"], det["width"], det["height"]]
        if not bbox or len(bbox) < 4:
            continue
        x, y, w, h = bbox
        x1, y1 = int(round(x)), int(round(y))
        tag = f"OVERSTACK +{det.get('excessHeightM', 0.0)}m"
        cv2.rectangle(frame, (x1, y1 - 20), (x1 + len(tag) * 8 + 8, y1), (0, 69, 255), -1)
        cv2.putText(frame, tag, (x1 + 4, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)
