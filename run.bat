@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
title AFI Vision Builder

echo ========================================================
echo               AFI VISION BUILDER
echo ========================================================
echo.
echo Direktori aktif: "%CD%"
echo.

set "PY_CMD="

rem 1. Periksa apakah .venv tersedia dan cocok
if not exist ".venv\Scripts\python.exe" goto :TRY_SYS_PYTHON

call ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
if !ERRORLEVEL! neq 0 (
    echo [INFO] Folder .venv lama tidak cocok dengan lokasi folder saat ini.
    goto :TRY_SYS_PYTHON
)

set "PY_CMD=.venv\Scripts\python.exe"
echo [OK] Menggunakan Virtual Environment .venv.
goto :CHECK_DEPS

:TRY_SYS_PYTHON
rem 2. Cek Python sistem
python --version >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=python"
    echo [OK] Menggunakan Python sistem.
    goto :CHECK_DEPS
)

py --version >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=py"
    echo [OK] Menggunakan Python Launcher py.
    goto :CHECK_DEPS
)

where python >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=python"
    echo [OK] Menggunakan Python sistem.
    goto :CHECK_DEPS
)

rem 3. Jika Python tidak ditemukan sama sekali
echo.
echo ========================================================
echo [ERROR] Python tidak ditemukan di sistem Anda!
echo Silakan unduh dan pasang Python 3.10 / 3.11 / 3.12 dari:
echo   https://www.python.org/downloads/
echo Pastikan mencentang Add Python to PATH saat instalasi.
echo ========================================================
echo.
pause
exit /b 1

:CHECK_DEPS
rem 4. Periksa apakah FastAPI dan Uvicorn sudah terpasang
call %PY_CMD% -c "import fastapi, uvicorn" >nul 2>nul
if !ERRORLEVEL! equ 0 goto :START_SERVER

echo.
echo ========================================================
echo [ERROR] Paket FastAPI dan Uvicorn belum terpasang!
echo.
echo Server belum bisa dijalankan karena dependensi belum lengkap.
echo Silakan jalankan 'install.bat' terlebih dahulu, atau jalankan:
echo   %PY_CMD% -m pip install fastapi uvicorn
echo ========================================================
echo.
pause
exit /b 1

:START_SERVER
echo Membuka browser ke http://127.0.0.1:8765 ...
start "" "http://127.0.0.1:8765"

:SERVER_LOOP
echo.
echo ========================================================
echo  Menjalankan server AFI Vision Builder...
echo  (Tekan Ctrl+C di jendela ini untuk menghentikan server)
echo ========================================================
echo.

call %PY_CMD% server.py

echo.
echo ========================================================
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Server berhenti dengan kode error: !ERRORLEVEL!
) else (
    echo [INFO] Server AFI Vision Builder telah dihentikan.
)
echo ========================================================
echo.
echo Pilihan:
echo   Tekan [R] lalu Enter untuk Restart server
echo   Tekan [Enter] untuk menutup jendela ini
echo.
set "USER_ACT="
set /p "USER_ACT=Pilihan Anda: "
if /i "!USER_ACT!"=="R" goto :SERVER_LOOP
exit /b 0
