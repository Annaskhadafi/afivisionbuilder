from __future__ import annotations

import json
import os
import time
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from engine.ai_agent import AIAgentClient, AIAgentRuntime


class TestAIAgentClient(unittest.TestCase):
    def test_prompt_rendering(self):
        config = {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "taskMode": "decision",
            "userPrompt": "Obj count: {{detection_count}}, Details: {{detections}}, Ev: {{event}}",
        }
        client = AIAgentClient(config)
        detections = [
            {"class": "person", "confidence": 0.88, "track_id": 10},
            {"class": "tire", "confidence": 0.95},
        ]
        event = {"kind": "zone_activity_event", "zoneName": "Bay 1", "duration": 12.5}
        rendered = client.render_prompt(detections, event)
        self.assertIn("Obj count: 2", rendered)
        self.assertIn("person (conf: 0.88, track_id: 10)", rendered)
        self.assertIn("tire (conf: 0.95)", rendered)
        self.assertIn("zone_activity_event", rendered)
        self.assertIn('"decision": true or false', rendered)

    def test_frame_encoding(self):
        client = AIAgentClient({"includeImage": True, "imageQuality": 75, "imageMaxDimension": 320})
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        encoded = client.encode_frame(frame)
        self.assertIsNotNone(encoded)
        self.assertTrue(encoded.startswith("data:image/jpeg;base64,"))

    def test_response_parser_decision(self):
        client = AIAgentClient({"taskMode": "decision"})
        # 1. Direct JSON
        raw_1 = '{"decision": true, "reason": "Worker detected without helmet", "severity": "high"}'
        parsed_1 = client.parse_response(raw_1, {"total_tokens": 120})
        self.assertTrue(parsed_1["decision"])
        self.assertEqual(parsed_1["severity"], "high")
        self.assertIn("without helmet", parsed_1["reason"])

        # 2. Markdown fenced JSON
        raw_2 = '```json\n{"decision": false, "reason": "All personnel clear of restricted zone", "severity": "low"}\n```'
        parsed_2 = client.parse_response(raw_2, {"total_tokens": 110})
        self.assertFalse(parsed_2["decision"])
        self.assertEqual(parsed_2["severity"], "low")

        # 3. Text fallback
        raw_3 = "The decision is false because conditions are safe."
        parsed_3 = client.parse_response(raw_3, {})
        self.assertFalse(parsed_3["decision"])

    def test_providers_resolution(self):
        # OpenAI
        c_openai = AIAgentClient({"provider": "openai", "apiKey": "sk-test-123"})
        self.assertEqual(c_openai.base_url, "https://api.openai.com/v1")
        self.assertEqual(c_openai.api_key, "sk-test-123")

        # OpenRouter
        c_or = AIAgentClient({"provider": "openrouter", "apiKey": "sk-or-456"})
        self.assertEqual(c_or.base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(c_or.api_key, "sk-or-456")

        # Custom Ollama
        c_custom = AIAgentClient({"provider": "custom", "baseUrl": "http://192.168.1.50:11434/v1"})
        self.assertEqual(c_custom.base_url, "http://192.168.1.50:11434/v1")


class TestAIAgentRuntime(unittest.TestCase):
    @patch.object(AIAgentClient, "query")
    def test_on_event_trigger_and_downstream_gating(self, mock_query):
        mock_query.return_value = {
            "rawText": '{"decision": true, "reason": "Safety hazard detected"}',
            "usage": {},
            "provider": "openai",
            "model": "gpt-4o-mini",
            "taskMode": "decision",
            "decision": True,
            "reason": "Safety hazard detected",
            "severity": "high",
            "parsedJson": {"decision": True, "reason": "Safety hazard detected"},
        }

        config = {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "triggerMode": "on_event",
            "cooldownSeconds": 1.0,
            "passDownstreamOn": "decision_true",
            "includeImage": False,
        }
        runtime = AIAgentRuntime("ai_agent_1", config)

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        detections = [{"class": "person", "score": 0.9}]
        upstream_events = [{"kind": "zone_activity_event", "sourceNodeId": "zone_1"}]

        now = 100.0
        # Frame with upstream event triggers background query
        runtime.on_frame(frame, detections, upstream_events, now)
        time.sleep(0.3)

        # Subsequent frame drains results
        results = runtime.on_frame(frame, detections, [], now + 0.1)
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res["kind"], "ai_agent_event")
        self.assertEqual(res["sourceNodeId"], "ai_agent_1")
        self.assertTrue(res["decision"])
        self.assertTrue(res["passDownstream"])
        self.assertEqual(res["reason"], "Safety hazard detected")

        runtime.stop()

    @patch.object(AIAgentClient, "query")
    def test_negative_decision_suppression(self, mock_query):
        mock_query.return_value = {
            "rawText": '{"decision": false, "reason": "Normal operational movement"}',
            "usage": {},
            "provider": "openai",
            "model": "gpt-4o-mini",
            "taskMode": "decision",
            "decision": False,
            "reason": "Normal operational movement",
            "severity": "low",
            "parsedJson": {"decision": False, "reason": "Normal operational movement"},
        }

        config = {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "triggerMode": "on_event",
            "cooldownSeconds": 1.0,
            "passDownstreamOn": "decision_true",
            "includeImage": False,
        }
        runtime = AIAgentRuntime("ai_agent_2", config)

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        upstream_events = [{"kind": "zone_activity_event", "sourceNodeId": "zone_1"}]

        runtime.on_frame(frame, [], upstream_events, 200.0)
        time.sleep(0.3)

        results = runtime.on_frame(frame, [], [], 200.1)
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertFalse(res["decision"])
        # Should be suppressed from passing downstream because passDownstreamOn == 'decision_true'
        self.assertFalse(res["passDownstream"])

        runtime.stop()


if __name__ == "__main__":
    unittest.main()
