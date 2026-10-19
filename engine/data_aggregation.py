"""Data Aggregator & CSV Formatter Nodes.

- Data Aggregator: Computes rolling window statistics (count, sum_duration, avg_duration, max_occupancy)
  across sliding time windows (e.g. per 15 min, 1 hour, or per shift).
- CSV Formatter: Converts events and detection records into structured tabular CSV lines
  for shift logs, archiving, or ERP ingestion.
"""
from __future__ import annotations

import csv
import io
import os
import time
from typing import Any, Dict, List, Optional, Tuple


class DataAggregator:
    """Sliding time-window statistics accumulator."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.window_seconds = max(5.0, float(config.get("windowMinutes", 60) or 60) * 60.0)
        self.metric_types = set(
            config.get("metricTypes") or ["count", "sum_duration", "avg_duration", "max_occupancy"]
        )
        # Internal record buffer: [(timestamp, event_dict)]
        self.records: List[Tuple[float, Dict[str, Any]]] = []

    def add_event(self, event: Dict[str, Any], timestamp: Optional[float] = None) -> None:
        """Add an event to the rolling window."""
        t = timestamp if timestamp is not None else time.time()
        self.records.append((t, dict(event)))

    def prune_old_records(self, now: float) -> None:
        """Remove records older than now - window_seconds."""
        cutoff = now - self.window_seconds
        self.records = [(t, ev) for t, ev in self.records if t >= cutoff]

    def compute_summary(self, now: Optional[float] = None) -> Dict[str, Any]:
        """Compute summary statistics for the active sliding window."""
        current_time = now if now is not None else time.time()
        self.prune_old_records(current_time)

        count = len(self.records)
        durations = []
        occupancies = []

        for _, ev in self.records:
            dur = ev.get("durationSeconds", ev.get("duration", ev.get("working_seconds")))
            if dur is not None:
                try:
                    durations.append(float(dur))
                except (ValueError, TypeError):
                    pass

            occ = ev.get("occupancy", ev.get("count", ev.get("item_count")))
            if occ is not None:
                try:
                    occupancies.append(int(occ))
                except (ValueError, TypeError):
                    pass

        sum_dur = sum(durations) if durations else 0.0
        avg_dur = (sum_dur / len(durations)) if durations else 0.0
        max_occ = max(occupancies) if occupancies else 0

        summary = {
            "windowSeconds": self.window_seconds,
            "windowMinutes": round(self.window_seconds / 60.0, 1),
            "totalRecords": count,
            "metrics": {
                "count": count,
                "sumDurationSeconds": round(sum_dur, 2),
                "avgDurationSeconds": round(avg_dur, 2),
                "maxOccupancy": max_occ,
            },
            "timestamp": current_time,
        }
        return summary


def aggregate_events(
    events: List[Dict[str, Any]],
    config: Dict[str, Any],
    node_state: Dict[str, Any],
    now: Optional[float] = None,
) -> Dict[str, Any]:
    """Process incoming events with the node's persistent state aggregator."""
    t_now = now if now is not None else time.time()
    aggregator: Optional[DataAggregator] = node_state.get("_aggregator")
    if aggregator is None:
        aggregator = DataAggregator(config)
        node_state["_aggregator"] = aggregator

    for ev in events:
        aggregator.add_event(ev, t_now)

    return aggregator.compute_summary(t_now)


def format_events_as_csv(
    events: List[Dict[str, Any]],
    config: Dict[str, Any],
    file_path: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Format a list of events into a delimited CSV string and optionally append to file.

    Returns:
        (csv_string, written_file_path)
    """
    col_str = str(config.get("columns") or "timestamp,zone_name,type,working_seconds,item_count")
    delimiter = str(config.get("delimiter") or ",")
    target_path = file_path or str(config.get("outputFilePath") or "").strip() or None

    columns = [c.strip() for c in col_str.split(",") if c.strip()]
    if not columns:
        columns = ["timestamp", "type", "message"]

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=columns,
        delimiter=delimiter,
        extrasaction="ignore",
        lineterminator="\n",
    )

    for ev in events:
        row = {}
        for col in columns:
            val = ev.get(col)
            if val is None:
                # Aliases
                if col == "zone_name":
                    val = ev.get("zoneName", ev.get("bay_id", ""))
                elif col == "working_seconds":
                    val = ev.get("durationSeconds", ev.get("workingSeconds", 0))
                elif col == "item_count":
                    val = ev.get("count", ev.get("itemCount", 0))
                elif col == "timestamp" and "timestamp" not in ev:
                    val = time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    val = ""
            row[col] = val
        writer.writerow(row)

    csv_text = output.getvalue()

    if target_path:
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        with open(target_path, "a", encoding="utf-8") as f:
            f.write(csv_text)

    return csv_text, target_path
