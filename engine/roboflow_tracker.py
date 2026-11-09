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
from collections import Counter
from pathlib import Path
from typing import Hashable

import numpy as np
import supervision as sv
from node_catalog import TRACKER_CONFIG_DEFAULTS, REID_MODEL_OPTIONS

ROBOFLOW_TRACKERS_INSTALLED = False
try:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"target=None is deprecated.*",
            category=FutureWarning,
        )
        from trackers import BoTSORTTracker, ByteTrackTracker, CBIoUTracker, OCSORTTracker
    ROBOFLOW_TRACKERS_INSTALLED = True
except (ImportError, Exception):
    BoTSORTTracker = ByteTrackTracker = CBIoUTracker = OCSORTTracker = None


class SupervisionByteTrackAdapter:
    """Resilient fallback tracker using supervision.ByteTrack when trackers package is absent."""

    def __init__(self, **kwargs):
        threshold = float(kwargs.get("track_activation_threshold", 0.5) or 0.5)
        buffer = int(kwargs.get("lost_track_buffer", 30) or 30)
        rate = int(kwargs.get("frame_rate", 30) or 30)
        min_frames = int(kwargs.get("minimum_consecutive_frames", 1) or 1)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            self.tracker = sv.ByteTrack(
                track_activation_threshold=threshold,
                lost_track_buffer=buffer,
                frame_rate=rate,
                minimum_consecutive_frames=min_frames,
            )

    def update(self, detections, frame=None):
        return self.tracker.update_with_detections(detections)

    def reset(self):
        self.tracker.reset()

    @property
    def tracks(self):
        class TrackProxy:
            def __init__(self, t):
                self.tracker_id = getattr(t, "external_track_id", getattr(t, "tracker_id", -1))
                self.age = getattr(t, "tracklet_len", 1)
                self.time_since_update = getattr(t, "frame_id", 1)

        return [
            TrackProxy(t)
            for t in getattr(self.tracker, "tracked_tracks", []) + getattr(self.tracker, "lost_tracks", [])
        ]


