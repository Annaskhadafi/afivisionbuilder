"""Multi-Model Ensemble & Detections Consensus Node (Roboflow-Inspired).

Aggregates detections from multiple upstream detector branches or models,
requiring an agreement vote threshold (IoU overlap) to suppress false positives.
"""
from __future__ import annotations


def calculate_box_iou(box_a: list[float], box_b: list[float]) -> float:
    """Calculate Intersection-over-Union (IoU) between two [x, y, w, h] boxes."""
    if len(box_a) < 4 or len(box_b) < 4:
        return 0.0
    xa1, ya1, wa, ha = float(box_a[0]), float(box_a[1]), float(box_a[2]), float(box_a[3])
    xa2, ya2 = xa1 + wa, ya1 + ha
    xb1, yb1, wb, hb = float(box_b[0]), float(box_b[1]), float(box_b[2]), float(box_b[3])
    xb2, yb2 = xb1 + wb, yb1 + hb

    inter_x1 = max(xa1, xb1)
    inter_y1 = max(ya1, yb1)
    inter_x2 = min(xa2, xb2)
    inter_y2 = min(ya2, yb2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, wa * ha)
    area_b = max(0.0, wb * hb)
    union_area = area_a + area_b - inter_area
    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


def apply_detections_consensus(detections: list[dict], config: dict | None = None) -> list[dict]:
    """Compute consensus detections based on required votes and IoU threshold.

    Parameters:
      - requiredVotes: int, minimum number of agreeing detections (default: 2)
      - iouThreshold: float, minimum IoU overlap to consider an agreement (default: 0.5)
      - confidenceAggregation: 'average' | 'max' | 'min' (default: 'average')
      - classAware: bool, whether detections must share the same class label (default: True)
      - boxAggregation: 'highest_confidence' | 'average' (default: 'highest_confidence')
    """
    if not detections:
        return []
    if config is None:
        config = {}

    try:
        required_votes = max(1, int(config.get("requiredVotes", 2) or 2))
    except (TypeError, ValueError):
        required_votes = 2

    try:
        iou_threshold = max(0.01, min(1.0, float(config.get("iouThreshold", 0.5) or 0.5)))
    except (TypeError, ValueError):
        iou_threshold = 0.5

    conf_agg = str(config.get("confidenceAggregation", "average")).lower()
    class_aware = bool(config.get("classAware", True))
    box_agg = str(config.get("boxAggregation", "highest_confidence")).lower()

    # Normalize boxes
    parsed_items = []
    for item in detections:
        bbox = item.get("bbox")
        if bbox and len(bbox) >= 4:
            box = [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]
        else:
            box = [
                float(item.get("x", 0.0)),
                float(item.get("y", 0.0)),
                float(item.get("width", 0.0)),
                float(item.get("height", 0.0)),
            ]
        parsed_items.append({
            "record": item,
            "box": box,
            "class": str(item.get("class", "")).strip().lower(),
            "score": float(item.get("score", 0.0) or 0.0),
            "source": str(item.get("sourceNodeId") or item.get("originSourceNodeId") or ""),
        })

    # Cluster detections based on IoU and class
    visited: set[int] = set()
    consensus_results: list[dict] = []

    for i, candidate in enumerate(parsed_items):
        if i in visited:
            continue
        cluster = [candidate]
        visited.add(i)

        for j in range(i + 1, len(parsed_items)):
            if j in visited:
                continue
            other = parsed_items[j]
            if class_aware and candidate["class"] != other["class"]:
                continue
            if calculate_box_iou(candidate["box"], other["box"]) >= iou_threshold:
                cluster.append(other)
                visited.add(j)

        # Count votes: either distinct sources if available or total count
        sources = {c["source"] for c in cluster if c["source"]}
        votes = len(sources) if len(sources) > 1 else len(cluster)

        if votes >= required_votes:
            # Sort cluster by confidence descending
            cluster.sort(key=lambda c: c["score"], reverse=True)
            best = cluster[0]

            # Aggregate confidence
            scores = [c["score"] for c in cluster]
            if conf_agg == "max":
                final_score = max(scores)
            elif conf_agg == "min":
                final_score = min(scores)
            else:  # average
                final_score = sum(scores) / len(scores)

            # Aggregate box
            if box_agg == "average":
                avg_x = sum(c["box"][0] for c in cluster) / len(cluster)
                avg_y = sum(c["box"][1] for c in cluster) / len(cluster)
                avg_w = sum(c["box"][2] for c in cluster) / len(cluster)
                avg_h = sum(c["box"][3] for c in cluster) / len(cluster)
                final_box = [round(avg_x, 2), round(avg_y, 2), round(avg_w, 2), round(avg_h, 2)]
            else:
                final_box = list(best["box"])

            result_item = dict(best["record"])
            result_item["bbox"] = final_box
            result_item["score"] = round(final_score, 4)
            result_item["consensusVotes"] = votes
            result_item["sourceNodeId"] = "detections_consensus"
            consensus_results.append(result_item)

    return consensus_results
