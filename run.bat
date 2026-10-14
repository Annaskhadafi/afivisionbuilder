@echo off
setlocal
title AFI Vision Builder - Web Application

cd /d "%~dp0"

echo ========================================================
echo              MEMULAI AFI VISION BUILDER...
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Virtual environment (.venv) belum terpasang.
    echo Menjalankan instalasi otomatis terlebih dahulu...
    echo.
    call install.bat
)

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Gagal menemukan .venv\Scripts\python.exe setelah instalasi.
    pause
    exit /b 1
)

echo Mengaktifkan Virtual Environment (.venv)...
call .venv\Scripts\activate.bat

echo Membuka antarmuka web di browser (http://127.0.0.1:8765)...
start http://127.0.0.1:8765

echo.
echo ========================================================
echo   Server AFI Vision Builder sedang berjalan!
echo   Alamat: http://127.0.0.1:8765
echo.
echo   Tekan CTRL + C di jendela ini untuk menghentikan server.
echo ========================================================
echo.

python server.py

pause
