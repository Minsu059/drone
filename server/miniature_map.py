"""
미니어처 + 광역 맵 정의

=== 2단계 대시보드 구조 ===

[광역 뷰] 한국항공대학교 중심, 반경 수 km
  - 가상 드론 다수 배치 (인근 지역 순찰)
  - 가상 재난 시나리오 (고양시, 덕양구, 은평구 등)
  - 구역별 위험도 히트맵 + 구조 우선순위
  - 최적 진입 경로 표시
  → 한국항공대 구역 클릭 시 미니어처 뷰로 전환

[미니어처 뷰] 한국항공대 캠퍼스 내 시연 장소
  - 실제 드론(RPi + 카메라)이 미니어처 촬영
  - Edge AI 분류 결과 실시간 마킹
  - 미니어처 내 구역별 위험도 + 진입로 계산

좌표 기준:
  한국항공대: 37.6000, 126.8645
  0.001도 ≈ 약 100m
"""

# ============================================================
# 광역 뷰 — 한국항공대 중심, 가상 데이터
# ============================================================

WIDE_VIEW = {
    "center": (37.6000, 126.8645),
    "zoom": 13,  # Leaflet 줌 레벨
}

# 광역 가상 드론 배치
VIRTUAL_DRONES = [
    {"drone_id": "drone-v1", "area": "덕양구 화정동", "lat": 37.6150, "lon": 126.8320},
    {"drone_id": "drone-v2", "area": "덕양구 행신동", "lat": 37.6120, "lon": 126.8510},
    {"drone_id": "drone-v3", "area": "은평구 진관동", "lat": 37.6350, "lon": 126.9150},
    {"drone_id": "drone-v4", "area": "고양시 삼송동", "lat": 37.6420, "lon": 126.8900},
    {"drone_id": "drone-v5", "area": "파주시 운정", "lat": 37.7130, "lon": 126.7650},
]

# 광역 가상 재난 시나리오
VIRTUAL_DISASTERS = [
    {
        "id": "vd-1",
        "lat": 37.6150, "lon": 126.8330,
        "disaster_type": "fire",
        "description": "화정동 상가 화재",
        "person_count": 8,
        "collapse_rate": 30.0,
        "fire_detected": True,
        "fire_confidence": 0.92,
        "road_status": "congested",
    },
    {
        "id": "vd-2",
        "lat": 37.6350, "lon": 126.9160,
        "disaster_type": "flood",
        "description": "진관동 하천 범람",
        "person_count": 12,
        "collapse_rate": 15.0,
        "fire_detected": False,
        "fire_confidence": 0.0,
        "road_status": "blocked",
    },
    {
        "id": "vd-3",
        "lat": 37.6430, "lon": 126.8910,
        "disaster_type": "earthquake",
        "description": "삼송동 건물 균열",
        "person_count": 5,
        "collapse_rate": 65.0,
        "fire_detected": False,
        "fire_confidence": 0.0,
        "road_status": "congested",
    },
    {
        "id": "vd-4",
        "lat": 37.7140, "lon": 126.7660,
        "disaster_type": "landslide",
        "description": "운정 산사태",
        "person_count": 3,
        "collapse_rate": 80.0,
        "fire_detected": False,
        "fire_confidence": 0.0,
        "road_status": "blocked",
    },
]

# 광역 구역별 위험도 (가상, 0~100)
VIRTUAL_ZONE_RISKS = [
    {"name": "화정동", "center": (37.6150, 126.8330), "risk_score": 72},
    {"name": "행신동", "center": (37.6120, 126.8510), "risk_score": 25},
    {"name": "진관동", "center": (37.6350, 126.9160), "risk_score": 58},
    {"name": "삼송동", "center": (37.6430, 126.8910), "risk_score": 81},
    {"name": "운정",   "center": (37.7140, 126.7660), "risk_score": 90},
    {"name": "한국항공대", "center": (37.6000, 126.8645), "risk_score": 45, "has_miniature": True},
]


# ============================================================
# 미니어처 뷰 — 한국항공대 캠퍼스 내, 실제 드론 데이터
# ============================================================

MINIATURE_VIEW = {
    "center": (37.6000, 126.8645),
    "zoom": 18,  # 확대
}

