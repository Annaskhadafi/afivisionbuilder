"""
Single source of truth for VisoNode release metadata.

Public versions follow Semantic Versioning. The current release is 1.0.2;
beta builds for that release use 1.0.2-beta.<client git commit count>.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

APP_NAME = "VisoNode"
ORGANIZATION_NAME = "VisoLabel"

CLIENT_DIR = Path(__file__).resolve().parent
BUILD_INFO_FILENAME = "app_version_build.json"
BUILD_INFO_FILE = CLIENT_DIR / BUILD_INFO_FILENAME
DEFAULT_RELEASE_VERSION = "1.0.3"
DEFAULT_RELEASE_STAGE = "beta"
DEFAULT_RELEASE_NUMBER = 1

_PEP440_RELEASE_RE = re.compile(r"^\d+\.\d+\.\d+$")
_WINDOWS_FILE_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+\.\d+$")
_RELEASE_STAGE_TO_PEP440 = {
    "alpha": "a",
    "beta": "b",
    "rc": "rc",
}


def _run_git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=CLIENT_DIR,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return ""


def _positive_int(value: Any) -> int | None:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


@lru_cache(maxsize=1)
def _read_build_info_file() -> dict[str, Any]:
    if (CLIENT_DIR / ".git").exists() and not getattr(sys, "frozen", False):
        return {}

    paths = [
        BUILD_INFO_FILE,
        Path(sys.executable).resolve().with_name(BUILD_INFO_FILENAME),
    ]

    for path in dict.fromkeys(paths):
        if not path.exists():
            continue
        try:
            with path.open(encoding="utf-8") as build_file:
                data = json.load(build_file)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return data
    return {}


def _build_info_value(name: str) -> str:
    value = _read_build_info_file().get(name, "")
    return str(value).strip()


def _get_release_version() -> str:
    version = (
        os.getenv("VISONODE_RELEASE_VERSION", "").strip()
        or _build_info_value("release_version")
        or DEFAULT_RELEASE_VERSION
    )
    if not _PEP440_RELEASE_RE.fullmatch(version):
        raise RuntimeError(f"Invalid VisoNode release version: {version!r}")
    return version


def _get_release_stage() -> str:
    stage = (
        os.getenv("VISONODE_RELEASE_STAGE", "").strip()
        or _build_info_value("release_stage")
        or DEFAULT_RELEASE_STAGE
    ).lower()
    if stage not in {"alpha", "beta", "rc", "final"}:
        raise RuntimeError(f"Invalid VisoNode release stage: {stage!r}")
    return stage


def _get_git_commit_count() -> int | None:
    return _positive_int(_run_git("rev-list", "--count", "HEAD"))


def _get_release_number(stage: str) -> int:
    if stage == "final":
        return 0
    return (
        _positive_int(os.getenv("VISONODE_RELEASE_NUMBER", ""))
        or _get_git_commit_count()
        or _positive_int(_build_info_value("release_number"))
        or DEFAULT_RELEASE_NUMBER
    )


def _get_version(release_version: str, stage: str, release_number: int) -> str:
    explicit_version = os.getenv("VISONODE_APP_VERSION", "").strip()
    if explicit_version:
        return explicit_version
    if stage == "final":
        return release_version
    return f"{release_version}-{stage}.{release_number}"


def _get_pep440_version(release_version: str, stage: str, release_number: int) -> str:
    """Return the canonical Python-package representation of the version."""
    if stage == "final":
        return release_version
    return f"{release_version}{_RELEASE_STAGE_TO_PEP440[stage]}{release_number}"


def _get_windows_file_version(release_version: str, release_number: int) -> str:
    explicit_version = (
        os.getenv("VISONODE_WINDOWS_FILE_VERSION", "").strip()
        or _build_info_value("windows_file_version")
    )
    if explicit_version:
        if not _WINDOWS_FILE_VERSION_RE.fullmatch(explicit_version):
            raise RuntimeError(f"Invalid Windows file version: {explicit_version!r}")
        return explicit_version

    major, minor, patch = release_version.split(".")
    # PE version components are unsigned 16-bit values. VERSION remains the
    # canonical app version when the commit count exceeds that limit.
    build_number = min(max(release_number, 0), 65535)
    return f"{major}.{minor}.{patch}.{build_number}"


RELEASE_VERSION = _get_release_version()
RELEASE_STAGE = _get_release_stage()
RELEASE_NUMBER = _get_release_number(RELEASE_STAGE)
VERSION = _get_version(RELEASE_VERSION, RELEASE_STAGE, RELEASE_NUMBER)
PEP440_VERSION = _get_pep440_version(RELEASE_VERSION, RELEASE_STAGE, RELEASE_NUMBER)
WINDOWS_FILE_VERSION = _get_windows_file_version(RELEASE_VERSION, RELEASE_NUMBER)

__version__ = PEP440_VERSION


def get_display_version() -> str:
    """Return the human-readable version shown in the UI."""
    return VERSION


def get_build_info() -> dict[str, str | int]:
    """Return version metadata that can be embedded into packaged builds."""
    return {
        "app_name": APP_NAME,
        "organization_name": ORGANIZATION_NAME,
        "release_version": RELEASE_VERSION,
        "release_stage": RELEASE_STAGE,
        "release_number": RELEASE_NUMBER,
        "version": VERSION,
        "pep440_version": PEP440_VERSION,
        "windows_file_version": WINDOWS_FILE_VERSION,
        "git_commit": _run_git("rev-parse", "HEAD"),
        "git_commit_short": _run_git("rev-parse", "--short", "HEAD"),
        "git_commit_count": _get_git_commit_count() or RELEASE_NUMBER,
    }


def write_build_info_file(path: Path = BUILD_INFO_FILE) -> Path:
    """Write build-time version metadata for frozen apps without a .git folder."""
    path.write_text(
        json.dumps(get_build_info(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
