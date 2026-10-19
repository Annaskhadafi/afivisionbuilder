"""
Advanced Logic & Video Flow Control Module:
- Overlap Analysis (Parent-child spatial relationship for PPE inspection, e.g. helmet on person)
- Delta Filter (Visual motion compute throttler saving CPU/GPU when scene is static)
- Switch Case (Multi-branch conditional router based on class, status, or attribute)
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


def compute_box_intersection_area(box1: List[float], box2: List[float]) -> float:
    """Calculates intersection area between two [x, y, w, h] boxes."""
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    ix1 = max(x1, x2)
    iy1 = max(y1, y2)
    ix2 = min(x1 + w1, x2 + w2)
    iy2 = min(y1 + h1, y2 + h2)

    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    return iw * ih


def analyze_overlap(
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    now: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluates whether parent class objects (e.g. 'person') contain required child class objects
    (e.g. 'helmet', 'vest') in a specific sub-region ('top_half', 'bottom_half', 'full').
    
    Returns:
        (augmented_detections, compliance_events)
    """
    if state is None:
        state = {}
    if now is None:
        now = time.monotonic()

    parent_class = str(config.get("parentClass", "person")).strip().lower()
    child_class = str(config.get("childClass", "helmet")).strip().lower()
    min_overlap = float(config.get("minOverlapRatio", 0.5))
    parent_region = str(config.get("parentRegion", "top_half")).strip().lower()
    trigger_alarm = bool(config.get("triggerAlarmOnNonCompliance", True))
    alarm_cooldown = float(config.get("alarmCooldownSeconds", 3.0))

    last_alarm_times = state.setdefault("last_compliance_alarms", {})

    parent_dets = []
    child_dets = []

    for det in detections:
        cls_name = str(det.get("class", "")).strip().lower()
        if cls_name == parent_class:
            parent_dets.append(det)
        elif cls_name == child_class:
            child_dets.append(det)

    augmented = []
    events = []

    for p in parent_dets:
        p_copy = dict(p)
        bbox = p_copy.get("bbox")
        if not bbox or len(bbox) < 4:
            augmented.append(p_copy)
            continue

        bx, by, bw, bh = bbox
        if parent_region == "top_half":
            sub_box = [bx, by, bw, bh / 2.0]
        elif parent_region == "bottom_half":
            sub_box = [bx, by + bh / 2.0, bw, bh / 2.0]
        else:  # full
            sub_box = [bx, by, bw, bh]

        matched_child = None
        best_overlap_ratio = 0.0

        for c in child_dets:
            c_bbox = c.get("bbox")
            if not c_bbox or len(c_bbox) < 4:
                continue

            c_area = c_bbox[2] * c_bbox[3]
            if c_area <= 0:
                continue

            inter = compute_box_intersection_area(sub_box, c_bbox)
            ratio = inter / c_area  # fraction of child inside parent sub-region

            if ratio > best_overlap_ratio:
                best_overlap_ratio = ratio
                if ratio >= min_overlap:
                    matched_child = c

        is_compliant = matched_child is not None
        p_copy["is_compliant"] = is_compliant
        p_copy["compliance_target"] = child_class
        p_copy["child_overlap_ratio"] = round(best_overlap_ratio, 2)

        track_id = p_copy.get("track_id", p_copy.get("id", "0"))

        if not is_compliant and trigger_alarm:
            last_alarm = last_alarm_times.get(track_id, 0.0)
            if last_alarm == 0.0 or (now - last_alarm) >= alarm_cooldown:
                events.append({
                    "event_type": "compliance_violation",
                    "severity": "warning",
                    "message": f"Pelanggaran APD / Keselamatan: {parent_class} (ID {track_id}) terdeteksi tanpa kelengkapan {child_class}!",
                    "data": {
                        "parent_class": parent_class,
                        "child_class": child_class,
                        "track_id": track_id,
                        "parent_region": parent_region,
                        "overlap_ratio": round(best_overlap_ratio, 2),
                    },
                    "timestamp": now,
                })
                last_alarm_times[track_id] = now

        augmented.append(p_copy)

    # Append child detections and any other non-parent detections unchanged
    for det in detections:
        cls_name = str(det.get("class", "")).strip().lower()
        if cls_name != parent_class:
            augmented.append(det)

    return augmented, events


def evaluate_delta_filter(
    frame: Any,
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    now: Optional[float] = None,
) -> Tuple[bool, float]:
    """
    Evaluates visual motion between current frame and previous frame.
    Returns (continue_branch: bool, motion_score: float).
    When continue_branch is False, downstream expensive inference should be skipped.
    """
    if state is None:
        state = {}
    if now is None:
        now = time.monotonic()

    if frame is None or not hasattr(frame, "shape"):
        return True, 0.0

    delta_threshold = float(config.get("deltaThreshold", 0.03))  # 3% pixel change
    heartbeat_interval = float(config.get("heartbeatIntervalSeconds", 15.0))
    min_contour_area = float(config.get("minContourArea", 500.0))

    last_heartbeat = state.get("last_heartbeat_ts", 0.0)
    prev_gray = state.get("prev_gray_frame")

    h, w = frame.shape[:2]
    total_pixels = h * w

    # Convert current frame to small grayscale for super-fast difference calculation
    small = cv2.resize(frame, (320, 180), interpolation=cv2.INTER_LINEAR)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY) if len(small.shape) == 3 else small
    gray = cv2.GaussianBlur(gray, (7, 7), 0)

    if prev_gray is None:
        state["prev_gray_frame"] = gray
        state["last_heartbeat_ts"] = now
        return True, 1.0  # first frame always passes

    # Compute frame difference
    diff = cv2.absdiff(prev_gray, gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    motion_pixels = cv2.countNonZero(thresh)
    small_total = 320 * 180
    motion_ratio = motion_pixels / float(small_total)

    # Heartbeat check
    is_heartbeat = (now - last_heartbeat) >= heartbeat_interval
    has_motion = motion_ratio >= delta_threshold

    continue_branch = has_motion or is_heartbeat

    if continue_branch:
        state["prev_gray_frame"] = gray
        if is_heartbeat:
            state["last_heartbeat_ts"] = now

    state["last_motion_score"] = round(motion_ratio, 4)
    return continue_branch, round(motion_ratio, 4)


def route_switch_case(
    items: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Routes detection or packet items into different ports based on evaluation field.
    
    Config:
        evaluationField: "class", "status", or custom key
        cases: "person:port_1, forklift:port_2, default:port_3"
        defaultPort: "default"
    """
    eval_field = str(config.get("evaluationField", "class")).strip()
    cases_str = str(config.get("cases", "")).strip()
    default_port = str(config.get("defaultPort", "default")).strip()

    # Parse case mappings: {val: port}
    case_map = {}
    if cases_str:
        for entry in cases_str.split(","):
            if ":" in entry:
                val, port = entry.split(":", 1)
                case_map[val.strip().lower()] = port.strip()

    routed: Dict[str, List[Dict[str, Any]]] = {}

    for item in items:
        target_val = str(item.get(eval_field, "")).strip().lower()
        port = case_map.get(target_val, default_port)
        routed.setdefault(port, []).append(item)

    return routed
