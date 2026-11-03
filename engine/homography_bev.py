"""
Homography Ground Projection & Bird's Eye View (BEV) Module for VisoNode.

Features:
- 4-point ground plane perspective calibration (cv2.getPerspectiveTransform).
- Bottom-center ground contact projection (cv2.perspectiveTransform).
- Out-of-ground polygon filtering (cv2.pointPolygonTest).
- Track state management: position smoothing, trajectory trails, and heading angle estimation.
- 2D Footprint and dot symbol rendering with class-specific dimensions.
- Background generation: warped frame, synthetic dark road/grid/pastel, or custom blueprint image.
- Flexible layout composition: side-by-side dashboard, BEV-only, or camera overlay.
"""

from collections import deque
import math
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle", "bicycle", "train", "vehicle"}
DEFAULT_SYMBOL_SIZES = {
    "car": (10, 24),
    "truck": (13, 36),
    "bus": (13, 40),
    "train": (14, 44),
    "motorcycle": (6, 14),
    "bicycle": (5, 13),
    "person": (7, 9),
    "forklift": (12, 22),
    "default": (10, 22),
}

DARK = (18, 18, 18)
VIDEO_BACKGROUND = (104, 31, 17)  # #111F68 in OpenCV BGR
WHITE = (245, 245, 245)
ID_BACKGROUND = (255, 42, 17)  # Yellow in BGR
ID_TEXT = (255, 255, 255)
SELECTION_ORANGE = (0, 165, 255)
BEV_DARK_YELLOW = (0, 164, 201)  # #C9A400 in OpenCV BGR
CYAN_ACCENT = (255, 200, 0)


def parse_points(points_val: Any, frame_shape: Tuple[int, int]) -> Optional[np.ndarray]:
    """
    Parse 4 ground plane calibration points from list, tuple, or semicolon string.
    Points can be normalized [0, 1] or absolute pixel coordinates.
    Returns float32 numpy array of shape (4, 2) in absolute pixel coordinates.
    """
    h, w = frame_shape[:2]
    raw_points = []

    if isinstance(points_val, str):
        parts = [p.strip() for p in points_val.split(";") if p.strip()]
        for p in parts:
            coords = [float(c.strip()) for c in p.split(",") if c.strip()]
            if len(coords) == 2:
                raw_points.append(coords)
    elif isinstance(points_val, (list, tuple)):
        for item in points_val:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                raw_points.append([float(item[0]), float(item[1])])
            elif isinstance(item, dict) and "x" in item and "y" in item:
                raw_points.append([float(item["x"]), float(item["y"])])

    if len(raw_points) != 4:
        return None

    pts = np.asarray(raw_points, dtype=np.float32)
    # Check if normalized [0, 1]
    if np.all(pts >= 0.0) and np.all(pts <= 1.05):
        pts[:, 0] *= w
        pts[:, 1] *= h

    pts[:, 0] = np.clip(pts[:, 0], 0, max(0, w - 1))
    pts[:, 1] = np.clip(pts[:, 1], 0, max(0, h - 1))

    contour = pts.reshape(-1, 1, 2)
    if cv2.contourArea(contour) < 50 or not cv2.isContourConvex(contour):
        return None

    return pts


