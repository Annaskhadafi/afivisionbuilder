# -*- coding: utf-8 -*-
"""Hardware Acceleration Decoder Presets for AFI Vision Builder.

Detects available host hardware decoders (NVIDIA CUDA/NVDEC, Intel QuickSync,
VAAPI, Windows Media Foundation / DirectShow, and CPU fallback) and configures
optimal RTSP decode pipelines. Adapted from Open-NVR / Frigate presets.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from typing import Any

logger = logging.getLogger("afivision.hwaccel")


class HwAccelPresets:
    """Hardware acceleration registry and environment configurator."""

    BACKENDS = {
        "cpu": {
            "name": "CPU Software Decode",
            "description": "Standard software decoding using CPU cores (Universally compatible)",
            "ffmpeg_args": ["-c:v", "h264"],
            "opencv_opt": "rtsp_transport;tcp|timeout;5000000",
        },
        "cuda": {
            "name": "NVIDIA CUDA / NVDEC",
            "description": "Hardware-accelerated decode on NVIDIA GPUs via NVDEC",
            "ffmpeg_args": ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"],
            "opencv_opt": "rtsp_transport;tcp|hwaccel;cuda|timeout;5000000",
        },
        "qsv": {
            "name": "Intel Quick Sync Video (QSV)",
            "description": "Intel processor integrated GPU hardware decoding",
            "ffmpeg_args": ["-hwaccel", "qsv", "-hwaccel_output_format", "qsv"],
            "opencv_opt": "rtsp_transport;tcp|hwaccel;qsv|timeout;5000000",
        },
        "vaapi": {
            "name": "VA-API (Intel / AMD Linux)",
            "description": "Video Acceleration API for Intel and AMD GPUs",
            "ffmpeg_args": ["-hwaccel", "vaapi", "-hwaccel_output_format", "vaapi"],
            "opencv_opt": "rtsp_transport;tcp|hwaccel;vaapi|timeout;5000000",
        },
        "dshow": {
            "name": "Windows DirectShow / MSMF",
            "description": "Native Windows media capture and decoding subsystem",
            "ffmpeg_args": [],
            "opencv_opt": "rtsp_transport;tcp|timeout;5000000",
        },
    }

    @classmethod
    def get_available_backends(cls) -> list[dict[str, Any]]:
        """Probe and return available acceleration backends on this system."""
        available = [
            {"id": "cpu", **cls.BACKENDS["cpu"], "available": True, "is_default": True}
        ]

        # Check for NVIDIA CUDA / NVDEC availability
        has_nvidia = False
        try:
            res = subprocess.run(
                ["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.5
            )
            has_nvidia = res.returncode == 0
        except Exception:
            has_nvidia = False

        available.append({
            "id": "cuda",
            **cls.BACKENDS["cuda"],
            "available": has_nvidia,
            "is_default": False,
        })

        # Windows DirectShow
        is_windows = os.name == "nt"
        available.append({
            "id": "dshow",
            **cls.BACKENDS["dshow"],
            "available": is_windows,
            "is_default": False,
        })

        # Intel QSV
        has_ffmpeg = shutil.which("ffmpeg") is not None
        available.append({
            "id": "qsv",
            **cls.BACKENDS["qsv"],
            "available": has_ffmpeg and is_windows,
            "is_default": False,
        })

        return available

    @classmethod
    def apply_opencv_options(cls, backend: str = "cpu") -> str:
        """Set OPENCV_FFMPEG_CAPTURE_OPTIONS for the chosen backend."""
        b_info = cls.BACKENDS.get(backend.lower(), cls.BACKENDS["cpu"])
        opt = b_info.get("opencv_opt", "rtsp_transport;tcp|timeout;5000000")
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = opt
        logger.info(f"Applied OpenCV capture options for backend '{backend}': {opt}")
        return opt
