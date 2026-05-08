"""
한국항공대 반경 5km OSM 도로망 다운로드 → GraphML 캐싱

최초 1회만 실행 (인터넷 필요). 이후 dashboard는 GraphML을 ox.load_graphml()로 즉시 로드.
"""
import os
import sys
import time
from pathlib import Path

import osmnx as ox

CENTER = (37.6000, 126.8645)  # 한국항공대
DIST_M = 5000
NETWORK_TYPE = "drive"

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "road_kau_5km.graphml"


def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if OUT_PATH.exists():
        size_kb = OUT_PATH.stat().st_size / 1024
        print(f"이미 존재함: {OUT_PATH} ({size_kb:.1f} KB)")
        print("재다운로드를 원하면 파일을 지우고 다시 실행.")
        return 0

    print(f"OSM 다운로드 시작: center={CENTER}, dist={DIST_M}m, type={NETWORK_TYPE}")
    t0 = time.time()
    G = ox.graph_from_point(CENTER, dist=DIST_M, network_type=NETWORK_TYPE, simplify=True)
    elapsed = time.time() - t0

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    print(f"다운로드 완료: nodes={n_nodes}, edges={n_edges}, elapsed={elapsed:.1f}s")

    ox.save_graphml(G, OUT_PATH)
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"저장됨: {OUT_PATH} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
