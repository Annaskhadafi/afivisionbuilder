#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -f ".venv/bin/python" ]; then
    echo "Virtual environment belum ada. Menjalankan install.sh..."
    bash install.sh
fi

source .venv/bin/activate

echo "Membuka browser ke http://127.0.0.1:8765 ..."
if command -v xdg-open &> /dev/null; then
    xdg-open "http://127.0.0.1:8765" &
elif command -v open &> /dev/null; then
    open "http://127.0.0.1:8765" &
fi

echo "Menjalankan server AFI Vision Builder..."
exec .venv/bin/python server.py
