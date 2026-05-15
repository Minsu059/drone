"""시연용 시나리오 송신기.

재난 8건마다 드론 1대를 배정(drone-01~08). 모든 드론이 한국항공대에서 **동시 출발**해
같은 속도로 각자의 재난 현장으로 이동한다. 현장까지 거리가 제각각이므로 도착 시간이
달라, 재난이 관제맵에 하나씩 순차적으로 추가된다.

  - 매 tick: 미도착 드론 전체의 position 송신 → 대시보드에서 드론들이 동시 이동.
  - 현장 도착: 해당 드론이 disaster_report(메타 + 이미지) 송신 → 재난 마커 등장.

사용 예:
  python edge/scenario_sender.py --server-url http://192.168.0.10:8000/api/drone-data

이동 속도/주기는 --speed(도/tick), --tick(초)로 조정.
"""
from __future__ import annotations

import argparse
import base64
import math
import sys
import time
from pathlib import Path

import requests

KAU = (37.6000, 126.8645)  # 한국항공대 — 모든 드론의 출발 기지
ALT = 50.0
IMG_DIR = Path(__file__).resolve().parent / "scenario_images"

# 재난 시퀀스 — 각 재난에 드론 1대 배정 (인덱스 순으로 drone-01~08).
SCENARIO: list[dict] = [
    {"lat": 37.6150, "lon": 126.8330, "disaster_type": "fire",
     "description": "화정동 상가 화재", "person_count": 8, "collapse_rate": 30.0,
     "fire_detected": True, "fire_confidence": 0.92, "road_status": "congested",
     "impact_radius_m": 150.0, "image": "vd-1.jpg"},
    {"lat": 37.6350, "lon": 126.9160, "disaster_type": "flood",
     "description": "진관동 하천 범람", "person_count": 12, "collapse_rate": 15.0,
     "fire_detected": False, "fire_confidence": 0.0, "road_status": "blocked",
     "impact_radius_m": 300.0, "image": "vd-2.jpg"},
    {"lat": 37.6430, "lon": 126.8910, "disaster_type": "earthquake",
     "description": "삼송동 건물 균열", "person_count": 5, "collapse_rate": 65.0,
     "fire_detected": False, "fire_confidence": 0.0, "road_status": "congested",
     "impact_radius_m": 200.0, "image": "vd-3.jpg"},
    {"lat": 37.6080, "lon": 126.8390, "disaster_type": "fire",
     "description": "행신동 가스누출 화재", "person_count": 6, "collapse_rate": 20.0,
     "fire_detected": True, "fire_confidence": 0.85, "road_status": "normal",
     "impact_radius_m": 130.0, "image": "vd-4.png"},
    {"lat": 37.5870, "lon": 126.8820, "disaster_type": "flood",
     "description": "화전동 도로 침수", "person_count": 4, "collapse_rate": 5.0,
     "fire_detected": False, "fire_confidence": 0.0, "road_status": "blocked",
     "impact_radius_m": 250.0, "image": "vd-5.jpg"},
    {"lat": 37.6125, "lon": 126.8175, "disaster_type": "earthquake",
     "description": "능곡역 인근 건물 붕괴", "person_count": 9, "collapse_rate": 75.0,
     "fire_detected": False, "fire_confidence": 0.0, "road_status": "congested",
     "impact_radius_m": 180.0, "image": "vd-6.jpeg"},
    {"lat": 37.6180, "lon": 126.8910, "disaster_type": "fire",
     "description": "향동 빌라 화재", "person_count": 3, "collapse_rate": 40.0,
     "fire_detected": True, "fire_confidence": 0.78, "road_status": "normal",
     "impact_radius_m": 120.0, "image": "vd-7.jpg"},
    {"lat": 37.6033, "lon": 126.8260, "disaster_type": "landslide",
     "description": "행주산성 산사태", "person_count": 2, "collapse_rate": 70.0,
     "fire_detected": False, "fire_confidence": 0.0, "road_status": "blocked",
     "impact_radius_m": 220.0, "image": "vd-8.jpg"},
]

ANALYSIS_KEYS = (
    "person_count", "collapse_rate", "road_status", "fire_detected",
    "fire_confidence", "disaster_type", "description", "impact_radius_m",
)


def _post(url: str, payload: dict) -> str:
    try:
        r = requests.post(url, json=payload, timeout=10)
        return str(r.status_code)
    except requests.RequestException as e:
        return f"ERR {type(e).__name__}"


def _load_image_b64(name: str | None) -> str | None:
    if not name:
        return None
    path = IMG_DIR / name
    if not path.exists():
        print(f"  (경고: 이미지 없음 {path})", file=sys.stderr)
        return None
    return base64.b64encode(path.read_bytes()).decode()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="시연 시나리오 송신기 (다중 드론 동시 출발)")
    p.add_argument("--server-url", required=True,
                   help="예: http://192.168.0.10:8000/api/drone-data")
    p.add_argument("--speed", type=float, default=0.0009,
                   help="tick당 이동 거리(위경도 도 단위). 작을수록 느림")
    p.add_argument("--tick", type=float, default=0.6,
                   help="position 송신 간격(초)")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    drones = [
        {
            "drone_id": f"drone-{i:02d}",
            "sc": sc,
            "pos": [KAU[0], KAU[1]],
            "target": (sc["lat"], sc["lon"]),
            "arrived": False,
            "reported": False,
        }
        for i, sc in enumerate(SCENARIO, 1)
    ]
    print(f"드론 {len(drones)}대 — 한국항공대 동시 출발 (speed={args.speed}/tick)")

    while not all(d["reported"] for d in drones):
        for d in drones:
            if not d["arrived"]:
                dlat = d["target"][0] - d["pos"][0]
                dlon = d["target"][1] - d["pos"][1]
                dist = math.hypot(dlat, dlon)
                if dist <= args.speed:
                    d["pos"] = [d["target"][0], d["target"][1]]
                    d["arrived"] = True
                else:
                    d["pos"][0] += dlat / dist * args.speed
                    d["pos"][1] += dlon / dist * args.speed
                _post(args.server_url, {
                    "drone_id": d["drone_id"], "type": "position",
                    "lat": d["pos"][0], "lon": d["pos"][1],
                    "alt": ALT, "timestamp": time.time(),
                })
            elif not d["reported"]:
                sc = d["sc"]
                _post(args.server_url, {
                    "drone_id": d["drone_id"], "type": "disaster_report",
                    "lat": sc["lat"], "lon": sc["lon"], "alt": ALT,
                    "timestamp": time.time(),
                    "analysis": {k: sc[k] for k in ANALYSIS_KEYS},
                    "image_base64": _load_image_b64(sc["image"]),
                })
                d["reported"] = True
                print(f"  [도착] {d['drone_id']} → 재난 보고: {sc['description']}")

        moving = sum(1 for d in drones if not d["arrived"])
        print(f"  ... 이동 중 {moving}대 / 도착 {len(drones) - moving}대")
        time.sleep(args.tick)

    print("시나리오 완료 — 재난 8건 모두 관제맵에 등장.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