class HomographyEngine:
    """Manages ground plane perspective calibration, track state, and BEV coordinate projection."""

    def __init__(self, node_id: str = "homography"):
        self.node_id = node_id
        self.homography_matrix: Optional[np.ndarray] = None
        self.inv_homography_matrix: Optional[np.ndarray] = None
        self.source_points: Optional[np.ndarray] = None
        self.target_points: Optional[np.ndarray] = None
        self.bev_width = 640
        self.bev_height = 360
        self.header_height = 40
        self.states: Dict[str, Dict[str, Any]] = {}
        self.frame_index = 0

    def configure(
        self,
        points: Any,
        frame_shape: Tuple[int, int],
        bev_width: int = 640,
        bev_height: int = 360,
        real_width_meters: float = 0.0,
        real_length_meters: float = 0.0,
    ) -> bool:
        """Calculate homography transformation matrix from 4 ground plane points."""
        pts = parse_points(points, frame_shape)
        if pts is None:
            return False

        self.source_points = pts
        self.bev_width = max(160, int(bev_width))
        self.bev_height = max(160, int(bev_height))
        self.header_height = min(60, self.bev_height // 6)

        margin = 20
        target = np.float32([
            [margin, self.header_height + margin],
            [self.bev_width - margin, self.header_height + margin],
            [self.bev_width - margin, self.bev_height - margin],
            [margin, self.bev_height - margin],
        ])

        H = cv2.getPerspectiveTransform(pts, target)
        if not np.isfinite(H).all() or abs(np.linalg.det(H)) < 1e-12:
            return False

        self.target_points = target
        self.homography_matrix = H
        try:
            self.inv_homography_matrix = np.linalg.inv(H)
        except Exception:
            self.inv_homography_matrix = None

        self.real_width_meters = float(real_width_meters) if real_width_meters > 0 else None
        self.real_length_meters = float(real_length_meters) if real_length_meters > 0 else None
        return True

    def _new_track_state(self, trail_length: int = 45) -> Dict[str, Any]:
        return {
            "position": None,
            "angle": 0.0,
            "last_seen": -1,
            "positions": deque(maxlen=8),
            "trail": deque(maxlen=trail_length),
            "speed_kmh": 0.0,
            "last_timestamp": 0.0,
        }

    def project_bottom_center(self, bbox: List[float]) -> Tuple[float, float]:
        """Compute bottom-center contact point from bbox [x, y, w, h]."""
        x, y, w, h = bbox
        return float(x + w / 2.0), float(y + h)

    def is_inside_ground_plane(self, foot: Tuple[float, float]) -> bool:
        """Check if contact point is inside the 4-point ground quadrilateral."""
        if self.source_points is None:
            return True
        return cv2.pointPolygonTest(self.source_points, foot, False) >= 0

    def process_frame(
        self,
        frame: Any,
        detections: List[Dict[str, Any]],
        config: Dict[str, Any],
        now: float,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Projects detections to BEV coordinates and updates track states.
        Returns:
            (augmented_detections, telemetry_summary)
        """
        self.frame_index += 1
        h, w = frame.shape[:2] if hasattr(frame, "shape") else (720, 1280)

        bev_width = int(config.get("bevWidth", 640))
        bev_height = int(config.get("bevHeight", 360))
        filter_outside = bool(config.get("filterOutsideGround", True))
        trail_length = max(5, int(config.get("trailLength", 45)))
        real_w_m = float(config.get("realWidthMeters", 0.0))
        real_l_m = float(config.get("realLengthMeters", 0.0))

        raw_points = config.get("points") or config.get("groundPoints")
        if self.homography_matrix is None or raw_points is not None:
            self.configure(raw_points, (h, w), bev_width, bev_height, real_w_m, real_l_m)

        augmented = []
        inside_count = 0
        outside_count = 0

        # Expire old tracks absent for over 120 frames
        expired = [tid for tid, st in self.states.items() if self.frame_index - st["last_seen"] > 120]
        for tid in expired:
            del self.states[tid]

        for det in detections:
            bbox = det.get("bbox")
            if not bbox or len(bbox) < 4:
                continue

            foot = self.project_bottom_center(bbox)
            is_inside = self.is_inside_ground_plane(foot)

            if is_inside:
                inside_count += 1
            else:
                outside_count += 1
                if filter_outside:
                    continue

            det_copy = dict(det)
            det_copy["ground_foot"] = list(foot)
            det_copy["is_inside_ground"] = is_inside

            if self.homography_matrix is not None:
                pt_arr = np.float32([[[foot[0], foot[1]]]])
                mapped = cv2.perspectiveTransform(pt_arr, self.homography_matrix)[0, 0]
                raw_bev_x, raw_bev_y = float(mapped[0]), float(mapped[1])

                track_id = str(det.get("trackId", det.get("track_id", det.get("id", ""))))
                if not track_id:
                    track_id = f"temp_{id(det)}"

                state = self.states.setdefault(track_id, self._new_track_state(trail_length))
                if state["last_seen"] != self.frame_index - 1:
                    state["positions"].clear()
                    state["trail"].clear()

                category = str(det.get("class", "default")).lower()
                raw_pos = np.float32([raw_bev_x, raw_bev_y])

                # Smoothing position
                if category in VEHICLE_CLASSES:
                    prev = raw_pos if state["position"] is None else state["position"]
                    delta = raw_pos - prev
                    state["position"] = prev if np.linalg.norm(delta) < 2.0 else prev + 0.25 * delta
                else:
                    state["position"] = raw_pos

                cur_pos = (float(state["position"][0]), float(state["position"][1]))
                state["positions"].append(cur_pos)
                state["trail"].append(cur_pos)

                # Estimate heading orientation angle
                if len(state["positions"]) > 1:
                    d_pos = np.float32(cur_pos) - np.float32(state["positions"][0])
                    if np.linalg.norm(d_pos) >= 3.0:
                        target_deg = float(np.degrees(np.arctan2(d_pos[1], d_pos[0])) - 90)
                        diff = (target_deg - state["angle"] + 90) % 180 - 90
                        state["angle"] += 0.25 * diff

                # Metric speed estimation if real-world length/width specified
                if self.real_length_meters and self.target_points is not None:
                    bev_active_height = float(self.target_points[2, 1] - self.target_points[0, 1])
                    if bev_active_height > 0 and len(state["positions"]) > 2 and state["last_timestamp"] > 0:
                        dt = now - state["last_timestamp"]
                        if 0.02 < dt < 1.0:
                            dist_px = float(np.linalg.norm(d_pos))
                            dist_m = (dist_px / bev_active_height) * self.real_length_meters
                            speed_mps = dist_m / dt
                            state["speed_kmh"] = round(speed_mps * 3.6, 1)

                state["last_seen"] = self.frame_index
                state["last_timestamp"] = now

                det_copy["bev_x"] = cur_pos[0]
                det_copy["bev_y"] = cur_pos[1]
                det_copy["bev_angle"] = float(state["angle"])
                det_copy["bev_trail"] = list(state["trail"])
                det_copy["speed_kmh"] = state.get("speed_kmh", 0.0)

            augmented.append(det_copy)

        telemetry = {
            "node_id": self.node_id,
            "type": "homography_projection_summary",
            "inside_ground_count": inside_count,
            "outside_ground_count": outside_count,
            "active_tracks_bev": len(self.states),
            "has_calibration": self.homography_matrix is not None,
            "timestamp": now,
        }

        return augmented, telemetry


class BEVRenderer:
    """Renders top-down Bird's Eye View map and composes dashboard layout."""

    def __init__(self, node_id: str = "bev_visualizer"):
        self.node_id = node_id
        self.background_cache: Optional[np.ndarray] = None
        self.cached_style: Optional[str] = None
        self.cached_dims: Optional[Tuple[int, int]] = None

    def _build_background(
        self,
        style: str,
        bev_w: int,
        bev_h: int,
        header_h: int,
        custom_img_path: Optional[str] = None,
        source_frame: Optional[np.ndarray] = None,
        H: Optional[np.ndarray] = None,
        corners: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Create static or warped background canvas."""
        canvas = np.full((bev_h, bev_w, 3), VIDEO_BACKGROUND, dtype=np.uint8)

        if style == "pastel":
            canvas[:] = (245, 242, 240)
        elif style == "grid":
            canvas[:] = (24, 28, 36)
            for gx in range(0, bev_w, 40):
                cv2.line(canvas, (gx, header_h), (gx, bev_h), (35, 42, 54), 1)
            for gy in range(header_h, bev_h, 40):
                cv2.line(canvas, (0, gy), (bev_w, gy), (35, 42, 54), 1)
        elif style == "custom" and custom_img_path and os.path.isfile(custom_img_path):
            img = cv2.imread(custom_img_path)
            if img is not None:
                canvas = cv2.resize(img, (bev_w, bev_h))
        elif style == "warped_frame" and source_frame is not None and H is not None and corners is not None:
            warped = cv2.warpPerspective(source_frame, H, (bev_w, bev_h))
            road = cv2.addWeighted(warped, 0.65, np.full_like(warped, DARK), 0.35, 0)
            # Mask to ground polygon
            mask = np.zeros(source_frame.shape[:2], dtype=np.uint8)
            cv2.fillConvexPoly(mask, corners.astype(np.int32), 255)
            warped_mask = cv2.warpPerspective(mask, H, (bev_w, bev_h), flags=cv2.INTER_NEAREST) > 0
            canvas[warped_mask] = road[warped_mask]

        # Draw boundary polyline
        if corners is not None and H is not None:
            boundary = cv2.perspectiveTransform(corners.reshape(-1, 1, 2), H)
            cv2.polylines(canvas, [np.rint(boundary).astype(np.int32)], True, WHITE, 2, cv2.LINE_AA)

        # Draw Header
        canvas[:header_h] = VIDEO_BACKGROUND
        title = "Bird's Eye View (BEV)"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.4, min(0.8, (bev_w - 40) / 450))
        cv2.putText(canvas, title, (20, int(header_h * 0.7)), font, font_scale, WHITE, 1, cv2.LINE_AA)

        return canvas

    def _draw_rotated_footprint(
        self,
        canvas: np.ndarray,
        center: Tuple[int, int],
        category: str,
        angle: float,
        scale: float = 1.0,
    ) -> np.ndarray:
        """Render 2D rotated vehicle/person rectangle on BEV canvas."""
        w, l = DEFAULT_SYMBOL_SIZES.get(category, DEFAULT_SYMBOL_SIZES["default"])
        size = (w * scale, l * scale)
        rect = ((float(center[0]), float(center[1])), size, float(angle))
        poly = np.rint(cv2.boxPoints(rect)).astype(np.int32)
        cv2.fillConvexPoly(canvas, poly, BEV_DARK_YELLOW, cv2.LINE_AA)
        cv2.polylines(canvas, [poly], True, WHITE, 1, cv2.LINE_AA)
        return poly

    def _draw_bev_label(
        self,
        canvas: np.ndarray,
        pos: Tuple[int, int],
        label: str,
        bev_w: int,
        bev_h: int,
    ) -> None:
        """Render small identifier badge centered at coordinate."""
        font, font_scale = cv2.FONT_HERSHEY_SIMPLEX, 0.35
        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, 1)
        bx, by = pos[0] - tw // 2, pos[1] - th // 2
        pad = 2
        x1, y1 = max(0, bx - pad), max(0, by - pad)
        x2, y2 = min(bev_w, bx + tw + pad), min(bev_h, by + th + pad)
        if x2 > x1 and y2 > y1:
            cv2.rectangle(canvas, (x1, y1), (x2, y2), ID_BACKGROUND, -1)
            cv2.putText(canvas, label, (bx, by + th), font, font_scale, ID_TEXT, 1, cv2.LINE_AA)

    def render_bev_canvas(
        self,
        frame: Optional[np.ndarray],
        detections: List[Dict[str, Any]],
        config: Dict[str, Any],
        H: Optional[np.ndarray],
        corners: Optional[np.ndarray],
    ) -> np.ndarray:
        """Renders the top-down BEV canvas with tracked symbols and trails."""
        bev_w = max(160, int(config.get("bevWidth", 640)))
        bev_h = max(160, int(config.get("bevHeight", 360)))
        header_h = min(50, bev_h // 6)
        style = str(config.get("mapStyle", "dark_road")).lower()
        marker_type = str(config.get("markerType", "footprint")).lower()
        show_ids = bool(config.get("showIds", True))
        show_speed = bool(config.get("showSpeed", True))
        custom_img = config.get("customMapImage")

        # Background caching if static style
        cache_key = f"{style}_{bev_w}_{bev_h}"
        if self.background_cache is None or self.cached_style != cache_key or style == "warped_frame":
            self.background_cache = self._build_background(
                style, bev_w, bev_h, header_h, custom_img, frame, H, corners
            )
            self.cached_style = cache_key

        canvas = self.background_cache.copy()

        # Render trails and markers
        scale = max(0.5, min(2.0, bev_h / 480))
        for det in detections:
            bev_x = det.get("bev_x")
            bev_y = det.get("bev_y")
            if bev_x is None or bev_y is None:
                continue

            pt = (int(round(bev_x)), int(round(bev_y)))
            if not (0 <= pt[0] < bev_w and header_h <= pt[1] < bev_h):
                continue

            trail = det.get("bev_trail")
            if trail and len(trail) > 1:
                trail_pts = np.array([[int(round(p[0])), int(round(p[1]))] for p in trail], dtype=np.int32)
                cv2.polylines(canvas, [trail_pts], False, BEV_DARK_YELLOW, 2, cv2.LINE_AA)

            category = str(det.get("class", "car")).lower()
            angle = float(det.get("bev_angle", 0.0))

            if marker_type == "footprint":
                self._draw_rotated_footprint(canvas, pt, category, angle, scale)
            else:
                cv2.circle(canvas, pt, 6, WHITE, -1, cv2.LINE_AA)
                cv2.circle(canvas, pt, 4, CYAN_ACCENT, -1, cv2.LINE_AA)

            track_id = det.get("trackId", det.get("track_id", det.get("id")))
            lbl = f"#{track_id}" if track_id is not None else ""
            if show_speed and det.get("speed_kmh", 0) > 0:
                lbl = f"{lbl} {det['speed_kmh']}k" if lbl else f"{det['speed_kmh']}km/h"

            if show_ids and lbl:
                self._draw_bev_label(canvas, (pt[0], pt[1] - 12), lbl.strip(), bev_w, bev_h)

        return canvas

    def compose_layout(
        self,
        camera_frame: np.ndarray,
        bev_canvas: np.ndarray,
        layout: str = "side_by_side",
        corners: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Combines camera frame and BEV map into final visual stream."""
        layout = str(layout).lower()
        if layout == "bev_only":
            return bev_canvas

        annotated_cam = camera_frame.copy()
        if corners is not None:
            # Draw Ground Plane Polygon on original camera frame
            cv2.polylines(annotated_cam, [corners.astype(np.int32)], True, WHITE, 2, cv2.LINE_AA)
            for idx, pt in enumerate(corners):
                p_int = tuple(np.rint(pt).astype(int))
                cv2.circle(annotated_cam, p_int, 6, SELECTION_ORANGE, -1, cv2.LINE_AA)
                cv2.putText(annotated_cam, str(idx + 1), (p_int[0] + 6, p_int[1] - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1, cv2.LINE_AA)

        if layout == "camera_overlay":
            # Overlay BEV mini-map in top-right corner
            bev_h, bev_w = bev_canvas.shape[:2]
            cam_h, cam_w = annotated_cam.shape[:2]
            mini_w = max(160, cam_w // 4)
            mini_h = int(mini_w * (bev_h / bev_w))
            mini_map = cv2.resize(bev_canvas, (mini_w, mini_h))
            annotated_cam[10:10 + mini_h, cam_w - mini_w - 10:cam_w - 10] = mini_map
            cv2.rectangle(annotated_cam, (cam_w - mini_w - 10, 10), (cam_w - 10, 10 + mini_h), WHITE, 1)
            return annotated_cam

        # Default: side_by_side dashboard
        cam_h, cam_w = annotated_cam.shape[:2]
        bev_h, bev_w = bev_canvas.shape[:2]
        target_h = max(cam_h, bev_h)

        # Scale both to target height
        scaled_cam = cv2.resize(annotated_cam, (int(cam_w * (target_h / cam_h)), target_h))
        scaled_bev = cv2.resize(bev_canvas, (int(bev_w * (target_h / bev_h)), target_h))

        composite = np.concatenate((scaled_cam, scaled_bev), axis=1)
        # Draw vertical separator line
        sep_x = scaled_cam.shape[1]
        cv2.line(composite, (sep_x, 0), (sep_x, target_h - 1), (50, 50, 50), 2)
        return composite
