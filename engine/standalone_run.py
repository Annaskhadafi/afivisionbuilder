"""Entry point copied into exported workflow packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from threading import Lock

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
os.environ["VISONODE_APP_DATA_DIR"] = str(ROOT / "data")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _resolve(value):
    if isinstance(value, dict):
        return {key: _resolve(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item) for item in value]
    if isinstance(value, str) and value.startswith("$ENV/"):
        name = value[5:]
        result = os.environ.get(name, "").strip()
        if not result:
            raise ValueError(f"Missing required environment variable: {name}")
        return result
    if isinstance(value, str) and value.startswith("$PACKAGE/"):
        path = (ROOT / value[9:]).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("Package path escapes the extracted folder")
        if path.is_relative_to(ROOT / "data"):
            path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)
    return value


def load_workflow() -> dict:
    _load_env()
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    workflow = json.loads((ROOT / "workflow.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(json.dumps(workflow, sort_keys=True, allow_nan=False).encode()).hexdigest()
    if digest != manifest["workflowSha256"]:
        raise ValueError("workflow.json does not match manifest.json")
    for model in manifest["models"]:
        file_name = model.get("file")
        if file_name:
            path = ROOT / file_name
            if not path.is_file() or _sha256(path) != model["sha256"]:
                raise ValueError(f"Model checksum mismatch: {file_name}")
    workflow = _resolve(workflow)
    for variable in manifest["environment"]:
        if variable.get("required") or not os.environ.get(variable["name"]):
            continue
        node = next(item for item in workflow["nodes"] if item["id"] == variable["nodeId"])
        value = os.environ[variable["name"]]
        node["config"][variable["field"]] = int(value) if variable["field"] == "source" and value.isdigit() else value
    for model in manifest["models"]:
        if model.get("file"):
            continue
        node = next(item for item in workflow["nodes"] if item["id"] == model["nodeId"])
        path = Path(node["config"][model["field"]])
        if not path.is_file() or _sha256(path) != model["sha256"]:
            raise ValueError(f"Model checksum mismatch for node {model['nodeId']}")
    return workflow


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exported Afi Vision workflow")
    parser.add_argument("--check", action="store_true", help="validate package and configuration without capture")
    parser.add_argument("--seconds", type=float, default=0, help="stop after a duration (0 = until interrupted)")
    parser.add_argument("--headless", action="store_true", help="run without desktop OpenCV preview window")
    parser.add_argument("--no-preview", dest="headless", action="store_true", help="alias for --headless")
    args = parser.parse_args()
    try:
        workflow = load_workflow()
        sys.path.insert(0, str(ROOT / "engine"))
        import core
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        secret_values = [os.environ.get(item["name"], "") for item in manifest["environment"] if re.search(r"password|token|key|header|url|source", item["field"], re.I)]
        def redact(message):
            result = str(message)
            for value in secret_values:
                if len(value) >= 3:
                    result = result.replace(value, "[REDACTED]")
            return result

        latest_frame = None
        frame_lock = Lock()

        def on_frame(preview_id: str, frame: np.ndarray, has_annotation: bool):
            nonlocal latest_frame
            with frame_lock:
                latest_frame = frame

        runner = core.WorkflowRunner(
            on_log=lambda message: print(redact(message), flush=True),
            on_event=lambda *parts: print("EVENT", *(redact(part) for part in parts), flush=True),
            on_frame=on_frame,
        )
        if args.check:
            print("Package and configuration OK", flush=True)
            return 0

        runner.start(workflow)
        started = None
        cv2_window_created = False
        window_title = f"Afi Vision Preview — {manifest.get('name', 'Workflow')}"

        if not args.headless:
            print(f"[Preview] OpenCV window active: '{window_title}'. Press 'q' or 'ESC' to stop.", flush=True)

        while runner.is_running():
            if runner.status().get("state") == "running" and started is None:
                started = time.monotonic()
            if args.seconds > 0 and started is not None and time.monotonic() - started >= args.seconds:
                break

            frame_to_show = None
            with frame_lock:
                if latest_frame is not None:
                    frame_to_show = latest_frame
                    latest_frame = None

            if not args.headless:
                if frame_to_show is not None:
                    try:
                        if not cv2_window_created:
                            cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
                            # Reasonable default window size
                            h, w = frame_to_show.shape[:2]
                            target_w = min(1280, max(640, w))
                            target_h = int(target_w * (h / max(1, w)))
                            cv2.resizeWindow(window_title, target_w, target_h)
                            cv2_window_created = True

                        cv2.imshow(window_title, frame_to_show)
                    except cv2.error as err:
                        print(f"[Preview] GUI display unavailable ({err}). Continuing in headless mode.", flush=True)
                        args.headless = True

                if cv2_window_created:
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord('q'), ord('Q'), 27):  # 'q' or ESC
                        print("\n[Preview] User requested stop. Exiting...", flush=True)
                        break
                else:
                    time.sleep(0.01)
            else:
                time.sleep(0.01)

        error = runner.status().get("error")
        runner.stop()
        if cv2_window_created:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

        if error:
            raise RuntimeError(redact(error))
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(f"Exported workflow failed: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
