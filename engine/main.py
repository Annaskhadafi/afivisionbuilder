from __future__ import annotations

import json
import copy
import inspect
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import warnings
from functools import lru_cache, wraps
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Lock, RLock, Thread
from urllib.parse import urlsplit

from app_version import APP_NAME, VERSION as APP_VERSION
from node_catalog import (
    ALL_DRAWING_NODE_TYPES,
    TRACKER_CONFIG_VERSION,
    TRACKING_ALGORITHMS,
    TRACKER_CONFIG_DEFAULTS,
    migrate_tracker_config,
    normalize_overlay_config,
    normalize_efficientad_config,
    PYTHON_SCRIPT_DEFAULTS,
)
from python_script_runtime import (
    PythonScriptRunner,
    ScriptError,
    ScriptStopped,
    ScriptTimeout,
    validate_script,
)

ROOT = Path(__file__).resolve().parent
RFDETR_DETECTION_MODELS = ("rfdetr-nano", "rfdetr-small", "rfdetr-medium", "rfdetr-large")
RFDETR_SEGMENTATION_MODELS = ("rfdetr-seg-nano", "rfdetr-seg-small", "rfdetr-seg-medium", "rfdetr-seg-large")
CONVNEXT_MODELS = (
    "convnext_tiny.fb_in22k_ft_in1k",
    "convnext_small.fb_in22k_ft_in1k",
    "convnext_base.fb_in22k_ft_in1k",
    "convnext_large.fb_in22k_ft_in1k",
)
CONVNEXT_MODEL_ALIASES = {
    "ConvNeXt-Tiny": CONVNEXT_MODELS[0],
    "ConvNeXt-Small": CONVNEXT_MODELS[1],
    "ConvNeXt-Base": CONVNEXT_MODELS[2],
    "ConvNeXt-Large": CONVNEXT_MODELS[3],
}
RFDETR_MODEL_CLASSES = {
    "rfdetr-nano": "RFDETRNano",
    "rfdetr-small": "RFDETRSmall",
    "rfdetr-medium": "RFDETRMedium",
    "rfdetr-large": "RFDETRLarge",
    "rfdetr-seg-nano": "RFDETRSegNano",
    "rfdetr-seg-small": "RFDETRSegSmall",
    "rfdetr-seg-medium": "RFDETRSegMedium",
    "rfdetr-seg-large": "RFDETRSegLarge",
}
RFDETR_MODEL_SET = set(RFDETR_MODEL_CLASSES)
SAM3_MODELS = ("facebook/sam3",)
SAM3_IMAGE_SIZE = 1008
SAM3_DEFAULT_THRESHOLD = 0.1
RFDETR_NATIVE_IMAGE_SIZE = 0
INPUT_NODE_ID = "input"
LEGACY_CAMERA_NODE_ID = "camera"
INFERENCE_NODE_IDS = ("detector", "segmenter", "classifier", "efficientad")
FRAME_SAMPLER_NODE_TYPE = "frame_sampler"
IMAGE_PROCESSING_NODE_TYPES = (
    "resize", "crop", "rotate_flip", "color_convert", "brightness_contrast",
    "blur_sharpen", "perspective", "undistort", "background_subtract", "python_script",
)
DRAWING_NODE_TYPES = ALL_DRAWING_NODE_TYPES
LOGIC_NODE_TYPES = (
    "if_else", "compare_value", "roi_filter", "object_count_condition", "class_detected_condition",
    "confidence_threshold", "timer_delay", "debounce", "rate_limiter",
    "and_or_logic", "trigger_once",
)
IMAGE_EXTENSIONS = {".bmp", ".dib", ".jpg", ".jpeg", ".jpe", ".jp2", ".png", ".webp", ".pbm", ".pgm", ".ppm", ".pxm", ".pnm", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v", ".wmv"}
OUTPUT_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".m4v"}
MAX_EVENTS = 32
MAX_TERMINAL_LINES = 500

_model_cache = {}
_model_lock = Lock()
logger = logging.getLogger(__name__)


def exception_message(exc: BaseException) -> str:
    return str(exc).strip() or type(exc).__name__


VERSION_INFO = {"app": APP_NAME, "version": APP_VERSION}


