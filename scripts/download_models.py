"""
AFI Vision Builder - Model Verification & Downloader Script
Memverifikasi dan mengunduh model-model umum ke dalam data/models/
jika file belum ada atau hanya berupa Git LFS pointer (<1KB).
"""
from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = Path(os.environ.get("VISONODE_APP_DATA_DIR", str(ROOT / "data"))) / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Model umum Ultralytics standar yang siap diunduh jika belum ada di data/models/
ESSENTIAL_MODELS = {
    "yolov8n.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt",
    "yolov8s.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s.pt",
    "yolov8n-seg.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n-seg.pt",
    "yolov8n-pose.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n-pose.pt",
    "yolov8n-cls.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n-cls.pt",
    "yolo11n.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt",
}


def is_valid_model_file(path: Path) -> bool:
    """Cek apakah file ada dan bukan file kosong atau LFS pointer."""
    if not path.is_file():
        return False
    # File model .pt asli pasti berukuran minimal > 1 MB. Pointer LFS hanya ~130 bytes.
    return path.stat().st_size > 1024 * 1024


def download_progress_hook(block_num: int, block_size: int, total_size: int) -> None:
    if total_size <= 0:
        return
    downloaded = block_num * block_size
    percent = min(100.0, downloaded * 100.0 / total_size)
    mb_down = downloaded / (1024 * 1024)
    mb_total = total_size / (1024 * 1024)
    sys.stdout.write(f"\r    -> Mengunduh: {percent:5.1f}% ({mb_down:.1f} MB / {mb_total:.1f} MB)")
    sys.stdout.flush()


def verify_or_download_models(auto_download: bool = True) -> dict[str, bool]:
    """Cek keberadaan model umum di data/models/."""
    status = {}
    print("=" * 60)
    print(" Memeriksa Ketersediaan Bobot Model AI (data/models/)...")
    print("=" * 60)

    for filename, url in ESSENTIAL_MODELS.items():
        target = MODELS_DIR / filename
        if is_valid_model_file(target):
            size_mb = target.stat().st_size / (1024 * 1024)
            print(f" [OK] {filename} ({size_mb:.1f} MB) - Tersedia.")
            status[filename] = True
        else:
            status[filename] = False
            if auto_download:
                print(f" [MISSING] {filename} belum tersedia. Mengunduh dari sumber resmi...")
                try:
                    urllib.request.urlretrieve(url, str(target), reporthook=download_progress_hook)
                    print(f"\n    [OK] Berhasil mengunduh {filename}!")
                    status[filename] = True
                except Exception as exc:
                    print(f"\n    [ERROR] Gagal mengunduh {filename}: {exc}")
                    if target.is_file() and target.stat().st_size < 1024:
                        target.unlink(missing_ok=True)
            else:
                print(f" [MISSING] {filename} belum tersedia di {target}.")

    print("=" * 60)
    ready_count = sum(1 for v in status.values() if v)
    total_count = len(status)
    print(f" Ringkasan: {ready_count}/{total_count} model umum siap digunakan.")
    print("=" * 60)
    return status


if __name__ == "__main__":
    verify_or_download_models(auto_download=True)
