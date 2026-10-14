"""
Afi Vision Builder - Desktop Application Launcher
Membuka aplikasi Afi Vision Builder dalam jendela native desktop (WebView2) atau default browser.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Pastikan working directory mengarah ke folder webapp
ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

import uvicorn
from server import app

HOST = "127.0.0.1"
PORT = int(os.getenv("VISONODE_WEB_PORT", "8765"))
URL = f"http://{HOST}:{PORT}"


def start_server():
    """Jalankan server backend FastAPI di thread terpisah."""
    config = uvicorn.Config(app=app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def wait_for_server(timeout=10):
    import urllib.request
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(f"{URL}/api/catalog", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    # Jalankan FastAPI di background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Tunggu hingga server siap
    ready = wait_for_server(15)
    if not ready:
        print("[ERROR] Server Afi Vision Builder gagal dimulai dalam batas waktu.")
        sys.exit(1)

    print(f"[OK] Afi Vision Builder berjalan di {URL}")

    # Cek apakah pywebview tersedia untuk native desktop window
    try:
        import webview
        print("[INFO] Membuka jendela Desktop Native (WebView2)...")
        window = webview.create_window(
            title="Afi Vision Builder",
            url=URL,
            width=1380,
            height=860,
            min_size=(1024, 700),
            resizable=True
        )
        webview.start()
    except ImportError:
        print("[INFO] pywebview belum terpasang. Membuka di browser default...")
        webbrowser.open(URL)
        print("[INFO] Tekan Ctrl+C di terminal ini untuk keluar.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Menutup Afi Vision Builder...")


if __name__ == "__main__":
    main()
