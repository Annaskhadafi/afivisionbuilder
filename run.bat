@echo off
setlocal enabledelayedexpansion

:: Mencegah jendela CMD menutup otomatis jika dibuka lewat double-click di File Explorer
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

if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
    echo Menggunakan Virtual Environment [.venv]...
) else (
    where python >nul 2>nul
    if !ERRORLEVEL! neq 0 (
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

:SERVER_LOOP
echo.
echo ========================================================
echo  Menjalankan server AFI Vision Builder...
echo  (Tekan Ctrl+C di jendela ini untuk menghentikan server)
echo ========================================================
echo.

call "%PY_CMD%" server.py

echo.
echo ========================================================
if !ERRORLEVEL! neq 0 (
    echo [INFO] Server berhenti (Status Code: !ERRORLEVEL!).
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
