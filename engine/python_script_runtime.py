"""Bounded, per-node execution for the custom Python script node.

Scripts intentionally run as local Python with access to ``np`` and ``cv2``.
The worker process is isolation for hangs and state lifetime, not a security
sandbox.
"""
from __future__ import annotations

import ast
import contextlib
import io
import multiprocessing as mp
import time
import traceback
from dataclasses import dataclass
from threading import Lock

import numpy as np


MAX_LOG_BYTES = 4096
STARTUP_TIMEOUT = 30.0


class ScriptError(RuntimeError):
    """A script, worker, or frame contract failure."""

    def __init__(self, message: str, *, logs: str = "", traceback_text: str = ""):
        super().__init__(message)
        self.logs = logs
        self.traceback = traceback_text


class ScriptTimeout(ScriptError, TimeoutError):
    """The script exceeded its per-request timeout."""


class ScriptStopped(ScriptError, InterruptedError):
    """The owning workflow requested cancellation."""


@dataclass(frozen=True)
class ScriptResult:
    frame: np.ndarray
    logs: str = ""
    duration_ms: float = 0.0
    error: str | None = None
    state: str = "success"


class _BoundedWriter(io.TextIOBase):
    def __init__(self, limit: int = MAX_LOG_BYTES):
        self._buffer = io.StringIO()
        self._limit = limit
        self._size = 0

    def write(self, text):
        text = str(text)
        remaining = self._limit - self._size
        if remaining > 0:
            part = text[:remaining]
            self._buffer.write(part)
            self._size += len(part)
        return len(text)

    def flush(self):
        return None

    def getvalue(self):
        return self._buffer.getvalue()


def validate_script(code: str) -> None:
    """Check syntax and require a public ``process(frame, state)`` function."""
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Script code must be a non-empty string")
    try:
        tree = ast.parse(code, filename="<python-script>")
        compile(tree, "<python-script>", "exec")
    except SyntaxError as exc:
        raise ValueError(f"Script syntax error: {exc}") from exc
    process_defs = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == "process"]
    if not process_defs or isinstance(process_defs[0], ast.AsyncFunctionDef):
        raise ValueError("Script must define synchronous process(frame, state)")
    positional = process_defs[0].args.posonlyargs + process_defs[0].args.args
    required = len(positional) - len(process_defs[0].args.defaults)
    required_keywords = len(process_defs[0].args.kwonlyargs) - sum(value is not None for value in process_defs[0].args.kw_defaults)
    if len(positional) < 2 or len(positional) > 2 or required > 2 or required_keywords:
        raise ValueError("process must accept frame and state")


def _valid_frame(frame):
    return (isinstance(frame, np.ndarray) and frame.ndim == 3 and frame.shape[2] == 3
            and frame.dtype == np.uint8 and frame.shape[0] > 0 and frame.shape[1] > 0)


def _worker(connection):
    namespace = {}
    state = {}
    try:
        import cv2
        import numpy as worker_np
        namespace.update({"np": worker_np, "cv2": cv2, "__builtins__": __builtins__,
                          "__name__": "<python-script>"})
        connection.send({"ok": True, "kind": "ready"})
        while True:
            request = connection.recv()
            kind = request.get("kind")
            if kind == "close":
                return
            if kind == "initialize":
                output = _BoundedWriter()
                try:
                    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                        exec(compile(request["code"], "<python-script>", "exec"), namespace, namespace)
                    candidate = namespace.get("process")
                    if not callable(candidate):
                        raise ValueError("Script must define callable process(frame, state)")
                    state = {}
                    connection.send({"ok": True, "kind": "initialized", "logs": output.getvalue()})
                except BaseException:
                    connection.send({"ok": False, "kind": "error", "error": traceback.format_exc(),
                                     "logs": output.getvalue()})
                continue
            if kind != "frame":
                connection.send({"ok": False, "kind": "error", "error": "Unsupported script operation"})
                continue
            output = _BoundedWriter()
            try:
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    result = namespace["process"](request["frame"], state)
                if not _valid_frame(result):
                    raise ValueError("process must return a non-empty uint8 HxWx3 numpy array")
                if result.shape != request["frame"].shape:
                    raise ValueError("process must preserve frame dimensions; use the Resize node")
                connection.send({"ok": True, "kind": "frame", "frame": np.ascontiguousarray(result),
                                 "logs": output.getvalue()})
            except BaseException:
                connection.send({"ok": False, "kind": "error", "error": traceback.format_exc(),
                                 "logs": output.getvalue()})
    except (EOFError, BrokenPipeError, OSError):
        pass
    finally:
        connection.close()


