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
        echo Tekan tombol apapun untuk menutup jendela ini...
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

echo.
echo ========================================================
if %ERRORLEVEL% neq 0 (
    echo [INFO] Server berhenti (Status Code: %ERRORLEVEL%).
) else (
    echo [INFO] Server AFI Vision Builder telah dihentikan.
)
echo ========================================================
echo Jendela ini tidak akan tertutup otomatis agar Anda dapat membaca log di atas.
echo Silakan tutup jendela ini secara manual atau tekan tombol apapun...
echo.
pause
