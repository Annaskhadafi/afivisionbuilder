"""Interactive Object Zoom runtime and Picture-in-Picture (PiP) renderer.

Allows interactive click-to-zoom tracking on live objects in video streams.
"""

from __future__ import annotations

import copy
import math
import threading
import time
from typing import Any

import cv2
import numpy as np


def _extract_box(det: dict[str, Any]) -> tuple[int, int, int, int]:
    """Returns (x1, y1, x2, y2) regardless of whether det uses [x,y,w,h], [x1,y1,x2,y2], or dict keys."""
    if "x" in det and "y" in det and "width" in det and "height" in det:
        x = float(det["x"])
        y = float(det["y"])
        w = float(det["width"])
        h = float(det["height"])
        return int(round(x)), int(round(y)), int(round(x + w)), int(round(y + h))

    if "xyxy" in det:
        b = det["xyxy"]
        return int(round(b[0])), int(round(b[1])), int(round(b[2])), int(round(b[3]))

    b = det.get("bbox") or det.get("box")
    if b and len(b) >= 4:
        v0, v1, v2, v3 = [float(v) for v in b[:4]]
        if "box" in det and not det.get("bbox"):
            return int(round(v0)), int(round(v1)), int(round(v2)), int(round(v3))
        # Standard Afi Vision Builder detection bbox is [x, y, w, h]
        return int(round(v0)), int(round(v1)), int(round(v0 + v2)), int(round(v1 + v3))

    return 0, 0, 0, 0


