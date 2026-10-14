"""Install VisoNode's AI dependencies into its dedicated virtual environment."""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCK_FILE = ROOT / "requirements-ai.lock.txt"
GPU_LOCK_FILE = ROOT / "requirements-ai-gpu.lock.txt"
LEGACY_LOCK_FILE = ROOT / "requirements-ai-legacy.lock.txt"
LEGACY_GPU_LOCK_FILE = ROOT / "requirements-ai-gpu-legacy.lock.txt"
PIP_VERSION = "26.1.1"
TORCH_VERSION = "2.12.1"
TORCHVISION_VERSION = "0.27.1"
DEFAULT_CUDA_WHEEL = "cu132"
NUMPY_VERSION = "1.26.4"
TRACKERS_VERSION = "2.5.0.post0"

# The entry scripts use Python's safe-path mode: load this stdlib-only helper
# directly without exposing the compiled desktop directory's extension DLLs.
_profile_spec = importlib.util.spec_from_file_location(
    "visonode_install_profile", ROOT / "ai_runtime_profile.py",
)
runtime_profile = importlib.util.module_from_spec(_profile_spec)
sys.modules[_profile_spec.name] = runtime_profile
_profile_spec.loader.exec_module(runtime_profile)

# Exercise the same RF-DETR exporter used by Optimize for CPU, including its
# optional imports, then load and execute its output with the CPU provider.
# A tiny model keeps this offline and cheap: no pretrained weights are needed.
ONNX_EXPORT_VALIDATION = """
import tempfile
import numpy as np
import onnx
import onnxruntime as ort
import torch
from rfdetr.export.main import export_onnx

with tempfile.TemporaryDirectory(prefix="visonode-export-check-") as export_dir:
    sample = torch.tensor([[-1.0, 0.0, 2.0]], dtype=torch.float32)
    exported = export_onnx(
        output_dir=export_dir,
        model=torch.nn.ReLU().eval(),
        input_names=["input"],
        input_tensors=sample,
        output_names=["output"],
        dynamic_axes=None,
        verbose=False,
    )
    onnx.checker.check_model(onnx.load(exported))
    session = ort.InferenceSession(exported, providers=["CPUExecutionProvider"])
    actual = session.run(["output"], {"input": sample.numpy()})[0]
    np.testing.assert_allclose(actual, np.array([[0.0, 0.0, 2.0]], dtype=np.float32))
print("RF-DETR ONNX export and CPU execution ok", flush=True)
"""

# SAM 3 officially requires NumPy <2. Roboflow Trackers declares NumPy >=2.0.2,
# although the tracker APIs used by VisoNode are compatible with NumPy 1.26.4
# and are covered by the object-tracker regression suite. Keep this exception
# exact so an upstream version or requirement change must be reviewed.
TRACKERS_NUMPY_METADATA_CONFLICT = (
    f"trackers {TRACKERS_VERSION} has requirement numpy>=2.0.2, "
    f"but you have numpy {NUMPY_VERSION}."
)


