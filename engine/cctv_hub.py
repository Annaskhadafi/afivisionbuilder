# -*- coding: utf-8 -*-
"""CCTV & Open-NVR Hub Manager for AFI Vision Builder.

Manages registered CCTV cameras, persistent configuration (data/cameras.json),
and a Shared Stream Ingestion Engine (Single Ingest, Multi-Consumer) so multiple
AI workflows and dashboard previews can consume the same camera stream without
overloading the physical CCTV hardware.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
from typing import Any, Generator, Optional

import cv2
import numpy as np

logger = logging.getLogger("afivision.cctv_hub")

CAMERAS_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cameras.json"
)


class SharedCameraStream:
    """Thread-safe single-ingestion camera runner with auto-reconnect and frame caching."""

    def __init__(self, camera_id: str, rtsp_url: str, target_fps: int = 15, hwaccel: str = "cpu"):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.target_fps = max(1, min(30, int(target_fps or 15)))
        self.hwaccel = str(hwaccel or "cpu").lower()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest_frame_bgr: Optional[np.ndarray] = None
        self._latest_frame_jpeg: Optional[bytes] = None
        self._last_access_time = time.time()
        self._is_online = False
        self._fps_actual = 0.0
        self._frame_count = 0
        self._error_message: Optional[str] = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_worker, name=f"CCTVReader-{self.camera_id}", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def touch(self) -> None:
        """Mark stream as recently consumed to prevent auto-idle."""
        self._last_access_time = time.time()

    def get_frame(self) -> Optional[np.ndarray]:
        self.touch()
        with self._lock:
            if self._latest_frame_bgr is not None:
                return self._latest_frame_bgr.copy()
            return None

    def get_jpeg(self) -> Optional[bytes]:
        self.touch()
        with self._lock:
            return self._latest_frame_jpeg

    @property
    def is_online(self) -> bool:
        return self._is_online

    @property
    def fps_actual(self) -> float:
        return round(self._fps_actual, 1)

    def _capture_worker(self) -> None:
        logger.info(f"Starting shared RTSP ingest for {self.camera_id}")
        backoff = 1.0

        while self._running:
            # Auto-idle check: pause stream if no consumer touched it for 60 seconds
            if time.time() - self._last_access_time > 60.0:
                with self._lock:
                    self._is_online = False
                time.sleep(1.0)
                continue

            cap = None
            try:
                # Apply hardware acceleration options
                try:
                    from ffmpeg_decoder import HwAccelPresets
                except ImportError:
                    from engine.ffmpeg_decoder import HwAccelPresets
                HwAccelPresets.apply_opencv_options(getattr(self, "hwaccel", "cpu"))

                cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                if not cap.isOpened():
                    raise RuntimeError("Failed to open RTSP video capture stream")

                with self._lock:
                    self._is_online = True
                    self._error_message = None
                backoff = 1.0

                frame_interval = 1.0 / self.target_fps
                last_frame_time = time.time()
                fps_calc_start = time.time()
                frames_in_period = 0

                while self._running and (time.time() - self._last_access_time <= 60.0):
                    now = time.time()
                    elapsed = now - last_frame_time
                    if elapsed < frame_interval:
                        time.sleep(max(0.002, frame_interval - elapsed))

                    ret, frame = cap.read()
                    if not ret or frame is None:
                        logger.warning(f"RTSP stream empty/disconnected: {self.camera_id}")
                        break

                    last_frame_time = time.time()
                    frames_in_period += 1

                    # Update actual measured FPS every second
                    if now - fps_calc_start >= 1.0:
                        self._fps_actual = frames_in_period / (now - fps_calc_start)
                        fps_calc_start = now
                        frames_in_period = 0

                    # Encode JPEG snapshot for lightweight web preview
                    _, jpeg_buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    jpeg_bytes = jpeg_buf.tobytes()

                    with self._lock:
                        self._latest_frame_bgr = frame
                        self._latest_frame_jpeg = jpeg_bytes
                        self._frame_count += 1

            except Exception as e:
                with self._lock:
                    self._is_online = False
                    self._error_message = str(e)
                logger.debug(f"CCTV capture error for {self.camera_id}: {e}")
                time.sleep(min(backoff, 10.0))
                backoff = min(backoff * 1.5, 10.0)

            finally:
                if cap is not None:
                    try:
                        cap.release()
                    except Exception:
                        pass

        with self._lock:
            self._is_online = False
        logger.info(f"Stopped shared RTSP ingest for {self.camera_id}")


class CCTVHubManager:
    """Central singleton manager for configured CCTV cameras and stream hubs."""

    _instance: Optional["CCTVHubManager"] = None

    def __new__(cls) -> "CCTVHubManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._cameras: dict[str, dict[str, Any]] = {}
        self._streams: dict[str, SharedCameraStream] = {}
        self._lock = threading.Lock()
        self._load_config()

    def _load_config(self) -> None:
        os.makedirs(os.path.dirname(CAMERAS_CONFIG_PATH), exist_ok=True)
        if os.path.exists(CAMERAS_CONFIG_PATH):
            try:
                with open(CAMERAS_CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._cameras = data
                    elif isinstance(data, list):
                        self._cameras = {str(c.get("id") or f"cctv_{i}"): c for i, c in enumerate(data) if isinstance(c, dict)}
                    else:
                        self._cameras = {}
            except Exception as e:
                logger.warning(f"Failed to read cameras.json, starting fresh: {e}")
                self._cameras = {}
        else:
            self._cameras = {}
            self._save_config()

    def _save_config(self) -> None:
        os.makedirs(os.path.dirname(CAMERAS_CONFIG_PATH), exist_ok=True)
        try:
            with open(CAMERAS_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(list(self._cameras.values()), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cameras.json: {e}")

    def list_cameras(self) -> list[dict[str, Any]]:
        results = []
        with self._lock:
            for cam_id, cam_data in self._cameras.items():
                stream = self._streams.get(cam_id)
                c_copy = dict(cam_data)
                c_copy["is_online"] = stream.is_online if stream else False
                c_copy["fps_actual"] = stream.fps_actual if stream else 0.0
                results.append(c_copy)
        return results

    def get_camera(self, camera_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            cam = self._cameras.get(camera_id)
            if cam:
                c_copy = dict(cam)
                stream = self._streams.get(camera_id)
                c_copy["is_online"] = stream.is_online if stream else False
                c_copy["fps_actual"] = stream.fps_actual if stream else 0.0
                return c_copy
            return None

    def add_or_update_camera(self, data: dict[str, Any]) -> dict[str, Any]:
        cam_id = data.get("id") or f"cctv_{int(time.time() * 1000)}"
        name = data.get("name") or f"Kamera {cam_id}"
        rtsp_url = data.get("rtsp_url") or data.get("stream_uri") or data.get("streamUrl") or ""

        width = int(data.get("width") or 1280)
        height = int(data.get("height") or 720)
        resolution = str(data.get("resolution") or f"{height}p")
        if "1080" in resolution:
            width, height = 1920, 1080
        elif "720" in resolution:
            width, height = 1280, 720
        elif "480" in resolution or "360" in resolution:
            width, height = 640, 360

        cam_record = {
            "id": cam_id,
            "name": name,
            "ip": data.get("ip", ""),
            "port": int(data.get("port", 80)),
            "scheme": data.get("scheme", "http"),
            "username": data.get("username", "admin"),
            "password": data.get("password", ""),
            "rtsp_url": rtsp_url,
            "selected_profile": data.get("selected_profile", "SubStream"),
            "manufacturer": data.get("manufacturer", "Universal ONVIF"),
            "model": data.get("model", "Generic IP Camera"),
            "resolution": resolution,
            "width": width,
            "height": height,
            "fps": int(data.get("fps") or 25),
            "hwaccel": str(data.get("hwaccel", "cpu")).lower(),
            "group": data.get("group") or "Umum",
            "enabled": bool(data.get("enabled", True)),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        with self._lock:
            self._cameras[cam_id] = cam_record
            self._save_config()

            # Restart or create stream if enabled and url present
            if cam_id in self._streams:
                self._streams[cam_id].stop()
                del self._streams[cam_id]

            if cam_record["enabled"] and rtsp_url:
                stream = SharedCameraStream(
                    cam_id, rtsp_url, target_fps=min(25, cam_record["fps"]), hwaccel=cam_record["hwaccel"]
                )
                self._streams[cam_id] = stream
                stream.start()

        return cam_record

    def delete_camera(self, camera_id: str) -> bool:
        with self._lock:
            if camera_id in self._cameras:
                del self._cameras[camera_id]
                self._save_config()
                if camera_id in self._streams:
                    self._streams[camera_id].stop()
                    del self._streams[camera_id]
                return True
            return False

    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Fetch latest frame from shared stream buffer."""
        with self._lock:
            stream = self._streams.get(camera_id)
            if not stream:
                cam = self._cameras.get(camera_id)
                if cam and cam.get("rtsp_url") and cam.get("enabled", True):
                    stream = SharedCameraStream(camera_id, cam["rtsp_url"])
                    self._streams[camera_id] = stream
                    stream.start()
        if stream:
            f = stream.get_frame()
            if f is not None:
                return f

        # Offline cameras return no active numpy frame to prevent downstream AI hallucination
        return None

    def get_jpeg(self, camera_id: str) -> Optional[bytes]:
        """Fetch latest JPEG frame from shared stream buffer, or authentic CCTV NO SIGNAL standby card."""
        with self._lock:
            stream = self._streams.get(camera_id)
            if not stream:
                cam = self._cameras.get(camera_id)
                if cam and cam.get("rtsp_url") and cam.get("enabled", True):
                    stream = SharedCameraStream(camera_id, cam["rtsp_url"])
                    self._streams[camera_id] = stream
                    stream.start()
        if stream:
            jpg = stream.get_jpeg()
            if jpg:
                return jpg

        # Clean, professional CCTV NO SIGNAL frame (eliminated dummy sample workshop graphics)
        cam = self._cameras.get(camera_id, {})
        cam_name = cam.get("name", camera_id)
        rtsp_url = cam.get("rtsp_url", "")
        ip_addr = cam.get("ip", "")

        w, h = 640, 360
        img = np.full((h, w, 3), (22, 17, 13), dtype=np.uint8)  # Deep matte dark slate (BGR)

        # Draw subtle technical matrix grid lines
        for x in range(0, w, 40):
            cv2.line(img, (x, 0), (x, h), (32, 25, 20), 1)
        for y in range(0, h, 40):
            cv2.line(img, (0, y), (w, y), (32, 25, 20), 1)

        # Center reticle
        cx, cy = w // 2, h // 2
        cv2.circle(img, (cx, cy), 50, (55, 45, 35), 1)
        cv2.line(img, (cx - 65, cy), (cx + 65, cy), (55, 45, 35), 1)
        cv2.line(img, (cx, cy - 65), (cx, cy + 65), (55, 45, 35), 1)

        # OSD Header bar
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        osd_title = f"{cam_name.upper()[:24]} | {now_str}"
        cv2.rectangle(img, (12, 12), (min(w - 12, 420), 42), (10, 14, 22), -1)
        cv2.rectangle(img, (12, 12), (min(w - 12, 420), 42), (56, 189, 248), 1)
        cv2.putText(img, osd_title, (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (241, 245, 249), 1, cv2.LINE_AA)
        cv2.circle(img, (min(w - 30, 400), 27), 4, (100, 116, 139), -1)

        # Center "NO SIGNAL / OFFLINE" message
        cv2.putText(img, "NO SIGNAL / OFFLINE", (cx - 130, cy - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (148, 163, 184), 2, cv2.LINE_AA)
        sub_info = f"Menunggu Sinyal RTSP ({rtsp_url[:35] if rtsp_url else ip_addr or camera_id})"
        cv2.putText(img, sub_info, (cx - 150, cy + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 116, 139), 1, cv2.LINE_AA)

        _, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return enc.tobytes()


# Global singleton instance
cctv_hub = CCTVHubManager()
