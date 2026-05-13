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


# ============================================================
# 광역 뷰 — OSM 도로망 (osmnx) + 차단/정체 오버레이
# ============================================================
"""
공모전 사실적 임팩트를 위해 OSM(OpenStreetMap) 도로망 사용.
osmnx로 한국항공대 반경 5km 도로망 로드 → NetworkX 그래프 → A*/Dijkstra.

다운로드/캐싱 정책:
  1. 최초 1회 osmnx로 다운로드, GraphML로 디스크 저장 (data/road_kau_5km.graphml)
  2. 이후 실행은 ox.load_graphml()로 즉시 로드 (인터넷 불필요, 시연 안정성 ↑)
  3. 미니어처와는 분리 — 미니어처는 MINIATURE_ROAD_* 그대로 사용 (통제 환경)

차단/정체 오버레이 정책:
  - 시스템은 OSM 내부 노드 ID를 직접 다루지 않음 — 좌표만 다룸
  - 가상 재난 좌표 → ox.distance.nearest_edges()로 영향 엣지 자동 식별
  - 영향 엣지: 차단(blocked) → 그래프에서 제거, 정체(congested) → 가중치 ×N
"""

OSM_GRAPH_CONFIG = {
    "center": (37.6000, 126.8645),  # 한국항공대
    "dist_m": 5000,
    "network_type": "drive",
    "cache_path": "data/road_kau_5km.graphml",
    "congestion_weight_multiplier": 3.0,  # 정체 엣지 가중치 배수
}

# 가상 재난 좌표 → 도로 영향 매핑
# (재난 좌표 인근 radius_m 안의 엣지에 영향 적용)
DISASTER_ROAD_IMPACT = [
    {"disaster_id": "vd-1", "impact": "congested", "radius_m": 200},  # 화정동 화재
    {"disaster_id": "vd-2", "impact": "blocked",   "radius_m": 300},  # 진관동 범람
    {"disaster_id": "vd-3", "impact": "congested", "radius_m": 200},  # 삼송동 균열
    {"disaster_id": "vd-4", "impact": "blocked",   "radius_m": 400},  # 운정 산사태
]


# ============================================================
# 광역 뷰 — VWorld (한국 공간정보 오픈플랫폼)
# ============================================================
"""
한국 공모전 임팩트 + 정확한 행정구역 표현 위해 VWorld 통합.
회원가입 + API 키 필요 (국토부 운영, 무료): https://www.vworld.kr/

용도:
  1. 위성/하이브리드 타일 레이어 (Leaflet TileLayer)
     - 토글 버튼으로 OSM 일반맵 ↔ VWorld 위성 전환
     - 시연 시 위성 모드로 전환하면 "실제 도시 위에서 작동" 어필
  2. 행정구역 경계 GeoJSON (시/구/동 단위)
     - VIRTUAL_ZONE_RISKS의 위험도를 행정구역 폴리곤에 칠해 히트맵 생성
     - 원이 아니라 "진짜 화정동 경계"가 빨갛게 차오름 → 임팩트 ↑
     - 미리 받아서 GeoJSON 파일로 캐싱 (시연 시 인터넷 의존 제거)
  3. 건물 폴리곤 (선택, 데이터 무거움 — 시간 여유 있을 때만)
"""

VWORLD_CONFIG = {
    "api_key_env": "VWORLD_API_KEY",  # .env로 관리, git 커밋 금지
    "tiles": {
        "satellite": "https://api.vworld.kr/req/wmts/1.0.0/{key}/Satellite/{z}/{y}/{x}.jpeg",
        "hybrid":    "https://api.vworld.kr/req/wmts/1.0.0/{key}/Hybrid/{z}/{y}/{x}.png",
    },
    "boundary_geojson": "data/admin_boundary_kau_region.geojson",
    "boundary_target": ["고양시 덕양구", "고양시 일산동구", "은평구", "파주시 운정"],
}


