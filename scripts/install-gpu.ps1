<#
.SYNOPSIS
    Script PowerShell untuk menginstall PyTorch CUDA untuk akselerasi GPU NVIDIA.
#>

param(
    [string]$CudaVersion = "cu121"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   AFI Vision Builder - Install PyTorch CUDA GPU        " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Error "Virtual environment tidak ditemukan di $Python"
    exit 1
}

$NvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($NvidiaSmi) {
    Write-Host "[OK] GPU NVIDIA terdeteksi via nvidia-smi." -ForegroundColor Green
    & nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
} else {
    Write-Host "[WARNING] nvidia-smi tidak ditemukan. Pastikan driver NVIDIA sudah terpasang." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Menginstall PyTorch ($CudaVersion)..." -ForegroundColor Yellow
$IndexUrl = "https://download.pytorch.org/whl/$CudaVersion"

& $Python -m pip install torch torchvision --index-url $IndexUrl

Write-Host ""
Write-Host "Hasil verifikasi ketersediaan CUDA:" -ForegroundColor Cyan
& $Python -c "import torch; print('PyTorch Version:', torch.__version__); print('CUDA Available:', torch.cuda.is_available()); print('Device Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU Fallback')"
Write-Host "Selesai!" -ForegroundColor Green
