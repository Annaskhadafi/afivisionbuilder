from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine"))
from project_nodes import process_project_nodes, validate_project_config


FRAME = {"width": 100, "height": 100}


def _timer(**config):
    base = {"points": "0,0;1,0;1,1;0,1", "confirmationSeconds": 10,
            "countFromStart": True, "personGraceSeconds": 3,
            "requiredGraceSeconds": 15, "maxObservationGapSeconds": 5}
    base.update(config)
    return {"id": "timer", "type": "zone_activity_timer", "config": base}


def _detection(cls, box=(20, 20, 10, 20), track=None):
    item = {"class": cls, "score": .9, "bbox": list(box)}
    if track is not None:
        item["trackId"] = track
    return item


def test_timer_backdate_and_nonbackdate():
    for count_from_start, expected in ((True, 10), (False, 0)):
        runtime = {}
        node = _timer(countFromStart=count_from_start)
        process_project_nodes({"nodes": [node]}, FRAME, [_detection("tire"), _detection("person")], runtime, 0)
        process_project_nodes({"nodes": [node]}, FRAME, [_detection("tire"), _detection("person")], runtime, 5)
        events = process_project_nodes({"nodes": [node]}, FRAME, [_detection("tire"), _detection("person")], runtime, 10)
        assert events[-1]["state"] == "WORKING"
        assert events[-1]["workingSeconds"] == expected
        assert events[-1]["waitingSeconds"] == 10 - expected
        assert events[-1]["unknownSeconds"] == 0


def test_timer_grace_gap_completion_and_new_session():
    runtime = {}
    node = _timer()
    both = [_detection("tire"), _detection("person")]
    process_project_nodes({"nodes": [node]}, FRAME, both, runtime, 0)
    process_project_nodes({"nodes": [node]}, FRAME, both, runtime, 5)
    process_project_nodes({"nodes": [node]}, FRAME, both, runtime, 10)
    process_project_nodes({"nodes": [node]}, FRAME, [_detection("tire")], runtime, 11)
    assert runtime["timer"]["state"] == "PAUSED"
    process_project_nodes({"nodes": [node]}, FRAME, [_detection("tire")], runtime, 15)
    assert runtime["timer"]["snapshot"]["workingSeconds"] == 10
    for timestamp in (20, 25, 30, 35):
        process_project_nodes({"nodes": [node]}, FRAME, [], runtime, timestamp)
    assert runtime["timer"]["state"] == "COMPLETED"
    old = runtime["timer"]["sessionId"]
    process_project_nodes({"nodes": [node]}, FRAME, both, runtime, 31)
    assert runtime["timer"]["sessionId"] == old
    process_project_nodes({"nodes": [node]}, FRAME, both, runtime, 36)
    assert runtime["timer"]["sessionId"] != old
    process_project_nodes({"nodes": [node]}, FRAME, both, runtime, 40)
    assert runtime["timer"]["state"] == "CONFIRMING"
    assert runtime["timer"]["unknownSeconds"] == 0


def test_timer_multi_person_and_id_change_do_not_matter():
    runtime = {}
    node = _timer()
    both = [_detection("tire"), _detection("person"), _detection("person", (40, 20, 10, 20))]
    process_project_nodes({"nodes": [node]}, FRAME, both, runtime, 0)
    process_project_nodes({"nodes": [node]}, FRAME, both, runtime, 5)
    process_project_nodes({"nodes": [node]}, FRAME, [_detection("tire"), _detection("person")], runtime, 10)
    assert runtime["timer"]["state"] == "WORKING"


def test_exit_disappearance_first_outside_rearm_and_gap():
    node = {"id": "exit", "type": "zone_exit_event", "config": {"points": "0,0;1,0;1,1;0,1", "absenceGraceSeconds": 2}}
    workflow = {"nodes": [node]}
    runtime = {}
    process_project_nodes(workflow, FRAME, [_detection("truck", track="a")], runtime, 0)
    assert process_project_nodes(workflow, FRAME, [], runtime, 5) == []
    assert process_project_nodes(workflow, FRAME, [_detection("truck", (150, 20, 10, 20), "a")], runtime, 6) == []
    event = process_project_nodes(workflow, FRAME, [_detection("truck", (150, 20, 10, 20), "a")], runtime, 8)
    assert event and event[0]["direction"] == "OUT"
    process_project_nodes(workflow, FRAME, [_detection("truck", track="a")], runtime, 9)
    assert process_project_nodes(workflow, FRAME, [_detection("truck", (150, 20, 10, 20), "a")], runtime, 11) == []
    assert process_project_nodes(workflow, FRAME, [_detection("truck", (150, 20, 10, 20), "a")], runtime, 13)
    assert process_project_nodes(workflow, FRAME, [_detection("truck", track="a")], runtime, 20) == []


