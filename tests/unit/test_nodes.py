"""Deterministic smoke checks for the non-model vision node runtime.

Run with ``webapp\\.venv\\Scripts\\python.exe webapp\\test_nodes.py``.
Model loading/inference is intentionally excluded; these checks exercise the
same helpers used by the worker with synthetic frames and detections.
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

ENGINE = Path(__file__).resolve().parents[2] / "engine"
sys.path.insert(0, str(ENGINE))
import main as nodes  # noqa: E402


def _workflow(processor=None, extra=None):
    items = [{"id": "input", "type": "input", "enabled": True}]
    if processor:
        items.append(processor)
    items.extend(extra or [])
    return {"nodes": items, "edges": [["input", item["id"]] for item in items[1:]]}


def test_image_processing():
    frame = np.zeros((20, 30, 3), np.uint8)
    frame[4:16, 8:22] = (20, 80, 160)
    cases = [
        ({"id": "resize", "type": "resize", "config": {"width": 12, "height": 8}}, (8, 12)),
        ({"id": "crop", "type": "crop", "config": {"x": 5, "y": 3, "width": 10, "height": 7}}, (7, 10)),
        ({"id": "rotate", "type": "rotate_flip", "config": {"rotation": "90"}}, (30, 20)),
        ({"id": "gray", "type": "color_convert", "config": {"mode": "gray"}}, (20, 30)),
        ({"id": "contrast", "type": "brightness_contrast", "config": {"brightness": 10, "contrast": 1.2}}, (20, 30)),
        ({"id": "blur", "type": "blur_sharpen", "config": {"operation": "blur", "kernel": 3}}, (20, 30)),
        ({"id": "perspective", "type": "perspective", "config": {"width": 16, "height": 9}}, (9, 16)),
        ({"id": "bg", "type": "background_subtract", "config": {"method": "mog2"}}, (20, 30)),
    ]
    for node, shape in cases:
        result = nodes.apply_image_processing(frame, _workflow(node), {})
        assert result.shape[:2] == shape, (node["type"], result.shape)
        assert result.shape[2] == 3
    sharpened = nodes.apply_image_processing(frame, _workflow({"id": "sharp", "type": "blur_sharpen", "config": {"operation": "sharpen", "kernel": 3}}), {})
    assert sharpened.shape == frame.shape


def test_branch_remap_and_filter():
    detection = {"kind": "detection", "class": "person", "score": 0.9, "bbox": [10, 4, 8, 6]}
    crop = {"id": "branch", "type": "crop", "config": {"x": 5, "y": 2, "width": 20, "height": 15}}
    workflow = _workflow(crop, [{"id": "det", "type": "detector"}, {"id": "preview", "type": "preview"}])
    workflow["edges"] = [["input", "det"], ["det", "branch"], ["branch", "preview"]]
    result, mapped = nodes.apply_preview_image_processing(np.zeros((20, 30, 3), np.uint8), workflow, "preview", [detection])
    assert result.shape[:2] == (15, 20), result.shape
    assert mapped[0]["bbox"] == [5.0, 2.0, 8.0, 6.0], mapped

    filter_node = {"id": "filter", "type": "filter", "config": {"classes": "person", "minCount": 1}}
    filtered_workflow = _workflow(extra=[{"id": "det", "type": "detector"}, filter_node])
    filtered_workflow["edges"] = [["input", "det"], ["det", "filter"]]
    assert nodes.filter_detections(filtered_workflow, [detection, {"class": "car", "score": 0.9}]) == [detection]
    filter_node["config"]["minCount"] = 2
    assert nodes.filter_detections(filtered_workflow, [detection]) == []


def test_filter_per_class_confidence_and_padding():
    # 1. Test Per-Class Confidence and Default Confidence
    fn = {
        "id": "filter",
        "type": "filter",
        "config": {
            "perClassConfidence": "person:0.85, tire:0.40",
            "defaultConfidence": 0.50,
            "minCount": 1,
        },
    }
    wf = _workflow(extra=[{"id": "det", "type": "detector"}, fn])
    wf["edges"] = [["input", "det"], ["det", "filter"]]
    items = [
        {"class": "person", "score": 0.80, "bbox": [10, 10, 20, 20]},  # dropped (0.80 < 0.85)
        {"class": "person", "score": 0.90, "bbox": [10, 10, 20, 20]},  # kept (0.90 >= 0.85)
        {"class": "tire", "score": 0.45, "bbox": [10, 10, 20, 20]},    # kept (0.45 >= 0.40)
        {"class": "truck", "score": 0.55, "bbox": [10, 10, 20, 20]},   # kept (default 0.55 >= 0.50)
        {"class": "truck", "score": 0.35, "bbox": [10, 10, 20, 20]},   # dropped (default 0.35 < 0.50)
    ]
    res = nodes.filter_detections(wf, items)
    assert len(res) == 3
    assert [r["class"] for r in res] == ["person", "tire", "truck"]
    assert res[0]["score"] == 0.90

    # 2. Test Detection Bounding Box Padding (20% expansion)
    pad_fn = {
        "id": "filter",
        "type": "filter",
        "config": {
            "paddingPercent": 20,
            "minCount": 1,
        },
    }
    pad_wf = _workflow(extra=[{"id": "det", "type": "detector"}, pad_fn])
    pad_wf["edges"] = [["input", "det"], ["det", "filter"]]
    raw_item = [{"class": "person", "score": 0.90, "bbox": [10.0, 10.0, 20.0, 20.0]}]
    padded = nodes.filter_detections(pad_wf, raw_item, frame_size=(100, 100))
    assert len(padded) == 1
    # 20% of 20 = 4.0; dx = 2.0, dy = 2.0 -> bx = 8.0, by = 8.0, bw = 24.0, bh = 24.0
    assert padded[0]["bbox"] == [8.0, 8.0, 24.0, 24.0]
    assert padded[0]["rawBbox"] == [10.0, 10.0, 20.0, 20.0]


def test_logic_and_overlay():
    detection = {"kind": "detection", "class": "person", "score": 0.9, "bbox": [4, 5, 12, 8]}
    logic = {"id": "gate", "type": "confidence_threshold", "config": {"threshold": 0.8, "operator": "gte"}}
    target = {"id": "preview", "type": "preview"}
    workflow = _workflow(extra=[{"id": "det", "type": "detector"}, logic, target])
    workflow["edges"] = [["input", "det"], ["det", "gate"], ["gate", "preview"]]
    assert nodes.apply_logic_nodes(workflow, "preview", [detection], {}, now=10.0) == [detection], nodes.active_logic_nodes_for_target(workflow, "preview")
    logic["config"]["threshold"] = 0.95
    assert nodes.apply_logic_nodes(workflow, "preview", [detection], {}, now=10.0) == []

    output = np.zeros((32, 40, 3), np.uint8)
    overlay = {"id": "annotate", "type": "overlay_annotate", "config": {"layers": [
        {"type": "bounding_boxes", "color": "#ff0000", "thickness": 2},
        {"type": "labels", "template": "{detection.class}"},
        {"type": "confidence", "template": "{detection.confidence}"},
        {"type": "custom_text", "template": "{image.width}x{image.height}", "position": "top_left"},
    ]}}
    nodes._apply_overlay_node(output, overlay, [detection])
    assert output.shape == (32, 40, 3) and int(np.count_nonzero(output)) > 0, int(np.count_nonzero(output))


def test_catalog_helpers():
    from node_catalog import make_overlay_layer, normalize_overlay_config, available_output_labels

    layer = make_overlay_layer("labels", 0)
    assert layer["id"] == "labels-1" and layer["type"] == "labels"
    config = normalize_overlay_config({"layers": [layer, {"type": "unknown"}, {"type": "labels", "id": "labels-1"}]})
    assert len(config["layers"]) == 2 and len({item["id"] for item in config["layers"]}) == 2, config
    graph = {"nodes": [
        {"id": "input", "type": "input"},
        {"id": "det", "type": "detector", "config": {"engine": "rfdetr_onnx", "rfdetrOnnxClasses": "person,car"}},
        {"id": "filter", "type": "filter", "config": {"classes": "person"}},
        {"id": "preview", "type": "preview"},
    ], "edges": [["input", "det"], ["det", "filter"], ["filter", "preview"]]}
    assert [label for label, _source in available_output_labels(graph, "preview")] == ["person", "car"], available_output_labels(graph, "preview")


def test_line_counter():
    import core
    # 1. Box extraction
    assert core._extract_detection_box({"bbox": [10, 20, 30, 40]}) == (10.0, 20.0, 30.0, 40.0)
    assert core._extract_detection_box({"xyxy": [10, 20, 40, 60]}) == (10.0, 20.0, 30.0, 40.0)
    assert core._extract_detection_box({"x": 10, "y": 20, "width": 30, "height": 40}) == (10.0, 20.0, 30.0, 40.0)

    # 2. Crossing detection
    # Vertical line from (50, 0) to (50, 100) on 100x100 frame
    workflow = {
        "nodes": [{
            "id": "line1",
            "type": "line_counter",
            "enabled": True,
            "config": {
                "lines": [
                    {
                        "id": "line_a",
                        "name": "Gate A",
                        "startPoint": "0.5,0.0",
                        "endPoint": "0.5,1.0",
                        "invertDirection": False,
                        "countMode": "both",
                        "lineColor": "#22c55e",
                        "inLabel": "IN",
                        "outLabel": "OUT",
                    },
                    {
                        "id": "line_b",
                        "name": "Gate B",
                        "startPoint": "0.0,0.5",
                        "endPoint": "1.0,0.5",
                        "invertDirection": False,
                        "countMode": "both",
                        "lineColor": "#3b82f6",
                        "inLabel": "IN",
                        "outLabel": "OUT",
                    }
                ],
                "triggerAnchor": "center",
                "classes": "person",
                "inLabel": "IN",
                "outLabel": "OUT",
            }
        }],
        "edges": []
    }
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    event_runtime = {}

    # Frame 1: Person on left side (x=40, y=20) -> Center is (45, 25)
    # Notice: det has NO trackId! Tests auto-tracking!
    det1 = [{"class": "person", "score": 0.95, "bbox": [40, 20, 10, 10]}]
    events1 = core._process_line_counters(workflow, frame, det1, [], event_runtime, now=1.0)
    assert len(events1) == 0
    assert event_runtime["line1"]["count_in"] == 0
    assert event_runtime["line1"]["count_out"] == 0

    # Frame 2: Person moves to right side (x=55, y=20) -> Center is (60, 25), crosses Gate A (x=50)!
    det2 = [{"class": "person", "score": 0.95, "bbox": [55, 20, 10, 10]}]
    events2 = core._process_line_counters(workflow, frame, det2, [], event_runtime, now=1.1)
    assert len(events2) == 1, events2
    assert events2[0]["kind"] == "line_crossing"
    assert events2[0]["lineId"] == "line_a"
    assert events2[0]["lineName"] == "Gate A"
    assert "boxColor" in det2[0], "det2 should have boxColor set"
    assert "lineDirection" in det2[0], "det2 should have lineDirection set"
    assert event_runtime["line1"]["count_in"] + event_runtime["line1"]["count_out"] == 1
    assert event_runtime["line1"]["lines"]["line_a"]["count_in"] + event_runtime["line1"]["lines"]["line_a"]["count_out"] == 1

    # Frame 3: Frame overlay rendering does not crash
    core._draw_roboflow_workflow_overlays(frame, workflow, event_runtime)
    assert np.count_nonzero(frame) > 0

    # Frame 4: Test clearing/deleting a line (Gate A coordinates cleared)
    workflow["nodes"][0]["config"]["lines"][0]["startPoint"] = ""
    workflow["nodes"][0]["config"]["lines"][0]["endPoint"] = ""
    det3 = [{"class": "person", "score": 0.95, "bbox": [40, 20, 10, 10]}]
    events3 = core._process_line_counters(workflow, frame, det3, [], event_runtime, now=2.0)
    assert len(events3) == 0

    # Frame 5: Test runner reset counter (both line-specific and full)
    runner = core.WorkflowRunner(lambda x: None)
    runner._event_runtime = event_runtime
    runner.reset_counter("line1", "line_a")
    assert event_runtime["line1"]["lines"]["line_a"]["count_in"] == 0
    assert event_runtime["line1"]["lines"]["line_a"]["count_out"] == 0
    assert event_runtime["line1"]["count_in"] == 0
    assert event_runtime["line1"]["count_out"] == 0


def test_if_else_branching():
    # Test If/Else node with IF branch (passWhen: true) and ELSE branch (passWhen: false)
    if_node = {"id": "gate_if", "type": "if_else", "config": {"metric": "object_count", "operator": "gte", "value": 2, "passWhen": "true"}}
    else_node = {"id": "gate_else", "type": "if_else", "config": {"metric": "object_count", "operator": "gte", "value": 2, "passWhen": "false"}}

    runtime = {}
    dets_1 = [{"class": "person", "score": 0.9}]
    dets_2 = [{"class": "person", "score": 0.9}, {"class": "person", "score": 0.8}]

    # When count is 1:
    # IF branch (>= 2) should fail (return False)
    assert nodes._logic_signal(if_node, dets_1, runtime, now=1.0) is False
    # ELSE branch (>= 2) should pass (return True)
    assert nodes._logic_signal(else_node, dets_1, runtime, now=1.0) is True

    # When count is 2:
    # IF branch should pass
    assert nodes._logic_signal(if_node, dets_2, runtime, now=1.1) is True
    # ELSE branch should fail
    assert nodes._logic_signal(else_node, dets_2, runtime, now=1.1) is False

    # A detector result and its downstream classification on the same box are one object.
    same_object = [
        {"kind": "detection", "class": "person", "score": 0.9, "bbox": [2, 2, 5, 5]},
        {"kind": "classification", "class": "person", "score": 0.95, "bbox": [2, 2, 5, 5]},
    ]
    assert nodes._logic_signal(if_node, same_object, runtime, now=1.2) is False
    assert nodes.format_drawing_template("{detection.count}", np.zeros((10, 10, 3), np.uint8), same_object) == "1"

    frame = np.zeros((64, 96, 3), np.uint8)
    gate_if = {"id": "gate_if", "type": "if_else", "enabled": True, "config": {"metric": "object_count", "operator": "gte", "value": 2, "passWhen": "true"}}
    gate_else = {"id": "gate_else", "type": "if_else", "enabled": True, "config": {"metric": "object_count", "operator": "gte", "value": 2, "passWhen": "false"}}
    text_if = {"id": "text_if", "type": "draw_text", "enabled": True, "config": {"textTemplate": "TWO OR MORE", "x": 4, "y": 24, "backgroundColor": "#ff0000"}}
    text_else = {"id": "text_else", "type": "draw_text", "enabled": True, "config": {"textTemplate": "LESS THAN TWO", "x": 4, "y": 24, "backgroundColor": "#0000ff"}}
    branches = {
        "nodes": [{"id": "input", "type": "input", "enabled": True}, {"id": "detector", "type": "detector", "enabled": True}, gate_if, gate_else, text_if, text_else, {"id": "preview", "type": "preview", "enabled": True}],
        "edges": [["input", "detector"], ["detector", "gate_if"], ["detector", "gate_else"], ["gate_if", "text_if"], ["gate_else", "text_else"], ["text_if", "preview"], ["text_else", "preview"]],
    }
    two_objects = [
        {"kind": "detection", "class": "person", "score": 0.9, "bbox": [5, 5, 10, 10]},
        {"kind": "detection", "class": "person", "score": 0.8, "bbox": [30, 5, 10, 10]},
    ]
    actual = nodes.apply_drawing_nodes(frame, branches, "preview", two_objects, {})
    if_branch = {"nodes": [*branches["nodes"][:3], text_if, branches["nodes"][-1]], "edges": [["input", "detector"], ["detector", "gate_if"], ["gate_if", "text_if"], ["text_if", "preview"]]}
    expected = nodes.apply_drawing_nodes(frame, if_branch, "preview", two_objects, {})
    assert np.array_equal(actual, expected), "Only the passing IF branch should draw text"

    # Test line_counter_in metric with event_runtime
    runtime["_event_runtime"] = {"line1": {"total_in": 5, "total_out": 2}}
    line_metric_node = {"id": "gate_line", "type": "if_else", "config": {"metric": "line_counter_in", "operator": "gte", "value": 5, "passWhen": "true"}}
    assert nodes._logic_signal(line_metric_node, [], runtime, now=1.2) is True
    line_metric_node["config"]["value"] = 6
    assert nodes._logic_signal(line_metric_node, [], runtime, now=1.3) is False


def test_blur_sharpen_all_algorithms():
    frame = np.ones((40, 40, 3), np.uint8) * 128
    frame[15:25, 15:25] = 255  # High-contrast center patch

    # 1. Box Blur
    box_res = nodes.apply_image_processing(frame, _workflow({"id": "b1", "type": "blur_sharpen", "config": {"operation": "blur", "kernel": 5}}), {})
    assert box_res.shape == frame.shape

    # 2. Gaussian Blur
    gauss_res = nodes.apply_image_processing(frame, _workflow({"id": "b2", "type": "blur_sharpen", "config": {"operation": "gaussian_blur", "kernel": 5}}), {})
    assert gauss_res.shape == frame.shape

    # 3. Median Blur
    med_res = nodes.apply_image_processing(frame, _workflow({"id": "b3", "type": "blur_sharpen", "config": {"operation": "median_blur", "kernel": 5}}), {})
    assert med_res.shape == frame.shape

    # 4. Bilateral Filter
    bilat_res = nodes.apply_image_processing(frame, _workflow({"id": "b4", "type": "blur_sharpen", "config": {"operation": "bilateral", "kernel": 5}}), {})
    assert bilat_res.shape == frame.shape

    # 5. Sharpening
    sharp_res = nodes.apply_image_processing(frame, _workflow({"id": "b5", "type": "blur_sharpen", "config": {"operation": "sharpen", "kernel": 3, "strength": 1.5}}), {})
    assert sharp_res.shape == frame.shape

    # 6. Verify Brightness/Contrast does NOT blur image
    bc_res = nodes.apply_image_processing(frame, _workflow({"id": "bc", "type": "brightness_contrast", "config": {"brightness": 0, "contrast": 1.0}}), {})
    # Since brightness=0, contrast=1.0 and no CLAHE, it should be identical to frame
    assert np.array_equal(bc_res, frame), "Brightness/Contrast must not blur the frame!"


def test_privacy_blur():
    import core
    # Create textured frame with details inside target box
    frame = np.zeros((60, 60, 3), np.uint8)
    frame[20:40:2, 20:40:2] = 255  # Checkerboard texture

    detections = [{"class": "face", "score": 0.95, "x": 20, "y": 20, "width": 20, "height": 20}]
    workflow_gauss = {"nodes": [{"id": "anon", "type": "blur_anonymizer", "enabled": True, "config": {"classes": "face", "mode": "gaussian", "kernelSize": 15}}]}
    copy1 = frame.copy()
    core._apply_privacy_blur(workflow_gauss, copy1, detections)
    # Target center should be blurred (no longer raw checkerboard)
    assert not np.array_equal(copy1[20:40, 20:40], frame[20:40, 20:40])

    workflow_pix = {"nodes": [{"id": "anon2", "type": "blur_anonymizer", "enabled": True, "config": {"classes": "face", "mode": "pixelate", "pixelateBlock": 8}}]}
    copy2 = frame.copy()
    core._apply_privacy_blur(workflow_pix, copy2, detections)
    assert not np.array_equal(copy2[20:40, 20:40], frame[20:40, 20:40])


def test_all_nodes_catalog_audit():
    import node_catalog
    assert {"zone_activity_timer", "zone_exit_event"} <= node_catalog.NODE_BLUEPRINTS.keys()
    assert len(node_catalog.NODE_BLUEPRINTS) >= 48
    for key, bp in node_catalog.NODE_BLUEPRINTS.items():
        assert "title" in bp, f"Node {key} missing title"
        assert "subtitle" in bp, f"Node {key} missing subtitle"
        assert len(bp["title"].strip()) > 0, f"Node {key} title is empty"
        assert len(bp["subtitle"].strip()) > 0, f"Node {key} subtitle is empty"
        assert "config" in bp, f"Node {key} missing config dict"


def main():
    failures = []
    checks = (
        test_image_processing,
        test_branch_remap_and_filter,
        test_logic_and_overlay,
        test_catalog_helpers,
        test_line_counter,
        test_if_else_branching,
        test_blur_sharpen_all_algorithms,
        test_privacy_blur,
        test_all_nodes_catalog_audit,
    )
    for check in checks:
        try:
            check()
        except Exception as exc:
            failures.append((check.__name__, exc))
            print(f"FAIL {check.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"PASS {check.__name__}")
    if failures:
        raise SystemExit(1)
    print("all 9 node test suites passed successfully")


if __name__ == "__main__":
    main()
