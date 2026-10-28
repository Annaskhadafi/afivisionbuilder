"""
Dedicated License Plate Recognition (LPR / ANPR) & Access Control Module:
- Automatic Number Plate Recognition optimized for vehicles (trucks, cars, logistics fleets).
- Indonesian RI standard plate syntax regex normalization & character disambiguation.
- Temporal rolling consensus across N frames per vehicle track_id.
- Whitelist / Blacklist access policy evaluation and automated gate event emission.
"""

from collections import Counter
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


# Indonesia Plate Regex Pattern: e.g. "B 1234 XYZ", "KT 8888 AA", "AB 123 C"
RI_PLATE_PATTERN = re.compile(r"^([A-Z]{1,2})\s+([0-9]{1,4})\s+([A-Z]{1,3})$")
GENERIC_ALPHANUM_PATTERN = re.compile(r"^[A-Z0-9]{4,10}$")


def normalize_indonesia_plate(raw_text: str) -> Tuple[str, bool]:
    """
    Cleans and standardizes Indonesian license plate syntax.
    Handles common OCR ambiguities:
    - Middle segment (must be numeric): 'O'->'0', 'I'->'1', 'S'->'5', 'B'->'8'
    - Outer segments (must be alphabetic): '0'->'O', '1'->'I', '8'->'B', '5'->'S'
    """
    raw_clean = str(raw_text or "").strip().upper()
    parts = raw_clean.split()
    if len(parts) == 3:
        prefix, number, suffix = parts
    else:
        cleaned = re.sub(r"[^A-Za-z0-9]", "", raw_clean)
        if not cleaned or len(cleaned) < 4:
            return cleaned, False

        # Match 1-2 letters, 1-4 numbers, 1-3 letters
        m = re.match(r"^([A-Z]{1,2})([0-9OISB]{1,4})([A-Z0-9]{1,3})$", cleaned)
        if not m:
            m = re.match(r"^([A-Z0-9]{1,2})([0-9]{1,4})([A-Z]{1,3})$", cleaned)
        if not m:
            return cleaned, bool(GENERIC_ALPHANUM_PATTERN.match(cleaned))
        prefix, number, suffix = m.groups()

    # Disambiguate prefix letters (must be alphabetic)
    p_fixed = prefix.replace("0", "O").replace("1", "I").replace("8", "B")
    # Disambiguate middle numbers (must be numeric)
    n_fixed = number.replace("O", "0").replace("I", "1").replace("S", "5").replace("B", "8")
    # Disambiguate suffix letters (must be alphabetic)
    s_fixed = suffix.replace("0", "O").replace("1", "I").replace("8", "B")

    formatted = f"{p_fixed} {n_fixed} {s_fixed}"
    is_valid = bool(RI_PLATE_PATTERN.match(formatted))
    return (formatted, is_valid) if is_valid else (re.sub(r"[^A-Za-z0-9]", "", raw_clean), is_valid)


def enhance_plate_crop(crop: np.ndarray) -> np.ndarray:
    """Enhances contrast and sharpness for vehicle plate reading (CLAHE)."""
    if crop is None or crop.size == 0:
        return crop
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return enhanced


