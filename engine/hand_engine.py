from __future__ import annotations

import logging
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("afi.hand_engine")

# 21 Hand Landmarks Connections grouped by finger
# Each tuple: (pt1_idx, pt2_idx, color_bgr)
HAND_CONNECTIONS_WITH_COLORS = [
    # Palm base / metacarpal connections (Slate / Silver)
    (0, 1, (180, 180, 180)),
    (0, 5, (200, 200, 200)),
    (5, 9, (200, 200, 200)),
    (9, 13, (200, 200, 200)),
    (13, 17, (200, 200, 200)),
    (0, 17, (180, 180, 180)),

    # Thumb (Coral Orange: 0, 140, 255)
    (1, 2, (0, 140, 255)),
    (2, 3, (0, 160, 255)),
    (3, 4, (0, 180, 255)),

    # Index Finger (Electric Cyan: 255, 220, 0)
    (5, 6, (255, 200, 0)),
    (6, 7, (255, 220, 30)),
    (7, 8, (255, 240, 60)),

    # Middle Finger (Neon Lime Green: 0, 255, 128)
    (9, 10, (0, 240, 100)),
    (10, 11, (0, 255, 130)),
    (11, 12, (50, 255, 160)),

    # Ring Finger (Golden Yellow: 0, 220, 255)
    (13, 14, (0, 200, 240)),
    (14, 15, (0, 220, 255)),
    (15, 16, (30, 240, 255)),

    # Pinky Finger (Vibrant Magenta: 220, 0, 255)
    (17, 18, (200, 0, 240)),
    (18, 19, (220, 30, 255)),
    (19, 20, (240, 60, 255)),
]

# Joint Keypoint Colors (BGR)
FINGER_JOINT_COLORS = {
    0: (220, 220, 220),   # Wrist
    1: (0, 140, 255), 2: (0, 160, 255), 3: (0, 180, 255), 4: (0, 210, 255),       # Thumb
    5: (255, 200, 0), 6: (255, 220, 30), 7: (255, 240, 60), 8: (255, 255, 100),   # Index
    9: (0, 240, 100), 10: (0, 255, 130), 11: (50, 255, 160), 12: (100, 255, 190),  # Middle
    13: (0, 200, 240), 14: (0, 220, 255), 15: (30, 240, 255), 16: (80, 255, 255),   # Ring
    17: (200, 0, 240), 18: (220, 30, 255), 19: (240, 60, 255), 20: (255, 100, 255), # Pinky
}

# Indonesian Friendly Gesture Translations
GESTURE_TRANSLATIONS = {
    "None": "Mendeteksi Tangan",
    "Closed_Fist": "Kepalan Tangan (Fist)",
    "Open_Palm": "Telapak Terbuka (Open Palm)",
    "Pointing_Up": "Telunjuk Menunjuk (Pointer)",
    "Thumb_Down": "Jempol ke Bawah (Dislike)",
    "Thumb_Up": "Jempol ke Atas (Like)",
    "Victory": "Dua Jari / Peace (Victory)",
    "ILoveYou": "Tiga Jari (I Love You)",
    "Pinch": "Cubit / Klik (Pinch Air Click)",
}


