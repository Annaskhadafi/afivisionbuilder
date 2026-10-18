"""Unit tests for engine/vlm_box_tracker.py"""
import copy
import time
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2

from engine.vlm_box_tracker import (
    ConstantVelocityKalmanFilter,
    OpticalFlowTrack,
    FrameRecord,
    replay,
    VLMClient,
    VLMBoxTrackerRuntime,
    sanitize_vlm_config,
    resolve_api_key,
)


class TestVLMBoxTracker(unittest.TestCase):

    def test_kalman_filter_predict_and_update(self):
        kf = ConstantVelocityKalmanFilter((0.5, 0.5))
        self.assertAlmostEqual(kf.x[0], 0.5)
        self.assertAlmostEqual(kf.x[1], 0.5)

        # Predict forward 1 second with 0 initial velocity
        kf.predict(1.0)
        self.assertAlmostEqual(kf.x[0], 0.5)
        self.assertAlmostEqual(kf.x[1], 0.5)

        # Update with velocity (vx=0.1, vy=0.05)
        velocity = np.array([0.1, 0.05])
        kf.update(velocity, ConstantVelocityKalmanFilter.H_VELOCITY, 1e-3)
        self.assertGreater(kf.x[2], 0.05)

        # Next predict should move position
        kf.predict(1.0)
        self.assertGreater(kf.x[0], 0.5)

    def test_optical_flow_track_step_and_box(self):
        # Create a simple synthetic grayscale image with a white square
        gray1 = np.zeros((100, 100), dtype=np.uint8)
        gray1[40:60, 40:60] = 255
        # Add some texture corners inside the square
        gray1[45:55:2, 45:55:2] = 0

        track = OpticalFlowTrack(
            track_id=1,
            class_name="tire",
            centre=(0.5, 0.5),
            size=(0.2, 0.2),
            gray=gray1,
            confidence=0.9,
        )
        self.assertEqual(track.track_id, 1)
        self.assertEqual(track.class_name, "tire")

        # Second frame: shifted right by 5 pixels
        gray2 = np.zeros((100, 100), dtype=np.uint8)
        gray2[40:60, 45:65] = 255
        gray2[45:55:2, 50:60:2] = 0

        track.step(gray1, gray2, 0.1)
        box = track.box()
        self.assertEqual(len(box), 4)
        # Left, top, right, bottom are normalized [0, 1]
        self.assertTrue(0.0 <= box[0] <= box[2] <= 1.0)
        self.assertTrue(0.0 <= box[1] <= box[3] <= 1.0)

    def test_history_buffer_and_replay(self):
        from collections import deque
        history = deque()

        gray1 = np.zeros((100, 100), dtype=np.uint8)
        gray2 = np.zeros((100, 100), dtype=np.uint8)
        gray3 = np.zeros((100, 100), dtype=np.uint8)

        t1, t2, t3 = 1.0, 1.1, 1.2
        track1 = OpticalFlowTrack(1, "tire", (0.3, 0.3), (0.2, 0.2), gray1)
        track2 = copy.deepcopy(track1)
        track3 = copy.deepcopy(track1)

        history.append(FrameRecord(1, t1, gray1, {1: track1}))
        history.append(FrameRecord(2, t2, gray2, {1: track2}))
        history.append(FrameRecord(3, t3, gray3, {1: track3}))

        # VLM response arrives for frame 1: true position is (0.35, 0.35)
        corrected_track = copy.deepcopy(track1)
        corrected_track.correct((0.35, 0.35), (0.2, 0.2), gray1, 0.95)

        replayed_tracks = replay(history, 0, {1: corrected_track})
        self.assertIn(1, replayed_tracks)
        # Check that center of replayed track is close to the corrected position
        self.assertAlmostEqual(replayed_tracks[1].kf.x[0], 0.35, delta=0.05)

    def test_vlm_client_openrouter_parser(self):
        client = VLMClient(provider="openrouter", api_key="fake-key", model="google/gemini-2.0-flash-001")
        mock_response = MagicMock()
        json_content = '[{"class": "tire", "box": [0.1, 0.2, 0.5, 0.6], "confidence": 0.92}]'
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json_content
                    }
                }
            ]
        }
        with patch.object(client.session, "post", return_value=mock_response):
            frame = np.zeros((200, 200, 3), dtype=np.uint8)
            dets = client.detect(frame, ["tire"])
            self.assertEqual(len(dets), 1)
            self.assertEqual(dets[0]["class"], "tire")
            # [ymin, xmin, ymax, xmax] -> box: (xmin, ymin, xmax, ymax)
            self.assertEqual(dets[0]["box"], (0.2, 0.1, 0.6, 0.5))
            self.assertEqual(dets[0]["confidence"], 0.92)

    def test_vlm_client_typesafe_parser(self):
        client = VLMClient(provider="typesafe", api_key="fake-key", model="jev-preview")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answers": {
                "present": {"noul": 0.98},
                "tire": {
                    "confidence": 0.88,
                    "box": {"left": 0.15, "top": 0.2, "right": 0.45, "bottom": 0.7},
                },
            }
        }
        with patch.object(client.session, "post", return_value=mock_response):
            frame = np.zeros((200, 200, 3), dtype=np.uint8)
            dets = client.detect(frame, ["tire"])
            self.assertEqual(len(dets), 1)
            self.assertEqual(dets[0]["class"], "tire")
            self.assertEqual(dets[0]["box"], (0.15, 0.2, 0.45, 0.7))
            self.assertEqual(dets[0]["confidence"], 0.88)

    def test_runtime_sanitize_and_update(self):
        cfg = {
            "provider": "openrouter",
            "apiKey": "sk-or-secret-key-12345",
            "objectPrompt": "tire, worker",
            "queryIntervalSeconds": 1.0,
        }
        sanitized = sanitize_vlm_config(cfg)
        self.assertEqual(sanitized["apiKey"], "******")

        runtime = VLMBoxTrackerRuntime("vlm_node_1", cfg)
        try:
            frame = np.zeros((120, 160, 3), dtype=np.uint8)
            # Inject a synthetic detection directly
            with runtime.lock:
                runtime.latest_detections = [
                    {"class": "tire", "box": (0.2, 0.2, 0.6, 0.6), "confidence": 0.9}
                ]
                runtime.latest_result_frame_id = 1
                runtime.result_seq = 1

            results = runtime.update(frame, timestamp=10.0)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["class"], "tire")
            self.assertEqual(results[0]["sourceNodeId"], "vlm_node_1")
            self.assertEqual(results[0]["kind"], "detection")
            self.assertIn("bbox", results[0])
            self.assertEqual(len(results[0]["bbox"]), 4)
        finally:
            runtime.close()


if __name__ == "__main__":
    unittest.main()
