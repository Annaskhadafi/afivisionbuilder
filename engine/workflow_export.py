"""Build a portable workflow runner without copying project data or secrets."""

from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

PACKAGE_PREFIX = "$PACKAGE/"
ENV_PREFIX = "$ENV/"
MODEL_KEYS = {
    "modelPath", "customModelPath", "rfdetrCheckpoint", "rfdetrOnnxModel",
    "rfdetrTensorRTEngine", "samCheckpoint", "convnextCheckpoint", "efficientadModel",
}
OUTPUT_KEYS = {"outputPath", "outputDirectory", "databasePath", "outputFilePath"}
SECRET_KEYS = {"password", "apiKey", "roboflowApiKey", "botToken", "accessKey", "secretKey"}
SENSITIVE_QUERY = {"token", "key", "api_key", "apikey", "password", "secret", "signature"}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower().replace("_", "-")).strip("-")[:64] or "workflow"


def _file(root: Path, raw: str) -> Path | None:
    path = Path(raw).expanduser()
    app_data = Path(os.environ.get("VISONODE_APP_DATA_DIR", str(root / "data"))).resolve()
    candidates = [path] if path.is_absolute() else [
        root / path, root / "data" / "models" / path, root / "data" / "models" / path.name,
        app_data / path, app_data / "models" / path, app_data / "models" / path.name,
        app_data / "uploads" / path, app_data / "uploads" / path.name,
        root / "data" / "uploads" / path, root / "engine" / path,
    ]
    return next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


NODE_TYPE_TO_ENGINE_FILES = {
    "detector": {"custom_model_runtime.py", "rfdetr_onnx_runtime.py"},
    "segmenter": {"custom_model_runtime.py", "rfdetr_onnx_runtime.py"},
    "classifier": {"custom_model_runtime.py"},
    "tracker": {"roboflow_tracker.py"},
    "distance_measurement": {"spatial_measurement.py"},
    "size_measurement": {"spatial_measurement.py"},
    "camera_focus_score": {"classical_cv.py"},
    "auto_rotate_edges": {"classical_cv.py"},
    "overlap_analysis": {"advanced_logic.py"},
    "delta_filter": {"advanced_logic.py"},
    "switch_case": {"advanced_logic.py"},
    "velocity_calculator": {"video_kinematics.py"},
    "path_deviation": {"video_kinematics.py"},
    "detections_difference": {"detections_difference.py"},
    "detections_consensus": {"detections_consensus.py"},
    "data_aggregator": {"data_aggregation.py"},
    "csv_formatter": {"data_aggregation.py"},
    "s3_sink": {"cloud_sinks.py"},
    "notification_dispatcher": {"cloud_sinks.py"},
    "screenshot": {"screenshot_capture.py"},
    "telegram_sink": {"telegram_sink.py"},
    "ptz_controller": {"ptz_controller.py"},
    "ocr": {"ocr_engine.py"},
    "object_timer": {"object_timer.py"},
    "dominant_color": {"dominant_color.py"},
    "class_replacement": {"class_replacement.py"},
    "man_down_detector": {"man_down_detector.py"},
    "lpr_license_plate": {"lpr_license_plate.py"},
    "overstack_detector": {"overstack_detector.py"},
    "model_comparison": {"model_comparison.py"},
    "efficientad": {"efficientad_runtime.py"},
    "face_detector": {"uniface_runtime.py"},
    "face_tracker": {"uniface_runtime.py"},
    "face_crop": {"uniface_runtime.py"},
    "vlm_box_tracker": {"vlm_box_tracker.py"},
    "ai_agent": {"ai_agent.py"},
    "multi_zone_occupancy": {"multi_zone_occupancy.py"},
    "zone_timer": {"project_nodes.py"},
    "zone_exit_event": {"project_nodes.py"},
}

CORE_ENGINE_FILES = {
    "core.py",
    "main.py",
    "node_catalog.py",
    "app_version.py",
    "detector_process.py",
    "python_script_runtime.py",
    "visonode_database.py",
    "project_nodes.py",
}

