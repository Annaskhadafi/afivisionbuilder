from __future__ import annotations

import json
import queue
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from workflow_store import APP_DATA_DIR


DEFAULT_DB_FILENAME = "visonode.db"


def default_database_path() -> Path:
    return APP_DATA_DIR / DEFAULT_DB_FILENAME


def _json_dump(value: Any) -> str:
    try:
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps(str(value), separators=(",", ":"))


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bbox_xywh(detection: dict) -> tuple[float | None, float | None, float | None, float | None]:
    value = None
    for key in ("bbox", "box", "xywh"):
        candidate = detection.get(key)
        if isinstance(candidate, (list, tuple)) and len(candidate) >= 4:
            value = candidate
            break
    if value is None:
        xyxy = detection.get("xyxy")
        if isinstance(xyxy, (list, tuple)) and len(xyxy) >= 4:
            x1, y1, x2, y2 = [_float_or_none(item) for item in xyxy[:4]]
            if None not in (x1, y1, x2, y2):
                return x1, y1, x2 - x1, y2 - y1
        return None, None, None, None
    x, y, width, height = [_float_or_none(item) for item in value[:4]]
    return x, y, width, height


def connect_database(path: str | Path | None = None) -> sqlite3.Connection:
    db_path = Path(path).expanduser() if path else default_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=5.0, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA busy_timeout=5000")
    initialize_schema(conn)
    return conn


