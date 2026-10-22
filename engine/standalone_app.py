"""Streamlit Web Application for Exported Afi Vision Workflows."""

from __future__ import annotations

import copy
import json
import os
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import streamlit as st

ROOT = Path(__file__).resolve().parent
os.environ["VISONODE_APP_DATA_DIR"] = str(ROOT / "data")
sys.path.insert(0, str(ROOT / "engine"))

try:
    import core
    from standalone_run import load_workflow
except ImportError:
    # If running directly inside engine directory
    sys.path.insert(0, str(ROOT))
    import core
    from standalone_run import load_workflow


class StreamlitAppBridge:
    """Thread-safe bridge between background WorkflowRunner and Streamlit frontend."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.runner = None
        self.latest_frame: np.ndarray | None = None
        self.logs: list[str] = []
        self.events: list[str] = []
        self.is_running = False
        self.frame_count = 0
        self.start_time: float | None = None
        self.last_error: str | None = None

    def on_log(self, message: str) -> None:
        with self.lock:
            timestamp = time.strftime("%H:%M:%S")
            self.logs.append(f"[{timestamp}] {message}")
            if len(self.logs) > 200:
                self.logs.pop(0)

    def on_event(self, *parts: str) -> None:
        with self.lock:
            timestamp = time.strftime("%H:%M:%S")
            entry = f"[{timestamp}] " + " | ".join(str(p) for p in parts)
            self.events.append(entry)
            if len(self.events) > 200:
                self.events.pop(0)

    def on_frame(self, node_id: str, frame: np.ndarray, has_annotation: bool) -> None:
        with self.lock:
            self.latest_frame = frame
            self.frame_count += 1

    def start(self, workflow: dict) -> None:
        with self.lock:
            if self.runner is not None and self.runner.is_running():
                return
            self.last_error = None
            self.frame_count = 0
            self.start_time = time.time()
            self.latest_frame = None
            self.runner = core.WorkflowRunner(
                on_log=self.on_log,
                on_event=self.on_event,
                on_frame=self.on_frame,
            )
            self.runner.start(workflow)
            self.is_running = True

    def stop(self) -> None:
        with self.lock:
            if self.runner is not None:
                try:
                    self.runner.stop()
                except Exception as exc:
                    self.last_error = str(exc)
                self.runner = None
            self.is_running = False

    def get_state(self) -> dict:
        with self.lock:
            active = self.runner is not None and self.runner.is_running()
            status = self.runner.status() if active else {}
            error = self.last_error or (status.get("error") if active else None)
            return {
                "is_running": active,
                "frame": self.latest_frame,
                "logs": list(self.logs),
                "events": list(self.events),
                "fps": status.get("fps", 0.0) if active else 0.0,
                "object_count": status.get("objectCount", 0) if active else 0,
                "frame_count": self.frame_count,
                "duration": time.time() - self.start_time if (active and self.start_time) else 0.0,
                "error": error,
            }


@st.cache_resource
def get_bridge() -> StreamlitAppBridge:
    return StreamlitAppBridge()


def load_manifest() -> dict:
    manifest_path = ROOT / "manifest.json"
    if manifest_path.is_file():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"name": "Afi Vision Workflow", "version": "1.0.0", "models": [], "environment": []}


def main():
    st.set_page_config(
        page_title="Afi Vision — Live Workflow Web App",
        page_icon="👁️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom styling
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #0e1117;
                color: #e2e8f0;
            }
            .metric-card {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: center;
            }
            .badge-running {
                display: inline-block;
                background-color: rgba(16, 185, 129, 0.2);
                color: #10b981;
                border: 1px solid #10b981;
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 13px;
                font-weight: 600;
            }
            .badge-idle {
                display: inline-block;
                background-color: rgba(100, 116, 139, 0.2);
                color: #94a3b8;
                border: 1px solid #64748b;
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 13px;
                font-weight: 600;
            }
            .badge-error {
                display: inline-block;
                background-color: rgba(239, 68, 68, 0.2);
                color: #ef4444;
                border: 1px solid #ef4444;
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 13px;
                font-weight: 600;
            }
            .preview-frame-container {
                border: 1px solid #334155;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                background: #000;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    manifest = load_manifest()
    bridge = get_bridge()
    state = bridge.get_state()

    # Sidebar
    st.sidebar.markdown(f"## 👁️ {manifest.get('name', 'Workflow')}")
    st.sidebar.caption(f"Versi {manifest.get('version', '1.0.0')} • Standalone Web Runtime")

    # Status Badge in Sidebar
    if state["error"]:
        badge_html = f'<div class="badge-error">⚠️ ERROR: {state["error"][:30]}</div>'
    elif state["is_running"]:
        badge_html = '<div class="badge-running">● RUNNING</div>'
    else:
        badge_html = '<div class="badge-idle">○ IDLE (STOPPED)</div>'
    st.sidebar.markdown(badge_html, unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # Controls
    st.sidebar.markdown("### 🚀 Kontrol Pipeline")
    col_btn1, col_btn2 = st.sidebar.columns(2)
    start_clicked = col_btn1.button("▶️ Start", disabled=state["is_running"], use_container_width=True)
    stop_clicked = col_btn2.button("⏹️ Stop", disabled=not state["is_running"], use_container_width=True)

    # Load workflow config
    try:
        base_workflow = load_workflow()
    except Exception as exc:
        st.sidebar.error(f"Gagal memuat workflow: {exc}")
        base_workflow = None

    # Source Configuration
    st.sidebar.markdown("### 📹 Konfigurasi Sumber Input")
    source_node = None
    if base_workflow:
        for node in base_workflow.get("nodes", []):
            if node.get("type") in {"input", "ip_camera"} and node.get("enabled", True):
                source_node = node
                break

    source_mode = "Default"
    override_source = None
    if source_node:
        s_type = source_node.get("config", {}).get("sourceType", "camera")
        st.sidebar.caption(f"Tipe Sumber Node: `{s_type}`")
        if s_type == "camera":
            cam_idx = st.sidebar.number_input("Index Webcam / Kamera USB", min_value=0, max_value=10, value=int(source_node.get("config", {}).get("source") or 0))
            override_source = cam_idx
        elif s_type in {"video", "file", "image"}:
            current_path = str(source_node.get("config", {}).get("filePath") or "")
            path_input = st.sidebar.text_input("Path File Video / Gambar", value=current_path)
            override_source = path_input
            uploaded = st.sidebar.file_uploader("Atau Upload File Lokal", type=["mp4", "avi", "mov", "jpg", "png"])
            if uploaded:
                save_dir = ROOT / "data" / "uploads"
                save_dir.mkdir(parents=True, exist_ok=True)
                target_path = save_dir / uploaded.name
                target_path.write_bytes(uploaded.read())
                override_source = str(target_path)
                st.sidebar.success(f"File diupload: {uploaded.name}")
        elif s_type == "rtsp":
            current_url = str(source_node.get("config", {}).get("streamUrl") or source_node.get("config", {}).get("source") or "")
            url_input = st.sidebar.text_input("RTSP Stream URL", value=current_url)
            override_source = url_input

    # Model & Engine info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧠 Info Model & Engine")
    models = manifest.get("models", [])
    if models:
        for m in models:
            st.sidebar.text(f"• Node {m.get('nodeId')}: {Path(str(m.get('file') or m.get('field'))).name}")
    else:
        st.sidebar.caption("Tidak ada model khusus (Classical CV / Default)")

    # Handle Start / Stop
    if start_clicked and base_workflow:
        wf = copy.deepcopy(base_workflow)
        if source_node and override_source is not None:
            s_type = source_node.get("config", {}).get("sourceType", "camera")
            for node in wf.get("nodes", []):
                if node.get("id") == source_node.get("id"):
                    if s_type == "camera":
                        node["config"]["source"] = int(override_source)
                    elif s_type in {"video", "file", "image"}:
                        node["config"]["filePath"] = str(override_source)
                    elif s_type == "rtsp":
                        node["config"]["streamUrl"] = str(override_source)
        bridge.start(wf)
        st.rerun()

    if stop_clicked:
        bridge.stop()
        st.rerun()

    # Main Area
    st.title(f"👁️ {manifest.get('name', 'Afi Vision Workflow')}")
    st.caption("Afi Vision Standalone Web Streamlit Interface • Live Preview & Edge Processing")

    # Fragment for real-time video preview and metrics
    @st.fragment(run_every="50ms")
    def render_live_preview():
        cur = bridge.get_state()
        if cur["is_running"]:
            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("⚡ Pipeline FPS", f"{cur['fps']:.1f}")
            m2.metric("🎯 Object Count", f"{cur['object_count']}")
            m3.metric("🖼️ Processed Frames", f"{cur['frame_count']}")
            m4.metric("⏱️ Active Duration", f"{cur['duration']:.1f}s")

            # Video preview
            if cur["frame"] is not None:
                st.image(cur["frame"], channels="BGR", use_container_width=True)
            else:
                st.info("Sedang menghubungkan ke kamera / membaca sumber video...")
        else:
            st.markdown(
                """
                <div style="border: 2px dashed #475569; border-radius: 12px; padding: 70px 20px; text-align: center; background: rgba(30, 41, 59, 0.4); margin: 20px 0;">
                    <div style="font-size: 48px; margin-bottom: 12px;">📹</div>
                    <h3 style="color: #cbd5e1; margin-bottom: 6px;">Live Preview Standby</h3>
                    <p style="color: #94a3b8; font-size: 15px; max-width: 600px; margin: 0 auto;">
                        Workflow siap dijalankan. Klik tombol <b>▶️ Start</b> di panel sidebar untuk memulai deteksi dan streaming langsung dengan preview visual OpenCV.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    render_live_preview()

    # Tabs for deeper diagnostics
    tab_logs, tab_events, tab_graph = st.tabs(["📋 Realtime Logs", "🔔 Deteksi & Event", "⚙️ Pipeline Nodes"])

    with tab_logs:
        logs = state["logs"]
        if logs:
            st.code("\n".join(logs[-40:]), language="text")
        else:
            st.caption("Belum ada log aktif. Mulai pipeline untuk melihat log eksekusi.")

    with tab_events:
        events = state["events"]
        if events:
            for ev in reversed(events[-20:]):
                st.markdown(f"`{ev}`")
        else:
            st.caption("Belum ada event / alert yang dipicu.")

    with tab_graph:
        if base_workflow:
            nodes_info = [{"ID": n.get("id"), "Type": n.get("type"), "Enabled": n.get("enabled", True)} for n in base_workflow.get("nodes", [])]
            st.table(nodes_info)
        else:
            st.caption("Workflow graph tidak tersedia.")


if __name__ == "__main__":
    main()
