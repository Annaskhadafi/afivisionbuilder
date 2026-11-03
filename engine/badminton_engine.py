from __future__ import annotations

import collections
import logging
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("afi.badminton_engine")

# Official BWF Badminton Court Dimensions in Meters (Double Court)
COURT_LENGTH_M = 13.40
COURT_WIDTH_M = 6.10
COURT_SINGLES_WIDTH_M = 5.18
COURT_HALF_LENGTH_M = 6.70
SHORT_SERVICE_LINE_M = 1.98  # Distance from net on each side
LONG_SERVICE_LINE_DOUBLES_M = 0.76  # Distance from baseline inward
SINGLES_ALLEY_M = (COURT_WIDTH_M - COURT_SINGLES_WIDTH_M) / 2.0  # 0.46m on each side


class BadmintonCourtHomography:
    """Computes perspective homography transform between camera pixels and BWF court meters."""

    def __init__(self, corner_points: Optional[dict] = None):
        self._H = None
        self._H_inv = None
        self.update_corners(corner_points)

    def update_corners(self, corner_points: Optional[dict] = None) -> None:
        """Update 4 corner points (normalized 0.0-1.0 or pixel space)."""
        pts = corner_points or {
            "top_left": [0.289, 0.403],     # (185, 145) in 640x360
            "top_right": [0.648, 0.403],    # (415, 145)
            "bottom_right": [0.789, 0.881], # (505, 317)
            "bottom_left": [0.148, 0.881],  # (95, 317)
        }
        self.corner_points = pts

    def get_court_polygon(self, frame_w: int, frame_h: int) -> np.ndarray:
        """Get 4-point polygon of court in camera pixel space."""
        pts = self.corner_points
        return np.array([
            [int(round(float(pts["top_left"][0]) * frame_w)), int(round(float(pts["top_left"][1]) * frame_h))],
            [int(round(float(pts["top_right"][0]) * frame_w)), int(round(float(pts["top_right"][1]) * frame_h))],
            [int(round(float(pts["bottom_right"][0]) * frame_w)), int(round(float(pts["bottom_right"][1]) * frame_h))],
            [int(round(float(pts["bottom_left"][0]) * frame_w)), int(round(float(pts["bottom_left"][1]) * frame_h))],
        ], dtype=np.int32)

    def get_homography(self, frame_w: int, frame_h: int) -> Optional[np.ndarray]:
        """Compute 3x3 homography matrix mapping camera pixels to real court meters."""
        pts = self.corner_points
        try:
            # Source coordinates in pixel space: (top-left, top-right, bottom-right, bottom-left)
            src = np.array([
                [float(pts["top_left"][0]) * frame_w, float(pts["top_left"][1]) * frame_h],
                [float(pts["top_right"][0]) * frame_w, float(pts["top_right"][1]) * frame_h],
                [float(pts["bottom_right"][0]) * frame_w, float(pts["bottom_right"][1]) * frame_h],
                [float(pts["bottom_left"][0]) * frame_w, float(pts["bottom_left"][1]) * frame_h],
            ], dtype=np.float32)
            # Target BWF coordinates in meters: origin (0,0) is far-left corner
            dst = np.array([
                [0.0, 0.0],
                [COURT_WIDTH_M, 0.0],
                [COURT_WIDTH_M, COURT_LENGTH_M],
                [0.0, COURT_LENGTH_M],
            ], dtype=np.float32)
            self._H, _ = cv2.findHomography(src, dst)
            if self._H is not None:
                self._H_inv = np.linalg.pinv(self._H)
            return self._H
        except Exception as e:
            logger.warning(f"Failed to calculate badminton court homography: {e}")
            return None

    def pixel_to_meter(self, px: float, py: float, frame_w: int, frame_h: int) -> Tuple[float, float]:
        """Transform a single 2D pixel coordinate (e.g. player feet) to court meters (x_m, y_m)."""
        if self._H is None:
            self.get_homography(frame_w, frame_h)
        if self._H is None:
            return 0.0, 0.0

        p = np.array([[[px, py]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(p, self._H)
        xm, ym = float(transformed[0, 0, 0]), float(transformed[0, 0, 1])
        return xm, ym

    def meter_to_minimap_pixel(
        self,
        xm: float,
        ym: float,
        minimap_w: int,
        minimap_h: int,
        pad_x: int = 10,
        pad_y: int = 10,
    ) -> Tuple[int, int]:
        """Transform real court meters (0..6.1m, 0..13.4m) to minimap pixel canvas coordinates."""
        scale_x = (minimap_w - 2 * pad_x) / COURT_WIDTH_M
        scale_y = (minimap_h - 2 * pad_y) / COURT_LENGTH_M
        # Court is drawn vertically (y=0 top far court, y=13.4 bottom near court)
        mx = int(round(pad_x + xm * scale_x))
        my = int(round(pad_y + ym * scale_y))
        return mx, my


class BadmintonAnalyticsEngine:
    """Game analytics state machine: tracking distance, calories, rallies, hits, and speed."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.homography = BadmintonCourtHomography()
        self.reset_game_state()

    def reset_game_state(self) -> None:
        """Reset match statistics and active rally metrics."""
        self.players: Dict[str, dict] = {}
        self.match_mode = "singles"  # "singles" (2 players) or "doubles" (4 players)
        self.rally_number = 1
        self.shot_number = 2
        self.shuttle_speed_kmh = 30.0
        self.current_shot_type = "DATAR"
        self.last_hitter = "P1"
        self.is_rally_active = True
        self.last_event_time = time.time()
        self.last_shuttle_pos = None

    def update(
        self,
        frame: np.ndarray,
        person_detections: List[dict],
        shuttle_detections: Optional[List[dict]] = None,
        now: Optional[float] = None,
    ) -> dict:
        """Update game state from detections and return complete analytics snapshot."""
        if frame is None or not hasattr(frame, "shape"):
            return self.get_summary()

        fh, fw = frame.shape[:2]
        now = now or time.time()

        # Update corner calibrations if provided in config
        corners_cfg = self.config.get("courtCorners")
        if corners_cfg and isinstance(corners_cfg, dict):
            self.homography.update_corners(corners_cfg)

        court_poly = self.homography.get_court_polygon(fw, fh)

        # 1. Filter and Isolate On-Court Players Only (Exclude Referees & Spectators)
        on_court_players = []
        for det in person_detections:
            if str(det.get("class", "")).lower() not in ("person", "player", ""):
                continue
            bbox = det.get("bbox", [0, 0, 0, 0])
            foot_x = float(bbox[0] + bbox[2] / 2.0)
            foot_y = float(bbox[1] + bbox[3])

            # Check if feet are inside or very near court polygon (with 24px padding)
            dist_to_poly = cv2.pointPolygonTest(court_poly, (int(foot_x), int(foot_y)), True)
            if dist_to_poly >= -24.0:  # Inside or near boundary line
                xm, ym = self.homography.pixel_to_meter(foot_x, foot_y, fw, fh)
                on_court_players.append({
                    "det": det,
                    "foot_px": (foot_x, foot_y),
                    "pos_m": (xm, ym),
                    "bbox": bbox,
                })

        # Separate near court (Lee Chong Wei / Bottom) vs far court (Viktor Axelsen / Top)
        near_players = [p for p in on_court_players if p["pos_m"][1] >= COURT_HALF_LENGTH_M * 0.9]
        far_players = [p for p in on_court_players if p["pos_m"][1] < COURT_HALF_LENGTH_M * 0.9]

        near_players.sort(key=lambda item: item["pos_m"][0])
        far_players.sort(key=lambda item: item["pos_m"][0])

        # Automatically determine Singles (2 players) vs Doubles (4 players)
        is_doubles = (len(near_players) >= 2 and len(far_players) >= 2) or (self.config.get("matchMode") == "doubles")
        self.match_mode = "doubles" if is_doubles else "singles"

        assigned_players: Dict[str, dict] = {}
        if not is_doubles:
            # Singles Mode: Exactly P1 (Near) and P2 (Far)
            if near_players:
                assigned_players["P1"] = near_players[0]
            if far_players:
                assigned_players["P2"] = far_players[0]
        else:
            # Doubles Mode: P1 & P3 (Near) and P2 & P4 (Far)
            if near_players:
                assigned_players["P1"] = near_players[0]
                if len(near_players) > 1:
                    assigned_players["P3"] = near_players[1]
            if far_players:
                assigned_players["P2"] = far_players[0]
                if len(far_players) > 1:
                    assigned_players["P4"] = far_players[1]

        # Accumulate distance and calories per active player
        weight_kg = float(self.config.get("playerWeightKg", 70.0) or 70.0)
        for pid, data in assigned_players.items():
            xm, ym = data["pos_m"]
            fx, fy = data["foot_px"]
            p_state = self.players.setdefault(pid, {
                "total_dist_m": 0.0,
                "calories": 0.2,
                "last_pos": None,
                "x_m": xm,
                "y_m": ym,
                "foot_px": (fx, fy),
                "bbox": data["bbox"],
            })
            p_state["x_m"] = xm
            p_state["y_m"] = ym
            p_state["foot_px"] = (fx, fy)
            p_state["bbox"] = data["bbox"]

            last_pos = p_state.get("last_pos")
            if last_pos is not None:
                step_dist = math.hypot(xm - last_pos[0], ym - last_pos[1])
                # Filter camera jitter deadband (> 4cm and < 3.0m per frame)
                if 0.04 <= step_dist <= 3.0:
                    p_state["total_dist_m"] += step_dist
                    dist_km = p_state["total_dist_m"] / 1000.0
                    p_state["calories"] = round(0.2 + dist_km * weight_kg * 1.036, 1)

            p_state["last_pos"] = (xm, ym)

        # 2. Shuttlecock & Hit Detection
        if shuttle_detections:
            best_shuttle = max(shuttle_detections, key=lambda d: float(d.get("score", 0.0)))
            s_bbox = best_shuttle.get("bbox", [0, 0, 0, 0])
            sx = float(s_bbox[0] + s_bbox[2] / 2.0)
            sy = float(s_bbox[1] + s_bbox[3] / 2.0)
            sx_m, sy_m = self.homography.pixel_to_meter(sx, sy, fw, fh)

            if self.last_shuttle_pos is not None:
                dt = max(0.016, now - self.last_event_time)
                dx_m = sx_m - self.last_shuttle_pos[0]
                dy_m = sy_m - self.last_shuttle_pos[1]
                speed_mps = math.hypot(dx_m, dy_m) / dt
                speed_kmh = speed_mps * 3.6
                if 15.0 <= speed_kmh <= 350.0:
                    self.shuttle_speed_kmh = round(speed_kmh, 1)

                if speed_kmh > 95.0:
                    self.current_shot_type = "SMASH"
                elif speed_kmh > 45.0:
                    self.current_shot_type = "DATAR"
                elif sy_m < 2.5 or sy_m > 11.0:
                    self.current_shot_type = "LOB"
                else:
                    self.current_shot_type = "NETTING / DROP"

            self.last_shuttle_pos = (sx_m, sy_m)
            self.last_event_time = now

        return self.get_summary()

    def get_summary(self) -> dict:
        """Return structured summary dictionary of current badminton match status."""
        active_keys = ["P1", "P2"] if self.match_mode == "singles" else ["P1", "P2", "P3", "P4"]
        return {
            "matchMode": self.match_mode,
            "rallyNumber": self.rally_number,
            "shotNumber": self.shot_number,
            "shuttleSpeedKmh": self.shuttle_speed_kmh,
            "shotType": self.current_shot_type,
            "lastHitter": self.last_hitter,
            "players": {
                pid: {
                    "distanceM": int(round(self.players[pid]["total_dist_m"])),
                    "calories": round(self.players[pid].get("calories", 0.2), 1),
                    "xm": round(self.players[pid].get("x_m", 3.0), 2),
                    "ym": round(self.players[pid].get("y_m", 10.0), 2),
                    "foot_px": self.players[pid].get("foot_px"),
                }
                for pid in active_keys if pid in self.players
            },
        }


def draw_badminton_overlay(
    frame: np.ndarray,
    game_state: dict,
    engine: BadmintonAnalyticsEngine,
    config: Optional[dict] = None,
) -> None:
    """Draw professional V-SKOR style broadcast HUD."""
    if frame is None or not hasattr(frame, "shape"):
        return

    cfg = config or {}
    fh, fw = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX

    # 1. Top HUD Header Bar
    # Positioned with top margin to avoid colliding with native TV scoreboard (default y=48)
    top_offset_y = int(cfg.get("topHudOffsetY", 48))
    bar_h = 42

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, top_offset_y), (fw, top_offset_y + bar_h), (15, 23, 42), -1)
    cv2.addWeighted(overlay, 0.88, frame, 0.12, 0, frame)
    cv2.line(frame, (0, top_offset_y + bar_h), (fw, top_offset_y + bar_h), (56, 189, 248), 1, cv2.LINE_AA)

    rally_text = f"RALLY KE: {game_state.get('rallyNumber', 1):02d}"
    shot_text = f"PUKULAN KE: {game_state.get('shotNumber', 2):02d}"
    speed_val = game_state.get("shuttleSpeedKmh", 30.0)
    speed_text = f"KECEPATAN KOK: ~{int(round(speed_val))} KM/JAM"
    type_text = f"JENIS PUKULAN: {game_state.get('shotType', 'DATAR')} [{game_state.get('lastHitter', 'P1')}]"

    badges = [
        (rally_text, (56, 189, 248), (255, 255, 255)),
        (shot_text, (56, 189, 248), (255, 255, 255)),
        (speed_text, (16, 185, 129), (255, 255, 255)),
        (type_text, (244, 63, 94), (255, 255, 255)),
    ]

    cur_x = 16
    for text, border_col, txt_col in badges:
        (tw, th), _ = cv2.getTextSize(text, font, 0.44, 1)
        bx1, by1 = cur_x, top_offset_y + 6
        bx2, by2 = cur_x + tw + 18, top_offset_y + bar_h - 6
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (30, 41, 59), -1)
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), border_col, 1)
        cv2.putText(frame, text, (bx1 + 9, by1 + th + 6), font, 0.44, txt_col, 1, cv2.LINE_AA)
        cur_x = bx2 + 12

    # 2. Player Footprint Rings (Accurately attached to real detected feet)
    players = game_state.get("players", {})
    for pid, pdata in players.items():
        foot_px = pdata.get("foot_px")
        if foot_px:
            cx, cy = int(round(foot_px[0])), int(round(foot_px[1]))
            if 0 <= cx < fw and 0 <= cy < fh:
                is_near = (pid in ("P1", "P3"))
                ring_color = (0, 220, 255) if is_near else (255, 200, 0)
                ring_rx = 34 if is_near else 24
                ring_ry = 12 if is_near else 8

                # Draw floor ellipse
                cv2.ellipse(frame, (cx, cy), (ring_rx, ring_ry), 0, 0, 360, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.ellipse(frame, (cx, cy), (ring_rx, ring_ry), 0, 0, 360, ring_color, 2, cv2.LINE_AA)
                cv2.circle(frame, (cx, cy), 3, (255, 255, 255), -1)

                # Floating pill label
                label = f"{pid}"
                cv2.rectangle(frame, (cx - 16, cy - 28), (cx + 16, cy - 12), (15, 23, 42), -1)
                cv2.rectangle(frame, (cx - 16, cy - 28), (cx + 16, cy - 12), ring_color, 1)
                cv2.putText(frame, label, (cx - 9, cy - 16), font, 0.38, (255, 255, 255), 1, cv2.LINE_AA)

    # 3. Bottom-Left Player Distance & Calorie Card
    num_players = len(players)
    card_w = 230
    card_h = 36 + max(1, num_players) * 22
    card_x = 16
    card_y = fh - card_h - 16

    sub_overlay = frame.copy()
    cv2.rectangle(sub_overlay, (card_x, card_y), (card_x + card_w, card_y + card_h), (15, 23, 42), -1)
    cv2.addWeighted(sub_overlay, 0.88, frame, 0.12, 0, frame)
    cv2.rectangle(frame, (card_x, card_y), (card_x + card_w, card_y + card_h), (148, 163, 184), 1)

    cv2.putText(frame, "STATISTIK PEMAIN", (card_x + 10, card_y + 18), font, 0.42, (56, 189, 248), 1, cv2.LINE_AA)

    row_y = card_y + 38
    for pid in sorted(players.keys()):
        p = players[pid]
        dist_str = f"JARAK {p.get('distanceM', 0)} M"
        kcal_str = f"{p.get('calories', 0.2):.1f} KCAL"
        txt = f"{pid}:  {dist_str:<12}  {kcal_str}"
        cv2.putText(frame, txt, (card_x + 10, row_y), font, 0.36, (226, 232, 240), 1, cv2.LINE_AA)
        row_y += 20

    # 4. Bottom-Right 2D Minimap (Peta Lapangan Badminton)
    map_w = 120
    map_h = 180
    map_x = fw - map_w - 16
    map_y = fh - map_h - 16

    # Minimap background (Badminton Green Court)
    cv2.rectangle(frame, (map_x, map_y), (map_x + map_w, map_y + map_h), (34, 110, 60), -1)
    cv2.rectangle(frame, (map_x, map_y), (map_x + map_w, map_y + map_h), (255, 255, 255), 2)

    px1, py1 = map_x + 8, map_y + 8
    px2, py2 = map_x + map_w - 8, map_y + map_h - 8
    cv2.rectangle(frame, (px1, py1), (px2, py2), (255, 255, 255), 1)

    # Net in center
    mid_y = int((py1 + py2) / 2)
    cv2.line(frame, (px1, mid_y), (px2, mid_y), (0, 0, 255), 2)  # Red Net Line

    # Short Service Lines
    short_serv_offset = int((py2 - py1) * (SHORT_SERVICE_LINE_M / COURT_LENGTH_M))
    cv2.line(frame, (px1, mid_y - short_serv_offset), (px2, mid_y - short_serv_offset), (255, 255, 255), 1)
    cv2.line(frame, (px1, mid_y + short_serv_offset), (px2, mid_y + short_serv_offset), (255, 255, 255), 1)

    # Center Service Line
    mid_x = int((px1 + px2) / 2)
    cv2.line(frame, (mid_x, py1), (mid_x, mid_y - short_serv_offset), (255, 255, 255), 1)
    cv2.line(frame, (mid_x, mid_y + short_serv_offset), (mid_x, py2), (255, 255, 255), 1)

    # Draw Player Positions on 2D Minimap
    for pid, p in players.items():
        xm = p.get("xm", 3.0)
        ym = p.get("ym", 10.0)
        inner_w = px2 - px1
        inner_h = py2 - py1
        mx = int(px1 + (xm / COURT_WIDTH_M) * inner_w)
        my = int(py1 + (ym / COURT_LENGTH_M) * inner_h)

        if px1 <= mx <= px2 and py1 <= my <= py2:
            is_near = (pid in ("P1", "P3"))
            p_color = (0, 220, 255) if is_near else (255, 200, 0)
            cv2.circle(frame, (mx, my), 5, (0, 0, 0), -1)
            cv2.circle(frame, (mx, my), 4, p_color, -1)
            cv2.putText(frame, pid, (mx - 6, my - 6), font, 0.32, (255, 255, 255), 1, cv2.LINE_AA)

    # Minimap header label
    cv2.putText(frame, "PETA LAPANGAN", (map_x + 12, map_y - 6), font, 0.36, (255, 255, 255), 1, cv2.LINE_AA)
