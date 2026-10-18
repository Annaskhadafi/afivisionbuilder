"""Small, deterministic project-node processors used by the workflow runner."""
from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone


def _config(node):
    return node.get("config") or {}


def _classes(value, default=()):
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().lower() for item in value if str(item).strip()}
    if value is None:
        return set(default)
    return {item.strip().lower() for item in str(value).split(",") if item.strip()}


def _frame_size(frame):
    shape = getattr(frame, "shape", ())
    if len(shape) >= 2:
        return float(shape[1]), float(shape[0])
    if isinstance(frame, dict):
        return float(frame.get("width", 1) or 1), float(frame.get("height", 1) or 1)
    return 1.0, 1.0


def _polygon(value, width, height):
    if isinstance(value, str):
        points = []
        for part in value.split(";"):
            try:
                x, y = (float(item.strip()) for item in part.split(",", 1))
                points.append((x * width, y * height))
            except (ValueError, TypeError):
                continue
        return points
    if isinstance(value, (list, tuple)):
        result = []
        for point in value:
            try:
                x, y = point
                result.append((float(x) * width, float(y) * height))
            except (ValueError, TypeError):
                continue
        return result
    return []


def _inside(point, polygon):
    if len(polygon) < 3:
        # A malformed zone must never become an all-frame zone.
        return False
    x, y = point
    result = False
    for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1]):
        if abs((x - ax) * (by - ay) - (y - ay) * (bx - ax)) < 1e-8 and min(ax, bx) <= x <= max(ax, bx) and min(ay, by) <= y <= max(ay, by):
            return True
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            result = not result
    return result


_GEOMETRY_EPSILON = 1e-12


def _orientation(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a, b, point):
    return (abs(_orientation(a, b, point)) <= _GEOMETRY_EPSILON
            and min(a[0], b[0]) - _GEOMETRY_EPSILON <= point[0] <= max(a[0], b[0]) + _GEOMETRY_EPSILON
            and min(a[1], b[1]) - _GEOMETRY_EPSILON <= point[1] <= max(a[1], b[1]) + _GEOMETRY_EPSILON)


def _segments_intersect(a, b, c, d):
    orientations = (_orientation(a, b, c), _orientation(a, b, d),
                    _orientation(c, d, a), _orientation(c, d, b))
    if ((orientations[0] > _GEOMETRY_EPSILON and orientations[1] < -_GEOMETRY_EPSILON)
            or (orientations[0] < -_GEOMETRY_EPSILON and orientations[1] > _GEOMETRY_EPSILON)) and ((orientations[2] > _GEOMETRY_EPSILON and orientations[3] < -_GEOMETRY_EPSILON) or (orientations[2] < -_GEOMETRY_EPSILON and orientations[3] > _GEOMETRY_EPSILON)):
        return True
    return (_on_segment(a, b, c) or _on_segment(a, b, d)
            or _on_segment(c, d, a) or _on_segment(c, d, b))


def _simple_polygon(points):
    """Return whether points describe a simple, non-degenerate polygon."""
    if len(points) < 3:
        return False
    for index, point in enumerate(points):
        for other in points[index + 1:]:
            if (point[0] - other[0]) ** 2 + (point[1] - other[1]) ** 2 <= _GEOMETRY_EPSILON ** 2:
                return False
    size = len(points)
    edges = [(points[index], points[(index + 1) % size]) for index in range(size)]
    for first in range(size):
        for second in range(first + 1, size):
            adjacent = second == first + 1 or (first == 0 and second == size - 1)
            if not _segments_intersect(*edges[first], *edges[second]):
                continue
            if not adjacent:
                return False
            # Adjacent edges may meet only at their shared endpoint. Duplicate
            # vertices were rejected above; this catches collinear backtracking.
            shared = points[second] if second == first + 1 else points[0]
            first_other = edges[first][0] if edges[first][1] == shared else edges[first][1]
            second_other = edges[second][0] if edges[second][1] == shared else edges[second][1]
            if _on_segment(*edges[first], second_other) or _on_segment(*edges[second], first_other):
                return False
            if not (_on_segment(*edges[first], shared) and _on_segment(*edges[second], shared)):
                return False
    return True


