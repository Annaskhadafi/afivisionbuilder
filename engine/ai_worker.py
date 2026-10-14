from __future__ import annotations

import base64
import ctypes
import json
import os
import queue
import select
import sys
import threading
import time
import traceback


_write_lock = threading.Lock()
_runner = None


def send(payload: dict) -> None:
    with _write_lock:
        sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
        sys.stdout.flush()


def send_log(line: str) -> None:
    send({"type": "log", "line": line})


def send_event(title: str, detail: str) -> None:
    send({"type": "event", "title": title, "detail": detail})


def send_status(status: dict) -> None:
    send({"type": "status", "status": status})


def send_node_debug(payload: dict) -> None:
    send({"type": "node_debug", "payload": payload})


def send_frame(preview_id: str, frame, shown: bool) -> None:
    # Cocoa windows must live on the main UI thread. Use the desktop's Qt
    # preview transport on macOS instead of HighGUI in the workflow thread.
    data = None
    if shown and frame is not None:
        import cv2

        ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ok:
            raise RuntimeError("Could not encode the preview frame.")
        data = base64.b64encode(encoded).decode("ascii")
    send({"type": "frame", "previewId": preview_id, "shown": shown, "data": data})


def ensure_runner():
    global _runner
    if _runner is None:
        import core

        _runner = core.WorkflowRunner(
            on_log=send_log,
            on_event=send_event,
            on_status=send_status,
            on_node_debug=send_node_debug,
            on_frame=send_frame,
            native_preview=sys.platform != "darwin",
        )
    return _runner


def handle_command(payload: dict) -> bool:
    command = payload.get("command")
    if command == "devices":
        import main as engine

        send({"type": "devices", "payload": engine.runtime_devices()})
    elif command == "start":
        workflow = payload.get("workflow")
        if not isinstance(workflow, dict):
            raise ValueError("Missing workflow payload.")
        ensure_runner().start(workflow, debug=bool(payload.get("debug", False)))
    elif command == "stop":
        if _runner is not None:
            _runner.stop()
    elif command == "shutdown":
        if _runner is not None:
            _runner.stop()
        return False
    else:
        raise ValueError(f"Unsupported worker command '{command}'.")
    return True


def iter_stdin_lines():
    if os.name == "nt":
        import msvcrt

        handle = msvcrt.get_osfhandle(sys.stdin.fileno())
        kernel32 = ctypes.windll.kernel32
        available = ctypes.c_ulong()
        while True:
            ok = kernel32.PeekNamedPipe(
                ctypes.c_void_p(handle),
                None,
                0,
                None,
                ctypes.byref(available),
                None,
            )
            if not ok:
                return
            if available.value:
                line = sys.stdin.readline()
                if not line:
                    return
                yield line
            else:
                time.sleep(0.05)
    else:
        while True:
            readable, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not readable:
                continue
            line = sys.stdin.readline()
            if not line:
                return
            yield line


def main() -> int:
    send({"type": "ready"})
    commands: queue.Queue[str | None] = queue.Queue()

    def read_stdin() -> None:
        for line in iter_stdin_lines():
            commands.put(line)
        commands.put(None)

    threading.Thread(target=read_stdin, daemon=True).start()

    while True:
        line = commands.get()
        if line is None:
            break
        try:
            payload = json.loads(line)
            if not handle_command(payload):
                break
        except Exception as exc:  # noqa: BLE001
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
            send({"type": "error", "error": str(exc).strip() or type(exc).__name__,
                  "traceback": traceback.format_exc()})
    if _runner is not None:
        _runner.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
