"""Crowd Density Heatmap Generator Node for AFI Vision Builder.

Membangkitkan peta panas akumulasi spasial 2D (Gaussian density splatting)
untuk menganalisis pola mobilitas pejalan kaki, dwell hotspot ritel, atau jalur lalu lintas gudang.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("afi.crowd_heatmap")

COLORMAP_PRESETS = {
    "jet": cv2.COLORMAP_JET,
    "inferno": cv2.COLORMAP_INFERNO,
    "viridis": cv2.COLORMAP_VIRIDIS,
    "turbo": getattr(cv2, "COLORMAP_TURBO", cv2.COLORMAP_JET),
    "hot": cv2.COLORMAP_HOT,
    "plasma": getattr(cv2, "COLORMAP_PLASMA", cv2.COLORMAP_JET),
}


class CrowdDensityHeatmap:
    """Akumulator densitas kerumunan dan lintasan spasial berbasis Gaussian kernel."""

    def __init__(self, node_id: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.config = config or {}
        self.accumulator: Optional[np.ndarray] = None
        self.grid_shape: Optional[Tuple[int, int]] = None  # (height, width)
        self.scale = float(self.config.get("resolutionScale", 0.5))  # downscale grid for high FPS
        self.decay_factor = float(self.config.get("decayFactor", 0.985))  # per frame decay
        self.kernel_radius = int(self.config.get("kernelRadiusPx", 24))
        self.opacity = float(self.config.get("opacity", 0.45))
        self.colormap_name = self.config.get("colormap", "jet").lower()
        self.colormap_id = COLORMAP_PRESETS.get(self.colormap_name, cv2.COLORMAP_JET)
        self.min_density_threshold = float(self.config.get("minDensityThreshold", 0.08))
        self.target_class = self.config.get("targetClass", "person").lower()

    def update_config(self, config: Dict[str, Any]) -> None:
        self.config.update(config)
        self.decay_factor = float(self.config.get("decayFactor", 0.985))
        self.kernel_radius = int(self.config.get("kernelRadiusPx", 24))
        self.opacity = float(self.config.get("opacity", 0.45))
        self.colormap_name = self.config.get("colormap", "jet").lower()
        self.colormap_id = COLORMAP_PRESETS.get(self.colormap_name, cv2.COLORMAP_JET)
        self.min_density_threshold = float(self.config.get("minDensityThreshold", 0.08))
        self.target_class = self.config.get("targetClass", "person").lower()

    def reset(self) -> None:
        self.accumulator = None

    def process(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        if frame is None or not hasattr(frame, "shape"):
            return frame

        h_full, w_full = frame.shape[:2]
        gw = max(64, int(w_full * self.scale))
        gh = max(64, int(h_full * self.scale))

        # Inisialisasi atau sesuaikan grid akumulator
        if self.accumulator is None or self.accumulator.shape != (gh, gw):
            self.accumulator = np.zeros((gh, gw), dtype=np.float32)
            self.grid_shape = (gh, gw)

        # 1. Terapkan peluruhan temporal (decay) pada histori
        self.accumulator *= self.decay_factor

        # 2. Tambahkan densitas untuk setiap deteksi target
        rad = max(4, int(self.kernel_radius * self.scale))
        y_grid, x_grid = np.ogrid[-rad:rad + 1, -rad:rad + 1]
        sigma = rad / 2.0
        gaussian_kernel = np.exp(-(x_grid**2 + y_grid**2) / (2 * (sigma**2)))

        for det in detections:
            cls_name = str(det.get("class", "")).lower()
            if self.target_class != "any" and cls_name != self.target_class:
                continue

            bbox = det.get("bbox") or []
            if len(bbox) >= 4:
                # Titik bawah-tengah (kaki/landasan objek) atau centroid
                cx = (bbox[0] + bbox[2] / 2.0) * self.scale
                cy = (bbox[1] + bbox[3] * 0.85) * self.scale  # foot region preferred for trajectory
            else:
                continue

            cx_i = int(round(cx))
            cy_i = int(round(cy))

            if 0 <= cx_i < gw and 0 <= cy_i < gh:
                # Slicing batas kernel
                x1 = max(0, cx_i - rad)
                y1 = max(0, cy_i - rad)
                x2 = min(gw, cx_i + rad + 1)
                y2 = min(gh, cy_i + rad + 1)

                kx1 = x1 - (cx_i - rad)
                ky1 = y1 - (cy_i - rad)
                kx2 = kx1 + (x2 - x1)
                ky2 = ky1 + (y2 - y1)

                self.accumulator[y1:y2, x1:x2] += gaussian_kernel[ky1:ky2, kx1:kx2]

        # 3. Normalisasi akumulator ke 0..255 untuk colormap
        max_val = np.max(self.accumulator)
        if max_val > 0.001:
            norm_density = (self.accumulator / max_val)
        else:
            norm_density = np.zeros_like(self.accumulator)

        # Terapkan threshold filter agar area sepi tidak diwarnai
        mask = norm_density > self.min_density_threshold
        density_uint8 = np.clip(norm_density * 255.0, 0, 255).astype(np.uint8)

        # 4. Beri warna via OpenCV ColorMap
        colored_heat = cv2.applyColorMap(density_uint8, self.colormap_id)

        # Upscale ke resolusi frame asli
        colored_heat_full = cv2.resize(colored_heat, (w_full, h_full), interpolation=cv2.INTER_LINEAR)
        mask_full = cv2.resize(mask.astype(np.uint8), (w_full, h_full), interpolation=cv2.INTER_NEAREST).astype(bool)

        # 5. Blend ke frame
        out_frame = frame.copy()
        alpha = self.opacity
        if np.any(mask_full):
            out_frame[mask_full] = cv2.addWeighted(
                frame[mask_full], 1.0 - alpha, colored_heat_full[mask_full], alpha, 0
            )

        return out_frame


def process_crowd_density_heatmap(
    node: Dict[str, Any],
    frame: np.ndarray,
    candidates: List[Dict[str, Any]],
    state: Dict[str, Any],
    now: float
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Runner eksekusi node Crowd Density Heatmap."""
    node_id = str(node.get("id") or "crowd_density_heatmap")
    config = node.get("config", {})

    generator = state.get("generator")
    if generator is None:
        generator = CrowdDensityHeatmap(node_id, config)
        state["generator"] = generator
    else:
        generator.update_config(config)

    overlayed_frame = generator.process(frame, candidates)
    max_dens = float(np.max(generator.accumulator)) if generator.accumulator is not None else 0.0

    meta = {
        "node_id": node_id,
        "max_density": round(max_dens, 3),
        "target_class": generator.target_class,
        "colormap": generator.colormap_name,
        "opacity": generator.opacity,
    }
    return overlayed_frame, meta
