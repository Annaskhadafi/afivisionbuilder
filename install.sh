#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "========================================================"
echo "         AFI VISION BUILDER - SETUP & INSTALLASI        "
echo "========================================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 tidak ditemukan!"
    exit 1
fi

python3 --version

if [ ! -d ".venv" ]; then
    echo "Membuat virtual environment (.venv)..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "========================================================"
echo "  INSTALASI SELESAI!"
echo "  Jalankan aplikasi dengan: ./run.sh"
echo "========================================================"
