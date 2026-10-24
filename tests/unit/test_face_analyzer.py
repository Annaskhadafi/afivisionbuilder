import numpy as np
import pytest
from engine.uniface_runtime import (
    process_face_analyzer_node,
    draw_face_analyzer_overlay,
    get_age_bracket,
    EMOTION_TRANSLATIONS,
    get_uniface_manager,
)


def test_get_age_bracket():
    assert get_age_bracket(10) == "Anak-anak (<13)"
    assert get_age_bracket(18) == "Remaja (13-20)"
    assert get_age_bracket(25) == "Dewasa (21-35)"
    assert get_age_bracket(45) == "Dewasa Madya (36-50)"
    assert get_age_bracket(65) == "Lansia (>50)"


def test_emotion_translations():
    assert EMOTION_TRANSLATIONS.get("happy") == "Bahagia"
    assert EMOTION_TRANSLATIONS.get("neutral") == "Netral"
    assert EMOTION_TRANSLATIONS.get("sad") == "Sedih"
    assert EMOTION_TRANSLATIONS.get("surprise") == "Terkejut"
    assert EMOTION_TRANSLATIONS.get("angry") == "Marah"


def test_process_face_analyzer_with_existing_faces():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dummy_faces = [
        {
            "class": "face",
            "x": 100,
            "y": 100,
            "width": 80,
            "height": 80,
            "confidence": 0.95,
            "landmarks": [[120, 120], [160, 120], [140, 140], [125, 160], [155, 160]],
        },
        {
            "class": "face",
            "x": 300,
            "y": 150,
            "width": 90,
            "height": 90,
            "confidence": 0.92,
            "landmarks": [[320, 170], [360, 170], [340, 190], [325, 210], [355, 210]],
        },
    ]

    node = {
        "id": "analyzer_1",
        "type": "face_analyzer",
        "config": {
            "detectLandmarks": True,
            "estimateAgeGender": True,
            "classifyEmotion": True,
            "showFaceBadges": True,
            "showCornerHUD": True,
            "hudPosition": "top-left",
            "ageGrouping": "bracket",
        },
    }

    enriched_faces, events = process_face_analyzer_node(node, frame, dummy_faces)

    assert len(enriched_faces) == 2
    for f in enriched_faces:
        assert "age" in f
        assert isinstance(f["age"], int)
        assert f["age"] >= 1
        assert "gender" in f
        assert f["gender"] in ("Laki-laki", "Perempuan")
        assert "emotion" in f
        assert f["emotion"] in ("Bahagia", "Netral", "Terkejut", "Sedih", "Marah", "Takut", "Jijik", "Sinis")
        assert "faceAnalyzerStats" in f

    stats = enriched_faces[0]["faceAnalyzerStats"]
    assert stats["total"] == 2
    assert stats["avg_age"] is not None
    assert isinstance(stats["age_groups"], dict)
    assert isinstance(stats["emotions"], dict)
    assert stats["hudPosition"] == "top-left"

    assert len(events) == 1
    assert events[0]["kind"] == "face_analysis_summary"
    assert events[0]["totalFaces"] == 2


def test_process_face_analyzer_toggle_options():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dummy_faces = [
        {
            "class": "face",
            "x": 150,
            "y": 150,
            "width": 80,
            "height": 80,
            "confidence": 0.90,
        }
    ]

    # Only Emotion active, Age & Gender disabled
    node = {
        "id": "analyzer_2",
        "type": "face_analyzer",
        "config": {
            "estimateAgeGender": False,
            "classifyEmotion": True,
            "showFaceBadges": False,
            "showCornerHUD": True,
        },
    }

    enriched, events = process_face_analyzer_node(node, frame, dummy_faces)
    assert len(enriched) == 1
    assert "age" not in enriched[0]
    assert "gender" not in enriched[0]
    assert "emotion" in enriched[0]
    assert enriched[0]["faceAnalyzerStats"]["estimateAgeGender"] is False
    assert enriched[0]["faceAnalyzerStats"]["classifyEmotion"] is True


def test_draw_face_analyzer_overlay_renders_properly():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = [
        {
            "class": "face",
            "x": 80,
            "y": 80,
            "width": 100,
            "height": 100,
            "bbox": [80, 80, 100, 100],
            "landmarks": [[100, 100], [150, 100], [125, 125], [110, 150], [140, 150]],
            "age": 25,
            "gender": "Laki-laki",
            "emotion": "Bahagia",
            "faceAnalyzerActive": True,
            "detectLandmarks": True,
            "showFaceBadges": True,
            "faceAnalyzerStats": {
                "total": 1,
                "avg_age": 25,
                "age_groups": {"Dewasa (21-35)": 1},
                "exact_ages": {"25 thn": 1},
                "emotions": {"Bahagia": 1},
                "hudPosition": "top-right",
                "ageGrouping": "bracket",
                "showCornerHUD": True,
                "estimateAgeGender": True,
                "classifyEmotion": True,
            },
        }
    ]

    # Overlay should modify frame in-place without error
    draw_face_analyzer_overlay(frame, detections)
    # Verify frame contains drawn pixels (not pure black)
    assert np.any(frame > 0)


def test_draw_face_analyzer_overlay_exact_age_grouping():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = [
        {
            "class": "face",
            "x": 50,
            "y": 50,
            "width": 60,
            "height": 60,
            "bbox": [50, 50, 60, 60],
            "age": 28,
            "gender": "Perempuan",
            "emotion": "Netral",
            "faceAnalyzerActive": True,
            "detectLandmarks": False,
            "showFaceBadges": True,
            "faceAnalyzerStats": {
                "total": 1,
                "avg_age": 28,
                "age_groups": {"Dewasa (21-35)": 1},
                "exact_ages": {"28 thn": 1},
                "emotions": {"Netral": 1},
                "hudPosition": "bottom-left",
                "ageGrouping": "exact",
                "showCornerHUD": True,
                "estimateAgeGender": True,
                "classifyEmotion": True,
            },
        }
    ]

    draw_face_analyzer_overlay(frame, detections)
    assert np.any(frame > 0)


def test_draw_face_analyzer_empty_and_none_safe():
    # Should not raise exception on empty detections or None
    draw_face_analyzer_overlay(None, [])
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    draw_face_analyzer_overlay(frame, [])
    assert np.all(frame == 0)
