"""
공공데이터포털에서 다운받은 표준데이터(CSV)를 KAU 반경 N km로 필터 → JSON 저장

선행:
  1. data.go.kr 에서 아래 표준데이터셋 CSV로 다운로드 후 data/raw/ 에 저장:
       - shelters.csv     (전국 대피소 표준데이터)
       - fire_stations.csv (119안전센터/소방서 표준데이터)
       - hospitals.csv    (전국 병원/응급실 위치)

사용:
  python filter_public_data.py shelters
  python filter_public_data.py fire_stations
  python filter_public_data.py hospitals

주의:
  컬럼명은 데이터셋마다 다름. CONFIG의 lat_col/lon_col/name_col은 받은 CSV
  헤더를 보고 조정해야 함.
"""
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "public"

CENTER = (37.6000, 126.8645)
RADIUS_M = 10000

# 데이터셋별 설정. 컬럼명은 실제 받은 CSV 헤더에 맞춰 수정 필요.
CONFIG = {
    "shelters": {
        "input": "shelters.csv",
        "output": "shelters_kau_10km.json",
        "lat_col": "위도(EPSG4326)",
        "lon_col": "경도(EPSG4326)",
        "name_col": "시설명",
        "extra_cols": ["도로명전체주소", "최대수용인원", "시설구분", "운영상태"],
    },
    "fire_stations": {
        # geocode_fire_stations.py 가 위도/경도 컬럼을 채워 생성한 CSV
        "input": "fire_stations.csv",
        "output": "fire_stations_kau_10km.json",
        "lat_col": "위도",
        "lon_col": "경도",
        "name_col": "119안전센터명",
        "extra_cols": ["소방서명", "주소", "전화번호"],
    },
    "hospitals": {
        "input": "hospitals.csv",
        "output": "hospitals_kau_10km.json",
        "lat_col": "좌표(Y)",
        "lon_col": "좌표(X)",
        "name_col": "요양기관명",
        "extra_cols": ["주소", "전화번호", "종별코드명"],
        # 재난 대응 관점 — 병원급 이상만. 의원/치과/한의원/보건소 제외.
        "keep_col": "종별코드명",
        "keep_values": ["상급종합", "종합병원", "병원", "요양병원"],
    },
}


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def filter_dataset(kind: str) -> int:
    if kind not in CONFIG:
        print(f"ERROR: unknown kind '{kind}'. choose from {list(CONFIG)}", file=sys.stderr)
        return 1

    cfg = CONFIG[kind]
    src = RAW_DIR / cfg["input"]
    dst = OUT_DIR / cfg["output"]

    if not src.exists():
        print(f"ERROR: 입력 CSV 없음: {src}", file=sys.stderr)
        print(f"  공공데이터포털에서 받은 CSV를 {RAW_DIR}/{cfg['input']} 로 두세요.", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    keep_col = cfg.get("keep_col")
    keep_values = set(cfg.get("keep_values", []))
    items = []
    skipped = 0

    # 한국 공공데이터 CSV는 종종 EUC-KR 인코딩. UTF-8 실패 시 cp949 재시도.
    try:
        f = open(src, encoding="utf-8-sig")
        f.read(1)
        f.seek(0)
    except UnicodeDecodeError:
        f = open(src, encoding="cp949")

    with f:
        reader = csv.DictReader(f)
        for row in reader:
            if keep_col and row.get(keep_col) not in keep_values:
                continue
            try:
                lat = float(row[cfg["lat_col"]])
                lon = float(row[cfg["lon_col"]])
            except (KeyError, ValueError, TypeError):
                skipped += 1
                continue
            d = haversine_m(CENTER[0], CENTER[1], lat, lon)
            if d > RADIUS_M:
                continue
            item = {
                "name": row.get(cfg["name_col"], ""),
                "lat": lat,
                "lon": lon,
                "distance_m": round(d, 1),
            }
            for c in cfg["extra_cols"]:
                if c in row:
                    item[c] = row[c]
            items.append(item)

    items.sort(key=lambda x: x["distance_m"])
    dst.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{kind}: 필터 완료 — {len(items)}건 (skipped: {skipped}) → {dst}")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python filter_public_data.py [shelters|fire_stations|hospitals|all]", file=sys.stderr)
        return 2
    arg = sys.argv[1]
    if arg == "all":
        rcs = [filter_dataset(k) for k in CONFIG]
        return max(rcs)
    return filter_dataset(arg)


if __name__ == "__main__":
    sys.exit(main())