def _box(det):
    box = det.get("bbox") or det.get("box")
    if box and len(box) >= 4:
        return tuple(float(item) for item in box[:4])
    if all(key in det for key in ("x", "y", "width", "height")):
        return tuple(float(det[key]) for key in ("x", "y", "width", "height"))
    xyxy = det.get("xyxy")
    if xyxy and len(xyxy) >= 4:
        x1, y1, x2, y2 = (float(item) for item in xyxy[:4])
        return x1, y1, x2 - x1, y2 - y1
    return None


def _in_zone(det, polygon, width, height):
    box = _box(det)
    if box is None:
        return False
    x, y, w, h = box
    cls = str(det.get("class", "")).lower()
    if cls == "person":
        # Check feet (bottom edge), center (torso), or lower torso for sitting/webcam views
        pts = [
            (x + w / 2, y + h),
            (x + w / 2, y + h / 2),
            (x + w / 2, y + 0.75 * h),
        ]
        return any(_inside(pt, polygon) for pt in pts)
    point = (x + w / 2, y + h / 2)
    return _inside(point, polygon)


def _field_config(config, name, default):
    value = config.get(name, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def validate_project_config(node):
    """Validate the small config surface before a project node enters a run."""
    config = _config(node)
    if node.get("type") not in ("zone_activity_timer", "zone_exit_event"):
        raise ValueError("unsupported project node type")
    raw = config.get("points", "0.2,0.2;0.8,0.2;0.8,0.8;0.2,0.8")
    points = []
    for part in str(raw).split(";"):
        values = part.split(",")
        if len(values) != 2:
            raise ValueError("points must be normalized x,y pairs")
        try:
            x, y = (float(value.strip()) for value in values)
        except ValueError as exc:
            raise ValueError("points must be normalized x,y pairs") from exc
        if not all(0 <= value <= 1 and value == value and abs(value) != float("inf") for value in (x, y)):
            raise ValueError("points must be finite normalized coordinates")
        points.append((x, y))
    area = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])))
    if area < 1e-12:
        raise ValueError("points must define a non-empty polygon")
    if not _simple_polygon(points):
        raise ValueError("points must define a simple polygon without crossing or overlapping edges")
    if node.get("type") == "zone_activity_timer":
        for key in ("requiredCount", "triggerCount"):
            value = config.get(key, 1)
            try:
                valid = not isinstance(value, bool) and int(value) == value and int(value) >= 1
            except (TypeError, ValueError, OverflowError):
                valid = False
            if not valid:
                raise ValueError(f"{key} must be a positive integer")
        for key in ("confirmationSeconds", "personGraceSeconds", "requiredGraceSeconds", "maxObservationGapSeconds", "maxSessionDurationSeconds"):
            if isinstance(config.get(key), bool):
                raise ValueError(f"{key} must be a non-negative number")
            try:
                value = float(config.get(key, {"confirmationSeconds": 10, "personGraceSeconds": 3, "requiredGraceSeconds": 15, "maxObservationGapSeconds": 5, "maxSessionDurationSeconds": 0}[key]))
            except (TypeError, ValueError):
                raise ValueError(f"{key} must be a non-negative number")
            if value < 0 or value != value or abs(value) == float("inf"):
                raise ValueError(f"{key} must be a non-negative number")
            if key == "maxObservationGapSeconds" and value == 0:
                raise ValueError("maxObservationGapSeconds must be positive")
        if "countFromStart" in config and not isinstance(config["countFromStart"], bool):
            raise ValueError("countFromStart must be boolean")
        if not _classes(config.get("requiredClasses", "tire")) or not _classes(config.get("triggerClasses", "person")):
            raise ValueError("classes must not be empty")
    else:
        if any(isinstance(config.get(key), bool) for key in ("absenceGraceSeconds", "maxObservationGapSeconds")):
            raise ValueError("grace and gap must be numbers")
        try:
            grace = float(config.get("absenceGraceSeconds", 2))
            gap = float(config.get("maxObservationGapSeconds", 5))
        except (TypeError, ValueError) as exc:
            raise ValueError("grace and gap must be non-negative numbers") from exc
        if grace < 0 or grace != grace or abs(grace) == float("inf") or gap <= 0 or gap != gap or abs(gap) == float("inf"):
            raise ValueError("grace and gap must be non-negative numbers")
        if not _classes(config.get("classes", "truck,tire")):
            raise ValueError("classes must not be empty")
    return True