def process_license_plates(
    frame: Any,
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    now: Optional[float] = None,
    node_id: str = "lpr_license_plate",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Recognizes license plates from vehicle detections or plate crops.

    Returns:
        (augmented_detections, access_events)
    """
    if state is None:
        state = {}
    if now is None:
        now = time.monotonic()

    vehicle_classes = str(config.get("vehicleClasses", "truck, car, pickup, vehicle")).strip().lower()
    allowed_classes = [c.strip().lower() for c in vehicle_classes.split(",") if c.strip()]
    if not allowed_classes or "all" in allowed_classes:
        allowed_classes = []

    whitelist_raw = str(config.get("whitelist", "")).strip().upper()
    whitelist = {re.sub(r"\s+", "", p) for p in whitelist_raw.split(",") if p.strip()}

    blacklist_raw = str(config.get("blacklist", "")).strip().upper()
    blacklist = {re.sub(r"\s+", "", p) for p in blacklist_raw.split(",") if p.strip()}

    voting_window = max(1, int(config.get("temporalVotingFrames", 5)))
    min_confidence = float(config.get("minConfidence", 0.65))
    cooldown_seconds = float(config.get("gateCooldownSeconds", 10.0))

    tracks_mem = state.setdefault("_lpr_tracks", {})

    augmented = []
    events = []

    for det in detections:
        cls_name = str(det.get("class", "")).strip().lower()
        if allowed_classes and cls_name not in allowed_classes and cls_name != "license_plate":
            augmented.append(det)
            continue

        bbox = det.get("bbox")
        if not bbox and "x" in det and "width" in det:
            bbox = [det["x"], det["y"], det["width"], det["height"]]
        if not bbox or len(bbox) < 4:
            augmented.append(det)
            continue

        track_id = det.get("trackId", det.get("track_id", det.get("id")))
        # Untracked vehicles must not share a temporal voting buffer.
        t_data = tracks_mem.setdefault(track_id, {
            "buffer": [],
            "consensus": "",
            "last_event_time": 0.0,
            "last_status": "UNKNOWN",
        }) if track_id is not None else {"buffer": [], "consensus": "", "last_event_time": 0.0, "last_status": "UNKNOWN"}

        # Check if plate text already extracted by upstream OCR or attribute
        plate_text_raw = str(
            det.get("plate_text")
            or det.get("attributes", {}).get("plate_number")
            or det.get("attributes", {}).get("text")
            or det.get("ocr_text")
            or ""
        ).strip()

        # If empty and frame is available, try fast local OCR heuristic or fallback
        if not plate_text_raw and frame is not None and hasattr(frame, "shape"):
            ocr_eng = state.get("_ocr_engine")
            if ocr_eng is None:
                try:
                    from ocr_engine import OCREngine
                    ocr_eng = OCREngine(config)
                    state["_ocr_engine"] = ocr_eng
                except Exception:
                    ocr_eng = None
            if ocr_eng:
                try:
                    ocr_res, _ = ocr_eng.process_frame(frame, [det], node_id)
                    if ocr_res:
                        plate_text_raw = str(ocr_res[0].get("attributes", {}).get("text", "")).strip()
                except Exception:
                    pass

        if plate_text_raw:
            cleaned_plate, is_valid = normalize_indonesia_plate(plate_text_raw)
            if cleaned_plate:
                t_data["buffer"].append(cleaned_plate)
                if len(t_data["buffer"]) > voting_window:
                    t_data["buffer"].pop(0)

                # Majority vote
                counts = Counter(t_data["buffer"])
                most_common_plate, vote_cnt = counts.most_common(1)[0]
                t_data["consensus"] = most_common_plate

        consensus_plate = t_data.get("consensus", "")
        clean_key = re.sub(r"\s+", "", consensus_plate)

        # Access policy evaluation
        access_status = "UNKNOWN"
        if clean_key:
            if clean_key in blacklist:
                access_status = "BLACKLISTED"
            elif clean_key in whitelist:
                access_status = "AUTHORIZED"
            else:
                access_status = "UNREGISTERED"

        t_data["last_status"] = access_status

        det_copy = dict(det)
        attrs = dict(det_copy.get("attributes") or {})
        attrs["plate_number"] = consensus_plate
        attrs["plate_access_status"] = access_status
        det_copy["attributes"] = attrs
        det_copy["plateNumber"] = consensus_plate
        det_copy["plateAccessStatus"] = access_status
        augmented.append(det_copy)

        # Trigger access event if plate is recognized
        if consensus_plate and (now - t_data.get("last_event_time", 0) >= cooldown_seconds):
            t_data["last_event_time"] = now
            if access_status == "BLACKLISTED":
                events.append({
                    "event_type": "SECURITY_ALERT_BLACKLIST",
                    "type": "SECURITY_ALERT_BLACKLIST",
                    "severity": "CRITICAL",
                    "message": f"⛔ KENDARAAN TERLARANG (BLACKLIST): Plat {consensus_plate} terdeteksi di gerbang!",
                    "zoneName": "Gate Access",
                    "track_id": track_id,
                    "plate_number": consensus_plate,
                    "access_status": access_status,
                    "timestamp": now,
                })
            elif access_status == "AUTHORIZED":
                events.append({
                    "event_type": "GATE_ACCESS_GRANTED",
                    "type": "GATE_ACCESS_GRANTED",
                    "severity": "INFO",
                    "message": f"✅ AKSES DIIZINKAN (WHITELIST): Plat {consensus_plate} berhasil diverifikasi.",
                    "zoneName": "Gate Access",
                    "track_id": track_id,
                    "plate_number": consensus_plate,
                    "access_status": access_status,
                    "timestamp": now,
                })
            else:
                events.append({
                    "event_type": "VEHICLE_ARRIVED",
                    "type": "VEHICLE_ARRIVED",
                    "severity": "INFO",
                    "message": f"ℹ️ Kendaraan Masuk: Plat {consensus_plate} (Belum Terdaftar di Whitelist).",
                    "zoneName": "Gate Access",
                    "track_id": track_id,
                    "plate_number": consensus_plate,
                    "access_status": access_status,
                    "timestamp": now,
                })

    return augmented, events


def draw_license_plate_badges(frame: np.ndarray, detections: List[Dict[str, Any]]) -> None:
    """Draws a clean license plate badge overlay directly on vehicle bounding box."""
    if frame is None or not hasattr(frame, "shape"):
        return
    fh, fw = frame.shape[:2]
    for det in detections:
        plate = det.get("plateNumber")
        if not plate:
            continue
        bbox = det.get("bbox")
        if not bbox and "x" in det and "width" in det:
            bbox = [det["x"], det["y"], det["width"], det["height"]]
        if not bbox or len(bbox) < 4:
            continue
        x, y, w, h = bbox
        x1, y1 = int(round(x)), int(round(y))

        status = det.get("plateAccessStatus", "UNKNOWN")
        badge_color = (34, 197, 94) if status == "AUTHORIZED" else (
            (239, 68, 68) if status == "BLACKLISTED" else (15, 23, 42)
        )
        tag = f" {plate} "
        badge_y = max(20, y1 + int(round(h)) + 18)
        tw = len(tag) * 8 + 10
        cv2.rectangle(frame, (x1, badge_y - 16), (x1 + tw, badge_y), badge_color, -1)
        cv2.rectangle(frame, (x1, badge_y - 16), (x1 + tw, badge_y), (255, 255, 255), 1)
        cv2.putText(frame, tag, (x1 + 4, badge_y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
