import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import cv2
import numpy as np

from workflow_export import build_zip, prepare


ROOT = Path(__file__).resolve().parents[2]


def workflow(source_path="C:/private/source.mp4"):
    return {
        "nodes": [
            {"id": "input", "type": "input", "enabled": True, "config": {"sourceType": "video", "filePath": source_path}},
            {"id": "preview", "type": "preview", "enabled": True, "config": {}},
            {"id": "export_code", "type": "export_code", "enabled": True, "config": {"packageName": "Workshop Demo", "version": "1.0.0", "includeModels": True}},
            {"id": "disabled", "type": "notification_dispatcher", "enabled": False, "config": {"botToken": "do-not-export"}},
        ],
        "edges": [["input", "preview"]],
    }


def test_export_zip_runs_outside_project(tmp_path):
    graph, manifest, files = prepare(workflow(), "Original", ROOT)
    archive = tmp_path / "package.zip"
    build_zip(graph, manifest, files, ROOT, archive)
    with zipfile.ZipFile(archive) as zipped:
        payload = zipped.read("workflow.json").decode()
        assert "C:/private" not in payload
        assert "do-not-export" not in payload
        assert "export_code" not in payload
        assert json.loads(zipped.read("manifest.json"))["name"] == "workshop-demo"
        zipped.extractall(tmp_path / "unpacked")
    env = os.environ.copy()
    env["AFI_INPUT_FILEPATH"] = str(tmp_path / "video.mp4")
    check = subprocess.run([sys.executable, "run.py", "--check"], cwd=tmp_path / "unpacked", env=env, capture_output=True, text=True, timeout=30)
    assert check.returncode == 0, check.stderr
    assert "Package and configuration OK" in check.stdout
    video = cv2.VideoWriter(str(tmp_path / "video.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 64))
    assert video.isOpened()
    for index in range(12):
        video.write(np.full((64, 64, 3), index * 12, dtype=np.uint8))
    video.release()
    run = subprocess.run([sys.executable, "run.py", "--seconds", "2"], cwd=tmp_path / "unpacked", env=env, capture_output=True, text=True, timeout=45)
    assert run.returncode == 0, run.stderr
    assert "Starting workflow runner" in run.stdout
    assert "Opened video file" in run.stdout, run.stdout


def test_export_blocks_unsafe_graph_and_keeps_credentials_out(tmp_path):
    candidate = workflow()
    candidate["edges"].append(["preview", "export_code"])
    with pytest.raises(ValueError, match="must have no connections"):
        prepare(candidate, "Demo", ROOT)
    candidate["edges"].pop()
    candidate["nodes"][0]["config"]["sourceType"] = "camera"
    candidate["nodes"][0]["config"]["filePath"] = ""
    candidate["nodes"][0]["config"]["source"] = "rtsp://user:pass@example.test/live"
    graph, manifest, _ = prepare(candidate, "Demo", ROOT)
    assert graph["nodes"][0]["config"]["source"] == "$ENV/AFI_INPUT_SOURCE"
    assert "pass" not in json.dumps(graph)
    assert manifest["environment"][0]["name"] == "AFI_INPUT_SOURCE"
    candidate["nodes"][0]["config"]["extra"] = {"secretToken": "private-value"}
    with pytest.raises(ValueError, match="credential must be moved"):
        prepare(candidate, "Demo", ROOT)


def test_local_model_is_portable_or_requires_matching_file(tmp_path):
    model = tmp_path / "best.onnx"
    model.write_bytes(b"model-checksum-test")
    candidate = workflow()
    candidate["nodes"].insert(1, {"id": "detector", "type": "detector", "enabled": True, "config": {"engine": "onnx_custom", "modelPath": str(model)}})
    candidate["edges"] = [["input", "detector"], ["detector", "preview"]]
    graph, manifest, files = prepare(candidate, "Demo", ROOT)
    assert str(model) not in json.dumps(graph)
    assert len(files) == 1
    assert graph["nodes"][1]["config"]["modelPath"].startswith("$PACKAGE/models/")
    candidate["nodes"][-2]["config"]["includeModels"] = False
    graph, manifest, files = prepare(candidate, "Demo", ROOT)
    assert not files
    assert graph["nodes"][1]["config"]["modelPath"] == "$ENV/AFI_DETECTOR_MODELPATH"
    assert manifest["models"][0]["sha256"]
    archive = tmp_path / "external.zip"
    build_zip(graph, manifest, files, ROOT, archive)
    with zipfile.ZipFile(archive) as zipped:
        zipped.extractall(tmp_path / "external")
    env = os.environ.copy()
    env.update({"AFI_INPUT_FILEPATH": str(tmp_path / "video.mp4"), "AFI_DETECTOR_MODELPATH": str(model)})
    command = [sys.executable, "run.py", "--check"]
    assert subprocess.run(command, cwd=tmp_path / "external", env=env, capture_output=True, timeout=30).returncode == 0
    model.write_bytes(b"changed")
    assert subprocess.run(command, cwd=tmp_path / "external", env=env, capture_output=True, timeout=30).returncode == 1


def test_model_in_configured_app_data_is_found(tmp_path, monkeypatch):
    model = tmp_path / "models" / "best.onnx"
    model.parent.mkdir()
    model.write_bytes(b"managed-model")
    monkeypatch.setenv("VISONODE_APP_DATA_DIR", str(tmp_path))
    candidate = workflow()
    candidate["nodes"].insert(1, {"id": "detector", "type": "detector", "config": {"engine": "onnx_custom", "modelPath": "best.onnx"}})
    graph, manifest, files = prepare(candidate, "Demo", ROOT)
    assert manifest["models"][0]["sha256"]
    assert files


def test_default_detector_adds_its_runtime_dependency():
    candidate = workflow()
    candidate["nodes"].insert(1, {"id": "detector", "type": "detector", "config": {}})
    _, manifest, _ = prepare(candidate, "Demo", ROOT)
    assert manifest["dependencyVersions"]["rfdetr"]


def test_lean_requirements_and_engine_filtering(tmp_path):
    # Basic workflow with only input and preview
    basic_graph, basic_manifest, basic_files = prepare(workflow(), "Basic", ROOT)
    basic_zip = tmp_path / "basic.zip"
    build_zip(basic_graph, basic_manifest, basic_files, ROOT, basic_zip)

    with zipfile.ZipFile(basic_zip) as zipped:
        reqs = zipped.read("requirements.txt").decode()
        # Should include base runtime + streamlit
        assert "streamlit==" in reqs or "streamlit>=" in reqs
        assert "opencv-python" in reqs
        # Should NOT include heavy deep learning packages not used
        assert "rfdetr" not in reqs
        assert "tensorflow" not in reqs
        assert "uniface" not in reqs

        # App and launchers should exist
        namelist = zipped.namelist()
        assert "run.py" in namelist
        assert "app.py" in namelist
        assert "install.bat" in namelist
        assert "install.sh" in namelist
        assert "run_web.bat" in namelist
        assert "run_opencv.bat" in namelist
        assert "README.md" in namelist

        # App.py should be valid Python code
        app_code = zipped.read("app.py").decode("utf-8")
        compiled = compile(app_code, "app.py", "exec")
        assert compiled is not None

        # Excluded studio files should not be present
        assert "engine/ai_studio_assistant.py" not in namelist
        assert "engine/install_ai_dependencies.py" not in namelist
        assert "engine/workflow_store.py" not in namelist

    # Workflow with YOLO detector only - models should be bundled directly
    yolo_cand = workflow()
    yolo_cand["nodes"].insert(1, {"id": "detector", "type": "detector", "config": {"engine": "yolo", "modelPath": "yolov8n.pt"}})
    yolo_graph, yolo_manifest, yolo_files = prepare(yolo_cand, "YOLO_Test", ROOT)
    assert len(yolo_files) >= 1
    assert any("yolov8n.pt" in name for name in yolo_files)
    yolo_zip = tmp_path / "yolo.zip"
    build_zip(yolo_graph, yolo_manifest, yolo_files, ROOT, yolo_zip)

    with zipfile.ZipFile(yolo_zip) as zipped:
        yolo_reqs = zipped.read("requirements.txt").decode()
        assert "ultralytics" in yolo_reqs
        assert "torch" in yolo_reqs
        # RF-DETR and TensorFlow should NOT be bundled
        assert "rfdetr" not in yolo_reqs
        assert "tensorflow" not in yolo_reqs

        # Model file must be in the ZIP download
        zipped_names = zipped.namelist()
        assert any("yolov8n.pt" in name for name in zipped_names)
        assert "install.bat" in zipped_names
        install_bat_content = zipped.read("install.bat").decode("utf-8")
        assert "requirements.txt" in install_bat_content


def test_ocr_models_bundled_in_download(tmp_path):
    cand = workflow()
    cand["nodes"].insert(1, {"id": "ocr", "type": "ocr", "config": {}})
    graph, manifest, files = prepare(cand, "OCR_Test", ROOT)
    archive = tmp_path / "ocr.zip"
    build_zip(graph, manifest, files, ROOT, archive)
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        assert "data/models/ocr/ppocrv3_det.onnx" in names
        assert "data/models/ocr/ppocrv3_en_rec.onnx" in names
        assert "data/models/ocr/en_dict.txt" in names
        assert "install.bat" in names


def test_bat_files_syntax_validity(tmp_path):
    cand = workflow()
    graph, manifest, files = prepare(cand, "Bat_Test", ROOT)
    archive = tmp_path / "pkg.zip"
    build_zip(graph, manifest, files, ROOT, archive)
    unpacked = tmp_path / "unpacked"
    with zipfile.ZipFile(archive) as zipped:
        zipped.extractall(unpacked)

    # Check each batch file for fatal syntax errors like ") was unexpected at this time"
    for bat_name in ["install.bat", "run_web.bat", "run_opencv.bat"]:
        bat_file = unpacked / bat_name
        assert bat_file.is_file()
        content = bat_file.read_text(encoding="utf-8")
        assert 'cd /d "%~dp0"' in content
        assert "pause" in content
        # Ensure no dangerous parentheses patterns like 'echo ... (.venv)' inside parenthesized blocks
        assert "echo [1/4] Membuat Virtual Environment lokal (.venv)" not in content

    # Base workflow without AI should not test for torch/nvidia-smi
    base_install = (unpacked / "install.bat").read_text(encoding="utf-8")
    assert "nvidia-smi" not in base_install
    assert "run.py --check" in base_install

    # AI workflow should include hardware detection and self-test
    ai_cand = workflow()
    ai_cand["nodes"].insert(1, {"id": "detector", "type": "detector", "config": {"engine": "yolo", "modelPath": "yolov8n.pt"}})
    ai_graph, ai_manifest, ai_files = prepare(ai_cand, "AI_Test", ROOT)
    ai_archive = tmp_path / "ai_pkg.zip"
    build_zip(ai_graph, ai_manifest, ai_files, ROOT, ai_archive)
    with zipfile.ZipFile(ai_archive) as zipped:
        ai_install = zipped.read("install.bat").decode("utf-8")
        assert "nvidia-smi" in ai_install
        assert "run.py --check" in ai_install
