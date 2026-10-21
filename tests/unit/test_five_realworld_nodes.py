import numpy as np
import pytest
import cv2
import time

from engine.dominant_color import (
    inspect_dominant_color,
    draw_dominant_color_badges,
    COLOR_PRESETS,
)
from engine.class_replacement import (
    relabel_detections,
)
from engine.man_down_detector import (
    detect_man_down,
    draw_man_down_overlay,
)
from engine.lpr_license_plate import (
    normalize_indonesia_plate,
    process_license_plates,
    draw_license_plate_badges,
)
from engine.overstack_detector import (
    detect_overstack_violations,
    draw_overstack_overlay,
)


# --- 1. Dominant Color Tests ---

def test_dominant_color_safety_green_match():
    # Create image with bright safety green patch (RGB: 132, 204, 22 -> BGR: 22, 204, 132)
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    frame[30:150, 30:150] = (22, 204, 132)  # High-visibility green

    detections = [{
        "class": "person",
        "track_id": 101,
        "bbox": [20, 20, 140, 160],
    }]
    config = {
        "targetClass": "person",
        "subRegion": "torso",
        "targetPreset": "hi_vis_green",
        "minMatchPercent": 10.0,
        "requireMatch": False,
        "attributeKey": "vest_color",
    }
    state = {}
    now = 1000.0

    augmented, events = inspect_dominant_color(frame, detections, config, state, now)
    assert len(augmented) == 1
    det = augmented[0]
    assert det["dominantColorMatch"] is True
    assert det["dominantColorPct"] >= 10.0
    assert det["attributes"]["vest_color_compliant"] is True
    assert len(events) == 1
    assert events[0]["event_type"] == "COLOR_MATCH_DETECTED"

    # Test overlay drawing without crash
    draw_dominant_color_badges(frame, augmented)


def test_dominant_color_violation_event():
    # Black frame: no safety vest
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    detections = [{
        "class": "person",
        "track_id": 102,
        "bbox": [20, 20, 100, 120],
    }]
    config = {
        "targetClass": "person",
        "subRegion": "torso",
        "targetPreset": "hi_vis_green",
        "minMatchPercent": 15.0,
        "requireMatch": True,
        "attributeKey": "vest_color",
    }
    state = {}
    now = 1000.0

    augmented, events = inspect_dominant_color(frame, detections, config, state, now)
    assert len(augmented) == 1
    assert augmented[0]["dominantColorMatch"] is False
    assert len(events) == 1
    assert events[0]["event_type"] == "COLOR_NON_COMPLIANCE"
    assert events[0]["severity"] == "WARNING"


# --- 2. Class Replacement Tests ---

def test_class_replacement_direct_mapping():
    detections = [
        {"class": "vehicle", "track_id": 1, "confidence": 0.85, "attributes": {}},
        {"class": "person", "track_id": 2, "confidence": 0.90, "attributes": {}},
        {"class": "cone", "track_id": 3, "confidence": 0.70, "attributes": {}},
    ]
    config = {
        "sourceClass": "*",
        "replacementMode": "direct_mapping",
        "mappingTable": "vehicle:forklift, person:worker",
        "preserveOriginalClass": True,
        "fallbackAction": "keep_original",
    }
    relabeled, events = relabel_detections(detections, config)
    assert len(relabeled) == 3
    assert relabeled[0]["class"] == "forklift"
    assert relabeled[0]["attributes"]["original_class"] == "vehicle"
    assert relabeled[1]["class"] == "worker"
    assert relabeled[2]["class"] == "cone"  # unmapped retained
    assert len(events) == 2


def test_class_replacement_attribute_lookup_and_fallback():
    detections = [
        {"class": "vehicle", "track_id": 1, "attributes": {"sub_class": "dump_truck_scania", "sub_class_conf": 0.95}},
        {"class": "vehicle", "track_id": 2, "attributes": {}},  # Missing sub_class
    ]
    config = {
        "sourceClass": "vehicle",
        "replacementMode": "attribute_lookup",
        "attributeKey": "sub_class",
        "fallbackAction": "set_unknown",
        "preserveOriginalClass": True,
    }
    relabeled, events = relabel_detections(detections, config)
    assert len(relabeled) == 2
    assert relabeled[0]["class"] == "dump_truck_scania"
    assert relabeled[0]["confidence"] == 0.95
    assert relabeled[1]["class"] == "unknown"


# --- 3. Man Down Detector Tests ---

def test_man_down_standing_person():
    # Standing person: width=40, height=120 -> aspect ratio = 40/120 = 0.33 (upright)
    detections = [{
        "class": "person",
        "track_id": 201,
        "bbox": [50, 50, 40, 120],
    }]
    config = {
        "targetClass": "person",
        "aspectRatioThreshold": 0.90,
        "confirmationDurationSeconds": 3.0,
    }
    state = {}
    now = 100.0

    augmented, events = detect_man_down(None, detections, config, state, now)
    assert len(augmented) == 1
    assert augmented[0]["isManDown"] is False
    assert augmented[0]["attributes"]["posture"] == "standing"
    assert len(events) == 0