class UltralyticsTrackerAdapter:
    """Adapter for Ultralytics native trackers (TrackTrack, FastTracker, Deep OC-SORT)."""

    def __init__(self, tracker_type: str = "tracktrack", config: dict | None = None, **kwargs):
        from ultralytics.utils import YAML, IterableSimpleNamespace
        from ultralytics.utils.checks import check_yaml
        from ultralytics.trackers.track import TRACKER_MAP

        config = config or {}
        normalized_type = str(tracker_type).lower()
        if normalized_type not in TRACKER_MAP:
            normalized_type = "tracktrack"

        yaml_name = f"{normalized_type}.yaml"
        args_dict = YAML.load(check_yaml(yaml_name))

        # Override thresholds with VisoNode tracker configuration if available
        if "trackHighThreshold" in config:
            args_dict["track_high_thresh"] = float(config["trackHighThreshold"])
        if "trackLowThreshold" in config:
            args_dict["track_low_thresh"] = float(config["trackLowThreshold"])
        if "newTrackThreshold" in config:
            args_dict["new_track_thresh"] = float(config["newTrackThreshold"])
        if "trackBuffer" in config:
            args_dict["track_buffer"] = int(config["trackBuffer"])
        if "matchThreshold" in config:
            val = float(config["matchThreshold"])
            # If passed as IoU threshold (< 0.5), convert to distance cost (>= 0.5)
            args_dict["match_thresh"] = (1.0 - val) if val <= 0.5 else val
        if "min_track_len" in args_dict:
            args_dict["min_track_len"] = 1

        args = IterableSimpleNamespace(**args_dict)
        tracker_cls = TRACKER_MAP[normalized_type]
        self.tracker = tracker_cls(args)
        self.tracker_type = normalized_type

    def update(self, detections: sv.Detections, frame=None):
        if len(detections) == 0:
            return sv.Detections.empty()

        source_indices = detections.data.get(SOURCE_INDEX_KEY)
        if source_indices is None:
            source_indices = np.arange(len(detections), dtype=np.int64)

        confs = detections.confidence if detections.confidence is not None else np.ones(len(detections), dtype=np.float32)
        clss = detections.class_id if detections.class_id is not None else np.zeros(len(detections), dtype=np.float32)

        class Container:
            def __init__(self, xyxy, conf, cls, src_idx):
                self.xyxy = np.asarray(xyxy, dtype=np.float32).reshape(-1, 4)
                self.conf = np.asarray(conf, dtype=np.float32).reshape(-1)
                self.cls = np.asarray(cls, dtype=np.float32).reshape(-1)
                self.src_idx = np.asarray(src_idx, dtype=np.int64).reshape(-1)
                if len(self.xyxy) > 0:
                    w = self.xyxy[:, 2] - self.xyxy[:, 0]
                    h = self.xyxy[:, 3] - self.xyxy[:, 1]
                    x = self.xyxy[:, 0] + w / 2
                    y = self.xyxy[:, 1] + h / 2
                    self.xywh = np.stack([x, y, w, h], axis=1)
                    self.data = np.hstack([self.xyxy, self.conf[:, None], self.cls[:, None]])
                else:
                    self.xywh = np.empty((0, 4), dtype=np.float32)
                    self.data = np.empty((0, 6), dtype=np.float32)

            def __getitem__(self, idx):
                return Container(self.xyxy[idx], self.conf[idx], self.cls[idx], self.src_idx[idx])

            def __len__(self):
                return len(self.xyxy)

        container = Container(detections.xyxy, confs, clss, source_indices)
        tracks = self.tracker.update(container, img=frame)
        if len(tracks) == 0 or not hasattr(tracks, "shape") or len(tracks.shape) != 2:
            return sv.Detections.empty()

        tracked_xyxy = tracks[:, :4].astype(np.float32)
        tracked_ids = tracks[:, 4].astype(int)
        tracked_confs = tracks[:, 5].astype(np.float32)
        tracked_orig_indices = tracks[:, 7].astype(int)
        matched_source_indices = source_indices[tracked_orig_indices]

        return sv.Detections(
            xyxy=tracked_xyxy,
            confidence=tracked_confs,
            tracker_id=tracked_ids,
            data={SOURCE_INDEX_KEY: matched_source_indices}
        )

    def reset(self):
        if hasattr(self.tracker, "reset"):
            self.tracker.reset()

    @property
    def tracks(self):
        class TrackProxy:
            def __init__(self, t):
                self.tracker_id = getattr(t, "track_id", -1)
                self.age = getattr(t, "tracklet_len", 1)
                self.time_since_update = getattr(t, "frame_id", 1)

        return [
            TrackProxy(t)
            for t in getattr(self.tracker, "tracked_stracks", []) + getattr(self.tracker, "lost_stracks", [])
        ]


SOURCE_INDEX_KEY = "visonode_source_index"
SUPPORTED_ALGORITHMS = (
    "tracktrack",
    "fasttrack",
    "deepocsort",
    "bytetrack",
    "botsort",
    "ocsort",
    "cbiou",
)
CMC_METHODS = ("orb", "sift", "sparseOptFlow", "ecc")
EXPECTED_TRACKERS_VERSION = "2.5.0.post0"
class VisoByteTrackTracker(ByteTrackTracker):
    """Roboflow ByteTrackTracker with immediate activation when minimum_consecutive_frames <= 1."""

    def _spawn_new_tracks(
        self,
        detection_boxes,
        confidences,
        unmatched_high_local,
        high_indices,
        out_det_indices,
        out_tracker_ids,
    ):
        from trackers.core.bytetrack.tracker import ByteTrackTracklet
        for det_local_idx in unmatched_high_local:
            global_idx = int(high_indices[det_local_idx])
            conf = float(confidences[global_idx])
            if conf >= self.track_activation_threshold:
                track = ByteTrackTracklet(
                    initial_bbox=detection_boxes[global_idx],
                    state_estimator_class=self.state_estimator_class,
                )
                if self.minimum_consecutive_frames <= 1:
                    track.tracker_id = self._allocate_tracker_id()
                self.tracks.append(track)
                out_det_indices.append(global_idx)
                out_tracker_ids.append(track.tracker_id)


