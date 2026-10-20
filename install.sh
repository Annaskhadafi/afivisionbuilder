#!/usr/bin/env bash
set -e

# Tangani error agar script tidak mati tiba-tiba tanpa penjelasan
trap 'error_handler $? $LINENO' ERR

error_handler() {
    local exit_code=$1
    local line_no=$2
    echo ""
    echo "========================================================"
    echo " [ERROR] Instalasi terhenti di baris $line_no (Exit code: $exit_code)"
    echo "========================================================"
    echo "Kemungkinan penyebab masalah:"
    echo "1. Memori (RAM) tidak mencukupi saat install dependensi (OOM Killer)."
    echo "   -> Solusi: Tambahkan swap RAM minimal 2-4 GB:"
    echo "      sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile"
    echo "      sudo mkswap /swapfile && sudo swapon /swapfile"
    echo "2. Paket sistem OS belum lengkap."
    echo "   -> Solusi: Jalankan perintah berikut lalu coba lagi:"
    echo "      sudo apt update && sudo apt install -y python3-venv python3-pip python3-dev build-essential git ffmpeg libgl1 libglib2.0-0"
    echo "========================================================"
    exit $exit_code
}

cd "$(dirname "$0")"

echo "========================================================"
echo "         AFI VISION BUILDER - SETUP & INSTALLASI        "
echo "========================================================"
echo ""

# 1. Periksa Python 3
echo "[1/5] Memeriksa instalasi Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 tidak ditemukan di sistem Anda!"
    echo "Silakan install Python 3 terlebih dahulu:"
    echo "  sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    exit 1
fi
python3 --version

# 2. Periksa modul python3-venv
echo ""
echo "[2/5] Memeriksa modul virtual environment..."
if ! python3 -c "import venv" &> /dev/null; then
    echo "[ERROR] Modul 'venv' Python belum terpasang di sistem!"
    echo "Di Debian/Ubuntu, venv perlu diinstall terpisah. Silakan jalankan:"
    echo "  sudo apt update && sudo apt install -y python3-venv python3-pip"
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Membuat virtual environment baru di folder .venv..."
    python3 -m venv .venv
else
    echo "Virtual environment (.venv) sudah tersedia."
fi

# 3. Aktifkan venv & periksa Git
echo ""
echo "[3/5] Mengaktifkan virtual environment..."
source .venv/bin/activate

if ! command -v git &> /dev/null; then
    echo "[PERINGATAN] 'git' tidak terdeteksi di PATH."
    echo "Dependensi seperti CLIP membutuhkan git. Jika gagal, jalankan: sudo apt install -y git"
fi

python -m pip install --upgrade pip

# 4. Install dependensi
echo ""
echo "[4/5] Menginstall dependensi dari requirements.txt..."
pip install -r requirements.txt

# 5. Verifikasi dan unduh model-model umum jika belum ada
echo ""
echo "[5/5] Memeriksa ketersediaan bobot model AI bawaan..."
if [ -f "scripts/download_models.py" ]; then
    python scripts/download_models.py
fi

echo ""
echo "========================================================"
echo "  INSTALASI SELESAI DENGAN SUKSES!"
echo "  Jalankan aplikasi dengan: ./run.sh"
echo "========================================================"
