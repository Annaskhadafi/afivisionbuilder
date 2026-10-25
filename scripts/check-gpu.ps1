<#
.SYNOPSIS
    Pemeriksaan status GPU NVIDIA, Driver CUDA, dan Ketersediaan Akselerasi PyTorch pada AFI Vision Builder.
#>

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AFI Vision Builder - Pemeriksaan Status Hardware GPU   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$NvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($NvidiaSmi) {
    Write-Host "[1/3] Memeriksa Hardware Fisik GPU (nvidia-smi)..." -ForegroundColor Yellow
    $GpuOutput = & nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits 2>$null
    if ($LASTEXITCODE -eq 0 -and $GpuOutput) {
        Write-Host "  -> Terdeteksi GPU NVIDIA Fisik:" -ForegroundColor Green
        foreach ($Line in $GpuOutput) {
            $Parts = $Line -split ","
            if ($Parts.Count -ge 3) {
                Write-Host "     * Model  : $($Parts[0].Trim())" -ForegroundColor White
                Write-Host "     * VRAM   : $($Parts[1].Trim()) MB" -ForegroundColor White
                Write-Host "     * Driver : $($Parts[2].Trim())" -ForegroundColor White
            }
        }
    } else {
        Write-Host "  -> nvidia-smi terpanggil namun tidak ada GPU yang merespon." -ForegroundColor Yellow
    }
} else {
    Write-Host "[1/3] nvidia-smi tidak ditemukan di PATH (Tidak ada GPU NVIDIA / driver belum terpasang)." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "[2/3] Memeriksa Environment Python & PyTorch..." -ForegroundColor Yellow

$Python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$PyCheck = & $Python -c "
import sys
try:
    import torch
    installed = True
    ver = torch.__version__
    cuda_avail = torch.cuda.is_available()
    dev_count = torch.cuda.device_count() if cuda_avail else 0
    dev_name = torch.cuda.get_device_name(0) if cuda_avail and dev_count > 0 else 'N/A'
    print(f'TORCH_INSTALLED={installed}')
    print(f'TORCH_VERSION={ver}')
    print(f'CUDA_AVAILABLE={cuda_avail}')
    print(f'DEVICE_COUNT={dev_count}')
    print(f'DEVICE_NAME={dev_name}')
except ImportError:
    print('TORCH_INSTALLED=False')
" 2>$null

$TorchInstalled = ($PyCheck | Select-String "TORCH_INSTALLED=(.+)" | ForEach-Object { $_.Matches.Groups[1].Value }) -eq "True"
$TorchVersion = ($PyCheck | Select-String "TORCH_VERSION=(.+)" | ForEach-Object { $_.Matches.Groups[1].Value })
$CudaAvailable = ($PyCheck | Select-String "CUDA_AVAILABLE=(.+)" | ForEach-Object { $_.Matches.Groups[1].Value }) -eq "True"
$DeviceName = ($PyCheck | Select-String "DEVICE_NAME=(.+)" | ForEach-Object { $_.Matches.Groups[1].Value })

Write-Host "  -> Python Interpreter : $Python" -ForegroundColor White
Write-Host "  -> PyTorch Terpasang  : $(if ($TorchInstalled) { $TorchVersion } else { 'TIDAK TERPASANG' })" -ForegroundColor White
Write-Host "  -> Akselerasi CUDA    : $(if ($CudaAvailable) { 'AKTIF (' + $DeviceName + ')' } else { 'TIDAK AKTIF / CPU MODE' })" -ForegroundColor $(if ($CudaAvailable) { "Green" } else { "Yellow" })

Write-Host ""
Write-Host "[3/3] Kesimpulan & Mekanisme Auto-Fallback:" -ForegroundColor Yellow

if ($CudaAvailable) {
    Write-Host "  [OK] GPU terdeteksi dan akselerasi CUDA PyTorch AKTIF." -ForegroundColor Green
    Write-Host "       AFI Vision Builder otomatis menggunakan GPU ($DeviceName) untuk inferensi cepat." -ForegroundColor Green
} elseif ($NvidiaSmi -and $TorchInstalled) {
    Write-Host "  [INFO] GPU Fisik NVIDIA terdeteksi, TETAPI PyTorch yang terinstall adalah versi CPU ($TorchVersion)." -ForegroundColor Cyan
    Write-Host "  [STATUS AUTO-FALLBACK] AKTIF! Sistem otomatis mengalihkan komputasi ke CPU secara mulus." -ForegroundColor Green
    Write-Host "       Aplikasi tetap berjalan normal tanpa crash menggunakan CPU multi-core." -ForegroundColor Green
    Write-Host ""
    Write-Host "  [CARA AKTIFKAN GPU CUDA]:" -ForegroundColor Yellow
    Write-Host "       Untuk mengaktifkan akselerasi GPU NVIDIA, jalankan:" -ForegroundColor White
    Write-Host "       .\scripts\install-gpu.bat" -ForegroundColor Cyan
    Write-Host "       atau:" -ForegroundColor White
    Write-Host "       .venv\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121" -ForegroundColor Cyan
} else {
    Write-Host "  [INFO] Berjalan dalam mode CPU murni. Auto-fallback aktif." -ForegroundColor White
}

Write-Host ""