def test_validate_project_config():
    assert validate_project_config(_timer()) is True
    invalid = (
        "0,0;1,1;0,1;1,0",       # crossing edges
        "0,0;1,0;1,1;1,1;0,1",   # repeated vertex
        "0,0;1,0;1,1;0,1;0,0",   # repeated closing vertex
        "0,0;1,0;0.5,0;1,1;0,1", # zero-length/backtracking edge
        "0,0;1,0;1,1;0,1;0.5,0", # non-adjacent touch
        "0,0;1,0;1,1;0.75,0;0.25,0;0,1", # non-adjacent overlap
    )
    for points in invalid:
        try:
            validate_project_config(_timer(points=points))
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid polygon accepted: {points}")

    # Concavity alone is valid and must remain usable for workshop zones.
    assert validate_project_config(_timer(points="0,0;1,0;1,1;0.5,0.5;0,1")) is True


def test_malformed_runtime_zone_fails_closed():
    node = _timer(points="0,0;1,0")
    runtime = {}
    objects = [_detection("tire"), _detection("person")]
    process_project_nodes({"nodes": [node]}, FRAME, objects, runtime, 0)
    assert runtime["timer"]["snapshot"]["state"] == "EMPTY"
    assert runtime["timer"]["snapshot"]["sessionId"] is None


def test_exact_durations_grace_gap_and_completion():
    node = _timer(confirmationSeconds=0, requiredGraceSeconds=3)
    workflow = {"nodes": [node]}
    both = [_detection("tire"), _detection("person", track="p1")]
    runtime = {}
    def step(t, objects):
        process_project_nodes(workflow, FRAME, objects, runtime, t)
        return runtime["timer"]["snapshot"]
    step(0, both)
    assert step(5, both)["workingSeconds"] == 5
    missing = step(6, [_detection("tire")])
    assert (missing["workingSeconds"], missing["waitingSeconds"]) == (5, 1)
    restored = step(7, [_detection("tire"), _detection("person", track="p99")])
    assert (restored["workingSeconds"], restored["waitingSeconds"]) == (7, 0)
    gap = step(20, both)
    assert (gap["workingSeconds"], gap["waitingSeconds"], gap["unknownSeconds"]) == (7, 0, 13)
    assert gap["state"] == "UNKNOWN"
    step(21, both)
    step(22, both)
    step(23, [])
    step(24, [])
    done = step(25, [])
    assert done["state"] == "COMPLETED"
    assert done["endedAtMonotonic"] == 22
    assert (done["workingSeconds"], done["waitingSeconds"], done["unknownSeconds"]) == (8, 1, 13)
    assert sum(done["durations"].values()) == 22
    assert step(26, [])["durations"] == done["durations"]
    new = step(27, both)
    assert new["sessionId"] != done["sessionId"]
    assert sum(new["durations"].values()) == 0


def test_empty_failed_confirmation_and_config_change():
    runtime = {}
    node = _timer()
    workflow = {"nodes": [node]}
    for t in (0, 20, 50):
        process_project_nodes(workflow, FRAME, [_detection("person")], runtime, t)
        snapshot = runtime["timer"]["snapshot"]
        assert snapshot["state"] == "EMPTY" and snapshot["sessionId"] is None
        assert sum(snapshot["durations"].values()) == 0
    both = [_detection("tire"), _detection("person")]
    for t, objects in ((51, both), (55, both), (56, [_detection("tire")]), (59, both), (63, both)):
        process_project_nodes(workflow, FRAME, objects, runtime, t)
    snapshot = runtime["timer"]["snapshot"]
    assert snapshot["state"] == "CONFIRMING" and snapshot["workingSeconds"] == 0
    assert snapshot["waitingSeconds"] == 12
    old_session = snapshot["sessionId"]
    node["config"]["confirmationSeconds"] = 0
    events = process_project_nodes(workflow, FRAME, both, runtime, 64)
    assert events[0]["reason"] == "configuration_changed"
    assert events[0]["sessionId"] == old_session
    assert runtime["timer"]["snapshot"]["sessionId"] != old_session


def test_exit_no_spam_first_outside_missing_and_gap():
    node = {"id": "exit", "type": "zone_exit_event", "config": {"points": "0,0;1,0;1,1;0,1", "absenceGraceSeconds": 2}}
    workflow = {"nodes": [node]}
    runtime = {}
    outside = [_detection("truck", (150, 20, 10, 20), "a")]
    for t in (0, 2, 4):
        assert process_project_nodes(workflow, FRAME, outside, runtime, t) == []
    process_project_nodes(workflow, FRAME, [_detection("truck", track="a")], runtime, 5)
    assert process_project_nodes(workflow, FRAME, outside, runtime, 6) == []
    assert process_project_nodes(workflow, FRAME, [], runtime, 7) == []
    assert process_project_nodes(workflow, FRAME, outside, runtime, 8) == []
    events = process_project_nodes(workflow, FRAME, outside, runtime, 10)
    assert len(events) == 1 and events[0]["eventId"]
    assert process_project_nodes(workflow, FRAME, outside, runtime, 11) == []
    process_project_nodes(workflow, FRAME, [_detection("truck", track="a")], runtime, 12)
    for t in (30, 32):
        assert process_project_nodes(workflow, FRAME, outside, runtime, t) == []


