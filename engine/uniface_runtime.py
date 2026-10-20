"""
UniFace Runtime Module:
High-performance Face Detection, Facial Landmark Localization, Face Recognition,
and Face Re-ID Identity Tracking using UniFace and ONNX Runtime.

Includes:
- UniFaceRegistry: Local database for known / enrolled faces with ArcFace 512-D embeddings.
- UniFaceDetector: Real-time face detection with 5-point facial landmarks.
- UniFaceTracker: Re-ID identity tracker matching faces against the registry or dynamic tracks.
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("uniface_runtime")

FACES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "faces")
IMAGES_DIR = os.path.join(FACES_DIR, "images")
REGISTRY_FILE = os.path.join(FACES_DIR, "registry.json")


def _ensure_storage_dirs(faces_dir: str = FACES_DIR, images_dir: str = IMAGES_DIR, registry_file: str = REGISTRY_FILE) -> None:
    os.makedirs(images_dir, exist_ok=True)
    if not os.path.exists(registry_file):
        with open(registry_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)


class UniFaceRegistry:
    """Manages enrolled faces, avatar images, and 512-D ArcFace feature embeddings."""

    _instance: Optional["UniFaceRegistry"] = None

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or FACES_DIR
        self.images_dir = os.path.join(self.storage_dir, "images")
        self.registry_file = os.path.join(self.storage_dir, "registry.json")
        _ensure_storage_dirs(self.storage_dir, self.images_dir, self.registry_file)
        self.faces: List[Dict[str, Any]] = []
        self._load()

    @classmethod
    def get_instance(cls) -> "UniFaceRegistry":
        if cls._instance is None:
            cls._instance = UniFaceRegistry()
        return cls._instance

    def _load(self) -> None:
        try:
            if os.path.exists(self.registry_file):
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self.faces = json.load(f)
            else:
                self.faces = []
        except Exception as e:
            logger.error(f"Error loading face registry: {e}")
            self.faces = []

    def _save(self) -> None:
        try:
            _ensure_storage_dirs(self.storage_dir, self.images_dir, self.registry_file)
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self.faces, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving face registry: {e}")

    def list_faces(self) -> List[Dict[str, Any]]:
        """Return public list of faces (excluding raw embedding arrays for lightweight API response)."""
        result = []
        for f in self.faces:
            has_emb = bool(f.get("embedding") and len(f["embedding"]) > 0)
            result.append({
                "id": f.get("id"),
                "name": f.get("name", "Unknown"),
                "role": f.get("role", "Karyawan"),
                "notes": f.get("notes", ""),
                "photo_url": f.get("photo_url", ""),
                "has_embedding": has_emb,
                "created_at": f.get("created_at", 0),
            })
        return result

    def get_face(self, face_id: str) -> Optional[Dict[str, Any]]:
        for f in self.faces:
            if f.get("id") == face_id:
                return f
        return None

    def enroll_face(
        self,
        image_or_name: Any = None,
        name: Optional[str] = None,
        role: str = "Karyawan",
        notes: str = "",
        image_bgr: Optional[np.ndarray] = None,
        embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Enrolls a new face into the registry.
        Supports calling both enroll_face(name=...) and enroll_face(image_bgr, name=...).
        If embedding is omitted, detects the face and extracts a 512-D ArcFace embedding automatically.
        Crops and saves an avatar thumbnail.
        """
        if isinstance(image_or_name, str):
            final_name = image_or_name
            final_img = image_bgr
        elif isinstance(image_or_name, np.ndarray):
            final_img = image_or_name
            final_name = name or "Wajah Terdaftar"
        else:
            final_name = name or "Wajah Terdaftar"
            final_img = image_bgr

        _ensure_storage_dirs(self.storage_dir, self.images_dir, self.registry_file)
        face_id = "face_" + uuid.uuid4().hex[:12]
        crop_bgr = None
        extracted_emb = embedding

        if final_img is not None and getattr(final_img, "size", 0) > 0:
            h, w = final_img.shape[:2]
            crop_bgr = final_img
            # If embedding not provided, use UniFace to detect and extract
            if extracted_emb is None:
                mgr = get_uniface_manager()
                faces = mgr.detect_faces(final_img, conf_thresh=0.4)
                if faces:
                    # Pick largest face
                    largest = max(faces, key=lambda fc: (fc["width"] * fc["height"]))
                    x1 = max(0, int(largest["x"]))
                    y1 = max(0, int(largest["y"]))
                    x2 = min(w, int(largest["x"] + largest["width"]))
                    y2 = min(h, int(largest["y"] + largest["height"]))
                    if x2 > x1 and y2 > y1:
                        # Add 15% margin for avatar
                        pad_w = int((x2 - x1) * 0.15)
                        pad_h = int((y2 - y1) * 0.15)
                        crop_x1 = max(0, x1 - pad_w)
                        crop_y1 = max(0, y1 - pad_h)
                        crop_x2 = min(w, x2 + pad_w)
                        crop_y2 = min(h, y2 + pad_h)
                        crop_bgr = final_img[crop_y1:crop_y2, crop_x1:crop_x2]

                    # Extract embedding
                    emb_vec = mgr.extract_embedding(final_img, landmarks=largest.get("landmarks"))
                    if emb_vec is not None:
                        extracted_emb = emb_vec.tolist()

        # Save cropped avatar image if available
        avatar_filename = f"{face_id}.jpg"
        avatar_path = os.path.join(self.images_dir, avatar_filename)
        photo_url = ""
        if crop_bgr is not None and crop_bgr.size > 0:
            avatar_resized = cv2.resize(crop_bgr, (200, 200), interpolation=cv2.INTER_AREA)
            cv2.imwrite(avatar_path, avatar_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            photo_url = f"/api/faces/images/{avatar_filename}"

        record = {
            "id": face_id,
            "name": name.strip(),
            "role": role.strip() or "Karyawan",
            "notes": notes.strip(),
            "photo_url": photo_url,
            "embedding": extracted_emb or [],
            "created_at": time.time(),
        }

        self.faces.append(record)
        self._save()
        return record

    def update_face(self, face_id: str, name: str, role: str, notes: str = "") -> Optional[Dict[str, Any]]:
        face = self.get_face(face_id)
        if not face:
            return None
        face["name"] = name.strip()
        face["role"] = role.strip()
        face["notes"] = notes.strip()
        self._save()
        return face

    def delete_face(self, face_id: str) -> bool:
        face = self.get_face(face_id)
        if not face:
            return False
        # Remove photo
        photo_name = f"{face_id}.jpg"
        photo_path = os.path.join(self.images_dir, photo_name)
        if os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception:
                pass
        self.faces = [f for f in self.faces if f.get("id") != face_id]
        self._save()
        return True

    def match_face(self, embedding: np.ndarray, threshold: float = 0.48) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Computes Cosine Similarity against all registered faces.
        Returns (best_match_face, similarity_score). If similarity < threshold, returns (None, score).
        """
        if embedding is None or len(embedding) == 0 or not self.faces:
            return None, 0.0

        # Ensure L2 normalized
        norm = np.linalg.norm(embedding)
        if norm > 1e-6:
            query = embedding / norm
        else:
            query = embedding

        best_score = -1.0
        best_face = None

        for face in self.faces:
            face_emb = face.get("embedding")
            if not face_emb or len(face_emb) != len(query):
                continue
            f_vec = np.array(face_emb, dtype=np.float32)
            f_norm = np.linalg.norm(f_vec)
            if f_norm > 1e-6:
                f_vec = f_vec / f_norm
            similarity = float(np.dot(query, f_vec))
            if similarity > best_score:
                best_score = similarity
                best_face = face

        if best_face is not None and best_score >= threshold:
            return best_face, best_score
        return None, max(0.0, best_score)


class UniFaceManager:
    """Manages ONNX runtime instances for RetinaFace and ArcFace."""

    _instance: Optional["UniFaceManager"] = None

    def __init__(self):
        self._detector = None
        self._recognizer = None
        self._detector_name = "retinaface"
        self._init_models()

    @classmethod
    def get_instance(cls) -> "UniFaceManager":
        if cls._instance is None:
            cls._instance = UniFaceManager()
        return cls._instance

    def _init_models(self) -> None:
        try:
            from uniface.detection import RetinaFace
            from uniface.recognition import ArcFace
            logger.info("Initializing UniFace RetinaFace & ArcFace...")
            self._detector = RetinaFace(confidence_threshold=0.45)
            self._recognizer = ArcFace()
            logger.info("UniFace models loaded successfully!")
        except Exception as e:
            logger.warning(f"UniFace model initialization warning (will fallback if needed): {e}")

    def detect_faces(self, image_bgr: np.ndarray, conf_thresh: float = 0.45) -> List[Dict[str, Any]]:
        """
        Detects faces in image_bgr using RetinaFace.
        Returns list of detection dicts with x, y, width, height, confidence, landmarks.
        """
        if image_bgr is None or not hasattr(image_bgr, "shape"):
            return []

        if self._detector is None:
            # Fallback to OpenCV Haar cascade if UniFace ONNX is unavailable
            return self._fallback_haar_detect(image_bgr, conf_thresh)

        try:
            faces = self._detector.detect(image_bgr)
            detections = []
            for face in faces:
                conf = float(getattr(face, "confidence", 0.0))
                if conf < conf_thresh:
                    continue
                bbox = getattr(face, "bbox", None)
                if bbox is None or len(bbox) < 4:
                    continue
                x1, y1, x2, y2 = [float(v) for v in bbox[:4]]
                w = max(1.0, x2 - x1)
                h = max(1.0, y2 - y1)

                landmarks = []
                raw_lm = getattr(face, "landmarks", None)
                if raw_lm is not None:
                    try:
                        landmarks = [[float(pt[0]), float(pt[1])] for pt in raw_lm]
                    except Exception:
                        landmarks = []

                detections.append({
                    "class": "face",
                    "baseClass": "face",
                    "x": x1,
                    "y": y1,
                    "width": w,
                    "height": h,
                    "bbox": [x1, y1, w, h],
                    "confidence": conf,
                    "score": conf,
                    "kind": "detection",
                    "landmarks": landmarks,
                })
            return detections
        except Exception as e:
            logger.error(f"Error in UniFace detect_faces: {e}")
            return self._fallback_haar_detect(image_bgr, conf_thresh)

    def extract_embedding(self, image_bgr: np.ndarray, landmarks: Optional[List[List[float]]] = None) -> Optional[np.ndarray]:
        """Extracts 512-D L2-normalized face embedding using ArcFace."""
        if image_bgr is None or self._recognizer is None:
            return None
        try:
            lm_array = np.array(landmarks, dtype=np.float32) if landmarks and len(landmarks) >= 5 else None
            emb = self._recognizer.get_embedding(image_bgr, landmarks=lm_array)
            if emb is not None:
                norm = np.linalg.norm(emb)
                if norm > 1e-6:
                    emb = emb / norm
                return emb.astype(np.float32)
        except Exception as e:
            logger.error(f"Error in ArcFace extract_embedding: {e}")
        return None

    def _fallback_haar_detect(self, image_bgr: np.ndarray, conf_thresh: float) -> List[Dict[str, Any]]:
        """Fallback face detection using OpenCV Haar Cascades if ONNX is loading."""
        try:
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)
            boxes = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
            dets = []
            for (x, y, w, h) in boxes:
                dets.append({
                    "class": "face",
                    "baseClass": "face",
                    "x": float(x),
                    "y": float(y),
                    "width": float(w),
                    "height": float(h),
                    "bbox": [float(x), float(y), float(w), float(h)],
                    "confidence": 0.85,
                    "score": 0.85,
                    "kind": "detection",
                    "landmarks": [],
                })
            return dets
        except Exception as e:
            logger.error(f"Haar fallback error: {e}")
            return []


def get_uniface_manager() -> UniFaceManager:
    return UniFaceManager.get_instance()


def get_face_registry() -> UniFaceRegistry:
    return UniFaceRegistry.get_instance()


# ---------------------------------------------------------------------------
# Workflow Node Processors
# ---------------------------------------------------------------------------

def process_face_detector_node(
    project_node: Dict[str, Any],
    frame: np.ndarray,
) -> List[Dict[str, Any]]:
    """Runs Face Detection on frame and outputs detections with class='face'."""
    config = project_node.get("config", {})
    conf_thresh = float(config.get("confidenceThreshold", 0.45))
    min_size = float(config.get("minFaceSize", 20.0))

    mgr = get_uniface_manager()
    raw_faces = mgr.detect_faces(frame, conf_thresh=conf_thresh)

    filtered = []
    for f in raw_faces:
        if f["width"] >= min_size and f["height"] >= min_size:
            f["sourceNodeId"] = project_node.get("id")
            filtered.append(f)
    return filtered


def process_face_tracker_node(
    project_node: Dict[str, Any],
    frame: np.ndarray,
    detections: List[Dict[str, Any]],
    state: Dict[str, Any],
    now: float,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Tracks faces and matches them against UniFaceRegistry (Face Re-ID).
    Enriches detections with:
    - personName: "Budi Santoso" or "Tamu #1"
    - isEnrolled: True / False
    - similarity: float (e.g. 0.92)
    - trackId: int (stable Re-ID track ID)
    - showLandmarks: bool
    """
    config = project_node.get("config", {})
    node_id = str(project_node.get("id") or "face_tracker")
    sim_threshold = float(config.get("similarityThreshold", 0.48))
    unknown_prefix = str(config.get("unknownPrefix", "Tamu")).strip() or "Tamu"
    max_missing_seconds = max(1.0, float(config.get("maxMissingSeconds", 5.0)))
    show_landmarks = bool(config.get("showLandmarks", True))
    show_name_badge = bool(config.get("showNameBadge", True))

    registry = get_face_registry()
    mgr = get_uniface_manager()

    tracks: Dict[str, Dict[str, Any]] = state.setdefault("tracks", {})
    next_id: int = state.setdefault("next_track_id", 1)

    events: List[Dict[str, Any]] = []
    enriched_detections: List[Dict[str, Any]] = []

    h, w = frame.shape[:2] if frame is not None and hasattr(frame, "shape") else (480, 640)

    for det in detections:
        # Check if detection is a face or person
        cls_name = str(det.get("class", "")).lower()
        if cls_name != "face" and "face" not in cls_name and cls_name != "person":
            enriched_detections.append(det)
            continue

        box = (
            float(det.get("x", 0)),
            float(det.get("y", 0)),
            float(det.get("width", 0)),
            float(det.get("height", 0)),
        )
        x1 = max(0, int(box[0]))
        y1 = max(0, int(box[1]))
        x2 = min(w, int(box[0] + box[2]))
        y2 = min(h, int(box[1] + box[3]))

        landmarks = det.get("landmarks", [])

        # Extract embedding from face crop if frame is available
        emb = None
        if frame is not None and x2 > x1 and y2 > y1:
            face_crop = frame[y1:y2, x1:x2]
            emb = mgr.extract_embedding(face_crop, landmarks=landmarks)

        # 1. Match against Known Face Registry
        matched_face, similarity = registry.match_face(emb, threshold=sim_threshold)

        if matched_face is not None:
            person_name = matched_face["name"]
            person_role = matched_face.get("role", "Terdaftar")
            is_enrolled = True
            track_key = f"enrolled:{matched_face['id']}"
        else:
            person_name = ""
            person_role = "Tamu"
            is_enrolled = False
            track_key = None

        # 2. Dynamic Re-ID matching against active tracks if not in known gallery
        if track_key is None and emb is not None:
            best_t_sim = -1.0
            best_t_key = None
            for tk, tr in tracks.items():
                t_emb = tr.get("embedding")
                if t_emb is not None:
                    s = float(np.dot(emb, t_emb))
                    if s > best_t_sim and s >= sim_threshold:
                        best_t_sim = s
                        best_t_key = tk
            if best_t_key is not None:
                track_key = best_t_key
                similarity = best_t_sim

        # 3. New track allocation
        if track_key is None:
            track_id = next_id
            state["next_track_id"] = next_id + 1
            track_key = f"unknown:{track_id}"
            person_name = f"{unknown_prefix} #{track_id}"
        elif not person_name:
            track_id = tracks[track_key].get("trackId", next_id)
            person_name = f"{unknown_prefix} #{track_id}"
        else:
            track_id = tracks.get(track_key, {}).get("trackId", next_id)

        if track_key not in tracks:
            tracks[track_key] = {
                "trackId": track_id,
                "firstSeen": now,
                "lastSeen": now,
                "name": person_name,
                "isEnrolled": is_enrolled,
                "embedding": emb,
                "lastBox": box,
            }
            # Emit face identification event
            events.append({
                "kind": "face_identified",
                "event_type": "face_identified",
                "sourceNodeId": node_id,
                "trackId": track_id,
                "name": person_name,
                "isEnrolled": is_enrolled,
                "role": person_role,
                "similarity": round(similarity, 2),
                "timestamp": now,
                "message": f"Wajah teridentifikasi: '{person_name}' ({round(similarity*100):d}%)",
            })
        else:
            tracks[track_key]["lastSeen"] = now
            tracks[track_key]["lastBox"] = box
            if emb is not None:
                # Rolling feature update
                old_emb = tracks[track_key]["embedding"]
                tracks[track_key]["embedding"] = (0.8 * old_emb + 0.2 * emb) if old_emb is not None else emb

        # Enrich detection
        det["class"] = person_name
        det["baseClass"] = "face"
        det["personName"] = person_name
        det["faceRole"] = person_role
        det["isEnrolled"] = is_enrolled
        det["similarity"] = round(similarity, 2)
        det["trackId"] = track_id
        det["bbox"] = [float(box[0]), float(box[1]), float(box[2]), float(box[3])]
        det["score"] = float(det.get("confidence", 0.9))
        det["label"] = f"{person_name} ({round(similarity*100):d}%)"
        det["showLandmarks"] = show_landmarks
        det["showNameBadge"] = show_name_badge

        enriched_detections.append(det)

    # Evict stale tracks
    stale = [k for k, v in tracks.items() if (now - v.get("lastSeen", 0.0)) > max_missing_seconds]
    for k in stale:
        del tracks[k]

    return enriched_detections, events


def draw_face_landmarks_overlay(frame: np.ndarray, detections: List[Dict[str, Any]]) -> None:
    """Draws 5-point facial landmark dots and face identity badge on frame."""
    if frame is None or not hasattr(frame, "shape"):
        return

    for det in detections:
        # Landmarks: 5 dots
        landmarks = det.get("landmarks", [])
        if det.get("showLandmarks", True) and landmarks:
            for pt in landmarks:
                px, py = int(pt[0]), int(pt[1])
                cv2.circle(frame, (px, py), 3, (56, 189, 248), -1, cv2.LINE_AA)  # cyan dot
                cv2.circle(frame, (px, py), 4, (255, 255, 255), 1, cv2.LINE_AA)

        # Name / Re-ID Badge
        if det.get("showNameBadge", True) and det.get("personName"):
            name = det["personName"]
            is_enrolled = bool(det.get("isEnrolled", False))
            sim = det.get("similarity", 0.0)

            x = int(det.get("x", 0))
            y = int(det.get("y", 0))

            if is_enrolled:
                badge_text = f"👤 {name} ({int(sim * 100)}%)"
                badge_bgr = (16, 185, 129)  # green
            else:
                badge_text = f"👤 {name}"
                badge_bgr = (203, 138, 37)  # amber / blue

            font_scale = 0.42
            font_thick = 1
            ts, _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thick)

            bx1 = x
            by1 = max(18, y - 24)
            bx2 = x + ts[0] + 12
            by2 = by1 + ts[1] + 10

            cv2.rectangle(frame, (bx1, by1), (bx2, by2), (15, 23, 42), -1)
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), badge_bgr, 1, cv2.LINE_AA)
            cv2.putText(
                frame,
                badge_text,
                (bx1 + 6, by1 + ts[1] + 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),
                font_thick,
                cv2.LINE_AA,
            )
