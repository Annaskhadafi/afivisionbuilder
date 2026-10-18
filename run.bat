@echo off
setlocal
cd /d "%~dp0"
title AFI Vision Builder

echo ========================================================
echo               AFI VISION BUILDER
echo ========================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
    echo Menggunakan Virtual Environment [.venv]...
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python maupun virtual environment .venv tidak ditemukan!
        echo Silakan jalankan install.bat terlebih dahulu untuk instalasi.
        echo.
        pause
        exit /b 1
    )
    set "PY_CMD=python"
    echo Virtual Environment [.venv] tidak ditemukan, menggunakan python sistem...
)

echo Membuka browser ke http://127.0.0.1:8765 ...
start "" "http://127.0.0.1:8765"

echo Menjalankan server AFI Vision Builder...
echo (Tekan Ctrl+C di jendela ini untuk menghentikan server)
echo.

%PY_CMD% server.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Server berhenti dengan status error (Exit code: %ERRORLEVEL%).
    pause
)
