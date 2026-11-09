# -*- coding: utf-8 -*-
"""Event Clip Recorder Engine for AFI Vision Builder.

Captures automated event evidence video clips with pre-roll (5 seconds before event)
and post-roll (10 seconds after event). Saves MP4 video clips, thumbnail images,
and metadata to disk, and exposes them via REST API and live dashboard timeline scrubber.
Inspired by Open-NVR's Evidence Vault.
"""

from __future__ import annotations

import collections
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Optional

import cv2
import numpy as np

logger = logging.getLogger("afivision.event_recorder")

RECORDINGS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "recordings"
)
RECORDINGS_META_PATH = os.path.join(RECORDINGS_DIR, "recordings_catalog.json")


class EventClipRecorder:
    """Maintains a rolling ring-buffer and exports MP4 video clips upon trigger events."""

    def __init__(
        self,
        camera_id: str = "default_cam",
        fps: int = 15,
        pre_roll_seconds: float = 5.0,
        post_roll_seconds: float = 10.0,
        on_clip_ready: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        self.camera_id = camera_id
        self.fps = max(5, min(30, int(fps or 15)))
        self.pre_roll_seconds = max(1.0, min(30.0, float(pre_roll_seconds or 5.0)))
        self.post_roll_seconds = max(1.0, min(60.0, float(post_roll_seconds or 10.0)))
        self.on_clip_ready = on_clip_ready

        self.max_pre_roll_frames = int(self.pre_roll_seconds * self.fps)
        self.post_roll_frames_target = int(self.post_roll_seconds * self.fps)

        self._lock = threading.Lock()
        self._pre_roll_buffer: collections.deque[tuple[np.ndarray, float]] = collections.deque(
            maxlen=self.max_pre_roll_frames
        )

        # Active recording state
        self._is_recording = False
        self._active_event_info: Optional[dict[str, Any]] = None
        self._post_roll_buffer: list[tuple[np.ndarray, float]] = []
        self._trigger_frame: Optional[np.ndarray] = None

        os.makedirs(RECORDINGS_DIR, exist_ok=True)

    def add_frame(self, frame: np.ndarray, timestamp: Optional[float] = None) -> None:
        """Feed a new frame into the pre-roll ring buffer and active recording buffer."""
        if frame is None or not hasattr(frame, "shape"):
            return

        ts = timestamp if timestamp is not None else time.time()
        frame_copy = frame.copy()

        with self._lock:
            self._pre_roll_buffer.append((frame_copy, ts))

            if self._is_recording:
                self._post_roll_buffer.append((frame_copy, ts))
                if len(self._post_roll_buffer) >= self.post_roll_frames_target:
                    # Finalize clip in background worker
                    event_info = self._active_event_info or {}
                    trigger_frame = self._trigger_frame
                    full_frames = list(self._active_pre_roll_snapshot) + list(self._post_roll_buffer)

                    # Reset state
                    self._is_recording = False
                    self._active_event_info = None
                    self._post_roll_buffer = []
                    self._trigger_frame = None

                    # Spawn writer thread
                    threading.Thread(
                        target=self._write_clip_to_disk,
                        args=(full_frames, trigger_frame, event_info),
                        daemon=True,
                    ).start()

    def trigger(self, event_name: str, detail: str = "", metadata: Optional[dict[str, Any]] = None) -> bool:
        """Trigger an event recording if not already recording."""
        with self._lock:
            if self._is_recording:
                # Already capturing an event, extend or ignore
                return False

            self._is_recording = True
            now = time.time()
            self._active_pre_roll_snapshot = list(self._pre_roll_buffer)
            self._post_roll_buffer = []

            # Save latest frame as trigger thumbnail
            if self._pre_roll_buffer:
                self._trigger_frame = self._pre_roll_buffer[-1][0].copy()
            else:
                self._trigger_frame = None

            self._active_event_info = {
                "event_name": event_name,
                "detail": detail,
                "camera_id": self.camera_id,
                "timestamp": now,
                "date_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
                "metadata": metadata or {},
            }
            logger.info(f"EventClipRecorder triggered: '{event_name}' on {self.camera_id}")
            return True

    def _write_clip_to_disk(
        self,
        frames: list[tuple[np.ndarray, float]],
        trigger_frame: Optional[np.ndarray],
        event_info: dict[str, Any],
    ) -> None:
        """Encode and save MP4 video and JPEG thumbnail."""
        if not frames:
            return

        now_str = time.strftime("%Y%m%d_%H%M%S")
        safe_event = "".join(c for c in event_info.get("event_name", "event") if c.isalnum() or c in ("_", "-"))
        clip_filename = f"{now_str}_{self.camera_id}_{safe_event}.mp4"
        thumb_filename = f"{now_str}_{self.camera_id}_{safe_event}.jpg"

        clip_path = os.path.join(RECORDINGS_DIR, clip_filename)
        thumb_path = os.path.join(RECORDINGS_DIR, thumb_filename)

        first_frame = frames[0][0]
        h, w = first_frame.shape[:2]

        # 1. Save Thumbnail
        thumb_img = trigger_frame if trigger_frame is not None else first_frame
        try:
            cv2.imwrite(thumb_path, thumb_img)
        except Exception as e:
            logger.warning(f"Failed to save event thumbnail: {e}")

        # 2. Encode MP4 Video
        try:
            # Try mp4v codec
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(clip_path, fourcc, self.fps, (w, h))
            for f_img, _ in frames:
                # Ensure frame matches resolution
                if f_img.shape[:2] != (h, w):
                    f_img = cv2.resize(f_img, (w, h))
                writer.write(f_img)
            writer.release()
            duration_sec = round(len(frames) / max(1, self.fps), 1)
        except Exception as e:
            logger.error(f"Failed to encode event video clip: {e}")
            return

        record_entry = {
            "id": f"clip_{int(time.time()*1000)}",
            "camera_id": self.camera_id,
            "filename": clip_filename,
            "thumbnail": thumb_filename,
            "clip_path": clip_path,
            "thumb_path": thumb_path,
            "event_name": event_info.get("event_name"),
            "detail": event_info.get("detail"),
            "timestamp": event_info.get("timestamp"),
            "date_str": event_info.get("date_str"),
            "duration": duration_sec,
            "frames_count": len(frames),
            "width": w,
            "height": h,
            "size_bytes": os.path.getsize(clip_path) if os.path.exists(clip_path) else 0,
        }

        # Update metadata catalog JSON
        self._append_catalog(record_entry)

        if self.on_clip_ready:
            try:
                self.on_clip_ready(record_entry)
            except Exception as e:
                logger.debug(f"on_clip_ready callback error: {e}")

    @staticmethod
    def _append_catalog(entry: dict[str, Any]) -> None:
        """Thread-safe append to recordings_catalog.json."""
        catalog = []
        if os.path.exists(RECORDINGS_META_PATH):
            try:
                with open(RECORDINGS_META_PATH, "r", encoding="utf-8") as f:
                    catalog = json.load(f)
            except Exception:
                catalog = []
        catalog.insert(0, entry)
        # Keep maximum 500 records
        catalog = catalog[:500]
        try:
            with open(RECORDINGS_META_PATH, "w", encoding="utf-8") as f:
                json.dump(catalog, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save recordings catalog: {e}")

    @staticmethod
    def list_recordings(camera_id: Optional[str] = None) -> list[dict[str, Any]]:
        """List all saved recordings, optionally filtered by camera."""
        if not os.path.exists(RECORDINGS_META_PATH):
            return []
        try:
            with open(RECORDINGS_META_PATH, "r", encoding="utf-8") as f:
                records = json.load(f)
                if camera_id:
                    return [r for r in records if r.get("camera_id") == camera_id]
                return records
        except Exception:
            return []

    @staticmethod
    def delete_recording(filename: str) -> bool:
        """Delete an MP4 clip and its thumbnail from disk and catalog."""
        clip_path = os.path.join(RECORDINGS_DIR, filename)
        thumb_name = filename.replace(".mp4", ".jpg")
        thumb_path = os.path.join(RECORDINGS_DIR, thumb_name)

        if os.path.exists(clip_path):
            try:
                os.remove(clip_path)
            except Exception:
                pass
        if os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except Exception:
                pass

        # Update catalog
        if os.path.exists(RECORDINGS_META_PATH):
            try:
                with open(RECORDINGS_META_PATH, "r", encoding="utf-8") as f:
                    records = json.load(f)
                records = [r for r in records if r.get("filename") != filename]
                with open(RECORDINGS_META_PATH, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2)
                return True
            except Exception:
                pass
        return False
