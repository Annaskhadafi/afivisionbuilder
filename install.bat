@echo off
setlocal enabledelayedexpansion

:: Mencegah jendela CMD menutup otomatis jika dibuka lewat double-click di File Explorer
if "%~1"=="__KEEP_OPEN__" goto :MAIN
if not defined INSIDE_INSTALL_WRAPPER (
    set INSIDE_INSTALL_WRAPPER=1
    cmd /k ""%~f0" __KEEP_OPEN__ %*"
    exit /b
)

:MAIN
cd /d "%~dp0"
title AFI Vision Builder - Setup & Installation

echo ========================================================
echo         AFI VISION BUILDER - SETUP & INSTALLASI
echo ========================================================
echo.
echo Lokasi folder instalasi: "%CD%"
echo.

echo [1/5] Memeriksa versi Python...
set "SYS_PYTHON="
python --version >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "SYS_PYTHON=python"
) else (
    where python >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        set "SYS_PYTHON=python"
    ) else (
        echo.
        echo ========================================================
        echo [ERROR] Python tidak ditemukan di PATH sistem Anda!
        echo Silakan unduh dan install Python 3.10 / 3.11 / 3.12 dari:
        echo   https://www.python.org/downloads/
        echo Pastikan mencentang opsi "Add Python to PATH" saat instalasi.
        echo ========================================================
        echo.
        echo Tekan tombol apapun untuk keluar...
        pause
        exit /b 1
    )
)
call %SYS_PYTHON% --version

echo.
echo [2/5] Menyiapkan Virtual Environment (.venv)...
set "NEED_NEW_VENV=0"
if not exist ".venv" (
    set "NEED_NEW_VENV=1"
) else (
    :: Periksa apakah .venv yang ada masih valid atau dari folder lain yang dipindahkan
    call ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
    if !ERRORLEVEL! neq 0 (
        echo [INFO] Folder .venv lama terdeteksi tidak valid (kemungkinan dipindahkan dari path lain).
        echo Menghapus .venv lama untuk dibuat ulang di lokasi folder baru...
        rmdir /s /q ".venv"
        set "NEED_NEW_VENV=1"
    ) else (
        echo Virtual environment (.venv) sudah tersedia dan cocok dengan folder ini.
    )
)

if "!NEED_NEW_VENV!"=="1" (
    echo Membuat virtual environment baru di folder .venv...
    call %SYS_PYTHON% -m venv .venv
    if !ERRORLEVEL! neq 0 (
        echo.
        echo ========================================================
        echo [ERROR] Gagal membuat virtual environment!
        echo Pastikan Anda memiliki izin akses tulis di folder ini.
        echo ========================================================
        echo.
        echo Tekan tombol apapun untuk keluar...
        pause
        exit /b 1
    )
    echo Virtual environment berhasil dibuat.
)

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
echo Jendela ini TIDAK akan tertutup otomatis agar Anda bisa membaca log.
echo Tekan tombol apapun untuk keluar...
pause
