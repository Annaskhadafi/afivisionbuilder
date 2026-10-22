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
sys.path.insert(0, str(ROOT))

try:
    import core
except ImportError:
    pass

# Resilient import of load_workflow whether packaged as run.py or standalone_run.py
load_workflow = None
try:
    from run import load_workflow as _lw
    load_workflow = _lw
except ImportError:
    try:
        from standalone_run import load_workflow as _lw
        load_workflow = _lw
    except ImportError:
        import importlib.util
        for candidate_name in ["run.py", "standalone_run.py"]:
            candidate_path = ROOT / candidate_name
            if candidate_path.is_file():
                spec = importlib.util.spec_from_file_location("runner_module", candidate_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    load_workflow = getattr(mod, "load_workflow", None)
                    if load_workflow:
                        break

if load_workflow is None:
    raise ImportError("Tidak dapat menemukan modul 'run.py' atau 'standalone_run.py' untuk memuat workflow.")


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


# Module-level live preview fragment
@st.fragment(run_every=0.08)
def live_preview_widget(bridge: StreamlitAppBridge):
    state = bridge.get_state()
    if state["is_running"]:
        # Realtime metrics
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("⚡ Pipeline FPS", f"{state['fps']:.1f}")
        col_m2.metric("🎯 Objek Terdeteksi", f"{state['object_count']}")
        col_m3.metric("🖼️ Total Frame", f"{state['frame_count']}")
        col_m4.metric("⏱️ Waktu Berjalan", f"{state['duration']:.1f}s")

        if state["frame"] is not None:
            st.image(state["frame"], channels="BGR", use_container_width=True)
        else:
            st.info("⏳ Menghubungkan ke sumber video... Frame teranotasi pertama sedang diproses.")
    elif state["error"]:
        st.error(f"⚠️ Terjadi kendala pada pipeline eksekusi: {state['error']}")
        st.markdown(
            """
            <div style="border: 1px solid #ef4444; border-radius: 8px; padding: 20px; background: rgba(239, 68, 68, 0.1); margin: 10px 0;">
                <p style="color: #fca5a5; margin-bottom: 0;">Silakan periksa log eksekusi pada tab <b>📋 Realtime Logs</b> di bawah untuk melihat pesan error lengkap.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="border: 2px dashed #475569; border-radius: 12px; padding: 50px 20px; text-align: center; background: rgba(30, 41, 59, 0.4); margin: 16px 0;">
                <div style="font-size: 48px; margin-bottom: 12px;">📹</div>
                <h3 style="color: #cbd5e1; margin-bottom: 6px;">Live Video Standby</h3>
                <p style="color: #94a3b8; font-size: 15px; max-width: 600px; margin: 0 auto;">
                    Klik tombol <b>▶️ Start / Jalankan Stream</b> di atas untuk memulai video streaming dan deteksi AI secara langsung.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


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
        </style>
        """,
        unsafe_allow_html=True,
    )

    manifest = load_manifest()
    bridge = get_bridge()
    state = bridge.get_state()

    # Load workflow config
    try:
        base_workflow = load_workflow()
    except Exception as exc:
        st.error(f"Gagal memuat workflow: {exc}")
        base_workflow = None

    # Detect primary source node
    source_node = None
    if base_workflow:
        for node in base_workflow.get("nodes", []):
            if node.get("type") in {"input", "ip_camera"} and node.get("enabled", True):
                source_node = node
                break

    # Top Header on Main Area
    col_hdr1, col_hdr2 = st.columns([3, 1])
    with col_hdr1:
        st.markdown(f"## 👁️ {manifest.get('name', 'Afi Vision Workflow')}")
        st.caption(f"Versi {manifest.get('version', '1.0.0')} • Standalone Web Runtime")
    with col_hdr2:
        if state["error"]:
            st.markdown('<div style="text-align: right; margin-top: 10px;"><span class="badge-error">⚠️ ERROR</span></div>', unsafe_allow_html=True)
        elif state["is_running"]:
            st.markdown('<div style="text-align: right; margin-top: 10px;"><span class="badge-running">● LIVE STREAMING</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: right; margin-top: 10px;"><span class="badge-idle">○ STANDBY (OFF)</span></div>', unsafe_allow_html=True)

    # Main Action Toolbar (Prominent buttons at the top of the main screen)
    col_act1, col_act2, col_act3 = st.columns([2, 2, 4])
    start_clicked = col_act1.button("▶️ Start / Jalankan Stream", disabled=state["is_running"], type="primary", use_container_width=True)
    stop_clicked = col_act2.button("⏹️ Stop / Hentikan Stream", disabled=not state["is_running"], use_container_width=True)

    # Auto-start on first load if not explicitly stopped
    if "auto_started" not in st.session_state:
        st.session_state["auto_started"] = True
        if not state["is_running"] and base_workflow:
            bridge.start(copy.deepcopy(base_workflow))
            st.rerun()

    # Sidebar details (for optional deep adjustments)
    st.sidebar.markdown(f"### ⚙️ Pengaturan Sumber & Parameter")
    override_source = None
    if source_node:
        s_type = source_node.get("config", {}).get("sourceType", "camera")
        st.sidebar.caption(f"Tipe Sumber: `{s_type}`")
        if s_type == "camera":
            cam_idx = st.sidebar.number_input("Index Kamera USB / Webcam", min_value=0, max_value=10, value=int(source_node.get("config", {}).get("source") or 0))
            override_source = cam_idx
        elif s_type in {"video", "file", "image"}:
            current_path = str(source_node.get("config", {}).get("filePath") or "")
            path_input = st.sidebar.text_input("Path File Video / Gambar", value=current_path)
            override_source = path_input
            uploaded = st.sidebar.file_uploader("Upload Video / Gambar", type=["mp4", "avi", "mov", "jpg", "png"])
            if uploaded:
                save_dir = ROOT / "data" / "uploads"
                save_dir.mkdir(parents=True, exist_ok=True)
                target_path = save_dir / uploaded.name
                target_path.write_bytes(uploaded.read())
                override_source = str(target_path)
                st.sidebar.success(f"Uploaded: {uploaded.name}")
        elif s_type == "youtube":
            current_url = str(source_node.get("config", {}).get("youtubeUrl") or "")
            yt_url_input = st.sidebar.text_input("YouTube Stream URL", value=current_url)
            override_source = yt_url_input
        elif s_type == "rtsp":
            current_url = str(source_node.get("config", {}).get("streamUrl") or source_node.get("config", {}).get("source") or "")
            url_input = st.sidebar.text_input("RTSP Stream URL", value=current_url)
            override_source = url_input

    # Model & Engine info in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧠 Model AI & Aset")
    models = manifest.get("models", [])
    if models:
        for m in models:
            st.sidebar.text(f"• Node {m.get('nodeId')}: {Path(str(m.get('file') or m.get('field'))).name}")
    else:
        st.sidebar.caption("Tidak ada model khusus (Classical CV / Default)")

    # Handle Start / Stop actions
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
                    elif s_type == "youtube":
                        node["config"]["youtubeUrl"] = str(override_source)
                    elif s_type == "rtsp":
                        node["config"]["streamUrl"] = str(override_source)
        bridge.start(wf)
        st.rerun()

    if stop_clicked:
        bridge.stop()
        st.rerun()

    # Render Main Live Preview Widget
    live_preview_widget(bridge)

    # Diagnostic Tabs at the bottom
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
