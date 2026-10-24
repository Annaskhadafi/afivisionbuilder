from __future__ import annotations

import io
import json
import logging
import os
import sqlite3
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("afi.dashboard_bus")

try:
    import pandas as pd
    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False

try:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    _HAS_OPENPYXL = True
except ImportError:
    _HAS_OPENPYXL = False


class DashboardDataBus:
    """
    Afivision Universal Data Bus & SQLite Time-Series Metrics Logger.
    Provides singleton pub/sub for all CV workflows, live snapshot for widgets,
    time-series storage for analytics charts, and Excel export generation.
    """
    _instance: Optional[DashboardDataBus] = None
    _lock = threading.RLock()

    @classmethod
    def get_instance(cls, data_dir: Optional[str | Path] = None) -> DashboardDataBus:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(data_dir=data_dir)
            return cls._instance

    def __init__(self, data_dir: Optional[str | Path] = None):
        if data_dir is None:
            data_dir = os.environ.get("VISONODE_APP_DATA_DIR", "data")
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.dashboards_dir = self.data_dir / "dashboards"
        self.dashboards_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.data_dir / "dashboard_history.db"
        self._init_sqlite()

        # In-memory fast state
        self._metrics: dict[str, dict[str, Any]] = {}
        self._cameras: dict[str, dict[str, Any]] = {}
        self._recent_events: deque[dict[str, Any]] = deque(maxlen=2000)
        self._last_sqlite_flush: dict[str, float] = {}

    def _init_sqlite(self) -> None:
        """Initialize SQLite database for historical metrics and event logs."""
        try:
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS metrics_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp_epoch REAL NOT NULL,
                        timestamp_iso TEXT NOT NULL,
                        workflow_id TEXT NOT NULL DEFAULT '',
                        node_id TEXT NOT NULL DEFAULT '',
                        metric_key TEXT NOT NULL,
                        metric_label TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        unit TEXT NOT NULL DEFAULT '',
                        status TEXT NOT NULL DEFAULT 'normal',
                        camera_label TEXT NOT NULL DEFAULT '',
                        stream_id TEXT NOT NULL DEFAULT '',
                        extra_json TEXT NOT NULL DEFAULT '{}'
                    );
                    CREATE INDEX IF NOT EXISTS idx_metrics_key_time 
                        ON metrics_history(metric_key, timestamp_epoch);
                    CREATE INDEX IF NOT EXISTS idx_metrics_cam_time 
                        ON metrics_history(camera_label, timestamp_epoch);

                    CREATE TABLE IF NOT EXISTS event_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp_epoch REAL NOT NULL,
                        timestamp_iso TEXT NOT NULL,
                        workflow_id TEXT NOT NULL DEFAULT '',
                        node_id TEXT NOT NULL DEFAULT '',
                        event_type TEXT NOT NULL,
                        camera_label TEXT NOT NULL DEFAULT '',
                        description TEXT NOT NULL,
                        level TEXT NOT NULL DEFAULT 'info',
                        metadata_json TEXT NOT NULL DEFAULT '{}'
                    );
                    CREATE INDEX IF NOT EXISTS idx_events_time 
                        ON event_logs(timestamp_epoch);
                    CREATE INDEX IF NOT EXISTS idx_events_cam 
                        ON event_logs(camera_label);
                    """
                )
        except Exception as e:
            logger.error(f"Gagal inisialisasi basis data dashboard: {e}")

    # -------------------------------------------------------------------------
    # Publish & Ingest API
    # -------------------------------------------------------------------------
    def publish_metric(
        self,
        metric_key: str,
        value: float | int,
        label: str = "",
        unit: str = "",
        status: str = "normal",
        workflow_id: str = "default",
        node_id: str = "",
        camera_label: str = "",
        stream_id: str = "",
        extra_data: Optional[dict[str, Any]] = None,
        flush_interval_seconds: float = 2.0,
    ) -> dict[str, Any]:
        """Publish a metric reading from a workflow node or dashboard_sink."""
        now = time.time()
        iso_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        metric_record = {
            "key": metric_key,
            "label": label or metric_key,
            "value": float(value),
            "unit": unit,
            "status": status.lower(),
            "workflow_id": workflow_id,
            "node_id": node_id,
            "camera_label": camera_label,
            "stream_id": stream_id,
            "timestamp": now,
            "timestamp_iso": iso_str,
            "extra": extra_data or {},
        }

        with self._lock:
            self._metrics[metric_key] = metric_record

            # Throttled SQLite persistence to prevent disk thrashing
            last_flush = self._last_sqlite_flush.get(metric_key, 0.0)
            if now - last_flush >= flush_interval_seconds:
                self._last_sqlite_flush[metric_key] = now
                self._persist_metric_async(metric_record)

        return metric_record

    def publish_event(
        self,
        event_type: str,
        description: str,
        camera_label: str = "",
        level: str = "info",
        workflow_id: str = "default",
        node_id: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Publish an operational event or detection alert."""
        now = time.time()
        iso_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        event_record = {
            "id": f"EVT-{int(now * 1000)}",
            "type": event_type,
            "description": description,
            "camera_label": camera_label or "Sistem",
            "level": level.lower(),
            "workflow_id": workflow_id,
            "node_id": node_id,
            "timestamp": now,
            "timestamp_iso": iso_str,
            "metadata": metadata or {},
        }

        with self._lock:
            self._recent_events.appendleft(event_record)
            self._persist_event_async(event_record)

        return event_record

    def update_camera_status(
        self,
        stream_id: str,
        camera_label: str,
        status: str = "online",
        fps: float = 0.0,
        resolution: tuple[int, int] = (0, 0),
        workflow_id: str = "default",
    ) -> None:
        """Update live camera connectivity status."""
        now = time.time()
        with self._lock:
            self._cameras[stream_id] = {
                "stream_id": stream_id,
                "camera_label": camera_label or stream_id,
                "status": status,
                "fps": round(fps, 1),
                "resolution": f"{resolution[0]}x{resolution[1]}" if resolution[0] > 0 else "N/A",
                "last_seen": now,
                "workflow_id": workflow_id,
            }

    # -------------------------------------------------------------------------
    # Background SQLite Writers
    # -------------------------------------------------------------------------
    def _persist_metric_async(self, record: dict[str, Any]) -> None:
        def _write():
            try:
                with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                    conn.execute(
                        """
                        INSERT INTO metrics_history (
                            timestamp_epoch, timestamp_iso, workflow_id, node_id,
                            metric_key, metric_label, metric_value, unit, status,
                            camera_label, stream_id, extra_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record["timestamp"],
                            record["timestamp_iso"],
                            record["workflow_id"],
                            record["node_id"],
                            record["key"],
                            record["label"],
                            record["value"],
                            record["unit"],
                            record["status"],
                            record["camera_label"],
                            record["stream_id"],
                            json.dumps(record.get("extra", {})),
                        ),
                    )
            except Exception as e:
                logger.debug(f"Gagal menulis metrik historis ke SQLite: {e}")

        threading.Thread(target=_write, daemon=True).start()

    def _persist_event_async(self, record: dict[str, Any]) -> None:
        def _write():
            try:
                with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                    conn.execute(
                        """
                        INSERT INTO event_logs (
                            timestamp_epoch, timestamp_iso, workflow_id, node_id,
                            event_type, camera_label, description, level, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record["timestamp"],
                            record["timestamp_iso"],
                            record["workflow_id"],
                            record["node_id"],
                            record["type"],
                            record["camera_label"],
                            record["description"],
                            record["level"],
                            json.dumps(record.get("metadata", {})),
                        ),
                    )
            except Exception as e:
                logger.debug(f"Gagal menulis log kejadian ke SQLite: {e}")

        threading.Thread(target=_write, daemon=True).start()

    # -------------------------------------------------------------------------
    # Query API for Dashboard & Widgets
    # -------------------------------------------------------------------------
    def get_live_snapshot(self) -> dict[str, Any]:
        """Return full live state for WebSocket broadcast or polling."""
        with self._lock:
            # Check camera heartbeats (offline if no update > 6 seconds)
            now = time.time()
            cams = {}
            for k, cam in self._cameras.items():
                cam_copy = dict(cam)
                if now - cam.get("last_seen", 0) > 6.0:
                    cam_copy["status"] = "offline"
                cams[k] = cam_copy

            return {
                "timestamp": now,
                "timestamp_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
                "metrics": dict(self._metrics),
                "cameras": cams,
                "recent_events": list(self._recent_events)[:60],
            }

    def get_historical_timeseries(
        self,
        metric_key: Optional[str] = None,
        hours: float = 24.0,
        camera_label: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Return time-series points for trend line/bar charts."""
        since_epoch = time.time() - (hours * 3600.0)
        query = """
            SELECT timestamp_epoch, timestamp_iso, metric_key, metric_label, 
                   metric_value, unit, status, camera_label
            FROM metrics_history
            WHERE timestamp_epoch >= ?
        """
        params: list[Any] = [since_epoch]

        if metric_key:
            query += " AND metric_key = ?"
            params.append(metric_key)
        if camera_label:
            query += " AND camera_label = ?"
            params.append(camera_label)

        query += " ORDER BY timestamp_epoch ASC LIMIT 1000"

        points = []
        try:
            with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                cursor = conn.cursor()
                for row in cursor.execute(query, params):
                    points.append({
                        "timestamp": row[0],
                        "time_iso": row[1],
                        "key": row[2],
                        "label": row[3],
                        "value": row[4],
                        "unit": row[5],
                        "status": row[6],
                        "camera_label": row[7],
                    })
        except Exception as e:
            logger.error(f"Gagal mengambil riwayat grafik dari SQLite: {e}")

        return points

    def get_events(
        self,
        limit: int = 100,
        camera_label: Optional[str] = None,
        level: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Query event logs with filtering for Live Event Table widget."""
        query = """
            SELECT id, timestamp_epoch, timestamp_iso, event_type, 
                   camera_label, description, level, metadata_json
            FROM event_logs
            WHERE 1=1
        """
        params: list[Any] = []

        if start_time is not None:
            query += " AND timestamp_epoch >= ?"
            params.append(start_time)
        if end_time is not None:
            query += " AND timestamp_epoch <= ?"
            params.append(end_time)
        if camera_label:
            query += " AND camera_label = ?"
            params.append(camera_label)
        if level:
            query += " AND level = ?"
            params.append(level.lower())

        query += " ORDER BY timestamp_epoch DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))

        events = []
        try:
            with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                cursor = conn.cursor()
                for row in cursor.execute(query, params):
                    meta = {}
                    try:
                        meta = json.loads(row[7])
                    except Exception:
                        pass
                    events.append({
                        "id": f"LOG-{row[0]}",
                        "timestamp": row[1],
                        "timestamp_iso": row[2],
                        "type": row[3],
                        "camera_label": row[4],
                        "description": row[5],
                        "level": row[6],
                        "metadata": meta,
                    })
        except Exception as e:
            logger.error(f"Gagal mengambil daftar event dari SQLite: {e}")

        return events

    # -------------------------------------------------------------------------
    # Excel Report Generator (.XLSX)
    # -------------------------------------------------------------------------
    def export_excel(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        camera_label: Optional[str] = None,
    ) -> bytes:
        """
        Generate professionally formatted Excel workbook (.xlsx) containing
        Summary, Metrics Log, and Event Log sheets.
        """
        events = self.get_events(limit=5000, camera_label=camera_label, start_time=start_time, end_time=end_time)
        metrics = self.get_historical_timeseries(hours=168.0, camera_label=camera_label)

        if _HAS_OPENPYXL:
            import openpyxl
            from openpyxl.styles import Alignment, Font, PatternFill
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()
            # 1. Summary Sheet
            ws_summary: Any = wb.active
            ws_summary.title = "Ringkasan Eksekutif"
            ws_summary.views.sheetView[0].showGridLines = True

            header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
            header_font = Font(name="Segoe UI", size=14, bold=True, color="FFFFFF")
            sub_font = Font(name="Segoe UI", size=10, italic=True, color="64748B")
            title_cell = ws_summary["B2"]
            title_cell.value = "LAPORAN OPERASIONAL COMPUTER VISION — AFIVISION"
            title_cell.font = header_font
            title_cell.fill = header_fill
            title_cell.alignment = Alignment(horizontal="left", vertical="center")
            ws_summary.row_dimensions[2].height = 36

            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
            ws_summary["B3"].value = f"Waktu Ekspor: {now_str} | Lingkup: {camera_label or 'Semua Kamera'}"
            ws_summary["B3"].font = sub_font

            # KPI stats table
            kpi_labels = ["Total Kejadian Tercatat", "Kejadian Bahaya (Alert)", "Total Metrik Tersimpan", "Kamera Aktif"]
            alert_count = sum(1 for e in events if e.get("level") in ("danger", "critical", "warning"))
            kpi_values = [len(events), alert_count, len(metrics), len(self._cameras)]

            col_header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
            col_header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")

            for col_idx, (lbl, val) in enumerate(zip(kpi_labels, kpi_values), start=2):
                col_letter = get_column_letter(col_idx)
                c_head = ws_summary[f"{col_letter}5"]
                c_head.value = lbl
                c_head.font = col_header_font
                c_head.fill = col_header_fill
                c_head.alignment = Alignment(horizontal="center", vertical="center")

                c_val = ws_summary[f"{col_letter}6"]
                c_val.value = val
                c_val.font = Font(name="Segoe UI", size=16, bold=True, color="0284C7")
                c_val.alignment = Alignment(horizontal="center", vertical="center")
                ws_summary.column_dimensions[col_letter].width = 28

            ws_summary.row_dimensions[5].height = 24
            ws_summary.row_dimensions[6].height = 32

            # 2. Events Log Sheet
            ws_events = wb.create_sheet(title="Log Kejadian")
            ws_events.views.sheetView[0].showGridLines = True
            event_headers = ["ID Event", "Waktu (ISO)", "Kamera / Lokasi", "Kategori", "Tingkat", "Deskripsi Detail"]
            for col_idx, h in enumerate(event_headers, start=1):
                col_letter = get_column_letter(col_idx)
                cell = ws_events[f"{col_letter}1"]
                cell.value = h
                cell.font = col_header_font
                cell.fill = col_header_fill
                cell.alignment = Alignment(horizontal="left", vertical="center")

            for row_idx, ev in enumerate(events, start=2):
                ws_events[f"A{row_idx}"].value = ev["id"]
                ws_events[f"B{row_idx}"].value = ev["timestamp_iso"]
                ws_events[f"C{row_idx}"].value = ev["camera_label"]
                ws_events[f"D{row_idx}"].value = ev["type"]
                ws_events[f"E{row_idx}"].value = ev["level"].upper()
                ws_events[f"F{row_idx}"].value = ev["description"]

                # Highlight warning/danger rows
                lvl = ev.get("level", "").lower()
                if lvl in ("danger", "critical"):
                    fill_color = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                    for c_idx in range(1, 7):
                        ws_events[f"{get_column_letter(c_idx)}{row_idx}"].fill = fill_color
                elif lvl == "warning":
                    fill_color = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
                    for c_idx in range(1, 7):
                        ws_events[f"{get_column_letter(c_idx)}{row_idx}"].fill = fill_color

            # Auto fit columns
            for col in ws_events.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws_events.column_dimensions[col_letter].width = max(max_len + 4, 14)

            # 3. Metrics Log Sheet
            ws_metrics = wb.create_sheet(title="Rekap Angka Metrik")
            ws_metrics.views.sheetView[0].showGridLines = True
            metric_headers = ["Waktu (ISO)", "Kunci Metrik", "Label Metrik", "Nilai", "Satuan", "Status", "Kamera"]
            for col_idx, h in enumerate(metric_headers, start=1):
                col_letter = get_column_letter(col_idx)
                cell = ws_metrics[f"{col_letter}1"]
                cell.value = h
                cell.font = col_header_font
                cell.fill = col_header_fill

            for row_idx, m in enumerate(metrics, start=2):
                ws_metrics[f"A{row_idx}"].value = m["time_iso"]
                ws_metrics[f"B{row_idx}"].value = m["key"]
                ws_metrics[f"C{row_idx}"].value = m["label"]
                ws_metrics[f"D{row_idx}"].value = m["value"]
                ws_metrics[f"E{row_idx}"].value = m["unit"]
                ws_metrics[f"F{row_idx}"].value = m["status"].upper()
                ws_metrics[f"G{row_idx}"].value = m["camera_label"]

            for col in ws_metrics.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws_metrics.column_dimensions[col_letter].width = max(max_len + 4, 14)

            buf = io.BytesIO()
            wb.save(buf)
            return buf.getvalue()

        # Fallback to simple CSV in memory if openpyxl is unavailable
        out = io.StringIO()
        out.write("Waktu,Kamera,Kategori,Tingkat,Deskripsi\n")
        for ev in events:
            out.write(f'"{ev["timestamp_iso"]}","{ev["camera_label"]}","{ev["type"]}","{ev["level"]}","{ev["description"]}"\n')
        return out.getvalue().encode("utf-8")

    # -------------------------------------------------------------------------
    # Dashboard Layout Persistence
    # -------------------------------------------------------------------------
    def save_layout(self, project_id: str, layout_data: dict[str, Any]) -> str:
        """Save user's custom drag-and-drop dashboard layout."""
        clean_id = "".join(c for c in project_id if c.isalnum() or c in ("-", "_")).strip() or "default"
        file_path = self.dashboards_dir / f"{clean_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(layout_data, f, indent=2, ensure_ascii=False)
        return str(file_path)

    def load_layout(self, project_id: str) -> dict[str, Any]:
        """Load dashboard layout or return a rich production starter template."""
        clean_id = "".join(c for c in project_id if c.isalnum() or c in ("-", "_")).strip() or "default"
        file_path = self.dashboards_dir / f"{clean_id}.json"

        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Gagal membaca layout dashboard {clean_id}: {e}")

        # Return default starter layout
        return self._generate_default_layout(clean_id)

    def _generate_default_layout(self, project_id: str) -> dict[str, Any]:
        """Generate default modern dashboard with 5 core widgets & Elementor headers."""
        return {
            "version": "1.0.0",
            "project_id": project_id,
            "title": "Pusat Kendali & Pemantauan Visi Operasional",
            "theme": "dark",
            "canvas": {
                "width": 1440,
                "height": 960,
                "background": "#0F172A",
            },
            "widgets": [
                # 1. Header Title Text (Elementor Custom Text)
                {
                    "id": "w_header_title",
                    "type": "custom_text",
                    "x": 30,
                    "y": 24,
                    "w": 650,
                    "h": 60,
                    "z": 1,
                    "config": {
                        "text": "Pusat Kendali AI Vision & Pemantauan Operasional",
                        "tag": "h1",
                        "fontSize": 24,
                        "fontWeight": "bold",
                        "color": "#F8FAFC",
                        "subtitle": "Pemantauan CCTV Real-time, Rekapitulasi Deteksi, dan Log Pelanggaran",
                    },
                },
                # 2. Status Badge / Company Logo
                {
                    "id": "w_status_badge",
                    "type": "status_badge",
                    "x": 1200,
                    "y": 30,
                    "w": 210,
                    "h": 48,
                    "z": 1,
                    "config": {
                        "label": "Sistem Aktif (Live)",
                        "status": "online",
                        "shift": "Shift 1 (Operasional)",
                    },
                },
                # 3. Scorecard 1: Total Objek / Pekerja
                {
                    "id": "w_scorecard_1",
                    "type": "scorecard",
                    "x": 30,
                    "y": 95,
                    "w": 260,
                    "h": 120,
                    "z": 2,
                    "config": {
                        "metricKey": "total_person",
                        "title": "Total Personel / Pekerja",
                        "unit": "Orang",
                        "icon": "users",
                        "warningThreshold": 15,
                        "dangerThreshold": 30,
                        "defaultValue": 8,
                    },
                },
                # 4. Scorecard 2: Pelanggaran APD / Anomali
                {
                    "id": "w_scorecard_2",
                    "type": "scorecard",
                    "x": 310,
                    "y": 95,
                    "w": 260,
                    "h": 120,
                    "z": 2,
                    "config": {
                        "metricKey": "violation_count",
                        "title": "Peringatan / Pelanggaran",
                        "unit": "Insiden",
                        "icon": "shield-alert",
                        "warningThreshold": 1,
                        "dangerThreshold": 5,
                        "defaultValue": 0,
                    },
                },
                # 5. Scorecard 3: Kendaraan / Alur Masuk
                {
                    "id": "w_scorecard_3",
                    "type": "scorecard",
                    "x": 590,
                    "y": 95,
                    "w": 260,
                    "h": 120,
                    "z": 2,
                    "config": {
                        "metricKey": "vehicle_flow",
                        "title": "Laju Kendaraan Gerbang",
                        "unit": "Unit/Jam",
                        "icon": "truck",
                        "warningThreshold": 40,
                        "dangerThreshold": 60,
                        "defaultValue": 18,
                    },
                },
                # 6. Tombol Ekspor Excel
                {
                    "id": "w_btn_excel",
                    "type": "excel_export_btn",
                    "x": 1200,
                    "y": 95,
                    "w": 210,
                    "h": 50,
                    "z": 2,
                    "config": {
                        "label": "Unduh Rekap Excel (.xlsx)",
                        "includeEvents": True,
                        "includeMetrics": True,
                    },
                },
                # 7. CCTV Player 1: Kamera Utama / Workshop
                {
                    "id": "w_cctv_1",
                    "type": "cctv_player",
                    "x": 30,
                    "y": 235,
                    "w": 660,
                    "h": 400,
                    "z": 3,
                    "config": {
                        "cameraLabel": "Kamera 01 — Area Produksi Utama",
                        "streamId": "cam_01",
                        "nodeId": "preview",
                        "showAnnotatedToggle": True,
                        "showSnapshotBtn": True,
                        "showFullscreenBtn": True,
                        "defaultMode": "annotated",
                    },
                },
                # 8. CCTV Player 2: Kamera Gerbang / Gudang
                {
                    "id": "w_cctv_2",
                    "type": "cctv_player",
                    "x": 710,
                    "y": 235,
                    "w": 700,
                    "h": 400,
                    "z": 3,
                    "config": {
                        "cameraLabel": "Kamera 02 — Gerbang Masuk & Parkir",
                        "streamId": "cam_02",
                        "nodeId": "detector",
                        "showAnnotatedToggle": True,
                        "showSnapshotBtn": True,
                        "showFullscreenBtn": True,
                        "defaultMode": "annotated",
                    },
                },
                # 9. Trend Chart Widget
                {
                    "id": "w_trend_chart",
                    "type": "trend_chart",
                    "x": 30,
                    "y": 655,
                    "w": 660,
                    "h": 280,
                    "z": 4,
                    "config": {
                        "title": "Grafik Tren Fluktuasi Deteksi (24 Jam)",
                        "metricKey": "total_person",
                        "chartType": "line",
                        "rangeHours": 24,
                    },
                },
                # 10. Live Event Table Widget
                {
                    "id": "w_event_table",
                    "type": "event_table",
                    "x": 710,
                    "y": 655,
                    "w": 700,
                    "h": 280,
                    "z": 4,
                    "config": {
                        "title": "Tabel Log Kejadian Real-time",
                        "maxRows": 25,
                        "autoScroll": True,
                        "showFilter": True,
                    },
                },
            ],
        }