STUDIO_EXCLUDED_FILES = {
    "workflow_export.py",
    "standalone_run.py",
    "standalone_app.py",
    "server.py",
    "ai_studio_assistant.py",
    "ai_worker.py",
    "ai_runtime_assets.py",
    "ai_runtime_profile.py",
    "install_ai_dependencies.py",
    "model_optimization.py",
    "model_quantizer.py",
    "rfdetr_onnx_optimization.py",
    "workflow_store.py",
}


def _determine_required_packages(graph: dict) -> set[str]:
    # Selalu sertakan paket dasar runtime dan Streamlit web app
    packages = {"opencv-python", "numpy", "pillow", "requests", "pyyaml", "streamlit"}
    for node in graph.get("nodes", []):
        ntype = node.get("type", "")
        config = node.get("config", {})
        engine = str(config.get("engine") or "").lower()
        model_path = str(config.get("modelPath") or config.get("customModelPath") or "").lower()

        if ntype in {"detector", "segmenter"}:
            current_engine = engine or "rfdetr"
            if current_engine == "rfdetr":
                packages.update({"rfdetr", "torch", "torchvision"})
            elif current_engine == "rfdetr_onnx" or model_path.endswith(".onnx"):
                packages.update({"onnxruntime", "onnx"})
            elif current_engine in {"yolo", "ultralytics", "roboflow_universe"} or model_path.endswith(".pt") or "yolo" in model_path or "yolo" in current_engine:
                packages.update({"ultralytics", "torch", "torchvision"})
            else:
                if model_path.endswith(".onnx"):
                    packages.update({"onnxruntime", "onnx"})
                elif model_path.endswith(".pt"):
                    packages.update({"ultralytics", "torch", "torchvision"})
                else:
                    packages.update({"rfdetr", "torch", "torchvision"})

        elif ntype == "classifier":
            current_engine = engine or "convnext"
            if current_engine in {"convnext", "timm"}:
                packages.update({"timm", "torch", "torchvision"})
            elif current_engine in {"yolo", "ultralytics"}:
                packages.update({"ultralytics", "torch", "torchvision"})

        elif ntype == "efficientad":
            packages.update({"torch", "torchvision", "timm"})

        elif ntype in {"tracker", "zone", "line_counter", "speed_estimator", "zone_timer", "zone_exit_event", "multi_zone_occupancy"}:
            packages.add("supervision")
            algorithm = str(config.get("algorithm") or "").lower()
            if algorithm in {"norfair", "deepsort"} or engine == "trackers":
                packages.add("trackers")

        elif ntype == "input" and (config.get("sourceType") == "youtube" or config.get("youtubeUrl")):
            packages.add("yt-dlp")

        elif ntype == "ocr":
            packages.update({"onnxruntime", "onnx"})

        elif ntype in {"man_down_detector", "lpr_license_plate", "overstack_detector"}:
            packages.update({"onnxruntime", "onnx"})

    return packages


def _determine_needed_engine_files(graph: dict) -> set[str]:
    needed_files = set(CORE_ENGINE_FILES)
    for node in graph.get("nodes", []):
        ntype = node.get("type", "")
        if ntype in NODE_TYPE_TO_ENGINE_FILES:
            needed_files.update(NODE_TYPE_TO_ENGINE_FILES[ntype])
        config = node.get("config", {})
        if config.get("customModelPath") or config.get("modelPath"):
            needed_files.add("custom_model_runtime.py")
    return needed_files - STUDIO_EXCLUDED_FILES


