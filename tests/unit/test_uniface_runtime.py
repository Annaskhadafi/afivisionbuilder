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


def test_face_tracker_2d_embedding_alignment(temp_face_dir):
    """
    Verify ArcFace 2D embedding (shape (1, 512)) does NOT cause:
    'shapes (1,512) and (1,512) not aligned: 512 (dim 1) != 1 (dim 0)'.
    """
    registry = UniFaceRegistry(storage_dir=temp_face_dir)
    # 2D embedding shape (1, 512)
    vec_2d = np.random.randn(1, 512).astype(np.float32)
    vec_2d = vec_2d / np.linalg.norm(vec_2d)

    enrolled = registry.enroll_face(name="Citra Operator", embedding=vec_2d, role="Operator")
    assert enrolled is not None
    assert len(enrolled["embedding"]) == 512  # Must be flattened

    # Match with 2D query
    query_2d = vec_2d.copy()
    matched, score = registry.match_face(query_2d, threshold=0.5)
    assert matched is not None
    assert matched["name"] == "Citra Operator"
    assert score > 0.99

    # Mock recognizer that strictly returns 2D array (1, 512) as ArcFace ONNX does
    class Mock2DDetector:
        def detect(self, img):
            class FaceObj:
                bbox = [20, 20, 100, 100]
                landmarks = [[30, 30], [70, 30], [50, 50], [40, 70], [60, 70]]
                confidence = 0.96
            return [FaceObj()]

    class Mock2DRecognizer:
        def get_embedding(self, img, landmarks=None):
            return vec_2d.copy()

    mgr = UniFaceManager()
    mgr._detector = Mock2DDetector()
    mgr._recognizer = Mock2DRecognizer()

    orig_reg = UniFaceRegistry._instance
    orig_mgr = UniFaceManager._instance
    UniFaceRegistry._instance = registry
    UniFaceManager._instance = mgr

    try:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        node_det = {"id": "det_1", "type": "face_detector", "config": {}}
        dets = process_face_detector_node(node_det, frame)

        node_track = {"id": "track_1", "type": "face_tracker", "config": {}}
        state = {}

        # Frame 1: enrollment match & track initialization
        t0 = 1000.0
        out_dets_1, evts_1 = process_face_tracker_node(node_track, frame, dets, state, t0)
        assert len(out_dets_1) == 1
        assert out_dets_1[0]["personName"] == "Citra Operator"

        # Frame 2: rolling feature update and dynamic Re-ID comparison with 2D embedding
        t1 = t0 + 0.1
        dets_2 = process_face_detector_node(node_det, frame)
        out_dets_2, evts_2 = process_face_tracker_node(node_track, frame, dets_2, state, t1)
        assert len(out_dets_2) == 1
        assert out_dets_2[0]["personName"] == "Citra Operator"
    finally:
        UniFaceRegistry._instance = orig_reg
        UniFaceManager._instance = orig_mgr


def test_face_tracker_enrolled_promotion_and_iou(temp_face_dir):
    """Verify unknown track is cleanly promoted when recognized as enrolled face."""
    registry = UniFaceRegistry(storage_dir=temp_face_dir)
    vec1 = [0.2] * 512
    vec1_norm = (np.array(vec1) / np.linalg.norm(vec1)).tolist()
    registry.enroll_face(name="Annas Khadafi", embedding=vec1_norm, role="Karyawan")

    class MockDetector:
        def detect(self, img):
            return []

    class MockRecognizer:
        def __init__(self):
            self.return_vec = None
        def get_embedding(self, img, landmarks=None):
            return self.return_vec

    mgr = UniFaceManager()
    mgr._detector = MockDetector()
    recognizer = MockRecognizer()
    mgr._recognizer = recognizer

    orig_reg = UniFaceRegistry._instance
    orig_mgr = UniFaceManager._instance
    UniFaceRegistry._instance = registry
    UniFaceManager._instance = mgr

    try:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        node_track = {"id": "track_1", "type": "face_tracker", "config": {"similarityThreshold": 0.48, "unknownPrefix": "Tamu"}}
        state = {}

        # Frame 1: Face detected, but recognizer produces orthogonal vector (not in gallery) -> Classified as Tamu #1
        recognizer.return_vec = (-np.array(vec1_norm, dtype=np.float32))
        det_1 = [{
            "class": "face", "x": 100, "y": 100, "width": 80, "height": 80,
            "bbox": [100, 100, 80, 80], "confidence": 0.9,
            "landmarks": [[120, 120], [160, 120], [140, 140], [125, 160], [155, 160]]
        }]
        out_1, evts_1 = process_face_tracker_node(node_track, frame, det_1, state, 100.0)
        assert len(out_1) == 1
        assert out_1[0]["personName"] == "Tamu #1"
        assert out_1[0]["isEnrolled"] is False

        # Frame 2: Person faces camera clearly, embedding now matches Annas -> Seamlessly promoted to Annas Khadafi
        recognizer.return_vec = np.array(vec1_norm, dtype=np.float32)
        det_2 = [{
            "class": "face", "x": 102, "y": 101, "width": 80, "height": 80,
            "bbox": [102, 101, 80, 80], "confidence": 0.95,
            "landmarks": [[122, 121], [162, 121], [142, 141], [127, 161], [157, 161]]
        }]
        out_2, evts_2 = process_face_tracker_node(node_track, frame, det_2, state, 100.1)
        assert len(out_2) == 1
        assert out_2[0]["personName"] == "Annas Khadafi"
        assert out_2[0]["isEnrolled"] is True
        # Verify unknown:1 track was removed/promoted
        assert not any(k.startswith("unknown:") for k in state["tracks"].keys())
        assert any(k.startswith("enrolled:") for k in state["tracks"].keys())

        # Frame 3: Temporary slight head turn (recognizer returns None/weak), but spatial IoU preserves identity
        recognizer.return_vec = None
        det_3 = [{
            "class": "face", "x": 103, "y": 102, "width": 80, "height": 80,
            "bbox": [103, 102, 80, 80], "confidence": 0.9,
            "landmarks": []
        }]
        out_3, evts_3 = process_face_tracker_node(node_track, frame, det_3, state, 100.2)
        assert len(out_3) == 1
        assert out_3[0]["personName"] == "Annas Khadafi"
        assert out_3[0]["isEnrolled"] is True
    finally:
        UniFaceRegistry._instance = orig_reg
        UniFaceManager._instance = orig_mgr
