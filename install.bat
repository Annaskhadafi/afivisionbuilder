@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
title AFI Vision Builder - Setup and Installation

echo ========================================================
echo         AFI VISION BUILDER - SETUP DAN INSTALASI
echo ========================================================
echo.
echo Lokasi folder instalasi: "%CD%"
echo.

echo [1/5] Memeriksa versi Python...
set "SYS_PYTHON="
python --version >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "SYS_PYTHON=python"
    goto :FOUND_PYTHON
)

py --version >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "SYS_PYTHON=py"
    goto :FOUND_PYTHON
)

where python >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "SYS_PYTHON=python"
    goto :FOUND_PYTHON
)

echo.
echo ========================================================
echo [ERROR] Python tidak ditemukan di PATH sistem Anda!
echo Silakan unduh dan install Python 3.10 / 3.11 / 3.12 dari:
echo   https://www.python.org/downloads/
echo Pastikan mencentang opsi "Add Python to PATH" saat instalasi.
echo ========================================================
echo.
pause
exit /b 1

:FOUND_PYTHON
call %SYS_PYTHON% --version

echo.
echo [2/5] Menyiapkan Virtual Environment (.venv)...

if not exist ".venv" goto :CREATE_VENV

rem Cek apakah .venv yang sudah ada masih valid
call ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
if !ERRORLEVEL! equ 0 (
    echo Virtual environment .venv sudah tersedia dan cocok dengan folder ini.
    goto :VENV_READY
)

echo [INFO] Folder .venv lama tidak cocok dengan lokasi folder saat ini.
echo Menghapus .venv lama untuk dibuat ulang di lokasi folder baru...
rmdir /s /q ".venv"

:CREATE_VENV
echo Membuat virtual environment baru di folder .venv...
call %SYS_PYTHON% -m venv .venv
if !ERRORLEVEL! neq 0 (
    echo.
    echo ========================================================
    echo [ERROR] Gagal membuat virtual environment!
    echo Pastikan Anda memiliki izin akses tulis di folder ini.
    echo ========================================================
    echo.
    pause
    exit /b 1
)
echo Virtual environment berhasil dibuat.

:VENV_READY
echo.
echo [3/5] Mengaktifkan .venv dan mengupdate pip...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
call python -m pip install --upgrade pip

echo.
echo [4/5] Menginstall paket dependensi dari requirements.txt...
call python -m pip install --prefer-binary -r requirements.txt
if !ERRORLEVEL! neq 0 (
    echo.
    echo [WARNING] Mencoba opsi fallback kompatibilitas...
    call python -m pip install --prefer-binary --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
)

echo.
echo [5/5] Memeriksa ketersediaan bobot model AI bawaan...
if exist "scripts\download_models.py" (
    call python scripts\download_models.py
)

echo.
echo ========================================================
echo   INSTALASI SELESAI DENGAN SUKSES!
echo.
echo   Untuk menjalankan AFI Vision Builder, silakan buka:
echo   - run.bat (untuk membuka server web di browser)
echo ========================================================
echo.
pause
