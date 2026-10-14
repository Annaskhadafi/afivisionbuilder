"""Choose an AI runtime from NVIDIA hardware without importing PyTorch.

This module is shared by the installer and the already-installed application's
readiness check. Detection must work before any AI packages are installed.
"""
from __future__ import annotations

import argparse
import csv
import ctypes
import io
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class NvidiaGPU:
    index: int
    name: str
    compute_capability: tuple[int, int] | None


@dataclass(frozen=True)
class GPUDetection:
    gpus: tuple[NvidiaGPU, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class RuntimeSelection:
    profile: str
    reason: str
    gpus: tuple[NvidiaGPU, ...] = ()


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    torch_version: str
    torchvision_version: str
    cuda_wheel: str


PROFILES = {
    "cpu": RuntimeProfile("cpu", "2.12.1", "0.27.1", "cpu"),
    "current": RuntimeProfile("current", "2.12.1", "0.27.1", "cu132"),
    "legacy": RuntimeProfile("legacy", "2.14.0", "0.29.0", "cu126"),
}


def _nvidia_smi_path() -> str | None:
    executable = shutil.which("nvidia-smi")
    if executable:
        return executable
    if sys.platform == "win32":
        windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        for candidate in (
            windows / "System32" / "nvidia-smi.exe",
            windows / "Sysnative" / "nvidia-smi.exe",
            program_files / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe",
        ):
            if candidate.is_file():
                return str(candidate)
    return None


def _parse_nvidia_smi(output: str) -> tuple[NvidiaGPU, ...]:
    gpus = []
    for row in csv.reader(io.StringIO(output), skipinitialspace=True):
        if not row or not any(value.strip() for value in row):
            continue
        if len(row) != 3:
            raise ValueError("Unexpected NVIDIA GPU query output")
        index, name, capability = (value.strip() for value in row)
        match = re.fullmatch(r"(\d+)\.(\d+)", capability)
        gpus.append(NvidiaGPU(
            int(index), name,
            (int(match[1]), int(match[2])) if match else None,
        ))
    return tuple(gpus)


def _detect_with_cuda_driver() -> GPUDetection:
    """Older nvidia-smi versions lack compute_cap; ask the driver directly."""
    try:
        driver = (
            ctypes.WinDLL("nvcuda.dll") if sys.platform == "win32"
            else ctypes.CDLL("libcuda.so.1")
        )
        driver.cuInit.argtypes = [ctypes.c_uint]
        driver.cuDeviceGetCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
        driver.cuDeviceGet.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int]
        driver.cuDeviceComputeCapability.argtypes = [
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.c_int,
        ]
        driver.cuDeviceGetName.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        for name in ("cuInit", "cuDeviceGetCount", "cuDeviceGet",
                     "cuDeviceComputeCapability", "cuDeviceGetName"):
            getattr(driver, name).restype = ctypes.c_int

        def checked(result: int, operation: str) -> None:
            if result:
                raise RuntimeError(f"NVIDIA driver {operation} failed (CUDA error {result})")

        status = driver.cuInit(0)
        if status == 100:  # CUDA_ERROR_NO_DEVICE
            return GPUDetection()
        checked(status, "initialization")
        count = ctypes.c_int()
        checked(driver.cuDeviceGetCount(ctypes.byref(count)), "device count")
        gpus = []
        for index in range(count.value):
            device, major, minor = ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
            name = ctypes.create_string_buffer(256)
            checked(driver.cuDeviceGet(ctypes.byref(device), index), "device lookup")
            checked(driver.cuDeviceComputeCapability(
                ctypes.byref(major), ctypes.byref(minor), device.value,
            ), "compute capability lookup")
            checked(driver.cuDeviceGetName(name, len(name), device.value), "device name lookup")
            gpus.append(NvidiaGPU(index, name.value.decode("utf-8", errors="replace"),
                                  (major.value, minor.value)))
        return GPUDetection(tuple(gpus))
    except (OSError, AttributeError, RuntimeError) as exc:
        return GPUDetection(error=str(exc))


