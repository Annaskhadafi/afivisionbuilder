"""Afi Vision Builder - Human Pose Estimator & Skeleton Visualization Engine.

Provides:
- 17 COCO Keypoints & 19 Anatomical Skeleton Connections
- Multi-Color Anatomical Bones & Glowing Joint Dots rendering
- Heuristic Human Posture Estimation (Standing, Sitting, Bending, Lying/Fallen)
"""

from __future__ import annotations

import math
from typing import Any
import cv2
import numpy as np

# 17 COCO Keypoints Names
COCO_KEYPOINT_NAMES = [
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]

# Anatomical Limb Groups with Distinct Colors (BGR format)
# (pt1_idx, pt2_idx, color_bgr)
FACE_LIMBS = [
    # Head / Face (Golden Yellow: 0, 215, 255)
    (0, 1, (0, 220, 255)),
    (0, 2, (0, 220, 255)),
    (1, 3, (0, 200, 240)),
    (2, 4, (0, 200, 240)),
]

BODY_LIMBS = [
    # Torso / Spine (Neon Green: 0, 255, 128)
    (5, 6, (0, 255, 140)),
    (5, 11, (0, 240, 120)),
    (6, 12, (0, 240, 120)),
    (11, 12, (0, 255, 140)),
    # Left Arm (Electric Cyan: 255, 220, 0)
    (5, 7, (255, 220, 0)),
    (7, 9, (255, 240, 60)),
    # Right Arm (Vibrant Magenta: 220, 0, 255)
    (6, 8, (220, 0, 255)),
    (8, 10, (240, 60, 255)),
    # Left Leg (Tangerine Orange: 0, 140, 255)
    (11, 13, (0, 140, 255)),
    (13, 15, (0, 170, 255)),
    # Right Leg (Coral Red: 80, 80, 255)
    (12, 14, (70, 70, 255)),
    (14, 16, (90, 90, 255)),
]

# Default skeleton limbs (body only by default; face features use clean dots without crossing lines)
SKELETON_LIMBS = BODY_LIMBS

# Joint colors (BGR) for keypoint dots
JOINT_COLORS = {
    0: (0, 255, 255),    # Nose: Yellow
    1: (0, 230, 255),    # L Eye: Yellow
    2: (0, 230, 255),    # R Eye: Yellow
    3: (0, 200, 255),    # L Ear: Yellow
    4: (0, 200, 255),    # R Ear: Yellow
    5: (255, 220, 0),    # L Shoulder: Cyan
    6: (220, 0, 255),    # R Shoulder: Magenta
    7: (255, 200, 0),    # L Elbow: Cyan
    8: (200, 0, 255),    # R Elbow: Magenta
    9: (255, 240, 80),   # L Wrist: Bright Cyan
    10: (240, 80, 255),  # R Wrist: Bright Magenta
    11: (0, 160, 255),   # L Hip: Orange
    12: (70, 70, 255),   # R Hip: Coral
    13: (0, 180, 255),   # L Knee: Orange
    14: (90, 90, 255),   # R Knee: Coral
    15: (0, 210, 255),   # L Ankle: Light Orange
    16: (120, 120, 255), # R Ankle: Light Coral
}


