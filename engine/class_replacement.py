"""
Class Replacement & Hierarchical Cascade Relabeler Module:
- Replaces generic detection class labels (e.g., 'vehicle', 'person') with fine-grained
  specialized classes from secondary classifiers, attribute lookups, or mapping dictionaries.
- Preserves track_id, spatial coordinates, and bounding box trajectory history.
- Retains original class in `detection.attributes['original_class']` for full auditability.
"""

from typing import Any, Dict, List, Optional, Tuple


def relabel_detections(
    detections: List[Dict[str, Any]],
    config: Dict[str, Any],
    secondary_results: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Applies hierarchical relabeling to incoming detections.

    Returns:
        (relabeled_detections, relabel_events)
    """
    source_class = str(config.get("sourceClass", "*")).strip().lower()
    replacement_mode = str(config.get("replacementMode", "direct_mapping")).strip().lower()
    fallback_action = str(config.get("fallbackAction", "keep_original")).strip().lower()
    min_confidence = float(config.get("minClassifierConfidence", 0.50))
    preserve_original = bool(config.get("preserveOriginalClass", True))

    # Parse static mapping table: e.g. "vehicle:forklift, person:worker, car:pickup" or JSON-like
    raw_mapping = config.get("mappingTable")
    mapping_dict: Dict[str, str] = {}
    if isinstance(raw_mapping, dict):
        mapping_dict = {str(k).strip().lower(): str(v).strip() for k, v in raw_mapping.items()}
    elif isinstance(raw_mapping, str):
        for pair in raw_mapping.split(","):
            if ":" in pair:
                k, v = pair.split(":", 1)
                mapping_dict[k.strip().lower()] = v.strip()

    attribute_key = str(config.get("attributeKey", "sub_class")).strip() or "sub_class"

    relabeled: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []

    for det in detections:
        det_copy = dict(det)
        current_cls = str(det_copy.get("class", "")).strip().lower()

        # Check if this class is targeted
        is_target = (source_class == "*" or current_cls == source_class or
                     current_cls in [c.strip().lower() for c in source_class.split(",")])

        if not is_target:
            relabeled.append(det_copy)
            continue

        target_new_class: Optional[str] = None
        new_conf: Optional[float] = None

        if replacement_mode == "direct_mapping":
            # Lookup in static mapping table
            if current_cls in mapping_dict:
                target_new_class = mapping_dict[current_cls]
            elif "*" in mapping_dict:
                target_new_class = mapping_dict["*"]

        elif replacement_mode == "attribute_lookup":
            # Lookup from existing attributes dictionary (e.g. from VLM, OCR, or secondary node)
            attrs = det_copy.get("attributes", {})
            if isinstance(attrs, dict) and attribute_key in attrs:
                val = str(attrs[attribute_key]).strip()
                if val and val.lower() != "none":
                    target_new_class = val
                    new_conf = float(attrs.get(f"{attribute_key}_conf", det_copy.get("confidence", 1.0)))

        elif replacement_mode == "secondary_results" and secondary_results:
            # Match by track_id or closest bounding box
            my_track_id = det_copy.get("track_id")
            match = None
            if my_track_id is not None:
                match = next((s for s in secondary_results if s.get("track_id") == my_track_id), None)
            if not match and len(secondary_results) == 1:
                match = secondary_results[0]
            if match:
                sec_cls = str(match.get("class", "")).strip()
                sec_conf = float(match.get("confidence", 1.0))
                if sec_cls and sec_conf >= min_confidence:
                    target_new_class = sec_cls
                    new_conf = sec_conf

        # Apply relabeling or fallback
        if target_new_class:
            if preserve_original:
                attrs = dict(det_copy.get("attributes") or {})
                attrs["original_class"] = det_copy.get("class")
                attrs["relabel_mode"] = replacement_mode
                det_copy["attributes"] = attrs

            old_label = det_copy.get("class")
            det_copy["class"] = target_new_class
            if new_conf is not None:
                det_copy["confidence"] = round(new_conf, 3)

            relabeled.append(det_copy)
            events.append({
                "event_type": "CLASS_RELABELED",
                "type": "CLASS_RELABELED",
                "old_class": old_label,
                "new_class": target_new_class,
                "track_id": det_copy.get("track_id"),
                "message": f"Objek #{det_copy.get('track_id', 'ID')} di-relabel: '{old_label}' -> '{target_new_class}'",
            })
        else:
            # Fallback action
            if fallback_action == "drop":
                continue
            elif fallback_action == "set_unknown":
                if preserve_original:
                    attrs = dict(det_copy.get("attributes") or {})
                    attrs["original_class"] = det_copy.get("class")
                    det_copy["attributes"] = attrs
                det_copy["class"] = "unknown"
                relabeled.append(det_copy)
            else:  # "keep_original"
                relabeled.append(det_copy)

    return relabeled, events