def test_man_down_fallen_worker_emergency():
    # Fallen person: width=140, height=45 -> aspect ratio = 140/45 = 3.11 (lying horizontal)
    detections = [{
        "class": "person",
        "track_id": 202,
        "bbox": [50, 100, 140, 45],
    }]
    config = {
        "targetClass": "person",
        "aspectRatioThreshold": 0.90,
        "stillnessMaxMotionPx": 10.0,
        "confirmationDurationSeconds": 4.0,
        "alarmCooldownSeconds": 10.0,
    }
    state = {}

    # Frame 1 at t=0s: horizontal detected, but duration is 0
    aug1, ev1 = detect_man_down(None, detections, config, state, now=10.0)
    assert aug1[0]["isManDown"] is False
    assert len(ev1) == 0

    # Frame 2 at t=2.0s: still lying down, 2.0s < 4.0s
    aug2, ev2 = detect_man_down(None, detections, config, state, now=12.0)
    assert aug2[0]["isManDown"] is False
    assert len(ev2) == 0

    # Frame 3 at t=4.5s: persistent stillness for 4.5s >= 4.0s -> EMITS EMERGENCY EVENT
    aug3, ev3 = detect_man_down(None, detections, config, state, now=14.5)
    assert aug3[0]["isManDown"] is True
    assert aug3[0]["manDownDuration"] == 4.5
    assert len(ev3) == 1
    assert ev3[0]["event_type"] == "MAN_DOWN_ALERT"
    assert ev3[0]["severity"] == "CRITICAL"
    assert "BAHAYA" in ev3[0]["message"]

    # Test overlay drawing
    frame = np.zeros((300, 300, 3), dtype=np.uint8)
    draw_man_down_overlay(frame, aug3)


# --- 4. LPR License Plate Tests ---

def test_indonesia_plate_normalization():
    # Ambiguous OCR test cases
    raw_1 = "b 1234 xyz"
    clean_1, valid_1 = normalize_indonesia_plate(raw_1)
    assert clean_1 == "B 1234 XYZ"
    assert valid_1 is True

    # Number segment has letter 'O' instead of digit '0'
    raw_2 = "KT 888O AA"
    clean_2, valid_2 = normalize_indonesia_plate(raw_2)
    assert clean_2 == "KT 8880 AA"
    assert valid_2 is True


def test_lpr_whitelist_and_blacklist_access():
    detections = [
        {"class": "truck", "track_id": 301, "bbox": [50, 50, 120, 100], "plate_text": "B 1234 XYZ"},
        {"class": "car", "track_id": 302, "bbox": [200, 50, 100, 80], "plate_text": "B 6666 BAD"},
        {"class": "pickup", "track_id": 303, "bbox": [350, 50, 100, 80], "plate_text": "D 9999 UNK"},
    ]
    config = {
        "vehicleClasses": "truck, car, pickup",
        "whitelist": "B1234XYZ",
        "blacklist": "B6666BAD",
        "temporalVotingFrames": 3,
        "gateCooldownSeconds": 10.0,
    }
    state = {}
    now = 500.0

    augmented, events = process_license_plates(None, detections, config, state, now)
    assert len(augmented) == 3

    assert augmented[0]["plateAccessStatus"] == "AUTHORIZED"
    assert augmented[1]["plateAccessStatus"] == "BLACKLISTED"
    assert augmented[2]["plateAccessStatus"] == "UNREGISTERED"

    assert len(events) == 3
    event_types = [e["event_type"] for e in events]
    assert "GATE_ACCESS_GRANTED" in event_types
    assert "SECURITY_ALERT_BLACKLIST" in event_types
    assert "VEHICLE_ARRIVED" in event_types

    # Test overlay drawing
    frame = np.zeros((400, 500, 3), dtype=np.uint8)
    draw_license_plate_badges(frame, augmented)


# --- 5. Overstack Detector Tests ---

def test_overstack_normal_and_breach():
    # Ceiling line at Y=200
    # Safe pallet: y_top=250 (below ceiling in screen coords)
    safe_det = {"class": "pallet", "track_id": 401, "bbox": [50, 250, 80, 100]}
    # Overstack pallet: y_top=150 (above ceiling in screen coords)
    hazard_det = {"class": "pallet", "track_id": 402, "bbox": [150, 150, 80, 200]}

    config = {
        "targetClasses": "pallet, box",
        "ceilingY": 200.0,
        "pixelPerMeter": 50.0,
        "persistenceDurationSeconds": 2.0,
        "alarmCooldownSeconds": 15.0,
    }
    state = {}

    # At t=0s: safe is not overstack; hazard is breaching but hasn't reached 2.0s persistence
    aug1, ev1 = detect_overstack_violations(None, [safe_det, hazard_det], config, state, now=10.0)
    assert aug1[0]["isOverstack"] is False
    assert aug1[1]["isOverstack"] is False
    assert len(ev1) == 0

    # At t=2.5s: hazard persists for 2.5s >= 2.0s -> EMITS OVERSTACK_HAZARD
    aug2, ev2 = detect_overstack_violations(None, [safe_det, hazard_det], config, state, now=12.5)
    assert aug2[0]["isOverstack"] is False
    assert aug2[1]["isOverstack"] is True
    assert aug2[1]["excessHeightM"] == 1.0  # (200 - 150) / 50 = 1.0m
    assert len(ev2) == 1
    assert ev2[0]["event_type"] == "OVERSTACK_HAZARD"
    assert ev2[0]["excess_meters"] == 1.0

    # Test overlay drawing
    frame = np.zeros((400, 400, 3), dtype=np.uint8)
    draw_overstack_overlay(frame, aug2, config)