def git_version_info() -> dict:
    try:
        commit_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            capture_output=True,
            text=True,
            timeout=2,
        )
        dirty_result = subprocess.run(
            ["git", "diff", "--quiet"],
            cwd=ROOT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return {"commit": None, "dirty": None}
    return {
        "commit": commit_result.stdout.strip() or None,
        "dirty": dirty_result.returncode != 0,
    }


class TerminalBuffer:
    def __init__(self, max_lines: int = MAX_TERMINAL_LINES) -> None:
        self._lock = Lock()
        self._lines: list[dict] = []
        self._seq = 0
        self._max = max_lines

    def append(self, text: str) -> None:
        with self._lock:
            self._seq += 1
            self._lines.append({
                "seq": self._seq,
                "time": time.strftime("%H:%M:%S"),
                "text": text,
            })
            overflow = len(self._lines) - self._max
            if overflow > 0:
                del self._lines[:overflow]

    def since(self, cursor: int) -> dict:
        with self._lock:
            new_lines = [line for line in self._lines if line["seq"] > cursor]
            return {"cursor": self._seq, "lines": new_lines}


terminal = TerminalBuffer()


def terminal_log(text: str) -> None:
    print(text, flush=True)
    terminal.append(text)


def open_external_terminal() -> str:
    if sys.platform == "darwin":
        from app_support import open_external_terminal as open_macos_terminal
        return open_macos_terminal()

    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        windows_terminal = shutil.which("wt.exe") or shutil.which("wt")
        if windows_terminal:
            subprocess.Popen(
                [windows_terminal, "-d", str(ROOT)],
                cwd=str(ROOT),
                creationflags=creationflags,
            )
            return "Opened Windows Terminal"

        shell_path = shutil.which("pwsh.exe") or shutil.which("powershell.exe")
        if shell_path:
            subprocess.Popen(
                [shell_path, "-NoExit", "-Command", "Set-Location -LiteralPath $PWD"],
                cwd=str(ROOT),
                creationflags=creationflags,
            )
            return f"Opened {Path(shell_path).name}"

        subprocess.Popen(["cmd.exe", "/K"], cwd=str(ROOT), creationflags=creationflags)
        return "Opened Command Prompt"

    candidates = (
        ("x-terminal-emulator", []),
        ("gnome-terminal", ["--working-directory", str(ROOT)]),
        ("konsole", ["--workdir", str(ROOT)]),
        ("xfce4-terminal", ["--working-directory", str(ROOT)]),
        ("xterm", ["-e", f"cd {ROOT} && exec sh"]),
    )
    for executable, args in candidates:
        path = shutil.which(executable)
        if path:
            subprocess.Popen([path, *args], cwd=str(ROOT), start_new_session=True)
            return f"Opened {executable}"
    raise RuntimeError("No supported external terminal application was found.")


def open_file_dialog(kind: str = "vision") -> str | None:
    kind = str(kind or "vision").lower()
    checkpoint_mode = kind == "checkpoint"
    if os.name == "nt":
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if not powershell:
            raise RuntimeError("PowerShell is required to open the Windows file picker.")

        if checkpoint_mode:
            title = "Select RF-DETR checkpoint"
            filter_spec = "RF-DETR checkpoints (*.pth;*.pt;*.ckpt)|*.pth;*.pt;*.ckpt|All files (*.*)|*.*"
        elif kind == "image":
            title = "Select image file"
            filter_spec = (
                "Image files (*.bmp;*.dib;*.jpg;*.jpeg;*.jpe;*.jp2;*.png;*.webp;*.pbm;*.pgm;*.ppm;*.pxm;*.pnm;*.tif;*.tiff)"
                "|*.bmp;*.dib;*.jpg;*.jpeg;*.jpe;*.jp2;*.png;*.webp;*.pbm;*.pgm;*.ppm;*.pxm;*.pnm;*.tif;*.tiff"
                "|All files (*.*)|*.*"
            )
        elif kind == "video":
            title = "Select video file"
            filter_spec = (
                "Video files (*.mp4;*.avi;*.mov;*.mkv;*.webm;*.m4v;*.wmv)"
                "|*.mp4;*.avi;*.mov;*.mkv;*.webm;*.m4v;*.wmv"
                "|All files (*.*)|*.*"
            )
        else:
            title = "Select input file"
            filter_spec = (
                "Vision files (*.bmp;*.dib;*.jpg;*.jpeg;*.jpe;*.jp2;*.png;*.webp;*.pbm;*.pgm;*.ppm;*.pxm;*.pnm;*.tif;*.tiff;*.mp4;*.avi;*.mov;*.mkv;*.webm;*.m4v;*.wmv)"
                "|*.bmp;*.dib;*.jpg;*.jpeg;*.jpe;*.jp2;*.png;*.webp;*.pbm;*.pgm;*.ppm;*.pxm;*.pnm;*.tif;*.tiff;*.mp4;*.avi;*.mov;*.mkv;*.webm;*.m4v;*.wmv"
                "|Image files (*.bmp;*.jpg;*.jpeg;*.png;*.webp;*.tif;*.tiff)|*.bmp;*.jpg;*.jpeg;*.png;*.webp;*.tif;*.tiff"
                "|Video files (*.mp4;*.avi;*.mov;*.mkv;*.webm;*.m4v;*.wmv)|*.mp4;*.avi;*.mov;*.mkv;*.webm;*.m4v;*.wmv"
                "|All files (*.*)|*.*"
            )
        script = f"""
Add-Type -AssemblyName System.Windows.Forms
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = '{title}'
$dialog.Filter = @'
{filter_spec}
'@
$dialog.Multiselect = $false
$result = $dialog.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
  Write-Output $dialog.FileName
}}
"""
        result = subprocess.run(
            [powershell, "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-Command", script],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "Windows file picker failed.").strip()
            raise RuntimeError(detail)
        selected = result.stdout.strip()
        return str(Path(selected).resolve()) if selected else None

    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        raise RuntimeError("Tkinter is not available in this Python installation.") from exc

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.update()
    try:
        if checkpoint_mode:
            title = "Select RF-DETR checkpoint"
            filetypes = [
                ("RF-DETR checkpoints", "*.pth *.pt *.ckpt"),
                ("All files", "*.*"),
            ]
        elif kind == "image":
            title = "Select image file"
            filetypes = [
                ("Image files", "*.bmp *.dib *.jpg *.jpeg *.jpe *.jp2 *.png *.webp *.pbm *.pgm *.ppm *.pxm *.pnm *.tif *.tiff"),
                ("All files", "*.*"),
            ]
        elif kind == "video":
            title = "Select video file"
            filetypes = [
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.m4v *.wmv"),
                ("All files", "*.*"),
            ]
        else:
            title = "Select input file"
            filetypes = [
                ("Vision files", "*.bmp *.dib *.jpg *.jpeg *.jpe *.jp2 *.png *.webp *.pbm *.pgm *.ppm *.pxm *.pnm *.tif *.tiff *.mp4 *.avi *.mov *.mkv *.webm *.m4v *.wmv"),
                ("Image files", "*.bmp *.dib *.jpg *.jpeg *.jpe *.jp2 *.png *.webp *.pbm *.pgm *.ppm *.pxm *.pnm *.tif *.tiff"),
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.m4v *.wmv"),
                ("All files", "*.*"),
            ]
        path = filedialog.askopenfilename(
            title=title,
            filetypes=filetypes,
        )
        return str(Path(path).resolve()) if path else None
    finally:
        root.destroy()


@lru_cache(maxsize=None)
def _cuda_device_error(index: int) -> str | None:
    """Check actual CUDA execution once per device in this worker process.

    CUDA discovery only checks the driver; it can succeed even when the
    installed PyTorch wheel has no kernels for this GPU's architecture.
    """
    import torch

    try:
        # Allocation/copy alone does not launch a kernel. Exercise arithmetic
        # and synchronize so asynchronous launch failures are reported here.
        probe = torch.empty(1, device=f"cuda:{index}")
        probe.fill_(1).add_(1)
        torch.cuda.synchronize(index)
    except Exception as exc:
        try:
            name = torch.cuda.get_device_name(index)
        except Exception:
            name = f"device {index}"
        detail = (
            f"CUDA {index} ({name}) cannot run with the installed PyTorch "
            f"{torch.__version__} (CUDA {torch.version.cuda}): {exception_message(exc)}. "
            "PyTorch inference can fall back to CPU. For GPU acceleration, install "
            "a PyTorch/CUDA runtime that supports this GPU and its NVIDIA driver."
        )
        logger.warning(detail)
        return detail
    return None


def runtime_devices() -> dict:
    payload = {
        "torchInstalled": False,
        "torchVersion": None,
        "cudaAvailable": False,
        "cudaErrors": [],
        "mpsAvailable": False,
        "mpsBuilt": False,
        "cudaVersion": None,
        "nvidiaSmi": bool(shutil.which("nvidia-smi")),
        "nvidiaGpus": [],
        "devices": [],
        "recommendation": "Install the VisoNode AI runtime to enable inference.",
    }

    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            result = subprocess.run(
                [
                    nvidia_smi,
                    "--query-gpu=name,memory.total,driver_version",
                    "--format=csv,noheader,nounits",
                ],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    parts = [part.strip() for part in line.split(",")]
                    if len(parts) >= 3:
                        payload["nvidiaGpus"].append({
                            "name": parts[0],
                            "memoryMb": int(float(parts[1])),
                            "driver": parts[2],
                        })
        except Exception:
            pass

    try:
        import torch
    except ImportError:
        return payload

    payload["torchInstalled"] = True
    payload["torchVersion"] = torch.__version__
    payload["cudaVersion"] = torch.version.cuda
    mps = getattr(getattr(torch, "backends", None), "mps", None)
    payload["mpsBuilt"] = bool(mps and mps.is_built())
    payload["mpsAvailable"] = bool(mps and mps.is_available())
    payload["recommendation"] = "AI libraries are ready. CPU inference is available."
    if torch.cuda.is_available():
        for index in range(torch.cuda.device_count()):
            error = _cuda_device_error(index)
            if error:
                payload["cudaErrors"].append({"id": f"cuda:{index}", "error": error})
            try:
                name = torch.cuda.get_device_name(index)
                props = torch.cuda.get_device_properties(index)
                memory_mb = round(props.total_memory / (1024 * 1024))
            except Exception:
                name = f"NVIDIA GPU {index}"
                memory_mb = None
            payload["devices"].append({
                "id": f"cuda:{index}",
                "index": index,
                "name": name,
                "memoryMb": memory_mb,
                # Keep the CUDA inventory for engines with their own kernels,
                # notably TensorRT, while exposing PyTorch execution support.
                "torchUsable": error is None,
            })
        payload["cudaAvailable"] = any(device["torchUsable"] for device in payload["devices"])
    if payload["cudaAvailable"]:
        payload["recommendation"] = "CUDA is available. Select Auto or a CUDA device in Object Detection."
    elif payload["cudaErrors"]:
        payload["recommendation"] = (
            "The installed PyTorch runtime cannot execute on the detected NVIDIA GPU. "
            "Auto will use CPU inference. Select CPU or install a compatible PyTorch/CUDA runtime."
        )
    elif payload["nvidiaGpus"]:
        payload["recommendation"] = "NVIDIA GPU detected, but PyTorch CUDA is unavailable. Run scripts\\install-gpu.ps1."
    if payload["mpsAvailable"]:
        payload["devices"].append({"id": "mps", "name": "Apple Metal GPU", "memoryMb": None})
        if not payload["cudaAvailable"]:
            payload["recommendation"] = "Apple Metal (MPS) is available. Select Auto or MPS for AI inference."
    return payload


_inference_gpu_failures: dict[str, str] = {}
_inference_fallback_lock = Lock()


def reset_inference_fallbacks() -> None:
    """Reset process-local recovery state (normally cleared by restarting the worker)."""
    with _inference_fallback_lock:
        _inference_gpu_failures.clear()
    _mps_device_error.cache_clear()


def effective_inference_device(device: str) -> str:
    # A failed accelerator can leave its context unusable. Keep all Torch
    # models on CPU in this worker instead of retrying it on every frame.
    return "cpu" if _inference_gpu_failures and str(device) != "cpu" else str(device)


def _record_inference_fallback(device: str, exc: Exception) -> None:
    with _inference_fallback_lock:
        first_failure = not _inference_gpu_failures
        _inference_gpu_failures.setdefault(device, exception_message(exc))
    if first_failure:
        terminal_log(
            f"GPU inference failed on {device}: {exception_message(exc)}. "
            "Retrying on CPU."
        )


class CPUFallbackError(RuntimeError):
    """Both the GPU operation and its one CPU retry failed."""


def _with_cpu_fallback(operation, device: str):
    effective = effective_inference_device(device)
    try:
        return operation(effective)
    except CPUFallbackError:
        # Nested loading/inference wrappers must not retry a failed CPU retry.
        raise
    except Exception as gpu_error:
        if effective == "cpu":
            raise
        if _inference_gpu_failures:
            failed_device, reason = next(iter(_inference_gpu_failures.items()))
            raise CPUFallbackError(
                f"GPU operation on {failed_device} failed: {reason}. "
                f"CPU retry also failed: {exception_message(gpu_error)}"
            ) from gpu_error
        _record_inference_fallback(device, gpu_error)
        try:
            return operation("cpu")
        except CPUFallbackError:
            with _inference_fallback_lock:
                _inference_gpu_failures.pop(device, None)
            raise
        except Exception as cpu_error:
            # Invalid model files/configuration can fail on both devices. Do
            # not permanently disable a healthy accelerator in that case.
            with _inference_fallback_lock:
                _inference_gpu_failures.pop(device, None)
            raise CPUFallbackError(
                f"GPU operation on {device} failed: {exception_message(gpu_error)}. "
                f"CPU retry also failed: {exception_message(cpu_error)}"
            ) from cpu_error


def _cpu_fallback_loader(function):
    signature = inspect.signature(function)

    @wraps(function)
    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        device = str(bound.arguments["device"])

        def load(on_device):
            bound.arguments["device"] = on_device
            return function(*bound.args, **bound.kwargs)

        return _with_cpu_fallback(load, device)

    return wrapped


def _cpu_fallback_inference(function):
    signature = inspect.signature(function)

    @wraps(function)
    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        if "frames" in bound.arguments and not bound.arguments["frames"]:
            return function(*args, **kwargs)
        node = bound.arguments["inference_node"]
        device, _ = resolve_inference_device(node.get("config", {}))
        # The original function re-resolves the device after recovery, keeping
        # preprocessing, loading, forward passes and result conversion together.
        return _with_cpu_fallback(lambda _: function(*args, **kwargs), device)

    return wrapped


class TensorRTCPUFallbackUnavailable(RuntimeError):
    pass


def _tensorrt_recovery_error(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except TensorRTCPUFallbackUnavailable:
            raise
        except Exception as exc:
            raise TensorRTCPUFallbackUnavailable(
                f"TensorRT failed: {exception_message(exc)}. CPU fallback is unavailable "
                "for TensorRT .engine/.plan files. Select the original RF-DETR PyTorch "
                "checkpoint or its ONNX export to run this model on CPU."
            ) from exc

    return wrapped


def resolve_inference_device(config: dict) -> tuple[str, str]:
    if config.get("engine") == "rfdetr_onnx":
        return "cpu", "CPU (ONNX Runtime)"
    if config.get("engine") == "rfdetr_tensorrt":
        return _resolve_requested_inference_device(config)
    requested = str(config.get("device", "auto") or "auto").strip().lower()
    if requested not in ("auto", "cpu", "mps", "mps:0", "cuda") and not (
        requested.isdigit() or re.fullmatch(r"cuda:\d+", requested)
    ):
        raise RuntimeError(f"Unsupported inference device '{requested}'.")
    if _inference_gpu_failures:
        return "cpu", "CPU"
    try:
        return _resolve_requested_inference_device(config)
    except Exception as exc:
        if requested == "cpu":
            raise
        _record_inference_fallback(requested, exc)
        return "cpu", "CPU"


def _resolve_requested_inference_device(config: dict) -> tuple[str, str]:
    if config.get("engine") == "rfdetr_onnx":
        return "cpu", "CPU (ONNX Runtime)"
    requested = str(config.get("device", "auto") or "auto").strip().lower()
    if requested in ("", "auto"):
        try:
            import torch
        except ImportError:
            return "cpu", "CPU"
        if torch.cuda.is_available():
            for index in range(torch.cuda.device_count()):
                if config.get("engine") == "rfdetr_tensorrt" or _cuda_device_error(index) is None:
                    return f"cuda:{index}", f"CUDA {index} - {torch.cuda.get_device_name(index)}"
        mps = getattr(getattr(torch, "backends", None), "mps", None)
        if mps is not None and mps.is_available() and config.get("engine") != "rfdetr_tensorrt":
            error = _mps_device_error()
            if error:
                raise RuntimeError(error)
            return "mps", "Apple Metal (MPS)"
        return "cpu", "CPU"

    if requested == "cpu":
        return "cpu", "CPU"

    if requested in ("mps", "mps:0"):
        if config.get("engine") == "rfdetr_tensorrt":
            raise RuntimeError("TensorRT requires an NVIDIA CUDA GPU. Use the PyTorch RF-DETR model for MPS.")
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("MPS was selected, but PyTorch is not installed. Install the VisoNode AI runtime.") from exc
        mps = getattr(getattr(torch, "backends", None), "mps", None)
        if mps is None or not mps.is_available():
            raise RuntimeError("MPS was selected, but Apple Metal acceleration is unavailable. Select CPU or install an MPS-enabled PyTorch runtime on a supported Mac.")
        error = _mps_device_error()
        if error:
            raise RuntimeError(error)
        return "mps", "Apple Metal (MPS)"

    if requested.isdigit():
        requested = f"cuda:{requested}"
    if requested.startswith("cuda"):
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("GPU was selected, but PyTorch is not installed. Install the VisoNode AI runtime.") from exc
        if not torch.cuda.is_available():
            raise RuntimeError("GPU was selected, but PyTorch CUDA is not available. Run scripts\\check-gpu.ps1.")
        try:
            index = int(requested.split(":", 1)[1]) if ":" in requested else 0
        except ValueError as exc:
            raise RuntimeError(f"Invalid CUDA device '{requested}'.") from exc
        if index < 0 or index >= torch.cuda.device_count():
            raise RuntimeError(f"CUDA device {index} is not available.")
        # TensorRT executes its own kernels; Torch's compiled architectures
        # need not match the architectures supported by the TensorRT engine.
        error = None if config.get("engine") == "rfdetr_tensorrt" else _cuda_device_error(index)
        if error:
            raise RuntimeError(error)
        return f"cuda:{index}", f"CUDA {index} - {torch.cuda.get_device_name(index)}"

    raise RuntimeError(f"Unsupported inference device '{requested}'.")


@lru_cache(maxsize=1)
def _mps_device_error() -> str | None:
    import torch

    try:
        torch.empty(1, device="mps").fill_(1).add_(1)
        torch.mps.synchronize()
    except Exception as exc:
        return f"Apple Metal (MPS) cannot execute inference: {exception_message(exc)}"
    return None


def default_rfdetr_model(node_type: str) -> str:
    return "rfdetr-seg-nano" if node_type == "segmenter" else "rfdetr-nano"


def inference_model_name(inference_node: dict) -> str:
    if inference_node.get("type") == "efficientad":
        from efficientad_runtime import model_path
        return f"EfficientAD ({model_path(inference_node.get('config', {})).name})"
    config = inference_node.get("config", {})
    engine = config.get("engine", "rfdetr")
    if engine == "sam3":
        return str(sam3_checkpoint_path(config) or "facebook/sam3")
    if engine == "rfdetr_tensorrt":
        return str(rfdetr_tensorrt_engine_path(config))
    if engine == "rfdetr_onnx":
        return str(rfdetr_onnx_model_path(config))
    if engine == "convnext":
        checkpoint_path = convnext_checkpoint_path(config)
        if checkpoint_path:
            return f"ConvNeXt ({checkpoint_path})"
        return str(config.get("convnextModel") or CONVNEXT_MODELS[0])
    if engine in ("ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
        return str(config.get("customModelPath") or config.get("modelPath") or config.get("rfdetrCheckpoint") or "yolov8n.pt")
    model_name = config.get("rfdetrModel") or default_rfdetr_model(inference_node.get("type", "detector"))
    checkpoint_path = rfdetr_checkpoint_path(config)
    return f"{model_name} ({checkpoint_path})" if checkpoint_path else model_name


def rfdetr_checkpoint_path(config: dict) -> Path | None:
    raw_value = str(config.get("rfdetrCheckpoint") or "").strip().strip('"')
    if not raw_value:
        return None
    checkpoint_path = resolve_model_file(raw_value)
    if not checkpoint_path.exists() or not checkpoint_path.is_file():
        raise RuntimeError(f"RF-DETR checkpoint was not found at {checkpoint_path}.")
    return checkpoint_path


def convnext_checkpoint_path(config: dict) -> Path | None:
    raw_value = str(config.get("convnextCheckpoint") or "").strip().strip('"')
    if not raw_value:
        return None
    checkpoint_path = resolve_model_file(raw_value)
    if checkpoint_path.suffix.lower() not in (".pth", ".pt", ".ckpt"):
        raise RuntimeError("ConvNeXt checkpoints must use a .pth, .pt, or .ckpt file.")
    if not checkpoint_path.exists() or not checkpoint_path.is_file():
        raise RuntimeError(f"ConvNeXt checkpoint was not found at {checkpoint_path}.")
    return checkpoint_path


def convnext_class_names(config: dict) -> list[str]:
    value = config.get("convnextClasses", "")
    if isinstance(value, dict):
        def class_sort_key(item):
            try:
                return 0, int(item[0])
            except (TypeError, ValueError):
                return 1, str(item[0])
        return [str(label).strip() for _key, label in sorted(value.items(), key=class_sort_key)]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [
        item.strip()
        for item in str(value or "").replace(",", "\n").splitlines()
        if item.strip()
    ]


def rfdetr_tensorrt_engine_path(config: dict) -> Path:
    raw_value = str(config.get("rfdetrTensorRTEngine") or "").strip().strip('"')
    if not raw_value:
        raise RuntimeError("Select an RF-DETR TensorRT .engine or .plan file.")
    engine_path = resolve_model_file(raw_value)
    if engine_path.suffix.lower() not in (".engine", ".plan"):
        raise RuntimeError("RF-DETR TensorRT models must use an .engine or .plan file.")
    if not engine_path.exists() or not engine_path.is_file():
        raise RuntimeError(f"RF-DETR TensorRT engine was not found at {engine_path}.")
    return engine_path


def rfdetr_tensorrt_class_names(config: dict) -> list[str]:
    value = config.get("rfdetrTensorRTClasses", "")
    if isinstance(value, (list, tuple)):
        # Arrays represent class IDs; empty sparse slots must not shift labels.
        return [str(item).strip() if item is not None and str(item).strip() else str(index)
                for index, item in enumerate(value)]
    return [item.strip() for item in str(value or "").replace(",", "\n").splitlines() if item.strip()]


def rfdetr_onnx_model_path(config: dict) -> Path:
    raw_value = str(config.get("rfdetrOnnxModel") or "").strip().strip('"')
    if not raw_value:
        raise RuntimeError("Select a full RF-DETR ONNX .onnx model.")
    model_path = resolve_model_file(raw_value)
    if model_path.suffix.lower() != ".onnx":
        raise RuntimeError("RF-DETR ONNX models must use an .onnx file.")
    if not model_path.is_file():
        raise RuntimeError(f"RF-DETR ONNX model was not found at {model_path}.")
    return model_path


def _rfdetr_inference_size(raw_value: object) -> int:
    try:
        return max(0, int(raw_value or RFDETR_NATIVE_IMAGE_SIZE))
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"RF-DETR inference size must be a whole number, got {raw_value!r}."
        ) from exc


def _optimize_rfdetr_model(model, device: str, half_precision: bool = True) -> None:
    """Compile and warm one RF-DETR model before it receives live frames."""
    import torch

    optimize = getattr(model, "optimize_for_inference", None)
    if not callable(optimize):
        model._visonode_optimization_error = (
            "The installed RF-DETR version does not provide optimize_for_inference()."
        )
        return

    def _optimize_with_dtype(dtype) -> str:
        try:
            optimize(compile=True, batch_size=1, dtype=dtype)
        except TypeError:
            # Older RF-DETR versions accept no keyword arguments (FP32 only).
            optimize()
            return "FP32"
        return "FP16" if dtype == torch.float16 else "FP32"

    try:
        # RF-DETR 1.8 emits expected trace-shape warnings while creating its
        # fixed-resolution inference graph. They do not indicate a failed trace.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=torch.jit.TracerWarning)
            if half_precision and str(device).startswith("cuda"):
                try:
                    precision = _optimize_with_dtype(torch.float16)
                except Exception:
                    # optimize_for_inference cleans up after itself on failure,
                    # so a fresh FP32 attempt is safe.
                    precision = _optimize_with_dtype(torch.float32)
            else:
                precision = _optimize_with_dtype(torch.float32)

        resolution = int(getattr(getattr(model, "model", None), "resolution", 0) or 0)
        if resolution > 0:
            # predict() casts inputs to the optimized dtype internally.
            warmup_image = torch.zeros((3, resolution, resolution), dtype=torch.float32)
            model.predict(warmup_image, threshold=1.0, include_source_image=False)
            if str(device).startswith("cuda") and torch.cuda.is_available():
                torch.cuda.synchronize(torch.device(device))
            elif str(device).split(":", 1)[0] == "mps" and torch.backends.mps.is_available():
                torch.mps.synchronize()
        model._visonode_precision = precision
        model._visonode_optimization_error = None
    except Exception as exc:  # Optimization is optional; normal inference remains usable.
        remove_optimized = getattr(model, "remove_optimized_model", None)
        if callable(remove_optimized):
            try:
                remove_optimized()
            except Exception:
                pass
        model._visonode_optimization_error = exception_message(exc)
        logger.warning(
            "RF-DETR inference optimization failed; continuing with the regular model: %s",
            exception_message(exc),
        )


def _validate_rfdetr_node_type(
    model,
    expected_node_type: str | None,
    checkpoint_path: Path | None = None,
    model_name: str | None = None,
) -> None:
    """Reject detection/segmentation models attached to the wrong node type."""
    if expected_node_type not in ("detector", "segmenter"):
        return

    model_config = getattr(model, "model_config", None)
    segmentation_head = getattr(model_config, "segmentation_head", None)
    if segmentation_head is None:
        return

    is_segmentation_model = bool(segmentation_head)
    expects_segmentation_model = expected_node_type == "segmenter"
    if is_segmentation_model == expects_segmentation_model:
        return

    if checkpoint_path is not None:
        source = f"RF-DETR checkpoint '{checkpoint_path}'"
    else:
        source = f"RF-DETR model '{model_name or type(model).__name__}'"
    actual_task = "instance segmentation" if is_segmentation_model else "object detection"
    node_label = "Object Segmentation" if expects_segmentation_model else "Object Detection"
    required_task = "instance segmentation" if expects_segmentation_model else "object detection"
    raise RuntimeError(
        f"{source} is an {actual_task} model, but it is configured on an "
        f"{node_label} node. Use an {required_task} checkpoint or move this model "
        f"to an {'Object Segmentation' if is_segmentation_model else 'Object Detection'} node."
    )


def _rfdetr_checkpoint_foreground_class_count(checkpoint_path: Path) -> int | None:
    """Preserve the trained detection head instead of trusting saved arguments.

    RF-DETR heads include one background slot. Published checkpoints can carry
    stale ``args.num_classes`` (the Nano COCO checkpoint says 2 but has 91 head
    outputs), and legacy checkpoints count background in that argument. Either
    mismatch can make the package reinitialize trained classification weights.
    """
    try:
        import torch

        checkpoint = torch.load(
            checkpoint_path, map_location="cpu", weights_only=False
        )
    except Exception:
        # Let the package loader report unreadable or unsupported checkpoints.
        return None

    try:
        if not isinstance(checkpoint, dict):
            return None
        state_dict = checkpoint.get("model")
        if not isinstance(state_dict, dict):
            state_dict = checkpoint.get("state_dict")
        if not isinstance(state_dict, dict):
            state_dict = checkpoint
        for prefix in ("", "model."):
            bias = state_dict.get(prefix + "class_embed.bias")
            weight = state_dict.get(prefix + "class_embed.weight")
            tensor = bias if bias is not None else weight
            if tensor is None:
                continue
            shape = getattr(tensor, "shape", ())
            if len(shape) not in (1, 2) or int(shape[0]) < 2:
                return None
            if bias is not None and weight is not None and bias.shape[0] != weight.shape[0]:
                return None
            return int(shape[0]) - 1
    except (AttributeError, IndexError, TypeError, ValueError):
        return None
    finally:
        del checkpoint
    return None


@_cpu_fallback_loader
def load_rfdetr_model(
    model_name: str,
    device: str = "cpu",
    checkpoint_path: Path | None = None,
    inference_size: object = RFDETR_NATIVE_IMAGE_SIZE,
    half_precision: bool = True,
    expected_node_type: str | None = None,
):
    if checkpoint_path is None and model_name not in RFDETR_MODEL_SET:
        raise ValueError(f"Unsupported RF-DETR model '{model_name}'.")

    image_size = _rfdetr_inference_size(inference_size)
    cache_key = (
        "rfdetr", model_name, str(checkpoint_path or ""), device, image_size,
        bool(half_precision),
    )
    with _model_lock:
        if cache_key in _model_cache:
            model = _model_cache[cache_key]
            _validate_rfdetr_node_type(
                model, expected_node_type, checkpoint_path, model_name
            )
            return model
        try:
            import rfdetr
        except ImportError as exc:
            raise RuntimeError(
                "RF-DETR is not installed. Run '.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt'."
            ) from exc

        if str(device).startswith("cuda"):
            import torch

            # The JIT trace fixes input shapes, so autotuned kernels are safe.
            torch.backends.cudnn.benchmark = True
            # CPU-side torch work is tiny pre/postprocessing; the default
            # thread pool would fight the pipeline's stage threads.
            torch.set_num_threads(2)

        model_kwargs = {"device": device}
        if image_size > 0:
            # Constructing at the requested resolution lets RF-DETR compile a
            # matching fixed-shape inference graph instead of optimizing only
            # the variant's default resolution.
            model_kwargs["resolution"] = image_size

        model = None
        checkpoint_inference_error = None
        if checkpoint_path is not None:
            checkpoint_num_classes = _rfdetr_checkpoint_foreground_class_count(checkpoint_path)
            if checkpoint_num_classes is not None:
                model_kwargs["num_classes"] = checkpoint_num_classes
            checkpoint_loader = getattr(rfdetr, "from_checkpoint", None)
            if callable(checkpoint_loader):
                try:
                    # Custom checkpoints are self-describing. Restoring their
                    # saved variant/config prevents architectural parameters
                    # such as patch_size from being taken from the UI fallback.
                    model = checkpoint_loader(str(checkpoint_path), **model_kwargs)
                except KeyError as exc:
                    if exc.args != ("args",):
                        raise
                    checkpoint_inference_error = "it has no saved 'args' metadata"
                except ValueError as exc:
                    if not str(exc).startswith("Could not infer model class from checkpoint"):
                        raise
                    checkpoint_inference_error = str(exc)
            else:
                checkpoint_inference_error = (
                    "the installed RF-DETR version has no from_checkpoint() loader"
                )

        if model is None:
            if checkpoint_inference_error:
                logger.warning(
                    "Could not infer the RF-DETR architecture from checkpoint %s (%s); "
                    "falling back to the configured model variant %s.",
                    checkpoint_path,
                    checkpoint_inference_error,
                    model_name,
                )
            if model_name not in RFDETR_MODEL_SET:
                raise ValueError(
                    f"Unsupported RF-DETR model '{model_name}', and the checkpoint "
                    "architecture could not be inferred."
                )
            class_name = RFDETR_MODEL_CLASSES[model_name]
            model_class = getattr(rfdetr, class_name, None)
            if model_class is None:
                raise RuntimeError(
                    f"The installed RF-DETR package does not provide {class_name}. Update with '.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt'."
                )
            selected_model_kwargs = dict(model_kwargs)
            if checkpoint_path is not None:
                selected_model_kwargs["pretrain_weights"] = str(checkpoint_path)
            try:
                model = model_class(**selected_model_kwargs)
            except TypeError:
                selected_model_kwargs.pop("device", None)
                model = model_class(**selected_model_kwargs)

        _validate_rfdetr_node_type(
            model, expected_node_type, checkpoint_path, model_name
        )
        _optimize_rfdetr_model(model, device, half_precision)
        _model_cache[cache_key] = model
        return model


def rfdetr_predict_shape(config: dict, model) -> tuple[int, int] | None:
    """Return an optional square RF-DETR inference shape.

    A value of 0 means the package's native model resolution. This deliberately
    ignores SAM's generic ``imgsz`` field so old SAM configs do not make RF-DETR
    run at 1008x1008 by accident.
    """
    raw_value = config.get("rfdetrImageSize", RFDETR_NATIVE_IMAGE_SIZE)
    try:
        size = int(raw_value or RFDETR_NATIVE_IMAGE_SIZE)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"RF-DETR inference size must be a whole number, got {raw_value!r}.") from exc
    if size <= 0:
        return None

    model_config = getattr(model, "model_config", None)
    patch_size = int(getattr(model_config, "patch_size", 1) or 1)
    num_windows = int(getattr(model_config, "num_windows", 1) or 1)
    block_size = patch_size * num_windows
    if size % block_size != 0:
        native = getattr(getattr(model, "model", None), "resolution", None)
        native_text = f" Use 0 for the native {native}x{native} size." if native else " Use 0 for the native model size."
        raise RuntimeError(
            f"RF-DETR inference size {size} must be divisible by {block_size} "
            f"for this model ({patch_size} patch size x {num_windows} window(s)).{native_text}"
        )
    return (size, size)


def resolve_model_file(value: str, default_name: str = "") -> Path:
    model_path = Path(str(value or default_name).strip().strip('"') or default_name).expanduser()
    if not model_path.is_absolute():
        model_path = ROOT / model_path
    return model_path.resolve()


def sam3_concepts(config: dict) -> list[str]:
    concepts = [
        item.strip()
        for item in str(config.get("concepts") or "person").split(",")
        if item.strip()
    ]
    if not concepts:
        raise RuntimeError("SAM 3 concept prompts are empty. Add one or more noun phrases, for example 'person, car'.")
    return concepts


def sam3_checkpoint_path(config: dict) -> Path:
    raw_value = str(config.get("samCheckpoint") or "").strip().strip('"')
    if raw_value:
        checkpoint_path = resolve_model_file(raw_value)
    else:
        managed_value = os.environ.get("VISONODE_SAM3_CHECKPOINT", "").strip().strip('"')
        if managed_value:
            checkpoint_path = Path(managed_value).expanduser().resolve()
        else:
            candidates = (ROOT / "models" / "sam3.pt", ROOT.parent / "models" / "sam3.pt")
            checkpoint_path = next(
                (path.resolve() for path in candidates if path.is_file()),
                candidates[0].resolve(),
            )
    if not checkpoint_path.is_file():
        if raw_value:
            raise RuntimeError(f"SAM 3 checkpoint was not found at {checkpoint_path}.")
        raise RuntimeError(
            "SAM 3 is not downloaded. Open the Object Segmentation node and click "
            f"'Download SAM 3', or select a custom model path. Expected model: {checkpoint_path}"
        )
    return checkpoint_path


@_cpu_fallback_loader
def load_sam3_processor(config: dict, device: str = "cpu"):
    checkpoint_path = sam3_checkpoint_path(config)
    threshold = float(config.get("threshold", 0.25))
    imgsz = SAM3_IMAGE_SIZE
    cache_key = ("official-sam3", str(checkpoint_path or "hf"), device, threshold, imgsz)
    with _model_lock:
        if cache_key in _model_cache:
            return _model_cache[cache_key]
        try:
            import warnings
            from sam3_compat import (
                prepare_sam3_import, prepare_sam3_model,
                prepare_sam3_processor, sam3_build_device,
            )

            prepare_sam3_import(device)

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
                warnings.filterwarnings("ignore", message="Importing from timm.models.layers is deprecated.*", category=FutureWarning)
                from sam3.model.sam3_image_processor import Sam3Processor
                from sam3 import model_builder as sam3_builder
        except ImportError as exc:
            missing_module = getattr(exc, "name", "")
            if missing_module and missing_module != "sam3":
                raise RuntimeError(
                    f"Meta's official SAM 3 package is installed, but dependency '{missing_module}' is missing. Reinstall the AI runtime from Settings."
                ) from exc
            raise RuntimeError(
                "Meta's official SAM 3 package is not installed. Install the AI runtime from Settings."
            ) from exc

        try:
            builder_device = "cuda" if device.startswith("cuda") else "cpu"
            with sam3_build_device(sam3_builder, device):
                model = sam3_builder.build_sam3_image_model(
                    checkpoint_path=str(checkpoint_path),
                    device=builder_device,
                    load_from_HF=False,
                )
            prepare_sam3_model(model, device)
            model.to(device)
        except Exception as exc:
            raise RuntimeError(
                "Unable to load Meta SAM 3 from the selected checkpoint. "
                f"Device: {device}. {exc}"
            ) from exc

        processor = Sam3Processor(model, resolution=imgsz, device=device, confidence_threshold=threshold)
        prepare_sam3_processor(processor, device)
        _model_cache[cache_key] = processor
        return processor


def enabled_node(workflow: dict, node_id: str) -> dict | None:
    node = node_by_id(workflow, node_id)
    return node if node and node.get("enabled", True) else None


def node_by_id(workflow: dict, node_id: str) -> dict | None:
    return next((node for node in workflow.get("nodes", []) if node.get("id") == node_id), None)


def normalize_workflow(workflow: dict) -> dict:
    for node in workflow.get("nodes", []):
        if node.get("type") == LEGACY_CAMERA_NODE_ID:
            node["type"] = INPUT_NODE_ID
            if node.get("id") == LEGACY_CAMERA_NODE_ID and not node_by_id(workflow, INPUT_NODE_ID):
                node["id"] = INPUT_NODE_ID
        if node.get("type") == INPUT_NODE_ID:
            config = node.setdefault("config", {})
            config.setdefault("sourceType", "camera")
            if config.get("sourceType") not in ("camera", "daheng", "file", "image", "video"):
                config["sourceType"] = "camera"
            if "source" not in config:
                config["source"] = config.get("cameraIndex", config.get("deviceId", 0))
            config.setdefault("frameQueueSize", 8)
            config.setdefault("dropFrames", True)
            config.pop("youtubeUrl", None)
            config.pop("youtubeMaxHeight", None)
            config.pop("youtubeMaxFps", None)
        if node.get("type") == FRAME_SAMPLER_NODE_TYPE:
            config = node.setdefault("config", {})
            if isinstance(config.get("targetFps", 10), bool):
                raise ValueError("Frame sampler targetFps must be a finite number >= 0")
            try:
                target_fps = float(config.get("targetFps", 10))
            except (TypeError, ValueError):
                raise ValueError("Frame sampler targetFps must be a finite number >= 0") from None
            if not math.isfinite(target_fps) or target_fps < 0:
                raise ValueError("Frame sampler targetFps must be a finite number >= 0")
            config["targetFps"] = target_fps
        if node.get("type") == "python_script":
            config = node.setdefault("config", {})
            for key, value in PYTHON_SCRIPT_DEFAULTS.items():
                config.setdefault(key, value)
            code = config.get("code")
            if not isinstance(code, str):
                raise ValueError("Python script code must be a string")
            validate_script(code)
            timeout_ms = config.get("timeoutMs")
            if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or not 1 <= timeout_ms <= 60000:
                raise ValueError("Python script timeoutMs must be an integer between 1 and 60000")
            if config.get("onError") not in ("stop", "pass"):
                raise ValueError("Python script onError must be 'stop' or 'pass'")
        if node.get("type") == "detector":
            config = node.setdefault("config", {})
            if config.get("engine") not in ("rfdetr", "rfdetr_tensorrt", "rfdetr_onnx", "ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                config["engine"] = "rfdetr"
            config.pop("yoloModel", None)
            config.pop("end2end", None)
            config.pop("imgsz", None)
            config.setdefault("rfdetrModel", "rfdetr-nano")
            config.setdefault("rfdetrCheckpoint", "")
            config.setdefault("rfdetrImageSize", RFDETR_NATIVE_IMAGE_SIZE)
            config.setdefault("rfdetrHalfPrecision", True)
            config.setdefault("rfdetrTensorRTEngine", "")
            config.setdefault("rfdetrTensorRTClasses", "")
            config.setdefault("rfdetrOnnxModel", "")
            config.setdefault("rfdetrOnnxClasses", "")
            config.setdefault("detectEveryNFrames", 1)
            config.setdefault("maxDetectionFps", 0)
            config.setdefault("batchSize", 1)
        if node.get("type") == "segmenter":
            config = node.setdefault("config", {})
            if config.get("engine") not in ("sam3", "rfdetr", "rfdetr_tensorrt", "rfdetr_onnx", "ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                config["engine"] = "rfdetr"
            config.pop("yoloModel", None)
            config.pop("end2end", None)
            if config.get("engine") == "sam3":
                config["imgsz"] = SAM3_IMAGE_SIZE
                if float(config.get("threshold", 0.55)) == 0.55:
                    config["threshold"] = SAM3_DEFAULT_THRESHOLD
            config.setdefault("rfdetrModel", "rfdetr-seg-nano")
            config.setdefault("rfdetrCheckpoint", "")
            config.setdefault("rfdetrImageSize", RFDETR_NATIVE_IMAGE_SIZE)
            config.setdefault("rfdetrHalfPrecision", True)
            config.setdefault("rfdetrTensorRTEngine", "")
            config.setdefault("rfdetrTensorRTClasses", "")
            config.setdefault("rfdetrOnnxModel", "")
            config.setdefault("rfdetrOnnxClasses", "")
            config.setdefault("detectEveryNFrames", 1)
            config.setdefault("maxDetectionFps", 0)
            config.setdefault("batchSize", 1)
        if node.get("type") == "efficientad":
            normalize_efficientad_config(node.setdefault("config", {}))
        if node.get("type") == "classifier":
            config = node.setdefault("config", {})
            if config.get("engine") not in ("convnext", "ultralytics_yolo", "onnx_custom", "tflite", "tensorflow_keras", "custom_auto"):
                config["engine"] = "convnext"
            config.setdefault("threshold", 0.0)
            config.setdefault("convnextModel", "convnext_tiny.fb_in22k_ft_in1k")
            config.setdefault("convnextCheckpoint", "")
            config.setdefault("convnextClasses", "")
            config.setdefault("convnextImageSize", 224)
            config.setdefault("convnextHalfPrecision", True)
            config.setdefault("topK", 1)
            config.setdefault("detectEveryNFrames", 1)
            config.setdefault("maxDetectionFps", 0)
            config.setdefault("batchSize", 1)
        if node.get("type") == "detection_crop":
            config = node.setdefault("config", {})
            config.setdefault("classes", "")
            config.setdefault("paddingPercent", 0.0)
            config.setdefault("square", False)
            config.setdefault("minSize", 1)
            config.setdefault("maxCrops", 32)
        if node.get("type") == "track_snapshot":
            config = node.setdefault("config", {})
            config.setdefault("trackIds", "")
            config.setdefault("classes", "")
            config.setdefault("minimumConfidence", 0.0)
            config.setdefault("minimumTrackAgeFrames", 1)
            config.setdefault("retentionSeconds", 3600)
        if node.get("type") == "object_counter":
            config = node.setdefault("config", {})
            config.setdefault("classes", "")
            config.setdefault("countOncePerTrack", True)
            config.setdefault("retentionSeconds", 3600)
        if node.get("type") == "tracker":
            config = node.setdefault("config", {})
            migrate_tracker_config(config)
            if config.get("algorithm") not in TRACKING_ALGORITHMS:
                config["algorithm"] = "bytetrack"
            for key, value in TRACKER_CONFIG_DEFAULTS.items():
                config.setdefault(key, value)
        if node.get("type") == "preview":
            config = node.setdefault("config", {})
            config.pop("useFilter", None)
            config.setdefault("showTrackIds", True)
            config.setdefault("showTrails", True)
            config.setdefault("cropGridMaxItems", 16)
            config.setdefault("cropGridColumns", 0)
            config.setdefault("cropGridGap", 8)
            config.setdefault("holdLastEvent", True)
            config.setdefault("saveVideo", False)
            config.setdefault("outputPath", "")
            config.setdefault("outputFps", 0)
        if node.get("type") == "draw_text":
            config = node.setdefault("config", {})
            config.setdefault("textTemplate", "{classification.class}  {classification.confidence}")
            config.setdefault("x", 24)
            config.setdefault("y", 48)
            config.setdefault("fontScale", 1.0)
            config.setdefault("thickness", 2)
            config.setdefault("color", "#ffffff")
            config.setdefault("background", True)
            config.setdefault("backgroundColor", "#111827")
        if node.get("type") == "draw_boxes":
            config = node.setdefault("config", {})
            config.setdefault("labelTemplate", "{detection.class}  {detection.confidence}")
            config.setdefault("color", "#22c55e")
            config.setdefault("thickness", 2)
            config.setdefault("showLabel", True)
            config.setdefault("fillOpacity", 0.0)
        if node.get("type") == "overlay_annotate":
            normalize_overlay_config(node.setdefault("config", {}))
        if node.get("type") == "database_output":
            config = node.setdefault("config", {})
            config.setdefault("databasePath", "")
            config.setdefault("saveDetections", True)
            config.setdefault("eventObjectsOnly", True)
            config.setdefault("saveFrames", False)
            config.setdefault("saveEvents", True)
            config.setdefault("saveDebug", False)
            config.setdefault("sampleEvery", 1)
            config.setdefault("batchSize", 128)
            config.setdefault("flushIntervalMs", 500)
            config.setdefault("maxQueue", 10000)
        if node.get("type") == "image_output":
            config = node.setdefault("config", {})
            config.setdefault("outputDirectory", "")
            if config.get("format") not in ("jpg", "png"):
                config["format"] = "jpg"
            config.setdefault("format", "jpg")
            config.setdefault("jpegQuality", 95)
            config.setdefault("filenameTemplate", "{timestamp}_{track_id}_{class}")
        if node.get("type") in LOGIC_NODE_TYPES:
            config = node.setdefault("config", {})
            config.setdefault("operator", "gte")
            if config.get("operator") not in ("eq", "ne", "gt", "gte", "lt", "lte", "and", "or"):
                config["operator"] = "gte"
            config.setdefault("seconds", 1.0)
        if node.get("type") == "roi_filter":
            config = node.setdefault("config", {})
            if config.get("shape") not in ("rectangle", "polygon"):
                config["shape"] = "rectangle"
            config.setdefault("x", 0)
            config.setdefault("y", 0)
            config.setdefault("width", 640)
            config.setdefault("height", 480)
            if not isinstance(config.get("points"), list):
                config["points"] = []
            if config.get("mode") not in ("inside", "crossing"):
                config["mode"] = "inside"
            if config.get("match") not in ("center", "overlap", "contained"):
                config["match"] = "center"
            if config.get("crossingDirection") not in ("enter", "exit", "both"):
                config["crossingDirection"] = "enter"
            config.setdefault("showOverlay", True)

    for edge in workflow.get("edges", []):
        if len(edge) < 2:
            continue
        if edge[0] == LEGACY_CAMERA_NODE_ID:
            edge[0] = INPUT_NODE_ID
        if edge[1] == LEGACY_CAMERA_NODE_ID:
            edge[1] = INPUT_NODE_ID
    return workflow


def source_node_id(workflow: dict) -> str:
    input_node = next((node for node in workflow.get("nodes", []) if node.get("type") in (INPUT_NODE_ID, "ip_camera") and node.get("enabled", True)), None)
    if input_node:
        return input_node["id"]
    # Fallback to disabled input/ip_camera if none enabled
    any_input = next((node for node in workflow.get("nodes", []) if node.get("type") in (INPUT_NODE_ID, "ip_camera")), None)
    if any_input:
        return any_input["id"]
    return LEGACY_CAMERA_NODE_ID


def active_image_processing_nodes(workflow: dict) -> list[dict]:
    """Return enabled processing nodes in their graph execution order.

    Image processors operate on the frame stream before inference and display.
    Their order is derived from the graph, so a chain such as Input → Crop →
    Resize executes in that order even if its nodes were added in reverse.
    """
    input_id = source_node_id(workflow)
    candidates = [
        node for node in workflow.get("nodes", [])
        if node.get("type") in IMAGE_PROCESSING_NODE_TYPES
        and node.get("enabled", True)
        and has_active_path(workflow, input_id, node.get("id", ""))
    ]
    # Processing used by only one branch must not mutate the shared frame seen
    # by sibling branches.  The runner currently performs this pass once, so it
    # may contain only the common processing prefix.  Branch-local Crop nodes
    # feeding Detection Crop are handled as region constraints by
    # ``detection_crops`` below.
    frame_targets = [
        str(node.get("id") or "")
        for node in workflow.get("nodes", [])
        if (
            node.get("enabled", True)
            and node.get("type") in INFERENCE_NODE_IDS + ("preview",)
            and has_active_path(workflow, input_id, str(node.get("id") or ""))
            and not (
                node.get("type") in ("classifier", "efficientad")
                and any(
                    upstream.get("type") == "detection_crop"
                    and has_active_path(
                        workflow,
                        str(upstream.get("id") or ""),
                        str(node.get("id") or ""),
                    )
                    for upstream in workflow.get("nodes", [])
                )
            )
        )
    ]
    nodes = [
        node for node in candidates
        if not frame_targets or all(
            has_active_path(workflow, str(node.get("id") or ""), target_id)
            for target_id in frame_targets
        )
    ]
    common_ids = getattr(workflow, "common_processing_ids", None)
    if common_ids is not None:
        nodes = [node for node in nodes if str(node.get("id") or "") in common_ids]
    return _ordered_image_processing_nodes(workflow, nodes)


def _ordered_image_processing_nodes(workflow: dict, nodes: list[dict]) -> list[dict]:
    node_ids = {node.get("id") for node in nodes}
    order_hint = {node.get("id"): index for index, node in enumerate(nodes)}
    incoming = {node_id: 0 for node_id in node_ids}
    outgoing = {node_id: [] for node_id in node_ids}
    for edge in workflow.get("edges", []):
        if len(edge) < 2:
            continue
        from_id, to_id = edge[0], edge[1]
        if from_id in node_ids and to_id in node_ids:
            outgoing[from_id].append(to_id)
            incoming[to_id] += 1
    ready = sorted((node_id for node_id, degree in incoming.items() if degree == 0), key=order_hint.get)
    ordered_ids = []
    while ready:
        node_id = ready.pop(0)
        ordered_ids.append(node_id)
        for target_id in outgoing[node_id]:
            incoming[target_id] -= 1
            if incoming[target_id] == 0:
                ready.append(target_id)
                ready.sort(key=order_hint.get)
    # A cyclic graph is invalid in the editor, but retaining remaining nodes
    # gives old hand-edited workflows deterministic behavior.
    ordered_ids.extend(node.get("id") for node in nodes if node.get("id") not in ordered_ids)
    lookup = {node.get("id"): node for node in nodes}
    return [lookup[node_id] for node_id in ordered_ids]


def active_image_processing_nodes_for_path(
    workflow: dict,
    from_id: str,
    to_id: str,
) -> list[dict]:
    """Return processors that belong to a specific active graph branch."""
    nodes = [
        node for node in workflow.get("nodes", [])
        if (
            node.get("type") in IMAGE_PROCESSING_NODE_TYPES
            and node.get("enabled", True)
            and has_active_path(workflow, from_id, str(node.get("id") or ""))
            and has_active_path(workflow, str(node.get("id") or ""), to_id)
        )
    ]
    return _ordered_image_processing_nodes(workflow, nodes)


def active_drawing_nodes_for_target(workflow: dict, target_id: str) -> list[dict]:
    """Return enabled drawing nodes connected before a target in graph order."""
    input_id = source_node_id(workflow)
    nodes = [
        node for node in workflow.get("nodes", [])
        if (
            node.get("type") in DRAWING_NODE_TYPES
            and node.get("enabled", True)
            and has_active_path(workflow, input_id, str(node.get("id") or ""))
            and has_active_path(workflow, str(node.get("id") or ""), target_id)
        )
    ]
    return _ordered_image_processing_nodes(workflow, nodes)


def _perspective_points(value: object, width: int, height: int):
    import numpy as np

    try:
        points = []
        for pair in str(value).split(";"):
            x, y = (float(item.strip()) for item in pair.split(","))
            points.append((width * x / 100.0, height * y / 100.0))
    except (TypeError, ValueError):
        raise RuntimeError("Perspective points must be four 'x,y' percentage pairs separated by semicolons.") from None
    if len(points) != 4:
        raise RuntimeError("Perspective correction requires exactly four source points.")
    return np.float32(points)


def _calibration_data(path_value: object):
    """Load common JSON or OpenCV FileStorage camera calibration formats."""
    import numpy as np

    path = resolve_file_input_path(path_value)
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Unable to read calibration JSON: {path}") from exc
        matrix = data.get("camera_matrix", data.get("cameraMatrix"))
        distortion = data.get("distortion_coefficients", data.get("dist_coeff", data.get("distCoeffs", data.get("distortion"))))
        if matrix is None or distortion is None:
            raise RuntimeError("Calibration JSON needs camera_matrix and distortion_coefficients values.")
        return np.asarray(matrix, dtype=float), np.asarray(distortion, dtype=float)

    import cv2

    storage = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    try:
        matrix = storage.getNode("camera_matrix").mat()
        if matrix is None:
            matrix = storage.getNode("cameraMatrix").mat()
        distortion = storage.getNode("distortion_coefficients").mat()
        if distortion is None:
            distortion = storage.getNode("distCoeffs").mat()
    finally:
        storage.release()
    if matrix is None or distortion is None:
        raise RuntimeError("Calibration file needs camera_matrix and distortion_coefficients values.")
    return matrix, distortion


def run_python_script_node(frame, node: dict, runtime: dict, script_frames=None):
    """Run one persistent Python script node against a BGR frame."""
    context = runtime.setdefault("__python_scripts", {})
    runners = context.setdefault("runners", {})
    errors = context.setdefault("errors", {})
    callback = context.get("callback")
    stop_event = context.get("stop_event")
    lock = context.setdefault("lock", RLock())
    node_id = str(node.get("id") or node.get("type") or "python_script")
    config = node.get("config", {})
    signature = (config.get("code"), config.get("timeoutMs"), config.get("onError"))
    if script_frames is not None and node_id in script_frames:
        return script_frames[node_id]

    def notify(**fields):
        if callback:
            callback(node, **fields)

    with lock:
        if script_frames is not None and node_id in script_frames:
            return script_frames[node_id]
        if errors.get(node_id, (None,))[0] == signature:
            return frame.copy()
        current = runners.get(node_id)
        if current is None or current[0] != signature:
            if current is not None:
                current[1].close()
            errors.pop(node_id, None)
            notify(state="starting")
            try:
                # ponytail: one shared lock serializes lookup and execution; add per-node locks only if profiling proves contention.
                runner = PythonScriptRunner(
                    config["code"], config["timeoutMs"], stop_event, on_error="stop",
                )
            except BaseException as exc:
                errors[node_id] = (signature, exc)
                state = "timeout" if isinstance(exc, ScriptTimeout) else "error"
                notify(state=state, error=str(exc), logs=getattr(exc, "logs", ""), durationMs=0)
                if config["onError"] == "pass":
                    return frame.copy()
                raise
            runners[node_id] = (signature, runner)
        runner = runners[node_id][1]
        started_at = time.monotonic()
        notify(state="running")
        try:
            result = runner.run(frame)
        except ScriptStopped:
            raise
        except ScriptError as exc:
            duration_ms = (time.monotonic() - started_at) * 1000
            state = "timeout" if isinstance(exc, ScriptTimeout) else "error"
            notify(state=state, error=str(exc), logs=getattr(exc, "logs", ""), durationMs=duration_ms)
            if config["onError"] == "pass":
                return frame.copy()
            raise
        notify(logs=result.logs, durationMs=result.duration_ms, error=None)
        if script_frames is not None:
            script_frames[node_id] = result.frame
        return result.frame


def apply_image_processing(
    frame,
    workflow: dict,
    runtime: dict | None = None,
    debug_callback=None,
    processing_nodes: list[dict] | None = None,
    script_frames: dict | None = None,
):
    """Apply the workflow's frame processing chain and return a BGR frame."""
    import cv2
    import numpy as np

    runtime = runtime if runtime is not None else {}
    for node in (
        active_image_processing_nodes(workflow)
        if processing_nodes is None
        else processing_nodes
    ):
        before_frame = frame
        started_at = time.monotonic()
        config = node.get("config", {})
        node_id = node.get("id", node.get("type", "processor"))
        node_type = node.get("type")
        if node_type == "resize":
            width, height = int(config.get("width", frame.shape[1])), int(config.get("height", frame.shape[0]))
            if width <= 0 or height <= 0:
                raise RuntimeError("Resize width and height must be greater than zero.")
            interpolation = {"nearest": cv2.INTER_NEAREST, "linear": cv2.INTER_LINEAR, "cubic": cv2.INTER_CUBIC, "area": cv2.INTER_AREA, "lanczos": cv2.INTER_LANCZOS4}.get(config.get("interpolation"), cv2.INTER_LINEAR)
            frame = cv2.resize(frame, (width, height), interpolation=interpolation)
        elif node_type == "crop":
            x, y = max(0, int(config.get("x", 0))), max(0, int(config.get("y", 0)))
            width, height = int(config.get("width", frame.shape[1])), int(config.get("height", frame.shape[0]))
            x2, y2 = min(frame.shape[1], x + width), min(frame.shape[0], y + height)
            if x >= x2 or y >= y2:
                raise RuntimeError("Crop / Region of Interest does not overlap the input frame.")
            # Downstream consumers need contiguous data; this is a no-op copy
            # for full-width crops instead of always duplicating the region.
            frame = np.ascontiguousarray(frame[y:y2, x:x2])
        elif node_type == "rotate_flip":
            rotation = str(config.get("rotation", "0"))
            rotations = {"90": cv2.ROTATE_90_CLOCKWISE, "180": cv2.ROTATE_180, "270": cv2.ROTATE_90_COUNTERCLOCKWISE}
            if rotation in rotations:
                frame = cv2.rotate(frame, rotations[rotation])
            flip = config.get("flip", "none")
            if flip != "none":
                frame = cv2.flip(frame, {"horizontal": 1, "vertical": 0, "both": -1}.get(flip, 1))
        elif node_type == "color_convert":
            mode = config.get("mode", "gray")
            if mode == "gray":
                # Keep a 3-channel output so preview and inference consumers
                # can continue using their BGR frame contract.
                frame = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
            else:
                conversions = {"hsv": cv2.COLOR_BGR2HSV, "lab": cv2.COLOR_BGR2LAB, "ycrcb": cv2.COLOR_BGR2YCrCb}
                conversion = conversions.get(mode)
                if conversion is None:
                    frame = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        elif node_type == "brightness_contrast":
            alpha = float(config.get("contrast", 1.0) or 1.0)
            beta = int(config.get("brightness", 0) or 0)
            if alpha != 1.0 or beta != 0:
                frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
            if bool(config.get("useClahe", False)):
                auto_low = bool(config.get("autoLowLight", True))
                threshold = float(config.get("lowLightThreshold", 65.0) or 65.0)
                apply_clahe = True
                if auto_low:
                    if len(frame.shape) == 2:
                        mean_b = float(np.mean(frame))
                    else:
                        mean_b = float(np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)))
                    apply_clahe = mean_b < threshold
                if apply_clahe:
                    clip_limit = max(0.1, float(config.get("clipLimit", 2.5) or 2.5))
                    tile_size = max(2, int(config.get("tileGridSize", 8) or 8))
                    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
                    if len(frame.shape) == 2:
                        frame = clahe.apply(frame)
                    else:
                        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                        l_chan, a_chan, b_chan = cv2.split(lab)
                        cl = clahe.apply(l_chan)
        elif node_type == "blur_sharpen":
            kernel = max(1, int(config.get("kernel", 5) or 5)) | 1
            op = str(config.get("operation", "blur")).strip().lower()
            strength = float(config.get("strength", 1.0) or 1.0)
            if op == "sharpen":
                blurred = cv2.GaussianBlur(frame, (kernel, kernel), 0)
                frame = cv2.addWeighted(frame, 1.0 + strength, blurred, -strength, 0)
            elif op in ("gaussian", "gaussian_blur"):
                frame = cv2.GaussianBlur(frame, (kernel, kernel), 0)
            elif op in ("median", "median_blur"):
                frame = cv2.medianBlur(frame, kernel)
            elif op == "bilateral":
                frame = cv2.bilateralFilter(frame, kernel, 75, 75)
            else:
                frame = cv2.blur(frame, (kernel, kernel))
        elif node_type == "perspective":
            height, width = frame.shape[:2]
            output_width, output_height = int(config.get("width", 0)) or width, int(config.get("height", 0)) or height
            source = _perspective_points(config.get("points", "0,0; 100,0; 100,100; 0,100"), width, height)
            destination = np.float32(((0, 0), (output_width - 1, 0), (output_width - 1, output_height - 1), (0, output_height - 1)))
            frame = cv2.warpPerspective(frame, cv2.getPerspectiveTransform(source, destination), (output_width, output_height))
        elif node_type == "undistort":
            path = str(config.get("calibrationPath", "")).strip()
            if path:
                signature = (path, float(config.get("alpha", 0.0)), frame.shape[1], frame.shape[0])
                cached = runtime.get(node_id)
                if not cached or cached["signature"] != signature:
                    matrix, distortion = _calibration_data(path)
                    size = (frame.shape[1], frame.shape[0])
                    new_matrix, _ = cv2.getOptimalNewCameraMatrix(matrix, distortion, size, float(config.get("alpha", 0.0)), size)
                    maps = cv2.initUndistortRectifyMap(matrix, distortion, None, new_matrix, size, cv2.CV_16SC2)
                    cached = runtime[node_id] = {"signature": signature, "maps": maps}
                frame = cv2.remap(frame, cached["maps"][0], cached["maps"][1], cv2.INTER_LINEAR)
        elif node_type == "background_subtract":
            signature = (config.get("method", "mog2"), int(config.get("history", 500)), int(config.get("threshold", 16)), bool(config.get("detectShadows", True)))
            cached = runtime.get(node_id)
            if not cached or cached["signature"] != signature:
                factory = cv2.createBackgroundSubtractorKNN if signature[0] == "knn" else cv2.createBackgroundSubtractorMOG2
                subtractor = factory(history=signature[1], dist2Threshold=signature[2], detectShadows=signature[3]) if signature[0] == "knn" else factory(history=signature[1], varThreshold=signature[2], detectShadows=signature[3])
                cached = runtime[node_id] = {"signature": signature, "subtractor": subtractor}
            frame = cv2.cvtColor(cached["subtractor"].apply(frame), cv2.COLOR_GRAY2BGR)
        elif node_type == "python_script":
            frame = run_python_script_node(frame, node, runtime, script_frames)
        if debug_callback:
            debug_callback(node, before_frame, frame, (time.monotonic() - started_at) * 1000)
    return frame


def apply_preview_image_processing(
    frame,
    workflow: dict,
    target_id: str,
    detections: list[dict],
    runtime: dict | None = None,
    script_frames: dict | None = None,
):
    """Apply processors local to one preview branch and remap its boxes."""
    common_ids = {
        str(node.get("id") or "") for node in active_image_processing_nodes(workflow)
    }
    branch_nodes = [
        node
        for node in active_image_processing_nodes_for_path(
            workflow, source_node_id(workflow), target_id,
        )
        if str(node.get("id") or "") not in common_ids
    ]
    if not branch_nodes:
        return frame, detections

    mapped = [dict(item) for item in detections]
    result = frame
    for node in branch_nodes:
        before_height, before_width = result.shape[:2]
        result = apply_image_processing(
            result, workflow, runtime, processing_nodes=[node], script_frames=script_frames,
        )
        after_height, after_width = result.shape[:2]
        node_type = node.get("type")
        config = node.get("config", {})
        next_mapped = []
        for detection in mapped:
            box = _detection_box_xywh(detection)
            if box is None or detection.get("kind") == "classification":
                next_mapped.append(detection)
                continue
            x, y, width, height = box
            if node_type == "crop":
                crop_x = max(0, int(config.get("x", 0)))
                crop_y = max(0, int(config.get("y", 0)))
                x1 = max(0.0, x - crop_x)
                y1 = max(0.0, y - crop_y)
                x2 = min(float(after_width), x + width - crop_x)
                y2 = min(float(after_height), y + height - crop_y)
                if x2 <= x1 or y2 <= y1:
                    continue
                detection["bbox"] = [x1, y1, x2 - x1, y2 - y1]
                if detection.get("mask"):
                    detection["mask"] = [
                        [float(point[0]) - crop_x, float(point[1]) - crop_y]
                        for point in detection["mask"]
                    ]
                if detection.get("trail"):
                    detection["trail"] = [
                        [float(point[0]) - crop_x, float(point[1]) - crop_y]
                        for point in detection["trail"]
                    ]
            elif node_type == "resize":
                scale_x = after_width / max(1, before_width)
                scale_y = after_height / max(1, before_height)
                detection["bbox"] = [
                    x * scale_x, y * scale_y, width * scale_x, height * scale_y,
                ]
                if detection.get("mask"):
                    detection["mask"] = [
                        [float(point[0]) * scale_x, float(point[1]) * scale_y]
                        for point in detection["mask"]
                    ]
                if detection.get("trail"):
                    detection["trail"] = [
                        [float(point[0]) * scale_x, float(point[1]) * scale_y]
                        for point in detection["trail"]
                    ]
            next_mapped.append(detection)
        mapped = next_mapped
    return result, mapped


def active_input_node(workflow: dict) -> dict | None:
    return enabled_node(workflow, source_node_id(workflow))


class _RuntimeWorkflow(dict):
    """Run-owned snapshot: topology is fixed until the next workflow start."""


def prepare_runtime_workflow(workflow: dict) -> dict:
    snapshot = _RuntimeWorkflow(copy.deepcopy(dict(workflow)))
    enabled_ids = frozenset(node.get("id") for node in snapshot.get("nodes", []) if node.get("enabled", True) or node.get("type") == FRAME_SAMPLER_NODE_TYPE)
    edges = tuple((edge[0], edge[1]) for edge in snapshot.get("edges", []))
    # Attributes stay out of JSON/database workflow serialization.
    snapshot.reachability = {
        node_id: _reachable_node_ids(enabled_ids, edges, node_id) for node_id in enabled_ids
    }
    return snapshot


def has_active_path(workflow: dict, from_id: str, to_id: str) -> bool:
    if to_id == "auto_preview":
        if isinstance(workflow, _RuntimeWorkflow):
            return bool(getattr(workflow, "auto_preview_enabled", True))
        return True
    if isinstance(workflow, _RuntimeWorkflow):
        return to_id in workflow.reachability.get(from_id, ())
    # Key the cache by topology, not mutable workflow identity. Config edits do
    # not invalidate reachability; edge and enabled-state edits take effect now.
    enabled_ids = frozenset(node.get("id") for node in workflow.get("nodes", []) if node.get("enabled", True) or node.get("type") == FRAME_SAMPLER_NODE_TYPE)
    edges = tuple((edge[0], edge[1]) for edge in workflow.get("edges", []))
    return to_id in _reachable_node_ids(enabled_ids, edges, from_id)


@lru_cache(maxsize=512)
def _reachable_node_ids(enabled_ids: frozenset, edges: tuple, from_id: str) -> frozenset:
    if from_id not in enabled_ids:
        return frozenset()
    adjacency = {}
    for source, target in edges:
        if source in enabled_ids and target in enabled_ids:
            adjacency.setdefault(source, []).append(target)
    visited = set()
    pending = [from_id]
    while pending:
        current = pending.pop()
        if current not in visited:
            visited.add(current)
            pending.extend(adjacency.get(current, ()))
    return frozenset(visited)


def active_detector_node(workflow: dict) -> dict | None:
    input_id = source_node_id(workflow)
    return next(
        (node for node in workflow.get("nodes", [])
         if node.get("type") == "detector" and node.get("enabled", True)
         and has_active_path(workflow, input_id, node.get("id", ""))),
        None,
    )


def active_segmenter_node(workflow: dict) -> dict | None:
    input_id = source_node_id(workflow)
    return next(
        (node for node in workflow.get("nodes", [])
         if node.get("type") == "segmenter" and node.get("enabled", True)
         and has_active_path(workflow, input_id, node.get("id", ""))),
        None,
    )


def active_inference_nodes(workflow: dict) -> list[dict]:
    input_id = source_node_id(workflow)
    return [
        node for node in workflow.get("nodes", [])
        if node.get("type") in INFERENCE_NODE_IDS
        and node.get("enabled", True)
        and has_active_path(workflow, input_id, node.get("id", ""))
    ]


def active_detection_crop_nodes(workflow: dict) -> list[dict]:
    """Detection Crop nodes with an active detector or segmenter upstream."""
    input_id = source_node_id(workflow)
    detection_sources = [
        node for node in active_inference_nodes(workflow)
        if node.get("type") in ("detector", "segmenter")
    ]
    return [
        node for node in workflow.get("nodes", [])
        if (
            node.get("type") == "detection_crop"
            and node.get("enabled", True)
            and has_active_path(workflow, input_id, str(node.get("id") or ""))
            and any(
                has_active_path(
                    workflow,
                    str(source.get("id") or ""),
                    str(node.get("id") or ""),
                )
                for source in detection_sources
            )
        )
    ]


def active_detection_crop_bindings(workflow: dict) -> list[tuple[dict, dict]]:
    """Return enabled Detection Crop -> classification/inspection bindings."""
    inference_nodes = active_inference_nodes(workflow)
    classifiers = [node for node in inference_nodes if node.get("type") in ("classifier", "efficientad")]
    bindings: list[tuple[dict, dict]] = []
    for crop_node in active_detection_crop_nodes(workflow):
        crop_id = str(crop_node.get("id") or "")
        for classifier in classifiers:
            if has_active_path(workflow, crop_id, str(classifier.get("id") or "")):
                bindings.append((crop_node, classifier))
    return bindings


def validate_efficientad_workflow(workflow: dict) -> None:
    """Reject paths the shared-frame executor cannot inspect faithfully."""
    nodes = [node for node in active_inference_nodes(workflow) if node.get("type") == "efficientad"]
    if not nodes:
        return
    common_ids = {node["id"] for node in active_image_processing_nodes(workflow)}
    source_id = source_node_id(workflow)
    for node in nodes:
        crop_ancestors = [crop for crop in active_detection_crop_nodes(workflow)
                          if has_active_path(workflow, crop["id"], node["id"])]
        if len(crop_ancestors) > 1:
            raise RuntimeError("EfficientAD requires one Detection Crop input. Use a separate Visual Inspection node for each crop branch.")
        if crop_ancestors:
            crop_id = crop_ancestors[0]["id"]
            without_crop = {**workflow, "edges": [edge for edge in workflow.get("edges", [])
                                                 if crop_id not in edge[:2]]}
            if has_active_path(without_crop, source_id, node["id"]):
                raise RuntimeError("EfficientAD cannot mix full-frame and Detection Crop inputs. Use separate Visual Inspection nodes.")
        for upstream in workflow.get("nodes", []):
            if not upstream.get("enabled", True):
                continue
            upstream_id = str(upstream.get("id") or "")
            node_type = upstream.get("type")
            before = has_active_path(workflow, source_id, upstream_id) and has_active_path(workflow, upstream_id, node["id"])
            if before and node_type == "detection_crop" and upstream not in active_detection_crop_nodes(workflow):
                raise RuntimeError("EfficientAD Detection Crop requires an active detector or segmenter upstream.")
            if before and node_type in IMAGE_PROCESSING_NODE_TYPES and upstream_id not in common_ids:
                raise RuntimeError("EfficientAD requires a shared preprocessing path. Move Crop/processing before the workflow branches.")
            if before and node_type == "color_convert" and upstream.get("config", {}).get("mode", "gray") != "gray":
                raise RuntimeError("EfficientAD requires BGR or grayscale input; remove the HSV/Lab/color-space conversion.")
            if node_type in IMAGE_PROCESSING_NODE_TYPES and has_active_path(workflow, node["id"], upstream_id):
                raise RuntimeError("Place image processing before EfficientAD so the model input and anomaly map coordinates stay aligned.")


@_cpu_fallback_loader
def load_efficientad_model(config: dict, device: str = "cpu"):
    from efficientad_runtime import load_model
    return load_model(config, device)


@_cpu_fallback_inference
def run_efficientad_batch(frames: list, inference_node: dict) -> list[list[dict]]:
    from efficientad_runtime import run_batch
    device, _label = resolve_inference_device(inference_node.get("config", {}))
    return run_batch(frames, inference_node, device)


def run_efficientad_frame(frame, inference_node: dict) -> list[dict]:
    return run_efficientad_batch([frame], inference_node)[0]


def active_frame_inference_nodes(workflow: dict) -> list[dict]:
    """Inference nodes that consume the complete processed frame.

    Classification and EfficientAD downstream of Detection Crop consume object
    crops instead and must not also inspect the complete frame.
    """
    validate_efficientad_workflow(workflow)
    crop_classifier_ids = {
        str(classifier.get("id") or "")
        for _crop, classifier in active_detection_crop_bindings(workflow)
    }
    return [
        node for node in active_inference_nodes(workflow)
        if str(node.get("id") or "") not in crop_classifier_ids
    ]


def active_tracking_node(workflow: dict) -> dict | None:
    for node in workflow.get("nodes", []):
        if node.get("type") == "tracker" and node.get("enabled", True):
            node_id = str(node.get("id") or "tracker")
            if any(
                has_active_path(workflow, str(inf_node.get("id") or ""), node_id)
                for inf_node in active_inference_nodes(workflow)
                if inf_node.get("type") in ("detector", "segmenter")
            ):
                return node
    return None


def active_vlm_box_tracker_node(workflow: dict) -> dict | None:
    input_id = source_node_id(workflow)
    for node in workflow.get("nodes", []):
        if node.get("type") == "vlm_box_tracker" and node.get("enabled", True):
            node_id = str(node.get("id") or "vlm_box_tracker")
            if has_active_path(workflow, input_id, node_id) or not workflow.get("edges"):
                return node
    return None


def active_ai_agent_nodes(workflow: dict) -> list[dict]:
    input_id = source_node_id(workflow)
    nodes = []
    for node in workflow.get("nodes", []):
        if node.get("type") == "ai_agent" and node.get("enabled", True):
            node_id = str(node.get("id") or "ai_agent")
            if has_active_path(workflow, input_id, node_id) or not workflow.get("edges"):
                nodes.append(node)
    return nodes


def active_track_snapshot_nodes(workflow: dict) -> list[dict]:
    """Return enabled Once Per Track nodes reached from the active tracker."""
    tracker = active_tracking_node(workflow)
    if not tracker:
        return []
    tracker_id = str(tracker.get("id") or "tracker")
    return [
        node for node in workflow.get("nodes", [])
        if node.get("type") == "track_snapshot"
        and node.get("enabled", True)
        and has_active_path(workflow, tracker_id, str(node.get("id") or ""))
    ]


def active_object_counter_nodes(workflow: dict) -> list[dict]:
    """Return enabled counters reached from tracker or detector/source."""
    tracker = active_tracking_node(workflow)
    tracker_id = str(tracker.get("id") or "tracker") if tracker else None
    input_id = source_node_id(workflow)
    return [
        node for node in workflow.get("nodes", [])
        if node.get("type") == "object_counter"
        and node.get("enabled", True)
        and (
            (tracker_id and has_active_path(workflow, tracker_id, str(node.get("id") or "")))
            or (input_id and has_active_path(workflow, input_id, str(node.get("id") or "")))
            or not workflow.get("edges")
        )
    ]


def object_event_upstream_of(workflow: dict, target_id: str) -> bool:
    """Return whether a target consumes a sparse snapshot/count event path."""
    return any(
        has_active_path(workflow, str(node.get("id") or ""), target_id)
        for node in (*active_track_snapshot_nodes(workflow), *active_object_counter_nodes(workflow))
    )


def project_event_upstream_of(workflow: dict, target_id: str) -> bool:
    return any(node.get("type") in ("zone_activity_timer", "zone_exit_event")
               and node.get("enabled", True)
               and has_active_path(workflow, str(node.get("id") or ""), target_id)
               for node in workflow.get("nodes", []))


def track_driven_detection_crop_nodes(workflow: dict) -> list[dict]:
    """Detection Crop nodes gated by a nearby Once Per Track event stream.

    The gate may be drawn before the crop (Tracker -> Once -> Crop) or after
    it (Tracker -> Crop -> Once).  Cropping is executed after the gate in both
    cases so the observable graph behavior is one crop per emitted track.
    """
    snapshots = active_track_snapshot_nodes(workflow)
    return [
        crop for crop in active_detection_crop_nodes(workflow)
        if any(
            (
                has_active_path(
                    workflow,
                    str(snapshot.get("id") or ""),
                    str(crop.get("id") or ""),
                )
                or has_active_path(
                    workflow,
                    str(crop.get("id") or ""),
                    str(snapshot.get("id") or ""),
                )
            )
            for snapshot in snapshots
        )
    ]


def active_pretracking_detection_crop_bindings(workflow: dict) -> list[tuple[dict, dict]]:
    """Crop/classifier bindings that consume detector results before tracking."""
    driven_ids = {
        str(node.get("id") or "") for node in track_driven_detection_crop_nodes(workflow)
    }
    return [
        (crop, classifier)
        for crop, classifier in active_detection_crop_bindings(workflow)
        if str(crop.get("id") or "") not in driven_ids
    ]


def _configured_values(value: object) -> set[str]:
    return {
        item.strip().casefold()
        for item in str(value or "").replace("\n", ",").split(",")
        if item.strip()
    }


def _expire_track_state(state: dict, now: float, retention_seconds: float) -> None:
    last_seen = state.setdefault("last_seen", {})
    expired = [
        key for key, seen_at in last_seen.items()
        if now - float(seen_at) > retention_seconds
    ]
    for key in expired:
        last_seen.pop(key, None)
        state.setdefault("emitted", {}).pop(key, None)
        state.setdefault("ages", {}).pop(key, None)
        state.setdefault("counted", {}).pop(key, None)


def emit_track_snapshots(
    node: dict,
    detections: list[dict],
    runtime: dict,
    now: float | None = None,
) -> list[dict]:
    """Emit each eligible tracked object exactly once for this node."""
    now = time.monotonic() if now is None else now
    node_id = str(node.get("id") or "track_snapshot")
    state = runtime.setdefault(node_id, {})
    config = node.get("config", {})
    retention = max(1.0, float(config.get("retentionSeconds", 3600) or 3600))
    _expire_track_state(state, now, retention)
    wanted_ids = _configured_values(config.get("trackIds", ""))
    wanted_classes = _configured_values(config.get("classes", ""))
    minimum_score = max(0.0, float(config.get("minimumConfidence", 0.0) or 0.0))
    minimum_age = max(1, int(config.get("minimumTrackAgeFrames", 1) or 1))
    emitted = state.setdefault("emitted", {})
    ages = state.setdefault("ages", {})
    last_seen = state.setdefault("last_seen", {})
    output = []
    for detection in detections:
        key = _detection_track_key(detection)
        if key is None:
            continue
        last_seen[key] = now
        observed_age = detection.get("trackAgeFrames")
        if observed_age is None:
            ages[key] = int(ages.get(key, 0)) + 1
        else:
            ages[key] = max(int(ages.get(key, 0)), int(observed_age))
        track_id = str(detection.get("trackId"))
        label = str(detection.get("class", "object"))
        if wanted_ids and track_id.casefold() not in wanted_ids:
            continue
        if wanted_classes and label.casefold() not in wanted_classes:
            continue
        if float(detection.get("score", 0.0) or 0.0) < minimum_score:
            continue
        if ages[key] < minimum_age or key in emitted:
            continue
        emitted[key] = now
        event = dict(detection)
        event.update({
            "kind": "track_snapshot",
            "sourceNodeId": node_id,
            "parentSourceNodeId": str(detection.get("sourceNodeId") or "tracker"),
            "snapshotTimestamp": now,
        })
        output.append(event)
    return output


def observe_track_ages(
    node: dict,
    detections: list[dict],
    runtime: dict,
    now: float | None = None,
) -> list[dict]:
    """Annotate tracks with their age before an ROI/event gate filters them."""
    now = time.monotonic() if now is None else now
    node_id = str(node.get("id") or "track_snapshot")
    state = runtime.setdefault(node_id, {})
    retention = max(
        1.0,
        float(node.get("config", {}).get("retentionSeconds", 3600) or 3600),
    )
    _expire_track_state(state, now, retention)
    ages = state.setdefault("ages", {})
    last_seen = state.setdefault("last_seen", {})
    output = []
    for detection in detections:
        key = _detection_track_key(detection)
        if key is None:
            continue
        ages[key] = int(ages.get(key, 0)) + 1
        last_seen[key] = now
        observed = dict(detection)
        observed["trackAgeFrames"] = ages[key]
        output.append(observed)
    return output


def emit_object_count_events(
    node: dict,
    detections: list[dict],
    runtime: dict,
    now: float | None = None,
) -> list[dict]:
    """Convert detections into durable count events and maintain class/total counts."""
    now = time.monotonic() if now is None else now
    node_id = str(node.get("id") or "object_counter")
    state = runtime.setdefault(node_id, {})
    config = node.get("config", {})
    retention = max(1.0, float(config.get("retentionSeconds", 3600) or 3600))
    _expire_track_state(state, now, retention)
    wanted_classes = _configured_values(config.get("classes", ""))
    count_once = bool(config.get("countOncePerTrack", True))
    counted = state.setdefault("counted", {})
    last_seen = state.setdefault("last_seen", {})
    class_counts = state.setdefault("class_counts", {})
    frame_counts: dict[str, int] = {}
    total = int(state.get("total_count", 0))
    output = []
    mode = str(config.get("mode", "occupancy")).lower()
    max_capacity = int(config.get("maxCapacity", 0) or 0)
    for detection in detections:
        cls_name = str(detection.get("class", "object")).strip()
        if wanted_classes and cls_name.casefold() not in wanted_classes:
            continue
        frame_counts[cls_name] = frame_counts.get(cls_name, 0) + 1

        key = _detection_track_key(detection)
        if key is not None:
            last_seen[key] = now
            if count_once and key in counted:
                continue
            counted[key] = now
            total += 1
            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
            event = dict(detection)
            event.update({
                "kind": "count_event",
                "sourceNodeId": node_id,
                "parentSourceNodeId": str(detection.get("sourceNodeId") or "tracker"),
                "counterNodeId": node_id,
                "objectCount": total,
                "classCounts": dict(class_counts),
                "countTimestamp": now,
            })
            output.append(event)
        else:
            # Standalone counter without tracker: count current frame
            if not count_once:
                total += 1
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

    live_occupancy = sum(frame_counts.values())
    is_overcapacity = max_capacity > 0 and live_occupancy >= max_capacity
    if is_overcapacity:
        if not state.get("capacity_alerted", False):
            state["capacity_alerted"] = True
            output.append({
                "kind": "overcapacity_alert",
                "sourceNodeId": node_id,
                "counterNodeId": node_id,
                "occupancy": live_occupancy,
                "maxCapacity": max_capacity,
                "classCounts": dict(frame_counts),
                "timestamp": now,
            })
    elif live_occupancy < max_capacity:
        state["capacity_alerted"] = False

    state["mode"] = mode
    state["live_occupancy"] = live_occupancy
    state["cumulative_count"] = total if counted else live_occupancy
    state["total_count"] = live_occupancy if mode == "occupancy" else (total if counted else live_occupancy)
    state["frame_counts"] = frame_counts
    state["display_counts"] = dict(frame_counts) if mode == "occupancy" else (dict(class_counts) if counted else dict(frame_counts))
    state["max_capacity"] = max_capacity
    state["is_overcapacity"] = is_overcapacity
    return output


def tracking_input_threshold(workflow: dict, inference_node: dict) -> float:
    """Lowest detector score needed by a downstream tracker.

    Detector previews retain their configured threshold.  The AI model is run
    low enough for ByteTrack/BoT-SORT recovery detections or OC-SORT's single
    library confidence threshold.
    """
    config = inference_node.get("config", {})
    display_threshold = _clamp_probability(config.get("threshold", 0.55), 0.55)
    if inference_node.get("type") == "efficientad":
        return 0.0
    if inference_node.get("type") == "classifier":
        return display_threshold
    tracker = active_tracking_node(workflow)
    if not tracker:
        return display_threshold
    tracker_id = str(tracker.get("id") or "tracker")
    inference_id = str(
        inference_node.get("id") or inference_node.get("type") or "detector"
    )
    if not has_active_path(workflow, inference_id, tracker_id):
        return display_threshold
    tracker_config = tracker.get("config", {})
    algorithm = str(tracker_config.get("algorithm", "bytetrack")).lower()
    if algorithm in ("bytetrack", "botsort", "cbiou"):
        tracker_threshold = _clamp_probability(
            tracker_config.get("trackLowThreshold", 0.1),
            0.1,
        )
    elif algorithm == "ocsort":
        tracker_threshold = _clamp_probability(
            tracker_config.get("ocSortDetectionThreshold", 0.6),
            0.6,
        )
    else:
        return display_threshold
    return min(display_threshold, tracker_threshold)


def inference_node_with_threshold(inference_node: dict, threshold: float) -> dict:
    """Return a shallow node copy with an inference-only score threshold."""
    if inference_node.get("type") == "efficientad":
        return inference_node
    current = float(inference_node.get("config", {}).get("threshold", 0.55))
    if math.isclose(current, float(threshold), rel_tol=0.0, abs_tol=1e-9):
        return inference_node
    return {
        **inference_node,
        "config": {
            **inference_node.get("config", {}),
            "threshold": float(threshold),
        },
    }


def _clamp_probability(value, fallback: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return fallback


def active_filter_node(workflow: dict) -> dict | None:
    filter_node = enabled_node(workflow, "filter")
    upstream_nodes = active_inference_nodes(workflow)
    tracker = active_tracking_node(workflow)
    if tracker:
        upstream_nodes.append(tracker)
    if filter_node and any(has_active_path(workflow, node.get("id"), "filter") for node in upstream_nodes):
        return filter_node
    return None


def inference_results_for_node(workflow: dict, node_id: str, detections: list[dict]) -> list[dict]:
    def path_avoids(from_id: str, blocked_ids: set[str]) -> bool:
        if from_id == node_id:
            return True
        visited: set[str] = set()
        queue = [from_id]
        while queue:
            current_id = queue.pop(0)
            if current_id == node_id:
                return True
            if current_id in visited:
                continue
            visited.add(current_id)
            for edge in workflow.get("edges", []):
                if len(edge) < 2:
                    continue
                edge_from, edge_to = str(edge[0]), str(edge[1])
                if (
                    edge_from == current_id
                    and edge_to not in visited
                    and edge_to not in blocked_ids
                    and enabled_node(workflow, edge_to)
                ):
                    queue.append(edge_to)
        return False

    results = []
    bindings = active_detection_crop_bindings(workflow)
    for detection in detections:
        source_id = str(detection.get("sourceNodeId") or "detector")
        if not has_active_path(workflow, source_id, node_id):
            continue
        if detection.get("kind") in ("detection", "segmentation"):
            cascade_crop_ids = {
                str(crop.get("id") or "")
                for crop, classifier in bindings
                if (
                    has_active_path(workflow, source_id, str(crop.get("id") or ""))
                    and has_active_path(workflow, str(classifier.get("id") or ""), node_id)
                )
            }
            # A detector-only branch still exposes its original results.  On a
            # detector -> crop -> classifier branch, the mapped classification
            # replaces the upstream box to avoid drawing duplicate labels.
            if cascade_crop_ids and not path_avoids(source_id, cascade_crop_ids):
                continue
        results.append(detection)
    return results


def tracking_results_for_node(workflow: dict, node_id: str, tracked: list[dict]) -> list[dict]:
    tracker = active_tracking_node(workflow) or active_vlm_box_tracker_node(workflow)
    if not tracker:
        return []
    tracker_id = str(tracker.get("id") or tracker.get("type") or "tracker")
    if not has_active_path(workflow, tracker_id, node_id):
        return []
    return [
        detection for detection in tracked
        if detection.get("trackId") is not None
        and has_active_path(workflow, detection.get("sourceNodeId", tracker_id), node_id)
    ]


def results_for_node(
    workflow: dict,
    node_id: str,
    detections: list[dict],
    tracked: list[dict] | None = None,
) -> list[dict]:
    # Project nodes emit sparse business events for action outputs. Never
    # replace an empty event batch with the continuous detector/tracker stream.
    target = enabled_node(workflow, node_id)
    ai_agent_sources = {
        str(node.get("id") or "") for node in workflow.get("nodes", [])
        if node.get("type") == "ai_agent"
        and node.get("enabled", True)
        and str(node.get("id") or "") != node_id
        and has_active_path(workflow, str(node.get("id") or ""), node_id)
    }
    if ai_agent_sources and target and target.get("type") in (
        "alert", "webhook_output", "image_output", "database_output",
    ):
        events = [item for item in detections
                  if item.get("kind") == "ai_agent_event"
                  and str(item.get("sourceNodeId") or "") in ai_agent_sources]
        return [item for item in events if item.get("passDownstream", True)]

    project_sources = {
        str(node.get("id") or "") for node in workflow.get("nodes", [])
        if node.get("type") in ("zone_activity_timer", "zone_exit_event", "multi_zone_occupancy")
        and node.get("enabled", True)
        and str(node.get("id") or "") != node_id
        and has_active_path(workflow, str(node.get("id") or ""), node_id)
    }
    if project_sources and target and target.get("type") in (
        "alert", "webhook_output", "image_output", "database_output", "ai_agent",
    ):
        events = [item for item in detections
                  if item.get("kind") in ("zone_activity_event", "zone_exit", "zone_occupied", "zone_vacated", "zone_overstay")
                  and str(item.get("sourceNodeId") or "") in project_sources]
        return filter_project_inputs(workflow, node_id, events, after_sources=project_sources)
    tracker = active_tracking_node(workflow) or active_vlm_box_tracker_node(workflow)
    tracker_id = str(tracker.get("id") or tracker.get("type") or "tracker") if tracker else "tracker"
    if tracker and tracked is not None and has_active_path(workflow, tracker_id, node_id):
        blocked_ids = {
            str(node.get("id") or "")
            for node in workflow.get("nodes", [])
            if node.get("type") in ("track_snapshot",)
        }
        blocked_ids.discard(str(node_id))

        def tracker_has_continuous_path() -> bool:
            queue = [tracker_id]
            visited = set()
            while queue:
                current = queue.pop(0)
                if current == node_id:
                    return True
                if current in visited:
                    continue
                visited.add(current)
                for edge in workflow.get("edges", []):
                    if len(edge) < 2:
                        continue
                    edge_from, edge_to = str(edge[0]), str(edge[1])
                    if (
                        edge_from == current
                        and edge_to not in visited
                        and edge_to not in blocked_ids
                        and enabled_node(workflow, edge_to)
                    ):
                        queue.append(edge_to)
            return False

        results = (
            tracking_results_for_node(workflow, node_id, tracked)
            if tracker_has_continuous_path()
            else []
        )
        # Stateful object-event nodes and post-track crop classifiers produce
        # sparse event records in ``detections``.  Preserve those records for
        # downstream alerts/databases instead of replacing them with the
        # continuous tracker stream.
        event_kinds = {"track_snapshot", "count_event", "line_crossing", "loitering_alert", "object_classification", "anomaly", "zone_activity", "zone_activity_event", "zone_exit"}
        results.extend(
            item for item in detections
            if item.get("kind") in event_kinds
            and has_active_path(
                workflow,
                str(item.get("sourceNodeId") or ""),
                node_id,
            )
        )
        return results
    return inference_results_for_node(workflow, node_id, detections)


def detections_for_node(
    workflow: dict,
    node_id: str,
    detections: list[dict],
    filtered: list[dict],
    tracked: list[dict] | None = None,
) -> list[dict]:
    if node_id == "auto_preview":
        tracker = active_tracking_node(workflow)
        if tracker and tracked is not None and has_active_path(
            workflow, str(tracker.get("id") or "tracker"), node_id
        ):
            return tracking_results_for_node(workflow, node_id, tracked)
        return tracked if tracked is not None else (filtered if filtered is not None else detections)
    node = enabled_node(workflow, node_id)
    input_id = source_node_id(workflow)
    if not node or not has_active_path(workflow, input_id, node_id):
        return []
    if active_filter_node(workflow) and has_active_path(workflow, "filter", node_id) and not any(
        node.get("type") in ("zone_activity_timer", "zone_exit_event")
        and node.get("enabled", True)
        and has_active_path(workflow, str(node.get("id") or ""), node_id)
        for node in workflow.get("nodes", [])
    ):
        return filtered
    return results_for_node(workflow, node_id, detections, tracked)


def _compare_logic_value(left: float, operator: object, right: float) -> bool:
    """Evaluate a comparison configured by a Logic node."""
    return {
        "eq": left == right,
        "ne": left != right,
        "gt": left > right,
        "gte": left >= right,
        "lt": left < right,
        "lte": left <= right,
    }.get(str(operator), left >= right)


def _roi_rect(config: dict) -> tuple[float, float, float, float] | None:
    try:
        x1 = max(0.0, float(config.get("x", 0)))
        y1 = max(0.0, float(config.get("y", 0)))
        width = float(config.get("width", 0))
        height = float(config.get("height", 0))
    except (TypeError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    return x1, y1, x1 + width, y1 + height


def _roi_polygon(config: dict) -> list[tuple[float, float]] | None:
    raw_points = config.get("points", [])
    if not isinstance(raw_points, list):
        return None
    points: list[tuple[float, float]] = []
    for item in raw_points:
        try:
            x, y = item[:2]
            points.append((max(0.0, float(x)), max(0.0, float(y))))
        except (TypeError, ValueError):
            continue
    return points if len(points) >= 3 else None


def _roi_geometry(config: dict) -> tuple[str, object] | None:
    if config.get("shape") == "polygon":
        polygon = _roi_polygon(config)
        return ("polygon", polygon) if polygon is not None else None
    rect = _roi_rect(config)
    return ("rectangle", rect) if rect is not None else None


def _point_in_rect(point: tuple[float, float], rect: tuple[float, float, float, float]) -> bool:
    x, y = point
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2


def _point_on_segment(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> bool:
    px, py = point
    x1, y1 = start
    x2, y2 = end
    cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    if abs(cross) > 1e-6:
        return False
    return min(x1, x2) - 1e-6 <= px <= max(x1, x2) + 1e-6 and min(y1, y2) - 1e-6 <= py <= max(y1, y2) + 1e-6


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    previous = polygon[-1]
    for current in polygon:
        if _point_on_segment(point, previous, current):
            return True
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y):
            intersect_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x <= intersect_x:
                inside = not inside
        previous = current
    return inside


def _segments_intersect(
    a1: tuple[float, float],
    a2: tuple[float, float],
    b1: tuple[float, float],
    b2: tuple[float, float],
) -> bool:
    def orientation(p, q, r) -> float:
        return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

    o1 = orientation(a1, a2, b1)
    o2 = orientation(a1, a2, b2)
    o3 = orientation(b1, b2, a1)
    o4 = orientation(b1, b2, a2)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    return (
        abs(o1) <= 1e-6 and _point_on_segment(b1, a1, a2)
        or abs(o2) <= 1e-6 and _point_on_segment(b2, a1, a2)
        or abs(o3) <= 1e-6 and _point_on_segment(a1, b1, b2)
        or abs(o4) <= 1e-6 and _point_on_segment(a2, b1, b2)
    )


def _rect_corners(rect: tuple[float, float, float, float]) -> list[tuple[float, float]]:
    x1, y1, x2, y2 = rect
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def _rect_edges(rect: tuple[float, float, float, float]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    corners = _rect_corners(rect)
    return list(zip(corners, corners[1:] + corners[:1]))


def _polygon_edges(polygon: list[tuple[float, float]]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    return list(zip(polygon, polygon[1:] + polygon[:1]))


def _rect_overlaps_polygon(rect: tuple[float, float, float, float], polygon: list[tuple[float, float]]) -> bool:
    if any(_point_in_polygon(corner, polygon) for corner in _rect_corners(rect)):
        return True
    if any(_point_in_rect(point, rect) for point in polygon):
        return True
    return any(
        _segments_intersect(rect_edge[0], rect_edge[1], poly_edge[0], poly_edge[1])
        for rect_edge in _rect_edges(rect)
        for poly_edge in _polygon_edges(polygon)
    )


def _detection_in_roi(detection: dict, roi: tuple[str, object], match: object) -> bool:
    bbox = detection.get("bbox")
    if not bbox or len(bbox) < 4:
        return False
    try:
        x, y, width, height = [float(value) for value in bbox[:4]]
    except (TypeError, ValueError):
        return False
    if width <= 0 or height <= 0:
        return False
    box = (x, y, x + width, y + height)
    bx1, by1, bx2, by2 = box
    shape, geometry = roi
    match_mode = str(match or "bottom_center").lower()

    if shape == "polygon":
        polygon = geometry
        if not isinstance(polygon, list):
            return False
        if match_mode in ("overlap", "bbox_overlap"):
            return _rect_overlaps_polygon(box, polygon)
        if match_mode == "contained":
            return all(_point_in_polygon(corner, polygon) for corner in _rect_corners(box))
        if match_mode == "bottom_center":
            pt = ((bx1 + bx2) / 2.0, by2)
        elif match_mode == "top_center":
            pt = ((bx1 + bx2) / 2.0, by1)
        else:
            pt = ((bx1 + bx2) / 2.0, (by1 + by2) / 2.0)
        return _point_in_polygon(pt, polygon)

    rx1, ry1, rx2, ry2 = geometry
    if match_mode in ("overlap", "bbox_overlap"):
        return min(bx2, rx2) > max(bx1, rx1) and min(by2, ry2) > max(by1, ry1)
    if match_mode == "contained":
        return bx1 >= rx1 and by1 >= ry1 and bx2 <= rx2 and by2 <= ry2
    if match_mode == "bottom_center":
        px, py = (bx1 + bx2) / 2.0, by2
    elif match_mode == "top_center":
        px, py = (bx1 + bx2) / 2.0, by1
    else:
        px, py = (bx1 + bx2) / 2.0, (by1 + by2) / 2.0
    return rx1 <= px <= rx2 and ry1 <= py <= ry2


def _detection_center(detection: dict, anchor: str = "bottom_center") -> tuple[float, float] | None:
    bbox = detection.get("bbox")
    if not bbox or len(bbox) < 4:
        return None
    try:
        x, y, width, height = [float(value) for value in bbox[:4]]
    except (TypeError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    cx = x + width / 2.0
    if anchor == "bottom_center":
        return (cx, y + height)
    elif anchor == "top_center":
        return (cx, y)
    return (cx, y + height / 2.0)


def _segment_intersects_roi(
    start: tuple[float, float],
    end: tuple[float, float],
    roi: tuple[str, object],
) -> bool:
    if start == end:
        return False
    shape, geometry = roi
    if shape == "polygon":
        polygon = geometry
        if not isinstance(polygon, list):
            return False
        return any(
            _segments_intersect(start, end, edge_start, edge_end)
            for edge_start, edge_end in _polygon_edges(polygon)
        )

    rect = geometry
    if not isinstance(rect, tuple):
        return False
    return any(
        _segments_intersect(start, end, edge_start, edge_end)
        for edge_start, edge_end in _rect_edges(rect)
    )


def filter_detections_by_roi(node: dict, detections: list[dict]) -> list[dict]:
    config = node.get("config", {})
    roi = _roi_geometry(config)
    if roi is None:
        return []
    match = config.get("triggerAnchor") or config.get("match", "bottom_center")
    invert_zone = bool(config.get("invertZone", False))
    filtered = []
    for item in detections:
        inside = _detection_in_roi(item, roi, match)
        if (not inside if invert_zone else inside):
            filtered.append(item)
    return filtered


def _detection_track_key(detection: dict) -> str | None:
    track_id = detection.get("trackId")
    if track_id is None:
        return None
    return f"{detection.get('sourceNodeId', 'tracker')}:{track_id}"


def _roi_crossing_event(
    previous_inside: bool | None,
    inside: bool,
    previous_center: tuple[float, float] | None,
    current_center: tuple[float, float] | None,
    roi: tuple[str, object],
    direction: object,
) -> str | None:
    if previous_inside is None:
        return "enter" if inside and direction in ("enter", "both") else None
    if previous_inside != inside:
        return "enter" if inside else "exit"
    if (
        not previous_inside
        and not inside
        and previous_center is not None
        and current_center is not None
        and _segment_intersects_roi(previous_center, current_center, roi)
    ):
        return "exit" if direction == "exit" else "enter"
    return None


def apply_roi_node(
    node: dict,
    detections: list[dict],
    runtime: dict,
    now: float,
) -> list[dict]:
    """Apply an ROI logic node.

    Inside mode returns the detections currently inside the ROI. Crossing mode
    returns only tracked detections that crossed the ROI boundary this frame
    and keeps a cumulative count in the node runtime state.
    """
    config = node.get("config", {})
    if config.get("mode", "inside") != "crossing":
        return filter_detections_by_roi(node, detections)

    node_id = str(node.get("id") or node.get("type") or "roi_filter")
    state = runtime.setdefault(node_id, {})
    if state.get("last_crossing_at") == now:
        return list(state.get("last_crossing_output", []))

    roi = _roi_geometry(config)
    if roi is None:
        state["last_crossing_at"] = now
        state["last_crossing_output"] = []
        return []

    match = config.get("triggerAnchor") or config.get("match", "bottom_center")
    direction = config.get("crossingDirection", "enter")
    inside_by_track = state.setdefault("inside_by_track", {})
    center_by_track = state.setdefault("center_by_track", {})
    last_seen_at = state.setdefault("last_seen_at", {})
    total_count = int(state.get("total_count", 0))
    output = []
    current_keys = set()

    for detection in detections:
        track_key = _detection_track_key(detection)
        if track_key is None:
            continue
        current_keys.add(track_key)
        inside = _detection_in_roi(detection, roi, match)
        current_center = _detection_center(detection)
        previous_inside = inside_by_track.get(track_key)
        previous_center = center_by_track.get(track_key)
        event_type = _roi_crossing_event(
            previous_inside,
            inside,
            previous_center,
            current_center,
            roi,
            direction,
        )
        inside_by_track[track_key] = inside
        center_by_track[track_key] = current_center
        last_seen_at[track_key] = now
        if event_type is None or direction not in (event_type, "both"):
            continue
        total_count += 1
        event_detection = dict(detection)
        event_detection["roiEvent"] = event_type
        event_detection["roiNodeId"] = node_id
        event_detection["roiTotalCount"] = total_count
        output.append(event_detection)

    stale_after_seconds = 30.0
    stale_keys = [
        key for key, seen_at in last_seen_at.items()
        if key not in current_keys and now - float(seen_at) > stale_after_seconds
    ]
    for key in stale_keys:
        last_seen_at.pop(key, None)
        inside_by_track.pop(key, None)
        center_by_track.pop(key, None)

    state["total_count"] = total_count
    state["last_crossing_at"] = now
    state["last_crossing_output"] = list(output)
    return output


def _logic_only_path(workflow: dict, from_id: str, to_id: str) -> bool:
    """Return whether ``from_id`` can reach ``to_id`` through Logic nodes only.

    This makes a gate apply at the next regular data node. A gate before a
    Class Filter is therefore not evaluated a second time for a downstream
    Preview or Alert.
    """
    if from_id == to_id:
        return True
    visited = set()
    queue = [from_id]
    while queue:
        current_id = queue.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)
        for edge in workflow.get("edges", []):
            if len(edge) < 2 or edge[0] != current_id:
                continue
            target_id = edge[1]
            if target_id == to_id:
                return True
            target = enabled_node(workflow, target_id)
            if target and target.get("type") in LOGIC_NODE_TYPES:
                queue.append(target_id)
    return False


def active_logic_nodes_for_target(workflow: dict, target_id: str) -> list[dict]:
    """Return enabled Logic gates immediately upstream of a data node.

    The nodes are ordered by their Logic-to-Logic edges so a chain is evaluated
    left-to-right even when nodes were created in another order.
    """
    input_id = source_node_id(workflow)
    sources = [node.get("id", "") for node in active_inference_nodes(workflow)]
    tracker = active_tracking_node(workflow)
    filter_node = active_filter_node(workflow)
    if tracker:
        sources.append(tracker.get("id", ""))
    if filter_node:
        sources.append(filter_node.get("id", ""))
    if input_id:
        sources.append(input_id)
    for n in workflow.get("nodes", []):
        if n.get("type") in ("line_counter", "object_counter", "dwell_time", "barcode_reader", "crop", "roi_filter", "zone_activity_timer", "zone_exit_event") and n.get("enabled", True):
            sources.append(str(n.get("id", "")))

    nodes = [
        node for node in workflow.get("nodes", [])
        if node.get("type") in LOGIC_NODE_TYPES
        and node.get("enabled", True)
        and any(has_active_path(workflow, source_id, str(node.get("id", ""))) for source_id in sources if source_id)
        and _logic_only_path(workflow, str(node.get("id", "")), target_id)
    ]
    node_ids = {node.get("id") for node in nodes}
    order_hint = {node.get("id"): index for index, node in enumerate(nodes)}
    incoming = {node_id: 0 for node_id in node_ids}
    outgoing = {node_id: [] for node_id in node_ids}
    for edge in workflow.get("edges", []):
        if len(edge) >= 2 and edge[0] in node_ids and edge[1] in node_ids:
            outgoing[edge[0]].append(edge[1])
            incoming[edge[1]] += 1
    ready = sorted((node_id for node_id, degree in incoming.items() if degree == 0), key=order_hint.get)
    ordered_ids = []
    while ready:
        node_id = ready.pop(0)
        ordered_ids.append(node_id)
        for next_id in outgoing[node_id]:
            incoming[next_id] -= 1
            if incoming[next_id] == 0:
                ready.append(next_id)
                ready.sort(key=order_hint.get)
    ordered_ids.extend(node.get("id") for node in nodes if node.get("id") not in ordered_ids)
    lookup = {node.get("id"): node for node in nodes}
    return [lookup[node_id] for node_id in ordered_ids]


def _object_detection_count(detections: list[dict]) -> int:
    real_objects = [item for item in detections if item.get("kind") not in ("line_crossing", "count_event", "loitering_alert", "zone_activity", "zone_activity_event", "zone_exit")]
    boxed = [item for item in real_objects if _detection_box_xywh(item) is not None]
    return len(_overlay_objects(boxed)) + len(real_objects) - len(boxed)


def _logic_signal(node: dict, detections: list[dict], runtime: dict, now: float) -> bool:
    """Evaluate one Logic node against its current detection signal."""
    config = node.get("config", {})
    node_id = str(node.get("id") or node.get("type") or "logic")
    state = runtime.setdefault(node_id, {})
    node_type = node.get("type")
    count = len(detections)
    scores = [float(item.get("score", 0)) for item in detections]
    maximum = max(scores, default=0.0)
    signal = bool(detections)

    if node_type in ("if_else", "compare_value"):
        metric = str(config.get("metric", "object_count")).strip().lower()
        actual = 0.0

        if metric in ("object_count", "count"):
            actual = _object_detection_count(detections)
        elif metric in ("max_confidence", "confidence"):
            actual = maximum
        elif metric == "anomaly_score":
            anomaly_scores = [float(item["anomalyScore"]) for item in detections if item.get("kind") == "anomaly"]
            if not anomaly_scores:
                return False
            actual = max(anomaly_scores)
        elif metric in ("line_counter_in", "line_in"):
            ev_rt = runtime.get("_event_runtime", {})
            total_in = 0
            for k, v in ev_rt.items():
                if isinstance(v, dict):
                    total_in += v.get("total_in", v.get("count_in", 0))
            if total_in == 0:
                total_in = sum(1 for d in detections if d.get("kind") == "line_crossing" and d.get("direction") == "IN")
            actual = float(total_in)
        elif metric in ("line_counter_out", "line_out"):
            ev_rt = runtime.get("_event_runtime", {})
            total_out = 0
            for k, v in ev_rt.items():
                if isinstance(v, dict):
                    total_out += v.get("total_out", v.get("count_out", 0))
            if total_out == 0:
                total_out = sum(1 for d in detections if d.get("kind") == "line_crossing" and d.get("direction") == "OUT")
            actual = float(total_out)
        elif metric in ("line_counter_total", "line_total", "line_count"):
            ev_rt = runtime.get("_event_runtime", {})
            tot = 0
            for k, v in ev_rt.items():
                if isinstance(v, dict):
                    tot += v.get("total_in", v.get("count_in", 0)) + v.get("total_out", v.get("count_out", 0))
            if tot == 0:
                tot = sum(1 for d in detections if d.get("kind") == "line_crossing")
            actual = float(tot)
        elif metric == "line_crossing":
            crossing_count = sum(1 for d in detections if d.get("kind") == "line_crossing")
            actual = float(crossing_count)
        elif metric == "class_count":
            target_class = str(config.get("classes", "")).strip().casefold()
            if target_class:
                targets = [c.strip().casefold() for c in target_class.split(",") if c.strip()]
                actual = float(sum(1 for d in detections if str(d.get("class", "")).strip().casefold() in targets))
            else:
                actual = float(count)
        else:
            actual = float(count)

        comp_res = _compare_logic_value(actual, config.get("operator", "gte"), float(config.get("value", 1)))

        pass_when = str(config.get("passWhen", "true")).strip().lower()
        if node_type == "if_else" and pass_when in ("false", "else", "not", "f", "0"):
            signal = not comp_res
        else:
            signal = comp_res

        state["last_signal"] = signal
        state["actual_value"] = actual
        state["threshold_value"] = float(config.get("value", 1))
        state["metric"] = metric
        state["operator"] = config.get("operator", "gte")
        state["pass_when"] = pass_when
        state["last_eval_time"] = now
    elif node_type == "object_count_condition":
        signal = _compare_logic_value(_object_detection_count(detections), config.get("operator", "gte"), float(config.get("count", 1)))
    elif node_type == "class_detected_condition":
        wanted = {item.strip().casefold() for item in str(config.get("classes", "")).replace("\n", ",").split(",") if item.strip()}
        detected = {str(item.get("class", "")).casefold() for item in detections}
        signal = wanted.issubset(detected) if config.get("match", "any") == "all" else bool(wanted & detected)
    elif node_type == "confidence_threshold":
        matches = [_compare_logic_value(score, config.get("operator", "gte"), float(config.get("threshold", 0.55))) for score in scores]
        signal = bool(matches) and (all(matches) if config.get("match", "any") == "all" else any(matches))
    elif node_type == "timer_delay":
        if signal:
            state.setdefault("started_at", now)
            signal = now - state["started_at"] >= max(0.0, float(config.get("seconds", 1.0)))
        else:
            state.pop("started_at", None)
    elif node_type == "debounce":
        previous = state.get("input", signal)
        if previous != signal:
            state["input"] = signal
            state["changed_at"] = now
        state.setdefault("changed_at", now)
        signal = signal and now - state["changed_at"] >= max(0.0, float(config.get("seconds", 0.5)))
    elif node_type == "rate_limiter":
        if signal and now - state.get("last_pass_at", float("-inf")) >= max(0.0, float(config.get("seconds", 5.0))):
            state["last_pass_at"] = now
        else:
            signal = False
    elif node_type == "and_or_logic":
        static_input = bool(config.get("enabledValue", True))
        signal = signal and static_input if config.get("operator", "and") == "and" else signal or static_input
    elif node_type == "trigger_once":
        if not signal:
            if config.get("resetOnClear", True):
                state["triggered"] = False
        elif state.get("triggered", False):
            signal = False
        else:
            state["triggered"] = True
    state["last_signal"] = signal
    return signal


def apply_logic_nodes(
    workflow: dict,
    target_id: str,
    detections: list[dict],
    runtime: dict | None = None,
    now: float | None = None,
    debug_callback=None,
    *,
    crossing_passthrough: bool = False,
) -> list[dict]:
    """Apply the Logic gates directly upstream of ``target_id``.

    A passing gate preserves the current detection batch. A failing gate emits
    no batch, which suppresses the downstream Preview, Alert, Filter, or
    Tracking action for that frame.

    Crossing ROI nodes normally emit only the detections that crossed during
    this frame. Preview rendering can opt into pass-through mode so the counter
    is still updated while boxes, track IDs, and trails remain visible.
    """
    runtime = runtime if runtime is not None else {}
    now = time.monotonic() if now is None else now
    result = detections
    for node in active_logic_nodes_for_target(workflow, target_id):
        started_at = time.monotonic()
        if node.get("type") == "roi_filter":
            next_result = apply_roi_node(node, result, runtime, now)
            if crossing_passthrough and node.get("config", {}).get("mode", "inside") == "crossing":
                next_result = result
            passed = True
        else:
            passed = _logic_signal(node, result, runtime, now)
            next_result = result if passed else []
        if debug_callback:
            debug_callback(node, result, next_result, (time.monotonic() - started_at) * 1000, passed, target_id)
        if not passed:
            return []
        result = next_result
    return result


def normalize_camera_source(value) -> int | str:
    if value is None or value == "":
        return 0
    if isinstance(value, int):
        return value
    text = str(value).strip()
    return int(text) if text.isdigit() else text


def camera_backend_choices(cv2_module, source, config: dict) -> list[tuple[str, int | None]]:
    requested = str(
        config.get("cameraBackend")
        or os.environ.get("VISO_CAMERA_BACKEND")
        or "auto"
    ).strip().lower()
    backend_map = {
        "default": ("OpenCV default", None),
        "any": ("OpenCV default", None),
        "dshow": ("DirectShow", getattr(cv2_module, "CAP_DSHOW", None)),
        "directshow": ("DirectShow", getattr(cv2_module, "CAP_DSHOW", None)),
        "msmf": ("Media Foundation", getattr(cv2_module, "CAP_MSMF", None)),
        "mediafoundation": ("Media Foundation", getattr(cv2_module, "CAP_MSMF", None)),
        "v4l2": ("V4L2", getattr(cv2_module, "CAP_V4L2", None)),
    }
    if requested in backend_map:
        name, backend = backend_map[requested]
        if backend is None and requested not in ("default", "any"):
            return [("OpenCV default", None)]
        return [(name, backend)]

    if os.name == "nt" and isinstance(source, int):
        directshow = getattr(cv2_module, "CAP_DSHOW", None)
        if directshow is not None:
            return [("DirectShow", directshow), ("OpenCV default", None)]
    return [("OpenCV default", None)]


def resolve_file_input_path(value) -> Path:
    text = str(value or "").strip().strip('"')
    if not text:
        raise RuntimeError("File input path is empty.")
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.exists() or not path.is_file():
        raise RuntimeError(f"File input does not exist: {path}")
    return path


def read_image_file(cv2_module, path: Path):
    """Decode an image without passing a potentially non-ASCII path to OpenCV."""
    import numpy as np

    try:
        file_bytes = path.read_bytes()
    except OSError as exc:
        raise RuntimeError(
            f"Unable to read image file: {path}: {exception_message(exc)}"
        ) from exc
    if not file_bytes:
        raise RuntimeError(f"Image file is empty: {path}")

    try:
        image = cv2_module.imdecode(
            np.frombuffer(file_bytes, dtype=np.uint8),
            getattr(cv2_module, "IMREAD_COLOR", 1),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Unable to decode image file: {path}: {exception_message(exc)}"
        ) from exc
    if image is None:
        raise RuntimeError(f"Unable to decode image file: {path}")
    return image


def default_video_output_path() -> Path:
    return ROOT / "outputs" / f"visonode-output-{time.strftime('%Y%m%d-%H%M%S')}.mp4"


def resolve_video_output_path(value) -> Path:
    text = str(value or "").strip().strip('"')
    path = Path(text).expanduser() if text else default_video_output_path()
    if not path.suffix:
        path = path.with_suffix(".mp4")
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if path.suffix.lower() not in OUTPUT_VIDEO_EXTENSIONS:
        allowed = ", ".join(sorted(OUTPUT_VIDEO_EXTENSIONS))
        raise RuntimeError(f"Output video must use one of these extensions: {allowed}")
    if path.exists() and path.is_dir():
        raise RuntimeError(f"Output video path is a directory: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def output_video_fps(config: dict, input_fps: float) -> float:
    try:
        configured = float(config.get("outputFps", 0) or 0)
    except (TypeError, ValueError):
        configured = 0
    if configured > 0:
        return configured
    return input_fps if input_fps > 0 else 30.0


def output_video_fourcc(cv2_module, path: Path) -> int:
    suffix = path.suffix.lower()
    codec = "XVID" if suffix == ".avi" else "mp4v"
    return cv2_module.VideoWriter_fourcc(*codec)


class OpenCVVideoOutput:
    def __init__(self, cv2_module, config: dict, width: int, height: int, input_fps: float) -> None:
        self.cv2 = cv2_module
        self.config = config
        self.width = int(width)
        self.height = int(height)
        self.input_fps = input_fps
        self.writer = None
        self.path: Path | None = None
        self.fps = 0.0
        self.opened = False

    @property
    def enabled(self) -> bool:
        return bool(self.config.get("saveVideo", False))

    def open(self) -> tuple[Path, float] | None:
        if not self.enabled:
            return None
        if self.width <= 0 or self.height <= 0:
            raise RuntimeError("Cannot save video because the input frame size is unknown.")
        self.path = resolve_video_output_path(self.config.get("outputPath"))
        self.fps = output_video_fps(self.config, self.input_fps)
        self.writer = self.cv2.VideoWriter(
            str(self.path),
            output_video_fourcc(self.cv2, self.path),
            self.fps,
            (self.width, self.height),
        )
        if not self.writer.isOpened():
            raise RuntimeError(f"Unable to open output video for writing: {self.path}")
        self.opened = True
        return self.path, self.fps

    def write(self, frame) -> None:
        if self.writer is not None:
            self.writer.write(frame)

    def release(self) -> None:
        if self.writer is not None:
            self.writer.release()
            self.writer = None


def _positive_int(value, default: int = 0) -> int:
    try:
        return max(0, int(value or default))
    except (TypeError, ValueError):
        return default


def _positive_float(value, default: float = 0.0) -> float:
    try:
        return max(0.0, float(value or default))
    except (TypeError, ValueError):
        return default


class DahengInputSource:
    """Read Daheng Imaging cameras through the bundled gxipy SDK as BGR frames."""

    def __init__(self, cv2_module, config: dict) -> None:
        self.cv2 = cv2_module
        self.config = config
        self.gx = None
        self.manager = None
        self.device = None
        self.stream = None
        self.label = "Daheng Imaging camera"
        self._fps = 0.0
        self._width = 0
        self._height = 0
        self._streaming = False

    def open(self) -> tuple[str, int, int]:
        try:
            import gxipy as gx
        except ImportError as exc:
            raise RuntimeError(
                "Daheng Imaging input requires the bundled gxipy package and Daheng Galaxy SDK runtime."
            ) from exc

        self.gx = gx
        self.manager = gx.DeviceManager()
        device_count, device_info = self.manager.update_device_list()
        if device_count <= 0:
            raise RuntimeError("No Daheng Imaging camera was found.")

        self.device = self._open_device(device_count)
        if self.device is None:
            raise RuntimeError("Unable to open Daheng Imaging camera.")

        info = self._device_info(device_info)
        self.label = self._label_from_info(info)
        self._configure_device()
        self.device.stream_on()
        self._streaming = True
        self.stream = self.device.data_stream[0]
        self._width = self._feature_int("Width")
        self._height = self._feature_int("Height")
        self._fps = (
            self._feature_float("CurrentAcquisitionFrameRate")
            or self._feature_float("AcquisitionFrameRate")
        )
        return self.label, self.width, self.height

    def _open_device(self, device_count: int):
        mode = str(self.config.get("dahengOpenMode") or "index").strip().lower()
        identifier = str(self.config.get("dahengIdentifier") or "").strip()
        if mode == "sn" and identifier:
            return self.manager.open_device_by_sn(identifier)
        if mode in ("user_id", "user-id", "user") and identifier:
            return self.manager.open_device_by_user_id(identifier)
        if mode == "ip" and identifier:
            return self.manager.open_device_by_ip(identifier)
        if mode == "mac" and identifier:
            return self.manager.open_device_by_mac(identifier)

        index = _positive_int(identifier or self.config.get("source"), 1)
        index = min(max(1, index), device_count)
        return self.manager.open_device_by_index(index)

    def _device_info(self, device_info):
        if not isinstance(device_info, list) or not device_info:
            return {}
        mode = str(self.config.get("dahengOpenMode") or "index").strip().lower()
        identifier = str(self.config.get("dahengIdentifier") or "").strip()
        if mode == "index":
            index = _positive_int(identifier or self.config.get("source"), 1) - 1
            if 0 <= index < len(device_info):
                return device_info[index]
        lookup_key = {
            "sn": "sn",
            "user_id": "user_id",
            "user-id": "user_id",
            "user": "user_id",
            "ip": "ip",
            "mac": "mac",
        }.get(mode)
        if lookup_key and identifier:
            match = next((item for item in device_info if str(item.get(lookup_key) or "") == identifier), None)
            if match:
                return match
        return device_info[0]

    def _label_from_info(self, info: dict) -> str:
        model = str(info.get("model_name") or "Daheng Imaging").strip()
        parts = [model]
        for key in ("sn", "user_id", "ip"):
            value = str(info.get(key) or "").strip()
            if value:
                parts.append(value)
                break
        return "Daheng camera " + " ".join(parts)

    def _configure_device(self) -> None:
        gx = self.gx
        self._set_feature("AcquisitionMode", getattr(gx.GxAcquisitionModeEntry, "CONTINUOUS", 2))
        self._set_feature("TriggerMode", getattr(gx.GxSwitchEntry, "OFF", 0))
        width = _positive_int(self.config.get("width"), 0)
        height = _positive_int(self.config.get("height"), 0)
        if width > 0:
            self._set_feature("Width", width)
        if height > 0:
            self._set_feature("Height", height)
        frame_rate = _positive_float(self.config.get("dahengFrameRate"), 0.0)
        if frame_rate > 0:
            self._set_feature("AcquisitionFrameRateMode", getattr(gx.GxSwitchEntry, "ON", 1))
            self._set_feature("AcquisitionFrameRate", frame_rate)
        exposure = _positive_float(self.config.get("dahengExposureUs"), 0.0)
        if exposure > 0:
            self._set_feature("ExposureTime", exposure)
        gain = _positive_float(self.config.get("dahengGain"), 0.0)
        if gain > 0:
            self._set_feature("Gain", gain)

    def _set_feature(self, name: str, value) -> None:
        feature = getattr(self.device, name, None)
        setter = getattr(feature, "set", None)
        if callable(setter):
            try:
                setter(value)
            except Exception as exc:
                logger.warning("Could not set Daheng feature %s=%r: %s", name, value, exception_message(exc))

    def _feature_int(self, name: str) -> int:
        feature = getattr(self.device, name, None)
        getter = getattr(feature, "get", None)
        if callable(getter):
            try:
                return int(getter() or 0)
            except Exception:
                return 0
        return 0

    def _feature_float(self, name: str) -> float:
        feature = getattr(self.device, name, None)
        getter = getattr(feature, "get", None)
        if callable(getter):
            try:
                return max(0.0, float(getter() or 0))
            except Exception:
                return 0.0
        return 0.0

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def fps(self) -> float:
        return self._fps

    def read(self):
        if self.stream is None:
            return False, None
        timeout = _positive_int(self.config.get("dahengTimeoutMs"), 1000)
        raw_image = self.stream.get_image(timeout)
        if raw_image is None:
            return False, None
        frame = self._raw_image_to_bgr(raw_image)
        if frame is None:
            return False, None
        if not frame.flags["C_CONTIGUOUS"]:
            frame = frame.copy()
        return True, frame

    def _raw_image_to_bgr(self, raw_image):
        import numpy as np

        gx = self.gx
        try:
            rgb_image = raw_image.convert("RGB", channel_order=gx.DxRGBChannelOrder.ORDER_BGR)
            if rgb_image is not None:
                frame = rgb_image.get_numpy_array()
                return frame.copy() if frame is not None else None
        except Exception:
            pass

        gray = raw_image.get_numpy_array()
        if gray is None:
            return None
        if gray.dtype != np.uint8:
            max_value = (
                float(np.iinfo(gray.dtype).max)
                if np.issubdtype(gray.dtype, np.integer)
                else max(1.0, float(gray.max() or 1))
            )
            gray = np.clip(gray.astype(np.float32) * (255.0 / max_value), 0, 255).astype(np.uint8)
        return self.cv2.cvtColor(gray, self.cv2.COLOR_GRAY2BGR)

    def release(self) -> None:
        if self.device is not None:
            if self._streaming:
                try:
                    self.device.stream_off()
                except Exception:
                    pass
                self._streaming = False
            try:
                self.device.close_device()
            except Exception:
                pass
            self.device = None
        self.stream = None
        self.manager = None


class OpenCVInputSource:
    def __init__(self, cv2_module, config: dict) -> None:
        self.cv2 = cv2_module
        self.config = config
        self.capture = None
        self.daheng = None
        self.image = None
        self.loop = bool(config.get("loop", True))
        self.label = "input"
        self._finite_video = False
        self._frame_count = 0

    def open(self) -> tuple[str, int, int]:
        # Check if this input config is from an ip_camera node or has rtsp/http streamUrl
        stream_url = str(self.config.get("streamUrl") or "").strip()
        if stream_url:
            username = str(self.config.get("username") or "").strip()
            password = str(self.config.get("password") or "").strip()
            if username and "@" not in stream_url:
                # Inject credentials: rtsp://user:pass@host:port/path
                parts = stream_url.split("://", 1)
                if len(parts) == 2:
                    auth_prefix = f"{urllib.parse.quote(username)}:{urllib.parse.quote(password)}@" if password else f"{urllib.parse.quote(username)}@"
                    stream_url = f"{parts[0]}://{auth_prefix}{parts[1]}"
            self.loop = False
            self.label = f"IP Camera stream ({self.config.get('streamUrl')})"
            transport = str(self.config.get("transport", "tcp") or "tcp").lower()
            if transport == "tcp":
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
            elif transport == "udp":
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
            self.capture = self.cv2.VideoCapture(stream_url)
            self.capture.set(self.cv2.CAP_PROP_BUFFERSIZE, 1)
            if not self.capture.isOpened():
                self.capture.release()
                self.capture = None
                raise RuntimeError(f"Unable to connect to IP Camera stream: {self.config.get('streamUrl')}. Please verify camera IP, port, and credentials.")
            width = int(self.capture.get(self.cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(self.capture.get(self.cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            return self.label, width, height

        source_type = str(self.config.get("sourceType", "camera") or "camera").lower()
        if source_type == "daheng":
            self.loop = False
            self.daheng = DahengInputSource(self.cv2, self.config)
            label, width, height = self.daheng.open()
            self.label = label
            return label, width, height
        if source_type in ("file", "image", "video"):
            location = str(self.config.get("filePath") or "").strip().strip('"')
            if source_type in ("file", "video") and re.match(r"(?i)^https?:", location):
                try:
                    parsed = urlsplit(location)
                    if not parsed.netloc or not parsed.hostname:
                        raise ValueError("missing host")
                    parsed.port  # Validate an explicitly supplied port.
                except ValueError as exc:
                    raise RuntimeError("Enter a valid HTTP or HTTPS video file URL.") from exc
                self.label = location
                self.capture = self.cv2.VideoCapture(location)
                if not self.capture.isOpened():
                    self.capture.release()
                    self.capture = None
                    raise RuntimeError(
                        "Unable to open online video. Check that the URL is accessible "
                        "and links directly to a supported video file."
                    )
                return f"online video {location}", self.width, self.height
            path = resolve_file_input_path(self.config.get("filePath"))
            self.label = str(path)
            suffix = path.suffix.lower()
            if source_type == "image" and suffix not in IMAGE_EXTENSIONS:
                raise RuntimeError(f"Selected input is not a supported image file: {path}")
            if source_type == "video":
                if suffix in IMAGE_EXTENSIONS:
                    raise RuntimeError(f"Selected input is an image; choose Image input instead: {path}")
                if suffix not in VIDEO_EXTENSIONS:
                    raise RuntimeError(f"Selected input is not a supported video file: {path}")
            if suffix in IMAGE_EXTENSIONS:
                self.image = read_image_file(self.cv2, path)
                height, width = self.image.shape[:2]
                return f"image file {path}", width, height
            self.capture = self.cv2.VideoCapture(str(path))
            if not self.capture.isOpened():
                raise RuntimeError(f"Unable to open video file: {path}")
            self._frame_count = int(self.capture.get(self.cv2.CAP_PROP_FRAME_COUNT) or 0)
            self._finite_video = self._frame_count > 0
            return f"video file {path}", self.width, self.height

        source = normalize_camera_source(
            self.config.get("source", self.config.get("cameraIndex", self.config.get("deviceId", 0)))
        )
        backend_name = self._open_camera_capture(source)
        self.label = f"{source!r} via {backend_name}"
        self.capture.set(self.cv2.CAP_PROP_BUFFERSIZE, 1)
        width = int(self.config.get("width", 0) or 0)
        height = int(self.config.get("height", 0) or 0)
        if os.name == "nt" and backend_name == "DirectShow":
            fourcc_requested = str(self.config.get("fourcc") or "").strip()
            if fourcc_requested:
                self.capture.set(self.cv2.CAP_PROP_FOURCC, self.cv2.VideoWriter_fourcc(*fourcc_requested[:4]))
            else:
                self.capture.set(self.cv2.CAP_PROP_FOURCC, self.cv2.VideoWriter_fourcc(*"MJPG"))
        if width > 0:
            self.capture.set(self.cv2.CAP_PROP_FRAME_WIDTH, width)
        if height > 0:
            self.capture.set(self.cv2.CAP_PROP_FRAME_HEIGHT, height)
        # Verify camera can read a frame; if DirectShow with MJPG fails to read, fallback to native backend
        ok, _ = self.capture.read()
        if not ok and os.name == "nt" and backend_name == "DirectShow":
            self.capture.release()
            self.capture = self.cv2.VideoCapture(source)
            if width > 0:
                self.capture.set(self.cv2.CAP_PROP_FRAME_WIDTH, width)
            if height > 0:
                self.capture.set(self.cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.capture.isOpened():
            raise RuntimeError(f"Unable to open camera source {source!r}.")
        return f"camera source {self.label}", self.width, self.height

    def _open_camera_capture(self, source) -> str:
        for backend_name, backend in camera_backend_choices(self.cv2, source, self.config):
            if backend is None:
                capture = self.cv2.VideoCapture(source)
            else:
                capture = self.cv2.VideoCapture(source, backend)
            if capture.isOpened():
                self.capture = capture
                return backend_name
            capture.release()
        raise RuntimeError(f"Unable to open camera source {source!r}.")

    @property
    def width(self) -> int:
        if self.daheng is not None:
            return self.daheng.width
        if self.image is not None:
            return int(self.image.shape[1])
        return int(self.capture.get(self.cv2.CAP_PROP_FRAME_WIDTH) or 0) if self.capture is not None else 0

    @property
    def height(self) -> int:
        if self.daheng is not None:
            return self.daheng.height
        if self.image is not None:
            return int(self.image.shape[0])
        return int(self.capture.get(self.cv2.CAP_PROP_FRAME_HEIGHT) or 0) if self.capture is not None else 0

    @property
    def fps(self) -> float:
        if self.daheng is not None:
            return self.daheng.fps
        if self.capture is None:
            return 0.0
        try:
            return max(0.0, float(self.capture.get(self.cv2.CAP_PROP_FPS) or 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def is_static(self) -> bool:
        return self.image is not None

    @property
    def is_exhausted(self) -> bool:
        # ponytail: only classify known-length local files as EOF; unknown streams still fail loudly.
        if not self._finite_video or self.capture is None or self.loop:
            return False
        position = self.capture.get(self.cv2.CAP_PROP_POS_FRAMES)
        return position >= self._frame_count

    def read(self):
        if self.daheng is not None:
            return self.daheng.read()
        if self.image is not None:
            return True, self.image.copy()
        if self.capture is None:
            return False, None
        ok, frame = self.capture.read()
        if ok:
            return True, frame
        
        # If it's an IP Camera stream (streamUrl) with autoReconnect enabled, attempt reconnect
        stream_url = str(self.config.get("streamUrl") or "").strip()
        auto_reconnect = bool(self.config.get("autoReconnect", True))
        if stream_url and auto_reconnect:
            delay = max(0.5, float(self.config.get("reconnectDelaySeconds", 2.0) or 2.0))
            time.sleep(delay)
            try:
                if self.capture is not None:
                    self.capture.release()
                username = str(self.config.get("username") or "").strip()
                password = str(self.config.get("password") or "").strip()
                url_to_open = stream_url
                if username and "@" not in stream_url:
                    parts = stream_url.split("://", 1)
                    if len(parts) == 2:
                        auth_prefix = f"{urllib.parse.quote(username)}:{urllib.parse.quote(password)}@" if password else f"{urllib.parse.quote(username)}@"
                        url_to_open = f"{parts[0]}://{auth_prefix}{parts[1]}"
                self.capture = self.cv2.VideoCapture(url_to_open)
                self.capture.set(self.cv2.CAP_PROP_BUFFERSIZE, 1)
                if self.capture.isOpened():
                    reconnected_ok, reconnected_frame = self.capture.read()
                    if reconnected_ok:
                        return True, reconnected_frame
            except Exception:
                pass
            return False, None

        if not self.loop:
            return False, frame
        self.capture.set(self.cv2.CAP_PROP_POS_FRAMES, 0)
        return self.capture.read()

    def release(self) -> None:
        if self.daheng is not None:
            self.daheng.release()
            self.daheng = None
        if self.capture is not None:
            self.capture.release()


def _rfdetr_class_name(model, detections, index: int, class_id) -> str:
    data = getattr(detections, "data", {}) or {}
    for key in ("class_name", "class_names", "label", "labels"):
        labels = data.get(key)
        if labels is not None and index < len(labels):
            return str(labels[index])

    class_names = getattr(model, "class_names", {}) or {}
    try:
        class_key = int(class_id)
    except (TypeError, ValueError):
        return "object"
    return str(class_names.get(class_key, str(class_key)))


def _rfdetr_results_to_detections(model, results, inference_node: dict) -> list[dict]:
    import cv2
    import numpy as np

    source_node_id = inference_node.get("id", "detector")
    node_type = inference_node.get("type", "detector")
    if results is None:
        return []

    xyxy = getattr(results, "xyxy", None)
    if xyxy is None:
        return []
    boxes = np.asarray(xyxy).tolist()
    confidences = getattr(results, "confidence", None)
    scores = np.asarray(confidences).tolist() if confidences is not None else [1.0] * len(boxes)
    class_ids_raw = getattr(results, "class_id", None)
    class_ids = np.asarray(class_ids_raw).tolist() if class_ids_raw is not None else [None] * len(boxes)
    masks = getattr(results, "mask", None)

    detections = []
    for index, box in enumerate(boxes):
        if len(box) < 4:
            continue
        x1, y1, x2, y2 = [float(value) for value in box[:4]]
        class_id = class_ids[index] if index < len(class_ids) else None
        score = scores[index] if index < len(scores) else 1.0
        class_name = _rfdetr_class_name(model, results, index, class_id)
        if class_name == "__background__":
            continue
        detection = {
            "class": class_name,
            "score": float(score),
            "bbox": [x1, y1, x2 - x1, y2 - y1],
            "sourceNodeId": source_node_id,
            "kind": "segmentation" if node_type == "segmenter" else "detection",
        }
        if masks is not None and index < len(masks):
            mask = np.squeeze(np.asarray(masks[index]))
            if mask.ndim == 2:
                mask = (mask > 0).astype(np.uint8) * 255
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    contour = max(contours, key=cv2.contourArea).reshape(-1, 2)
                    if len(contour) >= 3:
                        detection["mask"] = [[float(point[0]), float(point[1])] for point in contour]
        detections.append(detection)
    return detections


def _rfdetr_input(frame, device: str):
    """RGB input for RFDETR.predict: CUDA tensor, ndarray for CPU and MPS.

    Uploading the uint8 BGR frame and converting on the GPU avoids the
    per-frame CPU cvtColor plus predict()'s CPU HWC->CHW float conversion.
    For MPS, predict() uploads the RGB ndarray to the model's Metal device.
    """
    if str(device).startswith("cuda"):
        import numpy as np
        import torch

        tensor = torch.from_numpy(np.ascontiguousarray(frame)).to(device)  # HWC uint8 BGR
        return tensor.flip(2).permute(2, 0, 1).float().div_(255.0)  # CHW RGB [0,1]
    import cv2

    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


@_cpu_fallback_inference
def run_rfdetr_frame(frame, inference_node: dict) -> list[dict]:
    import torch

    config = inference_node.get("config", {})
    node_type = inference_node.get("type", "detector")
    model_name = config.get("rfdetrModel") or default_rfdetr_model(node_type)
    checkpoint_path = rfdetr_checkpoint_path(config)
    if checkpoint_path is None:
        if node_type == "segmenter" and model_name not in RFDETR_SEGMENTATION_MODELS:
            raise RuntimeError(f"RF-DETR model '{model_name}' is not an instance segmentation model.")
        if node_type == "detector" and model_name not in RFDETR_DETECTION_MODELS:
            raise RuntimeError(f"RF-DETR model '{model_name}' is not an object detection model.")

    threshold = float(config.get("threshold", 0.55))
    device, _ = resolve_inference_device(config)
    model = load_rfdetr_model(
        model_name,
        device,
        checkpoint_path,
        config.get("rfdetrImageSize", RFDETR_NATIVE_IMAGE_SIZE),
        bool(config.get("rfdetrHalfPrecision", True)),
        expected_node_type=node_type,
    )
    device = effective_inference_device(device)
    predict_shape = rfdetr_predict_shape(config, model)
    with torch.inference_mode():
        model_input = _rfdetr_input(frame, device)
        results = model.predict(
            model_input,
            threshold=threshold,
            shape=predict_shape,
            include_source_image=False,
        )
    if isinstance(results, list):
        results = results[0] if results else None
    return _rfdetr_results_to_detections(model, results, inference_node)


@_cpu_fallback_inference
def run_rfdetr_batch(frames: list, inference_node: dict) -> list[list[dict]]:
    import torch

    if not frames:
        return []
    if len(frames) == 1:
        return [run_rfdetr_frame(frames[0], inference_node)]

    config = inference_node.get("config", {})
    node_type = inference_node.get("type", "detector")
    model_name = config.get("rfdetrModel") or default_rfdetr_model(node_type)
    checkpoint_path = rfdetr_checkpoint_path(config)
    if checkpoint_path is None:
        if node_type == "segmenter" and model_name not in RFDETR_SEGMENTATION_MODELS:
            raise RuntimeError(f"RF-DETR model '{model_name}' is not an instance segmentation model.")
        if node_type == "detector" and model_name not in RFDETR_DETECTION_MODELS:
            raise RuntimeError(f"RF-DETR model '{model_name}' is not an object detection model.")

    threshold = float(config.get("threshold", 0.55))
    device, _ = resolve_inference_device(config)
    model = load_rfdetr_model(
        model_name,
        device,
        checkpoint_path,
        config.get("rfdetrImageSize", RFDETR_NATIVE_IMAGE_SIZE),
        bool(config.get("rfdetrHalfPrecision", True)),
        expected_node_type=node_type,
    )
    device = effective_inference_device(device)
    predict_shape = rfdetr_predict_shape(config, model)
    try:
        with torch.inference_mode():
            model_inputs = [_rfdetr_input(frame, device) for frame in frames]
            results = model.predict(
                model_inputs,
                threshold=threshold,
                shape=predict_shape,
                include_source_image=False,
            )
    except (TypeError, ValueError, AttributeError):
        return [run_rfdetr_frame(frame, inference_node) for frame in frames]

    if not isinstance(results, list):
        results = [results]
    if len(results) != len(frames):
        return [run_rfdetr_frame(frame, inference_node) for frame in frames]
    return [_rfdetr_results_to_detections(model, result, inference_node) for result in results]


def _checkpoint_class_names(value) -> list[str]:
    if isinstance(value, dict):
        def sort_key(item):
            try:
                return 0, int(item[0])
            except (TypeError, ValueError):
                return 1, str(item[0])
        return [
            str(label).strip()
            for _key, label in sorted(value.items(), key=sort_key)
            if str(label).strip()
        ]
    if isinstance(value, (list, tuple)):
        return [str(label).strip() for label in value if str(label).strip()]
    return []


def _convnext_state_dict(checkpoint) -> dict:
    if not isinstance(checkpoint, dict):
        raise RuntimeError("The ConvNeXt checkpoint does not contain a state dictionary.")
    for key in ("model_state_dict", "state_dict", "model"):
        candidate = checkpoint.get(key)
        if isinstance(candidate, dict):
            checkpoint = candidate
            break
    state_dict = {
        str(key).removeprefix("module."): value
        for key, value in checkpoint.items()
        if hasattr(value, "shape")
    }
    if not state_dict:
        raise RuntimeError("The ConvNeXt checkpoint does not contain model weights.")
    return state_dict


def _convnext_num_classes(checkpoint: dict, state_dict: dict, configured_classes: list[str]) -> int:
    try:
        configured_count = int(checkpoint.get("num_classes", 0) or 0)
    except (TypeError, ValueError):
        configured_count = 0
    state_count = 0
    for key in ("head.fc.weight", "head.weight", "classifier.weight"):
        weight = state_dict.get(key)
        shape = getattr(weight, "shape", ())
        if len(shape) == 2 and int(shape[0]) > 0:
            state_count = int(shape[0])
            break
    if configured_count > 0 and state_count > 0 and configured_count != state_count:
        raise RuntimeError(
            f"ConvNeXt checkpoint metadata defines {configured_count} classes but "
            f"its classification head has {state_count} outputs."
        )
    if state_count > 0:
        return state_count
    if configured_count > 0:
        return configured_count
    if configured_classes:
        return len(configured_classes)
    raise RuntimeError(
        "Could not determine the number of ConvNeXt classes. "
        "Add one class name per line in the Classification node."
    )


@_cpu_fallback_loader
def load_convnext_model(config: dict, device: str = "cpu"):
    import torch

    checkpoint_path = convnext_checkpoint_path(config)
    cache_key = (
        "convnext",
        str(checkpoint_path),
        device,
        str(config.get("convnextModel") or ""),
        tuple(convnext_class_names(config)),
        str(config.get("convnextImageSize", 224) or 224),
        bool(config.get("convnextHalfPrecision", True)),
    )
    with _model_lock:
        if cache_key in _model_cache:
            return _model_cache[cache_key]
        try:
            import timm
        except ImportError as exc:
            raise RuntimeError(
                "ConvNeXt support is not installed. Reinstall the VisoNode AI runtime."
            ) from exc

        configured_model = str(
            config.get("convnextModel") or CONVNEXT_MODELS[0]
        ).strip()
        configured_model = CONVNEXT_MODEL_ALIASES.get(
            configured_model,
            configured_model,
        )
        default_mean = (0.485, 0.456, 0.406)
        default_std = (0.229, 0.224, 0.225)

        if checkpoint_path is None:
            if configured_model not in CONVNEXT_MODELS:
                raise RuntimeError(
                    f"Unsupported pretrained ConvNeXt model '{configured_model}'."
                )
            try:
                model = timm.create_model(configured_model, pretrained=True)
            except Exception as exc:
                raise RuntimeError(
                    f"Could not download or load pretrained ConvNeXt model "
                    f"'{configured_model}': {exception_message(exc)}"
                ) from exc
            pretrained_cfg = getattr(model, "pretrained_cfg", {}) or {}
            try:
                num_classes = int(
                    getattr(model, "num_classes", 0)
                    or pretrained_cfg.get("num_classes")
                    or 1000
                )
            except (TypeError, ValueError):
                num_classes = 1000
            classes = convnext_class_names(config)
            if not classes:
                try:
                    subset = timm.data.infer_imagenet_subset(model)
                    classes = (
                        timm.data.ImageNetInfo(subset).label_descriptions()
                        if subset
                        else []
                    )
                    classes = [
                        str(description).split(",", 1)[0].strip()
                        for description in classes
                    ]
                except Exception:
                    classes = []
            if not classes:
                classes = [f"ImageNet class {index}" for index in range(num_classes)]
            if len(classes) != num_classes:
                raise RuntimeError(
                    f"Pretrained ConvNeXt defines {num_classes} outputs but "
                    f"{len(classes)} custom class names were provided."
                )
            input_size = pretrained_cfg.get("input_size") or (3, 224, 224)
            image_size = int(input_size[-1])
            crop_pct = float(pretrained_cfg.get("crop_pct") or 0.875)
            resize_size = max(image_size, int(round(image_size / crop_pct)))
            mean = tuple(pretrained_cfg.get("mean") or default_mean)
            std = tuple(pretrained_cfg.get("std") or default_std)
            interpolation = str(
                pretrained_cfg.get("interpolation") or "bicubic"
            )
            model_name = configured_model
        else:
            try:
                try:
                    checkpoint = torch.load(
                        str(checkpoint_path),
                        map_location="cpu",
                        weights_only=True,
                    )
                except TypeError:
                    checkpoint = torch.load(str(checkpoint_path), map_location="cpu")
            except Exception as exc:
                raise RuntimeError(
                    f"Could not read ConvNeXt checkpoint {checkpoint_path}: "
                    f"{exception_message(exc)}"
                ) from exc
            if not isinstance(checkpoint, dict):
                raise RuntimeError(
                    "The ConvNeXt checkpoint must contain a PyTorch state dictionary."
                )

            state_dict = _convnext_state_dict(checkpoint)
            model_name = str(
                checkpoint.get("model_name") or configured_model
            ).strip()
            model_name = CONVNEXT_MODEL_ALIASES.get(model_name, model_name)
            classes = (
                _checkpoint_class_names(checkpoint.get("classes"))
                or _checkpoint_class_names(checkpoint.get("class_names"))
                or convnext_class_names(config)
            )
            num_classes = _convnext_num_classes(checkpoint, state_dict, classes)
            if not classes:
                classes = [f"class_{index}" for index in range(num_classes)]
            if len(classes) != num_classes:
                raise RuntimeError(
                    f"ConvNeXt checkpoint defines {num_classes} outputs but "
                    f"{len(classes)} class names were provided."
                )
            try:
                image_size = int(
                    checkpoint.get("image_size")
                    or config.get("convnextImageSize")
                    or 224
                )
            except (TypeError, ValueError) as exc:
                raise RuntimeError("ConvNeXt image size must be a whole number.") from exc
            resize_size = max(image_size, int(image_size * 1.14))
            mean = tuple(checkpoint.get("mean") or default_mean)
            std = tuple(checkpoint.get("std") or default_std)
            interpolation = str(checkpoint.get("interpolation") or "bilinear")
            try:
                model = timm.create_model(
                    model_name,
                    pretrained=False,
                    num_classes=num_classes,
                )
                model.load_state_dict(state_dict, strict=True)
            except Exception as exc:
                raise RuntimeError(
                    f"Could not load ConvNeXt architecture '{model_name}' from "
                    f"{checkpoint_path.name}: {exception_message(exc)}"
                ) from exc

        if image_size < 32 or image_size > 2048:
            raise RuntimeError("ConvNeXt image size must be between 32 and 2048 pixels.")
        if len(mean) != 3 or len(std) != 3:
            raise RuntimeError("ConvNeXt normalization metadata must contain three values.")
        model = model.to(device)
        use_half = str(device).startswith("cuda") and bool(
            config.get("convnextHalfPrecision", True)
        )
        if use_half:
            model = model.half()
        model.eval()
        model._visonode_classes = classes
        model._visonode_image_size = image_size
        model._visonode_resize_size = resize_size
        model._visonode_mean = tuple(float(value) for value in mean)
        model._visonode_std = tuple(float(value) for value in std)
        model._visonode_interpolation = (
            interpolation if interpolation in ("bilinear", "bicubic") else "bilinear"
        )
        model._visonode_precision = "FP16" if use_half else "FP32"
        model._visonode_model_name = model_name
        model._visonode_pretrained = checkpoint_path is None
        _model_cache[cache_key] = model
        return model


def _convnext_input(
    frame,
    image_size: int,
    resize_size: int,
    mean_values,
    std_values,
    interpolation: str,
    device: str,
    use_half: bool,
):
    import numpy as np
    import torch
    import torch.nn.functional as functional

    if frame is None or getattr(frame, "ndim", 0) != 3 or frame.shape[2] < 3:
        raise RuntimeError("ConvNeXt expects a three-channel image frame.")
    rgb = np.ascontiguousarray(frame[:, :, :3][:, :, ::-1])
    tensor = torch.from_numpy(rgb).permute(2, 0, 1).float().div_(255.0)
    height, width = int(tensor.shape[1]), int(tensor.shape[2])
    if height <= width:
        resized_height = resize_size
        resized_width = max(image_size, int(round(width * resize_size / max(1, height))))
    else:
        resized_width = resize_size
        resized_height = max(image_size, int(round(height * resize_size / max(1, width))))
    tensor = functional.interpolate(
        tensor.unsqueeze(0),
        size=(resized_height, resized_width),
        mode=interpolation,
        align_corners=False,
        antialias=True,
    ).squeeze(0)
    top = max(0, (resized_height - image_size) // 2)
    left = max(0, (resized_width - image_size) // 2)
    tensor = tensor[:, top:top + image_size, left:left + image_size]
    mean = tensor.new_tensor(mean_values).view(3, 1, 1)
    std = tensor.new_tensor(std_values).view(3, 1, 1)
    tensor = tensor.sub_(mean).div_(std).to(device)
    return tensor.half() if use_half else tensor


@_cpu_fallback_inference
def run_convnext_batch(frames: list, inference_node: dict) -> list[list[dict]]:
    import torch

    if not frames:
        return []
    config = inference_node.get("config", {})
    device, _device_label = resolve_inference_device(config)
    model = load_convnext_model(config, device)
    device = effective_inference_device(device)
    image_size = int(model._visonode_image_size)
    use_half = model._visonode_precision == "FP16"
    inputs = torch.stack([
        _convnext_input(
            frame,
            image_size,
            model._visonode_resize_size,
            model._visonode_mean,
            model._visonode_std,
            model._visonode_interpolation,
            device,
            use_half,
        )
        for frame in frames
    ])
    with torch.inference_mode():
        logits = model(inputs)
        if isinstance(logits, (tuple, list)):
            logits = logits[0]
        probabilities = torch.softmax(logits.float(), dim=1)
    try:
        requested_top_k = int(config.get("topK", 1) or 1)
    except (TypeError, ValueError):
        requested_top_k = 1
    top_k = max(1, min(requested_top_k, len(model._visonode_classes)))
    scores, class_ids = probabilities.topk(top_k, dim=1)
    scores = scores.detach().cpu().tolist()
    class_ids = class_ids.detach().cpu().tolist()
    source_node_id = inference_node.get("id", "classifier")
    results: list[list[dict]] = []
    for frame_scores, frame_class_ids in zip(scores, class_ids):
        results.append([
            {
                "class": model._visonode_classes[int(class_id)],
                "classId": int(class_id),
                "score": float(score),
                "sourceNodeId": source_node_id,
                "kind": "classification",
            }
            for score, class_id in zip(frame_scores, frame_class_ids)
        ])
    return results


def run_convnext_frame(frame, inference_node: dict) -> list[dict]:
    return run_convnext_batch([frame], inference_node)[0]


def _detection_box_xywh(detection: dict) -> tuple[float, float, float, float] | None:
    bbox = detection.get("bbox") or detection.get("box")
    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        try:
            x, y, width, height = (float(value) for value in bbox[:4])
        except (TypeError, ValueError):
            return None
        if width > 0 and height > 0:
            return x, y, width, height
    xyxy = detection.get("xyxy")
    if isinstance(xyxy, (list, tuple)) and len(xyxy) >= 4:
        try:
            x1, y1, x2, y2 = (float(value) for value in xyxy[:4])
        except (TypeError, ValueError):
            return None
        if x2 > x1 and y2 > y1:
            return x1, y1, x2 - x1, y2 - y1
    return None


def detection_crops(
    frame,
    workflow: dict,
    detections: list[dict],
    crop_node: dict,
    *,
    materialize: bool = True,
) -> list[dict]:
    """Select bounds-safe crops, optionally without copying their image pixels."""
    import numpy as np

    if frame is None or not getattr(frame, "shape", None) or len(frame.shape) < 2:
        return []
    frame_height, frame_width = int(frame.shape[0]), int(frame.shape[1])
    config = crop_node.get("config", {})
    crop_id = str(crop_node.get("id") or "detection_crop")
    classes = {
        value.strip().lower()
        for value in str(config.get("classes", "")).replace("\n", ",").split(",")
        if value.strip()
    }
    pad_val = config.get("contextPaddingPercent")
    if pad_val is None:
        pad_val = config.get("paddingPercent", 0.0)
    try:
        padding = float(pad_val or 0.0)
        if padding > 1.0:
            padding /= 100.0
        padding = max(0.0, padding)
    except (TypeError, ValueError):
        padding = 0.0
    try:
        min_size = max(1, int(config.get("minSize", 1) or 1))
    except (TypeError, ValueError):
        min_size = 1
    try:
        min_w = max(min_size, int(config.get("minCropWidth", min_size) or min_size))
        min_h = max(min_size, int(config.get("minCropHeight", min_size) or min_size))
    except (TypeError, ValueError):
        min_w = min_h = min_size
    try:
        max_crops = max(0, int(config.get("maxCrops", 32) or 0))
    except (TypeError, ValueError):
        max_crops = 0
    square = bool(config.get("square", False))
    pad_color_hex = str(config.get("padColor", "#000000") or "#000000").lstrip("#")
    try:
        pad_bgr = (
            int(pad_color_hex[4:6], 16),
            int(pad_color_hex[2:4], 16),
            int(pad_color_hex[0:2], 16),
        ) if len(pad_color_hex) == 6 else (0, 0, 0)
    except Exception:
        pad_bgr = (0, 0, 0)

    # Detection Crop consumes the detections emitted by Logic ROI nodes on its
    # incoming branch.  The normal preview/output pipeline applies Logic nodes
    # at the final target, but crops are materialized earlier, so using the
    # unfiltered global detection batch here would create crops for the whole
    # image.  Crossing ROIs remain stateful and are applied by the track-event
    # pipeline before it calls this function; an inside ROI is safe to apply
    # here as a stateless per-detection filter.
    for roi_node in active_logic_nodes_for_target(workflow, crop_id):
        roi_config = roi_node.get("config", {})
        if (
            roi_node.get("type") == "roi_filter"
            and roi_config.get("mode", "inside") == "inside"
        ):
            roi = _roi_geometry(roi_config)
            if roi is None:
                continue
            detections = [
                detection
                for detection in detections
                if not has_active_path(
                    workflow,
                    str(
                        detection.get("sourceNodeId")
                        or detection.get("parentSourceNodeId")
                        or "detector"
                    ),
                    str(roi_node.get("id") or "roi_filter"),
                )
                or _detection_in_roi(
                    detection,
                    roi,
                    roi_config.get("triggerAnchor") or roi_config.get("match", "bottom_center"),
                )
            ]

    branch_regions: dict[str, tuple[int, int, int, int]] = {}

    def branch_region(source_id: str) -> tuple[int, int, int, int]:
        """Return the source-frame ROI selected on this Detection Crop branch."""
        if source_id in branch_regions:
            return branch_regions[source_id]
        region = (0, 0, frame_width, frame_height)
        for node in active_image_processing_nodes_for_path(workflow, source_id, crop_id):
            if node.get("type") != "crop":
                continue
            node_config = node.get("config", {})
            region_x, region_y, region_width, region_height = region
            x = max(0, int(node_config.get("x", 0)))
            y = max(0, int(node_config.get("y", 0)))
            width = int(node_config.get("width", region_width))
            height = int(node_config.get("height", region_height))
            x1 = min(region_x + region_width, region_x + x)
            y1 = min(region_y + region_height, region_y + y)
            x2 = min(region_x + region_width, x1 + max(0, width))
            y2 = min(region_y + region_height, y1 + max(0, height))
            region = (x1, y1, max(0, x2 - x1), max(0, y2 - y1))
        branch_regions[source_id] = region
        return region

    crops: list[dict] = []
    ranked_detections = sorted(
        detections,
        key=lambda item: float(item.get("score", 0.0)),
        reverse=True,
    )
    for detection in ranked_detections:
        if classes and str(detection.get("class", "")).strip().lower() not in classes:
            continue
        source_id = str(detection.get("sourceNodeId") or "detector")
        if not has_active_path(workflow, source_id, crop_id):
            continue
        box = _detection_box_xywh(detection)
        if box is None:
            continue
        x, y, width, height = box
        center_x, center_y = x + width / 2.0, y + height / 2.0
        crop_width = width * (1.0 + 2.0 * padding)
        crop_height = height * (1.0 + 2.0 * padding)
        if square:
            crop_width = crop_height = max(crop_width, crop_height)
        x1 = max(0, int(math.floor(center_x - crop_width / 2.0)))
        y1 = max(0, int(math.floor(center_y - crop_height / 2.0)))
        x2 = min(frame_width, int(math.ceil(center_x + crop_width / 2.0)))
        y2 = min(frame_height, int(math.ceil(center_y + crop_height / 2.0)))
        region_x, region_y, region_width, region_height = branch_region(source_id)
        x1 = max(x1, region_x)
        y1 = max(y1, region_y)
        x2 = min(x2, region_x + region_width)
        y2 = min(y2, region_y + region_height)
        if (x2 - x1) < min_w or (y2 - y1) < min_h:
            continue
        
        crop_img = None
        if materialize:
            crop_slice = frame[y1:y2, x1:x2]
            if square and crop_slice.shape[0] != crop_slice.shape[1]:
                import cv2
                ch, cw = crop_slice.shape[:2]
                target_dim = max(ch, cw)
                pad_top = (target_dim - ch) // 2
                pad_bottom = target_dim - ch - pad_top
                pad_left = (target_dim - cw) // 2
                pad_right = target_dim - cw - pad_left
                crop_img = cv2.copyMakeBorder(
                    crop_slice, pad_top, pad_bottom, pad_left, pad_right,
                    cv2.BORDER_CONSTANT, value=pad_bgr
                )
            else:
                crop_img = np.ascontiguousarray(crop_slice)

        crops.append({
            "frame": crop_img,
            "detection": detection,
            "bounds": [x1, y1, x2 - x1, y2 - y1],
            "cropIndex": len(crops),
        })
        if max_crops and len(crops) >= max_crops:
            break
    return crops


def run_detection_crop_classifier_batch(
    frames: list,
    detections_by_frame: list[list[dict]],
    workflow: dict,
    crop_node: dict,
    classifier_node: dict,
    *,
    crops_by_frame: list[list[dict]] | None = None,
) -> list[list[dict]]:
    """Classify or inspect every crop and map results back onto source boxes."""
    if len(frames) != len(detections_by_frame):
        raise ValueError("Detection Crop frame and detection batch sizes must match.")
    if crops_by_frame is not None and len(crops_by_frame) != len(frames):
        raise ValueError("Detection Crop frame and crop batch sizes must match.")
    output: list[list[dict]] = [[] for _ in frames]
    pending_frames = []
    pending_metadata: list[tuple[int, dict]] = []
    for frame_index, (frame, detections) in enumerate(zip(frames, detections_by_frame)):
        crops = (crops_by_frame[frame_index] if crops_by_frame is not None
                 else detection_crops(frame, workflow, detections, crop_node))
        for crop in crops:
            pending_frames.append(crop["frame"])
            pending_metadata.append((frame_index, crop))
    if not pending_frames:
        return output

    config = classifier_node.get("config", {})
    try:
        batch_size = max(1, int(config.get("batchSize", 1) or 1))
    except (TypeError, ValueError):
        batch_size = 1
    try:
        threshold = float(config.get("threshold", 0.0) or 0.0)
    except (TypeError, ValueError):
        threshold = 0.0

    is_anomaly = classifier_node.get("type") == "efficientad"
    infer_batch = run_efficientad_batch if is_anomaly else run_convnext_batch
    classification_batches: list[list[dict]] = []
    for offset in range(0, len(pending_frames), batch_size):
        classification_batches.extend(
            infer_batch(pending_frames[offset:offset + batch_size], classifier_node)
        )
    if len(classification_batches) != len(pending_metadata):
        raise RuntimeError("Detection Crop inference returned an unexpected number of results.")

    crop_id = str(crop_node.get("id") or "detection_crop")
    for (frame_index, crop), classifications in zip(pending_metadata, classification_batches):
        parent = crop["detection"]
        parent_box = _detection_box_xywh(parent)
        for classification in classifications:
            if not is_anomaly and float(classification.get("score", 0.0)) < threshold:
                continue
            result = {
                **classification,
                "kind": "anomaly" if is_anomaly else "object_classification",
                "bbox": list(parent_box) if parent_box is not None else list(crop["bounds"]),
                "detectionClass": str(parent.get("class", "object")),
                "detectionScore": float(parent.get("score", 0.0)),
                "parentSourceNodeId": str(parent.get("sourceNodeId") or "detector"),
                "cropNodeId": crop_id,
                "cropIndex": int(crop.get("cropIndex", 0)),
                "cropBounds": list(crop["bounds"]),
            }
            if parent.get("trackId") is not None:
                result["trackId"] = parent.get("trackId")
            output[frame_index].append(result)
    return output


def run_detection_crop_classifier(
    frame,
    detections: list[dict],
    workflow: dict,
    crop_node: dict,
    classifier_node: dict,
) -> list[dict]:
    return run_detection_crop_classifier_batch(
        [frame], [detections], workflow, crop_node, classifier_node,
    )[0]


def detection_crop_batches(frame, workflow: dict, detections: list[dict]) -> dict[str, list[dict]]:
    """Build the per-frame crop collections emitted by active Detection Crop nodes."""
    track_driven_ids = {
        str(node.get("id") or "") for node in track_driven_detection_crop_nodes(workflow)
    }
    return {
        str(node.get("id") or "detection_crop"): detection_crops(
            frame, workflow, detections, node,
        )
        for node in active_detection_crop_nodes(workflow)
        if str(node.get("id") or "") not in track_driven_ids
    }


def detection_crop_items_for_target(
    workflow: dict,
    target_id: str,
    crop_batches: dict[str, list[dict]],
    detections: list[dict],
) -> list[dict] | None:
    """Return crop items for a downstream target, or None for a frame preview."""
    crop_nodes = [
        node for node in active_detection_crop_nodes(workflow)
        if has_active_path(workflow, str(node.get("id") or ""), target_id)
    ]
    if not crop_nodes:
        return None
    classifications: dict[tuple[str, int], list[dict]] = {}
    for detection in detections:
        if detection.get("kind") not in ("object_classification", "anomaly") or not detection.get("cropNodeId"):
            continue
        if detection.get("sourceNodeId") and not has_active_path(workflow, str(detection["sourceNodeId"]), target_id):
            continue
        key = (
            str(detection.get("cropNodeId") or ""),
            int(detection.get("cropIndex", 0) or 0),
        )
        classifications.setdefault(key, []).append(detection)
    items: list[dict] = []
    for node in crop_nodes:
        crop_id = str(node.get("id") or "detection_crop")
        for crop in crop_batches.get(crop_id, []):
            crop_index = int(crop.get("cropIndex", 0) or 0)
            items.append({
                **crop,
                "cropNodeId": crop_id,
                "classifications": classifications.get((crop_id, crop_index), []),
            })
    return items


def render_detection_crop_grid(frame, crop_items: list[dict], preview: dict):
    """Render a bounded contact sheet while preserving the source frame size."""
    import cv2
    import numpy as np

    height, width = int(frame.shape[0]), int(frame.shape[1])
    config = preview.get("config", {})
    max_items = max(1, int(config.get("cropGridMaxItems", 16) or 16))
    gap = max(0, int(config.get("cropGridGap", 8) or 0))
    for item in crop_items:
        item.pop("_previewBounds", None)
    visible = sorted(
        crop_items,
        key=lambda item: float(item.get("detection", {}).get("score", 0.0)),
        reverse=True,
    )[:max_items]
    canvas = np.full_like(frame, (15, 23, 42))
    if not visible:
        cv2.putText(
            canvas, "No detection crops", (max(12, width // 2 - 105), height // 2),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (203, 213, 225), 2, cv2.LINE_AA,
        )
        return canvas

    requested_columns = max(0, int(config.get("cropGridColumns", 0) or 0))
    columns = min(len(visible), requested_columns) if requested_columns else min(
        len(visible), max(1, int(math.ceil(math.sqrt(len(visible) * width / max(1, height)))))
    )
    rows = int(math.ceil(len(visible) / columns))
    cell_width = max(1, width // columns)
    cell_height = max(1, height // rows)
    show_labels = bool(config.get("showLabels", True))
    label_height = min(30, max(18, cell_height // 5)) if show_labels else 0

    for index, item in enumerate(visible):
        row, column = divmod(index, columns)
        left, top = column * cell_width, row * cell_height
        right = width if column == columns - 1 else (column + 1) * cell_width
        bottom = height if row == rows - 1 else (row + 1) * cell_height
        available_width = max(1, right - left - gap * 2)
        available_height = max(1, bottom - top - gap * 2 - label_height)
        crop_frame = item.get("frame")
        if crop_frame is None or not getattr(crop_frame, "shape", None):
            continue
        crop_height, crop_width = int(crop_frame.shape[0]), int(crop_frame.shape[1])
        scale = min(available_width / max(1, crop_width), available_height / max(1, crop_height))
        resized_width = max(1, int(round(crop_width * scale)))
        resized_height = max(1, int(round(crop_height * scale)))
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        resized = cv2.resize(crop_frame, (resized_width, resized_height), interpolation=interpolation)
        for result in item.get("classifications", []):
            if result.get("kind") == "anomaly":
                from efficientad_runtime import draw_result
                draw_result(resized, {**result, "cropBounds": [0, 0, resized_width, resized_height]},
                            show_labels=False, show_boxes=bool(config.get("showBoxes", True)))
        image_left = left + (right - left - resized_width) // 2
        image_top = top + gap + (available_height - resized_height) // 2
        # Overlay layers run after the contact sheet is composed. Retain the
        # actual on-screen crop rectangle so their anchors use preview-space
        # coordinates instead of the source camera's bounding box.
        item["_previewBounds"] = [image_left, image_top, resized_width, resized_height]
        canvas[image_top:image_top + resized_height, image_left:image_left + resized_width] = resized
        cv2.rectangle(canvas, (left + gap, top + gap), (right - gap - 1, bottom - gap - 1), (71, 85, 105), 1)
        if show_labels:
            detection = item.get("detection", {})
            label = f"{detection.get('class', 'object')} {float(detection.get('score', 0)):.2f}"
            ranked = sorted(
                item.get("classifications", []),
                key=lambda result: (result.get("kind") == "anomaly", float(result.get("score", 0.0))),
                reverse=True,
            )
            if ranked:
                best = ranked[0]
                label = f"{label} -> {best.get('class', 'class')} {float(best.get('score', 0)):.2f}"
            cv2.putText(
                canvas, label[:48], (left + gap + 4, bottom - gap - 7),
                cv2.FONT_HERSHEY_SIMPLEX, 0.46, (248, 250, 252), 1, cv2.LINE_AA,
            )
    overflow = len(crop_items) - len(visible)
    if overflow > 0:
        cv2.putText(
            canvas, f"+{overflow} more", (12, 24), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (255, 255, 255), 2, cv2.LINE_AA,
        )
    return canvas


def crop_grid_drawing_detections(crop_items: list[dict]) -> list[dict]:
    """Map crop detections/classifications onto their rendered preview boxes."""
    mapped: list[dict] = []
    for crop in crop_items:
        bounds = crop.get("_previewBounds")
        if not isinstance(bounds, (list, tuple)) or len(bounds) < 4:
            continue
        annotations = [crop.get("detection"), *crop.get("classifications", [])]
        for annotation in annotations:
            if not isinstance(annotation, dict):
                continue
            mapped.append({
                **annotation, "bbox": list(bounds[:4]),
                **({"cropBounds": list(bounds[:4])} if annotation.get("cropBounds") is not None else {}),
            })
    return mapped


def _rfdetr_tensorrt_postprocess(
    boxes,
    logits,
    frame_shapes: list[tuple[int, int]],
    inference_node: dict,
    masks=None,
) -> list[list[dict]]:
    """Convert exported RF-DETR raw tensors to VisoNode boxes and masks."""
    import cv2
    import numpy as np

    boxes = np.asarray(boxes, dtype=np.float32)
    logits = np.asarray(logits, dtype=np.float32)
    if boxes.ndim != 3 or boxes.shape[-1] != 4:
        raise RuntimeError(f"RF-DETR exported 'dets' output has unexpected shape {boxes.shape}.")
    if logits.ndim != 3 or logits.shape[:2] != boxes.shape[:2]:
        raise RuntimeError(f"RF-DETR exported 'labels' output has unexpected shape {logits.shape}.")
    if boxes.shape[0] != len(frame_shapes):
        raise RuntimeError("RF-DETR exported output batch does not match the input batch.")
    mask_logits = None
    if masks is not None:
        mask_logits = np.asarray(masks, dtype=np.float32)
        if mask_logits.ndim == 5 and mask_logits.shape[2] == 1:
            mask_logits = mask_logits[:, :, 0]
        if mask_logits.ndim != 4 or mask_logits.shape[:2] != boxes.shape[:2]:
            raise RuntimeError(f"RF-DETR exported 'masks' output has unexpected shape {mask_logits.shape}.")

    config = inference_node.get("config", {})
    threshold = float(config.get("threshold", 0.55))
    source_node_id = inference_node.get("id", "detector")
    custom_names = rfdetr_tensorrt_class_names(config)
    coco_names = None
    if not custom_names:
        try:
            from rfdetr.assets.coco_classes import COCO_CLASSES
            coco_names = COCO_CLASSES
        except ImportError:
            coco_names = {}

    # Stable sigmoid prevents overflow for very negative exported logits.
    probabilities = np.empty_like(logits)
    positive = logits >= 0
    probabilities[positive] = 1.0 / (1.0 + np.exp(-logits[positive]))
    exp_values = np.exp(logits[~positive])
    probabilities[~positive] = exp_values / (1.0 + exp_values)

    batch_results: list[list[dict]] = []
    for batch_index, (height, width) in enumerate(frame_shapes):
        flat = probabilities[batch_index].reshape(-1)
        count = min(300, flat.size)
        if count <= 0:
            batch_results.append([])
            continue
        top = np.argpartition(flat, flat.size - count)[-count:]
        top = top[np.argsort(flat[top])[::-1]]
        class_count = logits.shape[2]
        detections = []
        query_polygons = {}
        for flat_index in top:
            score = float(flat[flat_index])
            if score <= threshold:
                break
            query_index = int(flat_index // class_count)
            class_id = int(flat_index % class_count)
            cx, cy, box_width, box_height = boxes[batch_index, query_index]
            x1 = max(0.0, min(float(width), float((cx - box_width / 2) * width)))
            y1 = max(0.0, min(float(height), float((cy - box_height / 2) * height)))
            x2 = max(0.0, min(float(width), float((cx + box_width / 2) * width)))
            y2 = max(0.0, min(float(height), float((cy + box_height / 2) * height)))
            if x2 <= x1 or y2 <= y1:
                continue
            if custom_names:
                class_name = custom_names[class_id] if class_id < len(custom_names) else str(class_id)
            else:
                class_name = str(coco_names.get(class_id, class_id))
            detections.append({
                "class": class_name,
                "score": score,
                "bbox": [x1, y1, x2 - x1, y2 - y1],
                "sourceNodeId": source_node_id,
                "kind": "segmentation" if inference_node.get("type") == "segmenter" else "detection",
            })
            if mask_logits is not None:
                # Top-k may retain multiple classes for one object query. Its
                # mask is identical: resize and trace it once per frame/query.
                if query_index not in query_polygons:
                    query_polygons[query_index] = None
                    mask = cv2.resize(
                        mask_logits[batch_index, query_index],
                        (width, height),
                        interpolation=cv2.INTER_LINEAR,
                    )
                    binary_mask = (mask > 0).astype(np.uint8) * 255
                    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        contour = max(contours, key=cv2.contourArea).reshape(-1, 2)
                        if len(contour) >= 3:
                            query_polygons[query_index] = [
                                [float(point[0]), float(point[1])] for point in contour
                            ]
                polygon = query_polygons[query_index]
                if polygon is not None:
                    # Downstream coordinate transforms may edit lists in place.
                    detections[-1]["mask"] = [point.copy() for point in polygon]
        batch_results.append(detections)
    return batch_results


class RFDETRTensorRTRuntime:
    """TensorRT executor for RF-DETR engines exported by the rfdetr package."""

    def __init__(self, engine_path: Path, device: str = "cuda:0", *, cuda_graph: bool = False) -> None:
        try:
            import tensorrt as trt
        except ImportError as exc:
            raise RuntimeError(
                "TensorRT Python is not installed. Install NVIDIA TensorRT (including its Python package) "
                "in the VisoNode AI runtime."
            ) from exc
        import torch

        if not str(device).startswith("cuda") or not torch.cuda.is_available():
            raise RuntimeError("RF-DETR TensorRT requires an NVIDIA CUDA device.")
        self.device = str(device)
        # Cached runtimes can be called by multiple workflow workers. A TensorRT
        # execution context and its reusable buffers must have one owner at a time.
        self._inference_lock = Lock()
        self._input_buffers = None
        self._output_buffers = {}
        self._stream = torch.cuda.Stream(device=self.device)
        self._cuda_graph_enabled = bool(cuda_graph)
        self._cuda_graph = None
        self._cuda_graph_signature = None
        self.cuda_graph_error = None
        self.engine_path = Path(engine_path)
        self.trt = trt
        logger_instance = trt.Logger(trt.Logger.WARNING)
        self._runtime = trt.Runtime(logger_instance)
        self.engine = self._runtime.deserialize_cuda_engine(self.engine_path.read_bytes())
        if self.engine is None:
            raise RuntimeError(
                "TensorRT could not deserialize this engine. Rebuild it with the installed TensorRT version "
                "on this GPU family."
            )
        self.context = self.engine.create_execution_context()
        if self.context is None:
            raise RuntimeError("TensorRT could not create an execution context for this engine.")
        self._v3_api = hasattr(self.engine, "num_io_tensors") and hasattr(self.context, "execute_async_v3")
        self.input_names, self.output_names = self._io_names()
        if len(self.input_names) != 1:
            raise RuntimeError(f"RF-DETR TensorRT engines must have one input; found {self.input_names}.")
        self.input_name = self.input_names[0]
        self.input_shape = self._preferred_input_shape()
        if len(self.input_shape) != 4 or any(int(value) <= 0 for value in self.input_shape[1:]):
            raise RuntimeError(f"RF-DETR TensorRT input shape is unsupported: {self.input_shape}.")
        self.dets_name = next((name for name in self.output_names if name.lower() in ("dets", "boxes", "pred_boxes")), None)
        self.labels_name = next((name for name in self.output_names if name.lower() in ("labels", "logits", "pred_logits")), None)
        self.masks_name = next((name for name in self.output_names if name.lower() in ("masks", "mask", "pred_masks")), None)
        if not self.dets_name or not self.labels_name:
            raise RuntimeError(
                "This is not a full RF-DETR export: expected 'dets' and 'labels' TensorRT outputs, "
                f"found {self.output_names}."
            )

    def _io_names(self) -> tuple[list[str], list[str]]:
        trt = self.trt
        if self._v3_api:
            names = [self.engine.get_tensor_name(index) for index in range(self.engine.num_io_tensors)]
            inputs = [name for name in names if self.engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT]
        else:
            names = [self.engine.get_binding_name(index) for index in range(self.engine.num_bindings)]
            inputs = [name for index, name in enumerate(names) if self.engine.binding_is_input(index)]
        return inputs, [name for name in names if name not in inputs]

    def _engine_shape(self, name: str) -> tuple[int, ...]:
        if self._v3_api:
            return tuple(self.engine.get_tensor_shape(name))
        return tuple(self.engine.get_binding_shape(self.engine.get_binding_index(name)))

    def _preferred_input_shape(self) -> tuple[int, ...]:
        shape = self._engine_shape(self.input_name)
        if all(int(value) > 0 for value in shape):
            return shape
        try:
            if self._v3_api:
                return tuple(self.engine.get_tensor_profile_shape(self.input_name, 0)[1])
            index = self.engine.get_binding_index(self.input_name)
            return tuple(self.engine.get_profile_shape(0, index)[1])
        except Exception as exc:
            raise RuntimeError(f"Could not resolve dynamic TensorRT input shape {shape}.") from exc

    def _tensor_dtype(self, name: str):
        import numpy as np
        import torch

        dtype = self.engine.get_tensor_dtype(name) if self._v3_api else self.engine.get_binding_dtype(
            self.engine.get_binding_index(name)
        )
        numpy_dtype = np.dtype(self.trt.nptype(dtype))
        mapping = {
            np.dtype(np.float16): torch.float16,
            np.dtype(np.float32): torch.float32,
            np.dtype(np.int32): torch.int32,
            np.dtype(np.int64): torch.int64,
            np.dtype(np.int8): torch.int8,
            np.dtype(np.bool_): torch.bool,
        }
        if numpy_dtype not in mapping:
            raise RuntimeError(f"Unsupported TensorRT tensor dtype {numpy_dtype} for '{name}'.")
        return mapping[numpy_dtype]

    def _preprocess(self, frames: list):
        import cv2
        import numpy as np
        import torch

        input_height, input_width = int(self.input_shape[2]), int(self.input_shape[3])
        mean = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
        std = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)
        shape = (len(frames), 3, input_height, input_width)
        if self._input_buffers is None or tuple(self._input_buffers[0].shape) != shape:
            host = torch.empty(shape, dtype=torch.float32, pin_memory=True)
            device = torch.empty(shape, device=self.device, dtype=self._tensor_dtype(self.input_name))
            self._input_buffers = (host, device)
        host, device = self._input_buffers
        images = host.numpy()
        for index, frame in enumerate(frames):
            image = cv2.resize(frame, (input_width, input_height), interpolation=cv2.INTER_LINEAR)
            images[index] = image[:, :, ::-1].transpose(2, 0, 1)
        images /= 255.0
        images -= mean[None, :, None, None]
        images /= std[None, :, None, None]
        device.copy_(host, non_blocking=True)
        return device

    @contextmanager
    def _execution_guard(self):
        import torch

        with self._inference_lock, torch.cuda.device(self.device), torch.cuda.stream(self._stream), torch.inference_mode():
            try:
                yield
            except BaseException:
                # An upload may already be reading pinned staging memory when a
                # later shape/allocation/execution check fails. Drain it before
                # another caller can acquire the lock and overwrite those bytes.
                try:
                    self._stream.synchronize()
                except Exception:
                    # A failed CUDA context must not hide the original error.
                    pass
                raise

    def _enqueue_engine(self, tensors, stream):
        import torch

        signature = tuple((name, tuple(tensor.shape), int(tensor.data_ptr()))
                          for name, tensor in tensors.items())
        if signature != self._cuda_graph_signature:
            self._cuda_graph = None
            self._cuda_graph_signature = signature
        if self._cuda_graph is not None:
            self._cuda_graph.replay()
            return

        bindings = None
        if self._v3_api:
            for name, tensor in tensors.items():
                self.context.set_tensor_address(name, int(tensor.data_ptr()))
        else:
            bindings = [0] * self.engine.num_bindings
            for name, tensor in tensors.items():
                bindings[self.engine.get_binding_index(name)] = int(tensor.data_ptr())

        def execute():
            ok = (self.context.execute_async_v3(stream_handle=stream.cuda_stream) if self._v3_api else
                  self.context.execute_async_v2(bindings, stream.cuda_stream))
            if not ok:
                raise RuntimeError("TensorRT RF-DETR inference execution failed.")

        # Flush TensorRT's shape-dependent state before capture. This ordinary
        # enqueue also produces the first result; captured operations run later.
        execute()
        if self._cuda_graph_enabled:
            stream.synchronize()
            try:
                graph = torch.cuda.CUDAGraph()
                with torch.cuda.graph(graph, stream=stream, capture_error_mode="thread_local"):
                    execute()
                self._cuda_graph = graph
            except Exception as exc:
                # Engines containing CPU shape evaluation cannot be captured.
                # Keep their successful ordinary enqueue and disable retries.
                self._cuda_graph_enabled = False
                self.cuda_graph_error = str(exc)
                logging.getLogger(__name__).warning(
                    "TensorRT CUDA graph capture unavailable for %s; using ordinary inference: %s",
                    self.engine_path, exc,
                )

    def _enqueue_exact(self, frames: list):
        import torch

        input_tensor = self._preprocess(frames)
        actual_shape = tuple(input_tensor.shape)
        if self._v3_api:
            if not self.context.set_input_shape(self.input_name, actual_shape):
                raise RuntimeError(f"TensorRT rejected RF-DETR input shape {actual_shape}.")
        else:
            input_index = self.engine.get_binding_index(self.input_name)
            if not self.context.set_binding_shape(input_index, actual_shape):
                raise RuntimeError(f"TensorRT rejected RF-DETR input shape {actual_shape}.")

        tensors = {self.input_name: input_tensor}
        for name in self.output_names:
            shape = tuple(self.context.get_tensor_shape(name)) if self._v3_api else tuple(
                self.context.get_binding_shape(self.engine.get_binding_index(name))
            )
            if any(int(value) < 0 for value in shape):
                raise RuntimeError(f"TensorRT did not resolve output shape for '{name}': {shape}.")
            buffers = self._output_buffers.get(name)
            if buffers is None or tuple(buffers[0].shape) != shape:
                buffers = (
                    torch.empty(shape, dtype=self._tensor_dtype(name), device=self.device),
                    torch.empty(shape, dtype=self._tensor_dtype(name), pin_memory=True),
                )
                self._output_buffers[name] = buffers
            tensors[name] = buffers[0]

        stream = torch.cuda.current_stream(torch.device(self.device))
        self._enqueue_engine(tensors, stream)
        for name in self.output_names:
            self._output_buffers[name][1].copy_(tensors[name], non_blocking=True)
        return {name: self._output_buffers[name][1] for name in self.output_names}

    @staticmethod
    def _copy_outputs(outputs):
        import numpy as np
        # Results outlive the next invocation and must not alias staging memory.
        return {name: tensor.numpy().astype(np.float32, copy=True) for name, tensor in outputs.items()}

    def _infer_exact(self, frames: list) -> dict[str, object]:
        with self._execution_guard():
            outputs = self._enqueue_exact(frames)
            self._stream.synchronize()
            return self._copy_outputs(outputs)

    def _infer_chunks(self, chunks):
        # Distinct pinned/device slots let CPU preprocessing of the next chunk
        # overlap GPU execution of the previous one, without changing stream or
        # context ownership. Bound staging memory even for very large requests.
        results = []
        with self._execution_guard():
            slots = getattr(self, "_batch_buffers", None)
            if slots is None:
                slots = self._batch_buffers = [(None, {}) for _ in range(4)]
            original_buffers = (self._input_buffers, self._output_buffers)
            try:
                for offset in range(0, len(chunks), len(slots)):
                    pending = []
                    for index, chunk in enumerate(chunks[offset:offset + len(slots)]):
                        self._input_buffers, self._output_buffers = slots[index]
                        try:
                            pending.append(self._enqueue_exact(chunk))
                        finally:
                            slots[index] = (self._input_buffers, self._output_buffers)
                    self._stream.synchronize()
                    results.extend(self._copy_outputs(output) for output in pending)
            finally:
                self._input_buffers, self._output_buffers = original_buffers
        return results

    def infer(self, frames: list) -> tuple[object, object, object | None]:
        if not frames:
            return [], [], None
        fixed_batch = int(self._engine_shape(self.input_name)[0])
        min_batch = max_batch = fixed_batch
        if fixed_batch <= 0:
            if self._v3_api:
                profile = self.engine.get_tensor_profile_shape(self.input_name, 0)
            else:
                profile = self.engine.get_profile_shape(0, self.engine.get_binding_index(self.input_name))
            min_batch, max_batch = int(profile[0][0]), int(profile[2][0])
        if not min_batch <= len(frames) <= max_batch:
            chunks = []
            output_counts = []
            for offset in range(0, len(frames), max_batch):
                chunk = frames[offset:offset + max_batch]
                output_counts.append(len(chunk))
                if len(chunk) < min_batch:
                    chunk = chunk + [chunk[-1]] * (min_batch - len(chunk))
                chunks.append(chunk)
            outputs = (self._infer_chunks(chunks) if fixed_batch > 0 and len(chunks) > 1
                       and not self._cuda_graph_enabled else
                       [self._infer_exact(chunk) for chunk in chunks])
            import numpy as np
            masks = None
            if self.masks_name:
                masks = np.concatenate([
                    output[self.masks_name][:count]
                    for output, count in zip(outputs, output_counts)
                ])
            return (
                np.concatenate([
                    output[self.dets_name][:count]
                    for output, count in zip(outputs, output_counts)
                ]),
                np.concatenate([
                    output[self.labels_name][:count]
                    for output, count in zip(outputs, output_counts)
                ]),
                masks,
            )
        output = self._infer_exact(frames)
        masks = output[self.masks_name] if self.masks_name else None
        return output[self.dets_name], output[self.labels_name], masks


@_tensorrt_recovery_error
def load_rfdetr_tensorrt(config: dict):
    engine_path = rfdetr_tensorrt_engine_path(config)
    device, _ = resolve_inference_device({**config, "device": config.get("device", "auto")})
    if not device.startswith("cuda"):
        raise RuntimeError("RF-DETR TensorRT requires Device to be an NVIDIA CUDA GPU.")
    cuda_graph = bool(config.get("rfdetrTensorRTCudaGraph", False))
    cache_key = ("rfdetr_tensorrt", str(engine_path), device, cuda_graph)
    with _model_lock:
        if cache_key not in _model_cache:
            _model_cache[cache_key] = RFDETRTensorRTRuntime(engine_path, device, cuda_graph=cuda_graph)
        return _model_cache[cache_key]


@_tensorrt_recovery_error
def run_rfdetr_tensorrt_batch(frames: list, inference_node: dict) -> list[list[dict]]:
    if not frames:
        return []
    runtime = load_rfdetr_tensorrt(inference_node.get("config", {}))
    boxes, logits, masks = runtime.infer(frames)
    if inference_node.get("type") == "segmenter" and masks is None:
        raise RuntimeError(
            "The selected RF-DETR TensorRT engine has no 'masks' output. "
            "Select a full RF-DETR segmentation export."
        )
    frame_shapes = [(int(frame.shape[0]), int(frame.shape[1])) for frame in frames]
    return _rfdetr_tensorrt_postprocess(boxes, logits, frame_shapes, inference_node, masks)


def run_rfdetr_tensorrt_frame(frame, inference_node: dict) -> list[dict]:
    return run_rfdetr_tensorrt_batch([frame], inference_node)[0]


def load_rfdetr_onnx(config: dict):
    from rfdetr_onnx_runtime import RFDETRONNXRuntime

    model_path = rfdetr_onnx_model_path(config)
    image_size = _rfdetr_inference_size(config.get("rfdetrImageSize", 0))
    try:
        threads = int(config.get("rfdetrOnnxThreads", 0) or 0)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("ONNX CPU thread count must be a whole number.") from exc
    stat = model_path.stat()
    cache_key = ("rfdetr_onnx", str(model_path), stat.st_mtime_ns, stat.st_size, image_size, threads)
    with _model_lock:
        if cache_key not in _model_cache:
            _model_cache[cache_key] = RFDETRONNXRuntime(model_path, image_size, threads)
        return _model_cache[cache_key]


def run_rfdetr_onnx_batch(frames: list, inference_node: dict) -> list[list[dict]]:
    if not frames:
        return []
    config = inference_node.get("config", {})
    runtime = load_rfdetr_onnx(config)
    if inference_node.get("type") == "segmenter" and runtime.masks_name is None:
        raise RuntimeError("The selected RF-DETR ONNX model has no masks output. Select a full segmentation export.")
    boxes, logits, masks = runtime.infer(frames)
    frame_shapes = [(int(frame.shape[0]), int(frame.shape[1])) for frame in frames]
    node = {**inference_node, "config": {**config, "rfdetrTensorRTClasses": config.get("rfdetrOnnxClasses") or runtime.class_names}}
    return _rfdetr_tensorrt_postprocess(boxes, logits, frame_shapes, node, masks)


def run_rfdetr_onnx_frame(frame, inference_node: dict) -> list[dict]:
    return run_rfdetr_onnx_batch([frame], inference_node)[0]



@_cpu_fallback_inference
def run_sam3_frame(frame, inference_node: dict) -> list[dict]:
    from sam3_compat import sam3_autocast

    import cv2
    import numpy as np
    import torch
    from PIL import Image

    config = inference_node.get("config", {})
    source_node_id = inference_node.get("id", "segmenter")
    device, _ = resolve_inference_device(config)
    processor = load_sam3_processor(config, device)
    device = effective_inference_device(device)
    concepts = sam3_concepts(config)
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    with sam3_autocast(device):
        image_state = processor.set_image(image)

    detections = []
    for concept in concepts:
        prompt_state = dict(image_state)
        prompt_state["backbone_out"] = dict(image_state["backbone_out"])
        with sam3_autocast(device):
            output = processor.set_text_prompt(state=prompt_state, prompt=concept)
        masks = output.get("masks")
        boxes = output.get("boxes")
        scores = output.get("scores")
        if masks is None or boxes is None or scores is None:
            continue
        boxes = boxes.detach().cpu().tolist()
        scores = scores.detach().cpu().tolist()
        masks = masks.detach().cpu().numpy()
        for index, (box, score) in enumerate(zip(boxes, scores)):
            x1, y1, x2, y2 = [float(value) for value in box]
            detection = {
                "class": concept,
                "score": float(score),
                "bbox": [float(x1), float(y1), float(x2 - x1), float(y2 - y1)],
                "sourceNodeId": source_node_id,
                "kind": "segmentation",
            }
            if index < len(masks):
                mask = np.squeeze(masks[index]).astype(np.uint8)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    contour = max(contours, key=cv2.contourArea).reshape(-1, 2)
                    if len(contour) >= 3:
                        detection["mask"] = [[float(point[0]), float(point[1])] for point in contour]
            detections.append(detection)
    return detections


def filter_project_inputs(workflow: dict, target_id: str, detections: list[dict], frame_size=None, *, after_sources=None) -> list[dict]:
    """Apply geometry/class filters on a project-node branch, independent of IDs."""
    if after_sources is not None:
        from graphlib import TopologicalSorter
        nodes = {str(node.get("id") or ""): node for node in workflow.get("nodes", []) if node.get("enabled", True)}
        parents = {key: set() for key in nodes}
        for left, right in workflow.get("edges", []):
            if left in nodes and right in nodes:
                parents[right].add(left)
        order = tuple(TopologicalSorter(parents).static_order())
        result = []
        for source in after_sources:
            batches = {source: [item for item in detections if str(item.get("sourceNodeId") or "") == source]}
            for key in order:
                if key == source:
                    continue
                # Merge by identity so one event reaching two routes is emitted once.
                batch = list({id(item): item for parent in parents[key] for item in batches.get(parent, [])}.values())
                if nodes[key].get("type") == "filter":
                    batch = filter_detections(workflow, batch, frame_size, filter_node=nodes[key])
                elif nodes[key].get("type") == "detections_consensus":
                    from detections_consensus import apply_detections_consensus
                    batch = apply_detections_consensus(batch, nodes[key].get("config", {}))
                batches[key] = batch
            result.extend(batches.get(target_id, []))
        return result
    result = detections
    for node in workflow.get("nodes", []):
        if node.get("type") == "filter" and node.get("enabled", True) and has_active_path(
            workflow, str(node.get("id") or ""), target_id,
        ):
            result = filter_detections(workflow, result, frame_size, filter_node=node)
        elif node.get("type") == "detections_consensus" and node.get("enabled", True) and has_active_path(
            workflow, str(node.get("id") or ""), target_id,
        ):
            from detections_consensus import apply_detections_consensus
            result = apply_detections_consensus(result, node.get("config", {}))
    return result


def parse_per_class_confidence(raw_val: str | dict | None) -> dict[str, float]:
    """Parse format like 'person:0.75, tire:0.40, truck:0.60' or dict into {class: threshold}."""
    if isinstance(raw_val, dict):
        return {str(k).strip().lower(): float(v) for k, v in raw_val.items() if str(k).strip()}
    if not isinstance(raw_val, str) or not raw_val.strip():
        return {}
    result = {}
    for entry in raw_val.split(","):
        if ":" in entry:
            cls_name, score_str = entry.split(":", 1)
            cls_name = cls_name.strip().lower()
            try:
                score = float(score_str.strip())
                if cls_name:
                    result[cls_name] = max(0.0, min(1.0, score))
            except (TypeError, ValueError):
                continue
    return result


def filter_detections(workflow: dict, detections: list[dict], frame_size: tuple[int, int] | None = None, *, filter_node=None) -> list[dict]:
    filter_node = filter_node or active_filter_node(workflow)
    if not filter_node:
        return detections
    config = filter_node.get("config", {})
    classes = {
        item.strip().lower()
        for item in str(config.get("classes", "")).split(",")
        if item.strip()
    }
    min_area = float(config.get("minArea", 0) or 0)
    max_area = float(config.get("maxArea", 0) or 0)
    min_aspect = float(config.get("minAspectRatio", 0) or 0)
    max_aspect = float(config.get("maxAspectRatio", 0) or 0)
    border_margin = float(config.get("excludeBorderMargin", 0) or 0)

    # Per-Class Confidence & Default Confidence
    per_class_conf = parse_per_class_confidence(config.get("perClassConfidence"))
    default_conf = float(config.get("defaultConfidence", 0.0) or 0.0)

    # Detection Bounding Box Padding
    padding_percent = float(config.get("paddingPercent", 0.0) or 0.0)

    filtered = []
    for raw_item in detections:
        item = dict(raw_item)
        item_class = str(item.get("class", "")).lower()
        if classes and item_class not in classes:
            continue

        item_score = float(item.get("score", 0.0) or 0.0)
        if item_class in per_class_conf:
            if item_score < per_class_conf[item_class]:
                continue
        elif default_conf > 0.0:
            if item_score < default_conf:
                continue

        bbox = item.get("bbox")
        if bbox and len(bbox) >= 4:
            bx, by, bw, bh = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        else:
            bx = float(item.get("x", 0))
            by = float(item.get("y", 0))
            bw = float(item.get("width", 0))
            bh = float(item.get("height", 0))

        area = bw * bh
        if min_area > 0 and area < min_area:
            continue
        if max_area > 0 and area > max_area:
            continue

        aspect = bw / max(1.0, bh)
        if min_aspect > 0 and aspect < min_aspect:
            continue
        if max_aspect > 0 and aspect > max_aspect:
            continue

        if border_margin > 0 and frame_size:
            fw, fh = frame_size
            if bx < border_margin or by < border_margin or (bx + bw) > (fw - border_margin) or (by + bh) > (fh - border_margin):
                continue

        if padding_percent > 0.0:
            pad_fraction = padding_percent / 100.0
            dx = (bw * pad_fraction) / 2.0
            dy = (bh * pad_fraction) / 2.0
            new_bx = bx - dx
            new_by = by - dy
            new_bw = bw + (2.0 * dx)
            new_bh = bh + (2.0 * dy)

            if frame_size:
                fw, fh = frame_size
                clamped_x = max(0.0, new_bx)
                clamped_y = max(0.0, new_by)
                clamped_w = max(0.0, min(float(fw) - clamped_x, new_bw))
                clamped_h = max(0.0, min(float(fh) - clamped_y, new_bh))
            else:
                clamped_x = max(0.0, new_bx)
                clamped_y = max(0.0, new_by)
                clamped_w = new_bw
                clamped_h = new_bh

            item["rawBbox"] = [bx, by, bw, bh]
            item["bbox"] = [round(clamped_x, 2), round(clamped_y, 2), round(clamped_w, 2), round(clamped_h, 2)]

        filtered.append(item)

    return filtered if len(filtered) >= int(config.get("minCount", 1) or 1) else []


class ObjectTracker:
    """Thin VisoNode facade over Roboflow's maintained tracker library."""

    def __init__(self, tracker_node: dict) -> None:
        from roboflow_tracker import RoboflowTracker

        self._runtime = RoboflowTracker(tracker_node.get("config", {}))
        self.algorithm = self._runtime.algorithm

    def status_label(self) -> str:
        return self._runtime.status_label()

    def update(
        self,
        detections: list[dict],
        frame=None,
        *,
        frame_id: int | None = None,
        timestamp: float | None = None,
    ) -> list[dict]:
        return self._runtime.update(
            detections,
            frame,
            frame_id=frame_id,
            timestamp=timestamp,
        )

    def reset(self) -> None:
        self._runtime.reset()

ROBOFLOW_COLOR_PALETTE = (
    (41, 211, 145),   # Emerald / Mint
    (56, 189, 248),   # Sky blue
    (168, 85, 247),   # Purple
    (245, 158, 11),   # Amber
    (239, 68, 68),    # Rose / Red
    (99, 102, 241),   # Indigo
    (236, 72, 153),   # Pink
    (20, 184, 166),   # Teal
    (234, 179, 8),    # Yellow
    (139, 92, 246),   # Violet
    (59, 130, 246),   # Blue
    (16, 185, 129),   # Green
    (249, 115, 22),   # Orange
    (217, 70, 239),   # Fuchsia
    (6, 182, 212),    # Cyan
    (132, 204, 22),   # Lime
    (251, 146, 60),   # Light orange
    (147, 197, 253),  # Soft blue
    (196, 181, 253),  # Lavender
    (252, 165, 165),  # Soft red
    (110, 231, 183),  # Soft teal
    (253, 224, 71),   # Soft yellow
    (190, 242, 100),  # Soft lime
    (244, 114, 182),  # Soft pink
    (129, 140, 248),  # Soft indigo
    (52, 211, 153),   # Medium emerald
    (96, 165, 250),   # Medium sky
    (192, 132, 252),  # Medium purple
    (251, 191, 36),   # Medium amber
    (248, 113, 113),  # Medium red
    (45, 212, 191),   # Medium teal
    (163, 230, 53),   # Medium lime
)


def detection_color(label: str | int) -> tuple[int, int, int]:
    if isinstance(label, int):
        return ROBOFLOW_COLOR_PALETTE[label % len(ROBOFLOW_COLOR_PALETTE)]
    s = str(label)
    if ":" in s:
        parts = s.split(":")
        if len(parts) >= 2 and parts[-1].isdigit():
            return ROBOFLOW_COLOR_PALETTE[int(parts[-1]) % len(ROBOFLOW_COLOR_PALETTE)]
    index = sum(s.encode("utf-8")) % len(ROBOFLOW_COLOR_PALETTE)
    return ROBOFLOW_COLOR_PALETTE[index]


def roi_nodes_for_target(
    workflow: dict,
    target_id: str,
    *,
    require_overlay: bool = False,
) -> list[dict]:
    sources = [node.get("id", "") for node in active_inference_nodes(workflow)]
    tracker = active_tracking_node(workflow)
    filter_node = active_filter_node(workflow)
    if tracker:
        sources.append(tracker.get("id", ""))
    if filter_node:
        sources.append(filter_node.get("id", ""))
    return [
        node for node in workflow.get("nodes", [])
        if node.get("type") == "roi_filter"
        and node.get("enabled", True)
        and (not require_overlay or bool(node.get("config", {}).get("showOverlay", True)))
        and any(has_active_path(workflow, source_id, str(node.get("id", ""))) for source_id in sources)
        and has_active_path(workflow, str(node.get("id", "")), target_id)
    ]


def roi_crossing_count_for_target(workflow: dict, runtime: dict, target_id: str) -> int | None:
    total = 0
    found = False
    for node in roi_nodes_for_target(workflow, target_id):
        if node.get("config", {}).get("mode", "inside") != "crossing":
            continue
        node_id = str(node.get("id") or node.get("type") or "roi_filter")
        total += int(runtime.get(node_id, {}).get("total_count", 0))
        found = True
    return total if found else None


def roi_overlay_nodes_for_target(workflow: dict, target_id: str) -> list[dict]:
    """Return visible ROIs that share the target's active input stream.

    An ROI often feeds an alert or counter while Preview is connected as a
    parallel branch.  The region still belongs to the same video stream and
    should remain visible there even though the ROI is not upstream of Preview.
    """
    input_id = source_node_id(workflow)
    if not has_active_path(workflow, input_id, target_id):
        return []
    return [
        node for node in workflow.get("nodes", [])
        if node.get("type") == "roi_filter"
        and node.get("enabled", True)
        and bool(node.get("config", {}).get("showOverlay", True))
        and has_active_path(workflow, input_id, str(node.get("id", "")))
    ]


def draw_roi_overlays(
    frame,
    workflow: dict,
    target_id: str = "preview",
    runtime: dict | None = None,
) -> None:
    import cv2
    import numpy as np

    runtime = runtime or {}
    height, width = frame.shape[:2]
    for node in roi_overlay_nodes_for_target(workflow, target_id):
        roi = _roi_geometry(node.get("config", {}))
        if roi is None:
            continue
        color = (212, 179, 6)
        shape, geometry = roi
        if shape == "polygon":
            points = np.array([
                [
                    int(round(max(0, min(width - 1, x)))),
                    int(round(max(0, min(height - 1, y)))),
                ]
                for x, y in geometry
            ], dtype=np.int32)
            if len(points) < 3:
                continue
            box_x, box_y, box_w, box_h = cv2.boundingRect(points)
            label_x, label_y_base = points[:, 0].min(), points[:, 1].min()
        else:
            x1, y1, x2, y2 = geometry
            x1 = int(round(max(0, min(width - 1, x1))))
            y1 = int(round(max(0, min(height - 1, y1))))
            x2 = int(round(max(0, min(width, x2))))
            y2 = int(round(max(0, min(height, y2))))
            if x1 >= x2 or y1 >= y2:
                continue
            box_x, box_y, box_w, box_h = x1, y1, x2 - x1, y2 - y1
            label_x, label_y_base = x1, y1
        # Blend only the ROI's bounding rect instead of copying the full frame.
        sub = frame[box_y:box_y + box_h, box_x:box_x + box_w]
        if sub.size:
            overlay = sub.copy()
            if shape == "polygon":
                cv2.fillPoly(overlay, [points - (box_x, box_y)], color)
            else:
                cv2.rectangle(overlay, (0, 0), (box_w, box_h), color, -1)
            cv2.addWeighted(overlay, 0.10, sub, 0.90, 0, dst=sub)
        if shape == "polygon":
            cv2.polylines(frame, [points], True, color, 2)
        else:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = str(node.get("title") or "ROI")
        if node.get("config", {}).get("mode", "inside") == "crossing":
            node_id = str(node.get("id") or node.get("type") or "roi_filter")
            count = int(runtime.get(node_id, {}).get("total_count", 0))
            label = f"{label}: {count}"
        text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        label_x = int(max(0, min(width - text_size[0] - 10, label_x)))
        label_y = int(max(0, label_y_base - text_size[1] - 8))
        cv2.rectangle(frame, (label_x, label_y), (label_x + text_size[0] + 10, label_y + text_size[1] + 8), (8, 18, 27), -1)
        cv2.putText(frame, label, (label_x + 5, label_y + text_size[1] + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)


def _drawing_color(value: object, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    text = str(value or "").strip().lstrip("#")
    if len(text) == 6:
        try:
            red, green, blue = (int(text[index:index + 2], 16) for index in (0, 2, 4))
            return blue, green, red
        except ValueError:
            pass
    return fallback


def drawing_template_values(frame, detections: list[dict], current: dict | None = None) -> dict[str, str]:
    """Resolve stable, user-facing values for drawing templates."""
    height, width = frame.shape[:2]
    classifications = [
        item for item in detections
        if item.get("kind") in ("classification", "object_classification")
    ]
    boxes = _overlay_objects(detections)
    best_classification = max(
        classifications, key=lambda item: float(item.get("score", 0.0) or 0.0),
        default=None,
    )
    best_detection = current or max(
        boxes, key=lambda item: float(item.get("score", 0.0) or 0.0), default=None,
    )
    values = {
        "image.width": str(width),
        "image.height": str(height),
        "detection.count": str(len(boxes)),
        "classification.class": "—",
        "classification.confidence": "—",
        "detection.class": "—",
        "detection.confidence": "—",
        "detection.x": "—",
        "detection.y": "—",
        "detection.width": "—",
        "detection.height": "—",
        "track.id": "—",
        "count.total": "—",
        "anomaly.result": "—", "anomaly.score": "—", "anomaly.threshold": "—",
    }
    anomaly_candidates = [item for item in detections if item.get("kind") == "anomaly"]
    if current is not None:
        anomaly_candidates = [current] if current.get("kind") == "anomaly" else [
            item for item in anomaly_candidates
            if _detection_box_xywh(item) == _detection_box_xywh(current)
            and _detection_box_xywh(current) is not None
        ]
    anomaly = max(anomaly_candidates,
                  key=lambda item: item["anomalyScore"], default=None)
    if anomaly is not None:
        values.update({"anomaly.result": anomaly["result"],
                       "anomaly.score": f"{anomaly['anomalyScore']:.4f}",
                       "anomaly.threshold": f"{anomaly['threshold']:.4f}"})
    if best_classification is not None:
        values["classification.class"] = str(best_classification.get("class") or "")
        values["classification.confidence"] = f"{float(best_classification.get('score', 0.0) or 0.0) * 100:.1f}%"
    if best_detection is not None:
        box = _detection_box_xywh(best_detection)
        if box is not None:
            x, y, box_width, box_height = box
            values.update({
                "detection.class": str(best_detection.get("class") or "object"),
                "detection.confidence": f"{float(best_detection.get('score', 0.0) or 0.0) * 100:.1f}%",
                "detection.x": str(int(round(x))),
                "detection.y": str(int(round(y))),
                "detection.width": str(int(round(box_width))),
                "detection.height": str(int(round(box_height))),
                "track.id": str(best_detection.get("trackId", "—")),
            })
    count_events = [item for item in detections if item.get("objectCount") is not None]
    if count_events:
        values["count.total"] = str(max(int(item.get("objectCount", 0)) for item in count_events))
    return values


def format_drawing_template(
    template: object,
    frame,
    detections: list[dict],
    current: dict | None = None,
) -> str:
    values = drawing_template_values(frame, detections, current)
    return re.sub(
        r"\{([a-z][a-z0-9_.]*)\}",
        lambda match: values.get(match.group(1).lower(), match.group(0)),
        str(template or ""),
        flags=re.IGNORECASE,
    )


def _overlay_objects(detections: list[dict]) -> list[dict]:
    """Return one best annotation object per box, preferring downstream results."""
    ranked: dict[tuple[float, float, float, float], tuple[int, int, dict]] = {}
    kind_rank = {
        "detection": 1,
        "segmentation": 1,
        "classification": 2,
        "object_classification": 3,
        "anomaly": 4,
    }
    for index, item in enumerate(detections):
        if item.get("kind") in ("zone_activity", "zone_activity_event", "zone_exit"):
            continue
        box = _detection_box_xywh(item)
        if box is None:
            continue
        key = tuple(round(float(value), 3) for value in box)
        candidate = (kind_rank.get(str(item.get("kind") or ""), 0), index, item)
        if key not in ranked or candidate[:2] > ranked[key][:2]:
            ranked[key] = candidate
    return [candidate[2] for candidate in sorted(ranked.values(), key=lambda value: value[1])]


def _overlay_class_filter_matches(layer: dict, item: dict) -> bool:
    classes = {
        value.strip().lower()
        for value in str(layer.get("classes") or "").split(",")
        if value.strip()
    }
    return not classes or str(item.get("class") or "").strip().lower() in classes


def _draw_overlay_caption(
    cv2,
    output,
    text: str,
    item: dict,
    color: tuple[int, int, int],
    scale: float,
    offsets: dict[tuple[int, int, int, int], int],
    position: str = "top",
) -> None:
    if not text:
        return
    box = _detection_box_xywh(item)
    if box is None:
        return
    x, y, width, height = (int(round(value)) for value in box)
    key = (x, y, width, height)
    row = offsets.get(key, 0)
    thickness = max(1, int(round(scale * 3)))
    text_size, baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    row_height = text_size[1] + baseline + 9
    left = x
    if position == "top_left":
        top = y + row * row_height
    elif position in ("bottom_left", "bottom_right"):
        top = y + height + row * row_height
    elif position == "center":
        top = y + max(0, (height - row_height) // 2) + row * row_height
    else:
        top = y - row_height * (row + 1)
        if top < 0:
            top = y + height + row * row_height
    if position in ("top_right", "bottom_right"):
        left = x + width - text_size[0] - 10
    elif position == "center":
        left = x + (width - text_size[0] - 10) // 2
    left = max(0, min(output.shape[1] - text_size[0] - 10, left))
    top = max(0, min(output.shape[0] - row_height, top))
    right = min(output.shape[1] - 1, left + text_size[0] + 10)
    cv2.rectangle(output, (left, top), (right, min(output.shape[0] - 1, top + row_height)), color, -1)
    cv2.putText(
        output,
        text,
        (left + 5, min(output.shape[0] - 1, top + text_size[1] + 3)),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )
    offsets[key] = row + 1


def _apply_overlay_node(output, node: dict, detections: list[dict]) -> None:
    """Render an Overlay / Annotate node's ordered instruction stack."""
    import cv2

    config = normalize_overlay_config(node.setdefault("config", {}))
    objects = _overlay_objects(detections)
    caption_offsets: dict[tuple[int, int, int, int], int] = {}
    for layer in config.get("layers", []):
        if not layer.get("enabled", True):
            continue
        layer_type = layer.get("type")
        matching = [item for item in objects if _overlay_class_filter_matches(layer, item)]
        if layer_type == "bounding_boxes":
            color = _drawing_color(layer.get("color"), (235, 99, 37))
            thickness = max(1, int(layer.get("thickness", 2) or 1))
            opacity = max(0.0, min(0.8, float(layer.get("fillOpacity", 0.0) or 0.0)))
            for item in matching:
                box = _detection_box_xywh(item)
                if box is None:
                    continue
                x, y, width, height = (int(round(value)) for value in box)
                if opacity > 0:
                    overlay = output.copy()
                    cv2.rectangle(overlay, (x, y), (x + width, y + height), color, -1)
                    cv2.addWeighted(overlay, opacity, output, 1.0 - opacity, 0, output)
                cv2.rectangle(output, (x, y), (x + width, y + height), color, thickness)
        elif layer_type in ("labels", "confidence"):
            fallback = (94, 197, 34) if layer_type == "labels" else (237, 51, 124)
            color = _drawing_color(layer.get("color"), fallback)
            scale = max(0.25, min(8.0, float(layer.get("fontScale", 0.55) or 0.55)))
            for item in matching:
                text = format_drawing_template(
                    layer.get("template", ""), output, detections, item,
                )
                _draw_overlay_caption(
                    cv2,
                    output,
                    text,
                    item,
                    color,
                    scale,
                    caption_offsets,
                    str(layer.get("position") or ("top" if layer_type == "labels" else "below_label")),
                )
        elif layer_type == "result_icons":
            pass_classes = {
                value.strip().lower()
                for value in str(layer.get("passClasses") or "ok, pass, good").split(",")
                if value.strip()
            }
            scale = max(0.25, min(8.0, float(layer.get("size", 0.65) or 0.65)))
            for item in matching:
                box = _detection_box_xywh(item)
                if box is None:
                    continue
                passed = str(item.get("class") or "").strip().lower() in pass_classes
                text = str(layer.get("passText" if passed else "failText") or ("OK" if passed else "X"))
                color = _drawing_color(
                    layer.get("passColor" if passed else "failColor"),
                    (94, 197, 34) if passed else (68, 68, 239),
                )
                x, y, width, _height = (int(round(value)) for value in box)
                text_size, baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
                position = str(layer.get("position") or "top_right")
                right = min(output.shape[1] - 1, x + width)
                left = max(0, right - text_size[0] - 10)
                top = max(0, y)
                if position in ("top", "top_left", "bottom_left"):
                    left = max(0, x)
                    right = min(output.shape[1] - 1, left + text_size[0] + 10)
                if position in ("bottom_left", "bottom_right"):
                    top = max(0, y + int(round(box[3])) - text_size[1] - baseline - 8)
                elif position == "center":
                    left = max(0, x + (width - text_size[0] - 10) // 2)
                    right = min(output.shape[1] - 1, left + text_size[0] + 10)
                    top = max(0, y + (int(round(box[3])) - text_size[1] - baseline - 8) // 2)
                bottom = min(output.shape[0] - 1, top + text_size[1] + baseline + 8)
                cv2.rectangle(output, (left, top), (right, bottom), color, -1)
                cv2.putText(output, text, (left + 5, top + text_size[1] + 2), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 2, cv2.LINE_AA)
        elif layer_type == "custom_text":
            if layer.get("classes") and not any(
                _overlay_class_filter_matches(layer, item) for item in detections
            ):
                continue
            text = format_drawing_template(layer.get("template", ""), output, detections)
            x = max(0, int(layer.get("x", 24) or 0))
            y = max(0, int(layer.get("y", 48) or 0))
            scale = max(0.1, float(layer.get("fontScale", 1.0) or 1.0))
            thickness = max(1, int(layer.get("thickness", 2) or 1))
            color = _drawing_color(layer.get("color"), (255, 255, 255))
            text_size, baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
            position = str(layer.get("position") or "bottom_right")
            if position != "custom":
                margin = 24
                if position in ("top", "top_left", "top_right"):
                    y = margin + text_size[1]
                elif position in ("bottom_left", "bottom_right"):
                    y = max(text_size[1], output.shape[0] - margin)
                elif position == "center":
                    y = max(text_size[1], (output.shape[0] + text_size[1]) // 2)
                if position in ("top_right", "bottom_right"):
                    x = max(0, output.shape[1] - text_size[0] - margin)
                elif position in ("top", "top_left", "bottom_left"):
                    x = margin
                elif position == "center":
                    x = max(0, (output.shape[1] - text_size[0]) // 2)
            if layer.get("background", True):
                background = _drawing_color(layer.get("backgroundColor"), (39, 27, 17))
                cv2.rectangle(output, (max(0, x - 6), max(0, y - text_size[1] - 7)), (x + text_size[0] + 6, y + baseline + 5), background, -1)
            cv2.putText(output, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)
        elif layer_type == "vector_arrow":
            color = _drawing_color(layer.get("color"), (248, 189, 56))
            thickness = max(1, int(layer.get("thickness", 2) or 2))
            scale = max(0.5, float(layer.get("scale", 1.5) or 1.5))
            for item in matching:
                trail = item.get("trail")
                if trail and len(trail) >= 2:
                    p_prev = trail[-2]
                    p_curr = trail[-1]
                    dx = (p_curr[0] - p_prev[0]) * scale
                    dy = (p_curr[1] - p_prev[1]) * scale
                    p1 = (int(round(p_curr[0])), int(round(p_curr[1])))
                    p2 = (int(round(p_curr[0] + dx)), int(round(p_curr[1] + dy)))
                    if abs(dx) > 1 or abs(dy) > 1:
                        cv2.arrowedLine(output, p1, p2, color, thickness, tipLength=0.35)
        elif layer_type == "heatmap":
            import numpy as np
            opacity = max(0.05, min(0.95, float(layer.get("opacity", 0.40) or 0.40)))
            decay = max(0.80, min(0.999, float(layer.get("decay", 0.98) or 0.98)))
            colormap_name = str(layer.get("colormap", "jet")).lower()
            cmap = cv2.COLORMAP_JET if colormap_name == "jet" else (cv2.COLORMAP_HOT if colormap_name == "hot" else cv2.COLORMAP_TURBO)
            h, w = output.shape[:2]
            heatmap_mat = node.setdefault("_heatmap_matrix", None)
            if heatmap_mat is None or heatmap_mat.shape != (max(1, h // 2), max(1, w // 2)):
                heatmap_mat = np.zeros((max(1, h // 2), max(1, w // 2)), dtype=np.float32)
                node["_heatmap_matrix"] = heatmap_mat
            heatmap_mat *= decay
            for item in matching:
                box = _detection_box_xywh(item)
                if box:
                    cx = int(round((box[0] + box[2] / 2) / 2))
                    cy = int(round((box[1] + box[3] / 2) / 2))
                    if 0 <= cx < (w // 2) and 0 <= cy < (h // 2):
                        radius = max(3, int(round(min(box[2], box[3]) / 4)))
                        y_min, y_max = max(0, cy - radius), min(h // 2, cy + radius)
                        x_min, x_max = max(0, cx - radius), min(w // 2, cx + radius)
                        heatmap_mat[y_min:y_max, x_min:x_max] += 0.25
            max_v = float(np.max(heatmap_mat))
            if max_v > 0.01:
                norm = np.clip(heatmap_mat / max_v, 0, 1)
                colored_heat = cv2.applyColorMap((norm * 255).astype(np.uint8), cmap)
                colored_heat = cv2.resize(colored_heat, (w, h), interpolation=cv2.INTER_LINEAR)
                mask = cv2.resize(norm, (w, h), interpolation=cv2.INTER_LINEAR)
                mask_3ch = np.dstack([mask, mask, mask])
                blended = cv2.addWeighted(output, 1.0 - opacity, colored_heat, opacity, 0)
                output[:] = np.where(mask_3ch > 0.05, blended, output)


def apply_drawing_nodes(frame, workflow: dict, target_id: str, detections: list[dict], runtime: dict | None = None, *, copy_frame: bool = True):
    """Apply OpenCV-style drawing nodes connected before the target."""
    import cv2

    nodes = active_drawing_nodes_for_target(workflow, target_id)
    if not nodes:
        return frame
    runtime = runtime if runtime is not None else {}
    output = frame.copy() if copy_frame else frame
    for node in nodes:
        config = node.get("config", {})
        node_id = str(node.get("id") or "")
        node_detections = [
            item for item in detections
            if has_active_path(
                workflow,
                str(item.get("sourceNodeId") or item.get("parentSourceNodeId") or "detector"),
                node_id,
            )
        ]
        gates = active_logic_nodes_for_target(workflow, node_id)
        if gates:
            node_detections = apply_logic_nodes(workflow, node_id, node_detections, runtime)
        if any(
            gate.get("type") != "roi_filter"
            and not runtime.get(str(gate.get("id") or gate.get("type") or "logic"), {}).get("last_signal", False)
            for gate in gates
        ):
            continue
        if node.get("type") == "overlay_annotate":
            _apply_overlay_node(output, node, node_detections)
        elif node.get("type") == "draw_text":
            text = format_drawing_template(config.get("textTemplate", ""), output, node_detections)
            x = max(0, int(config.get("x", 24) or 0))
            y = max(0, int(config.get("y", 48) or 0))
            scale = max(0.1, float(config.get("fontScale", 1.0) or 1.0))
            thickness = max(1, int(config.get("thickness", 2) or 1))
            color = _drawing_color(config.get("color"), (255, 255, 255))
            text_size, baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
            if config.get("background", True):
                background = _drawing_color(config.get("backgroundColor"), (39, 27, 17))
                cv2.rectangle(
                    output,
                    (x - 6, max(0, y - text_size[1] - 7)),
                    (x + text_size[0] + 6, y + baseline + 5),
                    background,
                    -1,
                )
            cv2.putText(output, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)
        elif node.get("type") == "draw_boxes":
            color = _drawing_color(config.get("color"), (94, 197, 34))
            thickness = max(1, int(config.get("thickness", 2) or 1))
            opacity = max(0.0, min(0.8, float(config.get("fillOpacity", 0.0) or 0.0)))
            for detection in node_detections:
                box = _detection_box_xywh(detection)
                if box is None:
                    continue
                x, y, width, height = (int(round(value)) for value in box)
                if opacity > 0:
                    overlay = output.copy()
                    cv2.rectangle(overlay, (x, y), (x + width, y + height), color, -1)
                    cv2.addWeighted(overlay, opacity, output, 1.0 - opacity, 0, output)
                cv2.rectangle(output, (x, y), (x + width, y + height), color, thickness)
                if config.get("showLabel", True):
                    label = format_drawing_template(
                        config.get("labelTemplate", ""), output, node_detections, detection,
                    )
                    label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                    label_y = max(label_size[1] + 8, y)
                    cv2.rectangle(
                        output,
                        (x, label_y - label_size[1] - 8),
                        (x + label_size[0] + 10, label_y + baseline),
                        color,
                        -1,
                    )
                    cv2.putText(output, label, (x + 5, label_y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
    return output


def preview_style_before_drawing_nodes(workflow: dict, target_id: str, preview: dict) -> dict:
    """Avoid default preview marks duplicated by explicit drawing layers."""
    owns_boxes = False
    owns_labels = False
    for node in active_drawing_nodes_for_target(workflow, target_id):
        if node.get("type") == "draw_boxes":
            owns_boxes = True
            owns_labels = bool(node.get("config", {}).get("showLabel", True))
        elif node.get("type") == "overlay_annotate":
            layers = normalize_overlay_config(node.setdefault("config", {})).get("layers", [])
            enabled_types = {layer.get("type") for layer in layers if layer.get("enabled", True)}
            owns_boxes = owns_boxes or "bounding_boxes" in enabled_types
            owns_labels = owns_labels or bool(enabled_types & {"labels", "confidence", "result_icons"})
    if not owns_boxes and not owns_labels:
        return preview
    return {
        **preview,
        "config": {
            **preview.get("config", {}),
            "showBoxes": not owns_boxes and preview.get("config", {}).get("showBoxes", True),
            "showLabels": not owns_labels and preview.get("config", {}).get("showLabels", True),
        },
    }


def _draw_object_count_overlay(
    frame,
    detections: list[dict],
    counter_state: dict | None = None,
) -> None:
    """Render a modern HUD badge in the top-right corner with class names and quantities."""
    import cv2

    display_counts: dict[str, int] = {}
    total_cumulative: int | None = None

    if counter_state:
        raw_display = counter_state.get("display_counts") or counter_state.get("class_counts") or {}
        frame_counts = counter_state.get("frame_counts") or {}
        display_counts = dict(raw_display if raw_display else frame_counts)
        total_cumulative = counter_state.get("total_count")

    if not display_counts:
        for d in detections:
            if d.get("kind") in ("anomaly", "classification", "zone_activity", "zone_activity_event", "zone_exit"):
                continue
            cls_name = str(d.get("class") or "object").strip()
            display_counts[cls_name] = display_counts.get(cls_name, 0) + 1

    if not display_counts and not counter_state:
        return

    frame_h, frame_w = frame.shape[:2]
    if frame_h < 60 or frame_w < 100:
        return

    lines: list[tuple[str, str, tuple[int, int, int]]] = []
    total_qty = 0
    for cls_name, qty in sorted(display_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append((cls_name, str(qty), detection_color(cls_name)))
        total_qty += qty

    font = cv2.FONT_HERSHEY_SIMPLEX
    header_scale = 0.44
    item_scale = 0.52
    total_scale = 0.52
    line_height = 24
    header_height = 26
    show_footer = len(lines) > 1 or total_cumulative is not None
    footer_height = 26 if show_footer else 0

    pad_x = 14
    pad_y = 10
    box_h = pad_y * 2 + header_height + max(1, len(lines)) * line_height + footer_height

    max_w = 140
    for cls_name, qty_str, _ in lines:
        text = f"{cls_name}: {qty_str}"
        tw = cv2.getTextSize(text, font, item_scale, 1)[0][0]
        max_w = max(max_w, tw + 45)

    box_w = max(160, min(max_w + pad_x * 2, frame_w - 20))
    margin_right = 14
    margin_top = 14

    x2 = frame_w - margin_right
    x1 = max(0, x2 - box_w)
    y1 = margin_top
    y2 = min(frame_h, y1 + box_h)

    is_overcap = bool(counter_state.get("is_overcapacity", False)) if counter_state else False
    is_occupancy = bool(counter_state.get("mode") == "occupancy") if counter_state else True
    max_cap = int(counter_state.get("max_capacity", 0) or 0) if counter_state else 0

    # Semi-transparent dark background
    sub = frame[y1:y2, x1:x2]
    if sub.shape[0] > 0 and sub.shape[1] > 0:
        overlay = sub.copy()
        overlay[:] = (24, 18, 12)  # Dark slate BGR
        cv2.addWeighted(overlay, 0.82, sub, 0.18, 0, dst=sub)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 239) if is_overcap else (75, 75, 90), 1)
        # Accent top bar: Red if overcapacity, vibrant cyan if normal
        cv2.rectangle(frame, (x1, y1), (x2, y1 + 3), (0, 0, 239) if is_overcap else (235, 140, 20), -1)

    cur_y = y1 + pad_y + 14
    dot_color = (0, 0, 239) if is_overcap else (50, 205, 50)
    badge_title = "CAPACITY EXCEEDED!" if is_overcap else ("LIVE OCCUPANCY" if is_occupancy else "OBJECT COUNT")
    cv2.circle(frame, (x1 + pad_x + 2, cur_y - 4), 4, dot_color, -1)
    cv2.putText(frame, badge_title, (x1 + pad_x + 12, cur_y), font, header_scale, (0, 200, 255) if is_overcap else (200, 210, 220), 1, cv2.LINE_AA)

    div_y = cur_y + 6
    cv2.line(frame, (x1 + pad_x, div_y), (x2 - pad_x, div_y), (60, 60, 75), 1)
    cur_y = div_y + 18

    if not lines:
        cv2.putText(frame, "No objects", (x1 + pad_x, cur_y), font, 0.48, (140, 140, 150), 1, cv2.LINE_AA)
    else:
        for cls_name, qty_str, color in lines:
            cv2.circle(frame, (x1 + pad_x + 4, cur_y - 4), 4, color, -1)
            cv2.putText(frame, cls_name, (x1 + pad_x + 14, cur_y), font, item_scale, (240, 240, 240), 1, cv2.LINE_AA)
            qw = cv2.getTextSize(qty_str, font, item_scale, 2)[0][0]
            qty_x = x2 - pad_x - qw
            cv2.putText(frame, qty_str, (qty_x, cur_y), font, item_scale, (100, 255, 100), 2, cv2.LINE_AA)
            cur_y += line_height

    if show_footer:
        cv2.line(frame, (x1 + pad_x, cur_y - 8), (x2 - pad_x, cur_y - 8), (60, 60, 75), 1)
        if max_cap > 0:
            tot_label = f"Cap {total_qty}/{max_cap}"
            tot_val = "OVERFLOW" if is_overcap else "OK"
            val_color = (0, 0, 239) if is_overcap else (50, 205, 50)
        else:
            tot_label = "Live Total" if is_occupancy else ("Total Tracked" if (total_cumulative is not None and total_cumulative > total_qty) else "Total")
            tot_val = str(total_qty if is_occupancy else (total_cumulative if total_cumulative is not None else total_qty))
            val_color = (255, 215, 0)
        cv2.putText(frame, tot_label, (x1 + pad_x, cur_y + 8), font, total_scale, (180, 200, 210), 1, cv2.LINE_AA)
        tw = cv2.getTextSize(tot_val, font, total_scale, 2)[0][0]
        cv2.putText(frame, tot_val, (x2 - pad_x - tw, cur_y + 8), font, total_scale, val_color, 2, cv2.LINE_AA)


def draw_detections(frame, detections: list[dict], preview: dict, counter_state: dict | None = None) -> None:
    import cv2
    import numpy as np

    config = preview.get("config", {})
    show_boxes = bool(config.get("showBoxes", True))
    show_labels = bool(config.get("showLabels", True))
    show_masks = bool(config.get("showMasks", True))
    show_track_ids = bool(config.get("showTrackIds", True))
    show_trails = bool(config.get("showTrails", True))
    show_counts = bool(config.get("showCounts", True))
    mask_opacity = min(0.85, max(0.05, float(config.get("maskOpacity", 0.35))))
    classification_y = 12
    for detection in detections:
        if detection.get("kind") in ("count_event", "line_crossing", "loitering_alert", "zone_activity", "zone_activity_event", "zone_exit"):
            continue
        if detection.get("kind") == "anomaly":
            from efficientad_runtime import draw_result
            classification_y = draw_result(frame, detection, show_labels=show_labels, y=classification_y,
                                           show_boxes=show_boxes, show_track_ids=show_track_ids)
            continue
        label_text = detection.get("class", "object")
        track_id = detection.get("trackId")
        color_key = f"{label_text}:{track_id}" if track_id is not None else label_text
        color = detection_color(color_key)
        if "boxColor" in detection:
            custom_c = detection["boxColor"]
            if isinstance(custom_c, (list, tuple)) and len(custom_c) >= 3:
                color = tuple(int(c) for c in custom_c[:3])
            elif isinstance(custom_c, str) and custom_c.startswith("#"):
                h = custom_c.lstrip("#")
                if len(h) == 6:
                    color = (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))

        label = f"{label_text} {round(float(detection.get('score', 0)) * 100)}%"
        if show_track_ids and track_id is not None:
            label = f"#{track_id} {label}"
        if "lineDirection" in detection:
            label = f"{label} [{detection['lineDirection']}]"
        if detection.get("kind") == "classification":
            if show_labels:
                text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
                x = 12
                y = classification_y
                cv2.rectangle(frame, (x, y), (x + text_size[0] + 14, y + text_size[1] + 12), (8, 18, 27), -1)
                cv2.rectangle(frame, (x, y), (x + text_size[0] + 14, y + text_size[1] + 12), color, 2)
                cv2.putText(frame, label, (x + 7, y + text_size[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                classification_y += text_size[1] + 18
            continue

        x, y, width, height = [int(round(value)) for value in detection.get("bbox", [0, 0, 0, 0])]
        mask = detection.get("mask")
        if show_masks and mask:
            points = np.array(mask, dtype=np.int32).reshape((-1, 1, 2))
            frame_height, frame_width = frame.shape[:2]
            box_x, box_y, box_w, box_h = cv2.boundingRect(points)
            x0 = max(0, box_x)
            y0 = max(0, box_y)
            x1 = min(frame_width, box_x + box_w)
            y1 = min(frame_height, box_y + box_h)
            if x1 > x0 and y1 > y0:
                sub = frame[y0:y1, x0:x1]
                overlay = sub.copy()
                cv2.fillPoly(overlay, [points - (x0, y0)], color)
                cv2.addWeighted(overlay, mask_opacity, sub, 1 - mask_opacity, 0, dst=sub)
            cv2.polylines(frame, [points], True, color, 2)
        if show_boxes:
            # Main rectangle
            box_thick = 2 if "lineDirection" in detection else 1
            cv2.rectangle(frame, (x, y), (x + width, y + height), color, box_thick)
            # Modern prominent corner brackets (4 corners)
            corner_len = min(16, max(4, width // 4), max(4, height // 4))
            if corner_len >= 4:
                # Top-Left
                cv2.line(frame, (x, y), (x + corner_len, y), color, 3, cv2.LINE_AA)
                cv2.line(frame, (x, y), (x, y + corner_len), color, 3, cv2.LINE_AA)
                # Top-Right
                cv2.line(frame, (x + width, y), (x + width - corner_len, y), color, 3, cv2.LINE_AA)
                cv2.line(frame, (x + width, y), (x + width, y + corner_len), color, 3, cv2.LINE_AA)
                # Bottom-Left
                cv2.line(frame, (x, y + height), (x + corner_len, y + height), color, 3, cv2.LINE_AA)
                cv2.line(frame, (x, y + height), (x, y + height - corner_len), color, 3, cv2.LINE_AA)
                # Bottom-Right
                cv2.line(frame, (x + width, y + height), (x + width - corner_len, y + height), color, 3, cv2.LINE_AA)
                cv2.line(frame, (x + width, y + height), (x + width, y + height - corner_len), color, 3, cv2.LINE_AA)
        trail = detection.get("trail")
        if show_trails and trail and len(trail) >= 2:
            pts_count = len(trail)
            for i in range(pts_count - 1):
                p_start = (int(round(trail[i][0])), int(round(trail[i][1])))
                p_end = (int(round(trail[i + 1][0])), int(round(trail[i + 1][1])))
                progress = (i + 1) / pts_count
                thick = 1 if progress < 0.4 else (2 if progress < 0.8 else 3)
                cv2.line(frame, p_start, p_end, color, thick, cv2.LINE_AA)
                if i % 2 == 0:
                    cv2.circle(frame, p_start, max(1, int(round(2.5 * progress))), color, -1, cv2.LINE_AA)
            cv2.circle(frame, (int(round(trail[-1][0])), int(round(trail[-1][1]))), 3, (255, 255, 255), -1, cv2.LINE_AA)
        if show_labels:
            text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.46, 1)
            bg_w = text_size[0] + 12
            bg_h = text_size[1] + 8
            label_y = max(bg_h + 4, y - 6)
            # Modern studio pill with color indicator
            cv2.rectangle(frame, (x, label_y - bg_h), (x + bg_w, label_y), (15, 23, 42), -1)
            cv2.rectangle(frame, (x, label_y - bg_h), (x + 3, label_y), color, -1)
            cv2.rectangle(frame, (x, label_y - bg_h), (x + bg_w, label_y), (50, 65, 85), 1)
            cv2.putText(frame, label, (x + 7, label_y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1, cv2.LINE_AA)

    if show_counts:
        _draw_object_count_overlay(frame, detections, counter_state=counter_state)


class WorkflowRunner:
    def __init__(self) -> None:
        self._lock = Lock()
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._status = {
            "running": False,
            "state": "idle",
            "fps": 0,
            "objectCount": 0,
            "model": None,
            "device": "CPU",
            "error": None,
            "events": [],
        }

    def start(self, workflow: dict) -> dict:
        self.stop()
        workflow = normalize_workflow(workflow)
        if any(node.get("type") in (FRAME_SAMPLER_NODE_TYPE, "python_script") for node in workflow.get("nodes", [])):
            raise RuntimeError("Frame Sampler and Python Script nodes require the threaded runtime.")
        if not active_input_node(workflow):
            raise ValueError("Input node is disabled.")

        self._stop_event = Event()
        with self._lock:
            self._status.update({
                "running": True,
                "state": "starting",
                "fps": 0,
                "objectCount": 0,
                "model": None,
                "device": "CPU",
                "error": None,
                "events": [],
            })
        self._add_terminal("Workflow launched from desktop Run button")
        self._add_terminal("Starting workflow runner")
        self._thread = Thread(target=self._run, args=(workflow,), daemon=True)
        self._thread.start()
        return self.status()

    def stop(self) -> dict:
        thread = self._thread
        if thread and thread.is_alive():
            self._stop_event.set()
            thread.join(timeout=5)
        self._thread = None
        with self._lock:
            if self._status["state"] != "error":
                self._status.update({"running": False, "state": "stopped", "fps": 0, "objectCount": 0})
        return self.status()

    def status(self) -> dict:
        with self._lock:
            return dict(
                self._status,
                events=list(self._status["events"]),
            )

    def _run(self, workflow: dict) -> None:
        import cv2

        input_source = None
        video_output = None
        window_name = "VisoNode"
        last_fps_at = time.monotonic()
        frame_count = 0
        total_frame_index = 0
        crop_last_inference: dict[tuple[str, str], float] = {}
        last_alert_at = 0.0
        last_terminal_detection_at = 0.0
        last_slow_inference_at = 0.0
        first_frame_logged = False
        first_inference_logged = False
        detections: list[dict] = []
        tracked: list[dict] = []
        filtered: list[dict] = []
        tracker_runtime: ObjectTracker | None = None
        tracker_signature: str | None = None
        vlm_tracker_runtime: Any | None = None
        vlm_tracker_signature: str | None = None
        processing_runtime: dict = {}
        logic_runtime: dict = {}
        video_output_initialized = False
        try:
            input_node = active_input_node(workflow)
            input_source = OpenCVInputSource(cv2, input_node.get("config", {}))
            source_label, actual_width, actual_height = input_source.open()
            self._add_terminal(f"Opened {source_label} ({actual_width}x{actual_height})")
            preview_node = enabled_node(workflow, "preview")

            inference_nodes = active_inference_nodes(workflow)
            frame_inference_nodes = active_frame_inference_nodes(workflow)
            detection_crop_bindings = active_pretracking_detection_crop_bindings(workflow)
            if inference_nodes:
                loaded_models = []
                device_labels = []
                for inference_node in inference_nodes:
                    engine = inference_node.get("config", {}).get("engine", "rfdetr")
                    if engine not in ("sam3", "rfdetr", "rfdetr_tensorrt", "rfdetr_onnx", "convnext", "efficientad"):
                        raise RuntimeError(f"Backend runtime does not support inference engine '{engine}'.")
                    if engine == "sam3" and inference_node.get("type") != "segmenter":
                        raise RuntimeError("SAM 3 is available only on the Object Segmentation node.")
                    if engine == "rfdetr" and inference_node.get("type") not in ("detector", "segmenter"):
                        raise RuntimeError("RF-DETR is available only on Object Detection and Object Segmentation nodes.")
                    if engine in ("rfdetr_tensorrt", "rfdetr_onnx") and inference_node.get("type") not in ("detector", "segmenter"):
                        raise RuntimeError("RF-DETR exports are available only on Object Detection and Object Segmentation nodes.")
                    if engine == "efficientad" and inference_node.get("type") != "efficientad":
                        raise RuntimeError("EfficientAD is available only on the Anomaly Detection node.")
                    if engine == "convnext" and inference_node.get("type") != "classifier":
                        raise RuntimeError("ConvNeXt is available only on the Image Classification node.")
                    config = inference_node.get("config", {})
                    model_name = inference_model_name(inference_node)
                    device, device_label = resolve_inference_device(inference_node.get("config", {}))
                    task_labels = {"segmenter": "segmentation", "classifier": "classification", "efficientad": "EfficientAD anomaly inspection"}
                    task_label = task_labels.get(inference_node.get("type"), "detector")
                    if engine == "sam3":
                        task_label = f"SAM 3 {task_label}"
                    elif engine == "rfdetr":
                        task_label = f"RF-DETR {task_label}"
                    elif engine == "rfdetr_tensorrt":
                        task_label = f"RF-DETR TensorRT {task_label}"
                    elif engine == "rfdetr_onnx":
                        task_label = f"RF-DETR ONNX {task_label}"
                    elif engine == "convnext":
                        task_label = f"ConvNeXt {task_label}"
                    self._add_terminal(f"Loading {task_label} model {model_name}")
                    self._add_terminal(f"Using inference device {device_label}")
                    load_started_at = time.monotonic()
                    if engine == "sam3":
                        concepts = ", ".join(sam3_concepts(config))
                        self._add_terminal(f"SAM 3 concept prompt(s): {concepts}")
                        load_sam3_processor(config, device)
                    elif engine == "rfdetr":
                        rfdetr_model_name = config.get("rfdetrModel") or default_rfdetr_model(inference_node.get("type", "detector"))
                        load_rfdetr_model(
                            rfdetr_model_name,
                            device,
                            rfdetr_checkpoint_path(config),
                            config.get("rfdetrImageSize", RFDETR_NATIVE_IMAGE_SIZE),
                            expected_node_type=inference_node.get("type"),
                        )
                    elif engine == "rfdetr_tensorrt":
                        load_rfdetr_tensorrt(config)
                    elif engine == "rfdetr_onnx":
                        load_rfdetr_onnx(config)
                    elif engine == "efficientad":
                        load_efficientad_model(config, device)
                    else:
                        load_convnext_model(config, device)
                    load_seconds = time.monotonic() - load_started_at
                    loaded_models.append(model_name)
                    device_labels.append(resolve_inference_device(config)[1])
                    self._add_terminal(f"Loaded {task_label} model {model_name} in {load_seconds:.1f}s")
                device_labels = [resolve_inference_device(node.get("config", {}))[1] for node in inference_nodes]
                device_status = device_labels[0] if len(set(device_labels)) == 1 else "Mixed devices"
                self._set_status(state="running", model=", ".join(loaded_models), device=device_status)
            else:
                self._set_status(state="running")
                self._add_terminal("No inference node is active; streaming input frames only")

            self._add_event("Workflow running", "Python is loading, processing, and displaying frames with OpenCV.")
            self._add_terminal("Workflow running")

            while not self._stop_event.is_set():
                ok, frame = input_source.read()
                if not ok:
                    if input_source.is_exhausted:
                        self._add_terminal("Finite video input completed")
                        break
                    raise RuntimeError("Input frame could not be read.")
                if not first_frame_logged:
                    first_frame_logged = True
                    self._add_terminal(f"Read first input frame ({frame.shape[1]}x{frame.shape[0]})")
                frame = apply_image_processing(frame, workflow, processing_runtime)
                if not video_output_initialized:
                    video_output_initialized = True
                    if preview_node and has_active_path(workflow, source_node_id(workflow), "preview"):
                        video_output = OpenCVVideoOutput(
                            cv2, preview_node.get("config", {}), frame.shape[1], frame.shape[0], input_source.fps,
                        )
                        opened_output = video_output.open()
                        if opened_output:
                            output_path, output_fps = opened_output
                            self._add_terminal(f"Saving preview video to {output_path} at {output_fps:g} fps")

                frame_detections = detections if input_source.is_static else []
                frame_tracked = tracked if input_source.is_static else []
                frame_filtered = filtered if input_source.is_static else []
                inference_nodes = active_inference_nodes(workflow)
                now = time.monotonic()
                if inference_nodes:
                    detections = []
                    tracking_detections = []
                    for inference_node in frame_inference_nodes:
                        config = inference_node.get("config", {})
                        threshold = float(config.get("threshold", 0.55))
                        tracker_threshold = tracking_input_threshold(
                            workflow,
                            inference_node,
                        )
                        runtime_inference_node = inference_node_with_threshold(
                            inference_node,
                            tracker_threshold,
                        )
                        engine = config.get("engine", "rfdetr")
                        if engine == "sam3":
                            inference_started_at = time.monotonic()
                            node_detections = run_sam3_frame(
                                frame,
                                runtime_inference_node,
                            )
                        elif engine == "rfdetr":
                            inference_started_at = time.monotonic()
                            node_detections = run_rfdetr_frame(
                                frame,
                                runtime_inference_node,
                            )
                        elif engine == "rfdetr_tensorrt":
                            inference_started_at = time.monotonic()
                            node_detections = run_rfdetr_tensorrt_frame(
                                frame,
                                runtime_inference_node,
                            )
                        elif engine == "rfdetr_onnx":
                            inference_started_at = time.monotonic()
                            node_detections = run_rfdetr_onnx_frame(frame, runtime_inference_node)
                        elif engine == "efficientad":
                            inference_started_at = time.monotonic()
                            node_detections = run_efficientad_frame(frame, runtime_inference_node)
                        elif engine == "convnext":
                            inference_started_at = time.monotonic()
                            node_detections = run_convnext_frame(
                                frame,
                                runtime_inference_node,
                            )
                        else:
                            raise RuntimeError(f"Backend runtime does not support inference engine '{engine}'.")
                        inference_seconds = time.monotonic() - inference_started_at
                        if not first_inference_logged:
                            first_inference_logged = True
                            self._add_terminal(f"First inference completed in {inference_seconds:.2f}s")
                        elif inference_seconds >= 2.0 and now - last_slow_inference_at >= 5:
                            last_slow_inference_at = now
                            self._add_terminal(f"Slow inference: {inference_seconds:.2f}s")
                        detections.extend(
                            item for item in node_detections
                            if item.get("kind") == "anomaly" or float(item.get("score", 0)) >= threshold
                        )
                        if inference_node.get("type") in ("detector", "segmenter"):
                            tracking_detections.extend(
                                item for item in node_detections
                                if float(item.get("score", 0)) >= tracker_threshold
                            )
                    for crop_node, classifier_node in detection_crop_bindings:
                        crop_config = classifier_node.get("config", {})
                        every = max(1, int(crop_config.get("detectEveryNFrames", 1) or 1))
                        max_fps = max(0.0, float(crop_config.get("maxDetectionFps", 0) or 0))
                        schedule_id = (str(crop_node.get("id")), str(classifier_node.get("id")))
                        last = crop_last_inference.get(schedule_id)
                        if total_frame_index % every or (max_fps and last is not None and now - last < 1.0 / max_fps):
                            continue
                        crop_results = run_detection_crop_classifier(
                            frame,
                            detections,
                            workflow,
                            crop_node,
                            classifier_node,
                        )
                        if crop_results:
                            crop_last_inference[schedule_id] = now
                        detections.extend(crop_results)
                    device_labels = [resolve_inference_device(node.get("config", {}))[1] for node in inference_nodes]
                    device_status = device_labels[0] if len(set(device_labels)) == 1 else "Mixed devices"
                    self._set_status(device=device_status)
                    tracker_node = active_tracking_node(workflow)
                    if tracker_node:
                        tracker_config = tracker_node.get("config", {})
                        signature = json.dumps(tracker_config, sort_keys=True)
                        if tracker_runtime is None or tracker_signature != signature:
                            tracker_runtime = ObjectTracker(tracker_node)
                            tracker_signature = signature
                            self._add_terminal(
                                f"Object tracking enabled with {tracker_runtime.status_label()}"
                            )
                        track_candidates = apply_logic_nodes(
                            workflow,
                            "tracker",
                            results_for_node(
                                workflow,
                                "tracker",
                                tracking_detections,
                            ),
                            logic_runtime,
                            now,
                        )
                        tracked = tracker_runtime.update(
                            track_candidates,
                            frame,
                            frame_id=total_frame_index + 1,
                            timestamp=now,
                        )
                    else:
                        tracked = []
                        tracker_runtime = None
                        tracker_signature = None
                    vlm_tracker_node = active_vlm_box_tracker_node(workflow)
                    if vlm_tracker_node:
                        try:
                            from vlm_box_tracker import VLMBoxTrackerRuntime
                        except ImportError:
                            from .vlm_box_tracker import VLMBoxTrackerRuntime
                        vlm_config = vlm_tracker_node.get("config", {})
                        vlm_sig = json.dumps(vlm_config, sort_keys=True)
                        if vlm_tracker_runtime is None or vlm_tracker_signature != vlm_sig:
                            if vlm_tracker_runtime is not None:
                                vlm_tracker_runtime.close()
                            vlm_tracker_runtime = VLMBoxTrackerRuntime(
                                str(vlm_tracker_node.get("id") or "vlm_box_tracker"),
                                vlm_config,
                            )
                            vlm_tracker_signature = vlm_sig
                            self._add_terminal(f"VLM Box Tracker enabled (provider={vlm_config.get('provider', 'openrouter')})")
                        vlm_results = vlm_tracker_runtime.update(
                            frame,
                            timestamp=now,
                        )
                        tracked.extend(vlm_results)
                        detections.extend(vlm_results)
                    elif vlm_tracker_runtime is not None:
                        vlm_tracker_runtime.close()
                        vlm_tracker_runtime = None
                        vlm_tracker_signature = None
                    filter_candidates = (
                        results_for_node(workflow, "filter", detections, tracked)
                        if active_filter_node(workflow)
                        else detections
                    )
                    if active_filter_node(workflow):
                        filter_candidates = apply_logic_nodes(
                            workflow, "filter", filter_candidates, logic_runtime, now
                        )
                    filtered = filter_detections(workflow, filter_candidates)
                    frame_detections = detections
                    frame_tracked = tracked
                    frame_filtered = filtered

                    now = time.monotonic()
                    if detections and now - last_terminal_detection_at >= 1:
                        last_terminal_detection_at = now
                        labels = ", ".join(
                            f"{item.get('class', 'object')}:{float(item.get('score', 0)):.2f}"
                            for item in detections[:6]
                        )
                        if len(detections) > 6:
                            labels = f"{labels}, +{len(detections) - 6} more"
                        self._add_terminal(f"Detected {len(detections)} object(s): {labels}")
                else:
                    now = time.monotonic()

                preview = enabled_node(workflow, "preview")
                preview_detections = detections_for_node(
                    workflow, "preview", frame_detections, frame_filtered, frame_tracked
                )
                preview_detections = apply_logic_nodes(
                    workflow,
                    "preview",
                    preview_detections,
                    logic_runtime,
                    now,
                    crossing_passthrough=True,
                )
                preview_shown = False
                crop_items = None
                if preview and has_active_path(workflow, source_node_id(workflow), "preview"):
                    crop_batches = detection_crop_batches(frame, workflow, frame_detections)
                    crop_items = detection_crop_items_for_target(
                        workflow, "preview", crop_batches, frame_detections,
                    )
                    preview_frame, preview_detections = apply_preview_image_processing(
                        frame,
                        workflow,
                        "preview",
                        preview_detections,
                        processing_runtime,
                    )
                    if crop_items is not None:
                        display_frame = render_detection_crop_grid(preview_frame, crop_items, preview)
                        drawing_detections = crop_grid_drawing_detections(crop_items)
                    else:
                        drawing_detections = preview_detections
                        display_frame = preview_frame.copy()
                        draw_roi_overlays(display_frame, workflow, "preview", logic_runtime)
                        draw_detections(
                            display_frame,
                            preview_detections,
                            preview_style_before_drawing_nodes(
                                workflow, "preview", preview,
                            ),
                        )
                    display_frame = apply_drawing_nodes(
                        display_frame, workflow, "preview", drawing_detections, logic_runtime,
                    )
                    if video_output is not None:
                        video_output.write(display_frame)
                    # cv2.imshow(window_name, display_frame) -- disabled for webapp to prevent native OS popup window
                    preview_shown = True
                    # key = cv2.waitKey(1) & 0xFF
                else:
                    pass

                alert_detections = detections_for_node(
                    workflow, "alert", frame_detections, frame_filtered, frame_tracked
                )
                alert_detections = apply_logic_nodes(
                    workflow, "alert", alert_detections, logic_runtime, now
                )
                alert_node = enabled_node(workflow, "alert")
                if alert_node and alert_detections and has_active_path(workflow, source_node_id(workflow), "alert"):
                    cooldown = max(0, float(alert_node.get("config", {}).get("cooldownSeconds", 5)))
                    if now - last_alert_at >= cooldown:
                        last_alert_at = now
                        labels = ", ".join(item.get("class", "object") for item in alert_detections)
                        self._add_event(
                            str(alert_node.get("config", {}).get("message") or "Detected target object"),
                            f"{len(alert_detections)} match(es): {labels}",
                        )
                        self._add_terminal(f"Alert emitted for {len(alert_detections)} match(es): {labels}")

                total_frame_index += 1
                frame_count += 1
                elapsed = now - last_fps_at
                if elapsed >= 1:
                    roi_count = roi_crossing_count_for_target(workflow, logic_runtime, "preview")
                    visible_count = (
                        len(crop_items)
                        if crop_items is not None
                        else (roi_count if roi_count is not None else len(preview_detections) or len(alert_detections))
                    )
                    self._set_status(
                        state="running",
                        fps=round(frame_count / elapsed),
                        objectCount=visible_count,
                    )
                    frame_count = 0
                    last_fps_at = now
        except Exception as exc:
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            error = exception_message(exc)
            self._set_status(running=False, state="error", error=error)
            self._add_event("Workflow error", error)
            self._add_terminal(f"ERROR: {error}")
        finally:
            if vlm_tracker_runtime is not None:
                vlm_tracker_runtime.close()
            if video_output is not None:
                video_output.release()
                if video_output.opened and video_output.path is not None:
                    self._add_terminal(f"Saved preview video to {video_output.path}")
            if input_source is not None:
                input_source.release()
            cv2.destroyAllWindows()
            if self._stop_event.is_set():
                self._set_status(running=False, state="stopped", fps=0, objectCount=0)
                self._add_event("Workflow stopped", "Python runtime stopped and released the input source.")
                self._add_terminal("Workflow stopped")

    def _set_status(self, **updates) -> None:
        with self._lock:
            self._status.update(updates)

    def _add_event(self, title: str, detail: str) -> None:
        event = {
            "time": time.strftime("%H:%M:%S"),
            "title": title,
            "detail": detail,
        }
        with self._lock:
            self._status["events"].insert(0, event)
            del self._status["events"][MAX_EVENTS:]

    def _add_terminal(self, line: str) -> None:
        terminal_log(line)


def main() -> None:
    from app import main as desktop_main

    desktop_main()


if __name__ == "__main__":
    main()
