"""
소방청 119안전센터 현황 CSV → KAU 인근만 추려 VWorld 지오코딩 → 좌표 포함 CSV

소방청_119안전센터 현황 데이터에는 위경도가 없어 반경 필터를 못 한다.
주소(도로명)를 VWorld 지오코더 API로 좌표 변환하여 보강한다.

선행:
  - VWorld 인증키 (지오코더 API 권한 필요).
    환경변수 VWORLD_API_KEY, 또는 프로젝트 루트 .env 에 VWORLD_API_KEY=... 한 줄.
  - data/소방청_119안전센터*.csv (공공데이터포털 다운로드 원본)

출력: data/raw/fire_stations.csv (원본 컬럼 + 위도/경도)
이어서: python filter_public_data.py fire_stations  → 10km 정밀 필터
"""
import csv
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data" / "raw" / "fire_stations.csv"

GEOCODE_API = "https://api.vworld.kr/req/address"

# KAU 인근 시군구 — 지오코딩 호출 수 절감용 1차 광역 필터.
# 정밀 10km 필터는 이후 filter_public_data.py 가 좌표로 수행.
NEAR_KEYWORDS = ["고양시", "은평구", "파주시"]

ADDR_COL = "주소"
NAME_COL = "119안전센터명"


def load_api_key() -> str | None:
    """환경변수 우선, 없으면 루트 .env 의 VWORLD_API_KEY."""
    key = os.environ.get("VWORLD_API_KEY")
    if key:
        return key
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line.startswith("VWORLD_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def find_source() -> Path | None:
    matches = sorted((ROOT / "data").glob("소방청_119안전센터*.csv"))
    return matches[0] if matches else None


def clean_address(addr: str) -> str:
    """괄호 안 법정동 표기 등 제거 → 지오코더 매칭률 향상."""
    return re.sub(r"\s*\(.*?\)", "", addr).strip()


def geocode(address: str, api_key: str, addr_type: str) -> tuple[float, float] | None:
    """주소 → (lat, lon). addr_type: 'road'(도로명) | 'parcel'(지번). 실패 시 None."""
    params = {
        "service": "address",
        "request": "getcoord",
        "version": "2.0",
        "crs": "epsg:4326",
        "address": address,
        "type": addr_type,
        "format": "json",
        "key": api_key,
    }
    resp = requests.get(GEOCODE_API, params=params, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("response", {}).get("status") != "OK":
        return None
    pt = payload["response"]["result"]["point"]
    return float(pt["y"]), float(pt["x"])


def main() -> int:
    api_key = load_api_key()
    if not api_key:
        print("ERROR: VWORLD_API_KEY 없음 (환경변수 또는 .env 에 설정)", file=sys.stderr)
        return 1
    src = find_source()
    if src is None:
        print("ERROR: data/소방청_119안전센터*.csv 를 찾을 수 없음", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(open(src, encoding="cp949")))
    near = [r for r in rows if any(k in r[ADDR_COL] for k in NEAR_KEYWORDS)]
    print(f"입력 {src.name}: 전체 {len(rows)}건 → KAU 인근 후보 {len(near)}건, 지오코딩 시작")

    out_rows = []
    failed = []
    for r in near:
        addr = clean_address(r[ADDR_COL])
        coord = geocode(addr, api_key, "road") or geocode(addr, api_key, "parcel")
        if coord is None:
            failed.append((r[NAME_COL], addr))
            continue
        lat, lon = coord
        out_rows.append({**r, "위도": lat, "경도": lon})
        print(f"  OK  {r[NAME_COL]:22s} {lat:.6f}, {lon:.6f}")
        time.sleep(0.1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) + ["위도", "경도"]
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    print(f"\n저장: {OUT} ({len(out_rows)}건)")
    if failed:
        print(f"지오코딩 실패 {len(failed)}건 — 수동 확인 필요:")
        for name, addr in failed:
            print(f"  {name} | {addr}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
