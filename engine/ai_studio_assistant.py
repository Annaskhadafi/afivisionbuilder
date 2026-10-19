"""AI Studio Assistant & Copilot Engine for Afi Vision Builder.

Provides:
1. Unified OpenAI-compatible chat completion caller (9router, OpenAI, OpenRouter, Ollama, vLLM).
2. AI Prompt-to-Code generator for Custom Python Script node with AST verification.
3. AI Studio Assistant Copilot for generating new node pipelines and revising existing workflows.
4. Single-frame sandbox test execution with live Before/After visual comparison.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Optional

import cv2
import numpy as np

from python_script_runtime import PythonScriptRunner, validate_script

DEFAULT_NINEROUTER_BASE_URL = "https://9router.chitraparatama.com/v1"
DEFAULT_NINEROUTER_MODEL = "cx/gpt-5.6-luna"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
FALLBACK_API_KEY = ""


def resolve_ai_config(user_override: Optional[dict] = None) -> dict:
    """Resolve API key, base URL, and model from user settings, environment, or fallbacks."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    override = user_override or {}

    provider = str(override.get("provider") or "").lower().strip()
    base_url = str(override.get("baseUrl") or "").strip().rstrip("/")
    api_key = str(override.get("apiKey") or "").strip()
    model = str(override.get("model") or "").strip()

    # Fallback resolution for Base URL
    if not base_url:
        if provider == "openai":
            base_url = os.environ.get("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL).rstrip("/")
        elif provider == "ollama":
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
        elif provider == "openrouter":
            base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
        else:
            base_url = (
                os.environ.get("ROUTER_BASE_URL")
                or os.environ.get("OPENAI_BASE_URL")
                or os.environ.get("NINEROUTER_BASE_URL")
                or DEFAULT_NINEROUTER_BASE_URL
            ).rstrip("/")

    # Fallback resolution for API Key from local VPS / server environment (.env)
    if not api_key:
        api_key = (
            os.environ.get("ROUTER_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("NINEROUTER_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("CUSTOM_AI_API_KEY")
            or ""
        )

    # Fallback resolution for Model
    if not model:
        if "9router" in base_url:
            model = os.environ.get("AI_MODEL", DEFAULT_NINEROUTER_MODEL)
        elif "openai.com" in base_url:
            model = os.environ.get("AI_MODEL", DEFAULT_OPENAI_MODEL)
        elif "11434" in base_url:
            model = os.environ.get("AI_MODEL", "qwen2.5-coder:latest")
        else:
            model = os.environ.get("AI_MODEL", DEFAULT_NINEROUTER_MODEL)

    return {
        "provider": provider or "9router",
        "baseUrl": base_url,
        "apiKey": api_key,
        "model": model,
    }


def call_ai_completion(
    messages: list[dict],
    ai_config: Optional[dict] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 2500,
    json_mode: bool = False,
    timeout: int = 35,
) -> str:
    """Call OpenAI-compatible chat completion endpoint."""
    cfg = resolve_ai_config(ai_config)
    endpoint = f"{cfg['baseUrl']}/chat/completions"

    if not cfg["apiKey"] and "11434" not in cfg["baseUrl"] and "localhost" not in cfg["baseUrl"]:
        raise ValueError(
            "API Key belum diatur. Silakan masukkan API Key Anda di menu Settings > AI & VLM Keys atau atur ROUTER_API_KEY / OPENAI_API_KEY di file .env server lokal/VPS."
        )

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "AfiVisionBuilder/1.0",
    }
    if cfg["apiKey"]:
        headers["Authorization"] = f"Bearer {cfg['apiKey']}"
    if "openrouter" in cfg["baseUrl"]:
        headers["HTTP-Referer"] = "https://github.com/one-chitra/afi-vision-builder"
        headers["X-Title"] = "Afi Vision Builder Studio Copilot"

    formatted_messages = list(messages)
    if system_prompt and not any(m.get("role") == "system" for m in formatted_messages):
        formatted_messages.insert(0, {"role": "system", "content": system_prompt})

    payload: dict[str, Any] = {
        "model": cfg["model"],
        "messages": formatted_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode and "11434" not in cfg["baseUrl"]:
        payload["response_format"] = {"type": "json_object"}

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_body = resp.read().decode("utf-8")
            response_json = json.loads(raw_body)
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"AI Provider Error (HTTP {err.code}): {err_msg}") from err
    except Exception as err:
        raise RuntimeError(f"Gagal menghubungi endpoint AI ({cfg['baseUrl']}): {err}") from err

    choices = response_json.get("choices") or []
    if not choices:
        raise RuntimeError(f"AI tidak mengembalikan pilihan respons: {response_json}")

    content = choices[0].get("message", {}).get("content", "")
    return content.strip()


def extract_python_code(raw_text: str) -> str:
    """Extract clean Python code from raw LLM text output."""
    pattern = r"```(?:python)?\s*([\s\S]*?)```"
    match = re.search(pattern, raw_text, re.IGNORECASE)
    if match:
        code = match.group(1).strip()
    else:
        code = raw_text.strip()
    return code


PYTHON_SCRIPT_SYSTEM_PROMPT = """You are an elite Computer Vision and OpenCV Python engineer for Afi Vision Builder.
Your task is to write a single, clean, highly-optimized function:

def process(frame, state):
    ...
    return frame

Rules and Constraints:
1. `frame` is a NumPy ndarray in BGR format with shape (H, W, 3) and dtype uint8.
2. `state` is a persistent Python dictionary preserved across frames (use for counters, trackers, timestamps, etc.).
3. You have `cv2` and `np` already available in the execution namespace. Do NOT use heavy or uninstalled third-party packages.
4. The function MUST return a NumPy ndarray with the EXACT SAME dimensions (H, W, 3) and uint8 dtype as the input `frame`.
5. Write safe, performant code suitable for real-time video streaming (~30 FPS).
6. Return ONLY valid executable Python code. Provide clear inline comments explaining the logic.
"""


def generate_python_script_from_prompt(
    prompt: str,
    current_code: Optional[str] = None,
    ai_config: Optional[dict] = None,
) -> dict:
    """Generate or revise Python script code based on natural language prompt."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt instruksi tidak boleh kosong")

    messages = [
        {"role": "system", "content": PYTHON_SCRIPT_SYSTEM_PROMPT},
    ]

    user_content = f"User Request: {prompt.strip()}"
    if current_code and current_code.strip() and "def process" in current_code:
        user_content += f"\n\nExisting Code to revise or extend:\n```python\n{current_code.strip()}\n```"

    messages.append({"role": "user", "content": user_content})

    raw_response = call_ai_completion(messages, ai_config, temperature=0.2, max_tokens=2000)
    clean_code = extract_python_code(raw_response)

    # Validate syntax and process(frame, state) signature
    try:
        validate_script(clean_code)
        validation_error = None
        is_valid = True
    except Exception as exc:
        validation_error = str(exc)
        is_valid = False

    return {
        "success": is_valid,
        "code": clean_code,
        "error": validation_error,
        "raw": raw_response,
    }


def create_sample_test_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """Create a rich, colorful synthetic BGR test frame with shapes, text, and gradient."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Gradient background
    for y in range(height):
        b = int(240 - (y / height) * 60)
        g = int(245 - (y / height) * 40)
        r = int(250 - (y / height) * 30)
        frame[y, :] = (b, g, r)

    # Shapes for testing filters/contours
    cv2.rectangle(frame, (60, 80), (220, 260), (37, 99, 235), -1)   # Blue-orange box
    cv2.circle(frame, (380, 180), 75, (22, 163, 74), -1)           # Green circle
    cv2.circle(frame, (510, 310), 65, (220, 38, 38), -1)           # Red circle
    cv2.rectangle(frame, (120, 330), (340, 420), (202, 138, 4), -1) # Yellow box

    # Test typography
    cv2.putText(frame, "AFI VISION TEST FRAME", (50, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (15, 23, 42), 2)
    cv2.putText(frame, "Shapes: Blue, Green, Red, Yellow", (50, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (71, 85, 105), 1)

    return frame


def execute_test_python_script(
    code: str,
    custom_frame_bgr: Optional[np.ndarray] = None,
    initial_state: Optional[dict] = None,
    state: Optional[dict] = None,
    frame_source: str = "synthetic",
) -> dict:
    """Execute python script on a single test frame and return before/after images and metrics."""
    validate_script(code)

    frame_in = custom_frame_bgr if custom_frame_bgr is not None else create_sample_test_frame()
    h, w = frame_in.shape[:2]

    runner = PythonScriptRunner(code, timeout_ms=3000)
    t0 = time.perf_counter()
    try:
        result = runner.run(frame_in.copy())
        duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    finally:
        runner.close()

    if result.error:
        raise RuntimeError(f"Eksekusi script gagal: {result.error}\nLogs:\n{result.logs}")

    frame_out = result.frame

    # Encode both before & after to base64 jpeg
    _, buf_in = cv2.imencode(".jpg", frame_in, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    _, buf_out = cv2.imencode(".jpg", frame_out, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

    b64_in = f"data:image/jpeg;base64,{base64.b64encode(buf_in).decode('ascii')}"
    b64_out = f"data:image/jpeg;base64,{base64.b64encode(buf_out).decode('ascii')}"

    return {
        "success": True,
        "durationMs": duration_ms,
        "logs": result.logs.strip(),
        "inputImage": b64_in,
        "outputImage": b64_out,
        "dimensions": f"{w}x{h}",
    }


WORKFLOW_COPILOT_SYSTEM_PROMPT = """You are the expert AI Studio Copilot for Afi Vision Builder, an enterprise visual computer vision workflow platform.
You can CREATE new node workflows from scratch, REVISE existing workflows, or MODIFY node parameters (such as classes, confidence thresholds, filter criteria, and tracking settings) while remembering previous conversation turns.

### Key Rules & Memory Awareness:
1. Multi-Turn Context: Remember previous user prompts, suggestions, and actions in the conversation history. If the user previously asked for a pipeline and now says "ubah kelasnya jadi mobil dan motor", "naikkan confidence detector ke 0.7", or "tambahkan filter ukuran", understand the context from previous turns and revise the existing workflow accordingly.
2. In-Place Parameter Modification: When modifying an existing workflow (action = "update"):
   - KEEP existing node `id` and `type` unchanged so existing cable connections remain stable!
   - Update the specific parameters inside `config` (classes, confidenceThreshold, filter_type, smoothing factors, etc.).
   - If adding a node (like adding a Filter or CSV Sink), insert it cleanly into the node chain and update `edges`.
   - List each concrete change in the `modifications` array.
3. Node Config Specifications:
   - `detector`:
     * `classes`: list of target class strings, e.g. `["car", "motorcycle", "person", "truck"]`
     * `confidenceThreshold`: float `0.05` to `0.99`, default `0.5`
     * `iouThreshold`: float `0.1` to `0.95`, default `0.45`
     * `engine`: `"ultralytics_yolo"` (default), `"rfdetr"`, `"rfdetr_tensorrt"`, `"yolo_world"`
     * `customClasses`: comma-separated string for YOLO-World zero-shot, e.g. `"hard hat, safety vest, forklift"`
     * `modelPath`: string path or model name
   - `filter`:
     * `filter_type`: `"class"` (filter by specific classes), `"confidence"` (filter by score threshold), `"size"` (filter by bounding box area), `"zone"` (filter within polygon)
     * `classes`: list of string classes allowed to pass
     * `min_confidence`: float, e.g. `0.65`
     * `min_size`: int pixels, e.g. `50`
     * `max_size`: int pixels, e.g. `1200`
   - `per_class_confidence`:
     * `thresholds`: object mapping class to float, e.g. `{"person": 0.45, "car": 0.65, "truck": 0.75}`
   - `tracker`:
     * `tracker_type`: `"bytetrack"` (default) or `"botsort"`
     * `track_thresh`: float, default `0.5`
     * `track_buffer`: int frames, default `30`
     * `match_thresh`: float, default `0.8`
     * `class_lock`: bool, default `true` (enables majority vote class stabilization)
     * `stabilize_bbox`: bool, default `true` (enables EMA coordinate smoothing)
   - `track_class_lock`:
     * `lock_window`: int frames (e.g. `15`)
     * `majority_ratio`: float (e.g. `0.7`)
   - `bbox_stabilizer`:
     * `smoothing_alpha`: float `0.1` to `0.9` (e.g. `0.5`)
     * `max_missing_frames`: int (e.g. `5`)
   - `delta_filter`:
     * `position_threshold_px`: int (e.g. `15`)
     * `mode`: `"position"`, `"area"`, or `"both"`
   - `zone_activity_timer`:
     * `target_classes`: list of strings, e.g. `["person"]`
     * `min_duration_sec`: int seconds, e.g. `15`
     * `polygon`: list of `[x, y]` coordinates, e.g. `[[100, 100], [400, 100], [400, 400], [100, 400]]`
   - `zone_exit_event`:
     * `target_classes`: list of strings
     * `cooldown_sec`: int seconds (e.g. `10`)
     * `polygon`: list of `[x, y]` points
   - `multi_zone_occupancy`:
     * `zones`: list of zone definitions
     * `target_classes`: list of strings
   - `distance_measurement`:
     * `min_distance_px`: int alert distance
     * `class_pair`: list of 2 classes, e.g. `["person", "forklift"]`
   - `velocity_calculator`:
     * `pixels_per_meter`: float (e.g. `20.0`)
     * `speed_limit_kmh`: float (e.g. `40.0`)
   - `overlay_annotate`:
     * `show_boxes`: bool (default `true`)
     * `show_labels`: bool (default `true`)
     * `show_scores`: bool (default `true`)
     * `show_tracks`: bool (default `true`)
     * `show_halo`: bool (default `false`)
     * `show_traces`: bool (default `false`)
     * `box_thickness`: int (1-5)
     * `font_scale`: float (0.4-1.2)
   - `python_script`:
     * `code`: valid Python code with `def process(frame, state):`
   - `input`:
     * `source_type`: `"webcam"`, `"file"`, `"youtube"`
     * `source_path`: camera index or URL/file path
   - `ip_camera`:
     * `rtsp_url`: string RTSP URL
     * `fps_limit`: int FPS
   - `preview`:
     * `output_label`: string title
   - `csv_formatter`:
     * `file_name`: string CSV filename, e.g. `traffic_log.csv`
     * `include_timestamp`: bool
   - `database_output`:
     * `table_name`: string SQLite table name
   - `notification_dispatcher`:
     * `webhook_url`: string URL
     * `channel`: `"telegram"`, `"slack"`, `"discord"`, or `"whatsapp"`
     * `cooldown_sec`: int seconds
   - `s3_sink`:
     * `bucket`: string
     * `save_crops`: bool

### Output Format (Strict JSON):
{
  "explanation": "Penjelasan rinci dalam bahasa Indonesia mengenai alur atau perubahan parameter yang dilakukan.",
  "action": "create" | "update",
  "modifications": [
    "Deskripsi spesifik perubahan per node (contoh: 'Node Object Detection: classes diubah ke [\"car\", \"motorcycle\"], confidenceThreshold: 0.65')"
  ],
  "workflow": {
    "nodes": [
      {
        "id": "node_id",
        "type": "exact_node_type",
        "title": "Node Title",
        "x": 100, // x coordinate (left to right, ~260px step)
        "y": 200, // y coordinate (base 200, branches y=400)
        "config": { ... } // Detailed node config options matching requirements
      }
    ],
    "edges": [
      {
        "id": "e_from_to",
        "source": "source_node_id",
        "target": "target_node_id"
      }
    ]
  }
}
"""


def assistant_generate_or_modify_workflow(
    user_instruction: str,
    current_workflow: Optional[dict] = None,
    history: Optional[list] = None,
    ai_config: Optional[dict] = None,
) -> dict:
    """Generate or modify workflow nodes and edges based on user prompt and multi-turn history."""
    if not user_instruction or not user_instruction.strip():
        raise ValueError("Instruksi alur kerja tidak boleh kosong")

    messages = [
        {"role": "system", "content": WORKFLOW_COPILOT_SYSTEM_PROMPT},
    ]

    # Inject conversation history to retain context across multiple turns
    if history and isinstance(history, list):
        for h in history[-8:]:  # keep last 8 turns for deep context
            role = h.get("role")
            content = h.get("content")
            if role in ("user", "assistant") and content:
                # Avoid duplicating the current instruction if it's already in history tail
                if role == "user" and str(content).strip() == user_instruction.strip():
                    continue
                messages.append({"role": role, "content": str(content)})

    has_nodes = bool(current_workflow and current_workflow.get("nodes"))
    user_payload: dict[str, Any] = {
        "instruction": user_instruction.strip(),
        "hasExistingWorkflow": has_nodes,
    }
    if has_nodes:
        user_payload["currentWorkflow"] = current_workflow

    messages.append({
        "role": "user",
        "content": f"User Request:\n{json.dumps(user_payload, indent=2)}",
    })

    raw_response = call_ai_completion(
        messages,
        ai_config,
        temperature=0.2,
        max_tokens=2500,
        json_mode=True,
    )

    # Clean JSON markdown fences if present
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as err:
        raise RuntimeError(f"Gagal mem-parsing keluaran AI sebagai JSON alur kerja: {err}\nRaw:\n{raw_response}") from err

    workflow = parsed.get("workflow") or {}
    nodes = workflow.get("nodes") or []
    edges = workflow.get("edges") or []

    return {
        "success": True,
        "explanation": parsed.get("explanation", "Alur kerja berhasil dirancang."),
        "action": parsed.get("action", "update" if has_nodes else "create"),
        "modifications": parsed.get("modifications") or [],
        "workflow": {
            "nodes": nodes,
            "edges": edges,
        },
    }
