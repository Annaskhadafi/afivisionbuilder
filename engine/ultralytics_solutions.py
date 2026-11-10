"""Afi Vision Builder (VisoNode) - Ultralytics Solutions Adoption Module.

Implements 5 industrial & smart vision solutions inspired by Ultralytics Solutions:
1. ParkingManagement: Multi-slot parking vacancy and occupancy tracker.
2. QueueManager: Queue length, wait time (dwell), and congestion analyzer.
3. AIGym: Skeletal keypoint joint angle repetition counter & ergonomic posture inspector.
4. VisionEye: Observer sightline raycaster, proximity alert, and blind-spot hazard detector.
5. AnalyticsOverlay: On-screen HUD charts (trend line, bar distribution, KPI sparklines).
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


# ============================================================================
# 1. SMART PARKING MANAGEMENT (ParkingManagement)
# ============================================================================

def extract_detection_box(d: dict, frame_shape: tuple[int, int] | None = None) -> list[float] | None:
    """Extract [x1, y1, x2, y2] from detection dict supporting various formats."""
    if not isinstance(d, dict):
        return None
    # 1. Check xyxy
    if "xyxy" in d and isinstance(d["xyxy"], (list, tuple)) and len(d["xyxy"]) >= 4:
        return [float(v) for v in d["xyxy"][:4]]
    # 2. Check box
    if "box" in d and isinstance(d["box"], (list, tuple)) and len(d["box"]) >= 4:
        b = d["box"]
        return [float(b[0]), float(b[1]), float(b[2]), float(b[3])]
    # 3. Check bbox: [x, y, w, h]
    if "bbox" in d and isinstance(d["bbox"], (list, tuple)) and len(d["bbox"]) >= 4:
        x, y, w, h = [float(v) for v in d["bbox"][:4]]
        return [x, y, x + w, y + h]
    # 4. Check x, y, width/w, height/h
    if "x" in d and "y" in d:
        x = float(d["x"])
        y = float(d["y"])
        w = float(d.get("width", d.get("w", 0)))
        h = float(d.get("height", d.get("h", 0)))
        return [x, y, x + w, y + h]
    return None


def extract_detection_class(d: dict) -> str:
    """Extract lowercase class name from detection dict."""
    if not isinstance(d, dict):
        return ""
    for k in ("class", "class_name", "label", "rawClass", "name"):
        v = d.get(k)
        if v is not None and str(v).strip():
            return str(v).strip().casefold()
    return ""


def normalize_polygon_points(points: list, frame_shape: tuple[int, int]) -> np.ndarray:
    """Convert points list to ndarray, scaling normalized coordinates (0..1) if needed."""
    if not points:
        return np.empty((0, 2), dtype=np.int32)
    h, w = frame_shape[:2]
    # Check if normalized (all coords <= 1.0)
    is_normalized = all(
        (0.0 <= pt[0] <= 1.0 and 0.0 <= pt[1] <= 1.0)
        for pt in points if len(pt) >= 2
    )
    res = []
    for pt in points:
        if len(pt) < 2:
            continue
        px, py = float(pt[0]), float(pt[1])
        if is_normalized and w > 1 and h > 1:
            px *= w
            py *= h
        res.append([int(px), int(py)])
    return np.array(res, dtype=np.int32)


def _point_in_polygon(x: float, y: float, polygon: list[list[float]]) -> bool:
    """Ray casting algorithm to test point in polygon."""
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def _box_polygon_overlap_ratio(box: list[float], polygon_pts: np.ndarray, frame_shape: tuple[int, int]) -> float:
    """Calculate overlap ratio between bounding box and parking slot polygon."""
    x1, y1, x2, y2 = [int(v) for v in box[:4]]
    bw = max(1, x2 - x1)
    bh = max(1, y2 - y1)
    box_area = float(bw * bh)

    # Fast centroid check
    cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    if cv2.pointPolygonTest(polygon_pts, (float(cx), float(cy)), False) >= 0:
        return 1.0

    # Polygon intersection mask
    h, w = frame_shape[:2]
    min_x, max_x = max(0, min(x1, int(np.min(polygon_pts[:, 0])))), min(w, max(x2, int(np.max(polygon_pts[:, 0]))))
    min_y, max_y = max(0, min(y1, int(np.min(polygon_pts[:, 1])))), min(h, max(y2, int(np.max(polygon_pts[:, 1]))))
    if max_x <= min_x or max_y <= min_y:
        return 0.0

    mask_box = np.zeros((max_y - min_y, max_x - min_x), dtype=np.uint8)
    bx1, by1 = max(0, x1 - min_x), max(0, y1 - min_y)
    bx2, by2 = min(max_x - min_x, x2 - min_x), min(max_y - min_y, y2 - min_y)
    mask_box[by1:by2, bx1:bx2] = 255

    mask_poly = np.zeros_like(mask_box)
    shifted_poly = polygon_pts - np.array([min_x, min_y], dtype=np.int32)
    cv2.fillPoly(mask_poly, [shifted_poly], 255)

    intersection = np.logical_and(mask_box, mask_poly)
    inter_area = float(np.count_nonzero(intersection))
    poly_area = float(cv2.contourArea(polygon_pts))
    denom = min(box_area, max(1.0, poly_area))
    return inter_area / denom


def process_parking_management(
    frame: Any,
    detections: list[dict],
    config: dict,
    state: dict,
    now: float,
) -> tuple[dict, list[dict], dict]:
    """Evaluates parking slots occupancy against vehicle detections."""
    frame_shape = frame.shape[:2] if frame is not None and hasattr(frame, "shape") else (720, 1280)
    h, w = frame_shape

    slots_config = config.get("slots") or state.get("slots_config") or []
    # If no slots defined, generate default 4 demo slots across middle-bottom half
    if not slots_config:
        sw = w // 4
        sy = int(h * 0.40)
        sh = int(h * 0.45)
        slots_config = [
            {"id": f"P-{i+1}", "name": f"Slot {i+1}", "points": [
                [i * sw + 20, sy], [(i + 1) * sw - 20, sy],
                [(i + 1) * sw - 20, sy + sh], [i * sw + 20, sy + sh]
            ]}
            for i in range(4)
        ]
        state["slots_config"] = slots_config

    target_classes = {
        c.strip().casefold()
        for c in str(config.get("targetClasses", "car,truck,bus,motorcycle,vehicle")).split(",")
        if c.strip()
    }
    threshold = float(config.get("occupancyThreshold", 0.3) or 0.3)

    # Filter detections to target classes
    vehicle_boxes = []
    for d in detections:
        c_label = extract_detection_class(d)
        if not target_classes or c_label in target_classes or not c_label:
            box = extract_detection_box(d, frame_shape)
            if box and len(box) >= 4:
                vehicle_boxes.append((box, d))

    slot_statuses = {}
    events = []
    prev_statuses = state.setdefault("prev_statuses", {})
    occupied_count = 0

    for slot in slots_config:
        s_id = str(slot.get("id") or slot.get("name") or "slot")
        raw_pts = slot.get("points") or []
        if len(raw_pts) < 3:
            continue
        poly_pts = normalize_polygon_points(raw_pts, frame_shape)
        if len(poly_pts) < 3:
            continue
        is_occupied = False
        occupying_vehicle = None

        for box, det in vehicle_boxes:
            ratio = _box_polygon_overlap_ratio(box, poly_pts, frame_shape)
            if ratio >= threshold:
                is_occupied = True
                occupying_vehicle = det
                break

        prev = prev_statuses.get(s_id, "unknown")
        curr = "occupied" if is_occupied else "available"
        if is_occupied:
            occupied_count += 1

        slot_statuses[s_id] = {
            "id": s_id,
            "name": str(slot.get("name") or s_id),
            "status": curr,
            "points": poly_pts.tolist(),
            "vehicle": occupying_vehicle,
        }

        # Transition event
        if prev != "unknown" and prev != curr:
            ev_type = "parking_slot_occupied" if is_occupied else "parking_slot_vacated"
            events.append({
                "kind": "parking_event",
                "event_type": ev_type,
                "slot_id": s_id,
                "status": curr,
                "message": f"Parking {s_id} is now {curr.upper()}",
                "timestamp": now,
                "time_str": time.strftime("%H:%M:%S", time.localtime(now)),
            })
        prev_statuses[s_id] = curr

    total_slots = len(slot_statuses)
    available_count = total_slots - occupied_count
    occupancy_pct = (occupied_count / total_slots * 100.0) if total_slots > 0 else 0.0

    summary_metrics = {
        "total_slots": total_slots,
        "occupied_slots": occupied_count,
        "available_slots": available_count,
        "occupancy_rate_pct": round(occupancy_pct, 1),
    }

    # Alarm if full
    if config.get("alertOnFull", False) and total_slots > 0 and available_count == 0:
        events.append({
            "kind": "parking_alarm",
            "event_type": "parking_lot_full",
            "message": "Parking lot is FULL (100% capacity)",
            "timestamp": now,
        })

    return slot_statuses, events, summary_metrics


def draw_parking_overlay(frame: Any, slot_statuses: dict, summary_metrics: dict, config: dict) -> None:
    """Renders colored parking slot polygons and summary HUD onto frame."""
    if frame is None or not hasattr(frame, "shape"):
        return
    overlay = frame.copy()
    frame_shape = frame.shape[:2]
    for s_id, slot in slot_statuses.items():
        raw_pts = slot.get("points") or []
        pts = normalize_polygon_points(raw_pts, frame_shape)
        if len(pts) < 3:
            continue
        status = slot.get("status", "available")
        color = (34, 197, 94) if status == "available" else (59, 68, 246)  # Green or Red in BGR
        cv2.fillPoly(overlay, [pts], color)
        cv2.polylines(frame, [pts], True, color, 2, cv2.LINE_AA)

        # Slot ID label
        M = cv2.moments(pts)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            lbl = f"{slot.get('name', s_id)}: {status[:3].upper()}"
            cv2.putText(frame, lbl, (cx - 30, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    alpha = float(config.get("overlayAlpha", 0.3) or 0.3)
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)

    # HUD badge at top-left
    if config.get("showSummaryHud", True) and summary_metrics:
        avail = summary_metrics.get("available_slots", 0)
        tot = summary_metrics.get("total_slots", len(slot_statuses))
        pct = summary_metrics.get("occupancy_rate_pct", 0.0)
        hud_text = f"PARKING: {avail}/{tot} FREE ({pct}%)"
        color_hud = (34, 197, 94) if avail > 0 else (59, 68, 246)
        cv2.rectangle(frame, (10, 10), (320, 42), (20, 24, 33), -1)
        cv2.rectangle(frame, (10, 10), (320, 42), color_hud, 2)
        cv2.putText(frame, hud_text, (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)


# ============================================================================
# 2. QUEUE & WAIT-TIME MANAGEMENT (QueueManager)
# ============================================================================

def process_queue_management(
    frame: Any,
    detections: list[dict],
    config: dict,
    state: dict,
    now: float,
) -> tuple[dict, list[dict]]:
    """Monitors queue occupancy, computes individual and average wait time."""
    frame_shape = frame.shape[:2] if frame is not None and hasattr(frame, "shape") else (720, 1280)
    h, w = frame_shape

    raw_zone = config.get("queueZone") or state.get("queue_zone") or []
    if not raw_zone:
        # Default zone in center
        raw_zone = [[int(w * 0.25), int(h * 0.3)], [int(w * 0.75), int(h * 0.3)],
                    [int(w * 0.75), int(h * 0.85)], [int(w * 0.25), int(h * 0.85)]]
        state["queue_zone"] = raw_zone

    target_classes = {
        c.strip().casefold()
        for c in str(config.get("targetClasses", "person")).split(",")
        if c.strip()
    }
    max_queue = int(config.get("maxQueueCount", 5) or 5)
    max_wait_sec = float(config.get("maxWaitTimeSec", 180.0) or 180.0)

    tracked_queue = state.setdefault("tracked_queue", {})  # trackId -> entry_time
    poly_pts = normalize_polygon_points(raw_zone, frame_shape) if len(raw_zone) >= 3 else None

    current_in_queue = []
    events = []

    for d in detections:
        c_label = extract_detection_class(d)
        if target_classes and c_label not in target_classes:
            continue
        box = extract_detection_box(d, frame_shape)
        if not box or len(box) < 4:
            continue
        cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0

        in_zone = False
        if poly_pts is not None and len(poly_pts) >= 3:
            in_zone = cv2.pointPolygonTest(poly_pts, (float(cx), float(cy)), False) >= 0

        tid = d.get("trackId") or d.get("track_id")
        if tid is None:
            # Fallback to pseudo id based on spatial position
            tid = f"p_{int(cx)}_{int(cy)}"

        if in_zone:
            if tid not in tracked_queue:
                tracked_queue[tid] = now
            wait_time = max(0.0, now - tracked_queue[tid])
            current_in_queue.append({
                "trackId": tid,
                "box": box,
                "wait_sec": wait_time,
                "detection": d,
            })

    # Cleanup tracks that left the queue
    active_tids = {item["trackId"] for item in current_in_queue}
    left_tids = [tid for tid in tracked_queue if tid not in active_tids]
    for tid in left_tids:
        dwell_total = now - tracked_queue.pop(tid)
        if dwell_total >= 10.0:  # Only record exit if waited >= 10 seconds
            events.append({
                "kind": "queue_event",
                "event_type": "queue_served_or_left",
                "trackId": tid,
                "total_wait_sec": round(dwell_total, 1),
                "message": f"Customer ID {tid} finished queue after {round(dwell_total, 1)}s",
                "timestamp": now,
            })

    queue_count = len(current_in_queue)
    wait_times = [item["wait_sec"] for item in current_in_queue]
    avg_wait = float(np.mean(wait_times)) if wait_times else 0.0
    max_current_wait = float(np.max(wait_times)) if wait_times else 0.0

    congestion = "LOW"
    if queue_count >= max_queue or max_current_wait >= max_wait_sec:
        congestion = "OVERLOADED"
    elif queue_count >= max(2, max_queue // 2) or max_current_wait >= (max_wait_sec / 2):
        congestion = "MEDIUM"

    if congestion == "OVERLOADED":
        events.append({
            "kind": "queue_alarm",
            "event_type": "queue_congestion_alert",
            "queue_count": queue_count,
            "max_wait_sec": round(max_current_wait, 1),
            "congestion": congestion,
            "message": f"Queue CONGESTION: {queue_count} people waiting (Max: {round(max_current_wait, 0)}s)",
            "timestamp": now,
        })

    metrics = {
        "queue_count": queue_count,
        "avg_wait_sec": round(avg_wait, 1),
        "max_wait_sec": round(max_current_wait, 1),
        "congestion_level": congestion,
        "zone_points": poly_pts.tolist() if poly_pts is not None else raw_zone,
        "items": current_in_queue,
    }
    return metrics, events


def draw_queue_overlay(frame: Any, metrics: dict, config: dict) -> None:
    """Renders queue boundaries, individual customer wait badges, and congestion HUD."""
    if frame is None or not hasattr(frame, "shape") or not metrics:
        return
    frame_shape = frame.shape[:2]
    raw_pts = metrics.get("zone_points", [])
    pts = normalize_polygon_points(raw_pts, frame_shape)
    congestion = metrics.get("congestion_level", "LOW")
    border_color = (34, 197, 94) if congestion == "LOW" else ((245, 158, 11) if congestion == "MEDIUM" else (59, 68, 246))

    if len(pts) >= 3:
        cv2.polylines(frame, [pts], True, border_color, 2, cv2.LINE_AA)

    # Customer wait timer tags
    for item in metrics.get("items", []):
        box = item["box"]
        wait_s = item["wait_sec"]
        cx = int((box[0] + box[2]) / 2)
        top_y = int(box[1]) - 8
        tag = f"Wait: {int(wait_s)}s"
        cv2.rectangle(frame, (cx - 35, top_y - 14), (cx + 35, top_y + 2), (20, 24, 33), -1)
        cv2.putText(frame, tag, (cx - 30, top_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

    # HUD Card
    h, w = frame_shape
    hud_x, hud_y = w - 270, 10
    cv2.rectangle(frame, (hud_x, hud_y), (w - 10, hud_y + 60), (20, 24, 33), -1)
    cv2.rectangle(frame, (hud_x, hud_y), (w - 10, hud_y + 60), border_color, 2)
    cv2.putText(frame, f"QUEUE: {metrics.get('queue_count', 0)} IN LINE", (hud_x + 12, hud_y + 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"Avg Wait: {metrics.get('avg_wait_sec', 0.0)}s ({congestion})", (hud_x + 12, hud_y + 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, border_color, 1, cv2.LINE_AA)


# ============================================================================
# 3. AI GYM & ERGONOMIC POSTURE COUNTER (AIGym)
# ============================================================================

def _compute_angle(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    """Calculates angle ABC (at vertex B) in degrees."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    cosine_angle = (ba[0] * bc[0] + ba[1] * bc[1]) / (
        max(1e-6, math.hypot(ba[0], ba[1]) * math.hypot(bc[0], bc[1]))
    )
    cosine_angle = max(-1.0, min(1.0, cosine_angle))
    return math.degrees(math.acos(cosine_angle))


