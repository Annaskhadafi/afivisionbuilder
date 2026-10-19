from __future__ import annotations

import base64
import copy
import json
import os
import queue
import re
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple


class AIAgentClient:
    """Unified client for OpenAI, OpenRouter, and Local OpenAI-compatible APIs (Ollama, vLLM)."""

    def __init__(self, config: dict) -> None:
        self.provider = str(config.get("provider", "openai")).lower()
        self.model = str(config.get("model", "gpt-4o-mini"))
        self.task_mode = str(config.get("taskMode", "decision")).lower()
        self.system_prompt = str(config.get("systemPrompt", "You are an intelligent vision safety auditor and workflow agent."))
        self.user_prompt_template = str(config.get("userPrompt", "Analyze the visual scene and detection data: {{detections}}. Are there any violations or critical events?"))
        self.include_image = bool(config.get("includeImage", True))
        self.image_quality = int(config.get("imageQuality", 80))
        self.image_max_dimension = int(config.get("imageMaxDimension", 720))
        self.temperature = float(config.get("temperature", 0.2))
        self.max_tokens = int(config.get("maxTokens", 500))

        # Endpoint URL resolution
        if self.provider == "openrouter":
            self.base_url = str(config.get("baseUrl") or "https://openrouter.ai/api/v1").rstrip("/")
        elif self.provider == "custom":
            self.base_url = str(config.get("baseUrl") or "http://localhost:11434/v1").rstrip("/")
        else:  # default openai
            self.base_url = str(config.get("baseUrl") or "https://api.openai.com/v1").rstrip("/")

        # API Key resolution: config apiKey > environment variable fallback
        api_key = str(config.get("apiKey") or "").strip()
        if not api_key:
            if self.provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY", "")
            elif self.provider == "openrouter":
                api_key = os.environ.get("OPENROUTER_API_KEY", "")
            elif self.provider == "custom":
                api_key = os.environ.get("CUSTOM_AI_API_KEY", "")
        self.api_key = api_key

    def render_prompt(self, detections: list, event: Optional[dict] = None) -> str:
        """Render user prompt template with dynamic variables."""
        detections_summary = []
        for det in detections:
            cls_name = det.get("class", det.get("label", "object"))
            conf = det.get("confidence", det.get("score", 0.0))
            track_id = det.get("track_id", det.get("id"))
            item_str = f"- {cls_name} (conf: {conf:.2f}"
            if track_id is not None:
                item_str += f", track_id: {track_id}"
            item_str += ")"
            detections_summary.append(item_str)

        det_text = "\n".join(detections_summary) if detections_summary else "No objects detected"
        event_text = json.dumps(event, ensure_ascii=False) if event else "None"
        timestamp_text = time.strftime("%Y-%m-%d %H:%M:%S")

        prompt = self.user_prompt_template
        prompt = prompt.replace("{{detections}}", det_text)
        prompt = prompt.replace("{{detection_count}}", str(len(detections)))
        prompt = prompt.replace("{{event}}", event_text)
        prompt = prompt.replace("{{timestamp}}", timestamp_text)

        # Append explicit format instruction if in decision, structured_json, detector, or strict_classifier mode
        if self.task_mode == "decision":
            prompt += (
                "\n\nRespond strictly with a JSON object in the following schema:\n"
                '{\n  "decision": true or false,\n  "reason": "explanation of decision",\n  "severity": "low" | "medium" | "high" | "critical"\n}'
            )
        elif self.task_mode == "detector":
            prompt += (
                "\n\nDetect all relevant objects in the image. Respond strictly with a JSON object in this schema:\n"
                '{\n'
                '  "detections": [\n'
                '    {\n'
                '      "box_2d": [ymin, xmin, ymax, xmax],\n'
                '      "label": "class_name",\n'
                '      "confidence": 0.95\n'
                '    }\n'
                '  ]\n'
                '}\n'
                'Note: box_2d coordinates must be normalized (0 to 1000 or 0.0 to 1.0).'
            )
        elif self.task_mode == "strict_classifier":
            prompt += (
                "\n\nClassify the visual scene or item strictly according to inspection criteria. "
                "Respond strictly with a JSON object in this schema:\n"
                '{\n'
                '  "class": "label_name",\n'
                '  "confidence": 0.95,\n'
                '  "is_compliant": true or false,\n'
                '  "reason": "concise explanation"\n'
                '}'
            )
        elif self.task_mode == "structured_json":
            prompt += "\n\nRespond strictly with a valid JSON object matching the requested information."

        return prompt

    def encode_frame(self, frame_bgr: Any) -> Optional[str]:
        """Compress and encode OpenCV BGR frame to JPEG base64 data URI."""
        if frame_bgr is None:
            return None
        try:
            import cv2
            h, w = frame_bgr.shape[:2]
            scale = min(1.0, float(self.image_max_dimension) / max(h, w))
            if scale < 1.0:
                frame_bgr = cv2.resize(frame_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

            quality = max(10, min(100, self.image_quality))
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            success, buffer = cv2.imencode(".jpg", frame_bgr, encode_param)
            if not success:
                return None
            b64_str = base64.b64encode(buffer).decode("ascii")
            return f"data:image/jpeg;base64,{b64_str}"
        except Exception:
            return None

    def query(self, frame_bgr: Any, detections: list, event: Optional[dict] = None) -> dict:
        """Execute chat completion request against selected provider."""
        rendered_prompt = self.render_prompt(detections, event)
        endpoint = f"{self.base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AfiVisionBuilder/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/one-chitra/afi-vision-builder"
            headers["X-Title"] = "Afi Vision Builder"

        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        user_content: Any
        img_data_url = self.encode_frame(frame_bgr) if self.include_image else None
        if img_data_url:
            user_content = [
                {"type": "text", "text": rendered_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": img_data_url,
                        "detail": "low",
                    },
                },
            ]
        else:
            user_content = rendered_prompt

        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if self.task_mode in ("decision", "structured_json") and self.provider in ("openai", "openrouter"):
            payload["response_format"] = {"type": "json_object"}

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"AI Agent HTTP {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"AI Agent request error: {e}") from e

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("AI Agent returned no choices")

        raw_text = choices[0].get("message", {}).get("content", "").strip()
        usage = data.get("usage", {})
        return self.parse_response(raw_text, usage)

    def parse_response(self, raw_text: str, usage: dict) -> dict:
        """Parse raw response text based on configured taskMode."""
        result: dict = {
            "rawText": raw_text,
            "usage": usage,
            "provider": self.provider,
            "model": self.model,
            "taskMode": self.task_mode,
            "decision": True,
            "reason": raw_text,
            "parsedJson": None,
        }

        # Attempt JSON extraction if structured or decision
        parsed = None
        cleaned = raw_text
        # Remove markdown fences ```json ... ``` if present
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
        if json_match:
            cleaned = json_match.group(1).strip()

        try:
            parsed = json.loads(cleaned)
        except Exception:
            # Fallback regex search for json object
            obj_match = re.search(r"(\{[\s\S]*\})", cleaned)
            if obj_match:
                try:
                    parsed = json.loads(obj_match.group(1))
                except Exception:
                    parsed = None

        if parsed and isinstance(parsed, dict):
            result["parsedJson"] = parsed
            if self.task_mode == "decision":
                dec_val = parsed.get("decision", parsed.get("trigger", parsed.get("pass", True)))
                if isinstance(dec_val, str):
                    result["decision"] = dec_val.lower() in ("true", "1", "yes")
                else:
                    result["decision"] = bool(dec_val)
                result["reason"] = str(parsed.get("reason", parsed.get("explanation", raw_text)))
                result["severity"] = str(parsed.get("severity", "medium"))
            elif self.task_mode == "detector":
                raw_dets = parsed.get("detections", [])
                converted_dets = []
                for item in raw_dets:
                    label = str(item.get("label", item.get("class", "object")))
                    conf = float(item.get("confidence", item.get("score", 0.90)))
                    box = item.get("box_2d", item.get("box", item.get("bbox")))
                    if box and len(box) >= 4:
                        y1, x1, y2, x2 = [float(v) for v in box[:4]]
                        if max(y1, x1, y2, x2) > 1.0:
                            y1, x1, y2, x2 = y1 / 1000.0, x1 / 1000.0, y2 / 1000.0, x2 / 1000.0
                        converted_dets.append({
                            "class": label,
                            "confidence": conf,
                            "normalized_box": [x1, y1, x2, y2],
                            "source": "vlm_detector",
                        })
                result["detections"] = converted_dets
                result["decision"] = len(converted_dets) > 0
                result["reason"] = f"VLM detected {len(converted_dets)} objects"
            elif self.task_mode == "strict_classifier":
                result["class"] = str(parsed.get("class", "unknown"))
                result["confidence"] = float(parsed.get("confidence", 0.90))
                result["is_compliant"] = bool(parsed.get("is_compliant", True))
                result["decision"] = result["is_compliant"]
                result["reason"] = str(parsed.get("reason", raw_text))
            elif self.task_mode == "structured_json":
                result["reason"] = json.dumps(parsed, ensure_ascii=False)
        else:
            if self.task_mode == "decision":
                # Fallback: check if text indicates positive or negative
                lower_text = raw_text.lower()
                if (
                    "decision: false" in lower_text
                    or 'decision": false' in lower_text
                    or "decision is false" in lower_text
                    or "decision: no" in lower_text
                    or "decision is no" in lower_text
                ):
                    result["decision"] = False
                else:
                    result["decision"] = True

        return result