# ============================================================
# 광역 뷰 — 공공 인프라 (대피소 / 소방서 / 병원)
# ============================================================
"""
구조 시나리오 강화를 위해 공공데이터포털 (data.go.kr) 데이터 통합.

추천 데이터셋:
  - 전국 대피소 표준데이터 (지진/민방위/임시): 행정안전부
  - 전국 119안전센터/소방서 표준데이터: 소방청
  - 전국 병원/응급실 위치: 보건복지부 (또는 건강보험심사평가원)

전처리 방식:
  1. 공공데이터포털에서 CSV/JSON 일괄 다운로드 (1회)
  2. 한국항공대 반경 10km로 필터링 (수십~수백 건 수준)
  3. JSON으로 변환·캐싱하여 git에 포함 (라이선스 확인 후)

대시보드 표시:
  - 대피소: 초록 깃발 아이콘
  - 소방서: 빨간 헬멧 아이콘
  - 병원: 파란 + 아이콘
  - 토글 가능 (체크박스로 레이어 on/off)

확장 시연 시나리오:
  - 재난 마커 클릭 시 → 가장 가까운 대피소/소방서/병원까지의 OSM 경로 동시 표시
  - "구조 우선순위" 패널에 "최근접 소방서까지 ETA" 같은 지표 추가
  - 진관동 범람으로 인근 도로 차단 시, 우회 소방서 자동 선택 → 시스템 똑똑함 어필
"""

PUBLIC_INFRA_DATA = {
    "shelter":   "data/public/shelters_kau_10km.json",
    "fire_dept": "data/public/fire_stations_kau_10km.json",
    "hospital":  "data/public/hospitals_kau_10km.json",
    "filter_radius_m": 10000,
    "filter_center": (37.6000, 126.8645),
}


# ============================================================
# UX / 인터랙션 명세
# ============================================================
"""
[광역 뷰 화면 구성]
  - 좌측: Leaflet 지도 (zoom 13)
      * 가상 드론: 회색 아이콘 (정적/순찰 패턴)
      * 실제 드론: 파란색 아이콘 + 펄스 애니메이션 (한국항공대 위에 표시, 라즈베리파이 실시간 좌표)
      * 재난 마커: 위험도에 따라 노랑→주황→빨강
      * 구역 폴리곤: 위험도 히트맵 (반투명 채움)
      * 진입 경로: KAU → 각 재난 지점, 차단 엣지 회피한 최단 경로 (점선)
  - 우측 패널:
      * 구조 우선순위 랭킹 (위험도 내림차순)
      * 선택된 재난의 분류 결과 + 추천 경로
  - "한국항공대" 구역 클릭 → 미니어처 뷰 전환
      * 트리거: VIRTUAL_ZONE_RISKS 항목 중 has_miniature=True인 항목 클릭
      * 전환 방식: 풀스크린 모달 (또는 라우트 변경)
      * "← 광역으로 돌아가기" 버튼 상단 고정

[미니어처 뷰 화면 구성]
  - 좌측: Leaflet 지도 (zoom 18)
      * 미니어처 건물: 사각형 폴리곤, collapse_rate 색상 매핑
      * 재난 마커: MINIATURE_DISASTERS (실시간 갱신)
      * 도로 그래프: 노드/엣지 표시, 차단/정체 엣지는 빨강/주황
      * 실제 드론: 파란색, 라즈베리파이 position 스트림으로 이동
      * 추천 진입로: KAU 외부에서 가장 위험한 재난 지점까지의 경로
  - 우측 패널:
      * 미니어처 종합 위험도 (구역별)
      * 최근 disaster_report 리스트 + 첨부 이미지 썸네일
      * 분류 결과 상세 (인명/붕괴/도로/화재)

[가상 드론 vs 실제 드론 시각 구분]
  - source 필드: "virtual" | "real"
  - 실제 드론은 카메라 모듈 + Edge AI에서 흘러오는 데이터, 광역/미니어처 양쪽에 표시
  - 가상 드론은 순찰 시뮬레이터에서 흘러오는 데이터, 광역에만 표시
"""


# ============================================================
# 미니어처 view_slot (카메라 시점 슬롯 9개)
# ============================================================
"""
실제 카메라(라즈베리파이)가 미니어처 위 어느 지점을 어떤 순서로 촬영할지가
운영 시점에 결정되므로, "detection bbox → 어느 건물/도로 incident냐"를
자동으로 결정할 수 없다. 대신 운영자가 카메라를 옮길 때마다 활성 슬롯을
대시보드 버튼으로 전환하고, 서버가 들어오는 detection을 그 슬롯으로 태깅한다.

[운영 모델]
  - 활성 슬롯: 서버가 단일 상태(active_view_slot)로 보유.
  - edge → server 페이로드는 변경 없음 (detection만 전송).
  - server가 수신 시 active_view_slot으로 태깅 + 누적 갱신.
  - 운영자가 대시보드 버튼 클릭 → POST /api/view-slot {slot_id}
    → 다음 detection부터 새 슬롯으로 태깅.
  - 리셋 버튼: POST /api/view-slot/reset → 누적 상태 초기화.

[누적 정책]
  - 같은 슬롯이 여러 번 활성화되면:
      · building.collapseProbability  = max(prev, new)
      · road_incident 세기/표시 여부  = max(prev, new) 또는 최신 갱신
      · section.riskLevel            = 누적된 ClassifyResult 종합 점수에서 매번 재계산
  - 시연 도중 한번 떠오른 위험 표시는 사라지지 않음 (보수적).

[슬롯 정의]
좌표는 docs/ui-mock/drone-risk-map.html 의 SVG viewBox(1200×675) 기준.
drone_marker 좌표는 미니어처 SVG 위 드론 아이콘 위치.
"""