def initialize_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL DEFAULT '',
            workflow_json TEXT NOT NULL,
            started_at REAL NOT NULL,
            stopped_at REAL,
            status TEXT NOT NULL DEFAULT 'running'
        );

        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            frame_index INTEGER NOT NULL,
            timestamp_ms INTEGER NOT NULL,
            fps REAL,
            object_count INTEGER,
            width INTEGER,
            height INTEGER,
            FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            frame_index INTEGER NOT NULL,
            timestamp_ms INTEGER NOT NULL,
            node_id TEXT NOT NULL,
            source_node_id TEXT NOT NULL DEFAULT '',
            class_name TEXT NOT NULL DEFAULT 'object',
            confidence REAL,
            x REAL,
            y REAL,
            width REAL,
            height REAL,
            track_id INTEGER,
            payload_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            timestamp_ms INTEGER NOT NULL,
            node_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            inspection_node_id TEXT NOT NULL DEFAULT '',
            source_node_id TEXT NOT NULL DEFAULT '',
            track_id INTEGER NOT NULL,
            detection_class TEXT NOT NULL DEFAULT 'object',
            detection_confidence REAL,
            classification_class TEXT,
            classification_confidence REAL,
            first_seen_ms INTEGER NOT NULL,
            inspected_at_ms INTEGER NOT NULL,
            snapshot_path TEXT NOT NULL DEFAULT '',
            inspection_status TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '{}',
            UNIQUE(run_id, inspection_node_id, source_node_id, track_id),
            FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS count_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            timestamp_ms INTEGER NOT NULL,
            counter_node_id TEXT NOT NULL,
            source_node_id TEXT NOT NULL DEFAULT '',
            track_id INTEGER,
            class_name TEXT NOT NULL DEFAULT 'object',
            direction TEXT NOT NULL DEFAULT '',
            cumulative_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS node_debug (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            timestamp_ms INTEGER NOT NULL,
            node_id TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT '',
            duration_ms REAL,
            input_json TEXT NOT NULL DEFAULT '{}',
            output_json TEXT NOT NULL DEFAULT '{}',
            sample_json TEXT NOT NULL DEFAULT 'null',
            message TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS analytics_hourly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hour_timestamp INTEGER NOT NULL,
            node_id TEXT NOT NULL,
            class_name TEXT NOT NULL,
            detection_count INTEGER NOT NULL DEFAULT 0,
            avg_confidence REAL,
            UNIQUE(hour_timestamp, node_id, class_name)
        );

        CREATE INDEX IF NOT EXISTS idx_frames_run_frame ON frames(run_id, frame_index);
        CREATE INDEX IF NOT EXISTS idx_detections_run_frame ON detections(run_id, frame_index);
        CREATE INDEX IF NOT EXISTS idx_detections_class ON detections(class_name);
        CREATE INDEX IF NOT EXISTS idx_events_run_time ON events(run_id, timestamp_ms);
        CREATE INDEX IF NOT EXISTS idx_objects_run_track ON objects(run_id, inspection_node_id, source_node_id, track_id);
        CREATE INDEX IF NOT EXISTS idx_count_events_run_time ON count_events(run_id, timestamp_ms);
        CREATE INDEX IF NOT EXISTS idx_node_debug_run_node ON node_debug(run_id, node_id);
        CREATE INDEX IF NOT EXISTS idx_analytics_hourly_time ON analytics_hourly(hour_timestamp);
        """
    )
    conn.commit()


class DatabaseWriter:
    """Background SQLite writer for runtime data.

    The workflow loop only enqueues compact payloads. This writer owns the SQLite
    connection and commits rows in batches so disk I/O does not become part of
    frame processing latency.
    """

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        batch_size: int = 128,
        flush_interval: float = 0.5,
        max_queue: int = 10000,
        retention_days: int = 14,
        aggregate_hourly: bool = True,
    ) -> None:
        self.path = Path(path).expanduser() if path else default_database_path()
        self.batch_size = max(1, int(batch_size))
        self.flush_interval = max(0.05, float(flush_interval))
        self.retention_days = max(0, int(retention_days))
        self.aggregate_hourly = bool(aggregate_hourly)
        self.run_id = uuid.uuid4().hex
        self._queue: queue.Queue[tuple[str, dict] | None] = queue.Queue(maxsize=max(1, int(max_queue)))
        self._thread: threading.Thread | None = None
        self._dropped = 0
        self._started = False
        self._last_purge_time = 0.0

    def purge_retention(self, conn: sqlite3.Connection) -> int:
        if self.retention_days <= 0:
            return 0
        cutoff_ms = int((time.time() - (self.retention_days * 86400)) * 1000)
        deleted = 0
        try:
            with conn:
                cur = conn.execute("DELETE FROM detections WHERE timestamp_ms < ?", (cutoff_ms,))
                deleted += cur.rowcount
                cur = conn.execute("DELETE FROM frames WHERE timestamp_ms < ?", (cutoff_ms,))
                deleted += cur.rowcount
                cur = conn.execute("DELETE FROM events WHERE timestamp_ms < ?", (cutoff_ms,))
                deleted += cur.rowcount
                cur = conn.execute("DELETE FROM node_debug WHERE timestamp_ms < ?", (cutoff_ms,))
                deleted += cur.rowcount
            if deleted > 500:
                try:
                    conn.execute("VACUUM")
                except Exception:
                    pass
        except Exception:
            pass
        return deleted

    @property
    def dropped_rows(self) -> int:
        return self._dropped

    def start(self, workflow: dict, project_id: str = "") -> None:
        if self._started:
            return
        conn = connect_database(self.path)
        conn.close()
        self._started = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.enqueue("run_start", {
            "project_id": project_id,
            "workflow_json": _json_dump(workflow),
            "started_at": time.time(),
        })

    def stop(self, status: str = "stopped") -> None:
        if not self._started:
            return
        self.enqueue("run_stop", {"status": status, "stopped_at": time.time()}, block=True)
        while True:
            try:
                self._queue.put(None, timeout=1)
                break
            except queue.Full:
                if self._thread and not self._thread.is_alive():
                    break
        if self._thread:
            self._thread.join(timeout=5)
        self._started = False

    def enqueue(self, kind: str, payload: dict, *, block: bool = False) -> None:
        item = (kind, payload)
        try:
            if block:
                self._queue.put(item, timeout=2)
            else:
                self._queue.put_nowait(item)
        except queue.Full:
            self._dropped += 1

    def frame(
        self,
        *,
        frame_index: int,
        timestamp_ms: int,
        fps: float | None,
        object_count: int | None,
        width: int | None,
        height: int | None,
    ) -> None:
        self.enqueue("frame", {
            "frame_index": frame_index,
            "timestamp_ms": timestamp_ms,
            "fps": fps,
            "object_count": object_count,
            "width": width,
            "height": height,
        })

    def detections(
        self,
        *,
        frame_index: int,
        timestamp_ms: int,
        node_id: str,
        detections: list[dict],
    ) -> None:
        if detections:
            self.enqueue("detections", {
                "frame_index": frame_index,
                "timestamp_ms": timestamp_ms,
                "node_id": node_id,
                "detections": list(detections),
            })

    def event(self, *, timestamp_ms: int, title: str, detail: str, node_id: str = "") -> None:
        self.enqueue("event", {
            "timestamp_ms": timestamp_ms,
            "node_id": node_id,
            "title": title,
            "detail": detail,
        })

    def object_record(self, *, timestamp_ms: int, record: dict) -> None:
        self.enqueue("object_record", {
            "timestamp_ms": timestamp_ms,
            "record": dict(record),
        })

    def count_event(self, *, timestamp_ms: int, event: dict) -> None:
        self.enqueue("count_event", {
            "timestamp_ms": timestamp_ms,
            "event": dict(event),
        })

    def node_debug(self, payload: dict) -> None:
        self.enqueue("node_debug", dict(payload))

    def _run(self) -> None:
        conn = connect_database(self.path)
        pending: list[tuple[str, dict]] = []
        last_flush = time.monotonic()
        try:
            self.purge_retention(conn)
            self._last_purge_time = time.monotonic()
            while True:
                now_m = time.monotonic()
                if self.retention_days > 0 and (now_m - self._last_purge_time) >= 3600.0:
                    self.purge_retention(conn)
                    self._last_purge_time = now_m

                timeout = max(0.05, self.flush_interval - (time.monotonic() - last_flush))
                try:
                    item = self._queue.get(timeout=timeout)
                except queue.Empty:
                    item = None
                    should_exit = False
                else:
                    should_exit = item is None

                if item is not None:
                    pending.append(item)

                due = time.monotonic() - last_flush >= self.flush_interval
                if pending and (len(pending) >= self.batch_size or due or should_exit):
                    self._flush(conn, pending)
                    pending.clear()
                    last_flush = time.monotonic()

                if should_exit:
                    break
        finally:
            if pending:
                self._flush(conn, pending)
            conn.close()

    def _flush(self, conn: sqlite3.Connection, rows: list[tuple[str, dict]]) -> None:
        with conn:
            for kind, payload in rows:
                if kind == "run_start":
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO runs(id, project_id, workflow_json, started_at, status)
                        VALUES (?, ?, ?, ?, 'running')
                        """,
                        (
                            self.run_id,
                            str(payload.get("project_id") or ""),
                            str(payload.get("workflow_json") or "{}"),
                            float(payload.get("started_at") or time.time()),
                        ),
                    )
                elif kind == "run_stop":
                    conn.execute(
                        "UPDATE runs SET stopped_at = ?, status = ? WHERE id = ?",
                        (
                            float(payload.get("stopped_at") or time.time()),
                            str(payload.get("status") or "stopped"),
                            self.run_id,
                        ),
                    )
                elif kind == "frame":
                    conn.execute(
                        """
                        INSERT INTO frames(run_id, frame_index, timestamp_ms, fps, object_count, width, height)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            self.run_id,
                            int(payload.get("frame_index") or 0),
                            int(payload.get("timestamp_ms") or 0),
                            _float_or_none(payload.get("fps")),
                            _int_or_none(payload.get("object_count")),
                            _int_or_none(payload.get("width")),
                            _int_or_none(payload.get("height")),
                        ),
                    )
                elif kind == "detections":
                    self._insert_detections(conn, payload)
                elif kind == "event":
                    conn.execute(
                        """
                        INSERT INTO events(run_id, timestamp_ms, node_id, title, detail)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            self.run_id,
                            int(payload.get("timestamp_ms") or 0),
                            str(payload.get("node_id") or ""),
                            str(payload.get("title") or ""),
                            str(payload.get("detail") or ""),
                        ),
                    )
                elif kind == "object_record":
                    self._upsert_object(conn, payload)
                elif kind == "count_event":
                    self._insert_count_event(conn, payload)
                elif kind == "node_debug":
                    conn.execute(
                        """
                        INSERT INTO node_debug(
                            run_id, timestamp_ms, node_id, state, duration_ms,
                            input_json, output_json, sample_json, message
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            self.run_id,
                            int(float(payload.get("timestamp") or time.time()) * 1000),
                            str(payload.get("nodeId") or ""),
                            str(payload.get("state") or ""),
                            _float_or_none(payload.get("durationMs")),
                            _json_dump(payload.get("input") or {}),
                            _json_dump(payload.get("output") or {}),
                            _json_dump(payload.get("sample")),
                            str(payload.get("message") or ""),
                        ),
                    )

    def _insert_detections(self, conn: sqlite3.Connection, payload: dict) -> None:
        frame_index = int(payload.get("frame_index") or 0)
        timestamp_ms = int(payload.get("timestamp_ms") or 0)
        node_id = str(payload.get("node_id") or "")
        rows = []
        for detection in payload.get("detections") or []:
            if not isinstance(detection, dict):
                continue
            x, y, width, height = _bbox_xywh(detection)
            rows.append((
                self.run_id,
                frame_index,
                timestamp_ms,
                node_id,
                str(detection.get("sourceNodeId") or ""),
                str(detection.get("class") or "object"),
                _float_or_none(detection.get("score")),
                x,
                y,
                width,
                height,
                _int_or_none(detection.get("trackId")),
                _json_dump(detection),
            ))
        if rows:
            conn.executemany(
                """
                INSERT INTO detections(
                    run_id, frame_index, timestamp_ms, node_id, source_node_id,
                    class_name, confidence, x, y, width, height, track_id, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            if self.aggregate_hourly:
                hour_ts = (timestamp_ms // 3600000) * 3600000
                hourly_groups: dict[tuple[int, str, str], list[float]] = {}
                for r in rows:
                    c_name = r[5]
                    conf = r[6] if r[6] is not None else 0.0
                    key = (hour_ts, node_id, c_name)
                    if key not in hourly_groups:
                        hourly_groups[key] = []
                    hourly_groups[key].append(conf)
                for (h_ts, n_id, c_name), confs in hourly_groups.items():
                    cnt = len(confs)
                    avg_c = sum(confs) / cnt if cnt > 0 else 0.0
                    conn.execute(
                        """
                        INSERT INTO analytics_hourly(hour_timestamp, node_id, class_name, detection_count, avg_confidence)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(hour_timestamp, node_id, class_name) DO UPDATE SET
                            detection_count = analytics_hourly.detection_count + excluded.detection_count,
                            avg_confidence = (analytics_hourly.avg_confidence * analytics_hourly.detection_count + excluded.avg_confidence * excluded.detection_count) / (analytics_hourly.detection_count + excluded.detection_count)
                        """,
                        (h_ts, n_id, c_name, cnt, avg_c),
                    )

    def _upsert_object(self, conn: sqlite3.Connection, payload: dict) -> None:
        record = payload.get("record") or {}
        track_id = _int_or_none(record.get("trackId"))
        if track_id is None:
            return
        timestamp_ms = int(payload.get("timestamp_ms") or 0)
        source_node_id = str(
            record.get("parentSourceNodeId") or record.get("sourceNodeId") or "tracker"
        )
        inspection_node_id = str(record.get("sourceNodeId") or "track_snapshot")
        conn.execute(
            """
            INSERT INTO objects(
                run_id, inspection_node_id, source_node_id, track_id, detection_class,
                detection_confidence, classification_class,
                classification_confidence, first_seen_ms, inspected_at_ms,
                snapshot_path, inspection_status, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id, inspection_node_id, source_node_id, track_id) DO UPDATE SET
                detection_class = excluded.detection_class,
                detection_confidence = excluded.detection_confidence,
                classification_class = COALESCE(excluded.classification_class, objects.classification_class),
                classification_confidence = COALESCE(excluded.classification_confidence, objects.classification_confidence),
                inspected_at_ms = excluded.inspected_at_ms,
                snapshot_path = CASE WHEN excluded.snapshot_path != '' THEN excluded.snapshot_path ELSE objects.snapshot_path END,
                inspection_status = CASE WHEN excluded.inspection_status != '' THEN excluded.inspection_status ELSE objects.inspection_status END,
                payload_json = excluded.payload_json
            """,
            (
                self.run_id,
                inspection_node_id,
                source_node_id,
                track_id,
                str(record.get("detectionClass") or record.get("class") or "object"),
                _float_or_none(record.get("detectionScore", record.get("score"))),
                record.get("classificationClass"),
                _float_or_none(record.get("classificationConfidence")),
                timestamp_ms,
                timestamp_ms,
                str(record.get("snapshotPath") or ""),
                str(record.get("inspectionStatus") or ""),
                _json_dump(record),
            ),
        )

    def _insert_count_event(self, conn: sqlite3.Connection, payload: dict) -> None:
        event = payload.get("event") or {}
        conn.execute(
            """
            INSERT INTO count_events(
                run_id, timestamp_ms, counter_node_id, source_node_id,
                track_id, class_name, direction, cumulative_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.run_id,
                int(payload.get("timestamp_ms") or 0),
                str(event.get("counterNodeId") or event.get("sourceNodeId") or "object_counter"),
                str(event.get("parentSourceNodeId") or "tracker"),
                _int_or_none(event.get("trackId")),
                str(event.get("class") or "object"),
                str(event.get("roiEvent") or ""),
                int(event.get("objectCount") or 0),
                _json_dump(event),
            ),
        )