class HandTrackerEngine:
    """MediaPipe-backed 21-point 3D hand tracking and gesture recognition engine."""

    _instance: Optional[HandTrackerEngine] = None

    def __init__(self, model_path: Optional[str] = None):
        self._recognizer = None
        self._initialized = False
        self._model_path = model_path or self._default_model_path()
        self._init_mediapipe()

    @classmethod
    def get_instance(cls, model_path: Optional[str] = None) -> HandTrackerEngine:
        if cls._instance is None:
            cls._instance = HandTrackerEngine(model_path)
        return cls._instance

    def _default_model_path(self) -> str:
        base_dir = Path(__file__).resolve().parent.parent / "data" / "models"
        base_dir.mkdir(parents=True, exist_ok=True)
        return str(base_dir / "gesture_recognizer.task")

    def _init_mediapipe(self) -> None:
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            task_file = Path(self._model_path)
            if not task_file.exists():
                logger.warning(f"Hand gesture model file not found: {self._model_path}")
                return

            base_options = python.BaseOptions(model_asset_path=str(task_file))
            options = vision.GestureRecognizerOptions(
                base_options=base_options,
                num_hands=2,
                min_hand_detection_confidence=0.45,
                min_hand_presence_confidence=0.45,
                min_tracking_confidence=0.45,
            )
            self._recognizer = vision.GestureRecognizer.create_from_options(options)
            self._initialized = True
            logger.info("MediaPipe GestureRecognizer successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe GestureRecognizer: {e}")
            self._recognizer = None
            self._initialized = False

    def is_ready(self) -> bool:
        return self._initialized and self._recognizer is not None

    def process_frame(
        self,
        frame: np.ndarray,
        node_config: Optional[dict] = None,
        node_id: str = "hand_skeleton",
    ) -> List[dict]:
        """Process a frame and return standardized detection dictionaries with 21 keypoints."""
        if frame is None or not hasattr(frame, "shape") or not self.is_ready():
            return []

        cfg = node_config or {}
        detect_pinch = bool(cfg.get("detectPinch", True))
        pinch_thresh = float(cfg.get("pinchThreshold", 32.0) or 32.0)
        conf_thresh = float(cfg.get("threshold", 0.45) or 0.45)

        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        import mediapipe as mp
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        try:
            result = self._recognizer.recognize(mp_image)
        except Exception as exc:
            logger.warning(f"Hand recognition failed: {exc}")
            return []

        if not result or not result.hand_landmarks:
            return []

        detections: List[dict] = []

        for idx, landmarks in enumerate(result.hand_landmarks):
            # Extract 21 landmark coordinates in pixel space
            pts_px: List[Tuple[float, float, float]] = []
            xs: List[float] = []
            ys: List[float] = []

            for lm in landmarks:
                px = float(lm.x * w)
                py = float(lm.y * h)
                pz = float(getattr(lm, "z", 0.0))
                pts_px.append((px, py, 1.0))
                xs.append(px)
                ys.append(py)

            if not xs or not ys:
                continue

            # Bounding box with 15% headroom padding
            pad_x = (max(xs) - min(xs)) * 0.15
            pad_y = (max(ys) - min(ys)) * 0.15
            x_min = max(0.0, min(xs) - pad_x)
            y_min = max(0.0, min(ys) - pad_y)
            x_max = min(float(w), max(xs) + pad_x)
            y_max = min(float(h), max(ys) + pad_y)
            box_w = x_max - x_min
            box_h = y_max - y_min

            # Handedness (Left vs Right)
            handedness = "Hand"
            if result.handedness and idx < len(result.handedness):
                categories = result.handedness[idx]
                if categories:
                    handedness = categories[0].category_name  # "Left" or "Right"

            # Primary Gesture from MediaPipe model
            gesture_name = "None"
            score = 0.85
            if result.gestures and idx < len(result.gestures):
                gest_cats = result.gestures[idx]
                if gest_cats:
                    gesture_name = gest_cats[0].category_name
                    score = float(gest_cats[0].score)

            if score < conf_thresh and gesture_name != "None":
                gesture_name = "None"

            # Pinch Detection (Distance between thumb tip 4 and index tip 8)
            thumb_tip = pts_px[4]
            index_tip = pts_px[8]
            pinch_dist = math.hypot(thumb_tip[0] - index_tip[0], thumb_tip[1] - index_tip[1])
            is_pinch = detect_pinch and (pinch_dist <= pinch_thresh)

            if is_pinch:
                gesture_name = "Pinch"

            # Count Extended Fingers
            extended_count = self._count_extended_fingers(pts_px, handedness)

            # Indonesian translated label
            display_gesture = GESTURE_TRANSLATIONS.get(gesture_name, gesture_name)

            det_item = {
                "x": float(x_min),
                "y": float(y_min),
                "width": float(box_w),
                "height": float(box_h),
                "bbox": [float(x_min), float(y_min), float(box_w), float(box_h)],
                "class": gesture_name,
                "label": f"{handedness} ({display_gesture})",
                "score": float(score),
                "sourceNodeId": node_id,
                "hand": handedness,
                "gesture": gesture_name,
                "gestureLabel": display_gesture,
                "isPinch": is_pinch,
                "pinchDistance": round(pinch_dist, 1),
                "fingerCount": extended_count,
                "indexTip": [float(index_tip[0]), float(index_tip[1])],
                "thumbTip": [float(thumb_tip[0]), float(thumb_tip[1])],
                "keypoints": pts_px,
            }
            detections.append(det_item)

        return detections

    def _count_extended_fingers(self, pts: List[Tuple[float, float, float]], handedness: str) -> int:
        """Calculate how many fingers are extended using geometric heuristics."""
        count = 0
        # 1. Thumb (Tip 4 vs IP 3 or MCP 2)
        # Check horizontal extension relative to wrist and palm
        if handedness == "Right":
            if pts[4][0] < pts[3][0]:  # Extends outward to the left
                count += 1
        else:
            if pts[4][0] > pts[3][0]:  # Extends outward to the right
                count += 1

        # 2. Four Fingers (Index 8, Middle 12, Ring 16, Pinky 20 vs their PIP joints 6, 10, 14, 18)
        # When hand is upright, tip y is smaller than PIP y
        finger_tips_pips = [(8, 6), (12, 10), (16, 14), (20, 18)]
        for tip_idx, pip_idx in finger_tips_pips:
            if pts[tip_idx][1] < pts[pip_idx][1]:
                count += 1

        return count


