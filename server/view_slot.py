"""
미니어처 view_slot 누적 상태 관리.

운영 모델:
  - 활성 슬롯(active_slot_id) 1개를 모듈 레벨 상태로 보유.
  - edge가 보낸 detection rows → 활성 슬롯에 분배 → 누적 갱신.
  - 운영자가 대시보드 버튼으로 슬롯 전환 (set_active_slot).
  - 리셋 버튼으로 누적 상태 초기화 (reset).
  - 누적 정책: max(prev, new). 시연 도중 표시 사라지지 않음.

상세 사양은 docs/dashboard.md 의 MINIATURE_VIEW_SLOTS 섹션 참조.
"""
from __future__ import annotations

import threading
from typing import Optional


# ============================================================
# 슬롯 정의 (docs/dashboard.md 와 동기화)
# 좌표는 docs/ui-mock/drone-risk-map.html SVG viewBox(1200×675) 기준
# ============================================================

VIEW_SLOTS: list[dict] = [
    # 건물 6슬롯
    {"slot_id": "b_topleft",     "label": "건물 좌상 (붕괴)", "kind": "building",
     "target_buildings": ["topLeft"],    "target_road_incident": None,
     "section_influence": ["A"], "drone_marker_svg": [390, 50]},
    {"slot_id": "b_topright",    "label": "건물 우상 (붕괴)", "kind": "building",
     "target_buildings": ["topRight"],   "target_road_incident": None,
     "section_influence": ["A"], "drone_marker_svg": [793, 50]},
    {"slot_id": "b_center",      "label": "건물 중앙 (붕괴)", "kind": "building",
     "target_buildings": ["center"],     "target_road_incident": None,
     "section_influence": ["B"], "drone_marker_svg": [510, 248]},
    {"slot_id": "b_rightmid",    "label": "건물 중우 (붕괴)", "kind": "building",
     "target_buildings": ["rightMiddle"],"target_road_incident": None,
     "section_influence": ["C"], "drone_marker_svg": [962, 264]},
    {"slot_id": "b_bottomleft",  "label": "건물 좌하 (붕괴)", "kind": "building",
     "target_buildings": ["bottomLeft"], "target_road_incident": None,
     "section_influence": ["D"], "drone_marker_svg": [293, 486]},
    {"slot_id": "b_bottomright", "label": "건물 우하 (붕괴)", "kind": "building",
     "target_buildings": ["bottomRight"],"target_road_incident": None,
     "section_influence": ["E"], "drone_marker_svg": [910, 486]},
    # 도로 3슬롯
    {"slot_id": "r_tree",    "label": "나무 쓰러짐", "kind": "road",
     "target_buildings": [],
     "target_road_incident": {"id": "tree-1",    "type": "fallenTree", "x": 1010, "y": 439},
     "section_influence": ["C", "E"], "drone_marker_svg": [1010, 410]},
    {"slot_id": "r_traffic", "label": "도로 혼잡", "kind": "road",
     "target_buildings": [],
     "target_road_incident": {"id": "traffic-1", "type": "traffic",    "x": 850,  "y": 208},
     "section_influence": ["A"], "drone_marker_svg": [850, 175]},
    {"slot_id": "r_rubble",  "label": "건물 잔해", "kind": "road",
     "target_buildings": [],
     "target_road_incident": {"id": "rubble-1",  "type": "rubble",     "x": 548,  "y": 538,
                              "labelX": 592, "labelY": 518},
     "section_influence": ["D", "E"], "drone_marker_svg": [548, 508]},
]

SLOTS_BY_ID: dict[str, dict] = {s["slot_id"]: s for s in VIEW_SLOTS}

# 클래스 → 위험 점수 매핑
# (class_name, conf) → collapse_probability(%) (건물 슬롯용)
BUILDING_CLASS_SCALE = {
    "earthquake_building_level0": (20.0, 30.0),  # base + conf*weight
    "earthquake_building_level2": (60.0, 40.0),
}

# road 슬롯의 incident type 별 해당 클래스 후보
ROAD_INCIDENT_CLASSES = {
    "fallenTree": {"typhoon_tree_level0": 1.0, "typhoon_tree_level2": 1.0},
    "traffic":    {"traffic_congestion_level0": 1.0, "traffic_congestion_level2": 1.0},
    "rubble":     {"road_collapse_level0": 1.0, "road_collapse_level2": 1.0, "rock": 1.0},
}

# section riskLevel 산출 임계값 (점수 0~100 → 1~4)
SECTION_RISK_BINS = [(0, 25, 1), (25, 50, 2), (50, 75, 3), (75, 101, 4)]
INCIDENT_INTENSITY_THRESHOLD = 0.4  # 이 이상이어야 incident 노출
ROAD_TO_SECTION_SCORE = 80.0  # intensity 1.0이면 섹션 점수에 80점 기여


# ============================================================
# 누적 상태 (모듈 레벨)
# ============================================================

_lock = threading.Lock()

_DEFAULT_ACTIVE = VIEW_SLOTS[0]["slot_id"]

_state: dict = {
    "active_slot_id": _DEFAULT_ACTIVE,
    # building_id → collapseProbability (max 누적)
    "buildings": {},
    # incident_id → { id, type, x, y, labelX?, labelY?, intensity }
    "road_incidents": {},
    # 현재 활성 슬롯의 drone_marker (SVG 좌표). 슬롯 전환 시 즉시 이동.
    "drone_marker": list(SLOTS_BY_ID[_DEFAULT_ACTIVE]["drone_marker_svg"]),
}


def _clamp01(v: float) -> float:
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