def classify_human_posture(keypoints: list[list[float]] | np.ndarray) -> tuple[str, str, float]:
    """Classify posture based on 17 COCO keypoints geometry.

    Returns:
        (posture_key, posture_label, confidence)
        posture_key: "standing" | "sitting" | "bending" | "lying_down"
        posture_label: "Berdiri" | "Duduk" | "Membungkuk" | "Terlentang / Jatuh"
    """
    if keypoints is None or len(keypoints) < 17:
        return "unknown", "Tidak Diketahui", 0.0

    kpts = np.array(keypoints, dtype=np.float32)
    # Extract key anatomical points [x, y, conf]
    # 5: L Shoulder, 6: R Shoulder
    # 11: L Hip, 12: R Hip
    # 13: L Knee, 14: R Knee
    # 15: L Ankle, 16: R Ankle

    def get_pt(idx: int) -> tuple[float, float, float]:
        if idx < len(kpts):
            p = kpts[idx]
            conf = float(p[2]) if len(p) > 2 else 1.0
            return float(p[0]), float(p[1]), conf
        return 0.0, 0.0, 0.0

    ls_x, ls_y, ls_c = get_pt(5)
    rs_x, rs_y, rs_c = get_pt(6)
    lh_x, lh_y, lh_c = get_pt(11)
    rh_x, rh_y, rh_c = get_pt(12)
    lk_x, lk_y, lk_c = get_pt(13)
    rk_x, rk_y, rk_c = get_pt(14)
    la_x, la_y, la_c = get_pt(15)
    ra_x, ra_y, ra_c = get_pt(16)

    min_c = 0.25
    has_shoulders = (ls_c > min_c or rs_c > min_c)
    has_hips = (lh_c > min_c or rh_c > min_c)

    if not (has_shoulders and has_hips):
        return "standing", "Berdiri", 0.50

    # Midpoints
    mid_shoulder_y = (ls_y + rs_y) / 2.0 if (ls_c > min_c and rs_c > min_c) else (ls_y if ls_c > min_c else rs_y)
    mid_shoulder_x = (ls_x + rs_x) / 2.0 if (ls_c > min_c and rs_c > min_c) else (ls_x if ls_c > min_c else rs_x)

    mid_hip_y = (lh_y + rh_y) / 2.0 if (lh_c > min_c and rh_c > min_c) else (lh_y if lh_c > min_c else rh_y)
    mid_hip_x = (lh_x + rh_x) / 2.0 if (lh_c > min_c and rh_c > min_c) else (lh_x if lh_c > min_c else rh_x)

    torso_dy = abs(mid_hip_y - mid_shoulder_y)
    torso_dx = abs(mid_hip_x - mid_shoulder_x)

    # 1. Check Lying Down / Fallen: Torso is horizontal (dx > dy * 1.3)
    if torso_dx > (torso_dy * 1.3) and torso_dy < 80:
        return "lying_down", "Terlentang / Jatuh", 0.90

    # Knee & Ankle checks
    has_knees = (lk_c > min_c or rk_c > min_c)
    if has_knees:
        mid_knee_y = (lk_y + rk_y) / 2.0 if (lk_c > min_c and rk_c > min_c) else (lk_y if lk_c > min_c else rk_y)
        thigh_dy = abs(mid_knee_y - mid_hip_y)

        # Torso angle from vertical
        torso_angle = math.degrees(math.atan2(torso_dx, max(1.0, torso_dy)))

        # 2. Check Sitting:
        # a) Thigh is relatively horizontal from CCTV angle (hip y close to knee y) while torso is upright
        is_sitting_thigh = (thigh_dy < (torso_dy * 0.65) and torso_dy > 25 and torso_angle < 35.0)

        # b) Check Knee Bending Angle when hip, knee, and ankle are all visible
        has_ankles = (la_c > min_c or ra_c > min_c)
        is_sitting_knee_angle = False
        if has_ankles:
            # Measure knee angle on the side with best confidence
            left_valid = (lh_c > min_c and lk_c > min_c and la_c > min_c)
            right_valid = (rh_c > min_c and rk_c > min_c and ra_c > min_c)
            if left_valid or right_valid:
                h_pt = (lh_x, lh_y) if left_valid else (rh_x, rh_y)
                k_pt = (lk_x, lk_y) if left_valid else (rk_x, rk_y)
                a_pt = (la_x, la_y) if left_valid else (ra_x, ra_y)

                v1 = (h_pt[0] - k_pt[0], h_pt[1] - k_pt[1])
                v2 = (a_pt[0] - k_pt[0], a_pt[1] - k_pt[1])
                mag1 = math.hypot(*v1)
                mag2 = math.hypot(*v2)
                if mag1 > 8 and mag2 > 8:
                    cos_k = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (mag1 * mag2)))
                    knee_deg = math.degrees(math.acos(cos_k))
                    # Standing knee is ~160-180 deg; sitting knee is typically 60-135 deg
                    if knee_deg < 135.0 and torso_angle < 35.0:
                        is_sitting_knee_angle = True

        if is_sitting_thigh or is_sitting_knee_angle:
            return "sitting", "Duduk", 0.88

        # 3. Check Bending: Torso bent forward (torso angle with vertical > 40 deg)
        if torso_angle > 40.0:
            return "bending", "Membungkuk", 0.85

        # Check Ankle distance to knee for full standing check
        if has_ankles:
            mid_ankle_y = (la_y + ra_y) / 2.0 if (la_c > min_c and ra_c > min_c) else (la_y if la_c > min_c else ra_y)
            shin_dy = abs(mid_ankle_y - mid_knee_y)
            # Standing when legs are vertical and extended
            if thigh_dy > 25 and shin_dy > 25:
                return "standing", "Berdiri", 0.92

    # Default to standing with moderate confidence
    return "standing", "Berdiri", 0.82