class AIAgentRuntime:
    """Non-blocking background runtime for AI Agent node."""

    def __init__(self, node_id: str, config: dict, on_log: Optional[Callable[[str], None]] = None) -> None:
        self.node_id = str(node_id)
        self.config = dict(config)
        self.on_log = on_log or (lambda s: None)

        self.client = AIAgentClient(self.config)
        self.trigger_mode = str(self.config.get("triggerMode", "on_event")).lower()
        self.periodic_interval = float(self.config.get("periodicIntervalSeconds", 10.0))
        self.cooldown_seconds = float(self.config.get("cooldownSeconds", 5.0))
        self.pass_downstream_on = str(self.config.get("passDownstreamOn", "decision_true")).lower()

        self._queue: queue.Queue = queue.Queue(maxsize=3)
        self._results: list[dict] = []
        self._results_lock = threading.Lock()

        self._last_trigger_time = 0.0
        self._last_periodic_time = 0.0
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True, name=f"AIAgent-{self.node_id}")
        self._worker_thread.start()

    def stop(self) -> None:
        """Signal worker thread to stop."""
        self._stop_event.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass

    def _worker_loop(self) -> None:
        """Worker loop executing LLM/VLM calls asynchronously."""
        while not self._stop_event.is_set():
            try:
                task = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if task is None or self._stop_event.is_set():
                break

            frame_bgr, detections, event, timestamp_ms = task
            try:
                t0 = time.time()
                res = self.client.query(frame_bgr, detections, event)
                latency = time.time() - t0

                # Determine if event should pass downstream
                pass_downstream = True
                if self.pass_downstream_on == "decision_true" and not res.get("decision", True):
                    pass_downstream = False

                event_packet = {
                    "kind": "ai_agent_event",
                    "sourceNodeId": self.node_id,
                    "timestamp": timestamp_ms,
                    "provider": res["provider"],
                    "model": res["model"],
                    "taskMode": res["taskMode"],
                    "decision": res["decision"],
                    "reason": res["reason"],
                    "rawText": res["rawText"],
                    "parsedJson": res.get("parsedJson"),
                    "severity": res.get("severity", "medium"),
                    "latencySeconds": round(latency, 2),
                    "passDownstream": pass_downstream,
                    "event": event,
                    "detectionCount": len(detections),
                    "detections": res.get("detections"),
                    "classifierClass": res.get("class"),
                    "classifierConfidence": res.get("confidence"),
                    "isCompliant": res.get("is_compliant"),
                }

                with self._results_lock:
                    self._results.append(event_packet)
                    if len(self._results) > 20:
                        del self._results[:-20]

                decision_tag = "APPROVED" if res["decision"] else "REJECTED"
                self.on_log(f"AI Agent [{self.node_id}] {res['model']} {decision_tag} in {latency:.2f}s: {res['reason'][:80]}")

            except Exception as e:
                self.on_log(f"AI Agent [{self.node_id}] error: {e}")

    def on_frame(self, frame_bgr: Any, detections: list, upstream_events: list, now: float) -> list[dict]:
        """Called on every frame from pipeline execution."""
        timestamp_ms = int(now * 1000)
        should_trigger = False
        trigger_event = None

        # Check triggers
        if self.trigger_mode == "on_event":
            if upstream_events:
                # Find event directed to this node or from active upstream
                trigger_event = upstream_events[0]
                if (now - self._last_trigger_time) >= self.cooldown_seconds:
                    should_trigger = True
        elif self.trigger_mode == "periodic":
            if (now - self._last_periodic_time) >= self.periodic_interval and (now - self._last_trigger_time) >= self.cooldown_seconds:
                should_trigger = True
                self._last_periodic_time = now
        elif self.trigger_mode == "always":
            if (now - self._last_trigger_time) >= self.cooldown_seconds:
                should_trigger = True

        if should_trigger and not self._queue.full():
            self._last_trigger_time = now
            # Pass copy of frame to avoid thread contention
            frame_copy = frame_bgr.copy() if frame_bgr is not None and self.client.include_image else None
            try:
                self._queue.put_nowait((frame_copy, copy.deepcopy(detections), copy.deepcopy(trigger_event), timestamp_ms))
            except queue.Full:
                pass

        # Drain completed results
        with self._results_lock:
            if not self._results:
                return []
            dispatched = list(self._results)
            self._results.clear()
            return dispatched
