"""PPE (Personal Protective Equipment) Compliance Matrix Node for AFI Vision Builder.

Mengevaluasi kelengkapan Alat Pelindung Diri (K3) pekerja konstruksi & pabrik
(Helm, Rompi Reflektif, Sepatu Safety, Sarung Tangan) dengan analisis asosiasi spasial
antara deteksi pekerja ('person') dan komponen APD pelindung.
"""

from __future__ import annotations

import datetime
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("afi.ppe_compliance")

# Pemetaan sinonim dan kelas APD umum
PPE_SYNONYMS = {
    "helmet": ["helmet", "hard_hat", "safety_helmet", "hardhat", "cap"],
    "vest": ["vest", "safety_vest", "reflective_vest", "hi_vis", "hivis", "hi_vis_vest"],
    "boots": ["boots", "safety_boots", "shoes", "safety_shoes"],
    "gloves": ["gloves", "safety_gloves"],
    "mask": ["mask", "face_mask", "respirator"],
}


def _bbox_intersection_ratio(boxA: List[float], boxB: List[float]) -> float:
    """Menghitung rasio luas irisan boxA dan boxB terhadap luas boxB."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    inter_w = max(0.0, xB - xA)
    inter_h = max(0.0, yB - yA)
    inter_area = inter_w * inter_h

    areaB = max(1.0, boxB[2] * boxB[3])
    return inter_area / areaB


def _get_anatomical_subzone(person_bbox: List[float], zone_type: str) -> List[float]:
    """Mengembalikan sub-kotak zona anatomi tubuh pekerja."""
    x, y, w, h = person_bbox[:4]
    if zone_type == "helmet":
        # Zona kepala: dari sedikit di atas kepala s/d 35% tinggi tubuh
        return [x - w * 0.1, y - h * 0.1, w * 1.2, h * 0.45]
    elif zone_type == "vest":
        # Zona torso: 18% s/d 75% tinggi tubuh
        return [x - w * 0.05, y + h * 0.18, w * 1.1, h * 0.57]
    elif zone_type == "boots":
        # Zona kaki: 68% s/d 105% tinggi tubuh
        return [x - w * 0.1, y + h * 0.68, w * 1.2, h * 0.38]
    elif zone_type == "gloves":
        # Rentang lengan kiri dan kanan
        return [x - w * 0.25, y + h * 0.3, w * 1.5, h * 0.5]
    # Default ke seluruh badan
    return [x, y, w, h]


class PPEComplianceMatrix:
    """Mesin evaluator kepatuhan APD / K3 terpadu."""

    def __init__(self, node_id: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.config = config or {}
        self.required_ppe = [str(x).lower() for x in self.config.get("requiredPPE", ["helmet", "vest"])]
        if not self.required_ppe:
            self.required_ppe = ["helmet", "vest"]
        self.min_compliance_score = float(self.config.get("minComplianceScore", 70.0))
        self.alarm_cooldown = float(self.config.get("alarmCooldownSeconds", 5.0))
        self.last_alarm_time: Dict[str, float] = {}

    def update_config(self, config: Dict[str, Any]) -> None:
        self.config.update(config)
        self.required_ppe = [str(x).lower() for x in self.config.get("requiredPPE", ["helmet", "vest"])]
        if not self.required_ppe:
            self.required_ppe = ["helmet", "vest"]
        self.min_compliance_score = float(self.config.get("minComplianceScore", 70.0))
        self.alarm_cooldown = float(self.config.get("alarmCooldownSeconds", 5.0))

    def evaluate(
        self,
        detections: List[Dict[str, Any]],
        now: Optional[float] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        current_time = now if now is not None else time.time()
        events = []

        # Pisahkan pekerja (person) dan kandidat item APD
        persons = []
        ppe_items = []

        for d in detections:
            cls_name = str(d.get("class", "")).lower()
            if cls_name == "person":
                persons.append(d)
            else:
                ppe_items.append(d)

        # Untuk setiap pekerja, cari kelengkapan APD
        for person in persons:
            p_box = person.get("bbox") or []
            if len(p_box) < 4:
                continue

            detected_ppe = []
            missing_ppe = []

            for req_key in self.required_ppe:
                # Periksa apakah ada objek yang cocok di zona anatomi
                synonyms = PPE_SYNONYMS.get(req_key, [req_key])
                zone_box = _get_anatomical_subzone(p_box, req_key)

                matched = False
                for item in ppe_items:
                    item_cls = str(item.get("class", "")).lower()
                    if item_cls in synonyms or any(s in item_cls for s in synonyms):
                        item_box = item.get("bbox") or []
                        if len(item_box) >= 4:
                            overlap = _bbox_intersection_ratio(zone_box, item_box)
                            if overlap >= 0.25:
                                matched = True
                                break

                # Fallback: periksa atribut bawaan (misal detektor vest dominant color)
                if not matched and req_key == "vest":
                    if person.get("has_vest") or str(person.get("vest_color", "")).lower() in ("hi_vis_green", "green", "orange", "yellow"):
                        matched = True

                if matched:
                    detected_ppe.append(req_key)
                else:
                    missing_ppe.append(req_key)

            total_req = len(self.required_ppe)
            score = round((len(detected_ppe) / float(total_req)) * 100.0, 1) if total_req > 0 else 100.0

            if score >= 99.0:
                status = "COMPLIANT"
            elif score >= self.min_compliance_score:
                status = "PARTIAL"
            else:
                status = "VIOLATION"

            is_violation = (status == "VIOLATION")

            # Sematkan metadata ke objek deteksi pekerja
            person["ppeScore"] = score
            person["ppeStatus"] = status
            person["detectedPPE"] = detected_ppe
            person["missingPPE"] = missing_ppe
            person["isViolation"] = is_violation

            # Cek trigger alarm kejadian
            raw_id = person.get("trackId", person.get("track_id", person.get("id")))
            track_id = str(raw_id) if raw_id is not None else "unknown"
            if is_violation:
                last_time = self.last_alarm_time.get(track_id, 0.0) if raw_id is not None else 0.0
                if current_time - last_time >= self.alarm_cooldown:
                    if raw_id is not None:
                        self.last_alarm_time[track_id] = current_time
                    events.append({
                        "event_type": "ppe_safety_violation",
                        "node_id": self.node_id,
                        "track_id": track_id,
                        "score": score,
                        "missing_ppe": missing_ppe,
                        "bbox": p_box,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "message": f"Pekerja (ID {track_id}) melanggar K3! Hilang: {', '.join(missing_ppe)} (Kepatuhan: {score}%)"
                    })

        return detections, events


def draw_ppe_compliance_badges(frame: np.ndarray, detections: List[Dict[str, Any]]) -> None:
    """Menggambar badge visual kepatuhan K3 di atas bounding box setiap pekerja."""
    if frame is None or not hasattr(frame, "shape"):
        return

    for det in detections:
        if "ppeScore" not in det:
            continue
        p_box = det.get("bbox") or []
        if len(p_box) < 4:
            continue

        x, y, w, h = [int(v) for v in p_box[:4]]
        score = det.get("ppeScore", 0)
        status = det.get("ppeStatus", "VIOLATION")
        missing = det.get("missingPPE", [])

        if status == "COMPLIANT":
            bg_color = (34, 197, 94)    # Hijau Emerald
            text_color = (255, 255, 255)
            badge_text = f"K3 OK {score:.0f}%"
        elif status == "PARTIAL":
            bg_color = (14, 165, 233)   # Cyan / Biru Langit
            text_color = (255, 255, 255)
            badge_text = f"K3 {score:.0f}%"
        else:
            bg_color = (37, 99, 235)    # Merah Coral (BGR: Merah = (0, 0, 220))
            bg_color = (20, 20, 220)
            text_color = (255, 255, 255)
            missing_str = missing[0] if missing else "APD"
            badge_text = f"K3 NO {missing_str.upper()} ({score:.0f}%)"

        # Gambar pill badge di atas kepala
        badge_y = max(18, y - 6)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.42
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(badge_text, font, font_scale, thickness)

        cv2.rectangle(frame, (x, badge_y - th - 5), (x + tw + 10, badge_y + baseline), bg_color, -1)
        cv2.rectangle(frame, (x, badge_y - th - 5), (x + tw + 10, badge_y + baseline), (255, 255, 255), 1)
        cv2.putText(frame, badge_text, (x + 5, badge_y - 2), font, font_scale, text_color, thickness, cv2.LINE_AA)


def process_ppe_compliance_matrix(
    node: Dict[str, Any],
    frame: np.ndarray,
    candidates: List[Dict[str, Any]],
    state: Dict[str, Any],
    now: float
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Runner eksekusi node PPE Compliance Matrix."""
    node_id = str(node.get("id") or "ppe_compliance_matrix")
    config = node.get("config", {})

    evaluator = state.get("evaluator")
    if evaluator is None:
        evaluator = PPEComplianceMatrix(node_id, config)
        state["evaluator"] = evaluator
    else:
        evaluator.update_config(config)

    augmented_dets, events = evaluator.evaluate(candidates, now)
    if config.get("showBadgeOverlay", True):
        draw_ppe_compliance_badges(frame, augmented_dets)

    return augmented_dets, events