def _new_session(state, zone):
    state.update({
        "sessionId": None, "zoneName": zone, "state": "EMPTY",
        "startedAt": None, "confirmStartedAt": None,
        "workingSeconds": 0.0, "waitingSeconds": 0.0, "unknownSeconds": 0.0,
        "lastFrame": None, "lastRequired": None, "lastTrigger": None,
        "pendingAbsence": None, "requiredMissingSince": None, "completed": False,
        "_lastEmittedState": None,
        "sessionEnd": None,
        "durationLimitExceeded": False,
        "durationLimitExceededAt": None,
    })


def _start_session(state, now):
    state["sessionId"] = str(uuid.uuid4())
    state["startedAt"] = now
    state["completed"] = False
    state["state"] = "WAITING"


def _latch_duration_limit(state, config, observed_now):
    """Latch the first observed overlong-session boundary without closing it."""
    try:
        limit = float(config.get("maxSessionDurationSeconds", 0))
    except (TypeError, ValueError, OverflowError):
        return False
    started = state.get("startedAt")
    if limit <= 0 or started is None or state.get("durationLimitExceeded"):
        return False
    cutoff = state.get("sessionEnd") if state.get("completed") and state.get("sessionEnd") is not None else observed_now
    if cutoff - started < limit:
        return False
    state["durationLimitExceeded"] = True
    state["durationLimitExceededAt"] = started + limit
    return True


def _timer_snapshot(node, state, now):
    durations = {"workingSeconds": round(state["workingSeconds"], 6),
                 "waitingSeconds": round(state["waitingSeconds"], 6),
                 "unknownSeconds": round(state["unknownSeconds"], 6)}
    counts = dict(state.get("counts", {}))
    return {"kind": "zone_activity", "sourceNodeId": str(node.get("id") or ""),
            "sessionId": state["sessionId"], "zoneName": state["zoneName"],
            "state": state["state"], "counts": counts, "durations": durations,
            "requiredCount": counts.get("required", 0), "triggerCount": counts.get("trigger", 0),
            "durationLimitExceeded": bool(state.get("durationLimitExceeded")),
            "durationLimitExceededAt": state.get("durationLimitExceededAt"),
            **durations,
            "monotonicTime": now}


def _append_segment(state, start, end, label):
    if end <= start:
        return
    segments = state["segments"]
    if segments and segments[-1][2] == label and segments[-1][1] == start:
        segments[-1][1] = end
    else:
        segments.append([start, end, label])


def _relabel_segments(state, start, label):
    segments = state["segments"]
    state["segments"] = []
    for a, b, old_label in segments:
        if b <= start:
            _append_segment(state, a, b, old_label)
        else:
            _append_segment(state, a, min(b, start), old_label)
            _append_segment(state, max(a, start), b, label)


