"""PTZ Controller — ONVIF PTZ Auto-Follower Node.

Tracks a target object and calculates Pan/Tilt/Zoom continuous movement vectors
to keep the target centered in the camera frame with configurable deadzone protection.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple


def _extract_centroid(det: Dict[str, Any]) -> Tuple[float, float]:
    """Calculate centroid (cx, cy) from detection bounding box."""
    if "box" in det and isinstance(det["box"], (list, tuple)) and len(det["box"]) >= 4:
        b = det["box"]
        return float(b[0] + b[2]) / 2.0, float(b[1] + b[3]) / 2.0
    if "bbox" in det and isinstance(det["bbox"], (list, tuple)) and len(det["bbox"]) >= 4:
        b = det["bbox"]
        return float(b[0] + b[2] / 2.0), float(b[1] + b[3] / 2.0)
    x = float(det.get("x", 0.0))
    y = float(det.get("y", 0.0))
    w = float(det.get("width", 0.0))
    h = float(det.get("height", 0.0))
    return x + w / 2.0, y + h / 2.0


def calculate_ptz_velocity(
    tracked_detections: List[Dict[str, Any]],
    frame_size: Tuple[int, int],
    config: Dict[str, Any],
    node_state: Dict[str, Any],
) -> Dict[str, Any]:
    """Calculate normalized ONVIF Pan/Tilt continuous speed commands.

    Args:
        tracked_detections: List of tracked objects
        frame_size: (width, height)
        config: Node configuration
        node_state: Persistent runtime state for PID/smoothing

    Returns:
        {"status": "tracking" | "idle", "pan": float, "tilt": float, "zoom": float, "targetId": ...}
    """
    target_track_id = config.get("targetTrackId")
    target_class = str(config.get("targetClass") or "").strip().lower()
    deadzone = max(0.01, min(0.50, float(config.get("deadzonePercent", 0.15) or 0.15)))
    pan_speed_gain = float(config.get("panSpeed", 0.6) or 0.6)
    tilt_speed_gain = float(config.get("tiltSpeed", 0.6) or 0.6)
    camera_ip = str(config.get("cameraIp") or "192.168.1.100").strip()

    fw, fh = frame_size
    center_x, center_y = fw / 2.0, fh / 2.0

    # Find the target detection
    target = None
    if target_track_id is not None:
        for d in tracked_detections:
            if str(d.get("track_id", d.get("id"))) == str(target_track_id):
                target = d
                break

    if target is None:
        # Fallback: find by target class or highest confidence
        candidates = [
            d for d in tracked_detections
            if not target_class or str(d.get("class", "")).strip().lower() == target_class
        ]
        if candidates:
            # Pick highest confidence or largest object
            target = max(candidates, key=lambda d: float(d.get("confidence", d.get("score", 0.0))))

    if target is None:
        return {
            "status": "idle",
            "pan": 0.0,
            "tilt": 0.0,
            "zoom": 0.0,
            "targetId": None,
            "cameraIp": camera_ip,
            "timestamp": time.time(),
        }

    cx, cy = _extract_centroid(target)
    track_id = target.get("track_id", target.get("id"))

    # Compute normalized error (-1.0 to 1.0)
    err_x = (cx - center_x) / (center_x if center_x > 0 else 1.0)
    err_y = (cy - center_y) / (center_y if center_y > 0 else 1.0)

    # Deadzone filter
    pan_vel = 0.0
    tilt_vel = 0.0

    if abs(err_x) > deadzone:
        # Scale remaining error outside deadzone
        sign_x = 1.0 if err_x > 0 else -1.0
        norm_x = (abs(err_x) - deadzone) / (1.0 - deadzone)
        pan_vel = round(sign_x * norm_x * pan_speed_gain, 3)

    if abs(err_y) > deadzone:
        sign_y = 1.0 if err_y > 0 else -1.0
        norm_y = (abs(err_y) - deadzone) / (1.0 - deadzone)
        tilt_vel = round(sign_y * norm_y * tilt_speed_gain, 3)

    command = {
        "status": "tracking" if (pan_vel != 0.0 or tilt_vel != 0.0) else "centered",
        "pan": max(-1.0, min(1.0, pan_vel)),
        "tilt": max(-1.0, min(1.0, tilt_vel)),
        "zoom": 0.0,
        "targetId": track_id,
        "targetCentroid": [round(cx, 1), round(cy, 1)],
        "cameraIp": camera_ip,
        "timestamp": time.time(),
    }

    node_state["last_ptz_command"] = command
    return command
