"""Unit tests for Phase 4: Advanced Visualization & VLM Integration.

Covers:
- Model Comparison Diff (side-by-side & diff overlay rendering)
- Detections Difference (state comparison before vs after, added/removed/unchanged)
- AIAgentClient in detector and strict_classifier modes
- Overlay Annotate enhancements (motion_trace and corner_bracket)
"""
import sys
import os
import numpy as np
import pytest

# Ensure engine path is accessible
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "engine"))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from model_comparison import compare_model_detections, compute_iou
from detections_difference import compare_detections_difference
from ai_agent import AIAgentClient
from main import _apply_overlay_node


def test_compute_iou():
    box1 = (0.0, 0.0, 100.0, 100.0)
    box2 = (0.0, 0.0, 100.0, 100.0)
    assert compute_iou(box1, box2) == 1.0

    box3 = (50.0, 0.0, 150.0, 100.0)
    # intersection: [50, 0, 100, 100] = 50 * 100 = 5000
    # union: 10000 + 10000 - 5000 = 15000
    # iou = 5000 / 15000 = 0.3333
    assert abs(compute_iou(box1, box3) - (1.0 / 3.0)) < 1e-3

    box4 = (200.0, 200.0, 300.0, 300.0)
    assert compute_iou(box1, box4) == 0.0


def test_model_comparison_side_by_side():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dets_a = [{"box": [50, 50, 150, 150], "class": "person", "confidence": 0.92}]
    dets_b = [{"box": [52, 51, 153, 152], "class": "person", "confidence": 0.88}]

    config = {
        "modelAName": "Model Alpha",
        "modelBName": "Model Beta",
        "renderMode": "side_by_side",
        "iouThreshold": 0.50,
        "showStatsHeader": True,
    }

    out_frame, stats = compare_model_detections(frame, dets_a, dets_b, config)
    # Side-by-side stitches two 640w frames into 1280w
    assert out_frame.shape == (480, 1280, 3)
    assert stats["consensusCount"] == 1
    assert stats["uniqueA"] == 0
    assert stats["uniqueB"] == 0
    assert stats["agreementRatio"] == 1.0


def test_model_comparison_diff_overlay():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # One consensus match, one unique A, one unique B
    dets_a = [
        {"box": [50, 50, 150, 150], "class": "person", "confidence": 0.92},
        {"box": [200, 200, 300, 300], "class": "car", "confidence": 0.85},
    ]
    dets_b = [
        {"box": [52, 51, 153, 152], "class": "person", "confidence": 0.88},
        {"box": [400, 100, 500, 200], "class": "truck", "confidence": 0.75},
    ]

    config = {
        "modelAName": "YOLOv8",
        "modelBName": "RF-DETR",
        "renderMode": "diff_overlay",
        "iouThreshold": 0.50,
        "showStatsHeader": True,
    }

    out_frame, stats = compare_model_detections(frame, dets_a, dets_b, config)
    assert out_frame.shape == (480, 640, 3)
    assert stats["consensusCount"] == 1
    assert stats["uniqueA"] == 1
    assert stats["uniqueB"] == 1
    assert stats["agreementRatio"] == 0.50


def test_detections_difference_baseline_and_changes():
    state = {}
    config = {
        "matchIoU": 0.50,
        "cooldownSeconds": 1.0,
        "alarmOnDifference": True,
    }

    # Step 1: Initial frame sets baseline
    cur_dets_1 = [
        {"box": [50, 50, 150, 150], "class": "pallet"},
        {"box": [200, 50, 300, 150], "class": "pallet"},
    ]
    res1, event1 = compare_detections_difference(cur_dets_1, None, config, state)
    assert res1["baselineCount"] == 2
    assert res1["addedCount"] == 0
    assert res1["removedCount"] == 0
    assert res1["diffCount"] == 0
    assert event1 is None

    # Step 2: Next frame, 1 pallet removed, 1 forklift added
    cur_dets_2 = [
        {"box": [50, 50, 150, 150], "class": "pallet"},          # unchanged
        {"box": [400, 100, 550, 250], "class": "forklift"},       # added
    ]
    res2, event2 = compare_detections_difference(cur_dets_2, None, config, state)
    assert res2["unchangedCount"] == 1
    assert res2["addedCount"] == 1
    assert res2["removedCount"] == 1  # the second pallet missing
    assert res2["diffCount"] == 2
    assert event2 is not None
    assert event2["kind"] == "detections_difference_event"
    assert event2["addedCount"] == 1
    assert event2["removedCount"] == 1


def test_ai_agent_detector_mode_parsing():
    client = AIAgentClient({
        "provider": "openai",
        "model": "gpt-4o-mini",
        "taskMode": "detector",
    })

    prompt = client.render_prompt([])
    assert "Detect all relevant objects" in prompt
    assert "box_2d" in prompt

    raw_response = """
    ```json
    {
      "detections": [
        {
          "box_2d": [100, 200, 400, 500],
          "label": "hard_hat",
          "confidence": 0.94
        }
      ]
    }
    ```
    """
    parsed = client.parse_response(raw_response, {"prompt_tokens": 50, "completion_tokens": 20})
    assert parsed["taskMode"] == "detector"
    assert len(parsed["detections"]) == 1
    det = parsed["detections"][0]
    assert det["class"] == "hard_hat"
    assert det["confidence"] == 0.94
    # Check normalized coordinate scaling from 0..1000 to 0..1
    assert det["normalized_box"] == [0.2, 0.1, 0.5, 0.4]


def test_ai_agent_strict_classifier_mode_parsing():
    client = AIAgentClient({
        "provider": "openai",
        "model": "gpt-4o-mini",
        "taskMode": "strict_classifier",
    })

    prompt = client.render_prompt([])
    assert "Classify the visual scene" in prompt
    assert "is_compliant" in prompt

    raw_response = """
    {
      "class": "missing_vest",
      "confidence": 0.91,
      "is_compliant": false,
      "reason": "Worker is wearing dark jacket without high-vis safety vest."
    }
    """
    parsed = client.parse_response(raw_response, {})
    assert parsed["taskMode"] == "strict_classifier"
    assert parsed["class"] == "missing_vest"
    assert parsed["confidence"] == 0.91
    assert parsed["is_compliant"] is False
    assert parsed["decision"] is False
    assert "safety vest" in parsed["reason"]


def test_overlay_annotate_motion_trace_and_corner_bracket():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = [
        {
            "id": "trk-1",
            "track_id": "trk-1",
            "class": "worker",
            "x": 100,
            "y": 100,
            "width": 60,
            "height": 120,
            "trail": [(90, 80), (95, 90), (130, 160)],
        }
    ]

    node = {
        "id": "overlay_1",
        "type": "overlay_annotate",
        "config": {
            "layers": [
                {
                    "type": "corner_bracket",
                    "enabled": True,
                    "color": "#22c55e",
                    "thickness": 2,
                    "bracketLength": 15,
                    "glow": True,
                },
                {
                    "type": "motion_trace",
                    "enabled": True,
                    "color": "#a855f7",
                    "thickness": 2,
                    "historyLen": 10,
                    "fadeAlpha": True,
                },
            ]
        },
    }

    # Execute annotation
    _apply_overlay_node(frame, node, detections)

    # Verify frame was modified (not all zeros)
    assert np.count_nonzero(frame) > 0