def _process_timer(node, frame, detections, runtime, now):
    config = _config(node)
    node_id = str(node.get("id") or "zone_activity_timer")
    zone = str(config.get("zoneName") or "")
    state = runtime.get(node_id)
    if not isinstance(state, dict) or state.get("zoneName") != zone:
        state = runtime[node_id] = {}
        _new_session(state, zone)
        state["segments"] = []
    previous = state.get("lastFrame")
    previous_required = state.get("lastRequired")
    if previous is not None and now < previous:
        return []
    width, height = _frame_size(frame)
    polygon = _polygon(config.get("points", "0.2,0.2;0.8,0.2;0.8,0.8;0.2,0.8"), width, height)
    inside = [d for d in detections if d.get("kind", "detection") in ("detection", "segmentation")
              and _in_zone(d, polygon, width, height)]
    required = sum(str(d.get("class", "")).lower() in _classes(config.get("requiredClasses", "tire")) for d in inside)
    trigger = sum(str(d.get("class", "")).lower() in _classes(config.get("triggerClasses", "person")) for d in inside)
    req_ok = required >= int(config.get("requiredCount", 1))
    trigger_ok = trigger >= int(config.get("triggerCount", 1))
    active = state.get("sessionId") is not None and not state.get("completed")
    gap = previous is not None and now - previous > float(config.get("maxObservationGapSeconds", 5))
    closure = []
    # A return after required-object grace has elapsed starts a fresh session,
    # even if no frame landed at the exact expiry time.
    if active and not gap and req_ok and state.get("requiredMissingSince") is not None:
        cutoff = state.get("lastRequired")
        if cutoff is not None and now - cutoff > float(config.get("requiredGraceSeconds", 15)):
            state["segments"] = [[a, min(b, cutoff), label] for a, b, label in state["segments"] if a < cutoff]
            state.update(state="COMPLETED", completed=True, sessionEnd=cutoff)
            totals = {"WORKING": 0.0, "WAITING": 0.0, "UNKNOWN": 0.0}
            for a, b, label in state["segments"]:
                totals[label] += b - a
            state.update(workingSeconds=totals["WORKING"], waitingSeconds=totals["WAITING"], unknownSeconds=totals["UNKNOWN"])
            limit_latched = _latch_duration_limit(state, config, now)
            closure = [{**_timer_snapshot(node, state, now), "endedAtMonotonic": cutoff,
                        "kind": "zone_activity_event", "eventId": str(uuid.uuid4()),
                        "observedAt": datetime.now(timezone.utc).isoformat()}]
            if limit_latched:
                closure.insert(0, {**_timer_snapshot(node, state, now),
                                   "kind": "zone_activity_event", "reason": "max_session_duration_exceeded",
                                   "eventId": str(uuid.uuid4()),
                                   "observedAt": datetime.now(timezone.utc).isoformat()})
            active = False
    if active and previous is not None:
        label = "UNKNOWN" if gap else ("WORKING" if state["state"] == "WORKING" else "WAITING")
        _append_segment(state, previous, now, label)
    if not active and req_ok:
        _new_session(state, zone)
        state["segments"] = []
        _start_session(state, now)
        active = True
        gap = False

    if active and gap:
        state.update(state="UNKNOWN", confirmStartedAt=None, pendingAbsence=None,
                     lastRequired=None, lastTrigger=None, requiredMissingSince=None)
    elif active:
        req_grace = float(config.get("requiredGraceSeconds", 15))
        person_grace = float(config.get("personGraceSeconds", 3))
        # Evaluate return eligibility before overwriting the last observations.
        req_return_valid = state.get("lastRequired") is not None and now - state["lastRequired"] <= req_grace
        person_return_valid = state.get("lastTrigger") is not None and now - state["lastTrigger"] <= person_grace
        resume = state.get("pendingAbsence") is not None and req_return_valid and person_return_valid
        if req_ok:
            state["lastRequired"] = now
            state["requiredMissingSince"] = None
        elif state.get("requiredMissingSince") is None:
            state["requiredMissingSince"] = now
        if trigger_ok:
            state["lastTrigger"] = now

        last_required = state.get("lastRequired")
        missing_required_expired = not req_ok and (
            now - (last_required if last_required is not None else state["requiredMissingSince"]) >= req_grace
        )
        if missing_required_expired:
            cutoff = last_required if last_required is not None else now
            state["segments"] = [[a, min(b, cutoff), label] for a, b, label in state["segments"] if a < cutoff]
            state.update(state="COMPLETED", completed=True, sessionEnd=cutoff,
                         pendingAbsence=None, confirmStartedAt=None)
        elif req_ok and trigger_ok:
            if resume:
                _relabel_segments(state, state["pendingAbsence"], "WORKING")
                state.update(state="WORKING", pendingAbsence=None, confirmStartedAt=None)
            elif state["state"] != "WORKING":
                state["pendingAbsence"] = None
                if state.get("confirmStartedAt") is None:
                    state["confirmStartedAt"] = now
                if now - state["confirmStartedAt"] >= float(config.get("confirmationSeconds", 10)):
                    if config.get("countFromStart", True):
                        _relabel_segments(state, state["confirmStartedAt"], "WORKING")
                    state["state"] = "WORKING"
                else:
                    state["state"] = "CONFIRMING"
        else:
            state["confirmStartedAt"] = None
            if state["state"] == "WORKING":
                cutoffs = []
                if not req_ok and last_required is not None:
                    cutoffs.append(last_required)
                if not trigger_ok and state.get("lastTrigger") is not None:
                    cutoffs.append(state["lastTrigger"])
                cutoff = min(cutoffs) if cutoffs else now
                _relabel_segments(state, cutoff, "WAITING")
                state["pendingAbsence"] = cutoff
            if state.get("pendingAbsence") is not None:
                req_expired = not req_ok and not req_return_valid
                person_expired = not trigger_ok and not person_return_valid
                if req_expired or person_expired:
                    state["pendingAbsence"] = None
                state["state"] = "PAUSED"
            else:
                state["state"] = "WAITING"

    state["counts"] = {"required": required, "trigger": trigger}
    state["lastFrame"] = now
    totals = {"WORKING": 0.0, "WAITING": 0.0, "UNKNOWN": 0.0}
    for a, b, label in state["segments"]:
        totals[label] += b - a
    state.update(workingSeconds=totals["WORKING"], waitingSeconds=totals["WAITING"], unknownSeconds=totals["UNKNOWN"])
    limit_event = None
    limit_now = now
    # Do not warn from time that may later be discarded when required-object
    # absence grace backdates completion. A valid return within grace resumes
    # normal age evaluation against the current observation.
    if not req_ok and not state.get("completed") and previous_required is not None:
        limit_now = min(limit_now, previous_required)
    if _latch_duration_limit(state, config, limit_now):
        limit_event = {**_timer_snapshot(node, state, now),
                       "kind": "zone_activity_event",
                       "reason": "max_session_duration_exceeded",
                       "eventId": str(uuid.uuid4()),
                       "observedAt": datetime.now(timezone.utc).isoformat()}
    snapshot = _timer_snapshot(node, state, now)
    snapshot["startedAtMonotonic"] = state.get("startedAt")
    snapshot["endedAtMonotonic"] = state.get("sessionEnd")
    state["snapshot"] = snapshot
    events = [snapshot]
    if limit_event is not None:
        events.append(limit_event)
    if state.get("sessionId") is not None and state.get("_lastEmittedState") != state["state"]:
        event = dict(snapshot)
        event.update(kind="zone_activity_event", eventId=str(uuid.uuid4()), observedAt=datetime.now(timezone.utc).isoformat())
        events.append(event)
        state["_lastEmittedState"] = state["state"]
    return closure + events


