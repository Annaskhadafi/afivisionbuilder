"""VisoNode adapter for the maintained Roboflow ``trackers`` package.

This module translates VisoNode detection dictionaries to Supervision
``Detections`` and delegates every association, motion-estimation, and track
lifecycle decision to Roboflow. It contains no local tracking algorithm.
"""
from __future__ import annotations

import importlib.metadata
import inspect
import math
import warnings
from pathlib import Path
from typing import Hashable

import numpy as np
import supervision as sv
from node_catalog import TRACKER_CONFIG_DEFAULTS

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message=r"target=None is deprecated.*",
        category=FutureWarning,
    )
    from trackers import BoTSORTTracker, ByteTrackTracker, CBIoUTracker, OCSORTTracker


SOURCE_INDEX_KEY = "visonode_source_index"
SUPPORTED_ALGORITHMS = ("bytetrack", "botsort", "ocsort", "cbiou")
CMC_METHODS = ("orb", "sift", "sparseOptFlow", "ecc")
EXPECTED_TRACKERS_VERSION = "2.5.0.post0"
ROBOFLOW_TRACKER_CLASSES = {
    "bytetrack": ByteTrackTracker,
    "botsort": BoTSORTTracker,
    "ocsort": OCSORTTracker,
    "cbiou": CBIoUTracker,
}
ROBOFLOW_TRACKER_MODULES = {
    "bytetrack": "trackers.core.bytetrack.tracker",
    "botsort": "trackers.core.botsort.tracker",
    "ocsort": "trackers.core.ocsort.tracker",
    "cbiou": "trackers.core.cbiou.tracker",
}


def _verified_roboflow_tracker_classes() -> tuple[dict[str, type], str]:
    """Fail closed unless every tracker comes from Roboflow's pinned package."""
    try:
        distribution = importlib.metadata.distribution("trackers")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError(
            "Roboflow Trackers is not installed in the VisoNode AI runtime."
        ) from exc

    if distribution.version != EXPECTED_TRACKERS_VERSION:
        raise RuntimeError(
            "VisoNode requires the validated Roboflow Trackers "
            f"{EXPECTED_TRACKERS_VERSION}, but found {distribution.version}."
        )
    vendor_metadata = " ".join(
        str(distribution.metadata.get(field, ""))
        for field in ("Author-email", "Maintainer-email")
    ).lower()
    if "@roboflow.com" not in vendor_metadata:
        raise RuntimeError(
            "The installed 'trackers' distribution is not identified as "
            "Roboflow's package."
        )

    package_root = Path(distribution.locate_file("trackers")).resolve()
    verified: dict[str, type] = {}
    for algorithm in SUPPORTED_ALGORITHMS:
        tracker_class = ROBOFLOW_TRACKER_CLASSES[algorithm]
        expected_module = ROBOFLOW_TRACKER_MODULES[algorithm]
        if tracker_class.__module__ != expected_module:
            raise RuntimeError(
                f"{algorithm} must use Roboflow's {expected_module}, "
                f"not {tracker_class.__module__}."
            )
        try:
            source_path = Path(inspect.getfile(tracker_class)).resolve()
        except (OSError, TypeError) as exc:
            raise RuntimeError(
                f"Could not verify the source of Roboflow's {algorithm} tracker."
            ) from exc
        if not source_path.is_relative_to(package_root):
            raise RuntimeError(
                f"{algorithm} was loaded from {source_path}, outside the "
                f"installed Roboflow package at {package_root}."
            )
        verified[algorithm] = tracker_class
    return verified, distribution.version