class InteractiveZoomRuntime:
    """Manages target lock state and Picture-in-Picture (PiP) rendering for a node."""

    def __init__(self, node_id: str = "interactive_zoom") -> None:
        self.node_id = str(node_id)
        self._lock = threading.RLock()
        self.selected_track_id: int | str | None = None
        self.selected_class: str = ""
        self.selected_confidence: float = 0.0
        self.selected_bbox: list[int] = []  # [x1, y1, x2, y2]
        self.status: str = "idle"  # "idle", "locked", "lost"
        self.last_seen_time: float = 0.0
        self.last_crop: np.ndarray | None = None
        self.last_crop_jpeg: bytes | None = None
        self.latest_detections: list[dict[str, Any]] = []
        self.frame_width: int = 1280
        self.frame_height: int = 720
        self.override_pip_size_pct: int | None = None
        self.show_class_name: bool = True
        self.show_confidence: bool = True
        self.show_download_button: bool = True
        self.override_aspect_ratio: str | None = None
        self.override_focus_point: str | None = None
        self.override_size_mode: str | None = None  # "dynamic" or "fixed"
        self.override_zoom_scale: float | None = None
        self.override_headroom_pct: int | None = None

    def select_by_point(self, norm_x: float, norm_y: float) -> dict[str, Any] | None:
        """Hit test click coordinate (normalized 0.0 - 1.0) against active detections."""
        with self._lock:
            detections_to_check = self.latest_detections
            if not detections_to_check:
                try:
                    from server import _runner
                    if _runner and hasattr(_runner, "_event_runtime"):
                        detections_to_check = _runner._event_runtime.get("_last_detections", [])
                except Exception:
                    pass

            if not detections_to_check:
                return None

            px = int(norm_x * self.frame_width)
            py = int(norm_y * self.frame_height)

            best_match: dict[str, Any] | None = None
            best_dist = float("inf")
            margin = 20  # 20px hit margin for easy comfortable clicking

            for det in detections_to_check:
                x1, y1, x2, y2 = _extract_box(det)
                if x2 <= x1 or y2 <= y1:
                    continue
                if (x1 - margin) <= px <= (x2 + margin) and (y1 - margin) <= py <= (y2 + margin):
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    dist = math.hypot(px - cx, py - cy)
                    if dist < best_dist:
                        best_dist = dist
                        best_match = det

            if best_match is not None:
                track_id = best_match.get("trackId") or best_match.get("track_id") or best_match.get("id")
                if track_id is None:
                    b = _extract_box(best_match)
                    track_id = f"box_{best_match.get('class', 'obj')}_{b[0]}_{b[1]}"
                self._lock_target_unlocked(best_match, track_id)
                return self._get_state_unlocked()

            return None

    def select_by_track_id(self, track_id: int | str) -> bool:
        """Lock target directly by known track_id."""
        with self._lock:
            detections_to_check = self.latest_detections
            if not detections_to_check:
                try:
                    from server import _runner
                    if _runner and hasattr(_runner, "_event_runtime"):
                        detections_to_check = _runner._event_runtime.get("_last_detections", [])
                except Exception:
                    pass

            for det in detections_to_check:
                tid = det.get("trackId") or det.get("track_id") or det.get("id")
                if str(tid) == str(track_id):
                    self._lock_target_unlocked(det, tid)
                    return True
            self.selected_track_id = track_id
            self.status = "lost"
            self.last_seen_time = time.time()
            return True

    def set_pip_size(self, size_pct: int) -> int:
        with self._lock:
            self.override_size_mode = "fixed"
            self.override_pip_size_pct = max(10, min(50, int(size_pct)))
            return self.override_pip_size_pct

    def set_aspect_ratio(self, aspect: str) -> str:
        with self._lock:
            self.override_aspect_ratio = str(aspect).lower()
            return self.override_aspect_ratio

    def set_focus_point(self, focus: str) -> str:
        with self._lock:
            self.override_focus_point = str(focus).lower()
            return self.override_focus_point

    def set_size_mode(self, mode: str) -> str:
        with self._lock:
            self.override_size_mode = str(mode).lower()
            return self.override_size_mode

    def set_headroom(self, headroom_pct: int) -> int:
        with self._lock:
            self.override_headroom_pct = max(10, min(100, int(headroom_pct)))
            return self.override_headroom_pct

    def set_zoom_scale(self, scale: float) -> float:
        with self._lock:
            self.override_zoom_scale = max(1.0, min(5.0, float(scale)))
            return self.override_zoom_scale

    def reset_target(self) -> None:
        """Clear target lock and return to idle state."""
        with self._lock:
            self.selected_track_id = None
            self.selected_class = ""
            self.selected_confidence = 0.0
            self.selected_bbox = []
            self.status = "idle"
            self.last_seen_time = 0.0
            self.last_crop = None
            self.last_crop_jpeg = None

    def _lock_target_unlocked(self, det: dict[str, Any], track_id: int | str) -> None:
        self.selected_track_id = track_id
        self.selected_class = str(det.get("class", "object"))
        self.selected_confidence = float(det.get("confidence", det.get("score", 1.0)) or 1.0)
        self.selected_bbox = list(_extract_box(det))
        self.status = "locked"
        self.last_seen_time = time.time()

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            return self._get_state_unlocked()

    def _get_state_unlocked(self) -> dict[str, Any]:
        return {
            "nodeId": self.node_id,
            "status": self.status,
            "trackId": self.selected_track_id,
            "className": self.selected_class,
            "confidence": round(self.selected_confidence, 3),
            "bbox": list(self.selected_bbox),
            "lastSeenTime": self.last_seen_time,
            "hasCrop": self.last_crop_jpeg is not None,
            "activeCount": len(self.latest_detections),
            "pipSizeMode": self.override_size_mode or "dynamic",
            "zoomScale": self.override_zoom_scale,
            "headroomPercent": self.override_headroom_pct,
            "pipSizePercent": self.override_pip_size_pct,
            "pipAspectRatio": self.override_aspect_ratio,
            "focusPoint": self.override_focus_point,
            "showClassName": self.show_class_name,
            "showConfidence": self.show_confidence,
            "showDownloadButton": self.show_download_button,
        }

    def get_latest_crop_jpeg(self) -> bytes | None:
        with self._lock:
            return self.last_crop_jpeg

    def apply(self, frame: np.ndarray, detections: list[dict[str, Any]], config: dict[str, Any]) -> np.ndarray:
        """Render Picture-in-Picture crop-zoom and target reticle on the frame."""
        if frame is None or not hasattr(frame, "shape"):
            return frame

        # Prevent double-rendering on the exact same frame object in same tick
        frame_token = (id(frame), self.node_id)
        if getattr(frame, "_interactive_zoom_applied", None) == frame_token:
            return frame
        try:
            setattr(frame, "_interactive_zoom_applied", frame_token)
        except Exception:
            pass

        fh, fw = frame.shape[:2]
        now = time.time()

        with self._lock:
            self.frame_width = fw
            self.frame_height = fh
            if detections is not None:
                self.latest_detections = list(detections)

            target_id = self.selected_track_id
            target_det: dict[str, Any] | None = None

            if target_id is not None:
                for det in (detections if detections is not None else self.latest_detections):
                    tid = det.get("trackId") or det.get("track_id") or det.get("id")
                    if str(tid) == str(target_id):
                        target_det = det
                        break

            # Config options
            pip_pos = str(config.get("pipPosition", "top-right")).lower()
            configured_size = int(config.get("pipSizePercent", 30) or 30)
            pip_size_pct = self.override_pip_size_pct if self.override_pip_size_pct is not None else configured_size
            pip_size_pct = max(10, min(50, pip_size_pct))
            zoom_scale = self.override_zoom_scale if self.override_zoom_scale is not None else float(config.get("zoomScale", 1.0) or 1.0)
            zoom_scale = max(1.0, min(5.0, zoom_scale))

            aspect_choice = (self.override_aspect_ratio or str(config.get("pipAspectRatio", "auto"))).lower()
            focus_point = (self.override_focus_point or str(config.get("focusPoint", "auto"))).lower()

            border_color_hex = str(config.get("borderColor", "#00e5ff"))
            border_color = _hex_to_bgr(border_color_hex, default=(255, 229, 0))  # BGR Cyan default
            border_thick = max(1, min(6, int(config.get("borderThickness", 2) or 2)))
            show_crosshair = bool(config.get("showCrosshair", True))
            show_label = bool(config.get("showLabel", True))
            show_target_box = bool(config.get("showTargetBox", True))
            hold_sec = max(0.5, float(config.get("targetLostHoldSeconds", 5.0) or 5.0))
            show_class_name = bool(config.get("showClassName", True))
            show_confidence = bool(config.get("showConfidence", True))
            show_download_btn = bool(config.get("showDownloadButton", True))
            self.show_class_name = show_class_name
            self.show_confidence = show_confidence
            self.show_download_button = show_download_btn

            if target_det is not None:
                self._lock_target_unlocked(target_det, target_id)
                self.status = "locked"
            elif target_id is not None:
                if (now - self.last_seen_time) > hold_sec:
                    self.reset_target()
                    return frame
                else:
                    self.status = "lost"
            else:
                self.status = "idle"
                return frame

            # Calculate crop area from the target detection or last known crop
            crop_img: np.ndarray | None = None
            bw, bh = 100, 100
            if self.status == "locked" and target_det is not None:
                x1, y1, x2, y2 = _extract_box(target_det)
                bw = max(1, x2 - x1)
                bh = max(1, y2 - y1)

                if bw > 1 and bh > 1:
                    # Draw target highlight reticle on the main frame
                    if show_target_box:
                        _draw_target_reticle(frame, x1, y1, x2, y2, border_color, self.selected_class, self.selected_track_id, self.selected_confidence, show_class_name, show_confidence)

                    # Extract crop with generous headroom padding for head & face
                    is_tall_or_person = (
                        (bh > bw * 1.05) or
                        (self.selected_class.lower() in ("person", "people", "man", "woman", "pedestrian", "human", "orang", "manusia", "wajah", "face", "0")) or
                        (str(target_det.get("originalClass", "")).lower() in ("person", "people", "man", "woman", "pedestrian", "human", "orang", "manusia"))
                    )
                    headroom_config = int(config.get("headroomPercent", 48) or 48)
                    headroom_pct = self.override_headroom_pct if self.override_headroom_pct is not None else headroom_config
                    headroom_pct = max(10, min(100, headroom_pct))
                    headroom_ratio = (headroom_pct / 100.0) if is_tall_or_person else 0.15

                    pad_x = int(bw * 0.15)
                    pad_top = int(bh * headroom_ratio)  # Extra headroom so face, hair, and head are never cut off!
                    pad_bottom = int(bh * 0.15)
                    cx1 = max(0, x1 - pad_x)
                    cy1 = max(0, y1 - pad_top)
                    cx2 = min(fw, x2 + pad_x)
                    cy2 = min(fh, y2 + pad_bottom)

                    if cx2 > cx1 and cy2 > cy1:
                        crop_img = frame[cy1:cy2, cx1:cx2].copy()
                        self.last_crop = crop_img.copy()
                        _, enc = cv2.imencode(".jpg", crop_img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                        self.last_crop_jpeg = enc.tobytes()

            elif self.status == "lost" and self.last_crop is not None:
                crop_img = self.last_crop.copy()
                ch_old, cw_old = crop_img.shape[:2]
                bw, bh = max(1, cw_old), max(1, ch_old)

            if crop_img is None or crop_img.size == 0:
                return frame

            # Determine Aspect Ratio (height / width)
            target_hw_ratio = bh / float(max(1, bw))
            if "auto" in aspect_choice:
                aspect_ratio = max(0.5, min(2.0, target_hw_ratio))
            elif "9:16" in aspect_choice:
                aspect_ratio = 16.0 / 9.0  # Portrait tall (~1.778)
            elif "3:4" in aspect_choice or "portrait" in aspect_choice:
                aspect_ratio = 4.0 / 3.0   # Portrait standard (~1.333)
            elif "1:1" in aspect_choice or "square" in aspect_choice:
                aspect_ratio = 1.0         # Square
            elif "16:9" in aspect_choice:
                aspect_ratio = 9.0 / 16.0  # Widescreen (~0.5625)
            elif "4:3" in aspect_choice or "landscape" in aspect_choice:
                aspect_ratio = 3.0 / 4.0   # Landscape (0.75)
            else:
                if bh > bw * 1.15:
                    aspect_ratio = 4.0 / 3.0
                else:
                    aspect_ratio = 0.75

            size_mode = (self.override_size_mode or str(config.get("pipSizeMode", "dynamic"))).lower()

            # Calculate PiP dimensions capped strictly at max 50% of frame
            max_pip_w = fw // 2
            max_pip_h = fh // 2

            ch, cw = crop_img.shape[:2]

            if "dynamic" in size_mode or "object" in size_mode:
                # Mode Dinamis: Ukuran & rasio PiP mengikuti dimensi crop aktual (termasuk ruang kepala)
                dyn_scale = max(1.5, zoom_scale)
                pip_w = int(cw * dyn_scale)
                pip_h = int(ch * dyn_scale)

                # Ensure minimum clear visibility dimension (e.g. 140px)
                min_dim = 140
                if pip_w < min_dim and pip_h < min_dim:
                    scale_up = float(min_dim) / max(1.0, float(max(pip_w, pip_h)))
                    pip_w = int(pip_w * scale_up)
                    pip_h = int(pip_h * scale_up)

                # Cap strictly at maximum half of preview frame (50%)
                if pip_w > max_pip_w:
                    scale_down = float(max_pip_w) / float(pip_w)
                    pip_w = max_pip_w
                    pip_h = max(64, int(pip_h * scale_down))
                if pip_h > max_pip_h:
                    scale_down = float(max_pip_h) / float(pip_h)
                    pip_h = max_pip_h
                    pip_w = max(64, int(pip_w * scale_down))

                # Maintain the dynamic object ratio for subcrop
                aspect_ratio = pip_h / float(max(1, pip_w))
            else:
                # Mode Fixed: Persentase ukuran tetap (S / M / L / XL)
                if aspect_ratio <= 1.0:
                    # Landscape or square
                    pip_w = int(fw * (pip_size_pct / 100.0))
                    pip_h = int(pip_w * aspect_ratio)
                    if pip_w > max_pip_w:
                        pip_w = max_pip_w
                        pip_h = int(pip_w * aspect_ratio)
                    if pip_h > max_pip_h:
                        pip_h = max_pip_h
                        pip_w = int(pip_h / max(0.01, aspect_ratio))
                else:
                    # Portrait (height > width): scale height gracefully
                    pip_h = int(fh * (pip_size_pct / 100.0) * 1.25)
                    if pip_h > max_pip_h:
                        pip_h = max_pip_h
                    pip_w = int(pip_h / max(0.01, aspect_ratio))
                    if pip_w > max_pip_w:
                        pip_w = max_pip_w
                        pip_h = int(pip_w * aspect_ratio)

            pip_w = max(64, min(max_pip_w, pip_w))
            pip_h = max(64, min(max_pip_h, pip_h))

            # Prevent Face Cut-off: Smart Vertical Focus & Aspect-Preserving Subcrop
            pip_aspect = pip_w / float(max(1, pip_h))
            crop_aspect = cw / float(max(1, ch))

            # Cover-fit crop to match PiP aspect ratio before zoom
            if crop_aspect > pip_aspect:
                # Crop is wider than target PiP -> narrow width
                sub_w = max(1, int(ch * pip_aspect))
                sub_h = ch
                sub_x1 = max(0, (cw - sub_w) // 2)
                sub_y1 = 0
            else:
                # Crop is taller than target PiP -> adjust vertical region
                sub_w = cw
                sub_h = max(1, int(cw / max(0.01, pip_aspect)))
                sub_x1 = 0
                is_tall_or_person = (
                    (bh > bw * 1.05) or
                    (self.selected_class.lower() in ("person", "people", "man", "woman", "pedestrian", "human", "orang", "manusia", "wajah", "face", "0")) or
                    (str(target_det.get("originalClass", "") if target_det else "").lower() in ("person", "people", "man", "woman", "pedestrian", "human", "orang", "manusia"))
                )
                if focus_point == "top" or (focus_point == "auto" and is_tall_or_person):
                    # Keep head & face in view (start from top edge)
                    sub_y1 = 0
                elif focus_point == "bottom":
                    sub_y1 = max(0, ch - sub_h)
                else:
                    sub_y1 = max(0, (ch - sub_h) // 2)

            sub_crop = crop_img[sub_y1:sub_y1 + sub_h, sub_x1:sub_x1 + sub_w]
            if sub_crop.size == 0:
                sub_crop = crop_img

            # Apply Zoom Scale on sub_crop
            sch, scw = sub_crop.shape[:2]
            if zoom_scale > 1.0:
                zw = max(10, int(scw / zoom_scale))
                zh = max(10, int(sch / zoom_scale))
                zx = max(0, (scw - zw) // 2)
                is_tall_or_person = (
                    (bh > bw * 1.05) or
                    (self.selected_class.lower() in ("person", "people", "man", "woman", "pedestrian", "human", "orang", "manusia", "wajah", "face", "0")) or
                    (str(target_det.get("originalClass", "") if target_det else "").lower() in ("person", "people", "man", "woman", "pedestrian", "human", "orang", "manusia"))
                )
                if focus_point == "top" or (focus_point == "auto" and is_tall_or_person):
                    # Prioritize head & face: start strictly at top edge so head is never cut!
                    zy = 0
                    if zy + zh > sch:
                        zy = max(0, sch - zh)
                elif focus_point == "bottom":
                    zy = max(0, sch - zh)
                else:
                    zy = max(0, (sch - zh) // 2)
                zoomed_frame = sub_crop[zy:zy + zh, zx:zx + zw]
            else:
                zoomed_frame = sub_crop

            if zoomed_frame.size > 0:
                rendered_pip = cv2.resize(zoomed_frame, (pip_w, pip_h), interpolation=cv2.INTER_LINEAR)
            else:
                rendered_pip = cv2.resize(crop_img, (pip_w, pip_h), interpolation=cv2.INTER_LINEAR)

            # Determine PiP position coordinates
            margin = 16
            if pip_pos == "top-left":
                px1 = margin
                py1 = margin
            elif pip_pos == "bottom-left":
                px1 = margin
                py1 = fh - pip_h - margin
            elif pip_pos == "bottom-right":
                px1 = fw - pip_w - margin
                py1 = fh - pip_h - margin
            else:  # top-right default
                px1 = fw - pip_w - margin
                py1 = margin

            px2 = px1 + pip_w
            py2 = py1 + pip_h

            if px1 < 0 or py1 < 0 or px2 > fw or py2 > fh:
                return frame

            # If status is lost, darken and tint red/gray
            if self.status == "lost":
                rendered_pip = cv2.addWeighted(rendered_pip, 0.45, np.zeros_like(rendered_pip), 0.55, 0)
                lost_text = "TARGET LOST / SEARCHING..."
                cv2.putText(
                    rendered_pip,
                    lost_text,
                    (10, pip_h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    max(0.4, pip_w / 600.0),
                    (0, 140, 255),
                    2,
                    cv2.LINE_AA,
                )

            # Draw optional center crosshairs in the PiP
            if show_crosshair and self.status == "locked":
                chx = pip_w // 2
                chy = pip_h // 2
                c_len = max(8, pip_w // 14)
                cv2.line(rendered_pip, (chx - c_len, chy), (chx + c_len, chy), (0, 255, 255), 1, cv2.LINE_AA)
                cv2.line(rendered_pip, (chx, chy - c_len), (chx, chy + c_len), (0, 255, 255), 1, cv2.LINE_AA)
                cv2.circle(rendered_pip, (chx, chy), max(3, c_len // 2), (0, 255, 255), 1, cv2.LINE_AA)

            # Place PiP onto output frame
            frame[py1:py2, px1:px2] = rendered_pip

            # Draw PiP Outer Border
            box_color = border_color if self.status == "locked" else (0, 140, 255)
            cv2.rectangle(frame, (px1, py1), (px2, py2), box_color, border_thick)

            # Header Banner inside PiP
            if show_label:
                header_h = max(20, int(pip_h * 0.16))
                cv2.rectangle(frame, (px1, py1), (px2, py1 + header_h), (20, 20, 25), -1)
                status_icon = "● LIVE ZOOM" if self.status == "locked" else "▲ SEARCHING"
                label_parts = [status_icon, f"ID #{self.selected_track_id}"]
                if show_class_name and self.selected_class:
                    label_parts.append(self.selected_class.upper())
                if show_confidence and self.selected_confidence > 0:
                    label_parts.append(f"({int(self.selected_confidence * 100)}%)")
                label_txt = " | ".join(label_parts[:2])
                if len(label_parts) > 2:
                    label_txt += " " + " ".join(label_parts[2:])
                font_scale = max(0.35, pip_w / 750.0)
                text_color = (255, 255, 255) if self.status == "locked" else (0, 180, 255)
                cv2.putText(
                    frame,
                    label_txt,
                    (px1 + 8, py1 + int(header_h * 0.72)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    text_color,
                    1,
                    cv2.LINE_AA,
                )

            return frame


def _draw_target_reticle(frame: np.ndarray, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int], class_name: str, track_id: Any, confidence: float = 1.0, show_class_name: bool = True, show_confidence: bool = True) -> None:
    """Draw corner reticle brackets and target lock badge around the selected object."""
    bw = x2 - x1
    bh = y2 - y1
    c_len = max(8, min(24, min(bw, bh) // 4))

    thick = 2
    cv2.line(frame, (x1, y1), (x1 + c_len, y1), color, thick)
    cv2.line(frame, (x1, y1), (x1, y1 + c_len), color, thick)

    cv2.line(frame, (x2, y1), (x2 - c_len, y1), color, thick)
    cv2.line(frame, (x2, y1), (x2, y1 + c_len), color, thick)

    cv2.line(frame, (x1, y2), (x1 + c_len, y2), color, thick)
    cv2.line(frame, (x1, y2), (x1, y2 - c_len), color, thick)

    cv2.line(frame, (x2, y2), (x2 - c_len, y2), color, thick)
    cv2.line(frame, (x2, y2), (x2 - c_len, y2), color, thick)

    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    cv2.circle(frame, (cx, cy), 3, color, -1)

    tag_parts = [f"TARGET #{track_id}"]
    if show_class_name and class_name:
        tag_parts.append(class_name.upper())
    if show_confidence and confidence > 0:
        tag_parts.append(f"({int(confidence * 100)}%)")
    tag_text = " ".join(tag_parts)
    ts, _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
    tag_y = max(ts[1] + 4, y1 - 6)
    cv2.rectangle(frame, (x1, tag_y - ts[1] - 4), (x1 + ts[0] + 8, tag_y + 2), (18, 18, 22), -1)
    cv2.rectangle(frame, (x1, tag_y - ts[1] - 4), (x1 + ts[0] + 8, tag_y + 2), color, 1)
    cv2.putText(frame, tag_text, (x1 + 4, tag_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1, cv2.LINE_AA)


def _hex_to_bgr(hex_str: str, default: tuple[int, int, int] = (255, 229, 0)) -> tuple[int, int, int]:
    try:
        hex_clean = hex_str.lstrip("#")
        if len(hex_clean) == 6:
            r = int(hex_clean[0:2], 16)
            g = int(hex_clean[2:4], 16)
            b = int(hex_clean[4:6], 16)
            return (b, g, r)
    except Exception:
        pass
    return default


_runtimes: dict[str, InteractiveZoomRuntime] = {}
_registry_lock = threading.Lock()


def get_interactive_zoom_runtime(node_id: str = "interactive_zoom") -> InteractiveZoomRuntime:
    with _registry_lock:
        if node_id not in _runtimes:
            _runtimes[node_id] = InteractiveZoomRuntime(node_id)
        return _runtimes[node_id]


def clear_interactive_zoom_runtimes() -> None:
    with _registry_lock:
        _runtimes.clear()
