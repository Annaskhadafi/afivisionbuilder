from __future__ import annotations

import collections
import logging
import os
import re
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import cv2

# Ensure engine path is available
_current_dir = Path(__file__).resolve().parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

import core
import workflow_store as store

try:
    import dashboard_bus
    _HAS_DASHBOARD_BUS = True
except ImportError:
    _HAS_DASHBOARD_BUS = False

logger = logging.getLogger("afi.fleet_manager")


class WorkflowFleetManager:
    """Manages and orchestrates concurrent background execution of multiple workflows."""

    def __init__(self, max_concurrent: int = 10):
        self._lock = threading.RLock()
        self.max_concurrent = max_concurrent
        self._runners: Dict[str, core.WorkflowRunner] = {}
        self._meta: Dict[str, dict] = {}
        self._previews: Dict[str, bytes] = {}
        self._logs: Dict[str, collections.deque] = {}
        self._events: Dict[str, collections.deque] = {}
        self._seq: Dict[str, int] = collections.defaultdict(int)

    def is_running(self, project_id: str) -> bool:
        with self._lock:
            runner = self._runners.get(project_id)
            if not runner:
                return False
            return bool(runner.is_running())

    def start(self, project_id: str, target_fps: int = 10, debug: bool = False) -> dict:
        """Start a workflow in background fleet execution."""
        with self._lock:
            if not project_id or not isinstance(project_id, str):
                raise ValueError("Valid projectId is required.")

            project = store.get_project(project_id)
            if not project:
                raise ValueError(f"Project with ID '{project_id}' not found.")

            # Check if already running
            existing = self._runners.get(project_id)
            if existing and existing.is_running():
                return self.get_status(project_id)

            # Check concurrency limit
            active_count = sum(1 for r in self._runners.values() if r.is_running())
            if active_count >= self.max_concurrent:
                raise RuntimeError(
                    f"Maksimal {self.max_concurrent} alur kerja bersamaan telah tercapai. "
                    "Hentikan salah satu alur kerja terlebih dahulu."
                )

            # Load and normalize workflow
            workflow = store.load_project_workflow(project_id)
            input_nodes = [
                n for n in workflow.get("nodes", [])
                if n.get("type") in ("input", "ip_camera") and n.get("enabled", True)
            ]
            if not input_nodes:
                raise ValueError(
                    f"Alur kerja '{project.get('name', project_id)}' tidak memiliki node Input yang aktif."
                )

            # Apply Target FPS throttle to input node config
            safe_target_fps = max(1, min(60, int(target_fps or 10)))
            for n in input_nodes:
                cfg = n.setdefault("config", {})
                cfg["targetFps"] = safe_target_fps
                cfg["asyncPreview"] = True
                cfg["dropFrames"] = True

            # Prepare logging and callbacks per project
            self._logs.setdefault(project_id, collections.deque(maxlen=300)).clear()
            self._events.setdefault(project_id, collections.deque(maxlen=300)).clear()
            self._seq[project_id] = 0

            def on_log(text: str) -> None:
                self._record_log(project_id, text)

            def on_event(title: str, detail: str = "") -> None:
                self._record_event(project_id, title, detail)

            def on_frame(node_id: str, frame: Any, *args: Any) -> None:
                self._record_frame(project_id, node_id, frame)

            # Instantiate isolated runner
            runner = core.WorkflowRunner(
                on_log=on_log,
                on_event=on_event,
                on_frame=on_frame,
                native_preview=False,
            )

            self._runners[project_id] = runner
            self._meta[project_id] = {
                "projectId": project_id,
                "projectName": project.get("name", "Untitled Workflow"),
                "targetFps": safe_target_fps,
                "startedAt": time.time(),
                "desiredState": "running",
                "lastActive": time.time(),
                "error": None,
            }

            try:
                runner.start(workflow, debug=debug)
            except Exception as exc:
                self._meta[project_id]["error"] = str(exc)
                self._meta[project_id]["desiredState"] = "error"
                logger.error(f"Failed to start workflow {project_id}: {exc}")
                raise

            on_log(f"Layanan alur kerja '{project.get('name')}' dimulai (Target {safe_target_fps} FPS).")
            return self.get_status(project_id)

    def stop(self, project_id: str) -> dict:
        """Stop a specific background workflow gracefully."""
        with self._lock:
            runner = self._runners.get(project_id)
            meta = self._meta.get(project_id, {})
            meta["desiredState"] = "stopped"

            if runner:
                try:
                    runner.stop()
                except Exception as exc:
                    logger.warning(f"Error stopping workflow {project_id}: {exc}")

            if project_id in self._meta:
                self._meta[project_id]["desiredState"] = "stopped"
                self._meta[project_id]["stoppedAt"] = time.time()

            self._record_log(project_id, "Layanan alur kerja dihentikan.")
            return self.get_status(project_id)

    def restart(self, project_id: str, target_fps: int = 10) -> dict:
        """Restart a specific background workflow with fresh configuration."""
        self.stop(project_id)
        time.sleep(0.3)
        return self.start(project_id, target_fps=target_fps)

    def stop_all(self) -> None:
        """Stop all running background workflows cleanly."""
        with self._lock:
            project_ids = list(self._runners.keys())
        for pid in project_ids:
            try:
                self.stop(pid)
            except Exception:
                pass

    def get_status(self, project_id: str) -> dict:
        """Get live status of a single workflow in the fleet."""
        with self._lock:
            runner = self._runners.get(project_id)
            meta = self._meta.get(project_id, {})
            project = store.get_project(project_id) or {}
            project_name = meta.get("projectName") or project.get("name") or "Workflow"

            if runner:
                runner_stat = runner.status()
                is_run = bool(runner_stat.get("running"))
                state = runner_stat.get("state", "idle")
                fps = float(runner_stat.get("fps", 0.0))
                error = runner_stat.get("error") or meta.get("error")
                uptime = round(time.time() - meta.get("startedAt", time.time()), 1) if is_run else 0.0
            else:
                is_run = False
                state = "stopped"
                fps = 0.0
                error = meta.get("error")
                uptime = 0.0

            return {
                "projectId": project_id,
                "projectName": project_name,
                "running": is_run,
                "state": state,
                "fps": fps,
                "targetFps": meta.get("targetFps", 10),
                "uptime": uptime,
                "error": error,
                "hasPreview": project_id in self._previews,
                "modifiedAt": project.get("modified_at", ""),
            }

    def get_fleet_status(self) -> dict:
        """Get comprehensive overview of all saved projects and their running status."""
        with self._lock:
            all_projects = store.list_projects()
            items: List[dict] = []
            running_count = 0

            for proj in all_projects:
                pid = proj["id"]
                stat = self.get_status(pid)
                if stat["running"]:
                    running_count += 1
                items.append(stat)

            return {
                "total": len(items),
                "runningCount": running_count,
                "stoppedCount": len(items) - running_count,
                "maxConcurrent": self.max_concurrent,
                "services": items,
            }

    def get_preview(self, project_id: str) -> Optional[bytes]:
        """Retrieve the latest encoded JPEG frame bytes for a specific workflow."""
        with self._lock:
            return self._previews.get(project_id)

    # -- Internal handlers ----------------------------------------------------

    def _record_log(self, project_id: str, text: str) -> None:
        with self._lock:
            self._seq[project_id] += 1
            queue = self._logs.setdefault(project_id, collections.deque(maxlen=300))
            queue.append({
                "seq": self._seq[project_id],
                "time": time.time(),
                "text": str(text),
            })

    def _record_event(self, project_id: str, title: str, detail: str = "") -> None:
        with self._lock:
            queue = self._events.setdefault(project_id, collections.deque(maxlen=300))
            queue.append({
                "time": time.time(),
                "title": str(title),
                "detail": str(detail),
            })
            if project_id in self._meta:
                self._meta[project_id]["lastActive"] = time.time()

        # Seamlessly broadcast to centralized dashboard bus if available
        if _HAS_DASHBOARD_BUS:
            try:
                meta = self._meta.get(project_id, {})
                bus = dashboard_bus.DashboardDataBus.get_instance()
                bus.publish_event(
                    event_type=title,
                    description=detail or title,
                    camera_label=meta.get("projectName", project_id),
                    level="warning" if "error" in title.lower() else "info",
                    workflow_id=project_id,
                )
            except Exception:
                pass

    def _record_frame(self, project_id: str, node_id: str, frame: Any) -> None:
        if frame is None or not hasattr(frame, "shape"):
            return
        try:
            h, w = frame.shape[:2]
            # Compress for multi-monitor grid preview: max dim 640px, quality 70
            max_dim = 640
            out_frame = frame
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                out_frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

            ok, encoded = cv2.imencode(".jpg", out_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ok:
                with self._lock:
                    self._previews[project_id] = encoded.tobytes()
                    if project_id in self._meta:
                        self._meta[project_id]["lastActive"] = time.time()
        except Exception:
            pass


# Global singleton instance
fleet_manager = WorkflowFleetManager(max_concurrent=10)
