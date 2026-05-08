"""
미니어처 + 광역 맵 정의

=== 2단계 대시보드 구조 ===

[광역 뷰] 한국항공대학교 중심, 반경 ~5km
  - 가상 드론 다수 배치 (인근 지역 순찰)
  - 가상 재난 시나리오 (덕양구 화정동·행신동·삼송동·향동·화전동·행주산성·능곡, 은평구 진관동)
  - 재난별 영향 반경 + 종합 위험도 계산 (frontend utils/risk.ts와 동일 가중치)
  → 한국항공대 (MINIATURE_ENTRY_POINT) 클릭 시 미니어처 뷰로 전환

[미니어처 뷰] 한국항공대 캠퍼스 내 시연 장소
  - 실제 드론(RPi + 카메라)이 미니어처 촬영
  - Edge AI 분류 결과 실시간 마킹
  - 미니어처 내 구역별 위험도 + 진입로 계산

좌표 기준:
  한국항공대: 37.6000, 126.8645
  0.001도 ≈ 약 100m

데이터 정책:
  이 파일은 광역/미니어처 정적 데이터의 단일 진실 소스(SSOT).
  /api/dashboard/wide, /api/dashboard/miniature 라우트가 그대로 노출.
  Frontend(src/data/mockData.ts)는 type 정의만 두고 fetch로 받음.
"""

# ============================================================
# 광역 뷰 — 한국항공대 중심, 가상 데이터
# ============================================================

WIDE_VIEW = {
    "center": (37.6000, 126.8645),
    "zoom": 13,
}

# 광역 가상 드론 배치 (반경 5km 안)
VIRTUAL_DRONES = [
    {"drone_id": "drone-v1", "area": "덕양구 화정동", "lat": 37.6150, "lon": 126.8320},
    {"drone_id": "drone-v2", "area": "덕양구 행신동", "lat": 37.6120, "lon": 126.8510},
    {"drone_id": "drone-v3", "area": "은평구 진관동", "lat": 37.6350, "lon": 126.9150},
    {"drone_id": "drone-v4", "area": "고양시 삼송동", "lat": 37.6420, "lon": 126.8900},
]

# 광역 가상 재난 시나리오 (8건, 모두 KAU 반경 ~5km 안)
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
        "impact_radius_m": 150,
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
        "impact_radius_m": 300,
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
        "impact_radius_m": 200,
    },
    {
        "id": "vd-4",
        "lat": 37.6080, "lon": 126.8390,
        "disaster_type": "fire",
        "description": "행신동 가스누출 화재",
        "person_count": 6,
        "collapse_rate": 20.0,
        "fire_detected": True,
        "fire_confidence": 0.85,
        "road_status": "normal",
        "impact_radius_m": 130,
    },
    {
        "id": "vd-5",
        "lat": 37.5870, "lon": 126.8820,
        "disaster_type": "flood",
        "description": "화전동 도로 침수",
        "person_count": 4,
        "collapse_rate": 5.0,
        "fire_detected": False,
        "fire_confidence": 0.0,
        "road_status": "blocked",
        "impact_radius_m": 250,
    },
    {
        "id": "vd-6",
        "lat": 37.6125, "lon": 126.8175,
        "disaster_type": "earthquake",
        "description": "능곡역 인근 건물 붕괴",
        "person_count": 9,
        "collapse_rate": 75.0,
        "fire_detected": False,
        "fire_confidence": 0.0,
        "road_status": "congested",
        "impact_radius_m": 180,
    },
    {
        "id": "vd-7",
        "lat": 37.6180, "lon": 126.8910,
        "disaster_type": "fire",
        "description": "향동 빌라 화재",
        "person_count": 3,
        "collapse_rate": 40.0,
        "fire_detected": True,
        "fire_confidence": 0.78,
        "road_status": "normal",
        "impact_radius_m": 120,
    },
    {
        "id": "vd-8",
        "lat": 37.6033, "lon": 126.8260,
        "disaster_type": "landslide",
        "description": "행주산성 산사태",
        "person_count": 2,
        "collapse_rate": 70.0,
        "fire_detected": False,
        "fire_confidence": 0.0,
        "road_status": "blocked",
        "impact_radius_m": 220,
    },
]

# 미니어처 드릴다운 진입점 (한국항공대만)
# 광역 위험도 히트맵 용도가 아니라 "여기 클릭 → 미니어처 모달" 트리거
MINIATURE_ENTRY_POINT = {
    "name": "한국항공대",
    "center": (37.6000, 126.8645),
    "risk_score": 45,
    "has_miniature": True,
}


