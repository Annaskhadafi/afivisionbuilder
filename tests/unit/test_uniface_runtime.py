# tests/unit/test_uniface_runtime.py
import os
import shutil
import tempfile
import time
import numpy as np
import pytest
from engine.uniface_runtime import (
    UniFaceRegistry,
    UniFaceManager,
    process_face_detector_node,
    process_face_tracker_node,
    draw_face_landmarks_overlay
)

@pytest.fixture
def temp_face_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_uniface_registry_crud(temp_face_dir):
    registry = UniFaceRegistry(storage_dir=temp_face_dir)
    assert len(registry.list_faces()) == 0

    # 1. Enroll face with 512-D embedding
    dummy_vec = np.random.randn(512).astype(np.float32)
    dummy_vec = (dummy_vec / np.linalg.norm(dummy_vec)).tolist()

    face = registry.enroll_face(
        name="Anas Supervisor",
        embedding=dummy_vec,
        role="Supervisor",
        notes="Shift A Workshop"
    )
    assert face is not None
    assert face["name"] == "Anas Supervisor"
    assert face["role"] == "Supervisor"
    assert len(registry.list_faces()) == 1

    # 2. Match face with high similarity
    matched, score = registry.match_face(np.array(dummy_vec), threshold=0.6)
    assert matched is not None
    assert matched["name"] == "Anas Supervisor"
    assert score > 0.99

    # 3. Match face with orthogonal/different vector
    diff_vec = (-np.array(dummy_vec))
    no_match, diff_score = registry.match_face(diff_vec, threshold=0.6)
    assert no_match is None

    # 4. Delete face
    deleted = registry.delete_face(face["id"])
    assert deleted is True
    assert len(registry.list_faces()) == 0

def test_face_detector_and_tracker_pipeline_flow(temp_face_dir):
    registry = UniFaceRegistry(storage_dir=temp_face_dir)
    # Enroll test profile
    vec1 = [0.1] * 512
    vec1_norm = (np.array(vec1) / np.linalg.norm(vec1)).tolist()
    registry.enroll_face(name="Budi Teknik", embedding=vec1_norm, role="Mekanik")

    # Mock manager to return predictable face detection and embedding
    class MockFace:
        def __init__(self, bbox, landmarks, confidence):
            self.bbox = bbox
            self.landmarks = landmarks
            self.confidence = confidence

    class MockDetector:
        def detect(self, img):
            # return 1 face at [10, 10, 80, 80]
            return [
                MockFace(
                    bbox=[10, 10, 80, 80],
                    landmarks=[[20, 25], [50, 25], [35, 45], [25, 60], [45, 60]],
                    confidence=0.95
                )
            ]

    class MockRecognizer:
        def get_embedding(self, img, landmarks=None):
            return np.array(vec1_norm, dtype=np.float32)

    manager = UniFaceManager()
    manager._detector = MockDetector()
    manager._recognizer = MockRecognizer()

    # Monkeypatch singleton registry & manager
    orig_registry = UniFaceRegistry._instance
    orig_manager = UniFaceManager._instance
    UniFaceRegistry._instance = registry
    UniFaceManager._instance = manager

    try:
        # Test process_face_detector_node
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        node_det = {
            "id": "det_face_1",
            "type": "face_detector",
            "config": {"confidence": 0.5, "drawLandmarks": True, "drawFaceBox": True}
        }
        detections = process_face_detector_node(node_det, dummy_img)

        assert len(detections) == 1
        face_item = detections[0]
        assert face_item["class"] == "face"
        assert len(face_item["landmarks"]) == 5

        # Test process_face_tracker_node with the detected face
        node_track = {
            "id": "track_face_1",
            "type": "face_tracker",
            "config": {"similarityThreshold": 0.5, "showNameBadge": True}
        }
        tracker_state = {}
        now = time.time()
        tracked_dets, events = process_face_tracker_node(node_track, dummy_img, detections, tracker_state, now)

        assert len(tracked_dets) == 1
        tracked = tracked_dets[0]
        assert tracked["personName"] == "Budi Teknik"
        assert tracked["isEnrolled"] is True
        assert tracked["similarity"] > 0.9
        assert len(events) == 1
        assert events[0]["kind"] == "face_identified"

        # Test overlay rendering
        display_frame = dummy_img.copy()
        draw_face_landmarks_overlay(display_frame, tracked_dets)
        assert display_frame.shape == (480, 640, 3)
    finally:
        UniFaceRegistry._instance = orig_registry
        UniFaceManager._instance = orig_manager
