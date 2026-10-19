import pytest
import numpy as np
import cv2

from engine.ai_studio_assistant import (
    resolve_ai_config,
    create_sample_test_frame,
    execute_test_python_script,
    extract_python_code,
)


def test_resolve_ai_config_fallbacks():
    custom_cfg = resolve_ai_config({
        "provider": "openai",
        "baseUrl": "https://api.openai.com/v1",
        "apiKey": "sk-dummy-test-key",
        "model": "gpt-4o",
    })
    assert custom_cfg["baseUrl"] == "https://api.openai.com/v1"
    assert custom_cfg["apiKey"] == "sk-dummy-test-key"
    assert custom_cfg["model"] == "gpt-4o"

    default_cfg = resolve_ai_config({})
    assert default_cfg["baseUrl"]
    assert default_cfg["model"]


def test_create_sample_test_frame():
    frame = create_sample_test_frame(640, 480)
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (480, 640, 3)
    assert frame.dtype == np.uint8


def test_execute_test_python_script_success():
    code = """def process(frame, state):
    state['count'] = state.get('count', 0) + 1
    cv2.putText(frame, f"TEST {state['count']}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    print(f"Log output: count={state['count']}")
    return frame
"""
    result = execute_test_python_script(code)
    assert result["success"] is True
    assert result["durationMs"] >= 0
    assert "Log output: count=1" in result["logs"]
    assert result["inputImage"].startswith("data:image/jpeg;base64,")
    assert result["outputImage"].startswith("data:image/jpeg;base64,")
    assert result["dimensions"] == "640x480"


def test_extract_python_code():
    raw_markdown = """Here is your code:
```python
def process(frame, state):
    return frame.copy()
```
Have fun!"""
    assert extract_python_code(raw_markdown) == "def process(frame, state):\n    return frame.copy()"

    plain_code = "def process(frame, state):\n    return frame"
    assert extract_python_code(plain_code) == plain_code


def test_assistant_generate_and_modify_workflow_multiturn():
    from unittest.mock import patch
    from engine.ai_studio_assistant import assistant_generate_or_modify_workflow
    import json

    # Mock Turn 1: create initial workflow
    turn1_response = json.dumps({
        "explanation": "Membuat pipeline deteksi kendaraan",
        "action": "create",
        "modifications": ["Node Object Detection dibuat dengan kelas ['car', 'motorcycle']"],
        "workflow": {
            "nodes": [
                {"id": "node_input", "type": "input", "title": "Kamera", "x": 100, "y": 200, "config": {}},
                {"id": "node_det", "type": "detector", "title": "Object Detection", "x": 380, "y": 200, "config": {"classes": ["car", "motorcycle"], "confidenceThreshold": 0.5}},
            ],
            "edges": [{"id": "e1", "source": "node_input", "target": "node_det"}]
        }
    })

    with patch("engine.ai_studio_assistant.call_ai_completion", return_value=turn1_response) as mock_call:
        res1 = assistant_generate_or_modify_workflow(
            user_instruction="Buat pipeline deteksi mobil dan motor",
            current_workflow=None,
            history=[],
        )
        assert res1["action"] == "create"
        assert len(res1["workflow"]["nodes"]) == 2
        assert res1["workflow"]["nodes"][1]["config"]["confidenceThreshold"] == 0.5

    # Mock Turn 2: revise workflow with multi-turn history
    turn2_response = json.dumps({
        "explanation": "Memperbarui kelas deteksi menjadi ['car', 'bus'] dan menaikkan confidence ke 0.75",
        "action": "update",
        "modifications": [
            "Node Object Detection: classes diubah ke ['car', 'bus']",
            "Node Object Detection: confidenceThreshold dinaikkan ke 0.75"
        ],
        "workflow": {
            "nodes": [
                {"id": "node_det", "type": "detector", "title": "Object Detection", "x": 380, "y": 200, "config": {"classes": ["car", "bus"], "confidenceThreshold": 0.75}},
            ],
            "edges": []
        }
    })

    history = [
        {"role": "user", "content": "Buat pipeline deteksi mobil dan motor"},
        {"role": "assistant", "content": "Membuat pipeline deteksi kendaraan"}
    ]

    with patch("engine.ai_studio_assistant.call_ai_completion", return_value=turn2_response) as mock_call:
        res2 = assistant_generate_or_modify_workflow(
            user_instruction="Ganti kelasnya jadi mobil dan bus, serta naikkan confidence ke 0.75",
            current_workflow=res1["workflow"],
            history=history,
        )
        assert res2["action"] == "update"
        assert len(res2["modifications"]) == 2
        assert res2["workflow"]["nodes"][0]["config"]["classes"] == ["car", "bus"]
        assert res2["workflow"]["nodes"][0]["config"]["confidenceThreshold"] == 0.75

        # Check call arguments to verify history was passed
        passed_messages = mock_call.call_args[0][0]
        roles = [m["role"] for m in passed_messages]
        assert "system" in roles
        assert roles.count("user") >= 1