MINIATURE_VIEW_SLOTS = [
    # ===== 건물 붕괴 6슬롯 =====
    {
        "slot_id": "b_topleft",
        "label": "건물 좌상 (붕괴)",
        "kind": "building",
        "target_buildings": ["topLeft"],
        "target_road_incident": None,
        "section_influence": ["A"],
        "drone_marker_svg": (390, 50),
    },
    {
        "slot_id": "b_topright",
        "label": "건물 우상 (붕괴)",
        "kind": "building",
        "target_buildings": ["topRight"],
        "target_road_incident": None,
        "section_influence": ["A"],
        "drone_marker_svg": (793, 50),
    },
    {
        "slot_id": "b_center",
        "label": "건물 중앙 (붕괴)",
        "kind": "building",
        "target_buildings": ["center"],
        "target_road_incident": None,
        "section_influence": ["B"],
        "drone_marker_svg": (510, 248),
    },
    {
        "slot_id": "b_rightmid",
        "label": "건물 중우 (붕괴)",
        "kind": "building",
        "target_buildings": ["rightMiddle"],
        "target_road_incident": None,
        "section_influence": ["C"],
        "drone_marker_svg": (962, 264),
    },
    {
        "slot_id": "b_bottomleft",
        "label": "건물 좌하 (붕괴)",
        "kind": "building",
        "target_buildings": ["bottomLeft"],
        "target_road_incident": None,
        "section_influence": ["D"],
        "drone_marker_svg": (293, 486),
    },
    {
        "slot_id": "b_bottomright",
        "label": "건물 우하 (붕괴)",
        "kind": "building",
        "target_buildings": ["bottomRight"],
        "target_road_incident": None,
        "section_influence": ["E"],
        "drone_marker_svg": (910, 486),
    },
    # ===== 도로 incident 3슬롯 =====
    {
        "slot_id": "r_tree",
        "label": "나무 쓰러짐",
        "kind": "road",
        "target_buildings": [],
        "target_road_incident": {
            "incident_id": "tree-1",
            "type": "fallenTree",
            "x": 1010,
            "y": 439,
        },
        "section_influence": ["C", "E"],
        "drone_marker_svg": (1010, 410),
    },
    {
        "slot_id": "r_traffic",
        "label": "도로 혼잡",
        "kind": "road",
        "target_buildings": [],
        "target_road_incident": {
            "incident_id": "traffic-1",
            "type": "traffic",
            "x": 850,
            "y": 208,
        },
        "section_influence": ["A"],
        "drone_marker_svg": (850, 175),
    },
    {
        "slot_id": "r_rubble",
        "label": "건물 잔해",
        "kind": "road",
        "target_buildings": [],
        "target_road_incident": {
            "incident_id": "rubble-1",
            "type": "rubble",
            "x": 548,
            "y": 538,
            "labelX": 592,
            "labelY": 518,
        },
        "section_influence": ["D", "E"],
        "drone_marker_svg": (548, 508),
    },
]

# YOLO class_name → slot.kind 매핑 (분배 로직)
# - building 슬롯: earthquake_building_* 의 max confidence
#                  → target_buildings[*].collapseProbability  (단일이면 그대로, 복수면 균등 분배)
# - road 슬롯: 슬롯의 target_road_incident.type에 따라
#       fallenTree → typhoon_tree_*    의 max confidence
#       traffic    → traffic_congestion_* 의 max confidence
#       rubble     → road_collapse_*, rock 의 max confidence
# 건물 슬롯에서 검출된 road_* 계열, 또는 그 반대는 무시 (해당 슬롯 책임 영역 아님).
SLOT_CLASS_RULES = {
    "building": {
        "primary": ["earthquake_building_level0", "earthquake_building_level2"],
        "scale": {
            "earthquake_building_level0": (20.0, 30.0),  # base, conf 가중치 → %
            "earthquake_building_level2": (60.0, 40.0),
        },
    },
    "fallenTree": {"primary": ["typhoon_tree_level0", "typhoon_tree_level2"]},
    "traffic":   {"primary": ["traffic_congestion_level0", "traffic_congestion_level2"]},
    "rubble":    {"primary": ["road_collapse_level0", "road_collapse_level2", "rock"]},
}