def test_required_returns_after_expired_grace_starts_new_session():
    runtime = {}
    node = _timer(confirmationSeconds=0, requiredGraceSeconds=2)
    workflow = {"nodes": [node]}
    both = [_detection("tire"), _detection("person")]
    process_project_nodes(workflow, FRAME, both, runtime, 0)
    original = runtime["timer"]["sessionId"]
    process_project_nodes(workflow, FRAME, [], runtime, 1)
    events = process_project_nodes(workflow, FRAME, both, runtime, 3)
    completed = [event for event in events if event.get("kind") == "zone_activity_event" and event["state"] == "COMPLETED"]
    assert len(completed) == 1 and completed[0]["sessionId"] == original
    assert completed[0]["endedAtMonotonic"] == 0
    assert runtime["timer"]["sessionId"] != original


def test_timer_max_session_duration_latches_once_and_resets():
    workflow = {"nodes": [_timer(confirmationSeconds=0, maxSessionDurationSeconds=5, requiredGraceSeconds=1)]}
    runtime = {}
    both = [_detection("tire"), _detection("person")]
    process_project_nodes(workflow, FRAME, both, runtime, 0)
    events = process_project_nodes(workflow, FRAME, both, runtime, 5)
    limit = [event for event in events if event.get("reason") == "max_session_duration_exceeded"]
    assert len(limit) == 1
    assert limit[0]["state"] == "WORKING"
    assert limit[0]["durationLimitExceededAt"] == 5
    assert runtime["timer"]["snapshot"]["durationLimitExceeded"] is True
    assert not [event for event in process_project_nodes(workflow, FRAME, both, runtime, 6)
                 if event.get("reason") == "max_session_duration_exceeded"]
    # Completion keeps the latch; a later session starts clean.
    process_project_nodes(workflow, FRAME, [], runtime, 7)
    process_project_nodes(workflow, FRAME, [], runtime, 9)
    assert runtime["timer"]["snapshot"]["durationLimitExceeded"] is True
    old_session = runtime["timer"]["sessionId"]
    process_project_nodes(workflow, FRAME, both, runtime, 10)
    assert runtime["timer"]["sessionId"] != old_session
    assert runtime["timer"]["snapshot"]["durationLimitExceeded"] is False


def test_timer_max_session_duration_disabled_and_completion_cutoff():
    runtime = {}
    node = _timer(confirmationSeconds=0, maxSessionDurationSeconds=5, requiredGraceSeconds=2,
                  maxObservationGapSeconds=20)
    workflow = {"nodes": [node]}
    both = [_detection("tire"), _detection("person")]
    process_project_nodes(workflow, FRAME, both, runtime, 0)
    # The tire disappeared before the limit; the late observation closes at 0.
    events = process_project_nodes(workflow, FRAME, [], runtime, 10)
    assert not [event for event in events if event.get("reason") == "max_session_duration_exceeded"]
    assert runtime["timer"]["snapshot"]["durationLimitExceeded"] is False
    disabled = _timer(confirmationSeconds=0, maxSessionDurationSeconds=0)
    runtime = {}
    process_project_nodes({"nodes": [disabled]}, FRAME, both, runtime, 0)
    assert not [event for event in process_project_nodes({"nodes": [disabled]}, FRAME, both, runtime, 100)
                if event.get("reason") == "max_session_duration_exceeded"]


def test_timer_max_session_duration_waits_for_required_grace_resolution():
    node = _timer(confirmationSeconds=0, maxSessionDurationSeconds=5, requiredGraceSeconds=3,
                  maxObservationGapSeconds=20)
    workflow = {"nodes": [node]}
    both = [_detection("tire"), _detection("person")]
    runtime = {}
    process_project_nodes(workflow, FRAME, both, runtime, 0)
    process_project_nodes(workflow, FRAME, both, runtime, 4)
    # The frame at t=5 is still within unresolved tire absence grace.
    events = process_project_nodes(workflow, FRAME, [], runtime, 5)
    assert not [event for event in events if event.get("reason") == "max_session_duration_exceeded"]
    process_project_nodes(workflow, FRAME, [], runtime, 7)
    assert runtime["timer"]["snapshot"]["durationLimitExceeded"] is False

    # A return within grace makes the current observed age eligible.
    runtime = {}
    process_project_nodes(workflow, FRAME, both, runtime, 0)
    process_project_nodes(workflow, FRAME, both, runtime, 4)
    process_project_nodes(workflow, FRAME, [], runtime, 5)
    events = process_project_nodes(workflow, FRAME, both, runtime, 6)
    assert len([event for event in events if event.get("reason") == "max_session_duration_exceeded"]) == 1
    assert not [event for event in process_project_nodes(workflow, FRAME, both, runtime, 7)
                if event.get("reason") == "max_session_duration_exceeded"]


def test_timer_max_session_duration_validation():
    for value in (True, float("nan"), float("inf"), -1):
        try:
            validate_project_config(_timer(maxSessionDurationSeconds=value))
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid maxSessionDurationSeconds accepted: {value!r}")
    assert validate_project_config(_timer(maxSessionDurationSeconds=0)) is True


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} project node checks passed")