def _requirements(root: Path, graph: dict) -> tuple[str, dict[str, str]]:
    needed = _determine_required_packages(graph)
    lines = []
    versions = {}
    host_reqs = {}
    req_file = root / "requirements.txt"
    if req_file.is_file():
        for raw in req_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("pytest"):
                continue
            match = re.match(r"[A-Za-z0-9_.-]+", line)
            if match:
                host_reqs[match.group().lower()] = line

    for pkg in sorted(needed):
        pkg_lower = pkg.lower()
        try:
            version = importlib.metadata.version(pkg)
            versions[pkg] = version
            if pkg_lower in host_reqs and " @ " in host_reqs[pkg_lower]:
                lines.append(host_reqs[pkg_lower])
            else:
                lines.append(f"{pkg}=={version}")
        except importlib.metadata.PackageNotFoundError as exc:
            if pkg == "rfdetr":
                raise ValueError("RF-DETR runtime is not installed on the build server") from exc
            if pkg_lower in host_reqs:
                lines.append(host_reqs[pkg_lower])
            else:
                lines.append(f"{pkg}>=1.0.0")

    return "\n".join(lines) + "\n", versions


def _sensitive_url(value: str) -> bool:
    if not value.startswith(("http://", "https://", "rtsp://", "rtsps://")):
        return False
    try:
        parsed = urlsplit(value)
        return bool(parsed.password or parsed.username or any(key.lower() in SENSITIVE_QUERY for key, _ in parse_qsl(parsed.query)))
    except ValueError:
        return True


