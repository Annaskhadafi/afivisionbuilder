from __future__ import annotations

from engine.main import _logic_signal, apply_logic_nodes


PERSON = {"kind": "detection", "class": "person", "score": 0.9, "bbox": [0, 0, 10, 10]}
CAR = {"kind": "detection", "class": "car", "score": 0.6, "bbox": [20, 0, 10, 10]}


def gate(node_type: str, **config):
    return {"id": f"gate-{node_type}", "type": node_type, "config": config}


def test_compare_value_compares_configured_confidence_metric():
    node = gate("compare_value", metric="max_confidence", operator="gte", value=0.8)
    runtime = {}

    assert _logic_signal(node, [PERSON, CAR], runtime, now=1.0) is True
    assert runtime[node["id"]]["actual_value"] == 0.9
    node["config"]["value"] = 0.95
    assert _logic_signal(node, [PERSON, CAR], runtime, now=2.0) is False


def test_object_count_condition_filters_downstream_classes():
    node = gate("object_count_condition", operator="gte", count=2, classes="person")
    workflow = {
        "nodes": [{"id": "input", "type": "input"}, {"id": "detector", "type": "detector"}, node, {"id": "preview", "type": "preview"}],
        "edges": [["input", "detector"], ["detector", node["id"]], [node["id"], "preview"]],
    }

    assert apply_logic_nodes(workflow, "preview", [PERSON, CAR], {}, now=1.0) == [PERSON]
    node["config"]["count"] = 3
    assert apply_logic_nodes(workflow, "preview", [PERSON, CAR], {}, now=2.0) == []


def test_timer_delay_requires_continuous_positive_signal_and_resets_on_clear():
    node = gate("timer_delay", seconds=2.0)
    runtime = {}

    assert _logic_signal(node, [PERSON], runtime, now=10.0) is False
    assert _logic_signal(node, [PERSON], runtime, now=11.9) is False
    assert _logic_signal(node, [PERSON], runtime, now=12.0) is True
    assert _logic_signal(node, [], runtime, now=12.1) is False
    assert _logic_signal(node, [PERSON], runtime, now=20.0) is False
    assert _logic_signal(node, [PERSON], runtime, now=22.0) is True


def test_debounce_passes_only_after_input_has_stayed_high_for_window():
    node = gate("debounce", seconds=1.5)
    runtime = {}

    assert _logic_signal(node, [PERSON], runtime, now=5.0) is False
    assert _logic_signal(node, [PERSON], runtime, now=6.49) is False
    assert _logic_signal(node, [PERSON], runtime, now=6.5) is True
    assert _logic_signal(node, [], runtime, now=7.0) is False
    assert _logic_signal(node, [PERSON], runtime, now=7.2) is False
    assert _logic_signal(node, [PERSON], runtime, now=8.7) is True


def test_rate_limiter_passes_first_signal_then_enforces_interval():
    node = gate("rate_limiter", seconds=3.0)
    runtime = {}

    assert _logic_signal(node, [PERSON], runtime, now=1.0) is True
    assert _logic_signal(node, [PERSON], runtime, now=3.99) is False
    assert _logic_signal(node, [PERSON], runtime, now=4.0) is True
    assert _logic_signal(node, [], runtime, now=5.0) is False
    assert _logic_signal(node, [PERSON], runtime, now=7.0) is True


def test_and_or_logic_combines_detection_signal_with_configured_boolean():
    and_node = gate("and_or_logic", operator="and", enabledValue=False)
    or_node = gate("and_or_logic", operator="or", enabledValue=True)

    assert _logic_signal(and_node, [PERSON], {}, now=1.0) is False
    assert _logic_signal(or_node, [], {}, now=1.0) is True
    assert _logic_signal(or_node, [PERSON], {}, now=1.1) is True


def test_trigger_once_suppresses_repeats_until_signal_clears():
    node = gate("trigger_once", resetOnClear=True)
    runtime = {}

    assert _logic_signal(node, [PERSON], runtime, now=1.0) is True
    assert _logic_signal(node, [PERSON], runtime, now=2.0) is False
    assert _logic_signal(node, [], runtime, now=3.0) is False
    assert _logic_signal(node, [PERSON], runtime, now=4.0) is True


def test_trigger_once_can_remain_latched_after_signal_clears():
    node = gate("trigger_once", resetOnClear=False)
    runtime = {}

    assert _logic_signal(node, [PERSON], runtime, now=1.0) is True
    assert _logic_signal(node, [], runtime, now=2.0) is False
    assert _logic_signal(node, [PERSON], runtime, now=3.0) is False
