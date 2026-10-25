@echo off
setlocal
echo ========================================================
echo   AFI Vision Builder - Install PyTorch CUDA GPU Support
echo ========================================================
echo.

set "VENV_PYTHON=.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment tidak ditemukan di .venv\Scripts\python.exe!
    echo Jalankan instalasi environment terlebih dahulu.
    pause
    exit /b 1
)

echo [1/2] Memeriksa keberadaan GPU NVIDIA...
where nvidia-smi >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] GPU NVIDIA terdeteksi via nvidia-smi:
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
) else (
    echo [WARNING] nvidia-smi tidak ditemukan. Pastikan driver NVIDIA terpasang.
)

echo.
echo [2/2] Menginstall PyTorch dengan akselerasi CUDA 12.1...
echo Perintah: %VENV_PYTHON% -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
echo.

"%VENV_PYTHON%" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

echo.
echo ========================================================
echo Validasi Instalasi GPU:
"%VENV_PYTHON%" -c "import torch; print('PyTorch Version:', torch.__version__); print('CUDA Available:', torch.cuda.is_available()); print('Device Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU Fallback')"
echo ========================================================
echo.
pause