# section riskLevel 산출 (누적 상태에서 매번 재계산)
# - 각 섹션에 영향을 미친 슬롯들의 최대 collapseProbability,
#   road_incident 세기, fire_confidence 등을 종합한 score(0~100)를
#   임계값으로 1~4 bin 매핑.
SECTION_RISK_BINS = [
    (0, 25, 1),    # 낮음
    (25, 50, 2),   # 주의
    (50, 75, 3),   # 높음
    (75, 101, 4),  # 매우 높음
]


# ============================================================
# 좌표 매핑 정책
# ============================================================
"""
미니어처는 실물 크기 약 1~2m × 1~2m로 추정. 이를 GPS 좌표 공간에 매핑할 때:
  - 미니어처 중심 = (37.6000, 126.8645)
  - 미니어처 1m ↔ GPS 약 ?m (스케일 결정 필요)
  - 현재 MINIATURE_ZONES의 좌표 분포: 위/아래 0.0008° (~80m), 좌/우 0.0016° (~140m)
    → 즉 미니어처를 "실제 80m × 140m 구역"으로 시뮬레이션하는 셈
    → 미니어처 실물 1m가 GPS 80m에 대응 (스케일 1:80)

권장:
  - 미니어처 내부 좌표는 로컬 (m 단위)로 다루고, 서버 송신 시 GPS로 변환
  - 변환 함수: local_to_gps(x_m, y_m) -> (lat, lon)
    * 변환식: lat = CENTER_LAT + (y_m * SCALE) / 111_000
              lon = CENTER_LON + (x_m * SCALE) / (111_000 * cos(CENTER_LAT))
    * SCALE = 80 (1m → 80m로 확대)

이렇게 하면 미니어처에서 RPi가 송신하는 GPS는 그대로 광역/미니어처 양쪽 지도에 찍힘.
"""


# ============================================================
# 결정 사항 / TBD
# ============================================================
"""
[결정됨]
- 광역 도로: OSM (osmnx) + 차단/정체 오버레이 (사실적 임팩트 우선)
- 행정구역 경계: VWorld GeoJSON 사용
- 공공 인프라: 대피소/소방서/병원 통합 (공모전 어필 + 시나리오 풍부화)
- 미니어처 카메라 시점: view_slot 9개 (건물 6 + 도로 3) — MINIATURE_VIEW_SLOTS 참조
    · 활성 슬롯 1개, 운영자가 대시보드 버튼으로 수동 전환
    · 누적 정책: max(prev, new), 시연 도중 표시 사라지지 않음
    · 리셋 버튼 별도
- 미니어처 SVG 디자인: docs/ui-mock/drone-risk-map.html (레퍼런스 보존)
    · server/dashboard/ 의 React 컴포넌트로 흡수 예정 (MiniatureRiskMap.tsx)

[TBD]
- 가상 드론 움직임: 정적 좌표 vs 순찰 시뮬레이터
        → 시연 임팩트 위해 시뮬레이터 권장. 트랙 A에서 dashboard용 별도 mock 송신 스크립트.
- 가상 재난 발생 타이밍: 데모 시작 시 모두 active vs 시간차로 등장 (스토리텔링)
- 한국항공대 risk_score 산출: 정적 45 vs 미니어처 결과 집계
        → 집계 권장 ("미니어처 위험도가 광역 지도에 그대로 반영" 일관성)
- 드릴다운 UX: 풀스크린 모달 vs 라우트 분리 vs 사이드바 토글
- 가상 드론↔가상 재난 1:1 매핑 명시 (현재 좌표는 일치하나 명시적 link 없음)
- 위성 타일 토글 기본값: 데모 시작 시 일반맵 vs 위성 — 발표 흐름 따라 결정

[선행 작업 필요]
- VWorld 회원가입 + API 키 발급 (1일 정도 승인 대기 가능)
- 공공데이터포털 데이터셋 다운로드 + 한국항공대 반경 10km 필터링 스크립트
- osmnx 다운로드 1회 실행 → GraphML 캐싱 (data/ 디렉토리 생성)
- 라이선스 확인: VWorld 타일/공공데이터 출처 표기 의무 — 대시보드 푸터에 명시
"""