class RoboflowTracker:
    """Adapt all VisoNode tracker modes to Roboflow's tracker implementations."""

    def __init__(self, config: dict) -> None:
        algorithm = str(config.get("algorithm", "bytetrack")).lower()
        self.algorithm = (
            algorithm if algorithm in SUPPORTED_ALGORITHMS else "bytetrack"
        )
        self.config = dict(TRACKER_CONFIG_DEFAULTS)
        self.config.update(config)
        self.class_agnostic = bool(self.config.get("classAgnostic", False))
        self.show_lost_tracks = bool(self.config.get("showLostTracks", False))
        self.frame_rate = self._positive_float(self.config.get("trackerFrameRate", 30), 30)
        self.track_buffer = self._positive_int(self.config.get("trackBuffer", 90), 90)
        self._runtimes: dict[Hashable, object] = {}
        self._global_ids: dict[tuple[Hashable, int], int] = {}
        self._track_state: dict[int, dict] = {}
        self._next_global_id = 1
        self._last_frame_id: int | None = None
        self._last_timestamp: float | None = None
        self._tracker_classes, self.library_version = (
            _verified_roboflow_tracker_classes()
        )

    def status_label(self) -> str:
        detail = " + CMC" if (
            self.algorithm == "botsort"
            and bool(self.config.get("botSortGmc", True))
        ) else ""
        return (
            f"{self.algorithm}{detail} · Roboflow trackers "
            f"{self.library_version}"
        )

    def update(
        self,
        detections: list[dict],
        frame=None,
        *,
        frame_id: int | None = None,
        timestamp: float | None = None,
    ) -> list[dict]:
        self._check_source_continuity(frame_id, timestamp)

        indexed = self._valid_detections(detections)
        grouped: dict[Hashable, list[tuple[int, dict, list[float], float]]] = {}
        for item in indexed:
            scope = self._scope_for(item[1])
            grouped.setdefault(scope, []).append(item)

        for scope in grouped:
            if scope not in self._runtimes:
                self._runtimes[scope] = self._create_runtime()

        current_matches: set[tuple[Hashable, int]] = set()
        outputs: list[tuple[int, dict]] = []
        for scope, runtime in list(self._runtimes.items()):
            items = grouped.get(scope, [])
            library_input = self._to_supervision(items)
            library_frame = frame if self.algorithm == "botsort" else None
            tracked = runtime.update(library_input, frame=library_frame)
            scope_outputs, scope_matches = self._matched_outputs(
                scope,
                runtime,
                tracked,
                detections,
            )
            # Ensure any detection in items that was omitted by tracker thresholds is preserved
            covered_indices = {out[0] for out in scope_outputs}
            for item in items:
                src_idx = int(item[0])
                if src_idx not in covered_indices:
                    det = dict(item[1])
                    box = [float(v) for v in item[2]]
                    sc = float(item[3])
                    scope_outputs.append((
                        src_idx,
                        self._decorate_untracked(det, box, sc),
                    ))
            outputs.extend(scope_outputs)
            current_matches.update(scope_matches)

        if self.show_lost_tracks:
            outputs.extend(self._lost_outputs(current_matches))

        self._prune_metadata(current_matches)
        outputs.sort(key=lambda item: item[0])
        return [item[1] for item in outputs]

    def reset(self) -> None:
        self._clear_library_state()
        self._track_state.clear()
        self._next_global_id = 1
        self._last_frame_id = None
        self._last_timestamp = None

    def _create_runtime(self):
        if self.algorithm == "botsort":
            cmc_method = str(
                self.config.get("botSortCmcMethod", "sparseOptFlow")
            )
            if cmc_method not in CMC_METHODS:
                cmc_method = "sparseOptFlow"
            return self._tracker_classes["botsort"](
                lost_track_buffer=self.track_buffer,
                frame_rate=self.frame_rate,
                track_activation_threshold=self._probability(
                    self.config.get("newTrackThreshold", 0.5),
                    0.5,
                ),
                minimum_consecutive_frames=self._positive_int(
                    self.config.get("minimumConsecutiveFrames", 1),
                    1,
                ),
                minimum_iou_threshold_first_assoc=self._probability(
                    self.config.get("botSortFirstIouThreshold", 0.2),
                    0.2,
                ),
                minimum_iou_threshold_second_assoc=self._probability(
                    self.config.get("botSortSecondIouThreshold", 0.5),
                    0.5,
                ),
                minimum_iou_threshold_unconfirmed_assoc=self._probability(
                    self.config.get("botSortUnconfirmedIouThreshold", 0.3),
                    0.3,
                ),
                high_conf_det_threshold=self._probability(
                    self.config.get("trackHighThreshold", 0.45),
                    0.45,
                ),
                enable_cmc=bool(self.config.get("botSortGmc", True)),
                cmc_method=cmc_method,
                cmc_downscale=self._positive_int(
                    self.config.get("botSortCmcDownscale", 2),
                    2,
                ),
            )
        if self.algorithm == "ocsort":
            return self._tracker_classes["ocsort"](
                lost_track_buffer=self._positive_int(
                    self.config.get("ocSortMaxAge", 30),
                    30,
                ),
                frame_rate=self.frame_rate,
                minimum_consecutive_frames=self._positive_int(
                    self.config.get("ocSortMinHits", 3),
                    3,
                ),
                minimum_iou_threshold=self._probability(
                    self.config.get("ocSortIouThreshold", 0.3),
                    0.3,
                ),
                direction_consistency_weight=self._probability(
                    self.config.get("ocSortInertia", 0.2),
                    0.2,
                ),
                high_conf_det_threshold=self._probability(
                    self.config.get("ocSortDetectionThreshold", 0.6),
                    0.6,
                ),
                delta_t=self._positive_int(
                    self.config.get("ocSortDeltaT", 3),
                    3,
                ),
            )
        if self.algorithm == "cbiou":
            return self._tracker_classes["cbiou"](
                lost_track_buffer=self.track_buffer,
                frame_rate=self.frame_rate,
                track_activation_threshold=self._probability(self.config.get("newTrackThreshold", 0.5), 0.5),
                minimum_consecutive_frames=self._positive_int(self.config.get("minimumConsecutiveFrames", 1), 1),
                minimum_iou_threshold_first_assoc=self._probability(self.config.get("botSortFirstIouThreshold", 0.2), 0.2),
                minimum_iou_threshold_second_assoc=self._probability(self.config.get("botSortSecondIouThreshold", 0.5), 0.5),
                minimum_iou_threshold_unconfirmed_assoc=self._probability(self.config.get("botSortUnconfirmedIouThreshold", 0.3), 0.3),
                high_conf_det_threshold=self._probability(self.config.get("trackHighThreshold", 0.45), 0.45),
                buffer_ratio_first=0.3,
                buffer_ratio_second=0.5,
            )
        return self._tracker_classes["bytetrack"](
            lost_track_buffer=self.track_buffer,
            frame_rate=self.frame_rate,
            track_activation_threshold=self._probability(
                self.config.get("newTrackThreshold", 0.5),
                0.5,
            ),
            minimum_consecutive_frames=self._positive_int(
                self.config.get("minimumConsecutiveFrames", 1),
                1,
            ),
            minimum_iou_threshold=self._probability(
                self.config.get("matchThreshold", 0.1),
                0.1,
            ),
            high_conf_det_threshold=self._probability(
                self.config.get("trackHighThreshold", 0.45),
                0.45,
            ),
        )

    def _valid_detections(
        self,
        detections: list[dict],
    ) -> list[tuple[int, dict, list[float], float]]:
        minimum_score = (
            self._probability(
                self.config.get("ocSortDetectionThreshold", 0.6),
                0.6,
            )
            if self.algorithm == "ocsort"
            else self._probability(
                self.config.get("trackLowThreshold", 0.1),
                0.1,
            )
        )
        valid = []
        for index, detection in enumerate(detections):
            bbox = detection.get("bbox")
            if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
                continue
            try:
                x, y, width, height = [float(value) for value in bbox[:4]]
                score = float(detection.get("score", 0))
            except (TypeError, ValueError):
                continue
            if not all(math.isfinite(value) for value in (x, y, width, height, score)):
                continue
            if width <= 0 or height <= 0 or score < minimum_score:
                continue
            valid.append((
                index,
                detection,
                [x, y, x + width, y + height],
                score,
            ))
        return valid

    def _to_supervision(
        self,
        items: list[tuple[int, dict, list[float], float]],
    ) -> sv.Detections:
        if not items:
            return sv.Detections.empty()
        return sv.Detections(
            xyxy=np.asarray([item[2] for item in items], dtype=np.float32),
            confidence=np.asarray([item[3] for item in items], dtype=np.float32),
            data={
                SOURCE_INDEX_KEY: np.asarray(
                    [item[0] for item in items],
                    dtype=np.int64,
                ),
            },
        )

    def _matched_outputs(
        self,
        scope: Hashable,
        runtime,
        tracked: sv.Detections,
        source_detections: list[dict],
    ) -> tuple[list[tuple[int, dict]], set[tuple[Hashable, int]]]:
        outputs = []
        matches: set[tuple[Hashable, int]] = set()
        tracker_ids = tracked.tracker_id
        source_indices = tracked.data.get(SOURCE_INDEX_KEY)
        if tracker_ids is None or source_indices is None:
            return outputs, matches

        confidences = tracked.confidence
        for row, raw_local_id in enumerate(tracker_ids):
            local_id = int(raw_local_id)
            source_index = int(source_indices[row])
            if not 0 <= source_index < len(source_detections):
                continue
            if local_id < 0:
                outputs.append((
                    source_index,
                    self._decorate_untracked(
                        source_detections[source_index],
                        [float(value) for value in tracked.xyxy[row]],
                        float(confidences[row]) if confidences is not None else 0.0,
                    ),
                ))
                continue
            global_id = self._global_id(scope, local_id)
            detection = dict(source_detections[source_index])
            score = (
                float(confidences[row])
                if confidences is not None
                else float(detection.get("score", 0))
            )
            box = [float(value) for value in tracked.xyxy[row]]
            tracklet = next(
                (
                    track
                    for track in getattr(runtime, "tracks", [])
                    if int(getattr(track, "tracker_id", -1)) == local_id
                ),
                None,
            )
            library_age = max(1, int(getattr(tracklet, "age", 0)) + 1)
            self._update_track_state(
                global_id,
                detection,
                box,
                score,
                library_age=library_age,
            )
            outputs.append((
                source_index,
                self._decorate_detection(global_id, detection, box, score, 0),
            ))
            matches.add((scope, local_id))
        return outputs, matches

    def _lost_outputs(
        self,
        current_matches: set[tuple[Hashable, int]],
    ) -> list[tuple[int, dict]]:
        outputs = []
        lost_order = 0
        for scope, runtime in self._runtimes.items():
            predicted = runtime.tracked_objects
            if predicted.tracker_id is None:
                continue
            for row, raw_local_id in enumerate(predicted.tracker_id):
                local_id = int(raw_local_id)
                key = (scope, local_id)
                if key in current_matches or key not in self._global_ids:
                    continue
                global_id = self._global_ids[key]
                state = self._track_state.get(global_id)
                if not state:
                    continue
                tracklet = next(
                    (
                        track
                        for track in getattr(runtime, "tracks", [])
                        if int(getattr(track, "tracker_id", -1)) == local_id
                    ),
                    None,
                )
                lost = max(1, int(getattr(tracklet, "time_since_update", 1)))
                detection = dict(state["detection"])
                box = [float(value) for value in predicted.xyxy[row]]
                outputs.append((
                    len(self._track_state) + lost_order,
                    self._decorate_detection(
                        global_id,
                        detection,
                        box,
                        float(state["score"]),
                        lost,
                    ),
                ))
                lost_order += 1
        return outputs

    def _decorate_detection(
        self,
        global_id: int,
        detection: dict,
        box: list[float],
        score: float,
        lost: int,
    ) -> dict:
        state = self._track_state[global_id]
        result = dict(detection)
        result["bbox"] = [
            box[0],
            box[1],
            max(0.0, box[2] - box[0]),
            max(0.0, box[3] - box[1]),
        ]
        result["score"] = score
        result["trackId"] = global_id
        result["trackAge"] = int(state["hits"])
        result["trackLost"] = int(lost)
        result["trackingAlgorithm"] = self.algorithm
        result["trackingLibrary"] = "roboflow-trackers"
        result["trackingLibraryVersion"] = self.library_version
        result["originSourceNodeId"] = result.get("sourceNodeId", "detector")
        result["sourceNodeId"] = "tracker"
        result["trail"] = list(state["trail"])
        return result

    def _decorate_untracked(
        self, detection: dict, box: list[float], score: float
    ) -> dict:
        result = dict(detection)
        result["bbox"] = [box[0], box[1], max(0.0, box[2] - box[0]), max(0.0, box[3] - box[1])]
        result["score"] = score
        for key in ("trackId", "trackAge", "trackLost", "trail"):
            result.pop(key, None)
        result["trackingAlgorithm"] = self.algorithm
        result["trackingLibrary"] = "roboflow-trackers"
        result["trackingLibraryVersion"] = self.library_version
        result["originSourceNodeId"] = result.get("sourceNodeId", "detector")
        result["sourceNodeId"] = "tracker"
        return result

    def _update_track_state(
        self,
        global_id: int,
        detection: dict,
        box: list[float],
        score: float,
        *,
        library_age: int,
    ) -> None:
        center = [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]
        state = self._track_state.setdefault(
            global_id,
            {"hits": 0, "trail": [], "detection": {}, "score": score},
        )
        state["hits"] = max(int(state["hits"]) + 1, library_age)
        state["detection"] = dict(detection)
        state["score"] = score
        state["trail"].append(center)
        del state["trail"][:-32]

    def _global_id(self, scope: Hashable, local_id: int) -> int:
        key = (scope, local_id)
        if key not in self._global_ids:
            self._global_ids[key] = self._next_global_id
            self._next_global_id += 1
        return self._global_ids[key]

    def _scope_for(self, detection: dict) -> Hashable:
        if self.class_agnostic:
            return "__all__"
        return str(detection.get("class", "object"))

    def _check_source_continuity(
        self,
        frame_id: int | None,
        timestamp: float | None,
    ) -> None:
        if frame_id is not None:
            try:
                current_frame_id = int(frame_id)
            except (TypeError, ValueError):
                current_frame_id = None
            if current_frame_id is not None:
                if (
                    self._last_frame_id is not None
                    and current_frame_id <= self._last_frame_id
                ):
                    self._clear_library_state()
                self._last_frame_id = current_frame_id
        if timestamp is not None:
            try:
                current_timestamp = float(timestamp)
            except (TypeError, ValueError):
                current_timestamp = None
            if current_timestamp is not None and math.isfinite(current_timestamp):
                if (
                    self._last_timestamp is not None
                    and current_timestamp > self._last_timestamp
                ):
                    inactivity_limit = self._lost_buffer_for_algorithm() / 30.0
                    if current_timestamp - self._last_timestamp > inactivity_limit:
                        self._clear_library_state()
                elif (
                    self._last_timestamp is not None
                    and current_timestamp <= self._last_timestamp
                ):
                    self._clear_library_state()
                self._last_timestamp = current_timestamp

    def _clear_library_state(self) -> None:
        self._runtimes.clear()
        self._global_ids.clear()
        self._track_state.clear()

    def _prune_metadata(self, current_matches: set[tuple[Hashable, int]] | None = None) -> None:
        alive_keys = {
            (scope, int(track.tracker_id))
            for scope, runtime in self._runtimes.items()
            for track in getattr(runtime, "tracks", [])
            if int(getattr(track, "tracker_id", -1)) >= 0
        }
        if current_matches:
            alive_keys.update(current_matches)
        removed_global_ids = {
            global_id
            for key, global_id in self._global_ids.items()
            if key not in alive_keys
        }
        self._global_ids = {
            key: global_id
            for key, global_id in self._global_ids.items()
            if key in alive_keys
        }
        still_mapped = set(self._global_ids.values())
        for global_id in removed_global_ids - still_mapped:
            self._track_state.pop(global_id, None)

    def _lost_buffer_for_algorithm(self) -> int:
        if self.algorithm == "ocsort":
            return self._positive_int(
                self.config.get("ocSortMaxAge", 30),
                30,
            )
        return self.track_buffer

    @staticmethod
    def _probability(value, fallback: float) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _positive_int(value, fallback: int) -> int:
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _positive_float(value, fallback: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return fallback
        return parsed if math.isfinite(parsed) and parsed > 0 else fallback