def draw_hand_skeleton(
    frame: np.ndarray,
    hand_detections: List[dict],
    config: Optional[dict] = None,
) -> None:
    """Draw vibrant 21-point hand skeleton bones, glowing joints, and status badges."""
    if frame is None or not hasattr(frame, "shape") or not hand_detections:
        return

    cfg = config or {}
    show_bones = cfg.get("showSkeleton", True) is not False
    show_joints = cfg.get("showJoints", True) is not False
    show_badge = cfg.get("showGestureBadge", True) is not False
    thickness = max(1, min(6, int(cfg.get("skeletonThickness", 2) or 2)))
    radius = max(2, min(10, int(cfg.get("jointRadius", 4) or 4)))

    fh, fw = frame.shape[:2]

    for det in hand_detections:
        kpts = det.get("keypoints", [])
        if len(kpts) < 21:
            continue

        # 1. Draw Skeleton Bones
        if show_bones:
            for idx1, idx2, color in HAND_CONNECTIONS_WITH_COLORS:
                p1, p2 = kpts[idx1], kpts[idx2]
                x1, y1 = int(round(p1[0])), int(round(p1[1]))
                x2, y2 = int(round(p2[0])), int(round(p2[1]))
                if 0 <= x1 < fw and 0 <= y1 < fh and 0 <= x2 < fw and 0 <= y2 < fh:
                    cv2.line(frame, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)

        # 2. Draw Glowing Joint Dots
        if show_joints:
            for idx in range(min(21, len(kpts))):
                pt = kpts[idx]
                x, y = int(round(pt[0])), int(round(pt[1]))
                if 0 <= x < fw and 0 <= y < fh:
                    color = FINGER_JOINT_COLORS.get(idx, (0, 255, 255))
                    # Outer halo ring
                    cv2.circle(frame, (x, y), radius + 2, (0, 0, 0), 1, cv2.LINE_AA)
                    # Colored joint circle
                    cv2.circle(frame, (x, y), radius, color, -1, cv2.LINE_AA)
                    # Bright white center dot
                    cv2.circle(frame, (x, y), max(1, radius // 2), (255, 255, 255), -1, cv2.LINE_AA)

        # Highlight Pinch Point if active
        if det.get("isPinch"):
            idx_pt = det.get("indexTip")
            if idx_pt:
                ix, iy = int(round(idx_pt[0])), int(round(idx_pt[1]))
                cv2.circle(frame, (ix, iy), radius + 6, (0, 255, 255), 2, cv2.LINE_AA)
                cv2.circle(frame, (ix, iy), radius + 10, (0, 140, 255), 1, cv2.LINE_AA)

        # 3. Draw Gesture Status Badge above hand
        if show_badge:
            bbox = det.get("bbox", [0, 0, 0, 0])
            bx, by = int(round(bbox[0])), int(round(bbox[1]))
            badge_text = f"{det.get('hand', 'Tangan')} · {det.get('gestureLabel', 'Hand')}"
            if det.get("isPinch"):
                badge_text += " [PINCH!]"
            elif det.get("fingerCount", 0) > 0:
                badge_text += f" ({det.get('fingerCount')} Jari)"

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.44
            (tw, th), baseline = cv2.getTextSize(badge_text, font, font_scale, 1)

            rx = max(6, min(bx, fw - tw - 16))
            ry = max(th + 14, by - 10)

            # Badge pill background
            bg_color = (0, 180, 255) if det.get("isPinch") else (15, 23, 42)
            border_color = (0, 220, 255) if det.get("isPinch") else (56, 189, 248)
            cv2.rectangle(frame, (rx - 4, ry - th - 6), (rx + tw + 8, ry + 4), bg_color, -1)
            cv2.rectangle(frame, (rx - 4, ry - th - 6), (rx + tw + 8, ry + 4), border_color, 1)
            text_color = (0, 0, 0) if det.get("isPinch") else (255, 255, 255)
            cv2.putText(frame, badge_text, (rx + 2, ry - 2), font, font_scale, text_color, 1, cv2.LINE_AA)
