from __future__ import annotations

import io
import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("afi.dashboard_export")

DOCKER_COMPOSE_TEMPLATE = """version: "3.8"

services:
  afivision-dashboard:
    build: .
    container_name: afivision-standalone
    restart: unless-stopped
    ports:
      - "8765:8765"
    environment:
      - VISONODE_WEB_HOST=0.0.0.0
      - VISONODE_WEB_PORT=8765
      - VISONODE_APP_DATA_DIR=/app/data
    volumes:
      - ./data:/app/data
    deploy:
      resources:
        limits:
          cpus: "4.0"
          memory: 4096M
"""

DOCKERFILE_TEMPLATE = """FROM python:3.10-slim
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \\
    ffmpeg libgl1 libglib2.0-0 curl \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8765

CMD ["python", "server.py"]
"""

STANDALONE_RUN_BAT = """@echo off
title Afivision Standalone Web Dashboard
echo ========================================================
echo  AFIVISION STANDALONE WEB DASHBOARD
echo ========================================================
echo Memeriksa lingkungan Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python tidak ditemukan di PATH sistem.
    echo Pasang Python 3.10 atau gunakan Docker Compose ^(docker compose up -d^).
    pause
    exit /b 1
)

if not exist .venv (
    echo Menyiapkan virtual environment...
    python -m venv .venv
    call .venv\\Scripts\\activate.bat
    echo Menginstal pustaka dependensi...
    pip install -r requirements.txt
) else (
    call .venv\\Scripts\\activate.bat
)

echo Membuka peramban di http://localhost:8765...
start http://localhost:8765
python server.py
pause
"""

STANDALONE_RUN_SH = """#!/usr/bin/env bash
set -e
echo "========================================================"
echo " AFIVISION STANDALONE WEB DASHBOARD"
echo "========================================================"
if [ ! -d ".venv" ]; then
    echo "Menyiapkan virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "Membuka peramban di http://localhost:8765..."
python server.py
"""

STANDALONE_REQUIREMENTS = """fastapi>=0.100.0
uvicorn>=0.22.0
python-dotenv>=1.0.0
numpy>=1.24.0
opencv-python-headless>=4.8.0
openpyxl>=3.1.0
pandas>=2.0.0
requests>=2.31.0
"""


def create_standalone_dashboard_package(
    project_id: str,
    layout_data: Optional[dict[str, Any]] = None,
    root_dir: Optional[str | Path] = None,
) -> bytes:
    """
    Generate a self-contained ZIP package containing Docker Compose,
    Dockerfile, launchers, standalone server, engine, and frontend assets.
    """
    if root_dir is None:
        root_dir = Path(__file__).resolve().parent.parent
    else:
        root_dir = Path(root_dir).resolve()

    try:
        from engine.dashboard_bus import DashboardDataBus
    except ImportError:
        from dashboard_bus import DashboardDataBus
    bus = DashboardDataBus.get_instance(root_dir / "data")

    if layout_data is None:
        layout_data = bus.load_layout(project_id)

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Orchestration & Launchers
        zf.writestr("docker-compose.yml", DOCKER_COMPOSE_TEMPLATE)
        zf.writestr("Dockerfile", DOCKERFILE_TEMPLATE)
        zf.writestr("run.bat", STANDALONE_RUN_BAT)
        zf.writestr("run.sh", STANDALONE_RUN_SH)
        zf.writestr("requirements.txt", STANDALONE_REQUIREMENTS)

        # 2. README & Documentation
        readme_content = f"""# Afivision Standalone Web Dashboard & CV Pipeline

Paket ini adalah bundel mandiri yang dihasilkan dari **Afivision Dashboard Builder**.
Dapat dijalankan langsung di server mana pun tanpa membutuhkan instalasi studio Afivision.

## Cara Menjalankan

### Opsi 1: Menggunakan Docker Compose (Direkomendasikan untuk Server/Produksi)
```bash
docker compose up -d
```
Buka browser di: `http://localhost:8765`

### Opsi 2: Menggunakan Windows Script
Klik dua kali file `run.bat`.

### Opsi 3: Menggunakan Linux / macOS Script
```bash
chmod +x run.sh
./run.sh
```

## Struktur Berkas
- `docker-compose.yml`: Konfigurasi multi-container
- `data/dashboards/`: Berkas tata letak `{project_id}.json`
- `static/`: Antarmuka dashboard web
"""
        zf.writestr("README.md", readme_content)

        # 3. Server script
        server_path = root_dir / "server.py"
        if server_path.exists():
            zf.write(str(server_path), "server.py")

        # 4. Engine modules
        engine_dir = root_dir / "engine"
        engine_files = [
            "dashboard_bus.py",
            "dashboard_ai_generator.py",
            "ai_studio_assistant.py",
            "core.py",
            "node_catalog.py",
            "visonode_database.py",
            "app_version.py",
            "python_script_runtime.py",
            "cloud_sinks.py",
            "telegram_sink.py",
            "data_aggregation.py",
            "workflow_store.py",
        ]
        for ef in engine_files:
            p = engine_dir / ef
            if p.exists():
                zf.write(str(p), f"engine/{ef}")

        # 5. Static Web Frontend Assets
        static_dir = root_dir / "static"
        static_files = [
            "index.html",
            "style.css",
            "app.js",
            "dashboard_builder.js",
            "logo.png",
            "logo.ico",
        ]
        for sf in static_files:
            p = static_dir / sf
            if p.exists():
                zf.write(str(p), f"static/{sf}")

        # 5b. Uploaded Logos & Media Assets (data/uploads)
        data_uploads_dir = root_dir / "data" / "uploads"
        if data_uploads_dir.exists() and data_uploads_dir.is_dir():
            for uf in data_uploads_dir.iterdir():
                if uf.is_file():
                    zf.write(str(uf), f"data/uploads/{uf.name}")

        public_uploads_dir = root_dir / "public" / "uploads"
        if public_uploads_dir.exists() and public_uploads_dir.is_dir():
            for uf in public_uploads_dir.iterdir():
                if uf.is_file():
                    zf.write(str(uf), f"public/uploads/{uf.name}")

        # 6. Saved Dashboard Layout JSON
        layout_json_str = json.dumps(layout_data, indent=2, ensure_ascii=False)
        clean_id = "".join(c for c in project_id if c.isalnum() or c in ("-", "_")).strip() or "default"
        zf.writestr(f"data/dashboards/{clean_id}.json", layout_json_str)
        if clean_id != "default":
            zf.writestr("data/dashboards/default.json", layout_json_str)

    zip_bytes = zip_buffer.getvalue()
    logger.info(f"Paket ekspor standalone berhasil dibuat: {len(zip_bytes)} bytes")
    return zip_bytes
