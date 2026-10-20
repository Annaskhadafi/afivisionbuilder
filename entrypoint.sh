#!/usr/bin/env bash
set -e

DATA_DIR="${VISONODE_APP_DATA_DIR:-/app/data}"

echo "=========================================================="
echo "      AFI VISION BUILDER - DOKPLOY CONTAINER STARTUP      "
echo "=========================================================="
echo "Data Directory: $DATA_DIR"

# 1. Pastikan seluruh subfolder penting di dalam mount persisten sudah terbentuk
mkdir -p "$DATA_DIR/models"
mkdir -p "$DATA_DIR/uploads"
mkdir -p "$DATA_DIR/outputs"
mkdir -p "$DATA_DIR/projects"
mkdir -p "$DATA_DIR/faces"
mkdir -p /app/weights

# 2. Jika volume data baru di-mount dan folder models masih kosong,
# salin model bawaan (default models) dari initial image agar siap pakai
if [ -d "/app/initial_models" ] && [ -z "$(ls -A "$DATA_DIR/models" 2>/dev/null)" ]; then
    echo "[Dokploy Init] Mengisi model awal bawaan ke persistent mount ($DATA_DIR/models)..."
    cp -rn /app/initial_models/* "$DATA_DIR/models/" 2>/dev/null || true
fi

# 3. Jika cameras.json belum ada di volume persisten, salin dari template bawaan jika ada
if [ ! -f "$DATA_DIR/cameras.json" ] && [ -f "/app/default_cameras.json" ]; then
    echo "[Dokploy Init] Menyalin default cameras.json ke persistent mount..."
    cp /app/default_cameras.json "$DATA_DIR/cameras.json" 2>/dev/null || true
fi

# 4. Jika projects.json belum ada di volume persisten, salin dari template bawaan jika ada
if [ ! -f "$DATA_DIR/projects.json" ] && [ -f "/app/default_projects.json" ]; then
    echo "[Dokploy Init] Menyalin default projects.json ke persistent mount..."
    cp /app/default_projects.json "$DATA_DIR/projects.json" 2>/dev/null || true
fi

# 5. Jalankan server aplikasi
echo "[Dokploy Init] Menjalankan server pada ${VISONODE_WEB_HOST:-0.0.0.0}:${VISONODE_WEB_PORT:-8765}..."
exec python server.py
