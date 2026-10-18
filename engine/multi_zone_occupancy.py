from __future__ import annotations

import copy
import json
import math
import time
import uuid
from datetime import datetime, timezone
from typing import Any


def _inside_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Ray casting algorithm to test whether a 2D point is inside a polygon."""
    x, y = point
    inside = False
    size = len(polygon)
    if size < 3:
        return False
    for i in range(size):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % size]
        if (y1 > y) != (y2 > y):
            x_intersect = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1
            if x < x_intersect:
                inside = not inside
    return inside


def _parse_polygon_points(raw: Any, width: float, height: float) -> list[tuple[float, float]]:
    """Convert normalized (0.0 - 1.0) or pixel string points to pixel coordinates."""
    if isinstance(raw, list):
        pts = []
        for item in raw:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                px, py = float(item[0]), float(item[1])
                if 0.0 <= px <= 1.0 and 0.0 <= py <= 1.0:
                    pts.append((px * width, py * height))
                else:
                    pts.append((px, py))
        return pts

    text = str(raw or "").strip()
    if not text:
        return []

    pts = []
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        try:
            x_str, y_str = part.split(",", 1)
            px, py = float(x_str.strip()), float(y_str.strip())
            if 0.0 <= px <= 1.0 and 0.0 <= py <= 1.0:
                pts.append((px * width, py * height))
            else:
                pts.append((px, py))
        except (ValueError, TypeError):
            continue
    return pts


def _extract_box(det: dict) -> tuple[float, float, float, float] | None:
    """Extract (x, y, w, h) bounding box from a detection dictionary."""
    for key in ("bbox", "box"):
        b = det.get(key)
        if isinstance(b, (list, tuple)) and len(b) >= 4:
            try:
                x, y, w, h = float(b[0]), float(b[1]), float(b[2]), float(b[3])
                if w > 0 and h > 0:
                    return x, y, w, h
            except (TypeError, ValueError):
                pass
    xyxy = det.get("xyxy")
    if isinstance(xyxy, (list, tuple)) and len(xyxy) >= 4:
        try:
            x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
            if x2 > x1 and y2 > y1:
                return x1, y1, x2 - x1, y2 - y1
        except (TypeError, ValueError):
            pass
    if "x" in det and "y" in det:
        try:
            x = float(det["x"])
            y = float(det["y"])
            w = float(det.get("width", det.get("w", 0)))
            h = float(det.get("height", det.get("h", 0)))
            if w > 0 and h > 0:
                return x, y, w, h
        except (TypeError, ValueError):
            pass
    return None


def is_detection_in_zone(det: dict, polygon: list[tuple[float, float]]) -> bool:
    """Check if detection is inside polygon; tests feet, center, and torso for person, center for others."""
    box = _extract_box(det)
    if not box or len(polygon) < 3:
        return False
    x, y, w, h = box
    cls = str(det.get("class", "")).lower()

    if cls in ("person", "pedestrian", "man", "woman"):
        test_points = [
            (x + w / 2.0, y + h),        # Bottom / feet
            (x + w / 2.0, y + h / 2.0),  # Center / torso
            (x + w / 2.0, y + 0.75 * h), # Lower torso / waist
            (x + 0.25 * w, y + 0.75 * h),# Left waist
            (x + 0.75 * w, y + 0.75 * h),# Right waist
            (x + w / 2.0, y + 0.35 * h), # Upper torso / chest
            (x + 0.25 * w, y + h),       # Left foot
            (x + 0.75 * w, y + h),       # Right foot
        ]
        return any(_inside_polygon(pt, polygon) for pt in test_points)

    # Vehicles or general objects: test center and bottom-center
    test_points = [
        (x + w / 2.0, y + h / 2.0),
        (x + w / 2.0, y + h),
    ]
    return any(_inside_polygon(pt, polygon) for pt in test_points)


def parse_zones_config(config: dict) -> list[dict]:
    """Parse zones list from node configuration (supports JSON string or array)."""
    raw = config.get("zones")
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                raw = parsed
        except Exception:
            raw = None

    if isinstance(raw, list) and len(raw) > 0:
        result = []
        for idx, item in enumerate(raw):
            if not isinstance(item, dict):
                continue
            zid = str(item.get("id") or f"zone_{idx + 1}")
            name = str(item.get("name") or f"Zona {idx + 1}")
            capacity = max(1, int(item.get("capacity", 4) or 4))
            pts = str(item.get("points") or "").strip()
            result.append({
                "id": zid,
                "name": name,
                "capacity": capacity,
                "points": pts
            })
        if result:
            return result

    # Default fallback: 2 sample zones
    return [
        {
            "id": "zone_1",
            "name": "Zona A",
            "capacity": 4,
            "points": "0.15,0.20; 0.45,0.20; 0.45,0.80; 0.15,0.80"
        },
        {
            "id": "zone_2",
            "name": "Zona B",
            "capacity": 2,
            "points": "0.55,0.20; 0.85,0.20; 0.85,0.80; 0.55,0.80"
        }
    ]


def format_duration_human(seconds: float) -> str:
    """Format elapsed seconds into 0m 00s or 0h 00m."""
    s = max(0.0, float(seconds))
    if s < 60:
        return f"{int(s)}s"
    m = int(s // 60)
    sec = int(s % 60)
    if m < 60:
        return f"{m}m {sec:02d}s"
    h = int(m // 60)
    rem_m = int(m % 60)
    return f"{h}h {rem_m:02d}m"


def process_multi_zone_occupancy(
    node: dict,
    frame: Any,
    detections: list[dict],
    runtime: dict,
    now: float
) -> list[dict]:
    """
    Core stateful processor for Multi-Zone Occupancy & Activity Tracker.
    Calculates occupancy per zone, updates timers, and emits business events.
    """
    config = node.get("config", {})
    node_id = str(node.get("id") or "multi_zone_occupancy")

    # Frame dimensions
    width = 1280.0
    height = 720.0
    if hasattr(frame, "shape") and len(frame.shape) >= 2:
        height = float(frame.shape[0])
        width = float(frame.shape[1])
    elif isinstance(frame, dict):
        width = float(frame.get("width", 1280))
        height = float(frame.get("height", 720))

    # Configuration options
    target_classes_raw = str(config.get("targetClasses", "person")).lower()
    target_classes = [c.strip() for c in target_classes_raw.split(",") if c.strip()]
    if not target_classes:
        target_classes = ["person"]

    confirmation_sec = max(0.0, float(config.get("confirmationSeconds", 3.0)))
    grace_sec = max(0.0, float(config.get("graceSeconds", 10.0)))
    max_dwell_sec = max(0.0, float(config.get("maxDwellMinutes", 0.0)) * 60.0)

    # Initialize runtime state container
    state = runtime.setdefault(node_id, {})
    zones_state = state.setdefault("zones", {})

    zones_def = parse_zones_config(config)
    emitted_events: list[dict] = []

    # Filter detections matching target classes
    matching_dets = [
        d for d in detections
        if str(d.get("class", "")).lower() in target_classes
    ]

    total_objects_in_any_zone = 0
    total_occupied_zones = 0
    total_capacity_all = sum(z["capacity"] for z in zones_def)

    # Process each zone independently
    zones_summary = []

    for zdef in zones_def:
        zid = zdef["id"]
        zname = zdef["name"]
        capacity = zdef["capacity"]
        raw_pts = zdef["points"]

        poly = _parse_polygon_points(raw_pts, width, height)

        # Get or init persistent state for this zone
        zstate = zones_state.setdefault(zid, {
            "zoneId": zid,
            "zoneName": zname,
            "capacity": capacity,
            "status": "VACANT",
            "currentCount": 0,
            "sessionId": None,
            "sessionStart": None,
            "confirmStart": None,
            "occupiedSeconds": 0.0,
            "lastSeen": None,
            "missingSince": None,
            "overstayNotified": False,
            "historyTurnovers": 0,
        })
        # Keep name and capacity up to date
        zstate["zoneName"] = zname
        zstate["capacity"] = capacity

        # Find detections inside this zone
        in_zone_dets = [d for d in matching_dets if is_detection_in_zone(d, poly)]
        curr_count = len(in_zone_dets)
        zstate["currentCount"] = curr_count

        prev_status = zstate["status"]

        if curr_count > 0:
            total_objects_in_any_zone += curr_count
            zstate["lastSeen"] = now
            zstate["missingSince"] = None

            if prev_status == "VACANT":
                # Start confirmation phase
                if zstate.get("confirmStart") is None:
                    zstate["confirmStart"] = now

                if now - zstate["confirmStart"] >= confirmation_sec:
                    # Transition to OCCUPIED
                    zstate["status"] = "OCCUPIED" if curr_count <= capacity else "OVER_CAPACITY"
                    zstate["sessionId"] = str(uuid.uuid4())
                    zstate["sessionStart"] = now
                    zstate["occupiedSeconds"] = 0.0
                    zstate["confirmStart"] = None
                    zstate["overstayNotified"] = False

                    # Emit zone_occupied event
                    evt = {
                        "kind": "zone_occupied",
                        "sourceNodeId": node_id,
                        "zoneId": zid,
                        "zoneName": zname,
                        "sessionId": zstate["sessionId"],
                        "currentCount": curr_count,
                        "capacity": capacity,
                        "status": zstate["status"],
                        "occupiedAt": datetime.now(timezone.utc).isoformat(),
                        "monotonicTime": now,
                    }
                    emitted_events.append(evt)
                else:
                    zstate["status"] = "CONFIRMING"

            elif prev_status in ("CONFIRMING", "OCCUPIED", "OVER_CAPACITY", "OVERSTAY", "PENDING_VACANT"):
                if prev_status == "CONFIRMING":
                    if now - zstate["confirmStart"] >= confirmation_sec:
                        zstate["status"] = "OCCUPIED" if curr_count <= capacity else "OVER_CAPACITY"
                        zstate["sessionId"] = str(uuid.uuid4())
                        zstate["sessionStart"] = now
                        zstate["occupiedSeconds"] = 0.0
                        zstate["confirmStart"] = None
                        zstate["overstayNotified"] = False

                        evt = {
                            "kind": "zone_occupied",
                            "sourceNodeId": node_id,
                            "zoneId": zid,
                            "zoneName": zname,
                            "sessionId": zstate["sessionId"],
                            "currentCount": curr_count,
                            "capacity": capacity,
                            "status": zstate["status"],
                            "occupiedAt": datetime.now(timezone.utc).isoformat(),
                            "monotonicTime": now,
                        }
                        emitted_events.append(evt)
                else:
                    # Restore status if recovering from PENDING_VACANT
                    if prev_status == "PENDING_VACANT":
                        zstate["status"] = "OCCUPIED" if curr_count <= capacity else "OVER_CAPACITY"

                    # Accumulate occupied timer
                    if zstate.get("sessionStart") is not None:
                        zstate["occupiedSeconds"] = max(0.0, now - zstate["sessionStart"])

                    # Check overcapacity status
                    if curr_count > capacity:
                        zstate["status"] = "OVER_CAPACITY"
                    elif zstate["status"] == "OVER_CAPACITY":
                        zstate["status"] = "OCCUPIED"

                    # Check overstay limit
                    if max_dwell_sec > 0 and zstate["occupiedSeconds"] >= max_dwell_sec:
                        zstate["status"] = "OVERSTAY"
                        if not zstate.get("overstayNotified"):
                            zstate["overstayNotified"] = True
                            emitted_events.append({
                                "kind": "zone_overstay",
                                "sourceNodeId": node_id,
                                "zoneId": zid,
                                "zoneName": zname,
                                "sessionId": zstate["sessionId"],
                                "currentCount": curr_count,
                                "capacity": capacity,
                                "durationSeconds": round(zstate["occupiedSeconds"], 2),
                                "durationFormatted": format_duration_human(zstate["occupiedSeconds"]),
                                "maxDwellMinutes": config.get("maxDwellMinutes", 0),
                                "observedAt": datetime.now(timezone.utc).isoformat(),
                                "monotonicTime": now,
                            })

        else:
            # 0 objects in zone
            if prev_status in ("OCCUPIED", "OVER_CAPACITY", "OVERSTAY", "PENDING_VACANT"):
                if zstate.get("missingSince") is None:
                    zstate["missingSince"] = now
                    zstate["status"] = "PENDING_VACANT"

                # Check if grace period has expired
                if now - zstate["missingSince"] >= grace_sec:
                    # Selesai Sesi (Vacated)
                    final_duration = zstate.get("occupiedSeconds", 0.0)
                    turnovers = zstate.get("historyTurnovers", 0) + 1
                    zstate["historyTurnovers"] = turnovers

                    vacated_event = {
                        "kind": "zone_vacated",
                        "sourceNodeId": node_id,
                        "zoneId": zid,
                        "zoneName": zname,
                        "sessionId": zstate.get("sessionId"),
                        "capacity": capacity,
                        "durationSeconds": round(final_duration, 2),
                        "durationFormatted": format_duration_human(final_duration),
                        "turnoverIndex": turnovers,
                        "vacatedAt": datetime.now(timezone.utc).isoformat(),
                        "monotonicTime": now,
                    }
                    emitted_events.append(vacated_event)

                    # Reset to VACANT
                    zstate["status"] = "VACANT"
                    zstate["sessionId"] = None
                    zstate["sessionStart"] = None
                    zstate["occupiedSeconds"] = 0.0
                    zstate["missingSince"] = None
                    zstate["confirmStart"] = None
                    zstate["overstayNotified"] = False
            elif prev_status == "CONFIRMING":
                # Brief tolerance during confirming to avoid resetting on a single dropped frame
                if zstate.get("missingSince") is None:
                    zstate["missingSince"] = now
                elif now - zstate["missingSince"] >= 1.0:
                    zstate["status"] = "VACANT"
                    zstate["confirmStart"] = None
                    zstate["missingSince"] = None
            else:
                zstate["status"] = "VACANT"
                zstate["confirmStart"] = None
                zstate["occupiedSeconds"] = 0.0

        if zstate["status"] in ("OCCUPIED", "OVER_CAPACITY", "OVERSTAY", "PENDING_VACANT"):
            total_occupied_zones += 1

        zones_summary.append({
            "id": zid,
            "name": zname,
            "capacity": capacity,
            "status": zstate["status"],
            "currentCount": zstate["currentCount"],
            "occupiedSeconds": round(zstate["occupiedSeconds"], 1),
            "occupiedFormatted": format_duration_human(zstate["occupiedSeconds"]),
            "points": raw_pts,
        })

    # Prepare root snapshot for runner status & overlay rendering
    occupancy_rate = (total_occupied_zones / len(zones_def) * 100.0) if zones_def else 0.0
    snapshot = {
        "kind": "multi_zone_occupancy",
        "sourceNodeId": node_id,
        "totalZones": len(zones_def),
        "occupiedZones": total_occupied_zones,
        "vacantZones": len(zones_def) - total_occupied_zones,
        "occupancyRate": round(occupancy_rate, 1),
        "totalObjects": total_objects_in_any_zone,
        "totalCapacity": total_capacity_all,
        "zones": zones_summary,
        "monotonicTime": now,
    }
    state["snapshot"] = snapshot

    return emitted_events