def _check_remaining_secrets(value, path: str = "workflow") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if re.search(r"password|token|api.?key|secret", key, re.I) and isinstance(item, str) and item and not item.startswith(ENV_PREFIX) and key != "credentialsSecretRef":
                raise ValueError(f"{path}.{key}: credential must be moved to an environment variable")
            _check_remaining_secrets(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_remaining_secrets(item, f"{path}[{index}]")
    elif isinstance(value, str) and (_sensitive_url(value) or re.search(r"Bearer\s+\S+|sk-[A-Za-z0-9_-]{12,}", value, re.I) or re.match(r"(?:[A-Za-z]:[\\/]|\\\\|/(?:home|Users|mnt|tmp|var)/)", value)):
        raise ValueError(f"{path}: sensitive or nonportable value must be removed before export")


def prepare(workflow: dict, name: str, root: Path) -> tuple[dict, dict, dict[str, Path]]:
    """Return portable workflow, manifest, and local model files for ZIP creation."""
    graph = copy.deepcopy(workflow)
    export_nodes = [node for node in graph["nodes"] if node.get("type") == "export_code"]
    if len(export_nodes) != 1 or not export_nodes[0].get("enabled", True):
        raise ValueError("Exactly one enabled Export Code node is required")
    marker = export_nodes[0]
    if any(marker["id"] in edge for edge in graph["edges"]):
        raise ValueError("Export Code is a design-time node and must have no connections")
    options = marker.get("config") or {}
    package_name = _slug(str(options.get("packageName") or name))
    version = str(options.get("version") or "1.0.0").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,31}", version):
        raise ValueError("Export version must use letters, numbers, dots, dashes or underscores")
    include_models = options.get("includeModels", True)
    if not isinstance(include_models, bool):
        raise ValueError("includeModels must be boolean")
    graph["nodes"] = [node for node in graph["nodes"] if node["id"] != marker["id"] and node.get("enabled", True)]
    active_ids = {node["id"] for node in graph["nodes"]}
    graph["edges"] = [edge for edge in graph["edges"] if edge[0] in active_ids and edge[1] in active_ids]
    sources = [node for node in graph["nodes"] if node.get("enabled", True) and node["type"] in {"input", "ip_camera"}]
    if len(sources) != 1:
        raise ValueError("Standalone package requires exactly one enabled Input or IP Camera node")
    if sources[0]["type"] == "input" and sources[0].get("config", {}).get("sourceType") == "daheng":
        raise ValueError("Daheng capture requires a vendor SDK that is not included in standalone packages")
    if sources[0]["type"] == "input" and sources[0].get("config", {}).get("sourceType") in {"file", "image", "video"} and not str(sources[0].get("config", {}).get("filePath") or "").strip():
        raise ValueError("File, image and video sources require filePath before export")
    files: dict[str, Path] = {}
    model_records = []
    variables = []
    warnings = []
    for node in graph["nodes"]:
        config = node.setdefault("config", {})
        if node["type"] in {"face_detector", "face_tracker"}:
            raise ValueError(f"{node['id']}: face model/registry assets are not supported by standalone export yet")
        if node["type"] == "database_output" and not config.get("databasePath"):
            config["databasePath"] = PACKAGE_PREFIX + "data/visonode.db"
        if node["type"] == "image_output" and not config.get("outputDirectory"):
            config["outputDirectory"] = PACKAGE_PREFIX + "data/images"
        if node["type"] == "preview" and config.get("saveVideo") and not config.get("outputPath"):
            config["outputPath"] = PACKAGE_PREFIX + "data/preview.mp4"
        if node["type"] in {"detector", "segmenter", "classifier", "efficientad"}:
            engine_id = str(config.get("engine") or {"detector": "rfdetr", "segmenter": "rfdetr", "classifier": "convnext", "efficientad": "efficientad"}[node["type"]])
            if engine_id in {"sam3", "rfdetr_tensorrt"}:
                raise ValueError(f"{node['id']}: engine {engine_id} requires target-specific assets/runtime and is not supported yet")
            # Auto-assign default model path if not set so model is bundled directly
            if engine_id in {"yolo", "ultralytics"}:
                if not config.get("modelPath") and not config.get("customModelPath"):
                    default_models = {"detector": "yolov8n.pt", "segmenter": "yolov8n-seg.pt", "classifier": "yolov8n-cls.pt"}
                    if node["type"] in default_models:
                        config["modelPath"] = default_models[node["type"]]
            active_model_keys = {
                "rfdetr": {"rfdetrCheckpoint"}, "rfdetr_onnx": {"rfdetrOnnxModel"},
                "rfdetr_tensorrt": {"rfdetrTensorRTEngine"}, "sam3": {"samCheckpoint"},
                "convnext": {"convnextCheckpoint"}, "efficientad": {"efficientadModel"},
            }.get(engine_id, {"modelPath"} if config.get("modelPath") else {"customModelPath"})
            if engine_id == "roboflow_universe":
                active_model_keys = {"modelPath"}
            for model_key in MODEL_KEYS - active_model_keys:
                if model_key in config:
                    config[model_key] = ""
        if node["type"] == "ocr" and include_models:
            ocr_dir = root / "data" / "models" / "ocr"
            for ocr_name in ["ppocrv3_det.onnx", "ppocrv3_en_rec.onnx", "en_dict.txt"]:
                ocr_file = ocr_dir / ocr_name
                if ocr_file.is_file():
                    files[f"data/models/ocr/{ocr_name}"] = ocr_file
        node_tag = re.sub(r"[^A-Z0-9]+", "_", node["id"].upper()).strip("_")[:32]
        if node["type"] == "input" and config.get("sourceType", "camera") == "camera" and not _sensitive_url(str(config.get("source") or "")):
            variables.append({"name": f"AFI_{node_tag}_SOURCE", "nodeId": node["id"], "field": "source", "required": False})
        if node["type"] == "ip_camera" and config.get("streamUrl") and not _sensitive_url(str(config["streamUrl"])):
            variables.append({"name": f"AFI_{node_tag}_STREAMURL", "nodeId": node["id"], "field": "streamUrl", "required": False})
        if node["type"] == "python_script":
            warnings.append(f"{node['id']}: Python Script code is copied verbatim; review it for secrets and extra imports")
        if node["type"] in {"webhook_output", "s3_sink", "notification_dispatcher", "ai_agent", "vlm_box_tracker", "ptz_controller"}:
            warnings.append(f"{node['id']}: external service, connectivity and credentials must be verified on the target machine")
        for key, value in list(config.items()):
            if not isinstance(value, str) or not value:
                continue
            env_name = f"AFI_{node_tag}_{re.sub(r'[^A-Z0-9]+', '_', key.upper())}"
            if key in SECRET_KEYS or (key in {"source", "streamUrl", "url", "endpointUrl", "youtubeUrl"} and _sensitive_url(value)) or (key == "customHeaders" and re.search(r"authorization|api.key|token|secret", value, re.I)):
                config[key] = ENV_PREFIX + env_name
                variables.append({"name": env_name, "nodeId": node["id"], "field": key, "required": True})
            elif key == "filePath" and node["type"] == "input":
                if config.get("sourceType") in {"file", "image", "video"}:
                    config[key] = ENV_PREFIX + env_name
                    variables.append({"name": env_name, "nodeId": node["id"], "field": key, "required": True})
                else:
                    config[key] = ""
            elif key in OUTPUT_KEYS and not value.startswith(PACKAGE_PREFIX):
                suffix = Path(value).suffix if key in {"outputPath", "databasePath", "outputFilePath"} else ""
                config[key] = PACKAGE_PREFIX + f"data/{_slug(node['id'])}{suffix}"
            elif key in MODEL_KEYS and node["type"] in {"detector", "segmenter", "classifier", "efficientad"}:
                if config.get("engine") == "roboflow_universe" and key in {"modelPath", "customModelPath"}:
                    continue
                path = _file(root, value)
                if path is None:
                    raise ValueError(f"{node['id']}: model file not found: {value}")
                digest = _sha256(path)
                archive_name = f"models/{digest[:12]}-{path.name}"
                model_records.append({"nodeId": node["id"], "field": key, "sha256": digest, "file": archive_name if include_models else None})
                if include_models:
                    files[archive_name] = path
                    config[key] = PACKAGE_PREFIX + archive_name
                else:
                    config[key] = ENV_PREFIX + env_name
                    variables.append({"name": env_name, "nodeId": node["id"], "field": key, "required": True, "sha256": digest})
    _, dependency_versions = _requirements(root, graph)
    manifest = {
        "schemaVersion": 1, "name": package_name, "version": version,
        "pythonVersion": sys.version.split()[0], "dependencyVersions": dependency_versions,
        "workflowSha256": hashlib.sha256(json.dumps(graph, sort_keys=True, allow_nan=False).encode()).hexdigest(),
        "models": model_records, "environment": variables, "warnings": warnings,
    }
    _check_remaining_secrets(graph)
    return graph, manifest, files