def run(
    command: list[str],
    *,
    allowed_failure_lines: frozenset[str] = frozenset(),
) -> None:
    print("+ " + subprocess.list2cmdline(command), flush=True)
    # The compiled VisoNode directory contains Python 3.13 DLLs and extension
    # modules. Running the external Python 3.12 runtime from that directory can
    # make Windows load an incompatible python313.dll. The interpreter's own
    # directory is an isolated, writable working directory.
    cwd = Path(command[0]).absolute().parent
    if not allowed_failure_lines:
        subprocess.run(
            command, check=True, cwd=cwd,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return

    completed = subprocess.run(
        command,
        check=False,
        cwd=cwd,
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    failure_lines = frozenset(
        line.strip() for line in completed.stdout.splitlines() if line.strip()
    )
    if (
        completed.returncode == 1
        and failure_lines
        and failure_lines.issubset(allowed_failure_lines)
    ):
        if completed.stderr:
            print(completed.stderr, end="", flush=True)
        print(
            "Compatibility note: Trackers requests NumPy >=2 in its package "
            f"metadata; VisoNode uses tested NumPy {NUMPY_VERSION} compatibility "
            "for SAM 3.",
            flush=True,
        )
        return
    if completed.stdout:
        print(completed.stdout, end="", flush=True)
    if completed.stderr:
        print(completed.stderr, end="", flush=True)
    if completed.returncode:
        raise subprocess.CalledProcessError(
            completed.returncode,
            command,
            output=completed.stdout,
            stderr=completed.stderr,
        )


def _locked_requirements(lock_file: Path) -> list[str]:
    """Return installable requirement lines from a simple exact lock file."""
    return [
        line.strip()
        for line in lock_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _installation_profile(gpu: bool | None, cuda_wheel: str):
    if cuda_wheel not in ("auto", "cu126", DEFAULT_CUDA_WHEEL):
        raise RuntimeError(f"No locked GPU runtime is available for {cuda_wheel}.")
    if gpu is False or (sys.platform == "darwin" and gpu is not True):
        return runtime_profile.PROFILES["cpu"]
    if cuda_wheel != "auto":
        return runtime_profile.PROFILES["legacy" if cuda_wheel == "cu126" else "current"]
    selection = runtime_profile.select_runtime_profile(runtime_profile.detect_nvidia_gpus())
    print(selection.reason, flush=True)
    if gpu is True and selection.profile == "cpu":
        print("A GPU runtime was requested but is unavailable; falling back to the CPU runtime.", flush=True)
    return runtime_profile.PROFILES[selection.profile]


def _remove_obsolete_gpu_packages(python: Path, selected_lock: Path | None) -> None:
    """Remove only our optional GPU packages when changing runtime families."""
    def names(path):
        return {line.split("==", 1)[0].strip().lower().replace("_", "-")
                for line in _locked_requirements(path)} if path.is_file() else set()

    managed = names(GPU_LOCK_FILE) | names(LEGACY_GPU_LOCK_FILE)
    selected = names(selected_lock) if selected_lock is not None else set()
    obsolete = sorted(managed - selected)
    if not obsolete:
        return
    code = (
        "import importlib.metadata, subprocess, sys\n"
        "installed = {dist.metadata['Name'].lower().replace('_', '-') "
        "for dist in importlib.metadata.distributions() if dist.metadata['Name']}\n"
        f"obsolete = [name for name in {obsolete!r} if name in installed]\n"
        "if obsolete:\n"
        "    print('Removing packages from the previous GPU runtime: ' + ', '.join(obsolete), flush=True)\n"
        "    subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', *obsolete], check=True)\n"
    )
    run([str(python), "-c", code])


def _cuda_validation(profile, *, required: bool) -> str:
    return f"""
import torchvision
if {profile.name == 'legacy'!r} and torch.cuda.is_available():
    # CUDA 12.6 wheels must retain the architectures this profile promises.
    assert {{'sm_50', 'sm_60', 'sm_70'}}.issubset(torch.cuda.get_arch_list()), torch.cuda.get_arch_list()
validated_devices = 0
if torch.cuda.is_available():
    for index in range(torch.cuda.device_count()):
        capability = torch.cuda.get_device_capability(index)
        eligible = ((5, 0) <= capability < (10, 0)) if {profile.name == 'legacy'!r} else capability >= (7, 5)
        if not eligible:
            print('GPU', index, torch.cuda.get_device_name(index), 'is outside this runtime profile; skipping validation', flush=True)
            continue
        with torch.cuda.device(index), torch.inference_mode():
            device = 'cuda:' + str(index)
            sample = torch.ones((1, 3, 16, 16), device=device)
            weights = torch.ones((2, 3, 3, 3), device=device)
            output = torch.nn.functional.conv2d(sample, weights)
            assert torch.isfinite(output).all().item()
            boxes = torch.tensor([[0., 0., 4., 4.], [0., 0., 4., 4.]], device=device)
            scores = torch.tensor([0.9, 0.8], device=device)
            assert torchvision.ops.nms(boxes, scores, 0.5).numel() == 1
            torch.cuda.synchronize(index)
            validated_devices += 1
            print('CUDA execution validated:', torch.cuda.get_device_name(index), capability, flush=True)
if {required!r} and not validated_devices:
    raise RuntimeError('The selected GPU runtime could not execute on any supported NVIDIA GPU. Check the NVIDIA driver and installation log.')
"""


def install(python: Path, runtime_dir: Path, *, gpu: bool | None = None, cuda_wheel: str = "auto") -> None:
    if gpu and sys.platform == "darwin":
        raise RuntimeError("CUDA is not supported on macOS. Install the standard runtime for Apple Metal (MPS).")
    profile = _installation_profile(gpu, cuda_wheel)
    try:
        _install_profile(python, runtime_dir, profile, require_gpu=cuda_wheel == "auto")
    except Exception as gpu_error:
        # Automatic setup must leave the application usable when GPU packages,
        # drivers or execution checks fail. Explicit wheel-channel requests are
        # also used by release CI and remain strict validation of that channel.
        if profile.name == "cpu" or cuda_wheel != "auto":
            raise
        gpu_detail = _installation_error_message(gpu_error)
        print(
            f"GPU runtime installation or validation failed: {gpu_detail}. "
            "Falling back to the CPU runtime and validating CPU inference.",
            flush=True,
        )
        try:
            _install_profile(python, runtime_dir, runtime_profile.PROFILES["cpu"], require_gpu=False)
        except Exception as cpu_error:
            raise RuntimeError(
                f"GPU runtime failed ({gpu_detail}); CPU fallback installation also failed: "
                f"{_installation_error_message(cpu_error)}"
            ) from cpu_error
        print("CPU fallback runtime is ready. GPU acceleration is unavailable for this installation.", flush=True)


def _installation_error_message(error: Exception) -> str:
    if isinstance(error, subprocess.CalledProcessError):
        # Validation commands embed a complete Python program. Its command line
        # is not a useful error summary; detailed child output is already logged.
        detail = error.stderr or error.stdout
        return str(detail).strip() if detail else f"command exited with code {error.returncode}; see installation output"
    return str(error).strip() or type(error).__name__


def _install_profile(python: Path, runtime_dir: Path, profile, *, require_gpu: bool) -> None:
    gpu = profile.name != "cpu"
    legacy = profile.name == "legacy"
    lock_file = LEGACY_LOCK_FILE if legacy else LOCK_FILE
    gpu_lock_file = LEGACY_GPU_LOCK_FILE if legacy else GPU_LOCK_FILE
    if not lock_file.is_file():
        raise RuntimeError(f"AI requirements lock was not found at {lock_file}")
    if gpu and not gpu_lock_file.is_file():
        raise RuntimeError(f"GPU requirements lock was not found at {gpu_lock_file}")

    # Install every locked distribution without dependency resolution. The lock
    # contains the complete dependency graph, so a package cannot silently
    # replace NumPy (or any other shared dependency) with a different version.
    print("Installing pinned AI dependencies from online package indexes...", flush=True)
    print(
        f"Selected {profile.name} runtime: PyTorch {profile.torch_version}, "
        f"torchvision {profile.torchvision_version}, {profile.cuda_wheel}.", flush=True,
    )
    torch_index = f"https://download.pytorch.org/whl/{profile.cuda_wheel}"
    run([
        str(python), "-m", "pip", "install", "--no-cache-dir", "--upgrade",
        f"pip=={PIP_VERSION}",
    ])
    # CUDA 12/13 distributions can own overlapping headers and library paths.
    # Remove the previous family first, so uninstall cannot delete new files.
    _remove_obsolete_gpu_packages(python, gpu_lock_file if gpu else None)
    torch_command = [
        str(python), "-m", "pip", "install", "--no-cache-dir", "--no-deps",
        # Include the local build tag: a same-version CPU/CUDA wheel must not
        # satisfy a request for a different runtime when repairing an install.
        f"torch=={profile.torch_version}" + (f"+{profile.cuda_wheel}" if sys.platform != "darwin" else ""),
        f"torchvision=={profile.torchvision_version}" + (f"+{profile.cuda_wheel}" if sys.platform != "darwin" else ""),
    ]
    # macOS PyPI wheels include both CPU and Metal, without a +cpu suffix.
    if sys.platform != "darwin":
        torch_command.extend(["--index-url", torch_index])
    run(torch_command)
    run([
        str(python), "-m", "pip", "install", "--no-cache-dir", "--no-deps",
        "--requirement", str(lock_file),
    ])
    if gpu:
        # CUDA wheels are several gigabytes in total. Installing exact lock
        # entries one at a time keeps Ubuntu's peak temporary disk use bounded
        # because pip can discard each wheel before downloading the next one.
        for requirement in _locked_requirements(gpu_lock_file):
            run([
                str(python), "-m", "pip", "install", "--no-cache-dir", "--no-deps",
                requirement,
            ])

    # --no-deps makes the install immutable. pip check verifies every package,
    # with one exact compatibility exception documented above.
    run(
        [str(python), "-m", "pip", "check"],
        allowed_failure_lines=frozenset({TRACKERS_NUMPY_METADATA_CONFLICT}),
    )

    validation = (
        "import runpy; "
        f"runpy.run_path({str(ROOT / 'sam3_compat.py')!r})['prepare_sam3_import'](); "
        "import cv2, importlib.metadata, inspect, numpy, pathlib, psutil, rfdetr, sam3, supervision, torch, trackers, uuid; import onnx, onnxruntime; "
        "from trackers import BoTSORTTracker, ByteTrackTracker, OCSORTTracker, CBIoUTracker; "
        f"assert numpy.__version__ == '{NUMPY_VERSION}', numpy.__version__; "
        f"assert importlib.metadata.version('trackers') == '{TRACKERS_VERSION}'; "
        "trackers_distribution = importlib.metadata.distribution('trackers'); "
        "trackers_vendor = ' '.join(str(trackers_distribution.metadata.get(field, '')) "
        "for field in ('Author-email', 'Maintainer-email')).lower(); "
        "assert '@roboflow.com' in trackers_vendor, trackers_vendor; "
        "trackers_root = pathlib.Path(trackers_distribution.locate_file('trackers')).resolve(); "
        "tracker_classes = (ByteTrackTracker, BoTSORTTracker, OCSORTTracker, CBIoUTracker); "
        "assert tuple(cls.__module__ for cls in tracker_classes) == "
        "('trackers.core.bytetrack.tracker', 'trackers.core.botsort.tracker', "
        "'trackers.core.ocsort.tracker', 'trackers.core.cbiou.tracker'); "
        "assert all(pathlib.Path(inspect.getfile(cls)).resolve().is_relative_to(trackers_root) "
        "for cls in tracker_classes); "
        f"assert torch.__version__.split('+', 1)[0] == '{profile.torch_version}', torch.__version__; "
        f"assert importlib.metadata.version('torchvision').split('+', 1)[0] == '{profile.torchvision_version}'; "
        "empty_detections = supervision.Detections.empty(); "
        "[tracker.update(empty_detections) for tracker in "
        "(ByteTrackTracker(), BoTSORTTracker(), OCSORTTracker(), CBIoUTracker())]; "
    )
    if gpu:
        validation += (
            f"assert '+{profile.cuda_wheel}' in torch.__version__, torch.__version__; "
            f"assert '+{profile.cuda_wheel}' in importlib.metadata.version('torchvision'); "
        )
        if not legacy:
            validation += "import tensorrt; print('tensorrt', tensorrt.__version__); "
    elif sys.platform == "darwin":
        validation += "assert torch.version.cuda is None; print('mps available', torch.backends.mps.is_available()); "
    else:
        validation += "assert '+cpu' in torch.__version__, torch.__version__; "
    validation += (
        "print('python runtime ok'); print('torch', torch.__version__); "
        "print('cuda available', torch.cuda.is_available()); "
        "print('device count', torch.cuda.device_count())"
    )
    if gpu:
        validation += "\n" + _cuda_validation(profile, required=require_gpu)
    run([str(python), "-c", validation + "\n" + ONNX_EXPORT_VALIDATION])


def _absolute_without_resolving(path: Path) -> Path:
    """Make a path absolute without dereferencing a Linux venv Python symlink."""
    return Path(os.path.abspath(path.expanduser()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--cuda-wheel", choices=("auto", "cu126", DEFAULT_CUDA_WHEEL), default="auto")
    device_group = parser.add_mutually_exclusive_group()
    device_group.add_argument("--gpu", action="store_true", default=None)
    device_group.add_argument("--cpu", action="store_false", dest="gpu")
    args = parser.parse_args()
    install(
        _absolute_without_resolving(args.python),
        _absolute_without_resolving(args.runtime_dir),
        gpu=args.gpu,
        cuda_wheel=args.cuda_wheel,
    )


if __name__ == "__main__":
    main()
