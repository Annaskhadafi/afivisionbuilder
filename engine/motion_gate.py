# -*- coding: utf-8 -*-
"""Motion Gate Engine for AFI Vision Builder.

Lightweight frame-differencing and background motion analysis (<1% CPU).
Allows AI Computer Vision workflows to skip heavy deep-learning inference
(YOLO, SAM, Pose) when the scene is static, saving 70-85% CPU/GPU resources
in 24/7 CCTV surveillance environments (inspired by Open-NVR Tier-0 Gate).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import cv2
import numpy as np

logger = logging.getLogger("afivision.motion_gate")


class MotionGate:
    """Evaluates frame-to-frame optical movement with spatial masking and cooldown hysteresis."""

    def __init__(
        self,
        motion_threshold: float = 0.015,
        min_area_px: int = 500,
        cooldown_frames: int = 15,
        blur_size: int = 21,
        diff_threshold: int = 25,
        mask_polygons: Optional[list[list[list[int]]]] = None,
    ):
        self.motion_threshold = max(0.001, min(0.5, float(motion_threshold or 0.015)))
        self.min_area_px = max(50, int(min_area_px or 500))
        self.cooldown_frames = max(1, int(cooldown_frames or 15))
        self.blur_size = blur_size if blur_size % 2 == 1 else blur_size + 1
        self.diff_threshold = max(5, min(100, int(diff_threshold or 25)))
        self.mask_polygons = mask_polygons or []

        self._prev_gray: Optional[np.ndarray] = None
        self._cooldown_counter = 0
        self._exclusion_mask: Optional[np.ndarray] = None
        self._mask_shape: Optional[tuple[int, int]] = None
        self._total_frames = 0
        self._motion_frames = 0

    def update_masks(self, polygons: list[list[list[int]]], shape: tuple[int, int]) -> None:
        """Update exclusion mask polygon list."""
        self.mask_polygons = polygons
        h, w = shape[:2]
        self._mask_shape = (h, w)
        if not polygons:
            self._exclusion_mask = None
            return

        # 255 = active area, 0 = excluded area
        mask = np.ones((h, w), dtype=np.uint8) * 255
        for poly in polygons:
            pts = np.array(poly, dtype=np.int32)
            if len(pts) >= 3:
                cv2.fillPoly(mask, [pts], 0)
        self._exclusion_mask = mask

    def process_frame(self, frame: np.ndarray) -> dict[str, Any]:
        """Analyze frame for motion.

        Returns a dictionary with:
        - has_motion: bool (True if motion detected or within cooldown)
        - is_raw_motion: bool (True if motion detected in the current frame)
        - motion_ratio: float (fraction of active pixels changed)
        - motion_boxes: list of [x, y, w, h] bounding boxes of moving clusters
        - skip_inference: bool (True if frame is static and AI inference can be bypassed)
        - cooldown_remaining: int
        """
        if frame is None or not hasattr(frame, "shape"):
            return {
                "has_motion": True,
                "is_raw_motion": True,
                "motion_ratio": 1.0,
                "motion_boxes": [],
                "skip_inference": False,
                "cooldown_remaining": 0,
            }

        self._total_frames += 1
        h, w = frame.shape[:2]

        # Convert to downscaled grayscale for lightning-fast difference calculation
        # Max dimension 480 for sub-millisecond evaluation
        scale = 1.0
        if max(h, w) > 480:
            scale = 480.0 / max(h, w)
            proc_w = int(w * scale)
            proc_h = int(h * scale)
            small = cv2.resize(frame, (proc_w, proc_h), interpolation=cv2.INTER_LINEAR)
        else:
            small = frame
            proc_w, proc_h = w, h

        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)

        # First frame warmup
        if self._prev_gray is None or self._prev_gray.shape != gray.shape:
            self._prev_gray = gray
            self._cooldown_counter = self.cooldown_frames
            return {
                "has_motion": True,
                "is_raw_motion": True,
                "motion_ratio": 1.0,
                "motion_boxes": [],
                "skip_inference": False,
                "cooldown_remaining": self._cooldown_counter,
            }

        # Compute absolute difference
        frame_diff = cv2.absdiff(self._prev_gray, gray)
        _, thresh = cv2.threshold(frame_diff, self.diff_threshold, 255, cv2.THRESH_BINARY)
        self._prev_gray = gray

        # Apply exclusion mask if defined
        if self.mask_polygons:
            if self._exclusion_mask is None or self._mask_shape != (proc_h, proc_w):
                # Scale mask polygons to downscaled processing dimension
                scaled_polys = []
                for poly in self.mask_polygons:
                    scaled_polys.append([[int(pt[0] * scale), int(pt[1] * scale)] for pt in poly])
                mask = np.ones((proc_h, proc_w), dtype=np.uint8) * 255
                for sp in scaled_polys:
                    pts = np.array(sp, dtype=np.int32)
                    if len(pts) >= 3:
                        cv2.fillPoly(mask, [pts], 0)
                self._exclusion_mask = mask
                self._mask_shape = (proc_h, proc_w)

            thresh = cv2.bitwise_and(thresh, thresh, mask=self._exclusion_mask)

        # Dilate to join close motion blobs
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        thresh = cv2.dilate(thresh, kernel, iterations=2)

        total_pixels = proc_w * proc_h
        active_pixels = cv2.countNonZero(thresh)
        motion_ratio = float(active_pixels / max(1, total_pixels))

        # Find motion contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_scaled_area = self.min_area_px * (scale * scale)

        motion_boxes = []
        is_raw_motion = False

        for c in contours:
            if cv2.contourArea(c) >= min_scaled_area:
                bx, by, bw, bh = cv2.boundingRect(c)
                # Rescale boxes back to original coordinate space
                orig_box = [
                    int(round(bx / scale)),
                    int(round(by / scale)),
                    int(round(bw / scale)),
                    int(round(bh / scale)),
                ]
                motion_boxes.append(orig_box)
                is_raw_motion = True

        if motion_ratio >= self.motion_threshold:
            is_raw_motion = True

        # Hysteresis: Keep gate open during cooldown frames so objects pausing briefly aren't cut off
        if is_raw_motion:
            self._cooldown_counter = self.cooldown_frames
            self._motion_frames += 1
            has_motion = True
        elif self._cooldown_counter > 0:
            self._cooldown_counter -= 1
            has_motion = True
        else:
            has_motion = False

        skip_inference = not has_motion

        return {
            "has_motion": has_motion,
            "is_raw_motion": is_raw_motion,
            "motion_ratio": round(motion_ratio, 5),
            "motion_boxes": motion_boxes,
            "skip_inference": skip_inference,
            "cooldown_remaining": self._cooldown_counter,
            "stats": {
                "total_frames": self._total_frames,
                "motion_frames": self._motion_frames,
                "saving_percent": round((1.0 - (self._motion_frames / max(1, self._total_frames))) * 100, 1),
            },
        }

    def draw_debug_overlay(self, frame: np.ndarray, motion_result: dict[str, Any]) -> np.ndarray:
        """Render subtle motion gate telemetry (boxes and state pill) on frame."""
        if frame is None or not hasattr(frame, "shape"):
            return frame

        annotated = frame.copy()
        # Draw motion bounding boxes
        for bx, by, bw, bh in motion_result.get("motion_boxes", []):
            cv2.rectangle(annotated, (bx, by), (bx + bw, by + bh), (0, 220, 255), 1)

        # Draw status badge in top-left
        has_motion = motion_result.get("has_motion", False)
        is_raw = motion_result.get("is_raw_motion", False)
        ratio = motion_result.get("motion_ratio", 0.0)

        status_text = "MOTION ACTIVE" if is_raw else ("COOLDOWN" if has_motion else "STATIC (AI BYPASSED)")
        status_color = (34, 197, 94) if is_raw else ((234, 179, 8) if has_motion else (148, 163, 184))

        cv2.rectangle(annotated, (12, 12), (230, 42), (15, 23, 42), -1)
        cv2.rectangle(annotated, (12, 12), (230, 42), status_color, 1)
        cv2.circle(annotated, (26, 27), 5, status_color, -1)
        cv2.putText(
            annotated,
            f"{status_text} | {ratio*100:.1f}%",
            (38, 31),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        return annotated
