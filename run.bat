@echo off
setlocal enabledelayedexpansion

rem Mencegah jendela CMD menutup otomatis jika dibuka lewat double-click di File Explorer
if "%~1"=="__KEEP_OPEN__" goto :MAIN
if not defined INSIDE_RUN_WRAPPER (
    set INSIDE_RUN_WRAPPER=1
    cmd /k ""%~f0" __KEEP_OPEN__ %*"
    exit /b
)

:MAIN
cd /d "%~dp0"
title AFI Vision Builder

echo ========================================================
echo               AFI VISION BUILDER
echo ========================================================
echo.
echo Direktori aktif: "%CD%"
echo.

set "PY_CMD="

if not exist ".venv\Scripts\python.exe" goto :CHECK_SYS_PYTHON

rem Verifikasi apakah .venv valid
call ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=.venv\Scripts\python.exe"
    echo [OK] Virtual Environment .venv aktif dan cocok dengan folder ini.
    goto :START_SERVER
)

echo [PERINGATAN] Folder .venv lama tidak cocok dengan path folder saat ini.
echo Disarankan untuk menjalankan install.bat agar .venv disesuaikan.
echo Mencoba menggunakan Python sistem...

:CHECK_SYS_PYTHON
python --version >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=python"
    echo [OK] Menggunakan Python sistem.
    goto :START_SERVER
)

where python >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=python"
    echo [OK] Menggunakan Python sistem.
    goto :START_SERVER
)

echo.
echo ========================================================
echo [ERROR] Python tidak ditemukan di sistem Anda!
echo Silakan unduh dan pasang Python 3.10 / 3.11 / 3.12 dari:
echo   https://www.python.org/downloads/
echo Pastikan mencentang Add Python to PATH saat instalasi.
echo ========================================================
echo.
echo Tekan tombol apapun untuk keluar...
pause
exit /b 1

:START_SERVER
echo Membuka browser ke http://127.0.0.1:8765 ...
start "" "http://127.0.0.1:8765"

:SERVER_LOOP
echo.
echo ========================================================
echo  Menjalankan server AFI Vision Builder...
echo  Tekan Ctrl+C di jendela ini untuk menghentikan server
echo ========================================================
echo.

call "%PY_CMD%" server.py

echo.
echo ========================================================
if !ERRORLEVEL! neq 0 (
    echo [INFO] Server berhenti - Kode keluar: !ERRORLEVEL!
) else (
    echo [INFO] Server AFI Vision Builder telah dihentikan.
)
echo ========================================================
echo.
echo Tindakan selanjutnya:
echo   [1] Jalankan ulang server (Restart)
echo   [2] Keluar dan tutup jendela ini
echo.
set "USER_ACT=1"
set /p "USER_ACT=Masukkan pilihan Anda [1/2, default 1]: "
if "!USER_ACT!"=="2" (
    echo Menutup jendela...
    timeout /t 1 >nul
    exit /b 0
)
echo Memulai ulang server...
echo.
goto SERVER_LOOP
