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

# 광역 드론은 정적 데이터가 아니다 — 라즈베리파이가 송신한 실시간 위치를
# /api/dashboard/disasters 의 drones 필드가 노출한다 (drone_position DB 최신값).

# 광역 재난은 더 이상 정적 데이터가 아니다 — 라즈베리파이가 /api/drone-data 로
# 실시간 송신한 disaster_report DB 레코드를 /api/dashboard/disasters 가 노출한다.
# (시연 송신 스크립트: edge/scenario_sender.py)

# 광역 도로 통제 포인트 — 재난 2차 피해(도로 붕괴/잔해)로 통행 차단.
# routing.py 의 경로 추론이 이 지점을 회피해 우회로를 재탐색한다.
# 좌표는 각 재난의 최단경로 상에 위치 (통제 시 우회 발생).
ROAD_BLOCKAGES = [
    {"id": "blk-1", "lat": 37.615007, "lon": 126.835256, "radius_m": 80,
     "status": "blocked", "type": "debris",        "description": "상가 화재 잔해 도로 점거"},
    {"id": "blk-2", "lat": 37.634492, "lon": 126.917149, "radius_m": 80,
     "status": "blocked", "type": "road_collapse", "description": "하천 범람 도로 유실"},
    {"id": "blk-3", "lat": 37.643002, "lon": 126.894030, "radius_m": 80,
     "status": "blocked", "type": "debris",        "description": "건물 균열 외벽 낙하물"},
    {"id": "blk-4", "lat": 37.608466, "lon": 126.844854, "radius_m": 80,
     "status": "blocked", "type": "road_collapse", "description": "가스누출 도로 통제"},
    {"id": "blk-5", "lat": 37.586360, "lon": 126.888055, "radius_m": 80,
     "status": "blocked", "type": "road_collapse", "description": "침수 구간 도로 통제"},
    {"id": "blk-6", "lat": 37.616978, "lon": 126.824465, "radius_m": 80,
     "status": "blocked", "type": "debris",        "description": "건물 붕괴 잔해 매몰"},
    {"id": "blk-7", "lat": 37.600806, "lon": 126.907351, "radius_m": 80,
     "status": "blocked", "type": "debris",        "description": "소방 차량 도로 점거"},
    {"id": "blk-8", "lat": 37.610808, "lon": 126.821217, "radius_m": 80,
     "status": "blocked", "type": "road_collapse", "description": "산사태 토사 도로 매몰"},
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
