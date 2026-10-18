"""VLM Box Tracker — Realtime object tracking fused with VLM / decision models.

Inspired by BenCaunt/jev-box-tracking:
Combines high-latency, sparse bounding boxes from TypeSafe Jev or OpenRouter VLM
with high-frequency Lucas-Kanade sparse optical flow and a constant-velocity Kalman
filter, using a rewind-and-replay history buffer to maintain zero-drift, 30+ FPS tracking.
"""
from __future__ import annotations

import base64
import copy
import json
import os
import re
import threading
import time
from collections import deque
from typing import Any, Optional, Tuple, List, Dict

import cv2
import numpy as np

# Tuning constants
DEFAULT_TRACK_WIDTH = 480
DEFAULT_SEND_WIDTH = 640
DEFAULT_HISTORY_SECONDS = 5.0
DEFAULT_MIN_CONFIDENCE = 0.5
DEFAULT_MIN_PRESENT = 0.5

VLM_POS_NOISE = 2e-4      # Variance of VLM box center (image fractions squared)
FLOW_VEL_NOISE = 1e-3     # Variance of optical flow velocity measurement
PROCESS_ACCEL_NOISE = 0.5 # Acceleration noise of constant velocity model
MIN_FLOW_POINTS = 8       # Minimum feature points to compute valid affine flow


def resolve_api_key(node_config: dict, provider: str) -> str:
    """Resolve API key from node config, fallback to environment variable."""
    cfg_key = str(node_config.get("apiKey") or "").strip()
    if cfg_key:
        return cfg_key
    if provider == "typesafe":
        return os.environ.get("TYPESAFE_API_KEY", "").strip()
    return os.environ.get("OPENROUTER_API_KEY", "").strip()


def sanitize_vlm_config(config: dict) -> dict:
    """Return a copy of config with API key masked for safe logging/export."""
    sanitized = copy.deepcopy(config)
    if "apiKey" in sanitized and sanitized["apiKey"]:
        sanitized["apiKey"] = "******"
    return sanitized


class ConstantVelocityKalmanFilter:
    """Kalman filter on bounding box center [cx, cy, vx, vy] with constant velocity model."""

    H_POSITION = np.array([[1.0, 0.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0, 0.0]])
    H_VELOCITY = np.array([[0.0, 0.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0, 1.0]])

    def __init__(self, position: Tuple[float, float], process_noise: float = PROCESS_ACCEL_NOISE):
        self.x = np.zeros(4, dtype=np.float64)
        self.x[:2] = position
        self.P = np.diag([VLM_POS_NOISE, VLM_POS_NOISE, 0.1, 0.1]).astype(np.float64)
        self.q = float(process_noise)

    def predict(self, dt: float) -> None:
        dt = max(float(dt), 1e-4)
        F = np.eye(4, dtype=np.float64)
        F[0, 2] = F[1, 3] = dt
        g = np.array([dt**2 / 2.0, dt**2 / 2.0, dt, dt], dtype=np.float64)
        Q = np.outer(g, g) * self.q * np.kron(np.ones((2, 2)), np.eye(2))
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q

    def update(self, z: np.ndarray, H: np.ndarray, variance: float) -> None:
        z = np.asarray(z, dtype=np.float64)
        y = z - H @ self.x
        S = H @ self.P @ H.T + np.eye(2, dtype=np.float64) * float(variance)
        try:
            K = self.P @ H.T @ np.linalg.inv(S)
        except np.linalg.LinAlgError:
            return
        self.x = self.x + K @ y
        self.P = (np.eye(4, dtype=np.float64) - K @ H) @ self.P


def seed_points(gray: np.ndarray, centre: Tuple[float, float], size: Tuple[float, float]) -> Optional[np.ndarray]:
    """Find good corner features to track inside the given normalized box."""
    h, w = gray.shape[:2]
    cx, cy = centre
    bw, bh = size
    left = int(max(0, min(w - 1, round((cx - bw / 2.0) * w))))
    right = int(max(0, min(w, round((cx + bw / 2.0) * w))))
    top = int(max(0, min(h - 1, round((cy - bh / 2.0) * h))))
    bottom = int(max(0, min(h, round((cy + bh / 2.0) * h))))

    if right - left < 5 or bottom - top < 5:
        return None

    mask = np.zeros_like(gray, dtype=np.uint8)
    mask[top:bottom, left:right] = 255
    pts = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.01, minDistance=5, mask=mask)
    return pts


