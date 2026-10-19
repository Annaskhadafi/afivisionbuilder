"""Detections Difference (State / Before vs After) Node.

Compares current detections against a baseline (or previous frame) snapshot to identify:
- added_objects: Items appearing in current frame not present in baseline.
- removed_objects: Items present in baseline that disappeared from current frame.
- unchanged_objects: Items reliably present in both before and after states.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple


def _compute_iou(box_a: Tuple[float, float, float, float], box_b: Tuple[float, float, float, float]) -> float:
    """Compute IoU between two [x1, y1, x2, y2] boxes."""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h
    if inter_area <= 0:
        return 0.0
    area_a = max(0.0, (box_a[2] - box_a[0]) * (box_a[3] - box_a[1]))
    area_b = max(0.0, (box_b[2] - box_b[0]) * (box_b[3] - box_b[1]))
    union_area = area_a + area_b - inter_area
    return inter_area / union_area if union_area > 0 else 0.0


def _extract_box_xyxy(det: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """Extract [x1, y1, x2, y2] from detection dict."""
    if "box" in det and isinstance(det["box"], (list, tuple)) and len(det["box"]) >= 4:
        b = det["box"]
        return float(b[0]), float(b[1]), float(b[2]), float(b[3])
    if "bbox" in det and isinstance(det["bbox"], (list, tuple)) and len(det["bbox"]) >= 4:
        b = det["bbox"]
        return float(b[0]), float(b[1]), float(b[0] + b[2]), float(b[1] + b[3])
    x = float(det.get("x", 0.0))
    y = float(det.get("y", 0.0))
    w = float(det.get("width", 0.0))
    h = float(det.get("height", 0.0))
    return x, y, x + w, y + h


def compare_detections_difference(
    current_detections: List[Dict[str, Any]],
    baseline_detections: Optional[List[Dict[str, Any]]],
    config: Dict[str, Any],
    node_state: Dict[str, Any],
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Compare current detections against baseline snapshot.

    Returns:
        (diff_result, alarm_event)
    """
    match_iou = float(config.get("matchIoU", 0.50))
    filter_classes = {
        c.strip().lower() for c in str(config.get("filterClasses", "")).split(",") if c.strip()
    }
    trigger_snapshot = bool(config.get("triggerSnapshot", False))
    cooldown = float(config.get("cooldownSeconds", 3.0))
    alarm_on_diff = bool(config.get("alarmOnDifference", True))

    now = time.time()

    # Filter detections if specified
    cur_filtered = [
        d for d in current_detections
        if not filter_classes or str(d.get("class", "")).strip().lower() in filter_classes
    ]

    # Initialize or update baseline snapshot if triggered or empty
    if trigger_snapshot or "baseline" not in node_state:
        if baseline_detections is not None:
            node_state["baseline"] = [
                d for d in baseline_detections
                if not filter_classes or str(d.get("class", "")).strip().lower() in filter_classes
            ]
        else:
            node_state["baseline"] = list(cur_filtered)
        node_state["last_snapshot_time"] = now

    base = node_state.get("baseline", [])

    matched_cur = set()
    matched_base = set()

    # Greedy IoU matching
    for i_cur, d_cur in enumerate(cur_filtered):
        box_cur = _extract_box_xyxy(d_cur)
        cls_cur = str(d_cur.get("class", "")).strip().lower()
        best_iou = 0.0
        best_base_idx = -1

        for i_base, d_base in enumerate(base):
            if i_base in matched_base:
                continue
            cls_base = str(d_base.get("class", "")).strip().lower()
            if cls_cur and cls_base and cls_cur != cls_base:
                continue
            box_base = _extract_box_xyxy(d_base)
            iou = _compute_iou(box_cur, box_base)
            if iou >= match_iou and iou > best_iou:
                best_iou = iou
                best_base_idx = i_base

        if best_base_idx >= 0:
            matched_cur.add(i_cur)
            matched_base.add(best_base_idx)

    added_objects = [d_cur for i_cur, d_cur in enumerate(cur_filtered) if i_cur not in matched_cur]
    removed_objects = [d_base for i_base, d_base in enumerate(base) if i_base not in matched_base]
    unchanged_objects = [d_cur for i_cur, d_cur in enumerate(cur_filtered) if i_cur in matched_cur]

    diff_count = len(added_objects) + len(removed_objects)

    diff_result = {
        "baselineCount": len(base),
        "currentCount": len(cur_filtered),
        "addedCount": len(added_objects),
        "removedCount": len(removed_objects),
        "unchangedCount": len(unchanged_objects),
        "diffCount": diff_count,
        "addedObjects": added_objects,
        "removedObjects": removed_objects,
        "unchangedObjects": unchanged_objects,
    }

    alarm_event = None
    last_alarm = float(node_state.get("last_alarm_time", 0.0))
    if alarm_on_diff and diff_count > 0:
        if last_alarm == 0.0 or (now - last_alarm) >= cooldown:
            node_state["last_alarm_time"] = now
            alarm_event = {
                "kind": "detections_difference_event",
                "type": "detections_diff",
                "message": (
                    f"Detections Diff Detected: +{len(added_objects)} added, "
                    f"-{len(removed_objects)} missing."
                ),
                "timestamp": now,
                "addedCount": len(added_objects),
                "removedCount": len(removed_objects),
            }

    return diff_result, alarm_event
