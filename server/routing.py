"""광역 경로 추론 엔진.

OSM 도로망(GraphML) + 재난 차단/정체 가중치 → A* 최단경로.
각 재난마다 최근접 119안전센터에서 출발하는 골든타임 경로를 계산한다.

도로 영향 소스:
  - 재난 차단/정체: VIRTUAL_DISASTERS 의 road_status + impact_radius_m 로 파생.
    blocked → 가중치 ×BLOCKED_MULT (그래프 연결성은 유지하여 도달 보장),
    congested → ×CONGESTED_MULT.
  - ITS 실시간 교통(정체): 키 발급 후 _edge_multiplier 에 레이어로 추가 예정.
"""
from __future__ import annotations

import math
from pathlib import Path

import networkx as nx
import osmnx as ox

_GRAPHML = Path(__file__).resolve().parent.parent / "data" / "road_kau_5km.graphml"

# 도로 영향 가중치 배수
CONGESTED_MULT = 3.0    # 정체 — 우회 유도
BLOCKED_MULT = 100.0    # 차단 — 사실상 통행 불가 (연결성은 유지해 도달 보장)

# 소방차 평균 주행 속도 (km/h) — ETA 산정용
FIRE_TRUCK_KMH = 45.0

_graph = None


def _load_graph():
    """GraphML 1회 로드 후 모듈 캐시."""
    global _graph
    if _graph is None:
        _graph = ox.load_graphml(_GRAPHML)
    return _graph


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _edge_multiplier(mid_lat: float, mid_lon: float, disasters: list[dict]) -> float:
    """엣지 중점이 재난 영향권 안이면 가중치 배수. 가장 강한 영향을 적용."""
    mult = 1.0
    for d in disasters:
        status = d.get("road_status", "normal")
        if status == "normal":
            continue
        radius = float(d.get("impact_radius_m", 0))
        dist = _haversine_m(mid_lat, mid_lon, d["lat"], d["lon"])
        if dist <= radius:
            m = BLOCKED_MULT if status == "blocked" else CONGESTED_MULT
            mult = max(mult, m)
    return mult


def _apply_weights(G, disasters: list[dict]) -> None:
    """각 엣지에 travel 가중치(길이 × 재난 영향배수)를 부여."""
    for u, v, _k, data in G.edges(keys=True, data=True):
        length = float(data.get("length", 0.0))
        mid_lat = (G.nodes[u]["y"] + G.nodes[v]["y"]) / 2
        mid_lon = (G.nodes[u]["x"] + G.nodes[v]["x"]) / 2
        data["travel"] = length * _edge_multiplier(mid_lat, mid_lon, disasters)


def _make_heuristic(G):
    """A* 휴리스틱 — 직선거리(m). travel ≥ length ≥ 직선거리 이므로 admissible."""
    def h(node, target):
        return _haversine_m(
            G.nodes[node]["y"], G.nodes[node]["x"],
            G.nodes[target]["y"], G.nodes[target]["x"],
        )
    return h


def _path_length_m(G, path: list) -> float:
    """경로의 순수 도로 길이(m) — 영향배수 제외."""
    total = 0.0
    for u, v in zip(path[:-1], path[1:]):
        edges = G.get_edge_data(u, v)
        total += min(float(e.get("length", 0.0)) for e in edges.values())
    return total


def compute_routes(disasters: list[dict], fire_stations: list[dict]) -> list[dict]:
    """각 재난별 최근접 119안전센터 → 재난 지점 골든타임 경로."""
    if not disasters or not fire_stations:
        return []

    G = _load_graph()
    _apply_weights(G, disasters)
    heuristic = _make_heuristic(G)

    fs_nodes = ox.distance.nearest_nodes(
        G,
        [fs["lon"] for fs in fire_stations],
        [fs["lat"] for fs in fire_stations],
    )

    routes: list[dict] = []
    for d in disasters:
        d_node = ox.distance.nearest_nodes(G, d["lon"], d["lat"])
        best_path = None
        best_cost = None
        best_fs = None
        for fs, fs_node in zip(fire_stations, fs_nodes):
            try:
                path = nx.astar_path(G, fs_node, d_node, heuristic=heuristic, weight="travel")
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
            cost = nx.path_weight(G, path, weight="travel")
            if best_cost is None or cost < best_cost:
                best_cost, best_path, best_fs = cost, path, fs

        if best_path is None:
            routes.append({
                "disaster_id": d["id"],
                "fire_station": None,
                "path": [],
                "distance_m": 0.0,
                "eta_min": 0.0,
            })
            continue

        dist_m = _path_length_m(G, best_path)
        routes.append({
            "disaster_id": d["id"],
            "fire_station": best_fs["name"],
            "fire_station_lat": best_fs["lat"],
            "fire_station_lon": best_fs["lon"],
            "path": [[G.nodes[n]["y"], G.nodes[n]["x"]] for n in best_path],
            "distance_m": round(dist_m, 1),
            "eta_min": round(dist_m / 1000 / FIRE_TRUCK_KMH * 60, 1),
        })
    return routes
