"""Small installed-runtime checks for the Roboflow tracker adapter."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine"))

from roboflow_tracker import RoboflowTracker, SUPPORTED_ALGORITHMS


def detection(x, score=0.9, label="object"):
    return {"bbox": [x, 10, 20, 20], "score": score, "class": label, "sourceNodeId": "detector"}


def tracked(result):
    return [item for item in result if item.get("trackId") is not None]


def make(algorithm):
    return RoboflowTracker({
        "algorithm": algorithm,
        "trackBuffer": 90,
        "minimumConsecutiveFrames": 1,
        "botSortGmc": False,
    })


def main():
    for algorithm in SUPPORTED_ALGORITHMS:
        runtime = make(algorithm)
        first = runtime.update([detection(10)], frame_id=1, timestamp=0)
        second = runtime.update([detection(11)], frame_id=5, timestamp=0.1)
        assert tracked(second), (algorithm, first, second)
        track_id = tracked(second)[0]["trackId"]
        recovered = runtime.update([], frame_id=6, timestamp=0.2)
        assert not recovered
        assert tracked(runtime.update([detection(12)], frame_id=7, timestamp=0.3))[0]["trackId"] == track_id

    runtime = make("bytetrack")
    runtime.update([detection(10)], frame_id=1, timestamp=0)
    assert tracked(runtime.update([detection(11)], frame_id=2, timestamp=0.1))
    assert not tracked(runtime.update([detection(12, score=0.05)], frame_id=3, timestamp=0.2))
    fresh = tracked(runtime.update([detection(13)], frame_id=4, timestamp=0.3))
    assert fresh and fresh[0]["trackId"]

    runtime = make("bytetrack")
    runtime.update([detection(10)], frame_id=1, timestamp=0)
    old = tracked(runtime.update([detection(10)], frame_id=2, timestamp=0.1))[0]["trackId"]
    runtime.update([], frame_id=3, timestamp=4)
    runtime.update([detection(10)], frame_id=4, timestamp=4.1)
    new = tracked(runtime.update([detection(10)], frame_id=5, timestamp=4.2))[0]["trackId"]
    assert new != old

    runtime = make("bytetrack")
    runtime.update([detection(10)], frame_id=10)
    old = tracked(runtime.update([detection(10)], frame_id=11))[0]["trackId"]
    runtime.update([detection(10)], frame_id=2)
    new = tracked(runtime.update([detection(10)], frame_id=3))[0]["trackId"]
    assert new != old

    runtime = make("bytetrack")
    first = runtime.update([detection(10), detection(100)], frame_id=1)
    second = tracked(runtime.update([detection(100), detection(10)], frame_id=2))
    assert len({item["trackId"] for item in second}) == 2
    identities = {int(item["bbox"][0]): item["trackId"] for item in second}
    reordered = tracked(runtime.update([detection(10), detection(100)], frame_id=3))
    assert {int(item["bbox"][0]): item["trackId"] for item in reordered} == identities

    runtime = RoboflowTracker({"minimumConsecutiveFrames": 2})
    outputs = [runtime.update([detection(10)], frame_id=i * 15 + 1, timestamp=i * .5)
               for i in range(6)]
    assert "trackId" not in outputs[0][0]
    ids = [item["trackId"] for batch in outputs for item in batch if "trackId" in item]
    assert ids and len(set(ids)) == 1, outputs
    low = make("bytetrack").update([detection(10, score=.2)], frame_id=1)
    assert low and "trackId" not in low[0]

    runtime = make("cbiou")
    first = tracked(runtime.update([detection(10)], frame_id=1))[0]["trackId"]
    second = tracked(runtime.update([detection(30)], frame_id=2))[0]["trackId"]
    assert second == first

    # Test Track Class Lock (majority voting against jitter)
    class_locked_tracker = RoboflowTracker({
        "algorithm": "bytetrack",
        "minimumConsecutiveFrames": 1,
        "enableClassLock": True,
        "classLockWindow": 5,
    })
    d1 = class_locked_tracker.update([{"bbox": [10, 10, 20, 20], "score": 0.9, "class": "car"}], frame_id=1)
    d2 = class_locked_tracker.update([{"bbox": [11, 10, 20, 20], "score": 0.9, "class": "car"}], frame_id=2)
    # 3rd frame has label jitter to "truck"
    d3 = class_locked_tracker.update([{"bbox": [12, 10, 20, 20], "score": 0.9, "class": "truck"}], frame_id=3)
    tracked_d3 = tracked(d3)[0]
    assert tracked_d3["class"] == "car", f"Expected locked class 'car', got {tracked_d3['class']}"
    assert tracked_d3["rawClass"] == "truck", f"Expected rawClass 'truck', got {tracked_d3.get('rawClass')}"

    # Test Bounding Box Stabilizer (EMA Smoothing)
    smoothed_tracker = RoboflowTracker({
        "algorithm": "bytetrack",
        "minimumConsecutiveFrames": 1,
        "enableSmoothing": True,
        "smoothingAlpha": 0.5,
    })
    # Frame 1: tracklet initiated
    smoothed_tracker.update([{"bbox": [10, 10, 20, 20], "score": 0.9, "class": "box"}], frame_id=1)
    # Frame 2: track confirmed at x=10
    s2 = tracked(smoothed_tracker.update([{"bbox": [10, 10, 20, 20], "score": 0.9, "class": "box"}], frame_id=2))
    assert s2, "Expected track to be confirmed at frame 2"
    assert abs(s2[0]["bbox"][0] - 10.0) < 0.1
    # Frame 3: bbox jumps from x=10 to x=20
    s3 = tracked(smoothed_tracker.update([{"bbox": [20, 10, 20, 20], "score": 0.9, "class": "box"}], frame_id=3))
    assert s3, "Expected track to continue at frame 3"
    # EMA with alpha=0.5: 0.5 * 20 + 0.5 * 10 = 15.0
    assert abs(s3[0]["bbox"][0] - 15.0) < 0.1, f"Expected smoothed bbox x around 15.0, got {s3[0]['bbox'][0]}"

    print("tracking checks passed")


if __name__ == "__main__":
    main()
