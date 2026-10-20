@echo off
setlocal enabledelayedexpansion
title AFI Vision Builder - Setup & Installation

echo ========================================================
echo         AFI VISION BUILDER - SETUP & INSTALLASI
echo ========================================================
echo.

cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python tidak ditemukan di PATH sistem Anda!
    echo Silakan unduh dan install Python 3.10 / 3.11 / 3.12 dari:
    echo   https://www.python.org/downloads/
    echo Pastikan mencentang opsi "Add Python to PATH" saat instalasi.
    echo.
    echo Tekan tombol apapun untuk menutup jendela ini...
    pause
    exit /b 1
)

echo [1/5] Memeriksa versi Python...
python --version

echo.
echo [2/5] Menyiapkan Virtual Environment (.venv)...
if not exist ".venv" (
    echo Membuat virtual environment baru di folder .venv...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo.
        echo [ERROR] Gagal membuat virtual environment!
        echo Pastikan Anda memiliki izin akses di folder ini.
        echo Tekan tombol apapun untuk menutup jendela ini...
        pause
        exit /b 1
    )
    echo Virtual environment berhasil dibuat.
) else (
    echo Virtual environment (.venv) sudah tersedia.
)

echo.
echo [3/5] Mengaktifkan .venv dan mengupdate pip...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo.
echo [4/5] Menginstall paket dependensi dari requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] Beberapa paket mungkin membutuhkan kompilasi C++ Build Tools.
    echo Jika ada error OpenCV atau PyTorch, pastikan koneksi internet stabil.
)

echo.
echo [5/5] Memeriksa ketersediaan bobot model AI bawaan...
if exist "scripts\download_models.py" (
    python scripts\download_models.py
)

echo.
echo ========================================================
echo   INSTALASI SELESAI!
echo.
echo   Untuk menjalankan AFI Vision Builder, silakan buka:
echo   - run.bat (untuk membuka server web di browser)
echo ========================================================
echo.
echo Tekan tombol apapun untuk menutup jendela instalasi ini...
pause