def build_zip(graph: dict, manifest: dict, files: dict[str, Path], root: Path, destination: Path) -> None:
    install_bat = (
        "@echo off\r\n"
        "setlocal enabledelayedexpansion\r\n\r\n"
        "echo ======================================================================\r\n"
        "echo   Afi Vision Standalone Runtime Installer\r\n"
        "echo ======================================================================\r\n"
        "echo.\r\n\r\n"
        "where python >nul 2>&1\r\n"
        "if %errorlevel% neq 0 (\r\n"
        "    echo [ERROR] Python tidak terdeteksi di PATH sistem Anda!\r\n"
        "    echo Silakan install Python 3.10, 3.11, atau 3.12 dari https://www.python.org/\r\n"
        "    echo PENTING: Centang opsi \"Add Python to PATH\" saat proses instalasi.\r\n"
        "    echo.\r\n"
        "    pause\r\n"
        "    exit /b 1\r\n"
        ")\r\n\r\n"
        "for /f \"tokens=*\" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i\r\n"
        "echo Menemukan Python: %PYTHON_VER%\r\n"
        "echo.\r\n\r\n"
        "if not exist \".venv\\Scripts\\python.exe\" (\r\n"
        "    echo [1/4] Membuat Virtual Environment lokal (.venv)...\r\n"
        "    python -m venv .venv\r\n"
        "    if %errorlevel% neq 0 (\r\n"
        "        echo [ERROR] Gagal membuat virtual environment.\r\n"
        "        pause\r\n"
        "        exit /b 1\r\n"
        "    )\r\n"
        "    echo Virtual environment (.venv) berhasil dibuat.\r\n"
        ") else (\r\n"
        "    echo [1/4] Virtual Environment (.venv) sudah tersedia.\r\n"
        ")\r\n\r\n"
        "echo.\r\n"
        "echo [2/4] Memperbarui pip...\r\n"
        ".venv\\Scripts\\python.exe -m pip install --upgrade pip --quiet\r\n\r\n"
        "echo.\r\n"
        "echo [3/4] Menginstall seluruh dependensi yang dibutuhkan (requirements.txt)...\r\n"
        "echo Mohon tunggu sebentar (membutuhkan koneksi internet untuk unduhan pertama)...\r\n"
        ".venv\\Scripts\\python.exe -m pip install -r requirements.txt\r\n"
        "if %errorlevel% neq 0 (\r\n"
        "    echo.\r\n"
        "    echo [ERROR] Gagal menginstall dependensi via pip.\r\n"
        "    echo Silakan periksa koneksi internet atau pesan error di atas.\r\n"
        "    pause\r\n"
        "    exit /b 1\r\n"
        ")\r\n\r\n"
        "echo.\r\n"
        "echo [4/4] Mempersiapkan konfigurasi (.env)...\r\n"
        "if not exist \".env\" (\r\n"
        "    if exist \".env.example\" (\r\n"
        "        copy .env.example .env >nul\r\n"
        "        echo Berkas .env berhasil disiapkan dari .env.example.\r\n"
        "    )\r\n"
        ") else (\r\n"
        "    echo Berkas .env sudah siap.\r\n"
        ")\r\n\r\n"
        "echo.\r\n"
        "echo ======================================================================\r\n"
        "echo   INSTALASI BERHASIL! Seluruh model & modul siap (\"Tinggal Pakai\").\r\n"
        "echo ======================================================================\r\n"
        "echo.\r\n"
        "echo Anda dapat langsung menjalankan:\r\n"
        "echo   - Double click 'run_web.bat'    (Web App Streamlit + Live Preview)\r\n"
        "echo   - Double click 'run_opencv.bat' (Desktop OpenCV Preview Window)\r\n"
        "echo.\r\n"
        "pause\r\n"
    )

    install_sh = (
        "#!/usr/bin/env bash\n"
        "set -e\n"
        "echo '======================================================================'\n"
        "echo '  Afi Vision Standalone Runtime Installer'\n"
        "echo '======================================================================'\n"
        "if ! command -v python3 &> /dev/null; then\n"
        "    echo '[ERROR] python3 could not be found. Please install Python 3.10+.'\n"
        "    exit 1\n"
        "fi\n"
        "if [ ! -f '.venv/bin/python' ]; then\n"
        "    echo '[1/4] Creating virtual environment (.venv)...'\n"
        "    python3 -m venv .venv\n"
        "fi\n"
        "echo '[2/4] Upgrading pip...'\n"
        ".venv/bin/python -m pip install --upgrade pip --quiet\n"
        "echo '[3/4] Installing dependencies from requirements.txt...'\n"
        ".venv/bin/python -m pip install -r requirements.txt\n"
        "echo '[4/4] Setting up .env...'\n"
        "if [ ! -f '.env' ] && [ -f '.env.example' ]; then\n"
        "    cp .env.example .env\n"
        "fi\n"
        "echo '======================================================================'\n"
        "echo '  Installation Complete! Ready to use.'\n"
        "echo '  Run web app: .venv/bin/streamlit run app.py'\n"
        "echo '  Run OpenCV:  .venv/bin/python run.py'\n"
        "echo '======================================================================'\n"
    )

    run_web_bat = (
        "@echo off\r\n"
        "setlocal\r\n"
        "if not exist \".venv\\Scripts\\python.exe\" (\r\n"
        "    echo [INFO] Virtual environment (.venv) belum terpasang.\r\n"
        "    echo Menjalankan instalasi otomatis terlebih dahulu (install.bat)...\r\n"
        "    echo.\r\n"
        "    call install.bat\r\n"
        "    if not exist \".venv\\Scripts\\python.exe\" (\r\n"
        "        echo [ERROR] Instalasi dependensi gagal atau dibatalkan.\r\n"
        "        pause\r\n"
        "        exit /b 1\r\n"
        "    )\r\n"
        ")\r\n"
        "echo Memulai Afi Vision Web App (Streamlit)...\r\n"
        ".venv\\Scripts\\python.exe -m streamlit run app.py\r\n"
        "pause\r\n"
    )

    run_opencv_bat = (
        "@echo off\r\n"
        "setlocal\r\n"
        "if not exist \".venv\\Scripts\\python.exe\" (\r\n"
        "    echo [INFO] Virtual environment (.venv) belum terpasang.\r\n"
        "    echo Menjalankan instalasi otomatis terlebih dahulu (install.bat)...\r\n"
        "    echo.\r\n"
        "    call install.bat\r\n"
        "    if not exist \".venv\\Scripts\\python.exe\" (\r\n"
        "        echo [ERROR] Instalasi dependensi gagal atau dibatalkan.\r\n"
        "        pause\r\n"
        "        exit /b 1\r\n"
        "    )\r\n"
        ")\r\n"
        "echo Memulai Afi Vision Desktop OpenCV Preview...\r\n"
        ".venv\\Scripts\\python.exe run.py\r\n"
        "pause\r\n"
    )

    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("workflow.json", json.dumps(graph, indent=2, ensure_ascii=False))
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        archive.write(root / "engine" / "standalone_run.py", "run.py")
        if (root / "engine" / "standalone_app.py").is_file():
            archive.write(root / "engine" / "standalone_app.py", "app.py")
        archive.writestr("requirements.txt", _requirements(root, graph)[0])
        archive.writestr(".env.example", "# Salin menjadi .env; isi nilai pada mesin tujuan. Jangan bagikan .env.\n" + "".join(f"# {item['nodeId']}.{item['field']}\n{item['name']}=\n" for item in manifest["environment"]))
        archive.writestr("install.bat", install_bat)
        archive.writestr("install.sh", install_sh)
        archive.writestr("run_web.bat", run_web_bat)
        archive.writestr("run_opencv.bat", run_opencv_bat)
        archive.writestr("README.md", f"""# {manifest['name']} {manifest['version']} — Siap Pakai ("Tinggal Pakai")

Paket mandiri ini telah menyertakan seluruh bobot model AI, konfigurasi graph, runner desktop, dan web app dashboard.

## 🚀 Cara Menjalankan Instan (1-Klik)

### Langkah 1: Instalasi Dependensi
Cukup double-click berkas **`install.bat`** (Windows) atau jalankan `bash install.sh` (Linux/macOS).
Script ini otomatis membuat environment `.venv` lokal dan menginstall paket yang dibutuhkan.
*(Tips: Jika Anda langsung menjalankan `run_web.bat`, script akan otomatis mendeteksi dan menjalankan instalasi terlebih dahulu!)*

### Langkah 2: Jalankan Workflow

#### 🌐 Opsi 1: Web App Streamlit (Rekomendasi)
Cukup double-click **`run_web.bat`** (atau jalankan `.venv\\Scripts\\python.exe -m streamlit run app.py`).
Browser akan terbuka otomatis menampilkan:
- Live streaming video preview teranotasi.
- Kontrol Start / Stop workflow.
- Penggantian input sumber kamera / video langsung di browser.
- Indikator real-time FPS dan jumlah objek terdeteksi.

#### 🖥️ Opsi 2: Desktop OpenCV Preview
Cukup double-click **`run_opencv.bat`** (atau jalankan `.venv\\Scripts\\python.exe run.py`).
Jendela preview desktop OpenCV HighGUI akan langsung muncul di monitor. Tekan **`q`** atau **`ESC`** untuk keluar.

## 🧠 Model AI & Aset
Semua model AI yang dibutuhkan workflow ini sudah langsung disertakan di dalam folder `models/` dengan verifikasi integritas SHA256. Tidak perlu mengunduh model manual!
""")
        needed_engine_files = _determine_needed_engine_files(graph)
        for filename in sorted(needed_engine_files):
            file_path = root / "engine" / filename
            if file_path.is_file():
                archive.write(file_path, f"engine/{filename}")
        for path in sorted((root / "engine").glob("*.json")):
            archive.write(path, f"engine/{path.name}")
        for name, path in files.items():
            archive.write(path, name)