class OpticalFlowTrack:
    """Maintains Kalman state, box size, and tracked feature points for one object."""

    def __init__(self, track_id: int, class_name: str, centre: Tuple[float, float],
                 size: Tuple[float, float], gray: np.ndarray, confidence: float = 1.0):
        self.track_id = int(track_id)
        self.class_name = str(class_name)
        self.kf = ConstantVelocityKalmanFilter(centre)
        self.size = np.array(size, dtype=np.float64)
        self.confidence = float(confidence)
        self.points = seed_points(gray, centre, self.size)
        self.last_seen = time.monotonic()

    def correct(self, centre: Tuple[float, float], size: Tuple[float, float],
                gray: np.ndarray, confidence: float) -> None:
        """Apply a new VLM measurement and reseed tracking points."""
        self.kf.update(np.array(centre), ConstantVelocityKalmanFilter.H_POSITION, VLM_POS_NOISE)
        self.size = np.array(size, dtype=np.float64)
        self.confidence = float(confidence)
        self.points = seed_points(gray, (float(self.kf.x[0]), float(self.kf.x[1])), self.size)
        self.last_seen = time.monotonic()

    def step(self, prev_gray: np.ndarray, gray: np.ndarray, dt: float) -> None:
        """Advance track forward one frame using Lucas-Kanade optical flow."""
        h, w = gray.shape[:2]
        prev_centre = self.kf.x[:2].copy()
        self.kf.predict(dt)

        if self.points is not None and len(self.points) >= MIN_FLOW_POINTS:
            nxt, status, _ = cv2.calcOpticalFlowPyrLK(
                prev_gray, gray, self.points, None, winSize=(21, 21), maxLevel=3
            )
            good = status.ravel() == 1
            p0, p1 = self.points[good], nxt[good]

            M, inliers = None, None
            if len(p0) >= MIN_FLOW_POINTS:
                M, inliers = cv2.estimateAffinePartial2D(
                    p0, p1, method=cv2.RANSAC, ransacReprojThreshold=3.0
                )

            if M is not None and inliers is not None and inliers.sum() >= MIN_FLOW_POINTS:
                c0 = prev_centre * (w, h)
                c1 = M[:, :2] @ c0 + M[:, 2]
                velocity = (c1 - c0) / (w, h) / max(dt, 1e-4)
                self.kf.update(velocity, ConstantVelocityKalmanFilter.H_VELOCITY, FLOW_VEL_NOISE)

                scale = np.sqrt(abs(np.linalg.det(M[:, :2])))
                if 0.5 <= scale <= 2.0:
                    self.size *= scale

                self.points = p1[inliers.ravel() == 1].reshape(-1, 1, 2)
            else:
                self.points = None

        if self.points is None or len(self.points) < MIN_FLOW_POINTS:
            self.points = seed_points(gray, (float(self.kf.x[0]), float(self.kf.x[1])), self.size)

    def box(self) -> Tuple[float, float, float, float]:
        """Returns normalized (left, top, right, bottom) clamped to [0, 1]."""
        cx, cy = float(self.kf.x[0]), float(self.kf.x[1])
        bw, bh = float(self.size[0]), float(self.size[1])
        left = max(0.0, min(1.0, cx - bw / 2.0))
        top = max(0.0, min(1.0, cy - bh / 2.0))
        right = max(0.0, min(1.0, cx + bw / 2.0))
        bottom = max(0.0, min(1.0, cy + bh / 2.0))
        return left, top, right, bottom


class FrameRecord:
    """Historical snapshot of a processed frame and tracker states."""

    def __init__(self, frame_id: int, t: float, gray: np.ndarray, tracks: Dict[int, OpticalFlowTrack]):
        self.frame_id = int(frame_id)
        self.t = float(t)
        self.gray = gray
        self.tracks = copy.deepcopy(tracks)


def replay(history: deque[FrameRecord], start_idx: int,
           corrected_tracks: Dict[int, OpticalFlowTrack]) -> Dict[int, OpticalFlowTrack]:
    """Re-run optical flow stepping from history[start_idx] up to newest frame."""
    if not history or start_idx < 0 or start_idx >= len(history):
        return corrected_tracks

    current_tracks = copy.deepcopy(corrected_tracks)
    history[start_idx].tracks = copy.deepcopy(current_tracks)

    for i in range(start_idx + 1, len(history)):
        prev_rec = history[i - 1]
        cur_rec = history[i]
        dt = max(cur_rec.t - prev_rec.t, 1e-3)

        for track_id, track in list(current_tracks.items()):
            track.step(prev_rec.gray, cur_rec.gray, dt)

        cur_rec.tracks = copy.deepcopy(current_tracks)

    return current_tracks


