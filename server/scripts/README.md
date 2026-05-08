# 선행 데이터 수집 가이드

대시보드(A5)에서 사용할 외부 데이터를 미리 받아 캐싱한다.
모두 1회성 작업이며, 받은 결과물은 `data/` 디렉토리에 저장된다.

## 디렉토리 구조

```
~/drone/
├── scripts/
│   ├── download_osm.py             # OSM 도로망 다운로드
│   ├── download_vworld_boundary.py # VWorld 행정구역 경계 다운로드
│   └── filter_public_data.py       # 공공데이터 KAU 반경 필터링
└── data/
    ├── road_kau_5km.graphml        # OSM 결과 (download_osm.py가 생성)
    ├── admin_boundary_kau_region.geojson  # VWorld 결과
    ├── raw/                        # 공공데이터포털에서 받은 원본 CSV
    └── public/                     # 필터링된 JSON 결과
```

## 1. OSM 도로망 (자동, 즉시 실행 가능)

osmnx가 모든 걸 알아서 함. 인터넷만 있으면 즉시 가능.

```bash
source ~/drone/drone/bin/activate
pip install osmnx
python ~/drone/scripts/download_osm.py
```

결과: `data/road_kau_5km.graphml`

## 2. VWorld 행정구역 경계 (회원가입 필요)

### 2-1. 인증키 발급

1. https://www.vworld.kr/ 회원가입
2. 마이페이지 → 인증키 관리 → "오픈 API 인증키 신청"
3. 인증키 종류: **서버형**, 사용 URL: `localhost` 추가
4. 승인 즉시 발급 (예전엔 1일 대기였으나 현재 자동 승인)

### 2-2. 다운로드 실행

```bash
export VWORLD_API_KEY="발급받은_인증키"
python ~/drone/scripts/download_vworld_boundary.py
```

결과: `data/admin_boundary_kau_region.geojson` (KAU 반경 6km 내 읍면동 경계)

> 위성 타일 레이어(`https://api.vworld.kr/req/wmts/...`)는 별도 다운로드 불필요 —
> 대시보드(Leaflet) 코드에서 같은 인증키로 직접 호출.

## 3. 공공데이터 (수동 다운로드 + 자동 필터)

### 3-1. data.go.kr 회원가입

https://www.data.go.kr/ 회원가입 (소셜 로그인 가능)

### 3-2. 데이터셋 다운로드 (3종)

각 페이지에서 CSV로 다운받아 `data/raw/` 에 아래 이름으로 저장:

| 데이터셋 | 검색어 (data.go.kr) | 저장 파일명 |
|---------|---------------------|-------------|
| 전국 대피소 표준데이터 | "전국대피소표준데이터" | `data/raw/shelters.csv` |
| 119안전센터/소방서 | "전국119안전센터표준데이터" | `data/raw/fire_stations.csv` |
| 병원/응급실 | "전국병원표준데이터" 또는 "응급의료기관" | `data/raw/hospitals.csv` |

> 한국 공공데이터 CSV는 EUC-KR/CP949 인코딩이 흔함. 스크립트가 자동 감지해서 처리.

### 3-3. 컬럼명 확인 후 필터 실행

다운받은 CSV 헤더를 한 번 열어보고 `scripts/filter_public_data.py`의 `CONFIG`
딕셔너리에서 `lat_col`, `lon_col`, `name_col` 컬럼명을 실제 헤더에 맞춰 조정.

```bash
head -1 ~/drone/data/raw/shelters.csv  # 헤더 확인
# 필요 시 filter_public_data.py 수정
python ~/drone/scripts/filter_public_data.py shelters
python ~/drone/scripts/filter_public_data.py fire_stations
python ~/drone/scripts/filter_public_data.py hospitals
# 또는 한 번에:
python ~/drone/scripts/filter_public_data.py all
```

결과: `data/public/{shelters,fire_stations,hospitals}_kau_10km.json`

## 라이선스 표기 의무

대시보드 푸터에 다음을 명시 (생략 시 라이선스 위반):

- 지도 데이터 © OpenStreetMap contributors (ODbL)
- 위성영상 © VWorld (국토교통부)
- 공공데이터 © 행정안전부 / 소방청 / 보건복지부 (data.go.kr)

## .gitignore 권장

`data/raw/`, `data/road_kau_5km.graphml`, `data/admin_boundary_kau_region.geojson`,
`data/public/`는 용량 크고 라이선스 있을 수 있으므로 git에 포함하지 말 것.
