# -*- coding: utf-8 -*-
"""Exclusion and Privacy Masking Engine for AFI Vision Builder.

Allows operators to define 2D polygon or bounding-box exclusion zones to filter
out false positives (wind-blown tree branches, public roads, timecode watermarks)
or apply privacy blur/blackout masks before AI inference. Inspired by Open-NVR.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import cv2
import numpy as np

logger = logging.getLogger("afivision.masking")


class PrivacyMaskEngine:
    """Manages exclusion zones, privacy blackout, and detection spatial filtering."""

    def __init__(
        self,
        masks: Optional[list[dict[str, Any]]] = None,
        mode: str = "filter_detections",  # 'filter_detections' | 'blackout' | 'blur'
    ):
        self.masks = masks or []
        self.mode = str(mode or "filter_detections").lower()
        self._cached_mask_img: Optional[np.ndarray] = None
        self._cached_shape: Optional[tuple[int, int]] = None

    def update_masks(self, masks: list[dict[str, Any]], mode: Optional[str] = None) -> None:
        self.masks = masks or []
        if mode:
            self.mode = mode.lower()
        self._cached_mask_img = None
        self._cached_shape = None

    def _build_mask_image(self, h: int, w: int) -> np.ndarray:
        """Create a binary mask: 255 = excluded zone, 0 = active vision area."""
        if self._cached_mask_img is not None and self._cached_shape == (h, w):
            return self._cached_mask_img

        mask_img = np.zeros((h, w), dtype=np.uint8)
        for m in self.masks:
            points = m.get("points") or []
            if len(points) >= 3:
                # Polygon
                pts = np.array([[int(p[0] * w if p[0] <= 1.0 else p[0]), int(p[1] * h if p[1] <= 1.0 else p[1])] for p in points], dtype=np.int32)
                cv2.fillPoly(mask_img, [pts], 255)
            elif m.get("bbox"):
                # Bbox [x, y, bw, bh]
                bx, by, bw, bh = m["bbox"]
                x1 = int(bx * w if bx <= 1.0 else bx)
                y1 = int(by * h if by <= 1.0 else by)
                x2 = int((bx + bw) * w if (bx + bw) <= 1.0 else (bx + bw))
                y2 = int((by + bh) * h if (by + bh) <= 1.0 else (by + bh))
                cv2.rectangle(mask_img, (x1, y1), (x2, y2), 255, -1)

        self._cached_mask_img = mask_img
        self._cached_shape = (h, w)
        return mask_img

    def apply_to_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply privacy blackout or blur to frame if mode is blackout/blur."""
        if not self.masks or frame is None or not hasattr(frame, "shape"):
            return frame

        h, w = frame.shape[:2]
        mask_bin = self._build_mask_image(h, w)
        if not np.any(mask_bin):
            return frame

        output = frame.copy()
        if self.mode == "blackout":
            output[mask_bin == 255] = 0
        elif self.mode == "blur":
            blurred = cv2.GaussianBlur(frame, (31, 31), 0)
            output[mask_bin == 255] = blurred[mask_bin == 255]

        return output

    def filter_detections(self, detections: list[dict[str, Any]], frame_shape: tuple[int, int]) -> list[dict[str, Any]]:
        """Filter out detections whose center or bottom feet falls inside an exclusion mask."""
        if not self.masks or not detections:
            return detections

        h, w = frame_shape[:2]
        mask_bin = self._build_mask_image(h, w)
        if not np.any(mask_bin):
            return detections

        survived = []
        for d in detections:
            bbox = d.get("bbox")
            if bbox and len(bbox) >= 4:
                cx = int(bbox[0] + bbox[2] / 2.0)
                cy = int(bbox[1] + bbox[3] / 2.0)
                feet_y = int(bbox[1] + bbox[3])
            else:
                cx = int(d.get("x", 0))
                cy = int(d.get("y", 0))
                feet_y = cy

            # Check bounds
            cx = max(0, min(w - 1, cx))
            cy = max(0, min(h - 1, cy))
            feet_y = max(0, min(h - 1, feet_y))

            # Exclude if center or bottom touches masked exclusion area
            if mask_bin[cy, cx] == 255 or mask_bin[feet_y, cx] == 255:
                continue
            survived.append(d)

        return survived

    def draw_mask_overlay(self, frame: np.ndarray, alpha: float = 0.35) -> np.ndarray:
        """Render transparent red/striped shading over exclusion zones on preview frame."""
        if not self.masks or frame is None or not hasattr(frame, "shape"):
            return frame

        h, w = frame.shape[:2]
        mask_bin = self._build_mask_image(h, w)
        if not np.any(mask_bin):
            return frame

        overlay = frame.copy()
        # Red shading for exclusion zone
        overlay[mask_bin == 255] = (40, 40, 220)
        result = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)

        # Draw contour borders
        contours, _ = cv2.findContours(mask_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(result, contours, -1, (0, 0, 255), 2)
        return result