class VLMClient:
    """Client for querying TypeSafe Jev or OpenRouter vision models."""

    def __init__(self, provider: str = "openrouter", api_key: str = "",
                 model: str = "google/gemini-2.0-flash-001",
                 send_width: int = DEFAULT_SEND_WIDTH, timeout: float = 15.0):
        self.provider = str(provider).lower().strip()
        self.api_key = str(api_key).strip()
        self.model = str(model).strip() or "google/gemini-2.0-flash-001"
        self.send_width = int(send_width)
        self.timeout = float(timeout)
        self._session: Optional[Any] = None

    @property
    def session(self):
        if self._session is None:
            import requests
            self._session = requests.Session()
        return self._session

    def detect(self, frame_bgr: np.ndarray, target_objects: List[str]) -> List[dict]:
        """Detect target objects on frame. Returns list of {class, box: (l, t, r, b), confidence}."""
        if not self.api_key:
            return []

        h, w = frame_bgr.shape[:2]
        if w > self.send_width:
            target_h = max(1, round(h * self.send_width / w))
            resized = cv2.resize(frame_bgr, (self.send_width, target_h))
        else:
            resized = frame_bgr

        if self.provider == "typesafe":
            return self._detect_typesafe(resized, target_objects)
        return self._detect_openrouter(resized, target_objects)

    def _detect_typesafe(self, frame_bgr: np.ndarray, target_objects: List[str]) -> List[dict]:
        _, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        b64_img = base64.b64encode(buf).decode("ascii")

        results = []
        for obj in target_objects:
            obj_name = obj.strip()
            if not obj_name:
                continue
            body = {
                "model": self.model if "jev" in self.model.lower() else "jev-preview",
                "image": f"data:image/jpeg;base64,{b64_img}",
                "questions": [
                    {"question": f"Is there a {obj_name}?", "type": "noul"},
                    {"question": f"Where is the {obj_name}?", "type": "box"},
                ],
            }
            resp = self.session.post(
                "https://api.typesafe.ai/v1/systemone",
                json=body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "TypeSafe-Danger-Zone-Images": "true",
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json().get("answers", {})

            pres_ans = data.get("present", {})
            present_score = float(pres_ans.get("noul", 1.0))
            box_ans = data.get(obj_name, {})
            conf = float(box_ans.get("confidence", 0.0)) if box_ans else 0.0

            if present_score >= DEFAULT_MIN_PRESENT and conf >= DEFAULT_MIN_CONFIDENCE and "box" in box_ans:
                b = box_ans["box"]
                results.append({
                    "class": obj_name,
                    "box": (float(b["left"]), float(b["top"]), float(b["right"]), float(b["bottom"])),
                    "confidence": conf,
                })
        return results

    def _detect_openrouter(self, frame_bgr: np.ndarray, target_objects: List[str]) -> List[dict]:
        _, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        b64_img = base64.b64encode(buf).decode("ascii")

        targets_str = ", ".join(f'"{t.strip()}"' for t in target_objects if t.strip())
        prompt = (
            f"Detect and locate visible instances of: {targets_str}.\n"
            "Respond ONLY with a valid JSON array of detected objects without markdown formatting or markdown codeblocks.\n"
            "Each element must have:\n"
            ' - "class": name of the target class\n'
            ' - "box": normalized [ymin, xmin, ymax, xmax] coordinates from 0.0 to 1.0\n'
            ' - "confidence": confidence estimate from 0.0 to 1.0\n'
            "If none are visible, return []."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://afivision.local",
            "X-Title": "Afi Vision Builder",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                        },
                    ],
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        resp = self.session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=body,
            headers=headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        raw_content = resp.json()["choices"][0]["message"]["content"].strip()

        # Clean markdown code blocks if returned
        raw_content = re.sub(r"^```[a-zA-Z]*\n?", "", raw_content)
        raw_content = re.sub(r"\n?```$", "", raw_content).strip()

        items = []
        try:
            items = json.loads(raw_content)
        except Exception:
            match = re.search(r"\[.*\]", raw_content, re.DOTALL)
            if match:
                items = json.loads(match.group(0))

        results = []
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                cls_name = str(item.get("class") or "").strip()
                b = item.get("box")
                conf = float(item.get("confidence", 0.8))
                if isinstance(b, (list, tuple)) and len(b) == 4:
                    ymin, xmin, ymax, xmax = (float(v) for v in b)
                    results.append({
                        "class": cls_name,
                        "box": (min(xmin, xmax), min(ymin, ymax), max(xmin, xmax), max(ymin, ymax)),
                        "confidence": conf,
                    })
        return results


