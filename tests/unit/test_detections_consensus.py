"""Unit tests for Detections Consensus (Multi-Model Ensemble Voting)."""
import pytest
from detections_consensus import calculate_box_iou, apply_detections_consensus


def test_box_iou_calculation():
    # Exactly identical boxes: IoU = 1.0
    box1 = [10.0, 10.0, 20.0, 20.0]
    box2 = [10.0, 10.0, 20.0, 20.0]
    assert abs(calculate_box_iou(box1, box2) - 1.0) < 1e-4

    # Completely non-overlapping boxes: IoU = 0.0
    box3 = [50.0, 50.0, 20.0, 20.0]
    assert calculate_box_iou(box1, box3) == 0.0

    # Partial overlap
    # Box A: [0, 0, 10, 10] -> area 100
    # Box B: [5, 0, 10, 10] -> area 100
    # Intersection: [5, 0, 5, 10] -> area 50
    # Union: 100 + 100 - 50 = 150 -> IoU = 50 / 150 = 1/3 ~ 0.3333
    box_a = [0, 0, 10, 10]
    box_b = [5, 0, 10, 10]
    assert abs(calculate_box_iou(box_a, box_b) - (1.0 / 3.0)) < 1e-3


def test_detections_consensus_voting_agreement():
    # Model A (YOLO) and Model B (RF-DETR) detecting the same person
    d1 = {"class": "person", "score": 0.80, "bbox": [10.0, 10.0, 30.0, 40.0], "sourceNodeId": "yolo"}
    d2 = {"class": "person", "score": 0.90, "bbox": [12.0, 11.0, 28.0, 39.0], "sourceNodeId": "rfdetr"}
    # Model A detecting a lone false positive
    d3 = {"class": "person", "score": 0.70, "bbox": [150.0, 150.0, 20.0, 20.0], "sourceNodeId": "yolo"}

    config = {
        "requiredVotes": 2,
        "iouThreshold": 0.5,
        "confidenceAggregation": "average",
        "boxAggregation": "highest_confidence",
        "classAware": True,
    }

    results = apply_detections_consensus([d1, d2, d3], config)

    # Only the agreed detection should pass
    assert len(results) == 1
    consensus = results[0]
    assert consensus["class"] == "person"
    assert consensus["consensusVotes"] == 2
    # Average confidence: (0.80 + 0.90) / 2 = 0.85
    assert abs(consensus["score"] - 0.85) < 1e-4
    # Highest confidence box: d2 box
    assert consensus["bbox"] == [12.0, 11.0, 28.0, 39.0]


def test_detections_consensus_class_aware():
    # Model A detects 'person', Model B detects 'car' at identical coordinates
    d1 = {"class": "person", "score": 0.85, "bbox": [10, 10, 30, 30], "sourceNodeId": "m1"}
    d2 = {"class": "car", "score": 0.80, "bbox": [10, 10, 30, 30], "sourceNodeId": "m2"}

    # With classAware = True, they do not match
    config_aware = {"requiredVotes": 2, "iouThreshold": 0.5, "classAware": True}
    res_aware = apply_detections_consensus([d1, d2], config_aware)
    assert len(res_aware) == 0

    # With classAware = False, they match as object
    config_agnostic = {"requiredVotes": 2, "iouThreshold": 0.5, "classAware": False}
    res_agnostic = apply_detections_consensus([d1, d2], config_agnostic)
    assert len(res_agnostic) == 1
    assert res_agnostic[0]["consensusVotes"] == 2


def test_detections_consensus_aggregation_modes():
    d1 = {"class": "bottle", "score": 0.60, "bbox": [10.0, 10.0, 20.0, 20.0]}
    d2 = {"class": "bottle", "score": 0.90, "bbox": [12.0, 10.0, 20.0, 20.0]}

    # Max confidence aggregation & Average box aggregation
    cfg = {
        "requiredVotes": 2,
        "iouThreshold": 0.5,
        "confidenceAggregation": "max",
        "boxAggregation": "average",
    }
    res = apply_detections_consensus([d1, d2], cfg)
    assert len(res) == 1
    assert res[0]["score"] == 0.90
    assert res[0]["bbox"] == [11.0, 10.0, 20.0, 20.0]
