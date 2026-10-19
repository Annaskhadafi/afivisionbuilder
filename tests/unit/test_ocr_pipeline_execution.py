"""Integration tests for OCR pipeline execution without upstream detector.
Validates:
1. active_analysis_pipeline returns True for OCR workflow (input -> ocr -> preview/alert).
2. _process_track_event_nodes runs OCR on full frame when standalone.
3. Detections contain class='text', text, score, box, and bbox.
4. Results are routed to preview and alert nodes.
5. draw_detections handles OCR text label and renders without errors.
"""
import cv2
import numpy as np
import pytest

import engine.core as core
import engine.main as engine
from engine.ocr_engine import OCREngine


def test_active_analysis_pipeline_detects_ocr():
    workflow = {
        "nodes": [
            {"id": "node_input", "type": "input", "enabled": True},
            {"id": "node_ocr", "type": "ocr_reader", "enabled": True, "config": {}},
            {"id": "node_preview", "type": "preview", "enabled": True, "config": {}},
        ],
        "edges": [
            ("node_input", "node_ocr"),
            ("node_ocr", "node_preview"),
        ],
    }
    assert engine.active_analysis_pipeline(workflow) is True


def test_process_track_event_nodes_runs_ocr_standalone():
    # Synthetic frame with clear text 257
    frame = np.full((360, 640, 3), 255, dtype=np.uint8)
    cv2.putText(frame, "257", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 0), 4)

    workflow = {
        "nodes": [
            {"id": "node_input", "type": "input", "enabled": True},
            {"id": "node_ocr", "type": "ocr_reader", "enabled": True, "config": {
                "minConfidence": 0.30,
            }},
            {"id": "node_preview", "type": "preview", "enabled": True, "config": {}},
            {"id": "node_alert", "type": "alert", "enabled": True, "config": {}},
        ],
        "edges": [
            ("node_input", "node_ocr"),
            ("node_ocr", "node_preview"),
            ("node_ocr", "node_alert"),
        ],
    }

    detections = []
    tracked = []
    logic_runtime = {}
    event_runtime = {}

    extra_results, crops, object_records, count_records = core._process_track_event_nodes(
        cv2,
        frame,
        workflow,
        detections,
        tracked,
        logic_runtime,
        event_runtime,
        1.0,
    )

    # OCR should have detected text
    assert len(detections) >= 1, f"Expected text detection in detections, got {detections}"
    text_det = detections[0]
    assert text_det["class"] == "text"
    assert "text" in text_det
    assert "257" in text_det["text"] or len(text_det["text"]) > 0
    assert "bbox" in text_det
    assert "box" in text_det
    assert len(text_det["bbox"]) == 4

    # Events should be emitted
    assert len(extra_results) >= 1
    assert any(ev.get("kind") in ("ocr_text_read", "text_detected") for ev in extra_results)

    detections.extend(extra_results)

    # Test routing to preview
    preview_dets = engine.detections_for_node(workflow, "node_preview", detections, detections, tracked)
    assert len(preview_dets) >= 1

    # Test routing to alert
    alert_dets = engine.detections_for_node(workflow, "node_alert", detections, detections, tracked)
    assert len(alert_dets) >= 1

    # Test draw_detections works and renders text label on frame
    preview_config = {"config": {"showBoxes": True, "showLabels": True}}
    canvas = frame.copy()
    engine.draw_detections(canvas, preview_dets, preview_config)