def _process_exit(node, frame, detections, runtime, now):
    config = _config(node)
    node_id = str(node.get("id") or "zone_exit_event")
    state = runtime.setdefault(node_id, {"tracks": {}, "lastFrame": None})
    width, height = _frame_size(frame)
    polygon = _polygon(config.get("points", "0.2,0.2;0.8,0.2;0.8,0.8;0.2,0.8"), width, height)
    classes = _classes(config.get("classes", "truck,tire"))
    gap = _field_config(config, "maxObservationGapSeconds", 5)
    if state.get("lastFrame") is not None and now - state["lastFrame"] > gap:
        state["tracks"].clear()
    if state.get("lastFrame") is not None and now < state["lastFrame"]:
        return []
    seen = set()
    events = []
    grace = _field_config(config, "absenceGraceSeconds", 2)
    for det in detections:
        cls = str(det.get("class", "")).lower()
        track = det.get("trackId")
        if det.get("kind", "detection") not in ("detection", "segmentation") or cls not in classes or track is None or _box(det) is None:
            continue
        key = str(track)
        seen.add(key)
        inside = _in_zone(det, polygon, width, height)
        item = state["tracks"].setdefault(key, {"inside": inside, "lastSeen": now, "outsideSince": None, "emitted": False})
        if inside:
            item.update(inside=True, lastSeen=now, outsideSince=None, emitted=False)
        else:
            if item.get("inside") and item.get("outsideSince") is None:
                item["outsideSince"] = now
            item["lastSeen"] = now
            if item.get("inside") and not item.get("emitted") and item.get("outsideSince") is not None and now - item["outsideSince"] >= grace:
                events.append({"kind": "zone_exit", "sourceNodeId": node_id, "trackId": track,
                               "class": cls, "score": det.get("score"), "bbox": det.get("bbox"),
                               "zoneName": config.get("zoneName", ""), "direction": "OUT", "monotonicTime": now,
                               "eventId": str(uuid.uuid4()), "observedAt": datetime.now(timezone.utc).isoformat()})
                item["emitted"] = True
    for key, item in state["tracks"].items():
        if key not in seen:
            item["outsideSince"] = None
    state["tracks"] = {key: item for key, item in state["tracks"].items() if now - item.get("lastSeen", now) <= max(grace, gap)}
    state["lastFrame"] = now
    state["snapshot"] = {"kind": "zone_exit_state", "sourceNodeId": node_id,
                         "zoneName": config.get("zoneName", ""), "state": "MONITORING",
                         "trackedCount": len(state["tracks"]), "monotonicTime": now}
    return events


