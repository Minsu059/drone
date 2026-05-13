from __future__ import annotations

from typing import Sequence

from edge.classifier.base import ClassifyResult, DisasterType, RoadStatus


def _to_confidence(value: object) -> float:
    try:
        conf = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, conf))


def _choose_disaster_type(scores: dict[DisasterType, float]) -> DisasterType:
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_type, top_score = ordered[0]
    if top_score < 0.35:
        return "none"
    return top_type


def map_detections_to_classify_result(
    rows: Sequence[dict],
    *,
    inference_ms: int,
) -> ClassifyResult:
    person_count = 0
    collapse_rate = 0.0
    road_blocked_score = 0.0
    road_congested_score = 0.0
    fire_confidence = 0.0

    disaster_scores: dict[DisasterType, float] = {
        "earthquake": 0.0,
        "flood": 0.0,
        "fire": 0.0,
        "landslide": 0.0,
        "none": 0.0,
    }

    for row in rows:
        class_name = str(row.get("class_name", "")).lower()
        conf = _to_confidence(row.get("confidence", 0.0))

        if "person" in class_name:
            person_count += 1

        if "earthquake_building_level2" in class_name:
            collapse_rate = max(collapse_rate, 60.0 + (40.0 * conf))
            disaster_scores["earthquake"] = max(disaster_scores["earthquake"], conf)
        elif "earthquake_building_level0" in class_name:
            collapse_rate = max(collapse_rate, 20.0 + (30.0 * conf))
            disaster_scores["earthquake"] = max(disaster_scores["earthquake"], conf * 0.7)

        if "road_collapse_level2" in class_name:
            collapse_rate = max(collapse_rate, 50.0 + (50.0 * conf))
            road_blocked_score = max(road_blocked_score, conf)
            disaster_scores["earthquake"] = max(disaster_scores["earthquake"], conf * 0.9)
        elif "road_collapse_level0" in class_name:
            collapse_rate = max(collapse_rate, 20.0 + (40.0 * conf))
            road_congested_score = max(road_congested_score, conf)

        if "traffic_congestion_level2" in class_name:
            road_congested_score = max(road_congested_score, min(1.0, conf + 0.15))
        elif "traffic_congestion_level0" in class_name:
            road_congested_score = max(road_congested_score, conf)

        # "rock" is treated as a rockfall/landslide indicator for downstream schema compatibility.
        if class_name == "rock" or class_name.startswith("rock_") or "rockfall" in class_name:
            collapse_rate = max(collapse_rate, 25.0 + (55.0 * conf))
            road_blocked_score = max(road_blocked_score, conf * 0.8)
            disaster_scores["landslide"] = max(disaster_scores["landslide"], conf)

        if "fire" in class_name:
            fire_confidence = max(fire_confidence, conf)
            disaster_scores["fire"] = max(disaster_scores["fire"], conf)
        if "flood" in class_name:
            disaster_scores["flood"] = max(disaster_scores["flood"], conf)
        if "landslide" in class_name or "typhoon_tree" in class_name:
            disaster_scores["landslide"] = max(disaster_scores["landslide"], conf)

    road_status: RoadStatus
    if road_blocked_score >= 0.55:
        road_status = "blocked"
    elif road_congested_score >= 0.35:
        road_status = "congested"
    else:
        road_status = "normal"

    fire_detected = fire_confidence >= 0.4
    if fire_detected:
        disaster_scores["fire"] = max(disaster_scores["fire"], fire_confidence)

    disaster_type = _choose_disaster_type(disaster_scores)
    if disaster_type == "none" and fire_detected:
        disaster_type = "fire"

    return {
        "person_count": person_count,
        "collapse_rate": round(collapse_rate, 1),
        "road_status": road_status,
        "fire_detected": fire_detected,
        "fire_confidence": round(fire_confidence, 3),
        "disaster_type": disaster_type,
        "inference_ms": max(0, int(inference_ms)),
    }
