"""Model Comparison Diff — Side-by-side and overlay comparison for dual AI model evaluation.

Visualizes detection differences between Model A and Model B:
- Side-by-side mode: Two frames stitched horizontally with color-coded detections and performance metrics.
- Diff overlay mode: Single frame where matching detections (consensus) are green,
  unique Model A detections are Cyan, and unique Model B detections are Magenta.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import cv2
import numpy as np


def compute_iou(box_a: Tuple[float, float, float, float], box_b: Tuple[float, float, float, float]) -> float:
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
    """Extract [x1, y1, x2, y2] from a detection dictionary."""
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


def compare_model_detections(
    frame: np.ndarray,
    detections_a: List[Dict[str, Any]],
    detections_b: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Compare predictions from Model A and Model B.

    Returns:
        (comparison_frame, diff_stats)
    """
    model_a_name = str(config.get("modelAName", "Model A")).strip() or "Model A"
    model_b_name = str(config.get("modelBName", "Model B")).strip() or "Model B"
    render_mode = str(config.get("renderMode", "side_by_side")).strip().lower()
    iou_thresh = float(config.get("iouThreshold", 0.50))
    show_header = bool(config.get("showStatsHeader", True))

    color_a = (255, 255, 0)     # Cyan in BGR (Model A)
    color_b = (255, 0, 255)     # Magenta in BGR (Model B)
    color_match = (34, 197, 94) # Green in BGR (Both agree)

    h, w = frame.shape[:2]

    # Calculate match pairs via IoU
    matched_a = set()
    matched_b = set()

    for idx_a, det_a in enumerate(detections_a):
        box_a = _extract_box_xyxy(det_a)
        cls_a = str(det_a.get("class", "")).strip().lower()
        for idx_b, det_b in enumerate(detections_b):
            if idx_b in matched_b:
                continue
            cls_b = str(det_b.get("class", "")).strip().lower()
            if cls_a and cls_b and cls_a != cls_b:
                continue
            box_b = _extract_box_xyxy(det_b)
            if compute_iou(box_a, box_b) >= iou_thresh:
                matched_a.add(idx_a)
                matched_b.add(idx_b)
                break

    consensus_count = len(matched_a)
    unique_a_count = len(detections_a) - consensus_count
    unique_b_count = len(detections_b) - len(matched_b)

    diff_stats = {
        "modelA": model_a_name,
        "modelB": model_b_name,
        "totalA": len(detections_a),
        "totalB": len(detections_b),
        "consensusCount": consensus_count,
        "uniqueA": unique_a_count,
        "uniqueB": unique_b_count,
        "agreementRatio": round(
            (2.0 * consensus_count) / max(1, len(detections_a) + len(detections_b)), 3
        ),
    }

    if render_mode == "diff_overlay":
        # Draw on single frame
        out = frame.copy()

        # 1. Consensus matches
        for idx_a in matched_a:
            det = detections_a[idx_a]
            x1, y1, x2, y2 = [int(round(v)) for v in _extract_box_xyxy(det)]
            cls_name = str(det.get("class", "object"))
            cv2.rectangle(out, (x1, y1), (x2, y2), color_match, 2)
            cv2.putText(
                out, f"Both: {cls_name}", (x1, max(18, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_match, 2, cv2.LINE_AA,
            )

        # 2. Unique A
        for idx_a, det in enumerate(detections_a):
            if idx_a in matched_a:
                continue
            x1, y1, x2, y2 = [int(round(v)) for v in _extract_box_xyxy(det)]
            cls_name = str(det.get("class", "object"))
            cv2.rectangle(out, (x1, y1), (x2, y2), color_a, 2)
            cv2.putText(
                out, f"{model_a_name}: {cls_name}", (x1, max(18, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color_a, 1, cv2.LINE_AA,
            )

        # 3. Unique B
        for idx_b, det in enumerate(detections_b):
            if idx_b in matched_b:
                continue
            x1, y1, x2, y2 = [int(round(v)) for v in _extract_box_xyxy(det)]
            cls_name = str(det.get("class", "object"))
            cv2.rectangle(out, (x1, y1), (x2, y2), color_b, 2)
            cv2.putText(
                out, f"{model_b_name}: {cls_name}", (x1, max(18, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color_b, 1, cv2.LINE_AA,
            )

        if show_header:
            header_text = (
                f"Diff Mode | Both: {consensus_count} | {model_a_name}: +{unique_a_count} | "
                f"{model_b_name}: +{unique_b_count} (Agreement: {int(diff_stats['agreementRatio'] * 100)}%)"
            )
            cv2.rectangle(out, (0, 0), (w, 32), (20, 20, 25), -1)
            cv2.putText(out, header_text, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        return out, diff_stats

    else:
        # Default side-by-side mode
        frame_a = frame.copy()
        frame_b = frame.copy()

        # Render Model A
        for det in detections_a:
            x1, y1, x2, y2 = [int(round(v)) for v in _extract_box_xyxy(det)]
            cls_name = str(det.get("class", "object"))
            conf = float(det.get("confidence", 0.0))
            cv2.rectangle(frame_a, (x1, y1), (x2, y2), color_a, 2)
            label = f"{cls_name} {conf:.2f}"
            cv2.putText(frame_a, label, (x1, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_a, 2, cv2.LINE_AA)

        # Render Model B
        for det in detections_b:
            x1, y1, x2, y2 = [int(round(v)) for v in _extract_box_xyxy(det)]
            cls_name = str(det.get("class", "object"))
            conf = float(det.get("confidence", 0.0))
            cv2.rectangle(frame_b, (x1, y1), (x2, y2), color_b, 2)
            label = f"{cls_name} {conf:.2f}"
            cv2.putText(frame_b, label, (x1, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_b, 2, cv2.LINE_AA)

        # Header for Frame A
        cv2.rectangle(frame_a, (0, 0), (w, 32), (30, 20, 20), -1)
        cv2.putText(
            frame_a, f"Model A: {model_a_name} ({len(detections_a)} items)", (12, 22),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color_a, 2, cv2.LINE_AA,
        )

        # Header for Frame B
        cv2.rectangle(frame_b, (0, 0), (w, 32), (30, 20, 30), -1)
        cv2.putText(
            frame_b, f"Model B: {model_b_name} ({len(detections_b)} items)", (12, 22),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color_b, 2, cv2.LINE_AA,
        )

        # Stitch horizontally
        stitched = np.hstack([frame_a, frame_b])

        # Draw center separator
        cv2.line(stitched, (w, 0), (w, h), (120, 120, 130), 2)

        return stitched, diff_stats