# ============================================================
# 미니어처 뷰 — 한국항공대 캠퍼스 내, 실제 드론 데이터
# ============================================================

MINIATURE_VIEW = {
    "center": (37.6000, 126.8645),
    "zoom": 18,
}

# 미니어처 구역 (A~E)
MINIATURE_ZONES = [
    {"key": "A", "name": "A구역 (상단)",   "center": (37.6008, 126.8645), "radius_m": 30, "description": "건물 2동, 주요 도로 인접"},
    {"key": "B", "name": "B구역 (중앙)",   "center": (37.6000, 126.8645), "radius_m": 30, "description": "대형 건물 1동, 교차로, 위쪽 도로 포화"},
    {"key": "C", "name": "C구역 (우측)",   "center": (37.6000, 126.8660), "radius_m": 25, "description": "건물 1동"},
    {"key": "D", "name": "D구역 (좌하단)", "center": (37.5992, 126.8632), "radius_m": 25, "description": "건물 1동"},
    {"key": "E", "name": "E구역 (우하단)", "center": (37.5992, 126.8658), "radius_m": 25, "description": "건물 1동, 화재 + 포장도로 파괴"},
]

# 미니어처 건물 (collapse_rate: 0~100, 시연 전 유동적 조정)
MINIATURE_BUILDINGS = [
    {"zone": "A", "lat": 37.6010, "lon": 126.8638, "name": "A-건물1",        "collapse_rate": 0},
    {"zone": "A", "lat": 37.6010, "lon": 126.8652, "name": "A-건물2",        "collapse_rate": 0},
    {"zone": "B", "lat": 37.6000, "lon": 126.8645, "name": "B-건물1 (대형)", "collapse_rate": 0},
    {"zone": "C", "lat": 37.6000, "lon": 126.8660, "name": "C-건물1",        "collapse_rate": 0},
    {"zone": "D", "lat": 37.5992, "lon": 126.8632, "name": "D-건물1",        "collapse_rate": 0},
    {"zone": "E", "lat": 37.5992, "lon": 126.8658, "name": "E-건물1",        "collapse_rate": 0},
]

# 미니어처 재난 시나리오
MINIATURE_DISASTERS = [
    {"key": "road_saturated", "zone": "B 위쪽 도로", "lat": 37.6004, "lon": 126.8643, "type": "road_saturated", "description": "도로 포화 — 차량 진입 불가"},
    {"key": "road_damage",    "zone": "D-E 사이",    "lat": 37.5992, "lon": 126.8645, "type": "road_damage",    "description": "도로 파괴 구간 (통행불가)"},
    {"key": "fire",           "zone": "E",           "lat": 37.5992, "lon": 126.8662, "type": "fire",           "description": "화재 + 포장도로 파괴"},
]

# 미니어처 도로 그래프
MINIATURE_ROAD_NODES = {
    "N1":  (37.6012, 126.8628),  # 좌상단
    "N2":  (37.6012, 126.8645),  # 상단 중앙
    "N3":  (37.6012, 126.8665),  # 우상단
    "N4":  (37.6004, 126.8628),  # B위-좌
    "N5":  (37.6004, 126.8645),  # B위-중 (포화)
    "N6":  (37.6004, 126.8665),  # B위-우
    "N7":  (37.5996, 126.8628),  # 중앙-좌
    "N8":  (37.5996, 126.8645),  # 중앙
    "N9":  (37.5996, 126.8665),  # 중앙-우
    "N10": (37.5988, 126.8628),  # 하단-좌
    "N11": (37.5988, 126.8645),  # 하단-중 (파괴)
    "N12": (37.5988, 126.8665),  # 하단-우
}

MINIATURE_ROAD_EDGES = [
    # 수평
    ("N1", "N2"), ("N2", "N3"),
    ("N4", "N5"), ("N5", "N6"),
    ("N7", "N8"), ("N8", "N9"),
    ("N10", "N11"), ("N11", "N12"),
    # 수직
    ("N1", "N4"), ("N4", "N7"), ("N7", "N10"),
    ("N2", "N5"), ("N5", "N8"), ("N8", "N11"),
    ("N3", "N6"), ("N6", "N9"), ("N9", "N12"),
]

MINIATURE_BLOCKED_ROADS = [
    ("N4", "N5"),    # B 위쪽 도로 포화
    ("N10", "N11"),  # D-E 사이 도로 파괴
]

MINIATURE_CONGESTED_ROADS = [
    ("N8", "N9"),    # 화재 인근 정체
    ("N9", "N12"),   # E구역 포장도로 파괴 영향
]
