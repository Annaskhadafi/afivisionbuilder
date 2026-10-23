import pytest
from engine.core import _filter_and_remap_detections
from engine.main import active_filter_node, filter_detections, detections_for_node, apply_logic_nodes


def test_filter_and_remap_with_allowed_classes():
    dets = [
        {"class": "person", "score": 0.9, "bbox": [10, 10, 20, 20]},
        {"class": "car", "score": 0.85, "bbox": [30, 30, 40, 40]},
        {"class": "dog", "score": 0.75, "bbox": [50, 50, 20, 20]},
    ]
    # Filter for only "person"
    kept, _ = _filter_and_remap_detections(
        dets,
        default_threshold=0.5,
        tracking_threshold=0.3,
        is_tracking_eligible=True,
        per_class_map={},
        class_remap_map={},
        allowed_classes={"person"},
    )
    assert len(kept) == 1
    assert kept[0]["class"] == "person"

    # Filter for "person" and "car"
    kept2, _ = _filter_and_remap_detections(
        dets,
        default_threshold=0.5,
        tracking_threshold=0.3,
        is_tracking_eligible=True,
        per_class_map={},
        class_remap_map={},
        allowed_classes={"person", "car"},
    )
    assert len(kept2) == 2
    assert {d["class"] for d in kept2} == {"person", "car"}


def test_dynamic_filter_node_id():
    workflow = {
        "nodes": [
            {"id": "input", "type": "input", "enabled": True},
            {"id": "det_1", "type": "detector", "enabled": True},
            {"id": "filter_custom_id_123", "type": "filter", "enabled": True, "config": {"classes": "person"}},
            {"id": "preview_1", "type": "preview", "enabled": True},
        ],
        "edges": [
            ["input", "det_1"],
            ["det_1", "filter_custom_id_123"],
            ["filter_custom_id_123", "preview_1"],
        ],
    }
    filter_node = active_filter_node(workflow)
    assert filter_node is not None
    assert filter_node["id"] == "filter_custom_id_123"

    raw_dets = [
        {"class": "person", "score": 0.9, "bbox": [10, 10, 20, 20]},
        {"class": "truck", "score": 0.8, "bbox": [50, 50, 30, 30]},
    ]
    filtered_dets = filter_detections(workflow, raw_dets)
    assert len(filtered_dets) == 1
    assert filtered_dets[0]["class"] == "person"

    # Preview downstream of filter gets filtered detections
    res = detections_for_node(workflow, "preview_1", raw_dets, filtered_dets)
    assert len(res) == 1
    assert res[0]["class"] == "person"


def test_class_detected_condition_filters_classes():
    workflow = {
        "nodes": [
            {"id": "input", "type": "input", "enabled": True},
            {"id": "det", "type": "detector", "enabled": True},
            {"id": "cond", "type": "class_detected_condition", "enabled": True, "config": {"classes": "person"}},
            {"id": "preview", "type": "preview", "enabled": True},
        ],
        "edges": [
            ["input", "det"],
            ["det", "cond"],
            ["cond", "preview"],
        ],
    }
    raw_dets = [
        {"class": "person", "score": 0.92, "bbox": [10, 10, 20, 20]},
        {"class": "bicycle", "score": 0.88, "bbox": [40, 40, 30, 30]},
    ]
    passed_dets = apply_logic_nodes(workflow, "preview", raw_dets)
    # Condition passed, and only person should be passed through
    assert len(passed_dets) == 1
    assert passed_dets[0]["class"] == "person"


def test_class_remap_parsing_and_filtering():
    from engine.core import _parse_class_remap

    # 1. Parsing formats
    assert _parse_class_remap("car->mobil") == {"car": "mobil"}
    assert _parse_class_remap("car -> mobil") == {"car": "mobil"}
    assert _parse_class_remap("car:mobil") == {"car": "mobil"}
    assert _parse_class_remap("car: mobil") == {"car": "mobil"}
    assert _parse_class_remap("car=>mobil") == {"car": "mobil"}
    assert _parse_class_remap("car=mobil") == {"car": "mobil"}
    assert _parse_class_remap("car->mobil, truck->truk") == {"car": "mobil", "truck": "truk"}
    assert _parse_class_remap("car->mobil; truck:truk\nperson=>orang") == {
        "car": "mobil",
        "truck": "truk",
        "person": "orang",
    }

    # 2. Remap with allowed_classes matching raw class
    dets = [
        {"class": "car", "score": 0.85, "bbox": [30, 30, 40, 40]},
        {"class": "person", "score": 0.90, "bbox": [10, 10, 20, 20]},
    ]
    remap_map = _parse_class_remap("car->mobil")
    kept, _ = _filter_and_remap_detections(
        dets,
        default_threshold=0.5,
        tracking_threshold=0.3,
        is_tracking_eligible=True,
        per_class_map={},
        class_remap_map=remap_map,
        allowed_classes={"car"},
    )
    assert len(kept) == 1
    assert kept[0]["class"] == "mobil"
    assert kept[0]["originalClass"] == "car"

    # 3. Remap with allowed_classes matching target class
    kept2, _ = _filter_and_remap_detections(
        dets,
        default_threshold=0.5,
        tracking_threshold=0.3,
        is_tracking_eligible=True,
        per_class_map={},
        class_remap_map=remap_map,
        allowed_classes={"mobil"},
    )
    assert len(kept2) == 1
    assert kept2[0]["class"] == "mobil"
    assert kept2[0]["originalClass"] == "car"

    # 4. Downstream filter accepts either original or remapped class
    workflow = {
        "nodes": [
            {"id": "filter", "type": "filter", "enabled": True, "config": {"classes": "mobil"}}
        ]
    }
    filtered = filter_detections(workflow, kept)
    assert len(filtered) == 1
    assert filtered[0]["class"] == "mobil"