def draw_human_skeleton(
    frame: np.ndarray,
    keypoints: list[list[float]] | np.ndarray,
    config: dict[str, Any] | None = None,
    posture_label: str = "",
) -> None:
    """Draw anatomical skeleton bones and glowing joint dots onto frame in-place."""
    if frame is None or keypoints is None or len(keypoints) < 17:
        return

    cfg = config or {}
    show_bones = cfg.get("showSkeleton", True) is not False
    show_joints = cfg.get("showJoints", True) is not False
    show_face_lines = bool(cfg.get("showFaceLines", False))
    show_posture = cfg.get("showPostureBadge", True) is not False
    kpt_thresh = float(cfg.get("keypointThreshold", 0.35) or 0.35)
    thickness = max(1, min(6, int(cfg.get("skeletonThickness", 2) or 2)))
    radius = max(2, min(10, int(cfg.get("jointRadius", 4) or 4)))

    kpts = np.array(keypoints, dtype=np.float32)
    fh, fw = frame.shape[:2]

    # 1. Draw Skeleton Bones (connecting lines)
    # By default, face lines are omitted so facial identity, eyes, and expressions stay clearly visible.
    if show_bones:
        draw_limbs = (BODY_LIMBS + FACE_LIMBS) if show_face_lines else BODY_LIMBS
        for idx1, idx2, color in draw_limbs:
            if idx1 >= len(kpts) or idx2 >= len(kpts):
                continue
            p1, p2 = kpts[idx1], kpts[idx2]
            c1 = float(p1[2]) if len(p1) > 2 else 1.0
            c2 = float(p2[2]) if len(p2) > 2 else 1.0

            if c1 >= kpt_thresh and c2 >= kpt_thresh:
                x1, y1 = int(round(p1[0])), int(round(p1[1]))
                x2, y2 = int(round(p2[0])), int(round(p2[1]))
                if 0 <= x1 < fw and 0 <= y1 < fh and 0 <= x2 < fw and 0 <= y2 < fh:
                    cv2.line(frame, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)

        # Draw neck connecting line only when show_face_lines is explicitly requested
        if show_face_lines and len(kpts) > 6:
            p_nose = kpts[0]
            p_ls, p_rs = kpts[5], kpts[6]
            if float(p_nose[2]) >= kpt_thresh and float(p_ls[2]) >= kpt_thresh and float(p_rs[2]) >= kpt_thresh:
                mid_sx = int(round((p_ls[0] + p_rs[0]) / 2.0))
                mid_sy = int(round((p_ls[1] + p_rs[1]) / 2.0))
                nx, ny = int(round(p_nose[0])), int(round(p_nose[1]))
                cv2.line(frame, (mid_sx, mid_sy), (nx, ny), (0, 255, 140), max(1, thickness - 1), cv2.LINE_AA)

    # 2. Draw Glowing Joint Dots (face features use clean subtle dots without crossing lines)
    if show_joints:
        for i in range(min(17, len(kpts))):
            p = kpts[i]
            conf = float(p[2]) if len(p) > 2 else 1.0
            if conf >= kpt_thresh:
                x, y = int(round(p[0])), int(round(p[1]))
                if 0 <= x < fw and 0 <= y < fh:
                    joint_color = JOINT_COLORS.get(i, (0, 255, 255))
                    is_face = i < 5
                    cur_radius = max(2, radius - 1) if is_face else radius
                    # Outer halo ring for body joints
                    if not is_face:
                        cv2.circle(frame, (x, y), cur_radius + 2, (0, 0, 0), 1, cv2.LINE_AA)
                    # Colored circle
                    cv2.circle(frame, (x, y), cur_radius, joint_color, -1, cv2.LINE_AA)
                    # Inner bright white center dot
                    cv2.circle(frame, (x, y), max(1, cur_radius // 2), (255, 255, 255), -1, cv2.LINE_AA)

    # 3. Draw Posture State Badge (near neck or head)
    if show_posture and posture_label:
        # Place label near nose or mid-shoulder
        badge_x, badge_y = 0, 0
        p_nose = kpts[0]
        if float(p_nose[2]) >= kpt_thresh:
            badge_x, badge_y = int(p_nose[0]), int(p_nose[1]) - 16
        elif len(kpts) > 5 and float(kpts[5][2]) >= kpt_thresh:
            badge_x, badge_y = int(kpts[5][0]), int(kpts[5][1]) - 16
        else:
            # First visible keypoint
            for p in kpts:
                if float(p[2]) >= kpt_thresh:
                    badge_x, badge_y = int(p[0]), int(p[1]) - 16
                    break

        if badge_x > 0 and badge_y > 0:
            badge_text = posture_label.upper()
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.40
            font_thick = 1
            (tw, th), _ = cv2.getTextSize(badge_text, font, font_scale, font_thick)
            dot_radius = 3
            dot_spacing = 10  # space for dot indicator + gap
            total_content_w = tw + dot_spacing
            bx1 = max(4, badge_x - (total_content_w // 2) - 6)
            by1 = max(4, badge_y - th - 6)
            bx2 = min(fw - 4, bx1 + total_content_w + 12)
            by2 = min(fh - 4, by1 + th + 6)

            # Badge dark translucent background
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), (15, 23, 42), -1)

            # Posture accent border & indicator dot
            posture_color = (0, 255, 128) if "BERDIRI" in badge_text else (0, 200, 255) if "DUDUK" in badge_text else (0, 80, 255)
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), posture_color, 1)

            # Draw glowing status dot with cv2.circle (avoids Hershey font Unicode '???' glyph bug)
            dot_cx = bx1 + 6 + dot_radius
            dot_cy = by1 + ((by2 - by1) // 2)
            cv2.circle(frame, (dot_cx, dot_cy), dot_radius, posture_color, -1, cv2.LINE_AA)

            # Render ASCII text cleanly
            cv2.putText(frame, badge_text, (dot_cx + dot_radius + 4, by1 + th + 2), font, font_scale, (255, 255, 255), font_thick, cv2.LINE_AA)
