"""Standalone checks for the custom Python script runtime."""
from __future__ import annotations

import multiprocessing as mp
import os
import sys
import threading
import time
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from engine.python_script_runtime import (  # noqa: E402
    PythonScriptRunner,
    ScriptStopped,
    ScriptTimeout,
    validate_script,
)


class PythonScriptRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.frame = np.zeros((4, 5, 3), dtype=np.uint8)
        self.frame[:, :, 1] = 10

    def test_state_logs_and_source_isolation(self):
        original = self.frame.copy()
        code = """\
def process(frame, state):
    state['count'] = state.get('count', 0) + 1
    print('count', state['count'])
    return 255 - frame
"""
        runner = PythonScriptRunner(code)
        try:
            first = runner.run(self.frame)
            second = runner.run(self.frame)
            self.assertEqual(first.frame[0, 0, 1], 245)
            self.assertIn("count 1", first.logs)
            self.assertIn("count 2", second.logs)
            np.testing.assert_array_equal(self.frame, original)
        finally:
            runner.close()

    def test_validation_and_bad_return(self):
        with self.assertRaises(ValueError):
            validate_script("def process(frame, state) return frame")
        with self.assertRaises(ValueError):
            validate_script("def process(frame): return frame")
        with self.assertRaises(ValueError):
            validate_script("def process(frame, state, required): return frame")
        runner = PythonScriptRunner("def process(frame, state): return frame[:, :, :1]")
        try:
            with self.assertRaises(Exception):
                runner.run(self.frame)
        finally:
            runner.close()

    def test_pass_result_reports_error(self):
        runner = PythonScriptRunner("print('initialized')\ndef process(frame, state):\n    raise ValueError('bad pixel')",
                                   on_error="pass")
        try:
            result = runner.run(self.frame)
            self.assertEqual(result.state, "error")
            self.assertIn("bad pixel", result.error)
            self.assertIn("initialized", runner.initialization_logs)
        finally:
            runner.close()

    def test_infinite_body_times_out(self):
        runner = PythonScriptRunner("def process(frame, state):\n    while True: pass", timeout_ms=100)
        try:
            with self.assertRaises(ScriptTimeout):
                runner.run(self.frame)
            with self.assertRaises(Exception):
                runner.run(self.frame)
        finally:
            runner.close()

    def test_infinite_top_level_times_out(self):
        code = "while True: pass\ndef process(frame, state): return frame"
        with self.assertRaises(ScriptTimeout):
            PythonScriptRunner(code, timeout_ms=100)

    def test_stop_cancels_wait(self):
        stop = threading.Event()
        runner = PythonScriptRunner("def process(frame, state):\n    while True: pass", timeout_ms=60000,
                                    stop_event=stop)
        try:
            thread = threading.Thread(target=lambda: self._run_ignoring_result(runner))
            thread.start()
            time.sleep(0.1)
            stop.set()
            thread.join(2)
            self.assertFalse(thread.is_alive())
        finally:
            runner.close()

    @staticmethod
    def _run_ignoring_result(runner):
        try:
            runner.run(np.zeros((2, 2, 3), dtype=np.uint8))
        except (ScriptStopped, Exception):
            pass


if __name__ == "__main__":
    mp.freeze_support()
    unittest.main()
