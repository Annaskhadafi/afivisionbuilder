"""Lightweight ONNX OCR Engine (PaddleOCR Mobile PP-OCRv3/v4 ONNX).

Provides:
- Ultra-lightweight ONNX text detection (~2.4 MB) & recognition (~7.8 MB)
- High-speed CPU inference (~5-15ms per text crop)
- Multi-mode text extraction:
  1. Full-frame / ROI text detection + recognition
  2. Crop-from-detections mode (reads text inside upstream object bounding boxes: license_plate, label, packaging)
- Greedy CTC decoding with confidence scoring
- Character whitelist filtering (for license plates, serial numbers, container IDs)
- Seamless fallback when ONNX models are not yet downloaded
"""
from __future__ import annotations

import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

try:
    import onnxruntime as ort
    HAS_ORT = True
except ImportError:
    HAS_ORT = False


class OCREngine:
    """Manages ONNX inference sessions for text detection and text recognition."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.rec_model_path = str(
            config.get("recModelPath")
            or config.get("modelPath")
            or "data/models/ocr/ppocrv3_en_rec.onnx"
        ).strip()
        self.det_model_path = str(
            config.get("detModelPath")
            or "data/models/ocr/ppocrv3_det.onnx"
        ).strip()
        self.dict_path = str(
            config.get("dictPath")
            or "data/models/ocr/en_dict.txt"
        ).strip()

        self.det_session: Optional[Any] = None
        self.rec_session: Optional[Any] = None
        self.dict_chars: List[str] = []
        self._last_event_time: float = 0.0

        self._load_dictionary()
        self._load_sessions()

    def _load_dictionary(self) -> None:
        """Load character dictionary for CTC decoding."""
        if os.path.exists(self.dict_path):
            try:
                with open(self.dict_path, "r", encoding="utf-8") as f:
                    # Token 0 is blank in CTC, followed by dictionary lines, then space
                    chars = [line.strip("\r\n") for line in f.readlines()]
                    self.dict_chars = [""] + chars + [" "]
                    return
            except Exception:
                pass

        # Fallback default alphanumeric dictionary (ASCII Printable)
        ascii_chars = [chr(i) for i in range(32, 127)]
        self.dict_chars = [""] + ascii_chars + [" "]

    def _load_sessions(self) -> None:
        """Initialize ONNX Runtime inference sessions if models exist."""
        if not HAS_ORT:
            return

        providers = ["CPUExecutionProvider"]
        # Recognition model
        if os.path.exists(self.rec_model_path) and self.rec_session is None:
            try:
                self.rec_session = ort.InferenceSession(self.rec_model_path, providers=providers)
            except Exception:
                self.rec_session = None

        # Detection model
        if os.path.exists(self.det_model_path) and self.det_session is None:
            try:
                self.det_session = ort.InferenceSession(self.det_model_path, providers=providers)
            except Exception:
                self.det_session = None

    def detect_text_boxes(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect text bounding boxes in the frame.

        Returns list of (x, y, width, height).
        """
        h, w = frame.shape[:2]
        boxes: List[Tuple[int, int, int, int]] = []

        # 1. Use ONNX Detection Model if available
        if self.det_session is not None:
            try:
                det_h = int(np.ceil(h / 32) * 32)
                det_w = int(np.ceil(w / 32) * 32)
                resized = cv2.resize(frame, (det_w, det_h))
                mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
                std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
                norm = (resized.astype(np.float32) / 255.0 - mean) / std
                blob = np.transpose(norm, (2, 0, 1))[np.newaxis, ...]

                out = self.det_session.run(None, {"x": blob})[0]
                pred_map = out[0, 0]
                binary = (pred_map > 0.3).astype(np.uint8) * 255

                contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    if bw > 15 and bh > 5:
                        # DBNet outputs the shrunk text core; expand vertically by ~0.65x height to cover ascenders/descenders
                        pad_x = max(2, int(bw * 0.04))
                        pad_y = max(4, int(bh * 0.65))
                        orig_x = max(0, int((bx - pad_x) * w / det_w))
                        orig_y = max(0, int((by - pad_y) * h / det_h))
                        orig_w = min(w - orig_x, int((bw + 2 * pad_x) * w / det_w))
                        orig_h = min(h - orig_y, int((bh + 2 * pad_y) * h / det_h))
                        boxes.append((orig_x, orig_y, orig_w, orig_h))
                if boxes:
                    return boxes
            except Exception:
                pass

        # 2. Morphological gradient fallback proposer
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
            grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, morph_kernel)
            _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, morph_kernel)
            contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                # Filter text line aspect ratio & size
                if bw > 25 and bh > 10 and (bw / float(bh)) > 1.2:
                    boxes.append((bx, by, bw, bh))
        except Exception:
            pass

        return boxes

    def recognize_crop(self, crop: np.ndarray) -> Tuple[str, float]:
        """Recognize text in a cropped image region.

        Returns (recognized_text, confidence).
        """
        if crop is None or crop.size == 0:
            return "", 0.0

        ch, cw = crop.shape[:2]
        if ch < 5 or cw < 5:
            return "", 0.0

        if self.rec_session is not None:
            try:
                # Resize to target height 48 while preserving aspect ratio
                target_w = max(16, min(960, int(round(cw * 48.0 / ch))))
                resized = cv2.resize(crop, (target_w, 48))
                norm = (resized.astype(np.float32) / 255.0 - 0.5) / 0.5
                blob = np.transpose(norm, (2, 0, 1))[np.newaxis, ...]

                out = self.rec_session.run(None, {"x": blob})[0]  # [1, seq_len, num_classes]
                preds = np.argmax(out[0], axis=-1)
                max_probs = np.max(out[0], axis=-1)

                chars = []
                confs = []
                prev_idx = -1

                for idx, prob in zip(preds, max_probs):
                    if idx != 0 and idx != prev_idx:
                        if idx < len(self.dict_chars):
                            chars.append(self.dict_chars[idx])
                            confs.append(float(prob))
                    prev_idx = idx

                text = "".join(chars).strip()
                mean_conf = float(np.mean(confs)) if confs else 0.0
                return text, round(mean_conf, 3)
            except Exception:
                pass

        # Fallback heuristic string extractor if model is absent
        return "", 0.0

    def process_frame(
        self,
        frame: np.ndarray,
        existing_detections: Optional[List[Dict[str, Any]]] = None,
        node_id: str = "ocr_reader",
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Run OCR extraction pipeline on frame and/or detections.

        Returns:
            (new_text_detections, new_events)
        """
        crop_from_detections = bool(self.config.get("cropFromDetections", False))
        filter_classes_raw = str(self.config.get("filterClasses") or "").lower()
        filter_classes = {c.strip() for c in filter_classes_raw.split(",") if c.strip()}
        min_conf = float(self.config.get("minConfidence", 0.50) or 0.50)
        whitelist = str(self.config.get("characterWhitelist") or "").strip()
        cooldown = max(0.1, float(self.config.get("cooldownSeconds", 1.0) or 1.0))
        emit_events = bool(self.config.get("emitEvents", True))

        fh, fw = frame.shape[:2]
        text_detections: List[Dict[str, Any]] = []
        events: List[Dict[str, Any]] = []

        regions_to_ocr: List[Tuple[int, int, int, int]] = []

        if crop_from_detections and existing_detections:
            for det in existing_detections:
                det_cls = str(det.get("class", "")).strip().lower()
                if filter_classes and det_cls not in filter_classes:
                    continue
                # Extract box
                if "box" in det and isinstance(det["box"], (list, tuple)) and len(det["box"]) >= 4:
                    x1, y1, x2, y2 = det["box"][:4]
                    x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
                else:
                    x = int(det.get("x", 0))
                    y = int(det.get("y", 0))
                    w = int(det.get("width", 0))
                    h = int(det.get("height", 0))

                x = max(0, min(fw - 1, x))
                y = max(0, min(fh - 1, y))
                w = max(1, min(fw - x, w))
                h = max(1, min(fh - y, h))
                regions_to_ocr.append((x, y, w, h))
        else:
            # Full-frame text detection
            regions_to_ocr = self.detect_text_boxes(frame)

        now = time.time()
        for x, y, w, h in regions_to_ocr:
            crop = frame[y : y + h, x : x + w]
            text, conf = self.recognize_crop(crop)

            # Apply character whitelist if specified
            if whitelist and text:
                pattern = f"[^{re.escape(whitelist)}]"
                text = re.sub(pattern, "", text).strip()

            if not text or conf < min_conf:
                continue

            det_obj = {
                "class": "text",
                "text": text,
                "confidence": conf,
                "score": conf,
                "box": [float(x), float(y), float(x + w), float(y + h)],
                "x": float(x),
                "y": float(y),
                "width": float(w),
                "height": float(h),
                "sourceNodeId": node_id,
            }
            text_detections.append(det_obj)

            if emit_events and (now - self._last_event_time) >= cooldown:
                self._last_event_time = now
                events.append({
                    "type": "ocr_text_read",
                    "kind": "text_detected",
                    "text": text,
                    "confidence": conf,
                    "box": det_obj["box"],
                    "sourceNodeId": node_id,
                    "timestamp": now,
                })

        return text_detections, events


def run_ocr_pipeline(
    frame: np.ndarray,
    workflow: Dict[str, Any],
    existing_detections: List[Dict[str, Any]],
    node_states: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Helper invoked by engine runtime when an ocr_reader node is enabled."""
    all_text_dets: List[Dict[str, Any]] = []
    all_events: List[Dict[str, Any]] = []

    for node in workflow.get("nodes", []):
        if node.get("type") == "ocr_reader" and node.get("enabled", True):
            node_id = str(node.get("id", "ocr_reader"))
            engine_inst = node_states.get(f"_ocr_{node_id}")
            if engine_inst is None:
                config = node.get("config", {})
                engine_inst = OCREngine(config)
                node_states[f"_ocr_{node_id}"] = engine_inst

            text_dets, evts = engine_inst.process_frame(frame, existing_detections, node_id)
            all_text_dets.extend(text_dets)
            all_events.extend(evts)

    return all_text_dets, all_events
