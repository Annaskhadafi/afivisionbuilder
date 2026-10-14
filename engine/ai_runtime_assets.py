"""Locate or download the Python runtime used by VisoNode AI workers."""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import platform
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


DEFAULT_API_BASE_URL = "https://api.visolabel.ovh"
MODEL_ASSETS_ENDPOINT = "/api/v1/ml-model-assets/"
PYTHON_VERSION = "3.12.10"
REQUIRED_PYTHON = (3, 12)
PRIVATE_PYTHON_DIR = ".python312"
DOWNLOAD_CHUNK_SIZE = 1024 * 1024
DOWNLOAD_MAX_ATTEMPTS = 8
DOWNLOAD_RETRY_MAX_DELAY_SECONDS = 30
SAM3_ASSET_KEY = "sam3"
SAM3_MODEL_FILENAME = "sam3.pt"
WINDOWS_PORTABLE_PYTHON_ASSETS = {
    "amd64": {
        "asset_key": "python312_portable_amd64",
        "install_filename": "python-3.12.10-portable-amd64.tar.gz",
        "file_size": 21169583,
        "file_sha256": "08670ab68f041481b8127b2ea27e01ddf56131e61fcf845f489024fddcd3deec",
        "download_url": (
            "https://github.com/astral-sh/python-build-standalone/releases/download/"
            "20250409/cpython-3.12.10%2B20250409-x86_64-pc-windows-msvc-"
            "install_only_stripped.tar.gz"
        ),
    },
}

LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int], None]


def normalized_arch() -> str:
    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64"}:
        return "amd64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    return machine or "unknown"


def normalized_platform() -> str:
    system = platform.system()
    if system == "Windows":
        return "win"
    if system == "Darwin":
        return "macos"
    if system == "Linux":
        return "linux"
    return system.lower() or "unknown"


def python_asset_key(arch: str | None = None, platform_tag: str | None = None) -> str:
    arch = arch or normalized_arch()
    platform_tag = platform_tag or normalized_platform()
    if arch not in {"amd64", "arm64"} or platform_tag not in {"win", "linux"}:
        raise RuntimeError(
            f"Automatic Python {PYTHON_VERSION} installation is not available for "
            f"{platform_tag}/{arch}."
        )
    return f"python312_{arch}" if platform_tag == "win" else f"python312_linux_{arch}"


def _manifest_url(asset_key: str) -> str:
    configured = os.environ.get("VISONODE_AI_ASSET_API_URL", "").strip()
    if configured:
        base = configured
    else:
        api_base = os.environ.get("VISONODE_LICENSE_BASE_URL", DEFAULT_API_BASE_URL).strip()
        base = urljoin(api_base.rstrip("/") + "/", MODEL_ASSETS_ENDPOINT.lstrip("/"))
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}{urlencode({'asset_key': asset_key})}"


def _ssl_context() -> ssl.SSLContext | None:
    configured = os.environ.get("SSL_CERT_FILE", "").strip()
    if configured and Path(configured).is_file():
        return ssl.create_default_context(cafile=configured)
    try:
        from pip._vendor import certifi  # type: ignore[import-not-found]

        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, AttributeError, OSError):
        return None


def _open(request: Request, timeout: int):
    context = _ssl_context()
    if context is None:
        return urlopen(request, timeout=timeout)
    return urlopen(request, timeout=timeout, context=context)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class _RetryableDownloadError(RuntimeError):
    """A transfer failed in a way that can be retried with a byte range."""


def _response_status(response) -> int | None:
    status = getattr(response, "status", None)
    if status is not None:
        return int(status)
    getcode = getattr(response, "getcode", None)
    if callable(getcode):
        status = getcode()
        if status is not None:
            return int(status)
    return None


def _content_range_start(response) -> tuple[int, int | None] | None:
    headers = getattr(response, "headers", None)
    value = headers.get("Content-Range", "") if headers is not None else ""
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+|\*)", str(value).strip(), re.IGNORECASE)
    if match is None:
        return None
    total = None if match.group(3) == "*" else int(match.group(3))
    return int(match.group(1)), total