def process_project_node(node, frame, detections, runtime, now):
    """Process one project node, keeping all mutable state under ``runtime[nodeId]``."""
    node_type = node.get("type")
    if node_type not in ("zone_activity_timer", "zone_exit_event"):
        return []
    signature = json.dumps(node.get("config", {}), sort_keys=True)
    node_id = str(node.get("id") or node_type)
    previous = runtime.get(node_id, {})
    closure = []
    if previous.get("_configSignature") not in (None, signature):
        if previous.get("sessionId") and not previous.get("completed"):
            closure = [{**previous.get("snapshot", {}), "kind": "zone_activity_event",
                        "state": "COMPLETED", "reason": "configuration_changed",
                        "eventId": str(uuid.uuid4()), "observedAt": datetime.now(timezone.utc).isoformat()}]
        runtime.pop(node_id, None)
    if node_type == "zone_activity_timer":
        result = _process_timer(node, frame, detections or [], runtime, float(now))
    else:
        result = _process_exit(node, frame, detections or [], runtime, float(now))
    runtime[node_id]["_configSignature"] = signature
    return closure + result


def process_project_nodes(workflow, frame, detections, runtime, now):
    """Process supported project nodes in workflow order."""
    runtime = runtime if runtime is not None else {}
    return [event for node in workflow.get("nodes", []) if node.get("enabled", True)
            for event in process_project_node(node, frame, detections, runtime, now)]


if __name__ == "__main__":
    node = {"id": "timer", "type": "zone_activity_timer", "config": {"points": "0,0;1,0;1,1;0,1"}}
    runtime = {}
    detections = [{"class": "tire", "bbox": [10, 10, 10, 10]}, {"class": "person", "bbox": [10, 10, 10, 20]}]
    process_project_nodes({"nodes": [node]}, {"width": 100, "height": 100}, detections, runtime, 0)
    process_project_nodes({"nodes": [node]}, {"width": 100, "height": 100}, detections, runtime, 5)
    assert runtime["timer"]["snapshot"]["state"] == "CONFIRMING"
    print("project_nodes smoke check passed")

