param(
  [ValidateSet("auto", "cu126", "cu132")]
  [string]$CudaWheel = "auto",
  [string]$RuntimeDir = "",
  [string]$BasePython = ""
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $RuntimeDir) {
  $RuntimeDir = Join-Path $Root "ai-runtime"
}
$RuntimeDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($RuntimeDir)
$Venv = Join-Path $RuntimeDir ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$Requirements = Join-Path $Root "requirements-ai.txt"
$DependencyInstaller = Join-Path $Root "install_ai_dependencies.py"
$VCRedistUrl = "https://aka.ms/vc14/vc_redist.x64.exe"

if (-not (Test-Path $Requirements)) {
  throw "requirements-ai.txt was not found at $Requirements"
}
if (-not (Test-Path $DependencyInstaller)) {
  throw "AI dependency installer was not found at $DependencyInstaller"
}

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
# The compiled app directory contains Python 3.13 DLLs. Keep every Python 3.12
# subprocess in the isolated runtime directory so Windows cannot load them.
Set-Location -LiteralPath $RuntimeDir

function Invoke-VenvCreate {
  param([string]$VenvPath, [string]$RequestedPython)

  $Launchers = @()
  if ($RequestedPython) {
    $Launchers += ,@($RequestedPython)
  }
  $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
  if ($PyLauncher) {
    $Launchers += ,@($PyLauncher.Source, "-3.12")
  }

  foreach ($Name in @("python", "python3")) {
    $Command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($Command) {
      $Launchers += ,@($Command.Source)
    }
  }

  foreach ($Launcher in $Launchers) {
    $Launcher = @($Launcher)
    $Exe = $Launcher[0]
    $PrefixArgs = @()
    if ($Launcher.Count -gt 1) {
      $PrefixArgs = $Launcher[1..($Launcher.Count - 1)]
    }

    & $Exe @PrefixArgs -c "import sys; print(sys.executable); raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 3)"
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "Skipping unusable Python launcher: $Exe $($PrefixArgs -join ' ')"
      continue
    }

    & $Exe @PrefixArgs -m venv --clear $VenvPath
    if ($LASTEXITCODE -eq 0) {
      return
    }
  }

  throw "Could not create the AI runtime venv with Python 3.12. Start VisoNode to download its private Python 3.12.10 runtime."
}

function Test-VCRuntime {
  # Microsoft records the installed v14 redistributable in these keys and
  # guarantees that newer v14 runtimes remain compatible with older binaries.
  # Do not require a fixed DLL list here: that layout can change between
  # redistributable releases (for example, Visual Studio 2026 / v14.50).
  $RuntimeKeys = @(
    "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
  )
  foreach ($Key in $RuntimeKeys) {
    $Runtime = Get-ItemProperty -LiteralPath $Key -ErrorAction SilentlyContinue
    if ($Runtime -and $Runtime.Installed -eq 1) {
      return $true
    }
  }
  return $false
}

function Install-VCRuntime {
  if (Test-VCRuntime) {
    Write-Host "Microsoft Visual C++ runtime is ready."
    return
  }
  if (-not [Environment]::Is64BitOperatingSystem) {
    throw "The AI runtime requires 64-bit Windows."
  }

  $Installer = Join-Path $RuntimeDir "vc_redist.x64.exe"
  $InstallLog = Join-Path $RuntimeDir "vc_redist.x64.log"
  Write-Host "Microsoft Visual C++ runtime is missing. Downloading it from Microsoft..."
  try {
    Invoke-WebRequest -Uri $VCRedistUrl -OutFile $Installer -UseBasicParsing
    $Signature = Get-AuthenticodeSignature -FilePath $Installer
    if (
      $Signature.Status -ne "Valid" -or
      -not $Signature.SignerCertificate -or
      $Signature.SignerCertificate.Subject -notmatch "O=Microsoft Corporation"
    ) {
      throw "The downloaded Visual C++ installer does not have a valid Microsoft signature."
    }

    Write-Host "Installing Microsoft Visual C++ runtime. Windows may ask for permission..."
    $Arguments = "/install /quiet /norestart /log `"$InstallLog`""
    $Process = Start-Process -FilePath $Installer -ArgumentList $Arguments -Verb RunAs -WindowStyle Hidden -Wait -PassThru
    if ($Process.ExitCode -eq 1638) {
      Write-Host "A newer Microsoft Visual C++ runtime is already installed."
      return
    }
    if (-not (Test-VCRuntime)) {
      if ($Process.ExitCode -eq 3010) {
        throw "Microsoft Visual C++ runtime installation requires a Windows restart. Restart Windows, then install the AI libraries again. Installer log: $InstallLog"
      }
      throw "Microsoft Visual C++ runtime installation failed with exit code $($Process.ExitCode). Installer log: $InstallLog"
    }
    Write-Host "Microsoft Visual C++ runtime installed successfully."
  } finally {
    Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
  }
}

$NeedsVenv = $true
if (Test-Path $Python) {
  & $Python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 3)" *> $null
  if ($LASTEXITCODE -eq 0) {
    $NeedsVenv = $false
  } else {
    Write-Warning "Existing AI runtime Python is unusable and will be repaired: $Python"
  }
}

if ($NeedsVenv) {
  Write-Host "Creating AI runtime venv at $Venv..."
  Invoke-VenvCreate $Venv $BasePython
}

Install-VCRuntime

Write-Host "Installing AI runtime dependencies in $Venv"
# The Python installer probes compute capability before importing PyTorch.
# A driver/executable alone does not establish compatibility with CUDA 13.
$InstallerArgs = @("-P", $DependencyInstaller, "--python", $Python, "--runtime-dir", $RuntimeDir, "--cuda-wheel", $CudaWheel)
if ($CudaWheel -ne "auto") {
  $InstallerArgs += "--gpu"
}
& $Python @InstallerArgs
if ($LASTEXITCODE -ne 0) {
  throw "AI dependency installation failed with exit code $LASTEXITCODE."
}

Write-Host ""
Write-Host "AI runtime installed. VisoNode will use:"
Write-Host $Python