def _seed_download_digest(partial: Path, expected_size: int) -> tuple[Any, int]:
    if not partial.is_file():
        return hashlib.sha256(), 0
    downloaded = partial.stat().st_size
    if expected_size and downloaded > expected_size:
        partial.unlink(missing_ok=True)
        return hashlib.sha256(), 0
    digest = hashlib.sha256()
    with partial.open("rb") as stream:
        for chunk in iter(lambda: stream.read(DOWNLOAD_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest, downloaded


def _completed_download_matches(path: Path, expected_size: int, expected_sha256: str) -> bool:
    if not path.is_file():
        return False
    if expected_size and path.stat().st_size != expected_size:
        return False
    return not expected_sha256 or _sha256_file(path).lower() == expected_sha256.lower()


def _download(
    url: str,
    destination: Path,
    expected_size: int,
    expected_sha256: str,
    artifact_label: str = "Asset",
    progress_callback: ProgressCallback | None = None,
) -> None:
    partial = destination.with_suffix(destination.suffix + ".part")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if _completed_download_matches(destination, expected_size, expected_sha256):
        if progress_callback is not None:
            size = destination.stat().st_size
            progress_callback(size, expected_size or size)
        return
    destination.unlink(missing_ok=True)

    digest, downloaded = _seed_download_digest(partial, expected_size)
    if progress_callback is not None:
        progress_callback(downloaded, expected_size)
    if downloaded:
        print(f"    resuming from {downloaded // (1024 * 1024)} MB...", flush=True)

    last_error: Exception | None = None
    for attempt in range(1, DOWNLOAD_MAX_ATTEMPTS + 1):
        if expected_size and downloaded == expected_size:
            if not expected_sha256 or digest.hexdigest().lower() == expected_sha256.lower():
                partial.replace(destination)
                if progress_callback is not None:
                    progress_callback(downloaded, expected_size or downloaded)
                return
            partial.unlink(missing_ok=True)
            digest, downloaded = hashlib.sha256(), 0
            last_error = RuntimeError(f"{artifact_label} SHA-256 verification failed")
            print(f"  [WARN] {last_error}; restarting the download.", flush=True)

        headers = {"User-Agent": "VisoNode-AI-Installer"}
        if downloaded:
            headers["Range"] = f"bytes={downloaded}-"
        request = Request(url, headers=headers)

        try:
            with _open(request, timeout=300) as response:
                status = _response_status(response)
                if downloaded and status == 206:
                    content_range = _content_range_start(response)
                    if content_range is None or content_range[0] != downloaded:
                        raise _RetryableDownloadError(
                            f"server returned an invalid Content-Range while resuming at byte {downloaded}"
                        )
                    if expected_size and content_range[1] not in {None, expected_size}:
                        raise _RetryableDownloadError(
                            f"server reports size {content_range[1]}, expected {expected_size}"
                        )
                elif downloaded:
                    print("  [WARN] Server did not honor the range request; restarting from zero.", flush=True)
                    partial.unlink(missing_ok=True)
                    digest, downloaded = hashlib.sha256(), 0

                mode = "ab" if downloaded else "wb"
                with partial.open(mode) as stream:
                    while not expected_size or downloaded < expected_size:
                        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        stream.write(chunk)
                        digest.update(chunk)
                        downloaded += len(chunk)
                        if progress_callback is not None:
                            progress_callback(downloaded, expected_size)
                        if downloaded and downloaded % (256 * 1024 * 1024) < len(chunk):
                            print(f"    downloaded {downloaded // (1024 * 1024)} MB...", flush=True)

            if expected_size and downloaded != expected_size:
                raise _RetryableDownloadError(
                    f"connection ended at {downloaded} of {expected_size} bytes"
                )
            if expected_sha256 and digest.hexdigest().lower() != expected_sha256.lower():
                partial.unlink(missing_ok=True)
                digest, downloaded = hashlib.sha256(), 0
                raise _RetryableDownloadError("SHA-256 verification failed; restarting from zero")
            partial.replace(destination)
            if progress_callback is not None:
                progress_callback(downloaded, expected_size or downloaded)
            return
        except (OSError, http.client.HTTPException, _RetryableDownloadError) as exc:
            last_error = exc
            if partial.is_file():
                actual_size = partial.stat().st_size
                if actual_size != downloaded:
                    digest, downloaded = _seed_download_digest(partial, expected_size)
            if attempt == DOWNLOAD_MAX_ATTEMPTS:
                break
            delay = min(2 ** (attempt - 1), DOWNLOAD_RETRY_MAX_DELAY_SECONDS)
            print(
                f"  [WARN] {artifact_label} download interrupted: {exc}. "
                f"Retrying in {delay}s (attempt {attempt + 1}/{DOWNLOAD_MAX_ATTEMPTS})...",
                flush=True,
            )
            time.sleep(delay)

    retained = f" Partial data was retained at {partial}." if partial.is_file() else ""
    raise RuntimeError(
        f"{artifact_label} download failed after {DOWNLOAD_MAX_ATTEMPTS} attempts: {last_error}.{retained}"
    ) from last_error


def _cached_download_path(runtime_dir: Path, filename: str) -> Path:
    safe_filename = Path(filename).name
    if not safe_filename:
        raise RuntimeError("AI asset manifest contains an invalid install filename")
    return runtime_dir / ".downloads" / safe_filename


def _load_asset(asset_key: str, label: str) -> dict | None:
    manifest_url = _manifest_url(asset_key)
    print(f"Looking for {label}: {asset_key}", flush=True)
    try:
        request = Request(manifest_url, headers={"User-Agent": "VisoNode-AI-Installer"})
        with _open(request, timeout=300) as response:
            manifest = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - caller decides whether online fallback is possible
        print(f"  [WARN] Could not load AI asset manifest: {exc}", flush=True)
        return None

    asset = next(
        (
            item for item in manifest.get("assets", [])
            if isinstance(item, dict) and item.get("asset_key") == asset_key
        ),
        None,
    )
    if not asset or not str(
        asset.get("download_url") or asset.get("presigned_download_url") or ""
    ).strip():
        print(f"  [WARN] {asset_key} is not published.", flush=True)
        return None
    asset = dict(asset)
    asset["download_url"] = urljoin(
        manifest_url,
        str(asset.get("download_url") or asset.get("presigned_download_url") or "").strip(),
    )
    return asset


def sam3_model_path(runtime_dir: Path) -> Path:
    """Return the stable local path used for VisoNode's managed SAM 3 model."""
    return Path(runtime_dir) / "models" / SAM3_MODEL_FILENAME


def sam3_model_available(runtime_dir: Path) -> bool:
    """Return whether a complete managed SAM 3 checkpoint is present."""
    path = sam3_model_path(runtime_dir)
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def download_sam3_model(
    runtime_dir: Path,
    on_log: LogCallback | None = None,
    on_progress: ProgressCallback | None = None,
) -> Path:
    """Download and verify SAM 3 through the existing ML model asset API."""
    log = on_log or (lambda line: print(line, flush=True))
    asset = _load_asset(SAM3_ASSET_KEY, "SAM 3 model")
    if asset is None:
        raise RuntimeError("The SAM 3 model is not currently published by the VisoLabel API.")

    download_url = str(asset.get("download_url") or "").strip()
    if not download_url:
        raise RuntimeError("The VisoLabel API did not provide a SAM 3 download URL.")

    destination = sam3_model_path(runtime_dir)
    published_name = Path(str(asset.get("install_filename") or SAM3_MODEL_FILENAME)).name
    log(f"Downloading {published_name} from the VisoLabel model service...")
    _download(
        download_url,
        destination,
        int(asset.get("file_size") or 0),
        str(asset.get("file_sha256") or ""),
        "SAM 3 model",
        progress_callback=on_progress,
    )
    log(f"SAM 3 model is ready at {destination}")
    return destination


def remove_sam3_model(runtime_dir: Path) -> bool:
    """Remove VisoNode's managed SAM 3 checkpoint and any partial transfer."""
    destination = sam3_model_path(runtime_dir)
    partial = destination.with_suffix(destination.suffix + ".part")
    removed = False
    for path in (destination, partial):
        if path.exists():
            path.unlink()
            removed = True
    return removed


def _private_python(runtime_dir: Path) -> Path:
    relative = Path("python.exe") if normalized_platform() == "win" else Path("bin/python")
    return runtime_dir / PRIVATE_PYTHON_DIR / relative


def _python_subprocess_env(runtime_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    if normalized_platform() == "linux":
        private_root = runtime_dir / PRIVATE_PYTHON_DIR
        additions = [str(private_root / "lib"), str(private_root / "lib64")]
        existing = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = os.pathsep.join([*additions, existing] if existing else additions)
    return env


def _checked_python(command: list[str], runtime_dir: Path) -> Path | None:
    try:
        result = subprocess.run(
            [*command, "-c", "import sys; print(sys.executable); print(*sys.version_info[:3])"],
            cwd=Path(command[0]).expanduser().absolute().parent,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            env=_python_subprocess_env(runtime_dir),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    try:
        version = tuple(int(part) for part in lines[-1].split())
    except ValueError:
        return None
    if version[:2] != REQUIRED_PYTHON:
        return None
    executable = Path(lines[-2]).expanduser()
    if os.path.normcase(os.path.abspath(executable)) == os.path.normcase(os.path.abspath(sys.executable)):
        return None
    return Path(os.path.abspath(executable))


def find_python312(runtime_dir: Path) -> Path | None:
    """Find a usable external Python 3.12 interpreter, preferring the private runtime."""
    commands: list[list[str]] = []
    private_python = _private_python(runtime_dir)
    if private_python.is_file():
        commands.append([str(private_python)])
    override = os.environ.get("VISONODE_AI_BASE_PYTHON", "").strip()
    if override:
        commands.append([str(Path(override).expanduser())])
    if normalized_platform() == "win":
        launcher = shutil.which("py")
        if launcher:
            commands.append([launcher, "-3.12"])
    for name in ("python3.12", "python3", "python"):
        executable = shutil.which(name)
        if executable and "windowsapps" not in executable.lower():
            commands.append([executable])

    if normalized_platform() == "macos":
        # Finder-launched apps do not inherit the user's Homebrew shell PATH.
        for location in (
            "/opt/homebrew/bin/python3.12",
            "/opt/homebrew/opt/python@3.12/bin/python3.12",
            "/usr/local/bin/python3.12",
            "/usr/local/opt/python@3.12/bin/python3.12",
            "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12",
        ):
            if Path(location).is_file():
                commands.append([location])

    seen: set[tuple[str, ...]] = set()
    for command in commands:
        key = tuple(os.path.normcase(part) for part in command)
        if key in seen:
            continue
        seen.add(key)
        python = _checked_python(command, runtime_dir)
        if python is not None:
            return python
    return None


def _safe_extract_tar(archive_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    try:
        with tarfile.open(archive_path) as archive:
            members = archive.getmembers()
            for member in members:
                member_path = Path(member.name)
                target = (destination / member_path).resolve()
                if member_path.is_absolute() or (target != root and root not in target.parents):
                    raise RuntimeError(f"Unsafe path in Python runtime: {member.name}")
                if member.issym() or member.islnk():
                    link_path = Path(member.linkname)
                    link_target = (target.parent / link_path).resolve()
                    if link_path.is_absolute() or (link_target != root and root not in link_target.parents):
                        raise RuntimeError(f"Unsafe link in Python runtime: {member.name}")
            archive.extractall(destination, members=members)
    except tarfile.TarError as exc:
        raise RuntimeError(f"Could not extract Python runtime: {exc}") from exc


def _install_linux_python(archive_path: Path, target_dir: Path) -> Path:
    with tempfile.TemporaryDirectory(prefix="visonode-python-extract-") as temp_name:
        extracted = Path(temp_name) / "extracted"
        _safe_extract_tar(archive_path, extracted)
        roots = [extracted, *(path for path in extracted.iterdir() if path.is_dir())]
        source_root = next(
            (
                root for root in roots
                if (root / "bin/python").exists() or (root / "bin/python3.12").exists()
            ),
            None,
        )
        if source_root is None:
            raise RuntimeError("Python runtime archive does not contain bin/python or bin/python3.12")
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(source_root, target_dir, symlinks=True)

    python = target_dir / "bin/python"
    versioned_python = target_dir / "bin/python3.12"
    if not python.exists() and versioned_python.exists():
        try:
            python.symlink_to(versioned_python.name)
        except OSError:
            shutil.copy2(versioned_python, python)
    if python.exists():
        python.chmod(python.stat().st_mode | 0o755)
    return python


def _missing_windows_python_files(target_dir: Path) -> list[str]:
    return [
        path.name
        for path in (
            target_dir / "python.exe",
            target_dir / "python312.dll",
            target_dir / "python3.dll",
        )
        if not path.is_file()
    ]


def _wait_for_windows_python_files(
    target_dir: Path,
    timeout_seconds: float = 15.0,
    poll_interval_seconds: float = 0.5,
) -> list[str]:
    """Wait for the Windows installer to finish materializing the runtime."""
    deadline = time.monotonic() + timeout_seconds
    missing = _missing_windows_python_files(target_dir)
    while missing:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return missing
        time.sleep(min(poll_interval_seconds, remaining))
        missing = _missing_windows_python_files(target_dir)
    return []


def _wait_for_checked_python(
    python: Path,
    runtime_dir: Path,
    timeout_seconds: float = 15.0,
    poll_interval_seconds: float = 1.0,
) -> Path | None:
    """Wait briefly for a freshly installed interpreter to become runnable."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        checked = _checked_python([str(python)], runtime_dir)
        if checked is not None:
            return checked
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        time.sleep(min(poll_interval_seconds, remaining))


def _installer_output(result: subprocess.CompletedProcess[str]) -> str:
    detail = (result.stderr or result.stdout or "").strip()
    return f" Details: {detail[-500:]}" if detail else ""


def _install_windows_python(installer_path: Path, target_dir: Path) -> Path:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir = target_dir.parent
    install_log = runtime_dir / "python312-installer.log"
    repair_log = runtime_dir / "python312-installer-repair.log"
    command = [
        str(installer_path),
        "/quiet",
        "InstallAllUsers=0",
        f"TargetDir={target_dir}",
        "AssociateFiles=0",
        "CompileAll=0",
        "Include_launcher=0",
        "Include_pip=1",
        "Include_tcltk=0",
        "Include_test=0",
        "PrependPath=0",
        "Shortcuts=0",
        "SimpleInstall=1",
        "Include_exe=1",
        "Include_lib=1",
        "/log",
        str(install_log),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=600,
        cwd=runtime_dir,
        env=_python_subprocess_env(runtime_dir),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Python {PYTHON_VERSION} installer exited with code {result.returncode}"
            + _installer_output(result)
            + f" Installer log: {install_log}"
        )

    python = target_dir / "python.exe"
    missing = _wait_for_windows_python_files(target_dir)
    checked = None if missing else _wait_for_checked_python(python, runtime_dir)
    if missing or checked is None:
        print("Finalizing private Python setup...", flush=True)
        repair_command = [
            str(installer_path),
            "/quiet",
            "/repair",
            "/log",
            str(repair_log),
        ]
        repair = subprocess.run(
            repair_command,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=runtime_dir,
            env=_python_subprocess_env(runtime_dir),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if repair.returncode != 0:
            raise RuntimeError(
                f"Python {PYTHON_VERSION} installer repair exited with code "
                f"{repair.returncode}"
                + _installer_output(repair)
                + f" Installer log: {install_log}. Repair log: {repair_log}"
            )
        missing = _wait_for_windows_python_files(target_dir)
        checked = None if missing else _wait_for_checked_python(python, runtime_dir)

    if missing:
        raise RuntimeError(
            "Private Python installation is incomplete after repair; missing "
            f"{', '.join(missing)} in {target_dir}. "
            f"Installer log: {install_log}. Repair log: {repair_log}"
        )
    if checked is None:
        raise RuntimeError(
            f"Private Python was installed at {python} but could not be started. "
            f"Installer log: {install_log}. Repair log: {repair_log}"
        )
    return checked


def _install_windows_python_archive(archive_path: Path, target_dir: Path) -> Path:
    """Extract an app-local Python without registering a Windows product."""
    with tempfile.TemporaryDirectory(prefix="visonode-python-extract-") as temp_name:
        extracted = Path(temp_name) / "extracted"
        _safe_extract_tar(archive_path, extracted)
        roots = [extracted, *(path for path in extracted.iterdir() if path.is_dir())]
        source_root = next((root for root in roots if (root / "python.exe").is_file()), None)
        if source_root is None:
            raise RuntimeError("Portable Python archive does not contain python.exe")
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(source_root, target_dir)
    return target_dir / "python.exe"


def _python_runtime_asset() -> dict | None:
    if normalized_platform() == "win":
        portable = WINDOWS_PORTABLE_PYTHON_ASSETS.get(normalized_arch())
        if portable is not None:
            print(
                f"Using portable VisoNode Python {PYTHON_VERSION} runtime: "
                f"{portable['asset_key']}",
                flush=True,
            )
            return dict(portable)
    asset_key = python_asset_key()
    return _load_asset(asset_key, f"VisoNode Python {PYTHON_VERSION} runtime")


def ensure_python312(runtime_dir: Path, on_log: LogCallback | None = None) -> Path:
    """Return Python 3.12, downloading the private 3.12.10 runtime if absent."""
    log = on_log or (lambda line: print(line, flush=True))
    installed = find_python312(runtime_dir)
    if installed is not None:
        log(f"Using Python 3.12 at {installed}")
        return installed

    if normalized_platform() == "macos":
        raise RuntimeError(
            "Python 3.12 was not found. Install it with 'brew install python@3.12', "
            "then retry AI runtime installation. A custom installation can be selected "
            "with VISONODE_AI_BASE_PYTHON."
        )

    asset = _python_runtime_asset()
    asset_key = str((asset or {}).get("asset_key") or python_asset_key())
    download_url = str((asset or {}).get("download_url") or "").strip()
    if not asset or not download_url:
        raise RuntimeError(
            f"Python 3.12 was not found and server asset {asset_key} is not published."
        )

    target_dir = runtime_dir / PRIVATE_PYTHON_DIR
    filename = str(asset.get("install_filename") or f"python-{PYTHON_VERSION}")
    artifact_path = _cached_download_path(runtime_dir, filename)
    try:
        log(f"Python 3.12 was not found. Downloading pinned runtime {filename}...")
        _download(
            download_url,
            artifact_path,
            int(asset.get("file_size") or 0),
            str(asset.get("file_sha256") or ""),
            f"Python {PYTHON_VERSION}",
        )
        log(f"Installing private Python {PYTHON_VERSION}...")
        if normalized_platform() == "win":
            if filename.lower().endswith((".tar.gz", ".tgz")):
                python = _install_windows_python_archive(artifact_path, target_dir)
            else:
                python = _install_windows_python(artifact_path, target_dir)
        else:
            python = _install_linux_python(artifact_path, target_dir)
    finally:
        artifact_path.unlink(missing_ok=True)

    checked = _checked_python([str(python)], runtime_dir)
    if checked is None:
        raise RuntimeError(f"Private Python installation did not produce Python 3.12 at {python}")
    log(f"Private Python {PYTHON_VERSION} is ready at {checked}")
    return checked