# 미니어처 구역 (A~E)
MINIATURE_ZONES = {
    "A": {
        "name": "A구역 (상단)",
        "center": (37.6008, 126.8645),
        "radius_m": 30,
        "description": "건물 2동, 주요 도로 인접",
    },
    "B": {
        "name": "B구역 (중앙)",
        "center": (37.6000, 126.8645),
        "radius_m": 30,
        "description": "대형 건물 1동, 교차로, 위쪽 도로 포화",
    },
    "C": {
        "name": "C구역 (우측)",
        "center": (37.6000, 126.8660),
        "radius_m": 25,
        "description": "건물 1동",
    },
    "D": {
        "name": "D구역 (좌하단)",
        "center": (37.5992, 126.8632),
        "radius_m": 25,
        "description": "건물 1동",
    },
    "E": {
        "name": "E구역 (우하단)",
        "center": (37.5992, 126.8658),
        "radius_m": 25,
        "description": "건물 1동, 화재 + 포장도로 파괴",
    },
}

# 미니어처 건물
# collapse_rate: 0~100 (시연 전 유동적 조정)
MINIATURE_BUILDINGS = [
    {"zone": "A", "lat": 37.6010, "lon": 126.8638, "name": "A-건물1", "collapse_rate": 0},
    {"zone": "A", "lat": 37.6010, "lon": 126.8652, "name": "A-건물2", "collapse_rate": 0},
    {"zone": "B", "lat": 37.6000, "lon": 126.8645, "name": "B-건물1 (대형)", "collapse_rate": 0},
    {"zone": "C", "lat": 37.6000, "lon": 126.8660, "name": "C-건물1", "collapse_rate": 0},
    {"zone": "D", "lat": 37.5992, "lon": 126.8632, "name": "D-건물1", "collapse_rate": 0},
    {"zone": "E", "lat": 37.5992, "lon": 126.8658, "name": "E-건물1", "collapse_rate": 0},
]

# 미니어처 재난 시나리오
MINIATURE_DISASTERS = {
    "road_saturated": {
        "zone": "B 위쪽 도로",
        "lat": 37.6004,
        "lon": 126.8643,
        "type": "road_saturated",
        "description": "도로 포화 — 차량 진입 불가",
    },
    "road_damage": {
        "zone": "D-E 사이",
        "lat": 37.5992,
        "lon": 126.8645,
        "type": "road_damage",
        "description": "도로 파괴 구간 (통행불가)",
    },
    "fire": {
        "zone": "E",
        "lat": 37.5992,
        "lon": 126.8662,
        "type": "fire",
        "description": "화재 + 포장도로 파괴",
    },
}

# 미니어처 도로 그래프
MINIATURE_ROAD_NODES = {
    "N1": (37.6012, 126.8628),  # 좌상단
    "N2": (37.6012, 126.8645),  # 상단 중앙
    "N3": (37.6012, 126.8665),  # 우상단
    "N4": (37.6004, 126.8628),  # B위-좌
    "N5": (37.6004, 126.8645),  # B위-중 (포화)
    "N6": (37.6004, 126.8665),  # B위-우
    "N7": (37.5996, 126.8628),  # 중앙-좌
    "N8": (37.5996, 126.8645),  # 중앙
    "N9": (37.5996, 126.8665),  # 중앙-우
    "N10": (37.5988, 126.8628), # 하단-좌
    "N11": (37.5988, 126.8645), # 하단-중 (파괴)
    "N12": (37.5988, 126.8665), # 하단-우
}

MINIATURE_ROAD_EDGES = [
    # 수평 도로
    ("N1", "N2"), ("N2", "N3"),
    ("N4", "N5"), ("N5", "N6"),
    ("N7", "N8"), ("N8", "N9"),
    ("N10", "N11"), ("N11", "N12"),
    # 수직 도로
    ("N1", "N4"), ("N4", "N7"), ("N7", "N10"),
    ("N2", "N5"), ("N5", "N8"), ("N8", "N11"),
    ("N3", "N6"), ("N6", "N9"), ("N9", "N12"),
]

MINIATURE_BLOCKED_ROADS = [
    ("N4", "N5"),    # B 위쪽 도로 포화 (진입불가)
    ("N10", "N11"),  # D-E 사이 도로 파괴
]

MINIATURE_CONGESTED_ROADS = [
    ("N8", "N9"),    # 화재 인근 정체
    ("N9", "N12"),   # E구역 포장도로 파괴 영향
]