def _bin_section_score(score: float) -> int:
    for lo, hi, level in SECTION_RISK_BINS:
        if lo <= score < hi:
            return level
    return 1


def _building_collapse_from_detection(class_name: str, conf: float) -> Optional[float]:
    """earthquake_building_* detection → collapseProbability(%) 반환. 다른 클래스면 None."""
    scale = BUILDING_CLASS_SCALE.get(class_name)
    if scale is None:
        return None
    base, weight = scale
    return base + weight * _clamp01(conf)


def _road_intensity_from_detection(incident_type: str, class_name: str, conf: float) -> Optional[float]:
    """road 슬롯의 incident_type 매칭 클래스면 intensity(0~1) 반환. 아니면 None."""
    candidates = ROAD_INCIDENT_CLASSES.get(incident_type, {})
    if class_name not in candidates:
        return None
    # level2 계열은 같은 conf라도 더 무겁게
    if class_name.endswith("_level2"):
        return _clamp01(conf + 0.15)
    return _clamp01(conf)


def apply_detections(rows: list[dict]) -> dict:
    """활성 슬롯 기준으로 detection rows를 누적 상태에 반영. 적용 결과 요약 반환."""
    with _lock:
        slot = SLOTS_BY_ID[_state["active_slot_id"]]
        applied = {"slot_id": slot["slot_id"], "buildings_updated": [], "incident_updated": None}

        if slot["kind"] == "building":
            best = 0.0
            for row in rows:
                cn = str(row.get("class_name", ""))
                conf = float(row.get("confidence", 0.0))
                prob = _building_collapse_from_detection(cn, conf)
                if prob is not None and prob > best:
                    best = prob
            if best > 0.0:
                for bld_id in slot["target_buildings"]:
                    prev = float(_state["buildings"].get(bld_id, 0.0))
                    new_val = max(prev, best)
                    _state["buildings"][bld_id] = round(new_val, 1)
                    applied["buildings_updated"].append({"id": bld_id, "probability": round(new_val, 1)})

        elif slot["kind"] == "road":
            inc = slot["target_road_incident"]
            best_intensity = 0.0
            for row in rows:
                cn = str(row.get("class_name", ""))
                conf = float(row.get("confidence", 0.0))
                intensity = _road_intensity_from_detection(inc["type"], cn, conf)
                if intensity is not None and intensity > best_intensity:
                    best_intensity = intensity
            if best_intensity >= INCIDENT_INTENSITY_THRESHOLD:
                prev_entry = _state["road_incidents"].get(inc["id"], {})
                prev_intensity = float(prev_entry.get("intensity", 0.0))
                new_intensity = max(prev_intensity, best_intensity)
                entry = {**inc, "intensity": round(new_intensity, 3)}
                _state["road_incidents"][inc["id"]] = entry
                applied["incident_updated"] = entry

        return applied


def set_active_slot(slot_id: str) -> dict:
    if slot_id not in SLOTS_BY_ID:
        raise ValueError(f"unknown slot_id: {slot_id}")
    with _lock:
        _state["active_slot_id"] = slot_id
        _state["drone_marker"] = list(SLOTS_BY_ID[slot_id]["drone_marker_svg"])
    return get_map_state()


def reset() -> dict:
    with _lock:
        _state["active_slot_id"] = _DEFAULT_ACTIVE
        _state["buildings"] = {}
        _state["road_incidents"] = {}
        _state["drone_marker"] = list(SLOTS_BY_ID[_DEFAULT_ACTIVE]["drone_marker_svg"])
    return get_map_state()


def _compute_sections() -> dict[str, dict]:
    """누적 상태에서 섹션별 riskLevel 산출."""
    # 섹션별 score 누적 (0~100)
    scores: dict[str, float] = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0, "E": 0.0}

    # 건물 → 섹션 매핑은 슬롯의 section_influence로 역추적
    building_to_sections: dict[str, list[str]] = {}
    for s in VIEW_SLOTS:
        for b in s["target_buildings"]:
            building_to_sections.setdefault(b, []).extend(s["section_influence"])

    for bld_id, prob in _state["buildings"].items():
        for sec in building_to_sections.get(bld_id, []):
            if prob > scores[sec]:
                scores[sec] = prob

    # road incidents → 영향 섹션에 score 기여
    incident_to_sections: dict[str, list[str]] = {}
    for s in VIEW_SLOTS:
        if s["kind"] != "road":
            continue
        inc = s["target_road_incident"]
        incident_to_sections[inc["id"]] = s["section_influence"]

    for inc_id, entry in _state["road_incidents"].items():
        intensity = float(entry.get("intensity", 0.0))
        contribution = intensity * ROAD_TO_SECTION_SCORE
        for sec in incident_to_sections.get(inc_id, []):
            if contribution > scores[sec]:
                scores[sec] = contribution

    return {sec: {"riskLevel": _bin_section_score(score), "score": round(score, 1)}
            for sec, score in scores.items()}


def get_map_state() -> dict:
    """프론트가 받아서 SVG에 그릴 누적 상태."""
    with _lock:
        return {
            "active_slot_id": _state["active_slot_id"],
            "sections": _compute_sections(),
            "buildings": {bid: {"collapseProbability": prob}
                          for bid, prob in _state["buildings"].items()},
            "road_incidents": list(_state["road_incidents"].values()),
            "drone": {"x": _state["drone_marker"][0], "y": _state["drone_marker"][1]},
        }


def list_slots() -> list[dict]:
    """대시보드 버튼 패널이 받을 슬롯 메타 목록."""
    return [{"slot_id": s["slot_id"], "label": s["label"], "kind": s["kind"]}
            for s in VIEW_SLOTS]
