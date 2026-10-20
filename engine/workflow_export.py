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


def _requirements(root: Path, graph: dict) -> tuple[str, dict[str, str]]:
    lines = []
    versions = {}
    for raw in (root / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("pytest"):
            continue
        name = re.match(r"[A-Za-z0-9_.-]+", line).group()
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise ValueError(f"Runtime dependency is not installed: {name}") from exc
        versions[name] = version
        lines.append(line if " @ " in line else f"{name}=={version}")
    if any((node.get("config", {}).get("engine") or ("rfdetr" if node.get("type") in {"detector", "segmenter"} else "")) == "rfdetr" for node in graph["nodes"]):
        try:
            version = importlib.metadata.version("rfdetr")
        except importlib.metadata.PackageNotFoundError as exc:
            raise ValueError("RF-DETR runtime is not installed on the build server") from exc
        versions["rfdetr"] = version
        lines.append(f"rfdetr=={version}")
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
    include_models = options.get("includeModels", False)
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
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("workflow.json", json.dumps(graph, indent=2, ensure_ascii=False))
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        archive.write(root / "engine" / "standalone_run.py", "run.py")
        archive.writestr("requirements.txt", _requirements(root, graph)[0])
        archive.writestr(".env.example", "# Salin menjadi .env; isi nilai pada mesin tujuan. Jangan bagikan .env.\n" + "".join(f"# {item['nodeId']}.{item['field']}\n{item['name']}=\n" for item in manifest["environment"]))
        archive.writestr("README.md", f"""# {manifest['name']} {manifest['version']}

Paket ini menjalankan satu snapshot workflow Afi Vision secara terpisah dari Studio.
Gunakan Python {manifest['pythonVersion']} dan simpan seluruh isi folder hasil ekstraksi.

## Instalasi Windows

```powershell
python -m venv .venv
.venv\\Scripts\\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Isi variabel dalam .env, lalu:
.venv\\Scripts\\python.exe run.py --check
.venv\\Scripts\\python.exe run.py
```

Pada Linux, ganti `.venv\\Scripts\\python.exe` dengan `.venv/bin/python`.
Gunakan `python run.py --seconds 10` untuk uji singkat. Ctrl+C menghentikan proses.
Hasil lokal disimpan dalam folder `data/`. Model yang tidak disertakan harus
disediakan pada path di `.env` dengan checksum yang cocok dengan `manifest.json`.
Alamat kamera dan layanan eksternal harus dapat dijangkau dari mesin tujuan.
Jangan memasukkan kredensial ke `workflow.json` atau membagikan `.env`.
""")
        for path in sorted((root / "engine").glob("*.py")):
            if path.name not in {"workflow_export.py", "standalone_run.py", "server.py"}:
                archive.write(path, f"engine/{path.name}")
        for path in sorted((root / "engine").glob("*.json")):
            archive.write(path, f"engine/{path.name}")
        for name, path in files.items():
            archive.write(path, name)
