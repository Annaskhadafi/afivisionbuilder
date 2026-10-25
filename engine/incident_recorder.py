"""Incident Video Recorder Node for AFI Vision Builder.

Merekam klip video MP4 otomatis menggunakan rolling buffer di memori RAM
(pre-buffer durasi N detik sebelum insiden + post-buffer N detik setelah insiden).
Proses encoding video dijalankan secara asinkron (background thread) agar tidak
membebani atau menghentikan alur inferensi computer vision real-time.
"""

from __future__ import annotations

import collections
import datetime
import json
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("afi.incident_recorder")


class IncidentVideoRecorder:
    """Manajer perekam klip insiden dengan rolling buffer multi-stream."""

    _instances: Dict[str, "IncidentVideoRecorder"] = {}
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, node_id: str, config: Optional[Dict[str, Any]] = None) -> "IncidentVideoRecorder":
        with cls._lock:
            if node_id not in cls._instances:
                cls._instances[node_id] = IncidentVideoRecorder(node_id, config or {})
            elif config:
                cls._instances[node_id].update_config(config)
            return cls._instances[node_id]

    def __init__(self, node_id: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.config = config or {}
        self.output_dir = self.config.get("outputDirectory", "data/recordings")
        os.makedirs(self.output_dir, exist_ok=True)

        self.fps = float(self.config.get("fps", 20.0))
        self.pre_buffer_seconds = float(self.config.get("preBufferSeconds", 5.0))
        self.post_buffer_seconds = float(self.config.get("postBufferSeconds", 10.0))
        self.max_pre_frames = max(10, int(self.pre_buffer_seconds * self.fps))
        self.max_post_frames = max(10, int(self.post_buffer_seconds * self.fps))

        # Rolling circular buffer for pre-incident frames: (timestamp, frame_bgr)
        self.frame_buffer = collections.deque(maxlen=self.max_pre_frames)

        # Active recording state
        self.is_recording = False
        self.recording_frames: List[np.ndarray] = []
        self.recording_start_time: float = 0.0
        self.recording_trigger_info: Dict[str, Any] = {}
        self.last_saved_clip: Optional[Dict[str, Any]] = None
        self.last_trigger_time: float = 0.0
        self.cooldown_seconds = float(self.config.get("cooldownSeconds", 15.0))

    def update_config(self, config: Dict[str, Any]) -> None:
        self.config.update(config)
        self.output_dir = self.config.get("outputDirectory", "data/recordings")
        os.makedirs(self.output_dir, exist_ok=True)
        self.fps = float(self.config.get("fps", 20.0))
        self.pre_buffer_seconds = float(self.config.get("preBufferSeconds", 5.0))
        self.post_buffer_seconds = float(self.config.get("postBufferSeconds", 10.0))
        self.max_pre_frames = max(10, int(self.pre_buffer_seconds * self.fps))
        self.max_post_frames = max(10, int(self.post_buffer_seconds * self.fps))
        if self.frame_buffer.maxlen != self.max_pre_frames:
            self.frame_buffer = collections.deque(self.frame_buffer, maxlen=self.max_pre_frames)
        self.cooldown_seconds = float(self.config.get("cooldownSeconds", 15.0))

    def process_frame(
        self,
        frame: np.ndarray,
        trigger_active: bool,
        trigger_meta: Optional[Dict[str, Any]] = None,
        now: Optional[float] = None
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Proses frame kontinu: menyimpan buffer dan memicu perekaman jika trigger aktif."""
        current_time = now if now is not None else time.time()
        result_event = None

        if frame is None or not hasattr(frame, "shape"):
            return {"status": "idle", "is_recording": False}, None

        # 1. Simpan frame ke rolling pre-buffer (ringan: salin atau simpan ref)
        # Resize frame jika dikonfigurasi resolusi simpan lebih hemat
        target_frame = frame.copy()
        self.frame_buffer.append(target_frame)

        # 2. Cek pemicu baru
        if trigger_active and not self.is_recording:
            if current_time - self.last_trigger_time >= self.cooldown_seconds:
                self.is_recording = True
                self.last_trigger_time = current_time
                self.recording_start_time = current_time
                self.recording_trigger_info = trigger_meta or {"trigger": "manual_or_event"}
                # Ambil semua frame pre-buffer yang tersimpan
                self.recording_frames = list(self.frame_buffer)
                logger.info("Incident recording dimulai untuk node %s (pre-buffer: %d frames)", self.node_id, len(self.recording_frames))

        # 3. Lanjutkan merekam jika sedang dalam fase post-buffer
        if self.is_recording:
            self.recording_frames.append(target_frame)
            elapsed_post = current_time - self.recording_start_time
            if elapsed_post >= self.post_buffer_seconds or len(self.recording_frames) >= (self.max_pre_frames + self.max_post_frames):
                # Selesaikan rekaman klip
                frames_to_save = list(self.recording_frames)
                meta_info = dict(self.recording_trigger_info)
                meta_info["duration_seconds"] = round(elapsed_post + self.pre_buffer_seconds, 2)
                meta_info["total_frames"] = len(frames_to_save)
                meta_info["fps"] = self.fps

                self.is_recording = False
                self.recording_frames = []

                # Jalankan writer di background thread
                clip_info = self._dispatch_save_clip(frames_to_save, meta_info)
                self.last_saved_clip = clip_info
                result_event = {
                    "event_type": "incident_clip_recorded",
                    "node_id": self.node_id,
                    "video_path": clip_info["video_path"],
                    "duration": clip_info["duration"],
                    "timestamp": clip_info["timestamp"],
                    "trigger_meta": meta_info,
                }

        status = {
            "is_recording": self.is_recording,
            "buffer_frames": len(self.frame_buffer),
            "recording_frames": len(self.recording_frames) if self.is_recording else 0,
            "last_saved_clip": self.last_saved_clip,
            "status": "recording" if self.is_recording else "monitoring"
        }
        return status, result_event

    def _dispatch_save_clip(self, frames: List[np.ndarray], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Menjadwalkan penyimpanan file MP4 dan JSON metadata di thread terpisah."""
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"incident_{self.node_id}_{timestamp_str}"
        video_path = os.path.join(self.output_dir, f"{filename_base}.mp4")
        meta_path = os.path.join(self.output_dir, f"{filename_base}.json")

        clip_info = {
            "video_path": os.path.abspath(video_path),
            "meta_path": os.path.abspath(meta_path),
            "filename": f"{filename_base}.mp4",
            "timestamp": datetime.datetime.now().isoformat(),
            "duration": meta.get("duration_seconds", 0.0),
            "frames": len(frames),
        }

        def _worker():
            try:
                if not frames:
                    return
                h, w = frames[0].shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(video_path, fourcc, self.fps, (w, h))
                for f in frames:
                    if f.shape[:2] != (h, w):
                        f = cv2.resize(f, (w, h))
                    writer.write(f)
                writer.release()

                meta_data = {
                    "clip": clip_info,
                    "trigger_info": meta,
                    "created_at": datetime.datetime.now().isoformat()
                }
                with open(meta_path, "w", encoding="utf-8") as f_json:
                    json.dump(meta_data, f_json, indent=2)

                logger.info("Incident clip tersimpan: %s (%d frames)", video_path, len(frames))
            except Exception as e:
                logger.error("Gagal menyimpan video incident clip %s: %s", video_path, e)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return clip_info


def process_incident_video_recorder(
    node: Dict[str, Any],
    frame: np.ndarray,
    candidates: List[Dict[str, Any]],
    state: Dict[str, Any],
    now: float
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Fungsi runner yang dipanggil oleh workflow engine core.py."""
    node_id = str(node.get("id") or "incident_recorder")
    config = node.get("config", {})
    recorder = IncidentVideoRecorder.get_instance(node_id, config)

    # Deteksi apakah trigger aktif
    # 1. Trigger via config manual
    trigger_mode = config.get("triggerMode", "on_detection")
    target_class = config.get("targetClass", "any")

    trigger_active = False
    trigger_meta = {}

    if trigger_mode == "manual":
        trigger_active = bool(config.get("manualTrigger", False))
        trigger_meta = {"reason": "manual_config"}
    elif trigger_mode == "on_detection":
        matching = []
        for d in candidates:
            c = str(d.get("class", "")).lower()
            if target_class == "any" or c == target_class.lower():
                matching.append(d)
        if matching:
            trigger_active = True
            trigger_meta = {
                "reason": "class_detection",
                "matched_count": len(matching),
                "matched_classes": list(set(d.get("class") for d in matching)),
                "sample_bbox": matching[0].get("bbox")
            }
    elif trigger_mode == "on_violation":
        violations = [d for d in candidates if d.get("isViolation") or d.get("isManDown") or d.get("ppeStatus") == "VIOLATION"]
        if violations:
            trigger_active = True
            trigger_meta = {
                "reason": "safety_violation",
                "violation_count": len(violations),
                "types": list(set(v.get("class") for v in violations))
            }

    status, event = recorder.process_frame(frame, trigger_active, trigger_meta, now)
    events = [event] if event else []
    return status, events
