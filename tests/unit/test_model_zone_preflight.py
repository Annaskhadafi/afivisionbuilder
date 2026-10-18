"""Focused contract checks for project-zone model class preflight."""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import HTTPException

import server
from engine.custom_model_runtime import extract_model_labels


def _workflow(model_paths: list[Path], zone_type: str, zone_config: dict, *, zone_enabled: bool = True) -> dict:
    nodes = [
        {"id": "input", "type": "input", "config": {}},
        {"id": "detector", "type": "detector", "config": {
            "engine": "onnx_custom", "modelPath": str(model_paths[0]), "threshold": 0.25,
        }},
        {"id": "tracker", "type": "tracker", "config": {}},
        {"id": "zone", "type": zone_type, "enabled": zone_enabled, "config": zone_config},
        {"id": "preview", "type": "preview", "config": {}},
    ]
    edges = [["input", "detector"], ["detector", "tracker"], ["tracker", "zone"], ["zone", "preview"]]
    for index, path in enumerate(model_paths[1:], start=2):
        nodes.append({"id": f"detector-{index}", "type": "detector", "config": {
            "engine": "onnx_custom", "modelPath": str(path), "threshold": 0.25,
        }})
    return {"nodes": nodes, "edges": edges}


def _model(directory: Path, name: str, labels: str) -> Path:
    path = directory / Path(name).stem / name
    path.parent.mkdir()
    path.write_bytes(b"fake onnx payload")
    (path.parent / "labels.txt").write_text(labels + "\n", encoding="utf-8")
    return path


def _run(workflow: dict) -> None:
    server._preflight_models(server.validate_workflow(workflow))


def _timer_config(**overrides: object) -> dict:
    config = {
        "points": "0,0;1,0;1,1;0,1",
        "requiredClasses": "tire",
        "requiredCount": 1,
        "triggerClasses": "person",
        "triggerCount": 1,
        "confirmationSeconds": 10,
        "maxObservationGapSeconds": 5,
    }
    config.update(overrides)
    return config


def _exit_config(**overrides: object) -> dict:
    config = {"points": "0,0;1,0;1,1;0,1", "classes": "truck,tire"}
    config.update(overrides)
    return config


def test_workshop_zone_accepts_tire_and_person_model_classes():
    with tempfile.TemporaryDirectory() as directory:
        model = _model(Path(directory), "workshop.onnx", "person\ntire")
        _run(_workflow([model], "zone_activity_timer", _timer_config()))


def test_default_rfdetr_uses_coco_classes_for_zone_preflight():
    with tempfile.TemporaryDirectory() as directory:
        workflow = _workflow([Path(directory) / "unused.onnx"], "zone_exit_event", _exit_config(classes="truck"))
        workflow["nodes"][1]["config"] = {"engine": "rfdetr", "modelPath": "", "customModelPath": ""}
        _run(workflow)


def test_default_rfdetr_does_not_claim_custom_tire_class():
    with tempfile.TemporaryDirectory() as directory:
        workflow = _workflow([Path(directory) / "unused.onnx"], "zone_exit_event", _exit_config(classes="tire"))
        workflow["nodes"][1]["config"] = {"engine": "rfdetr", "modelPath": "", "customModelPath": ""}
        try:
            _run(workflow)
        except HTTPException as exc:
            assert exc.status_code == 400
            assert "tire" in str(exc.detail).lower()
        else:
            raise AssertionError("default RF-DETR unexpectedly claimed custom tire class")


def test_workshop_zone_rejects_missing_tire_even_when_custom_classes_relabel_it():
    with tempfile.TemporaryDirectory() as directory:
        model = _model(Path(directory), "person-only.onnx", "person")
        workflow = _workflow([model], "zone_activity_timer", _timer_config())
        workflow["nodes"][1]["config"]["customClasses"] = "person,tire"
        try:
            _run(workflow)
        except HTTPException as exc:
            assert exc.status_code == 400
            assert "tire" in str(exc.detail).lower()
        else:
            raise AssertionError("model without tire label unexpectedly passed preflight")


def test_warehouse_zone_rejects_when_truck_or_tire_is_missing():
    for labels in ("truck", "tire"):
        with tempfile.TemporaryDirectory() as directory:
            model = _model(Path(directory), "warehouse.onnx", labels)
            workflow = _workflow([model], "zone_exit_event", _exit_config())
            try:
                _run(workflow)
            except HTTPException as exc:
                assert exc.status_code == 400
                assert any(label in str(exc.detail).lower() for label in ("truck", "tire"))
            else:
                raise AssertionError(f"warehouse model labels {labels!r} unexpectedly passed preflight")


def test_zone_preflight_does_not_merge_labels_from_unrelated_detector_branch():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        person_model = _model(root, "person.onnx", "person")
        tire_model = _model(root, "tire.onnx", "tire")
        workflow = _workflow([person_model, tire_model], "zone_activity_timer", _timer_config())
        try:
            _run(workflow)
        except HTTPException as exc:
            assert exc.status_code == 400
            assert "tire" in str(exc.detail).lower()
        else:
            raise AssertionError("labels from an unrelated detector branch satisfied the zone")


def test_disabled_zone_skips_model_class_preflight():
    with tempfile.TemporaryDirectory() as directory:
        model = _model(Path(directory), "person-only.onnx", "person")
        _run(_workflow([model], "zone_activity_timer", _timer_config(), zone_enabled=False))


def test_active_zone_rejects_unknown_required_class():
    with tempfile.TemporaryDirectory() as directory:
        model = _model(Path(directory), "car.onnx", "car")
        workflow = _workflow([model], "zone_exit_event", _exit_config(classes="forklift"))
        try:
            _run(workflow)
        except HTTPException as exc:
            assert exc.status_code == 400
            assert "forklift" in str(exc.detail).lower()
        else:
            raise AssertionError("unknown active zone class unexpectedly passed preflight")


def test_model_sidecar_label_changes_invalidate_label_cache():
    with tempfile.TemporaryDirectory() as directory:
        model = _model(Path(directory), "cache.onnx", "person")
        assert extract_model_labels(str(model)) == ["person"]

        labels_path = model.parent / "labels.txt"
        labels_path.write_text("person\ntire\n", encoding="utf-8")
        assert extract_model_labels(str(model)) == ["person", "tire"]

        labels_path.unlink()
        assert extract_model_labels(str(model)) == []