def process_ai_gym(
    frame: Any,
    detections: list[dict],
    config: dict,
    state: dict,
    now: float,
) -> tuple[dict, list[dict]]:
    """Evaluates human pose joint angles for repetition counting and ergonomic compliance."""
    exercise = str(config.get("exerciseType", "squat")).lower()
    up_thresh = float(config.get("angleThresholdUp", 160.0) or 160.0)
    down_thresh = float(config.get("angleThresholdDown", 90.0) or 90.0)

    person_states = state.setdefault("gym_states", {})  # tid -> {"reps": int, "stage": "up"|"down", ...}
    events = []
    active_evaluations = []

    # COCO Keypoints index map:
    # 5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow, 9: left_wrist, 10: right_wrist
    # 11: left_hip, 12: right_hip, 13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle
    for d in detections:
        kpts = d.get("keypoints") or d.get("kpts")
        if not kpts or len(kpts) < 17:
            continue

        tid = str(d.get("trackId") or d.get("track_id") or "1")
        pstate = person_states.setdefault(tid, {"reps": 0, "stage": "up", "last_rep_time": 0.0})

        current_angle = None
        vertex_pt = None
        angle_pts = None

        if exercise in ("squat", "lifting"):
            # Knee angle: hip -> knee -> ankle
            hip = kpts[11][:2] if kpts[11][2] > 0.3 else (kpts[12][:2] if kpts[12][2] > 0.3 else None)
            knee = kpts[13][:2] if kpts[13][2] > 0.3 else (kpts[14][:2] if kpts[14][2] > 0.3 else None)
            ankle = kpts[15][:2] if kpts[15][2] > 0.3 else (kpts[16][:2] if kpts[16][2] > 0.3 else None)
            if hip and knee and ankle:
                current_angle = _compute_angle(hip, knee, ankle)
                vertex_pt = (int(knee[0]), int(knee[1]))
                angle_pts = (hip, knee, ankle)
        elif exercise in ("pushup", "bicep_curl"):
            # Elbow angle: shoulder -> elbow -> wrist
            shld = kpts[5][:2] if kpts[5][2] > 0.3 else (kpts[6][:2] if kpts[6][2] > 0.3 else None)
            elbow = kpts[7][:2] if kpts[7][2] > 0.3 else (kpts[8][:2] if kpts[8][2] > 0.3 else None)
            wrist = kpts[9][:2] if kpts[9][2] > 0.3 else (kpts[10][:2] if kpts[10][2] > 0.3 else None)
            if shld and elbow and wrist:
                current_angle = _compute_angle(shld, elbow, wrist)
                vertex_pt = (int(elbow[0]), int(elbow[1]))
                angle_pts = (shld, elbow, wrist)

        if current_angle is not None:
            # Stage transition logic
            stage = pstate["stage"]
            if current_angle < down_thresh:
                pstate["stage"] = "down"
            elif current_angle > up_thresh and stage == "down":
                pstate["stage"] = "up"
                pstate["reps"] += 1
                pstate["last_rep_time"] = now
                events.append({
                    "kind": "gym_event",
                    "event_type": "rep_completed",
                    "exercise": exercise,
                    "trackId": tid,
                    "reps": pstate["reps"],
                    "message": f"Rep {pstate['reps']} {exercise.upper()} completed by #{tid}",
                    "timestamp": now,
                })

            active_evaluations.append({
                "trackId": tid,
                "exercise": exercise,
                "angle": round(current_angle, 1),
                "reps": pstate["reps"],
                "stage": pstate["stage"],
                "vertex": vertex_pt,
                "pts": angle_pts,
            })

    result_summary = {
        "exercise": exercise,
        "evaluations": active_evaluations,
        "total_active_users": len(active_evaluations),
    }
    return result_summary, events


