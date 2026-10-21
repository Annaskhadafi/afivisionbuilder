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


def _calc_box_iou(box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]) -> float:
    """Computes IoU between two [x, y, w, h] bounding boxes."""
    x1_a, y1_a, w_a, h_a = box1
    x2_a, y2_a = x1_a + w_a, y1_a + h_a

    x1_b, y1_b, w_b, h_b = box2
    x2_b, y2_b = x1_b + w_b, y1_b + h_b

    inter_x1 = max(x1_a, x1_b)
    inter_y1 = max(y1_a, y1_b)
    inter_x2 = min(x2_a, x2_b)
    inter_y2 = min(y2_a, y2_b)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, w_a * h_a)
    area_b = max(0.0, w_b * h_b)
    union_area = area_a + area_b - inter_area

    if union_area <= 1e-6:
        return 0.0
    return float(inter_area / union_area)


class UniFaceRegistry:
    """Manages enrolled faces, avatar images, and 512-D ArcFace feature embeddings."""

    _instance: Optional["UniFaceRegistry"] = None

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or FACES_DIR
        self.images_dir = os.path.join(self.storage_dir, "images")
        self.registry_file = os.path.join(self.storage_dir, "registry.json")
        _ensure_storage_dirs(self.storage_dir, self.images_dir, self.registry_file)
        self.faces: List[Dict[str, Any]] = []
        self._last_mtime: float = 0.0
        self._load()

    @classmethod
    def get_instance(cls) -> "UniFaceRegistry":
        if cls._instance is None:
            cls._instance = UniFaceRegistry()
        return cls._instance

    def _ensure_fresh(self) -> None:
        try:
            if os.path.exists(self.registry_file):
                mtime = os.path.getmtime(self.registry_file)
                if mtime > getattr(self, "_last_mtime", 0.0):
                    self._load()
        except Exception:
            pass

    def _load(self) -> None:
        try:
            if os.path.exists(self.registry_file):
                self._last_mtime = os.path.getmtime(self.registry_file)
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self.faces = json.load(f)
                # Ensure all stored embeddings are flattened 1D lists of floats
                for face in self.faces:
                    raw_emb = face.get("embedding")
                    if raw_emb:
                        try:
                            arr = np.asarray(raw_emb, dtype=np.float32).flatten()
                            norm = np.linalg.norm(arr)
                            if norm > 1e-6:
                                arr = arr / norm
                            face["embedding"] = arr.tolist()
                        except Exception:
                            pass
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
            if os.path.exists(self.registry_file):
                self._last_mtime = os.path.getmtime(self.registry_file)
        except Exception as e:
            logger.error(f"Error saving face registry: {e}")

    def list_faces(self) -> List[Dict[str, Any]]:
        """Return public list of faces (excluding raw embedding arrays for lightweight API response)."""
        self._ensure_fresh()
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
        self._ensure_fresh()
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
                faces = mgr.detect_faces(final_img, conf_thresh=0.35)
                if not faces:
                    faces = mgr.detect_faces(final_img, conf_thresh=0.20)
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
                else:
                    # If detector found no face (e.g. tight crop or small avatar), use aligned resize
                    aligned_avatar = cv2.resize(final_img, (112, 112), interpolation=cv2.INTER_AREA)
                    emb_vec = mgr.extract_embedding(aligned_avatar, landmarks=None)
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

        if extracted_emb is not None:
            try:
                emb_arr = np.asarray(extracted_emb, dtype=np.float32).flatten()
                norm = np.linalg.norm(emb_arr)
                if norm > 1e-6:
                    emb_arr = emb_arr / norm
                extracted_emb = emb_arr.tolist()
            except Exception:
                pass

        record = {
            "id": face_id,
            "name": final_name.strip() if final_name else "Wajah Terdaftar",
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

    def match_face(self, embedding: Any, threshold: float = 0.48) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Computes Cosine Similarity against all registered faces.
        Returns (best_match_face, similarity_score). If similarity < threshold, returns (None, score).
        Handles both 1D and 2D embedding inputs safely.
        """
        self._ensure_fresh()
        if embedding is None:
            return None, 0.0

        try:
            query = np.asarray(embedding, dtype=np.float32).flatten()
        except Exception:
            return None, 0.0

        if len(query) == 0 or not self.faces:
            return None, 0.0

        # Ensure L2 normalized
        norm = np.linalg.norm(query)
        if norm > 1e-6:
            query = query / norm

        best_score = -1.0
        best_face = None

        for face in self.faces:
            face_emb = face.get("embedding")
            if not face_emb:
                continue
            try:
                f_vec = np.asarray(face_emb, dtype=np.float32).flatten()
            except Exception:
                continue
            if len(f_vec) != len(query):
                continue
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
    """Manages ONNX runtime instances for RetinaFace, ArcFace, MiniFASNet, and EDifFIQA."""

    _instance: Optional["UniFaceManager"] = None

    def __init__(self):
        self._detector = None
        self._recognizer = None
        self._spoofer = None
        self._quality_estimator = None
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
            logger.info("UniFace detector and recognizer loaded successfully!")
        except Exception as e:
            logger.warning(f"UniFace model initialization warning (will fallback if needed): {e}")

        try:
            from uniface.spoofing import MiniFASNet
            from uniface.constants import MiniFASNetWeights
            self._spoofer = MiniFASNet(model_name=MiniFASNetWeights.V2)
            logger.info("UniFace MiniFASNet anti-spoofing model loaded successfully!")
        except Exception as e:
            logger.warning(f"UniFace MiniFASNet initialization warning: {e}")

        try:
            from uniface.quality import EDifFIQA
            from uniface.constants import EDifFIQAWeights
            self._quality_estimator = EDifFIQA(model_name=EDifFIQAWeights.T)
            logger.info("UniFace EDifFIQA face quality model loaded successfully!")
        except Exception as e:
            logger.warning(f"UniFace EDifFIQA initialization warning: {e}")

    def get_spoofer(self):
        if self._spoofer is None:
            try:
                from uniface.spoofing import MiniFASNet
                from uniface.constants import MiniFASNetWeights
                self._spoofer = MiniFASNet(model_name=MiniFASNetWeights.V2)
            except Exception as e:
                logger.error(f"Failed to load MiniFASNet on demand: {e}")
        return self._spoofer

    def get_quality_estimator(self):
        if self._quality_estimator is None:
            try:
                from uniface.quality import EDifFIQA
                from uniface.constants import EDifFIQAWeights
                self._quality_estimator = EDifFIQA(model_name=EDifFIQAWeights.T)
            except Exception as e:
                logger.error(f"Failed to load EDifFIQA on demand: {e}")
        return self._quality_estimator

    def predict_anti_spoof(self, image_bgr: np.ndarray, bbox_xyxy: list | np.ndarray) -> Tuple[bool, float]:
        """
        Runs anti-spoofing check using MiniFASNet.
        Returns (is_real, confidence).
        """
        if image_bgr is None or not hasattr(image_bgr, "shape"):
            return True, 1.0

        spoofer = self.get_spoofer()
        if spoofer is None:
            return True, 1.0

        try:
            result = spoofer.predict(image_bgr, bbox_xyxy)
            return bool(result.is_real), float(result.confidence)
        except Exception as e:
            logger.warning(f"Error in predict_anti_spoof: {e}")
            return True, 1.0

    def predict_face_quality(self, image_bgr: np.ndarray, landmarks: Optional[Any] = None) -> float:
        """
        Predicts face image quality score (0.0 - 1.0) using EDifFIQA.
        Higher score = sharper, clearer, and better frontal quality.
        """
        if image_bgr is None or not hasattr(image_bgr, "shape"):
            return 0.5

        estimator = self.get_quality_estimator()
        if estimator is None:
            return 0.5

        try:
            if landmarks is not None and len(landmarks) >= 5:
                lm_arr = np.asarray(landmarks, dtype=np.float32)[:5]
                result = estimator.predict(image_bgr, lm_arr)
                return float(result.score)
            else:
                gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY) if len(image_bgr.shape) == 3 else image_bgr
                blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                norm_score = max(0.1, min(0.95, blur_var / 350.0))
                return norm_score
        except Exception as e:
            logger.warning(f"Error in predict_face_quality: {e}")
            return 0.5

    def align_face(self, image_bgr: np.ndarray, landmarks: Any, size: int = 112) -> Optional[np.ndarray]:
        """
        Aligns face using 5-point facial landmarks and affine transformation to standard 112x112 size.
        """
        if image_bgr is None or landmarks is None or len(landmarks) < 5:
            return None
        try:
            from uniface.face_utils import face_alignment
            lm_arr = np.asarray(landmarks, dtype=np.float32)[:5]
            aligned, _ = face_alignment(image_bgr, lm_arr, image_size=size)
            return aligned
        except Exception as e:
            logger.warning(f"Error in align_face: {e}")
            return None

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
        """Extracts 512-D L2-normalized 1D face embedding using ArcFace."""
        if image_bgr is None or self._recognizer is None:
            return None
        try:
            lm_array = np.array(landmarks, dtype=np.float32) if landmarks and len(landmarks) >= 5 else None
            emb = self._recognizer.get_embedding(image_bgr, landmarks=lm_array)
            if emb is not None:
                emb = np.asarray(emb, dtype=np.float32).flatten()
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
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Runs Face Detection on frame with optional Anti-Spoofing (MiniFASNet).
    Outputs (detections, events).
    """
    config = project_node.get("config", {})
    conf_thresh = float(config.get("confidenceThreshold", 0.45))
    min_size = float(config.get("minFaceSize", 20.0))
    enable_anti_spoofing = bool(config.get("enableAntiSpoofing", False))
    anti_spoof_thresh = float(config.get("antiSpoofThreshold", 0.60))
    filter_spoof = bool(config.get("filterSpoof", True))

    mgr = get_uniface_manager()
    raw_faces = mgr.detect_faces(frame, conf_thresh=conf_thresh)

    filtered = []
    events = []
    node_id = str(project_node.get("id") or "face_detector")

    h, w = frame.shape[:2] if frame is not None and hasattr(frame, "shape") else (480, 640)

    for f in raw_faces:
        if f["width"] < min_size or f["height"] < min_size:
            continue

        f["sourceNodeId"] = node_id

        # Anti-Spoofing Verification
        if enable_anti_spoofing and frame is not None:
            x1 = max(0, int(f["x"]))
            y1 = max(0, int(f["y"]))
            x2 = min(w, int(f["x"] + f["width"]))
            y2 = min(h, int(f["y"] + f["height"]))
            bbox_xyxy = [x1, y1, x2, y2]

            is_real, spoof_conf = mgr.predict_anti_spoof(frame, bbox_xyxy)
            is_fake = (not is_real) and (spoof_conf >= anti_spoof_thresh)

            if is_fake:
                f["isReal"] = False
                f["antiSpoofStatus"] = "spoof"
                f["antiSpoofConfidence"] = spoof_conf
                events.append({
                    "kind": "face_spoof_detected",
                    "event_type": "face_spoof_detected",
                    "title": "Percobaan Face Spoof Terdeteksi",
                    "confidence": spoof_conf,
                    "bbox": [f["x"], f["y"], f["width"], f["height"]],
                    "sourceNodeId": node_id,
                    "timestamp": time.time(),
                })
                # If filterSpoof is active, drop fake face so it doesn't propagate
                if filter_spoof:
                    continue
            else:
                f["isReal"] = True
                f["antiSpoofStatus"] = "real"
                f["antiSpoofConfidence"] = spoof_conf

        filtered.append(f)

    if enable_anti_spoofing:
        return filtered, events
    return filtered


def process_face_crop_node(
    project_node: Dict[str, Any],
    frame: np.ndarray,
    detections: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Crops detected faces with optional 5-point alignment or padding crop,
    computes face image quality scores via eDifFIQA, and produces crop batches.
    Returns (crop_items, events).
    """
    config = project_node.get("config", {})
    align_faces = bool(config.get("alignFaces", True))
    padding_percent = float(config.get("paddingPercent", 0.15))
    assess_quality = bool(config.get("assessQuality", True))
    min_quality_score = float(config.get("minQualityScore", 0.40))
    filter_low_quality = bool(config.get("filterLowQuality", False))
    max_crops = max(1, int(config.get("maxCrops", 16)))
    show_quality_chip = bool(config.get("showQualityChip", True))

    mgr = get_uniface_manager()
    crops = []
    events = []

    if frame is None or not hasattr(frame, "shape"):
        return crops, events

    h, w = frame.shape[:2]
    crop_idx = 0

    for det in detections:
        cls_name = str(det.get("class", "")).lower()
        # Accept face detections or objects that contain face landmarks
        if cls_name != "face" and "face" not in cls_name and not det.get("landmarks"):
            continue

        if crop_idx >= max_crops:
            break

        box = det.get("bbox") or [
            float(det.get("x", 0)),
            float(det.get("y", 0)),
            float(det.get("width", 0)),
            float(det.get("height", 0)),
        ]
        bx, by, bw, bh = [float(v) for v in box[:4]]
        landmarks = det.get("landmarks", [])

        # Assess Face Image Quality via eDifFIQA
        quality_score = 0.5
        if assess_quality:
            if landmarks and len(landmarks) >= 5:
                quality_score = mgr.predict_face_quality(frame, landmarks)
            else:
                x1 = max(0, int(bx))
                y1 = max(0, int(by))
                x2 = min(w, int(bx + bw))
                y2 = min(h, int(by + bh))
                if x2 > x1 and y2 > y1:
                    quality_score = mgr.predict_face_quality(frame[y1:y2, x1:x2], None)
            det["faceQualityScore"] = quality_score
            det["qualityScore"] = quality_score

        if filter_low_quality and quality_score < min_quality_score:
            continue

        # Perform Cropping (Aligned or Padded Bounding Box)
        crop_img = None
        if align_faces and landmarks and len(landmarks) >= 5:
            crop_img = mgr.align_face(frame, landmarks, size=112)

        if crop_img is None:
            # Fallback / Padded crop
            pad_w = int(bw * padding_percent)
            pad_h = int(bh * padding_percent)
            x1 = max(0, int(bx - pad_w))
            y1 = max(0, int(by - pad_h))
            x2 = min(w, int(bx + bw + pad_w))
            y2 = min(h, int(by + bh + pad_h))
            if x2 > x1 and y2 > y1:
                crop_img = frame[y1:y2, x1:x2].copy()

        if crop_img is not None and crop_img.size > 0:
            det["showQualityChip"] = show_quality_chip
            crops.append({
                "frame": crop_img,
                "bounds": [int(bx), int(by), int(bw), int(bh)],
                "cropIndex": crop_idx,
                "detection": det,
                "qualityScore": quality_score,
                "sourceNodeId": project_node.get("id"),
            })
            crop_idx += 1

    return crops, events


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

    if isinstance(detections, tuple) and len(detections) >= 1:
        detections = detections[0]

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

        # Extract embedding from face
        emb = None
        if frame is not None and x2 > x1 and y2 > y1:
            raw_emb = None
            # Method A: Landmarks are in frame coordinates. Passing frame and landmarks aligns face accurately.
            if landmarks and len(landmarks) >= 5:
                raw_emb = mgr.extract_embedding(frame, landmarks=landmarks)

            # Method B: Fallback - crop face and shift landmarks relative to crop
            if raw_emb is None:
                face_crop = frame[y1:y2, x1:x2]
                if face_crop.size > 0:
                    if landmarks and len(landmarks) >= 5:
                        shifted_lm = [[float(pt[0]) - x1, float(pt[1]) - y1] for pt in landmarks]
                        raw_emb = mgr.extract_embedding(face_crop, landmarks=shifted_lm)
                    if raw_emb is None:
                        # Fallback without landmarks: resize crop to 112x112
                        aligned_crop = cv2.resize(face_crop, (112, 112), interpolation=cv2.INTER_AREA)
                        raw_emb = mgr.extract_embedding(aligned_crop, landmarks=None)

            if raw_emb is not None:
                emb = np.asarray(raw_emb, dtype=np.float32).flatten()

        # 1. Match against Known Face Registry
        matched_face, similarity = registry.match_face(emb, threshold=sim_threshold)

        if matched_face is not None:
            person_name = matched_face["name"]
            person_role = matched_face.get("role", "Terdaftar")
            is_enrolled = True
            track_key = f"enrolled:{matched_face['id']}"

            # Seamless promotion: Remove any previous unknown track that overlaps with this enrolled face
            overlapping_keys = [
                tk for tk, tr in tracks.items()
                if tk.startswith("unknown:") and tr.get("lastBox") and _calc_box_iou(box, tr["lastBox"]) > 0.35
            ]
            for ok in overlapping_keys:
                del tracks[ok]
        else:
            person_name = ""
            person_role = "Tamu"
            is_enrolled = False
            track_key = None

        # 2. Dynamic Re-ID matching against active tracks if not in known gallery
        if track_key is None and emb is not None:
            best_t_sim = -1.0
            best_t_key = None
            emb_vec = np.asarray(emb, dtype=np.float32).flatten()
            for tk, tr in tracks.items():
                t_emb = tr.get("embedding")
                if t_emb is not None:
                    try:
                        t_vec = np.asarray(t_emb, dtype=np.float32).flatten()
                        if len(t_vec) == len(emb_vec):
                            s = float(np.dot(emb_vec, t_vec))
                            if s > best_t_sim and s >= sim_threshold:
                                best_t_sim = s
                                best_t_key = tk
                    except Exception:
                        continue
            if best_t_key is not None:
                track_key = best_t_key
                similarity = best_t_sim

        # 2b. Spatial IoU Fallback tracking for continuous video frames
        # If Re-ID didn't match (e.g. lighting variation or angle), associate with existing track in nearby position
        if track_key is None:
            best_iou = 0.0
            best_iou_key = None
            for tk, tr in tracks.items():
                if tr.get("lastBox"):
                    iou = _calc_box_iou(box, tr["lastBox"])
                    if iou > best_iou and iou >= 0.35:
                        best_iou = iou
                        best_iou_key = tk
            if best_iou_key is not None:
                track_key = best_iou_key
                similarity = tracks[track_key].get("similarity", 0.80)

        # 3. Track allocation & identity resolution
        if track_key is None:
            track_id = next_id
            state["next_track_id"] = next_id + 1
            track_key = f"unknown:{track_id}"
            person_name = f"{unknown_prefix} #{track_id}"
        elif not person_name:
            # Preserve existing track identity
            track_id = tracks[track_key].get("trackId", next_id)
            person_name = tracks[track_key].get("name") or f"{unknown_prefix} #{track_id}"
            is_enrolled = bool(tracks[track_key].get("isEnrolled", False))
            person_role = tracks[track_key].get("role", "Tamu")
        else:
            track_id = tracks.get(track_key, {}).get("trackId", next_id)

        if track_key not in tracks:
            tracks[track_key] = {
                "trackId": track_id,
                "firstSeen": now,
                "lastSeen": now,
                "name": person_name,
                "role": person_role,
                "isEnrolled": is_enrolled,
                "similarity": similarity,
                "embedding": np.asarray(emb, dtype=np.float32).flatten() if emb is not None else None,
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
            tracks[track_key]["similarity"] = similarity
            if is_enrolled:
                tracks[track_key]["isEnrolled"] = True
                tracks[track_key]["name"] = person_name
                tracks[track_key]["role"] = person_role
            if emb is not None:
                # Rolling feature update
                emb_vec = np.asarray(emb, dtype=np.float32).flatten()
                old_emb = tracks[track_key].get("embedding")
                if old_emb is not None:
                    try:
                        old_vec = np.asarray(old_emb, dtype=np.float32).flatten()
                        if len(old_vec) == len(emb_vec):
                            new_vec = 0.8 * old_vec + 0.2 * emb_vec
                            norm = np.linalg.norm(new_vec)
                            if norm > 1e-6:
                                new_vec = new_vec / norm
                            tracks[track_key]["embedding"] = new_vec
                        else:
                            tracks[track_key]["embedding"] = emb_vec
                    except Exception:
                        tracks[track_key]["embedding"] = emb_vec
                else:
                    tracks[track_key]["embedding"] = emb_vec

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
    """Draws 5-point facial landmark dots, anti-spoof warnings, quality chips, and face identity badges."""
    if frame is None or not hasattr(frame, "shape"):
        return

    h, w = frame.shape[:2]

    for det in detections:
        box = det.get("bbox") or [
            float(det.get("x", 0)),
            float(det.get("y", 0)),
            float(det.get("width", 0)),
            float(det.get("height", 0)),
        ]
        x1 = max(0, min(w - 1, int(box[0])))
        y1 = max(0, min(h - 1, int(box[1])))
        x2 = max(0, min(w - 1, int(box[0] + box[2])))
        y2 = max(0, min(h - 1, int(box[1] + box[3])))
        bbox_xyxy = [x1, y1, x2, y2]

        # 1. Anti-Spoofing Visual Warning (if fake face not dropped)
        is_spoof = (det.get("isReal") is False) or (det.get("antiSpoofStatus") == "spoof")
        if is_spoof:
            spoof_conf = float(det.get("antiSpoofConfidence", 1.0))
            # Draw red corner box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 239), 2, cv2.LINE_AA)
            badge_text = f"SPOOF ({int(spoof_conf * 100)}%)"
            ts, _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(frame, (x1, max(16, y1 - 22)), (x1 + ts[0] + 12, max(16, y1 - 22) + ts[1] + 8), (0, 0, 200), -1)
            cv2.putText(frame, badge_text, (x1 + 6, max(16, y1 - 22) + ts[1] + 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # 2. Face Quality Score Chip (eDifFIQA)
        quality_score = det.get("faceQualityScore")
        if quality_score is None:
            quality_score = det.get("qualityScore")

        if quality_score is not None and det.get("showQualityChip", True) and not is_spoof:
            try:
                from uniface.draw import draw_quality_score
                draw_quality_score(frame, bbox_xyxy, float(quality_score), draw_bbox=True, corner_bbox=True, low_threshold=0.4, high_threshold=0.6)
            except Exception:
                # Fallback manual score chip
                q_val = float(quality_score)
                q_col = (16, 185, 129) if q_val >= 0.6 else ((0, 165, 255) if q_val >= 0.4 else (0, 0, 239))
                q_text = f"Q:{q_val:.2f}"
                cv2.putText(frame, q_text, (x1, min(h - 5, y2 + 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, q_col, 1, cv2.LINE_AA)

        # 3. Landmarks: 5 dots
        landmarks = det.get("landmarks", [])
        if det.get("showLandmarks", True) and landmarks and not is_spoof:
            for pt in landmarks:
                px, py = int(pt[0]), int(pt[1])
                cv2.circle(frame, (px, py), 3, (56, 189, 248), -1, cv2.LINE_AA)  # cyan dot
                cv2.circle(frame, (px, py), 4, (255, 255, 255), 1, cv2.LINE_AA)

        # 4. Name / Re-ID Badge
        if det.get("showNameBadge", True) and det.get("personName") and not is_spoof:
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
