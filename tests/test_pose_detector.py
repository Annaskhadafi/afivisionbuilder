import math
import numpy as np
import pytest

from engine.pose_engine import (
    COCO_KEYPOINT_NAMES,
    SKELETON_LIMBS,
    classify_human_posture,
    draw_human_skeleton,
)
from engine.node_catalog import NODE_BLUEPRINTS


def test_catalog_contains_pose_detector():
    assert "pose_detector" in NODE_BLUEPRINTS
    spec = NODE_BLUEPRINTS["pose_detector"]
    assert spec["title"] == "Human Pose Estimator"
    assert spec["category"] == "AI Vision Models"
    assert spec["config"]["modelPath"] == "yolov8n-pose.pt"
    assert spec["config"]["showSkeleton"] is True
    assert spec["config"]["showJoints"] is True


def test_posture_classification():
    # 1. Standing posture: vertical spine, hips above knees, knees above ankles
    standing_kpts = [[0.0, 0.0, 0.0] for _ in range(17)]
    standing_kpts[0] = [200.0, 60.0, 0.95]   # Nose
    standing_kpts[5] = [180.0, 100.0, 0.90]  # L Shoulder
    standing_kpts[6] = [220.0, 100.0, 0.90]  # R Shoulder
    standing_kpts[11] = [185.0, 200.0, 0.88] # L Hip
    standing_kpts[12] = [215.0, 200.0, 0.88] # R Hip
    standing_kpts[13] = [185.0, 320.0, 0.85] # L Knee
    standing_kpts[14] = [215.0, 320.0, 0.85] # R Knee
    standing_kpts[15] = [185.0, 450.0, 0.80] # L Ankle
    standing_kpts[16] = [215.0, 450.0, 0.80] # R Ankle

    pkey, plabel, pconf = classify_human_posture(standing_kpts)
    assert pkey == "standing"
    assert plabel == "Berdiri"
    assert pconf >= 0.80

    # 2. Sitting posture: thigh is horizontal (hip Y is close to knee Y)
    sitting_kpts = [list(pt) for pt in standing_kpts]
    sitting_kpts[13] = [250.0, 215.0, 0.88] # L Knee at same height as hip
    sitting_kpts[14] = [280.0, 215.0, 0.88] # R Knee at same height as hip
    sitting_kpts[15] = [250.0, 310.0, 0.85] # L Ankle
    sitting_kpts[16] = [280.0, 310.0, 0.85] # R Ankle

    skey, slabel, sconf = classify_human_posture(sitting_kpts)
    assert skey == "sitting"
    assert slabel == "Duduk"

    # 3. Lying down / Fallen: horizontal torso (dx > dy)
    lying_kpts = [[0.0, 0.0, 0.0] for _ in range(17)]
    lying_kpts[5] = [100.0, 300.0, 0.9]  # Shoulder
    lying_kpts[6] = [100.0, 320.0, 0.9]
    lying_kpts[11] = [250.0, 305.0, 0.9] # Hip (far horizontal offset)
    lying_kpts[12] = [250.0, 325.0, 0.9]

    lkey, llabel, lconf = classify_human_posture(lying_kpts)
    assert lkey == "lying_down"
    assert "Jatuh" in llabel or "Terlentang" in llabel


def test_skeleton_drawing():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    kpts = [[100.0 + i * 15.0, 100.0 + i * 18.0, 0.85] for i in range(17)]

    # Draw skeleton
    draw_human_skeleton(
        frame,
        kpts,
        {"showSkeleton": True, "showJoints": True, "showPostureBadge": True, "skeletonThickness": 2, "jointRadius": 4},
        posture_label="Berdiri",
    )

    # Frame should have colored lines and circles (not completely black)
    assert np.any(frame > 0)


def test_pose_model_inference():
    from engine.custom_model_runtime import CustomModelRunner

    node = {
        "id": "pose_node_test",
        "type": "pose_detector",
        "config": {
            "engine": "ultralytics_yolo",
            "modelPath": "yolov8n-pose.pt",
            "threshold": 0.25,
            "showSkeleton": True,
            "showJoints": True,
        },
    }
    frame = np.zeros((640, 640, 3), dtype=np.uint8)
    detections = CustomModelRunner.run_frame(frame, node)
    assert isinstance(detections, list)