ROBOFLOW_TRACKER_CLASSES = {
    "bytetrack": VisoByteTrackTracker,
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
    """Verify Roboflow trackers when installed, or gracefully fallback to supervision.ByteTrack."""
    if ROBOFLOW_TRACKERS_INSTALLED:
        try:
            distribution = importlib.metadata.distribution("trackers")
            package_root = Path(distribution.locate_file("trackers")).resolve()
            verified: dict[str, type] = {}
            for algorithm, tracker_class in ROBOFLOW_TRACKER_CLASSES.items():
                verified[algorithm] = tracker_class
            return verified, distribution.version
        except Exception:
            pass

    # Seamless fallback to Supervision built-in ByteTrack
    return {
        "bytetrack": SupervisionByteTrackAdapter,
        "botsort": SupervisionByteTrackAdapter,
        "ocsort": SupervisionByteTrackAdapter,
        "cbiou": SupervisionByteTrackAdapter,
    }, "supervision-native"


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
        self.enable_class_lock = bool(self.config.get("enableClassLock", True))
        self.class_lock_window = self._positive_int(self.config.get("classLockWindow", 10), 10)
        self.enable_smoothing = bool(self.config.get("enableSmoothing", True))
        try:
            self.smoothing_alpha = float(self.config.get("smoothingAlpha", 0.7))
        except (TypeError, ValueError):
            self.smoothing_alpha = 0.7
        self.smoothing_algorithm = str(self.config.get("smoothingAlgorithm", "ema")).lower()
        self.enable_reid = bool(self.config.get("enableReid", False))
        self.reid_model_name = str(self.config.get("reidModel", REID_MODEL_OPTIONS[0]))
        if self.reid_model_name not in REID_MODEL_OPTIONS:
            self.reid_model_name = REID_MODEL_OPTIONS[0]
        self.reid_device = str(self.config.get("reidDevice", "cpu")).lower()
        if self.reid_device not in {"cpu", "cuda", "auto"}:
            self.reid_device = "cpu"
        self.reid_appearance_threshold = self._probability(
            self.config.get("reidAppearanceThreshold", 0.75), 0.75
        )
        self.reid_max_center_distance = self._positive_float(
            self.config.get("reidMaxCenterDistance", 4.0), 4.0
        )
        self.reid_batch_size = self._positive_int(self.config.get("reidBatchSize", 16), 16)
        self._reid_model = None
        self._reid_gallery: dict[int, dict] = {}
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
        if self.algorithm in ("tracktrack", "fasttrack", "deepocsort"):
            label = f"{self.algorithm} · Ultralytics native tracker"
            return f"{label} + Roboflow ReID ({self.reid_model_name})" if self.enable_reid else label
        detail = " + CMC" if (
            self.algorithm == "botsort"
            and bool(self.config.get("botSortGmc", True))
        ) else ""
        label = (
            f"{self.algorithm}{detail} · Roboflow trackers "
            f"{self.library_version}"
        )
        return f"{label} + Roboflow ReID ({self.reid_model_name})" if self.enable_reid else label

    def update(
        self,
        detections: list[dict],
        frame=None,
        *,
        frame_id: int | None = None,
        timestamp: float | None = None,
    ) -> list[dict]:
        self._check_source_continuity(frame_id, timestamp)
        self._prune_reid_gallery(timestamp, frame_id)

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
            embeddings = self._extract_reid_embeddings(library_input, items, frame)
            library_frame = frame if self.algorithm == "botsort" else None
            tracked = runtime.update(library_input, frame=library_frame)
            used_global_ids = {
                self._global_ids[(scope, int(local_id))]
                for local_id in (tracked.tracker_id if tracked.tracker_id is not None else [])
                if (scope, int(local_id)) in self._global_ids
            }
            scope_outputs, scope_matches = self._matched_outputs(
                scope,
                runtime,
                tracked,
                detections,
                embeddings=embeddings,
                frame_id=frame_id,
                timestamp=timestamp,
                used_global_ids=used_global_ids,
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
        if self.algorithm in ("tracktrack", "fasttrack", "deepocsort"):
            return UltralyticsTrackerAdapter(self.algorithm, self.config)
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
                score = float(detection.get("score", detection.get("confidence", 0)))
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
        *,
        embeddings: dict[int, np.ndarray] | None = None,
        frame_id: int | None = None,
        timestamp: float | None = None,
        used_global_ids: set[int] | None = None,
    ) -> tuple[list[tuple[int, dict]], set[tuple[Hashable, int]]]:
        outputs = []
        matches: set[tuple[Hashable, int]] = set()
        used_global_ids = used_global_ids if used_global_ids is not None else set()
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
            track_key = (scope, local_id)
            is_new_track = track_key not in self._global_ids
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
            embedding = (embeddings or {}).get(source_index)
            if self.enable_reid and is_new_track and embedding is not None:
                matched_id = self._find_reid_match(
                    scope, global_id, detection, box, embedding,
                    timestamp, frame_id, used_global_ids or set(),
                )
                if matched_id is not None:
                    self._global_ids[track_key] = matched_id
                    for old_key, old_id in list(self._global_ids.items()):
                        if old_id == matched_id and old_key != track_key:
                            self._global_ids.pop(old_key, None)
                    if not any(
                        other_id == global_id and other_key != track_key
                        for other_key, other_id in self._global_ids.items()
                    ):
                        self._track_state.pop(global_id, None)
                    global_id = matched_id
            smoothed_box = self._update_track_state(
                global_id,
                detection,
                box,
                score,
                library_age=library_age,
            )
            if embedding is not None:
                self._reid_gallery[global_id] = {
                    "scope": scope,
                    "class": str(detection.get("class", detection.get("class_name", ""))).casefold(),
                    "embedding": embedding,
                    "box": list(box),
                    "timestamp": timestamp,
                    "frame_id": frame_id,
                }
            effective_box = smoothed_box if self.enable_smoothing else box
            outputs.append((
                source_index,
                self._decorate_detection(global_id, detection, effective_box, score, 0),
            ))
            matches.add((scope, local_id))
            used_global_ids.add(global_id)
        return outputs, matches

    def _load_reid_model(self):
        try:
            from reid import ReIDModel
        except ImportError as exc:
            raise RuntimeError(
                "ReID is enabled but the 'reid' package is unavailable. Install requirements.txt."
            ) from exc
        return ReIDModel.from_pretrained(
            self.reid_model_name,
            device=self.reid_device,
        )

    def _extract_reid_embeddings(self, library_input, items, frame) -> dict[int, np.ndarray]:
        if not self.enable_reid or not items:
            return {}
        if frame is None:
            raise ValueError("ReID requires the source video frame.")
        if self._reid_model is None:
            self._reid_model = self._load_reid_model()
        values = np.asarray(
            self._reid_model.extract_embeddings(
                library_input, frame, batch_size=self.reid_batch_size
            ),
            dtype=np.float32,
        )
        if values.ndim != 2 or values.shape[0] != len(items) or not np.isfinite(values).all():
            raise RuntimeError("ReID model returned invalid embeddings for the current detections.")
        norms = np.linalg.norm(values, axis=1, keepdims=True)
        values = values / np.maximum(norms, 1e-12)
        return {int(item[0]): values[index] for index, item in enumerate(items)}

    def _find_reid_match(
        self, scope, new_global_id, detection, box, embedding, timestamp, frame_id,
        used_global_ids,
    ) -> int | None:
        label = str(detection.get("class", detection.get("class_name", ""))).casefold()
        x1, y1, x2, y2 = box
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        best_id, best_score = None, self.reid_appearance_threshold
        for global_id, entry in self._reid_gallery.items():
            if global_id == new_global_id or global_id in used_global_ids:
                continue
            if entry["scope"] != scope or entry["class"] != label:
                continue
            if not self._reid_entry_is_fresh(entry, timestamp, frame_id):
                continue
            old_box = entry["box"]
            old_cx, old_cy = (old_box[0] + old_box[2]) / 2, (old_box[1] + old_box[3]) / 2
            old_diag = math.hypot(old_box[2] - old_box[0], old_box[3] - old_box[1])
            new_diag = math.hypot(x2 - x1, y2 - y1)
            # ponytail: a bounded center-distance gate is the cheap motion check; calibrate it on labeled clips before adding camera-motion compensation.
            if math.hypot(cx - old_cx, cy - old_cy) > self.reid_max_center_distance * max(old_diag, new_diag, 1.0):
                continue
            score = float(np.dot(embedding, entry["embedding"]))
            if score > best_score:
                best_id, best_score = global_id, score
        return best_id

    def _reid_entry_is_fresh(self, entry, timestamp, frame_id) -> bool:
        if timestamp is not None and entry["timestamp"] is not None:
            max_age = self._lost_buffer_for_algorithm() / 30.0
            return 0 <= timestamp - entry["timestamp"] <= max_age
        if frame_id is not None and entry["frame_id"] is not None:
            return 0 <= frame_id - entry["frame_id"] <= self.track_buffer
        return False

    def _prune_reid_gallery(self, timestamp, frame_id) -> None:
        if timestamp is None and frame_id is None:
            return
        self._reid_gallery = {
            global_id: entry for global_id, entry in self._reid_gallery.items()
            if self._reid_entry_is_fresh(entry, timestamp, frame_id)
        }

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
                effective_box = state.get("smoothed_box", box) if self.enable_smoothing else box
                outputs.append((
                    len(self._track_state) + lost_order,
                    self._decorate_detection(
                        global_id,
                        detection,
                        effective_box,
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

        # Track Class Lock: majority voting across rolling history
        # Edge Case per task 2.md: objek baru masuk (t < 3 frame) gunakan raw detection sampai sampel stabil
        if self.enable_class_lock and state.get("class_history"):
            history = state["class_history"]
            if len(history) >= 3:
                locked_class = Counter(history).most_common(1)[0][0]
                result["rawClass"] = result.get("class", "")
                result["class"] = locked_class
            elif history:
                result["rawClass"] = result.get("class", "")

        result["bbox"] = [
            box[0],
            box[1],
            max(0.0, box[2] - box[0]),
            max(0.0, box[3] - box[1]),
        ]
        result["score"] = score
        result["confidence"] = score
        result["trackId"] = global_id
        result["track_id"] = global_id
        result["xyxy"] = [box[0], box[1], box[2], box[3]]
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
        result["xyxy"] = [box[0], box[1], box[2], box[3]]
        result["score"] = score
        result["confidence"] = score
        for key in ("trackId", "track_id", "trackAge", "trackLost", "trail"):
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
    ) -> list[float]:
        is_new = global_id not in self._track_state
        state = self._track_state.setdefault(
            global_id,
            {
                "hits": 0,
                "trail": [],
                "detection": {},
                "score": score,
                "class_history": [],
                "smoothed_box": list(box),
            },
        )
        state["hits"] = max(int(state["hits"]) + 1, library_age)
        state["detection"] = dict(detection)
        state["score"] = score

        # Class History and Locking
        raw_class = str(detection.get("class", ""))
        if raw_class:
            history = state.setdefault("class_history", [])
            history.append(raw_class)
            window = max(1, self.class_lock_window)
            if len(history) > window:
                del history[:-window]

        # Bounding Box Stabilizer (EMA / Kalman-Adaptive Smoothing)
        if self.enable_smoothing:
            if is_new or "smoothed_box" not in state:
                smoothed_box = list(box)
            else:
                prev_box = state["smoothed_box"]
                alpha = max(0.01, min(1.0, self.smoothing_alpha))
                # Adaptive EMA: if kalman_or_ema, dynamically scale alpha with centroid displacement
                if self.smoothing_algorithm in ("kalman", "kalman_or_ema"):
                    diag = max(1.0, math.hypot(box[2] - box[0], box[3] - box[1]))
                    cur_cx, cur_cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
                    prev_cx, prev_cy = (prev_box[0] + prev_box[2]) / 2.0, (prev_box[1] + prev_box[3]) / 2.0
                    displacement = math.hypot(cur_cx - prev_cx, cur_cy - prev_cy)
                    motion_ratio = min(1.0, displacement / diag)
                    # When stationary/slow: lower alpha for maximum jitter reduction; when fast: increase alpha to eliminate lag
                    effective_alpha = max(alpha * 0.6, min(0.98, alpha + motion_ratio * (1.0 - alpha) * 0.8))
                else:
                    effective_alpha = alpha
                smoothed_box = [
                    float(effective_alpha * cur + (1.0 - effective_alpha) * prev)
                    for cur, prev in zip(box, prev_box)
                ]
        else:
            smoothed_box = list(box)

        state["smoothed_box"] = smoothed_box

        center = [(smoothed_box[0] + smoothed_box[2]) / 2, (smoothed_box[1] + smoothed_box[3]) / 2]
        state["trail"].append(center)
        del state["trail"][:-32]

        return smoothed_box

    def _global_id(self, scope: Hashable, local_id: int) -> int:
        key = (scope, local_id)
        if key not in self._global_ids:
            self._global_ids[key] = self._next_global_id
            self._next_global_id += 1
        return self._global_ids[key]

    def _scope_for(self, detection: dict) -> Hashable:
        if self.class_agnostic or self.enable_class_lock:
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
        self._reid_gallery.clear()

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
