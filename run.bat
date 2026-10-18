@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    echo Menggunakan Virtual Environment (.venv)...
    .venv\Scripts\python.exe server.py
) else (
    echo Virtual Environment (.venv) tidak ditemukan, menggunakan python sistem...
    python server.py
)