def draw_ai_gym_overlay(frame: Any, summary: dict, config: dict) -> None:
    """Renders joint angle arc, stage pill, and repetition counter HUD on frame."""
    if frame is None or not hasattr(frame, "shape"):
        return
    for item in summary.get("evaluations", []):
        v = item["vertex"]
        pts = item["pts"]
        if v and pts:
            # Draw joint connection lines
            p1, p2, p3 = pts
            cv2.line(frame, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (234, 179, 8), 3, cv2.LINE_AA)
            cv2.line(frame, (int(p2[0]), int(p2[1])), (int(p3[0]), int(p3[1])), (234, 179, 8), 3, cv2.LINE_AA)
            cv2.circle(frame, v, 6, (0, 0, 255), -1)

            # Angle text badge
            cv2.putText(frame, f"{int(item['angle'])} deg", (v[0] + 10, v[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)

        # Rep count badge
        cv2.rectangle(frame, (10, 10), (220, 52), (20, 24, 33), -1)
        cv2.rectangle(frame, (10, 10), (220, 52), (234, 179, 8), 2)
        cv2.putText(frame, f"{item['exercise'].upper()}: {item['reps']} REPS", (20, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Stage: {item['stage'].upper()}", (20, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (168, 85, 247), 1, cv2.LINE_AA)


# ============================================================================
# 4. VISION EYE & BLIND SPOT RAYCASTER (VisionEye)
# ============================================================================

def process_vision_eye(
    frame: Any,
    detections: list[dict],
    config: dict,
    state: dict,
    now: float,
) -> tuple[dict, list[dict]]:
    """Casts observer sightline rays to targets, calculates distance and blind spot hazards."""
    h, w = frame.shape[:2] if frame is not None and hasattr(frame, "shape") else (720, 1280)
    obs_ratio = config.get("observerPoint") or [0.5, 0.95]  # Default bottom-center (e.g. driver viewpoint)
    obs_x = int(obs_ratio[0] * w) if isinstance(obs_ratio[0], float) and obs_ratio[0] <= 1.0 else int(obs_ratio[0])
    obs_y = int(obs_ratio[1] * h) if isinstance(obs_ratio[1], float) and obs_ratio[1] <= 1.0 else int(obs_ratio[1])

    danger_radius = float(config.get("dangerRadiusPx", 180.0) or 180.0)
    blind_spot_start = float(config.get("blindSpotStartDeg", 120.0) or 120.0)
    blind_spot_end = float(config.get("blindSpotEndDeg", 240.0) or 240.0)

    rays = []
    events = []

    for d in detections:
        box = extract_detection_box(d, (h, w))
        if not box or len(box) < 4:
            continue

        # Target center
        tx, ty = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
        dist = math.hypot(tx - obs_x, ty - obs_y)

        # Angle relative to vertical observer forward vector (0 deg = straight up)
        dx, dy = tx - obs_x, obs_y - ty
        angle_deg = math.degrees(math.atan2(dx, dy)) % 360.0

        is_danger = dist <= danger_radius
        is_blind_spot = (blind_spot_start <= angle_deg <= blind_spot_end) if blind_spot_start < blind_spot_end else (
            angle_deg >= blind_spot_start or angle_deg <= blind_spot_end
        )

        tid = d.get("trackId") or d.get("track_id") or "target"
        c_name = extract_detection_class(d) or "object"

        if is_danger:
            events.append({
                "kind": "proximity_hazard_alert",
                "event_type": "vision_eye_danger",
                "trackId": tid,
                "distance_px": round(dist, 1),
                "message": f"DANGER: {c_name} #{tid} too close to observer ({round(dist, 0)}px)!",
                "timestamp": now,
            })
        elif is_blind_spot:
            events.append({
                "kind": "blind_spot_warning",
                "event_type": "vision_eye_blind_spot",
                "trackId": tid,
                "message": f"WARNING: {c_name} #{tid} entered driver BLIND SPOT ({round(angle_deg, 0)} deg)",
                "timestamp": now,
            })

        rays.append({
            "trackId": tid,
            "target": (int(tx), int(ty)),
            "distance": round(dist, 1),
            "angle": round(angle_deg, 1),
            "is_danger": is_danger,
            "is_blind_spot": is_blind_spot,
            "class": c_name,
        })

    summary = {
        "observer_point": (obs_x, obs_y),
        "danger_radius": danger_radius,
        "rays": rays,
        "hazard_count": sum(1 for r in rays if r["is_danger"]),
    }
    return summary, events


def draw_vision_eye_overlay(frame: Any, summary: dict, config: dict) -> None:
    """Renders observer reticle, proximity zone circle, and raycast sightlines."""
    if frame is None or not hasattr(frame, "shape"):
        return
    ox, oy = summary["observer_point"]
    dr = int(summary["danger_radius"])

    # Observer circle & reticle
    cv2.circle(frame, (ox, oy), 8, (59, 130, 246), -1)
    cv2.circle(frame, (ox, oy), 12, (255, 255, 255), 2)
    cv2.putText(frame, "OBSERVER", (ox - 30, oy + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # Danger radius perimeter
    cv2.circle(frame, (ox, oy), dr, (59, 68, 246), 2, cv2.LINE_AA)

    # Raycast lines
    for r in summary.get("rays", []):
        tx, ty = r["target"]
        color = (59, 68, 246) if r["is_danger"] else ((245, 158, 11) if r["is_blind_spot"] else (34, 197, 94))
        cv2.line(frame, (ox, oy), (tx, ty), color, 2, cv2.LINE_AA)
        cv2.circle(frame, (tx, ty), 4, color, -1)

        # Distance tag at midpoint
        mx, my = (ox + tx) // 2, (oy + ty) // 2
        tag = f"{int(r['distance'])}px"
        cv2.putText(frame, tag, (mx, my), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)


# ============================================================================
# 5. LIVE VIDEO ANALYTICS CHART HUD (AnalyticsOverlay)
# ============================================================================

def process_analytics_overlay(
    frame: Any,
    detections: list[dict],
    config: dict,
    state: dict,
    now: float,
) -> tuple[dict, list[dict]]:
    """Aggregates live metric data points into a rolling history buffer for on-screen HUD charts."""
    history = state.setdefault("history", [])
    metric_type = str(config.get("metricType", "count")).lower()
    max_history = int(config.get("historyWindow", 60) or 60)

    val = 0.0
    if metric_type == "count":
        val = float(len(detections))
    elif metric_type == "speed":
        speeds = [float(d.get("speed") or d.get("speed_kmh") or 0.0) for d in detections if "speed" in d or "speed_kmh" in d]
        val = float(np.mean(speeds)) if speeds else 0.0
    elif metric_type == "custom":
        val = float(len([d for d in detections if d.get("score", 0) > 0.5]))
    else:
        val = float(len(detections))

    history.append(val)
    if len(history) > max_history:
        del history[:-max_history]

    summary = {
        "metric_type": metric_type,
        "current_value": val,
        "history": list(history),
        "min_value": float(np.min(history)) if history else 0.0,
        "max_value": float(np.max(history)) if history else 0.0,
        "avg_value": float(np.mean(history)) if history else 0.0,
    }
    return summary, []


def draw_analytics_overlay(frame: Any, summary: dict, config: dict) -> None:
    """Renders semi-transparent real-time line/bar chart HUD overlay on frame."""
    if frame is None or not hasattr(frame, "shape"):
        return
    history = summary.get("history") or []
    if len(history) < 2:
        return

    h, w = frame.shape[:2]
    # Chart box dimensions: 260x100 px at bottom-left or bottom-right
    pos = str(config.get("chartPosition", "bottom_right")).lower()
    cw, ch = 260, 100
    if pos == "bottom_left":
        cx, cy = 15, h - ch - 15
    elif pos == "top_right":
        cx, cy = w - cw - 15, 15
    elif pos == "top_left":
        cx, cy = 15, 15
    else:  # bottom_right default
        cx, cy = w - cw - 15, h - ch - 15

    # Background card
    overlay = frame.copy()
    cv2.rectangle(overlay, (cx, cy), (cx + cw, cy + ch), (15, 18, 26), -1)
    alpha = float(config.get("opacity", 0.75) or 0.75)
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)
    cv2.rectangle(frame, (cx, cy), (cx + cw, cy + ch), (56, 189, 248), 1)

    # Title & current val
    title = str(config.get("chartTitle", "REALTIME TREND")).upper()
    curr_val = summary.get("current_value", 0.0)
    cv2.putText(frame, title, (cx + 10, cy + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (148, 163, 184), 1, cv2.LINE_AA)
    cv2.putText(frame, f"{curr_val:.0f}", (cx + cw - 40, cy + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (56, 189, 248), 2, cv2.LINE_AA)

    # Graph plot area: (cx + 10, cy + 28) to (cx + cw - 10, cy + ch - 10)
    gx1, gy1 = cx + 10, cy + 28
    gx2, gy2 = cx + cw - 10, cy + ch - 10
    gw = gx2 - gx1
    gh = gy2 - gy1

    min_v = summary.get("min_value", 0.0)
    max_v = max(min_v + 1.0, summary.get("max_value", 1.0))

    # Plot polyline
    n = len(history)
    pts = []
    for i, v in enumerate(history):
        px = int(gx1 + (i / max(1, n - 1)) * gw)
        norm_y = (v - min_v) / (max_v - min_v)
        py = int(gy2 - norm_y * gh)
        pts.append([px, py])

    if len(pts) >= 2:
        cv2.polylines(frame, [np.array(pts, dtype=np.int32)], False, (41, 211, 145), 2, cv2.LINE_AA)
        # Highlight last point
        cv2.circle(frame, tuple(pts[-1]), 4, (56, 189, 248), -1)