class PythonScriptRunner:
    """Persistent spawn worker for one node/run and one script source."""

    def __init__(self, code: str, timeout_ms: int = 500, stop_event=None, *, on_error: str = "stop"):
        validate_script(code)
        if not isinstance(timeout_ms, int) or not 1 <= timeout_ms <= 60000:
            raise ValueError("timeout_ms must be an integer between 1 and 60000")
        if on_error not in ("stop", "pass"):
            raise ValueError("on_error must be 'stop' or 'pass'")
        self.code = code
        self.timeout = timeout_ms / 1000.0
        self.stop_event = stop_event
        self.on_error = on_error
        self._lock = Lock()
        self._closed = False
        self._faulted = None
        self.initialization_logs = ""
        context = mp.get_context("spawn")
        self._connection, child = context.Pipe()
        self._process = context.Process(target=_worker, args=(child,), name="visonode-python-script", daemon=True)
        self._process.start()
        child.close()
        try:
            self._receive(STARTUP_TIMEOUT)
            initialized = self._send_receive({"kind": "initialize", "code": code}, self.timeout)
            self.initialization_logs = initialized.get("logs", "")
        except BaseException:
            self.close()
            raise

    def _check_stopped(self):
        if self._closed:
            raise ScriptStopped("Python script runner is closed")
        if self.stop_event is not None and self.stop_event.is_set():
            raise ScriptStopped("Python script runner stopped")

    def _receive(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
            self._check_stopped()
            if self._connection.poll(min(0.05, max(0, deadline - time.monotonic()))):
                try:
                    response = self._connection.recv()
                except (EOFError, OSError) as exc:
                    raise ScriptError("Python script worker disconnected") from exc
                if not response.get("ok"):
                    error = response.get("error", "unknown script error")
                    raise ScriptError("Python script failed:\n" + error, logs=response.get("logs", ""),
                                      traceback_text=error)
                return response
            if not self._process.is_alive():
                raise ScriptError(f"Python script worker exited with code {self._process.exitcode}")
            if time.monotonic() >= deadline:
                raise ScriptTimeout("Python script timed out")

    def _send_receive(self, request, timeout):
        try:
            self._connection.send(request)
            return self._receive(timeout)
        except ScriptTimeout:
            self._faulted = "Python script timed out"
            self._terminate()
            raise

    def run(self, frame) -> ScriptResult:
        if not _valid_frame(frame):
            raise ValueError("Input frame must be a non-empty uint8 HxWx3 numpy array")
        with self._lock:
            self._check_stopped()
            if self._faulted:
                error = ScriptError(self._faulted)
                if self.on_error == "pass":
                    return ScriptResult(np.array(frame, copy=True), error=str(error), state="error")
                raise error
            started = time.monotonic()
            try:
                response = self._send_receive({"kind": "frame", "frame": np.ascontiguousarray(frame)}, self.timeout)
                return ScriptResult(response["frame"], response.get("logs", ""),
                                    (time.monotonic() - started) * 1000)
            except ScriptStopped:
                raise
            except (ScriptTimeout, ScriptError) as exc:
                if self.on_error == "pass":
                    state = "timeout" if isinstance(exc, ScriptTimeout) else "error"
                    return ScriptResult(np.array(frame, copy=True), getattr(exc, "logs", ""),
                                        (time.monotonic() - started) * 1000, str(exc), state)
                raise

    def _terminate(self):
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=0.5)

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            if self._process.is_alive():
                try:
                    self._connection.send({"kind": "close"})
                except (EOFError, BrokenPipeError, OSError):
                    pass
                self._process.join(timeout=0.5)
                if self._process.is_alive():
                    self._process.terminate()
                    self._process.join(timeout=0.5)
        finally:
            self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