class VLMBoxTrackerRuntime:
    """Runtime engine for one vlm_box_tracker node instance."""

    def __init__(self, node_id: str, config: dict):
        self.node_id = str(node_id)
        self.config = dict(config or {})
        self.provider = str(self.config.get("provider", "openrouter")).lower()
        self.api_key = resolve_api_key(self.config, self.provider)
        self.model = str(self.config.get("model", "google/gemini-2.0-flash-001"))
        self.raw_prompt = str(self.config.get("objectPrompt", "tire, worker"))
        self.target_objects = [t.strip() for t in self.raw_prompt.split(",") if t.strip()]
        self.query_interval = max(0.0, float(self.config.get("queryIntervalSeconds", 1.0)))
        self.min_confidence = float(self.config.get("minConfidence", DEFAULT_MIN_CONFIDENCE))
        self.history_seconds = float(self.config.get("historySeconds", DEFAULT_HISTORY_SECONDS))
        self.track_width = int(self.config.get("trackWidth", DEFAULT_TRACK_WIDTH))
        self.send_width = int(self.config.get("sendWidth", DEFAULT_SEND_WIDTH))
        self.optical_flow_enabled = bool(self.config.get("opticalFlowEnabled", True))
        self.show_points = bool(self.config.get("showOpticalFlowPoints", False))

        self.client = VLMClient(
            provider=self.provider,
            api_key=self.api_key,
            model=self.model,
            send_width=self.send_width,
        )

        self.tracks: Dict[int, OpticalFlowTrack] = {}
        self.next_track_id = 1
        self.history: deque[FrameRecord] = deque()
        self.frame_id = 0

        # Background detector thread state
        self.lock = threading.Lock()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.running = True
        self.pending_frame = None
        self.pending_frame_id = 0
        self.last_query_time = 0.0
        self.latest_result_frame_id = 0
        self.latest_detections: List[dict] = []
        self.result_seq = 0
        self.last_applied_seq = 0
        self.last_error: Optional[str] = None
        self.latency: float = 0.0

        if self.api_key:
            self.worker_thread.start()

    def _worker_loop(self) -> None:
        """Background thread querying VLM without blocking video streaming."""
        while self.running:
            frame_to_process = None
            frame_id = 0
            with self.lock:
                now = time.monotonic()
                if (self.pending_frame is not None and
                        (now - self.last_query_time >= self.query_interval or self.last_query_time == 0.0)):
                    frame_to_process = self.pending_frame
                    frame_id = self.pending_frame_id
                    self.pending_frame = None
                    self.last_query_time = now

            if frame_to_process is None:
                time.sleep(0.02)
                continue

            t_start = time.monotonic()
            try:
                results = self.client.detect(frame_to_process, self.target_objects)
                t_latency = time.monotonic() - t_start
                with self.lock:
                    self.latest_result_frame_id = frame_id
                    self.latest_detections = results
                    self.result_seq += 1
                    self.latency = t_latency
                    self.last_error = None
            except Exception as e:
                t_latency = time.monotonic() - t_start
                with self.lock:
                    self.latency = t_latency
                    self.last_error = str(e)[:120]

    def close(self) -> None:
        """Stop background worker cleanly."""
        self.running = False

    def update(self, frame_bgr: np.ndarray, timestamp: Optional[float] = None) -> List[dict]:
        """Process one frame: tracks forward with optical flow, corrects & replays on VLM answers."""
        if frame_bgr is None or not hasattr(frame_bgr, "shape"):
            return []

        h, w = frame_bgr.shape[:2]
        t = time.monotonic() if timestamp is None else float(timestamp)
        self.frame_id += 1

        # Submit latest frame to background detector thread
        if self.running and self.api_key:
            with self.lock:
                self.pending_frame = frame_bgr.copy()
                self.pending_frame_id = self.frame_id

        # Downscale to grayscale for fast Lucas-Kanade optical flow
        track_h = max(1, round(h * self.track_width / w))
        gray = cv2.cvtColor(cv2.resize(frame_bgr, (self.track_width, track_h)), cv2.COLOR_BGR2GRAY)

        # 1. Step existing tracks forward one frame
        if self.optical_flow_enabled and self.history:
            prev_gray = self.history[-1].gray
            dt = max(t - self.history[-1].t, 1e-3)
            for track in self.tracks.values():
                track.step(prev_gray, gray, dt)

        # Record this frame in history
        self.history.append(FrameRecord(self.frame_id, t, gray, self.tracks))
        while self.history and t - self.history[0].t > self.history_seconds:
            self.history.popleft()

        # 2. Check if a new VLM answer arrived from the past
        with self.lock:
            seq = self.result_seq
            ans_frame_id = self.latest_result_frame_id
            vlm_dets = list(self.latest_detections)

        if seq != self.last_applied_seq and self.history:
            self.last_applied_seq = seq
            # Find the historical frame index corresponding to ans_frame_id
            start_idx = -1
            for idx, rec in enumerate(self.history):
                if rec.frame_id == ans_frame_id:
                    start_idx = idx
                    break

            if start_idx >= 0:
                rec = self.history[start_idx]
                past_tracks = copy.deepcopy(rec.tracks)

                # Match VLM detections to past tracks by IoU / class
                matched_tracks: Dict[int, OpticalFlowTrack] = {}
                used_det_indices = set()

                for tid, track in past_tracks.items():
                    tb = track.box()
                    best_iou = 0.0
                    best_idx = -1
                    for d_idx, det in enumerate(vlm_dets):
                        if d_idx in used_det_indices:
                            continue
                        if det["class"].lower() != track.class_name.lower():
                            continue
                        db = det["box"]
                        # Calculate IoU
                        ix1, iy1 = max(tb[0], db[0]), max(tb[1], db[1])
                        ix2, iy2 = min(tb[2], db[2]), min(tb[3], db[3])
                        inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
                        union = ((tb[2]-tb[0])*(tb[3]-tb[1]) + (db[2]-db[0])*(db[3]-db[1]) - inter)
                        iou = inter / union if union > 0 else 0.0
                        if iou > best_iou:
                            best_iou = iou
                            best_idx = d_idx

                    if best_idx >= 0 and best_iou >= 0.15:
                        det = vlm_dets[best_idx]
                        used_det_indices.add(best_idx)
                        db = det["box"]
                        centre = ((db[0] + db[2]) / 2.0, (db[1] + db[3]) / 2.0)
                        size = (db[2] - db[0], db[3] - db[1])
                        track.correct(centre, size, rec.gray, det["confidence"])
                        matched_tracks[tid] = track
                    else:
                        # Retain track if it was not detected in this frame
                        matched_tracks[tid] = track

                # Spawn new tracks for unmatched VLM detections
                for d_idx, det in enumerate(vlm_dets):
                    if d_idx in used_det_indices or det["confidence"] < self.min_confidence:
                        continue
                    db = det["box"]
                    centre = ((db[0] + db[2]) / 2.0, (db[1] + db[3]) / 2.0)
                    size = (db[2] - db[0], db[3] - db[1])
                    tid = self.next_track_id
                    self.next_track_id += 1
                    matched_tracks[tid] = OpticalFlowTrack(
                        track_id=tid,
                        class_name=det["class"],
                        centre=centre,
                        size=size,
                        gray=rec.gray,
                        confidence=det["confidence"],
                    )

                # Replay from historical frame to current frame!
                if self.optical_flow_enabled:
                    self.tracks = replay(self.history, start_idx, matched_tracks)
                else:
                    self.tracks = matched_tracks

        # 3. Clean up stale tracks (not seen in history_seconds)
        now = time.monotonic()
        self.tracks = {tid: trk for tid, trk in self.tracks.items()
                       if now - trk.last_seen <= self.history_seconds}

        # 4. Format into standardized detections/tracks
        output_results: List[dict] = []
        for tid, track in self.tracks.items():
            left, top, right, bottom = track.box()
            px1 = round(left * w)
            py1 = round(top * h)
            px2 = round(right * w)
            py2 = round(bottom * h)
            pw = max(1, px2 - px1)
            ph = max(1, py2 - py1)

            pts_list = None
            if self.show_points and track.points is not None:
                scale = w / float(self.track_width)
                pts_list = [(float(pt[0][0] * scale), float(pt[0][1] * scale)) for pt in track.points]

            det_item = {
                "id": f"vlm_{tid}",
                "trackId": tid,
                "class": track.class_name,
                "score": round(track.confidence, 3),
                "confidence": round(track.confidence, 3),
                "bbox": [px1, py1, pw, ph],
                "normalizedBbox": [left, top, right, bottom],
                "kind": "detection",
                "sourceNodeId": self.node_id,
                "latency": round(self.latency, 3),
                "opticalFlowPoints": pts_list,
            }
            output_results.append(det_item)

        return output_results
