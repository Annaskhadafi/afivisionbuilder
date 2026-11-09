"""Video Playback & Timeline Controller Engine.

Provides playback speed regulation (0.25x - 4.0x / slow-motion to fast-forward),
timeline seeking (jump to percentage, e.g. 50% middle, or jump to timestamp/seconds),
section looping, and on-screen HUD rendering for video files and YouTube streams.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

VIDEO_SPEED_DEFAULTS = {
    "playbackSpeed": 1.0,         # 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0
    "speedMode": "smooth",        # "smooth" (delay pacing) or "fast_forward" (skip frames)
    "timelinePercent": 0.0,       # 0.0 to 100.0 (e.g. 50.0 = middle)
    "seekTimestampSec": 0.0,      # timestamp in seconds
    "seekMode": "percent",        # "percent" or "timestamp"
    "jumpToMiddle": False,        # trigger jump to 50%
    "pause": False,               # pause playback
    "loopSection": False,         # loop section
    "loopStartPercent": 0.0,      # loop start %
    "loopEndPercent": 100.0,      # loop end %
    "showOverlayHud": False,      # overlay HUD on frame
    "hudPosition": "top_left",    # top_left, top_right, bottom_left, bottom_right
}


def normalize_video_speed_config(config: dict) -> dict:
    """Ensure all required keys and valid types exist in configuration."""
    cfg = dict(VIDEO_SPEED_DEFAULTS)
    if isinstance(config, dict):
        cfg.update(config)
    try:
        cfg["playbackSpeed"] = max(0.1, min(10.0, float(cfg.get("playbackSpeed", 1.0) or 1.0)))
    except (ValueError, TypeError):
        cfg["playbackSpeed"] = 1.0
    try:
        cfg["timelinePercent"] = max(0.0, min(100.0, float(cfg.get("timelinePercent", 0.0) or 0.0)))
    except (ValueError, TypeError):
        cfg["timelinePercent"] = 0.0
    try:
        cfg["seekTimestampSec"] = max(0.0, float(cfg.get("seekTimestampSec", 0.0) or 0.0))
    except (ValueError, TypeError):
        cfg["seekTimestampSec"] = 0.0
    cfg["pause"] = bool(cfg.get("pause", False))
    cfg["jumpToMiddle"] = bool(cfg.get("jumpToMiddle", False))
    cfg["showOverlayHud"] = bool(cfg.get("showOverlayHud", False))
    return cfg


def format_seconds_to_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    seconds = max(0.0, float(seconds or 0.0))
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def parse_time_to_seconds(time_str: str | float | int) -> float:
    """Parse string '01:30' or '01:15:30' or numeric seconds into float seconds."""
    if isinstance(time_str, (int, float)):
        return max(0.0, float(time_str))
    raw = str(time_str or "").strip()
    if not raw:
        return 0.0
    if ":" in raw:
        parts = raw.split(":")
        try:
            if len(parts) == 2:
                return max(0.0, float(parts[0]) * 60 + float(parts[1]))
            if len(parts) == 3:
                return max(0.0, float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2]))
        except ValueError:
            return 0.0
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.0


def render_playback_hud(
    frame: np.ndarray,
    config: dict,
    status: dict,
) -> np.ndarray:
    """Draw a clean, sleek playback HUD badge with speed & timecode onto the frame."""
    if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
        return frame

    h, w = frame.shape[:2]
    out = frame.copy()

    speed = float(config.get("playbackSpeed", 1.0) or 1.0)
    is_paused = bool(config.get("pause", False))
    percent = float(status.get("progress_percent", 0.0) or 0.0)
    cur_time = str(status.get("current_time_str") or "00:00")
    dur_time = str(status.get("duration_str") or "00:00")
    pos_mode = str(config.get("hudPosition", "top_left") or "top_left").lower()

    # Badge text
    status_icon = "PAUSED" if is_paused else f"{speed:.2f}".rstrip("0").rstrip(".") + "x"
    text = f"PLAYBACK: {status_icon} | {cur_time} / {dur_time} ({percent:.1f}%)"

    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.55
    thickness = 1
    (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)

    pad_x = 12
    pad_y = 8
    badge_w = text_w + pad_x * 2
    badge_h = text_h + pad_y * 2 + 6  # Extra height for mini progress bar

    if pos_mode == "top_right":
        x1 = w - badge_w - 16
        y1 = 16
    elif pos_mode == "bottom_left":
        x1 = 16
        y1 = h - badge_h - 16
    elif pos_mode == "bottom_right":
        x1 = w - badge_w - 16
        y1 = h - badge_h - 16
    else:  # top_left default
        x1 = 16
        y1 = 16

    x2 = x1 + badge_w
    y2 = y1 + badge_h

    # Ensure coordinates stay within frame bounds
    x1 = max(0, min(w - badge_w, x1))
    y1 = max(0, min(h - badge_h, y1))
    x2 = min(w, x1 + badge_w)
    y2 = min(h, y1 + badge_h)

    # Semi-transparent dark background
    overlay = out.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (20, 24, 33), -1)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (59, 130, 246), 1)  # Blue border
    alpha = 0.82
    cv2.addWeighted(overlay, alpha, out, 1 - alpha, 0, out)

    # Draw text
    text_y = y1 + pad_y + text_h
    cv2.putText(out, text, (x1 + pad_x, text_y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    # Draw mini progress bar at bottom of badge
    bar_x1 = x1 + pad_x
    bar_x2 = x2 - pad_x
    bar_y = y2 - 5
    bar_w = bar_x2 - bar_x1
    if bar_w > 10:
        cv2.line(out, (bar_x1, bar_y), (bar_x2, bar_y), (75, 85, 99), 2)  # Gray rail
        fill_w = int(bar_w * (max(0.0, min(100.0, percent)) / 100.0))
        if fill_w > 0:
            cv2.line(out, (bar_x1, bar_y), (bar_x1 + fill_w, bar_y), (37, 99, 235), 2)  # Blue fill

    return out
