"""
VWorld 데이터 API로 KAU 인근 행정구역 경계 GeoJSON 다운로드

선행:
  1. https://www.vworld.kr/ 가입 + 인증키 발급 (무료, 인증키 종류: '서버형')
  2. 환경변수 VWORLD_API_KEY 설정
       export VWORLD_API_KEY="발급받은_인증키"

VWorld 데이터 API 레퍼런스: https://www.vworld.kr/dev/v4dv_2ddataguide2_s001.do
  - 시도 경계: LT_C_ADSIDO_INFO
  - 시군구 경계: LT_C_ADSIGG_INFO
  - 읍면동 경계: LT_C_ADEMD_INFO   ← 본 프로젝트는 이걸 사용
"""
import json
import os
import sys
from pathlib import Path

import requests

API = "https://api.vworld.kr/req/data"

CENTER = (37.6000, 126.8645)  # 한국항공대 (lat, lon)
RADIUS_M = 6000               # 반경(미터). 광역 뷰가 5km라 살짝 여유.

# 받을 데이터: 읍면동 단위 경계
DATA_TYPE = "LT_C_ADEMD_INFO"

OUT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "admin_boundary_kau_region.geojson"


def fetch_boundary(api_key: str) -> dict:
    """VWorld 데이터 API로 KAU 반경 영역의 읍면동 경계 GeoJSON 반환."""
    # 좌표 순서 주의: VWorld geomFilter는 POINT(lon lat)
    params = {
        "service": "data",
        "request": "GetFeature",
        "data": DATA_TYPE,
        "key": api_key,
        "format": "json",
        "geometry": "true",
        "attribute": "true",
        "crs": "EPSG:4326",
        "geomFilter": f"POINT({CENTER[1]} {CENTER[0]})",
        "buffer": str(RADIUS_M),
        "size": "1000",
    }
    resp = requests.get(API, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if "response" not in payload or payload["response"].get("status") != "OK":
        raise RuntimeError(f"VWorld API error: {json.dumps(payload, ensure_ascii=False)[:500]}")
    return payload


def to_geojson(payload: dict) -> dict:
    """VWorld 응답을 표준 GeoJSON FeatureCollection으로 변환."""
    features = payload["response"]["result"]["featureCollection"]["features"]
    return {"type": "FeatureCollection", "features": features}


def main() -> int:
    api_key = os.environ.get("VWORLD_API_KEY")
    if not api_key:
        print("ERROR: 환경변수 VWORLD_API_KEY 가 설정되지 않았습니다.", file=sys.stderr)
        print("  export VWORLD_API_KEY=\"발급받은_인증키\"", file=sys.stderr)
        return 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"VWorld 다운로드 시작: data={DATA_TYPE}, center={CENTER}, radius={RADIUS_M}m")
    payload = fetch_boundary(api_key)
    geojson = to_geojson(payload)
    print(f"받은 행정구역 수: {len(geojson['features'])}")

    OUT_PATH.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"저장됨: {OUT_PATH} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
