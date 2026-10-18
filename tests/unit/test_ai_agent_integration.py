import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT))

import core
import main
from server import validate_workflow


class TestAIAgentIntegration(unittest.TestCase):
    def test_server_validation(self):
        # 1. Valid workflow
        valid_wf = {
            "nodes": [
                {"id": "input_1", "type": "input", "config": {}},
                {
                    "id": "agent_1",
                    "type": "ai_agent",
                    "config": {
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "triggerMode": "on_event",
                        "taskMode": "decision",
                        "cooldownSeconds": 5.0,
                    },
                },
            ],
            "edges": [["input_1", "agent_1"]],
        }
        # Should pass without exception
        validate_workflow(valid_wf)

        # 2. Invalid provider
        bad_provider_wf = copy.deepcopy(valid_wf)
        bad_provider_wf["nodes"][1]["config"]["provider"] = "invalid_llm"
        with self.assertRaises(HTTPException) as ctx:
            validate_workflow(bad_provider_wf)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("provider must be", ctx.exception.detail)

        # 3. Invalid triggerMode
        bad_trigger_wf = copy.deepcopy(valid_wf)
        bad_trigger_wf["nodes"][1]["config"]["triggerMode"] = "on_something_else"
        with self.assertRaises(HTTPException) as ctx:
            validate_workflow(bad_trigger_wf)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("triggerMode must be", ctx.exception.detail)

        # 4. Negative cooldown
        bad_cooldown_wf = copy.deepcopy(valid_wf)
        bad_cooldown_wf["nodes"][1]["config"]["cooldownSeconds"] = -2.0
        with self.assertRaises(HTTPException) as ctx:
            validate_workflow(bad_cooldown_wf)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("cooldownSeconds must be", ctx.exception.detail)

    def test_pipeline_graph_routing_and_downstream(self):
        workflow = {
            "nodes": [
                {"id": "input_1", "type": "input", "enabled": True},
                {
                    "id": "zone_1",
                    "type": "zone_activity_timer",
                    "enabled": True,
                    "config": {"zoneName": "Loading Dock"},
                },
                {
                    "id": "agent_1",
                    "type": "ai_agent",
                    "enabled": True,
                    "config": {
                        "provider": "openai",
                        "triggerMode": "on_event",
                        "taskMode": "decision",
                        "passDownstreamOn": "decision_true",
                    },
                },
                {
                    "id": "alert_1",
                    "type": "alert",
                    "enabled": True,
                    "config": {"message": "AI Confirmed Incident"},
                },
            ],
            "edges": [
                ["input_1", "zone_1"],
                ["zone_1", "agent_1"],
                ["agent_1", "alert_1"],
            ],
        }

        # 1. Verify active_ai_agent_nodes resolves
        active_agents = main.active_ai_agent_nodes(workflow)
        self.assertEqual(len(active_agents), 1)
        self.assertEqual(active_agents[0]["id"], "agent_1")

        # 2. Zone timer emits event: ai_agent receives it as input
        zone_events = [
            {
                "kind": "zone_activity_event",
                "sourceNodeId": "zone_1",
                "zoneName": "Loading Dock",
                "duration": 15.0,
            }
        ]
        agent_inputs = main.results_for_node(workflow, "agent_1", zone_events)
        self.assertEqual(len(agent_inputs), 1)
        self.assertEqual(agent_inputs[0]["zoneName"], "Loading Dock")

        # 3. AI Agent emits approved event (decision=True) -> Alert receives it
        ai_events_approved = [
            {
                "kind": "ai_agent_event",
                "sourceNodeId": "agent_1",
                "decision": True,
                "passDownstream": True,
                "reason": "Unauthorized person near active loading dock",
            }
        ]
        alert_inputs = main.results_for_node(workflow, "alert_1", ai_events_approved)
        self.assertEqual(len(alert_inputs), 1)
        self.assertEqual(alert_inputs[0]["reason"], "Unauthorized person near active loading dock")

        # 4. AI Agent emits rejected event (decision=False, passDownstream=False) -> Alert receives nothing!
        ai_events_rejected = [
            {
                "kind": "ai_agent_event",
                "sourceNodeId": "agent_1",
                "decision": False,
                "passDownstream": False,
                "reason": "Authorized supervisor wearing full PPE",
            }
        ]
        alert_inputs_suppressed = main.results_for_node(workflow, "alert_1", ai_events_rejected)
        self.assertEqual(len(alert_inputs_suppressed), 0)

    def test_deliver_project_events_with_ai_agent(self):
        import cv2

        workflow = {
            "nodes": [
                {"id": "input_1", "type": "input", "enabled": True},
                {"id": "agent_1", "type": "ai_agent", "enabled": True},
                {"id": "alert_1", "type": "alert", "enabled": True, "config": {"message": "Critical Alert"}},
            ],
            "edges": [
                ["input_1", "agent_1"],
                ["agent_1", "alert_1"],
            ],
        }

        alerts = []
        runner = core.WorkflowRunner(on_event=lambda title, detail: alerts.append((title, detail)), native_preview=False)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        # 1. Event with passDownstream=True triggers alert
        events_pass = [
            {
                "kind": "ai_agent_event",
                "sourceNodeId": "agent_1",
                "decision": True,
                "passDownstream": True,
                "reason": "Fire smoke detected",
            }
        ]
        runner._deliver_project_events(cv2, workflow, frame, events_pass, {}, 1.0)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0][0], "Critical Alert")
        self.assertIn("Fire smoke detected", alerts[0][1])

        # 2. Event with passDownstream=False is suppressed (no alert)
        events_suppress = [
            {
                "kind": "ai_agent_event",
                "sourceNodeId": "agent_1",
                "decision": False,
                "passDownstream": False,
                "reason": "Normal steam vent",
            }
        ]
        runner._deliver_project_events(cv2, workflow, frame, events_suppress, {}, 2.0)
        self.assertEqual(len(alerts), 1)  # Still 1, nothing added!


if __name__ == "__main__":
    unittest.main()
