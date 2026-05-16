"""미니어처 view_slot 누적 상태 관리.

운영 모델:
  - 활성 슬롯(active_slot_id) 1개를 모듈 레벨 상태로 보유.
  - edge가 보낸 detection rows → 활성 슬롯에 분배 → 누적 갱신.
  - 운영자가 대시보드 버튼으로 슬롯 전환 (set_active_slot).
  - 리셋 버튼으로 누적 상태 초기화 (reset).
  - 누적 정책: max(prev, new). 시연 도중 표시 사라지지 않음.

슬롯 구성 (12개): 건물 9 (A,B,C,D,F,G,H,I,J — E는 공원) + 도로 incident 3.
좌표는 미니어처 SVG viewBox(1200×920) 기준 — 디오라마 명세와 동기화.
"""
from __future__ import annotations

import threading
from typing import Optional


# ============================================================
# 슬롯 정의 (미니어처 디오라마 명세와 동기화, viewBox 1200×920)
# ============================================================

VIEW_SLOTS: list[dict] = [
    # 건물 9슬롯 — drone_marker 는 건물 중심(centerX, centerY)
    {"slot_id": "b_a", "label": "A동 대형 오피스", "kind": "building",
     "target_buildings": ["A"], "target_road_incident": None, "drone_marker_svg": [200, 90]},
    {"slot_id": "b_b", "label": "B동 중층 아파트", "kind": "building",
     "target_buildings": ["B"], "target_road_incident": None, "drone_marker_svg": [620, 90]},
    {"slot_id": "b_c", "label": "C동 상업 시설", "kind": "building",
     "target_buildings": ["C"], "target_road_incident": None, "drone_marker_svg": [1020, 90]},
    {"slot_id": "b_d", "label": "D동 주거", "kind": "building",
     "target_buildings": ["D"], "target_road_incident": None, "drone_marker_svg": [100, 440]},
    {"slot_id": "b_f", "label": "F동 소형 오피스", "kind": "building",
     "target_buildings": ["F"], "target_road_incident": None, "drone_marker_svg": [840, 410]},
    {"slot_id": "b_g", "label": "G동 소형 아파트", "kind": "building",
     "target_buildings": ["G"], "target_road_incident": None, "drone_marker_svg": [1120, 410]},
    {"slot_id": "b_h", "label": "H동 대단지 아파트", "kind": "building",
     "target_buildings": ["H"], "target_road_incident": None, "drone_marker_svg": [240, 810]},
    {"slot_id": "b_i", "label": "I동 고층 타워", "kind": "building",
     "target_buildings": ["I"], "target_road_incident": None, "drone_marker_svg": [730, 780]},
    {"slot_id": "b_j", "label": "J동 고층 아파트", "kind": "building",
     "target_buildings": ["J"], "target_road_incident": None, "drone_marker_svg": [1080, 780]},
    # 도로 3슬롯
    {"slot_id": "r_traffic", "label": "메인 간선 혼잡", "kind": "road",
     "target_buildings": [],
     "target_road_incident": {"id": "traffic-1", "type": "traffic", "x": 600, "y": 250},
     "drone_marker_svg": [600, 250]},
    {"slot_id": "r_tree", "label": "척추도로 나무 쓰러짐", "kind": "road",
     "target_buildings": [],
     "target_road_incident": {"id": "tree-1", "type": "fallenTree", "x": 300, "y": 470},
     "drone_marker_svg": [300, 470]},
    {"slot_id": "r_rubble", "label": "교차로 건물 잔해", "kind": "road",
     "target_buildings": [],
     "target_road_incident": {"id": "rubble-1", "type": "rubble", "x": 300, "y": 250,
                              "labelX": 344, "labelY": 230},
     "drone_marker_svg": [300, 250]},
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

INCIDENT_INTENSITY_THRESHOLD = 0.4  # 이 이상이어야 incident 노출


# ============================================================
# 누적 상태 (모듈 레벨)
# ============================================================

_lock = threading.Lock()

_DEFAULT_ACTIVE = VIEW_SLOTS[0]["slot_id"]

# ============================================================
# 시연용 시드 — 실제 edge detection 을 기다리지 않고 "데이터가 들어온 셈 치고"
# 미니어처 맵을 붕괴 상황으로 미리 채운다. detection 이 실제로 들어오면
# apply_detections 가 max 누적으로 이 값들을 그대로 이어받아 갱신한다.
# ============================================================

# 건물 붕괴도 — 1~5 등급 (image.png 표기 기준, 5가 가장 심각).
# edge detection 은 collapseProbability(0~100) 로 누적되므로, 시드 시
# 등급 → 해당 구간 대표 확률로 변환한다 (프론트가 다시 등급으로 환산).
_DEMO_BUILDING_LEVELS: dict[str, int] = {
    "F": 5,  # 소형 오피스 — 전면 붕괴
    "A": 4,  # 대형 오피스
    "I": 4,  # 고층 타워
    "C": 3,  # 상업 시설
    "H": 3,  # 대단지 아파트
    "B": 2,  # 중층 아파트
    "J": 2,  # 고층 아파트
    "D": 1,  # 주거
    "G": 1,  # 소형 아파트 — 경미
}

# 도로 incident intensity(0~1) — 시연 시드에서는 도로 incident 미사용 (비움).
# 실제 edge detection 이 들어오면 apply_detections 가 그대로 채운다.
_DEMO_ROAD_INTENSITY: dict[str, float] = {}


def _level_to_probability(level: int) -> float:
    """붕괴도 등급(1~5) → 구간 중앙값 collapseProbability(%).
    프론트 riskLevel() 의 20% 구간과 round-trip 된다 (1→10 … 5→90)."""
    return level * 20.0 - 10.0


def _seed_buildings() -> dict:
    return {bid: _level_to_probability(lv) for bid, lv in _DEMO_BUILDING_LEVELS.items()}


def _seed_road_incidents() -> dict:
    """슬롯 정의의 target_road_incident + _DEMO_ROAD_INTENSITY 로 incident 엔트리 구성."""
    result: dict = {}
    for slot in VIEW_SLOTS:
        inc = slot.get("target_road_incident")
        if inc and inc["id"] in _DEMO_ROAD_INTENSITY:
            result[inc["id"]] = {**inc, "intensity": _DEMO_ROAD_INTENSITY[inc["id"]]}
    return result


_state: dict = {
    "active_slot_id": _DEFAULT_ACTIVE,
    # building_id → collapseProbability (max 누적)
    "buildings": _seed_buildings(),
    # incident_id → { id, type, x, y, labelX?, labelY?, intensity }
    "road_incidents": _seed_road_incidents(),
    # 현재 활성 슬롯의 drone_marker (SVG 좌표). 슬롯 전환 시 즉시 이동.
    "drone_marker": list(SLOTS_BY_ID[_DEFAULT_ACTIVE]["drone_marker_svg"]),
}


def _clamp01(v: float) -> float:
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


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
    """시연 붕괴 시드 상태로 되돌린다 (빈 상태가 아님 — 시드가 곧 기준 상태)."""
    with _lock:
        _state["active_slot_id"] = _DEFAULT_ACTIVE
        _state["buildings"] = _seed_buildings()
        _state["road_incidents"] = _seed_road_incidents()
        _state["drone_marker"] = list(SLOTS_BY_ID[_DEFAULT_ACTIVE]["drone_marker_svg"])
    return get_map_state()


def get_map_state() -> dict:
    """프론트가 받아서 SVG에 그릴 누적 상태."""
    with _lock:
        return {
            "active_slot_id": _state["active_slot_id"],
            "buildings": {bid: {"collapseProbability": prob}
                          for bid, prob in _state["buildings"].items()},
            "road_incidents": list(_state["road_incidents"].values()),
            "drone": {"x": _state["drone_marker"][0], "y": _state["drone_marker"][1]},
        }


def list_slots() -> list[dict]:
    """대시보드 버튼 패널이 받을 슬롯 메타 목록."""
    return [{"slot_id": s["slot_id"], "label": s["label"], "kind": s["kind"]}
            for s in VIEW_SLOTS]
