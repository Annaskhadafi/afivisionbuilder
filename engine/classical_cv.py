"""
Classical Computer Vision Module:
- Camera Focus Health (Laplacian variance blur detector with ROI support and alarm event)
- Auto Rotate Edges (Image deskewing / alignment using MinAreaRect & Hough Transforms)
"""

import math
import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


def parse_roi_points(roi_str: str, width: int, height: int) -> Optional[np.ndarray]:
    """Parses semicolon-separated 'x,y; x,y' points into an integer pixel polygon array."""
    if not roi_str or not isinstance(roi_str, str):
        return None
    raw_pairs = [p.strip() for p in roi_str.replace("\n", ";").split(";") if p.strip()]
    pts = []
    for pair in raw_pairs:
        parts = pair.split(",")
        if len(parts) >= 2:
            try:
                x = float(parts[0].strip())
                y = float(parts[1].strip())
                # If normalized 0..1
                if x <= 1.0 and y <= 1.0:
                    x = x * width
                    y = y * height
                pts.append([int(x), int(y)])
            except ValueError:
                continue
    if len(pts) >= 3:
        return np.array(pts, dtype=np.int32)
    return None


def compute_camera_focus_score(
    frame: Any,
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
) -> Tuple[float, bool, List[Dict[str, Any]]]:
    """
    Computes camera sharpness/focus score via Laplacian Variance.
    
    Returns:
        (focus_score, is_blur, events_list)
    """
    if state is None:
        state = {}

    if frame is None or not hasattr(frame, "shape"):
        return 0.0, True, []

    blur_threshold = float(config.get("blurThreshold", 100.0))
    check_interval = float(config.get("checkIntervalSeconds", 5.0))
    enable_alarm = bool(config.get("enableAlarm", True))
    roi_str = str(config.get("roi", "")).strip()

    h, w = frame.shape[:2]
    now = time.monotonic()
    last_check_time = state.get("last_focus_check_ts", 0.0)

    # Convert to grayscale
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    # Crop or mask ROI if specified
    if roi_str:
        pts = parse_roi_points(roi_str, w, h)
        if pts is not None:
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(mask, [pts], 255)
            x, y, rw, rh = cv2.boundingRect(pts)
            if rw > 10 and rh > 10:
                gray = gray[y:y+rh, x:x+rw]

    # Calculate Laplacian variance
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    focus_score = float(laplacian.var())
    is_blur = focus_score < blur_threshold

    events = []
    if (now - last_check_time) >= check_interval:
        state["last_focus_check_ts"] = now
        state["last_focus_score"] = round(focus_score, 2)
        state["is_camera_blurry"] = is_blur

        if is_blur and enable_alarm:
            events.append({
                "event_type": "camera_blur_detected",
                "severity": "critical" if focus_score < (blur_threshold * 0.4) else "warning",
                "message": f"Kamera buram atau terhalang debu/kabut! Skor ketajaman: {round(focus_score, 1)} (Ambang batas minimum: {blur_threshold})",
                "data": {
                    "focus_score": round(focus_score, 2),
                    "threshold": blur_threshold,
                },
                "timestamp": now,
            })

    return round(focus_score, 2), is_blur, events


def auto_rotate_edges(
    frame: Any,
    config: Dict[str, Any],
) -> Tuple[Any, float]:
    """
    Detects dominant skew angle using MinAreaRect on high-contrast edges and rotates image to upright position.
    
    Returns:
        (aligned_frame, rotation_angle_deg)
    """
    if frame is None or not hasattr(frame, "shape"):
        return frame, 0.0

    max_angle_limit = float(config.get("maxAngleLimit", 45.0))
    min_angle_threshold = float(config.get("minAngleThreshold", 0.5))
    border_mode_str = str(config.get("borderMode", "black_constant")).strip().lower()

    border_mode = cv2.BORDER_REPLICATE if border_mode_str == "replicate" else cv2.BORDER_CONSTANT

    h, w = frame.shape[:2]

    # Convert to grayscale
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame.copy()

    # Apply Gaussian blur & Canny edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Find coordinates of all edge pixels
    pts = np.column_stack(np.where(edges > 0))
    if len(pts) < 50:
        return frame, 0.0

    # MinAreaRect expects (x, y) coordinates
    pts_xy = np.column_stack((pts[:, 1], pts[:, 0]))
    rect = cv2.minAreaRect(pts_xy)
    angle = rect[2]

    # OpenCV minAreaRect returns angle in range [-90, 0)
    # Correct angle so it represents skew from horizontal/vertical
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # If angle exceeds max limit or is negligible, don't rotate
    if abs(angle) < min_angle_threshold or abs(angle) > max_angle_limit:
        return frame, 0.0

    center = (w // 2, h // 2)
    m = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(frame, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=border_mode)

    return rotated, round(angle, 2)