def detect_nvidia_gpus(*, timeout: float = 10.0) -> GPUDetection:
    """Discover GPU capabilities, falling back when an older query is unsupported.

    Detection failures are explicit; a driver error must never be interpreted as
    proof that an unknown GPU is compatible with the current CUDA runtime.
    """
    executable = _nvidia_smi_path()
    smi_error = None
    smi_gpus: tuple[NvidiaGPU, ...] = ()
    if executable:
        try:
            result = subprocess.run(
                [executable, "--query-gpu=index,name,compute_cap", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=False, timeout=timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode:
                smi_error = (result.stderr or result.stdout).strip() or "nvidia-smi failed"
            else:
                smi_gpus = _parse_nvidia_smi(result.stdout)
                if smi_gpus and all(gpu.compute_capability is not None for gpu in smi_gpus):
                    return GPUDetection(smi_gpus)
                if not smi_gpus:
                    return GPUDetection()
                smi_error = "nvidia-smi did not report every GPU's compute capability"
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            smi_error = str(exc)
    driver_detection = _detect_with_cuda_driver()
    if driver_detection.error is None:
        # Do not discard a GPU reported by nvidia-smi if driver initialization
        # exposes no devices (for example, when CUDA_VISIBLE_DEVICES hides them).
        if not smi_gpus or len(driver_detection.gpus) == len(smi_gpus):
            return driver_detection
    errors = [error for error in (smi_error, driver_detection.error) if error]
    return GPUDetection(smi_gpus, "; ".join(errors) or "NVIDIA GPU capability is unknown")


def select_runtime_profile(detection: GPUDetection) -> RuntimeSelection:
    """Select cpu/current/legacy without making assumptions from model names."""
    gpus = detection.gpus
    if detection.error:
        return RuntimeSelection("cpu", f"NVIDIA hardware detection could not be completed: {detection.error}. Using CPU.", gpus)
    if not gpus:
        return RuntimeSelection("cpu", "No NVIDIA GPU was detected. Using the standard CPU/Metal runtime.")
    if any(gpu.compute_capability is None for gpu in gpus):
        return RuntimeSelection("cpu", "An NVIDIA GPU's compute capability is unknown. Using CPU until its driver can report it.", gpus)
    legacy = [gpu for gpu in gpus if (5, 0) <= gpu.compute_capability < (7, 5)]
    modern = [gpu for gpu in gpus if gpu.compute_capability >= (7, 5)]
    unsupported = [gpu for gpu in gpus if gpu.compute_capability < (5, 0)]
    if legacy:
        reason = "Maxwell, Pascal or Volta GPU detected; selecting the compatible legacy CUDA runtime."
        if any(gpu.compute_capability >= (10, 0) for gpu in modern):
            reason += " Blackwell or newer GPUs on this machine require a separate current CUDA runtime."
        profile = "legacy"
    elif modern:
        profile = "current"
        reason = "Turing or newer NVIDIA GPU detected; selecting the current CUDA runtime."
    else:
        return RuntimeSelection("cpu", "The detected NVIDIA GPUs predate Maxwell and are unsupported by the available CUDA runtimes. Using CPU.", gpus)
    if unsupported:
        reason += " GPUs older than Maxwell remain unsupported; use a supported GPU or CPU."
    return RuntimeSelection(profile, reason, gpus)


def installed_runtime_issue(
    torch_version: str,
    torchvision_version: str,
    cuda_version: str | None,
    *,
    detection: GPUDetection | None = None,
) -> str | None:
    """Explain when an existing runtime needs repair for the detected hardware.

    An intentional CPU installation is valid even on NVIDIA machines. Likewise,
    removing a GPU does not invalidate a pinned CUDA wheel's CPU support.
    """
    torch_base = torch_version.split("+", 1)[0]
    vision_base = torchvision_version.split("+", 1)[0]
    if cuda_version is None:
        expected = PROFILES["cpu"]
    else:
        selection = select_runtime_profile(detection if detection is not None else detect_nvidia_gpus())
        if selection.profile == "cpu":
            # Unknown hardware is not evidence that an existing CUDA package
            # needs replacing. Still enforce one of the supported exact pins.
            for profile in (PROFILES["current"], PROFILES["legacy"]):
                expected_cuda = {"cu132": "13.2", "cu126": "12.6"}[profile.cuda_wheel]
                if (torch_base, vision_base, cuda_version) == (
                    profile.torch_version, profile.torchvision_version, expected_cuda,
                ):
                    return None
            expected = PROFILES["current"]
        else:
            expected = PROFILES[selection.profile]
    expected_cuda = {"cpu": None, "cu132": "13.2", "cu126": "12.6"}[expected.cuda_wheel]
    suffixes_match = all(
        "+" not in version or version.split("+", 1)[1] == expected.cuda_wheel
        for version in (torch_version, torchvision_version)
    )
    if (torch_base, vision_base, cuda_version) == (
        expected.torch_version, expected.torchvision_version, expected_cuda,
    ) and suffixes_match:
        return None
    return (
        f"AI runtime does not match the {expected.name} hardware profile: "
        f"installed torch {torch_version}, torchvision {torchvision_version}, CUDA {cuda_version or 'none'}; "
        f"requires torch {expected.torch_version}, torchvision {expected.torchvision_version}, "
        f"{expected.cuda_wheel}. Reinstall the AI runtime to select compatible GPU libraries."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print hardware and runtime selection as JSON")
    args = parser.parse_args()
    selection = select_runtime_profile(detect_nvidia_gpus())
    if args.json:
        print(json.dumps(asdict(selection)))
    else:
        print(selection.profile)
        print(selection.reason)


if __name__ == "__main__":
    main()
