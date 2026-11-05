import numpy as np
import pytest
from engine.main import draw_detections
from engine.core import _default_inference_engine_for_node


def test_draw_detections_renders_human_pose_skeleton():
    """Verify that draw_detections draws 17-point pose skeleton onto the display frame."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # 17 COCO keypoints (x, y, conf) representing a standing human figure
    keypoints = [
        [320.0, 100.0, 0.95],  # nose
        [315.0, 95.0, 0.9],   # left eye
        [325.0, 95.0, 0.9],   # right eye
        [310.0, 100.0, 0.9],  # left ear
        [330.0, 100.0, 0.9],  # right ear
        [290.0, 150.0, 0.95], # left shoulder
        [350.0, 150.0, 0.95], # right shoulder
        [270.0, 220.0, 0.9],  # left elbow
        [370.0, 220.0, 0.9],  # right elbow
        [260.0, 290.0, 0.9],  # left wrist
        [380.0, 290.0, 0.9],  # right wrist
        [300.0, 280.0, 0.95], # left hip
        [340.0, 280.0, 0.95], # right hip
        [295.0, 360.0, 0.9],  # left knee
        [345.0, 360.0, 0.9],  # right knee
        [290.0, 440.0, 0.9],  # left ankle
        [350.0, 440.0, 0.9],  # right ankle
    ]

    pose_detection = {
        "x": 250.0,
        "y": 80.0,
        "width": 140.0,
        "height": 370.0,
        "class": "person",
        "score": 0.92,
        "keypoints": keypoints,
        "posture": "standing",
        "posture_label": "Berdiri",
        "showSkeleton": True,
        "showJoints": True,
        "showPostureBadge": True,
    }

    preview_cfg = {
        "config": {
            "showBoxes": True,
            "showLabels": True,
        }
    }

    # Frame before rendering is all zeros
    assert np.all(frame == 0)

    draw_detections(frame, [pose_detection], preview_cfg)

    # After rendering, pixels for skeleton bones and joints MUST be drawn (non-zero)
    assert np.any(frame > 0), "Skeleton lines and joints should be drawn onto the frame"

    # Specific bone check: right between left shoulder (290, 150) and right shoulder (350, 150)
    # The torso line y=150 between x=300 and 340 should have painted pixels
    mid_shoulder_pixels = frame[150, 300:340]
    assert np.any(mid_shoulder_pixels > 0), "Shoulder connecting bone should be visible"


def test_draw_detections_renders_hand_skeleton():
    """Verify that draw_detections draws 21-point hand skeleton onto the display frame."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # 21 hand landmarks simulating an open hand
    hand_keypoints = []
    for i in range(21):
        hand_keypoints.append([200.0 + (i % 5) * 20.0, 150.0 + (i // 5) * 40.0, 0.0])

    hand_detection = {
        "x": 190.0,
        "y": 140.0,
        "width": 100.0,
        "height": 180.0,
        "class": "Open_Palm",
        "label": "Right (Telapak Terbuka)",
        "score": 0.88,
        "hand": "Right",
        "gesture": "Open_Palm",
        "gestureLabel": "Telapak Terbuka",
        "keypoints": hand_keypoints,
        "showSkeleton": True,
        "showJoints": True,
        "showGestureBadge": True,
    }

    preview_cfg = {
        "config": {
            "showBoxes": True,
            "showLabels": True,
        }
    }

    assert np.all(frame == 0)
    draw_detections(frame, [hand_detection], preview_cfg)
    assert np.any(frame > 0), "Hand skeleton bones and joint dots should be drawn onto frame"


def test_default_inference_engine_fallback():
    """Verify that pose_detector node defaults to ultralytics_yolo and not rfdetr."""
    pose_node = {"id": "pose_1", "type": "pose_detector", "config": {}}
    eng = _default_inference_engine_for_node(pose_node)
    assert eng == "ultralytics_yolo", f"Expected 'ultralytics_yolo', got '{eng}'"

    eff_node = {"id": "eff_1", "type": "efficientad", "config": {}}
    eng_eff = _default_inference_engine_for_node(eff_node)
    assert eng_eff == "efficientad", f"Expected 'efficientad', got '{eng_eff}'"

    det_node = {"id": "det_1", "type": "detector", "config": {}}
    eng_det = _default_inference_engine_for_node(det_node)
    assert eng_det == "rfdetr", f"Expected 'rfdetr', got '{eng_det}'"
