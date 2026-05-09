# 드론 재난 대응 시스템

미니어처 프로토타입을 통한 재난 모니터링 및 구조 우선순위·진입 경로 관제 데모 시스템.
드론(라즈베리파이 + 카메라)이 재난 현장을 촬영·분류해 메인서버로 전송하면, 관제센터 대시보드가 실시간으로 위험 구역 위험도와 진입 경로를 시각화한다.


---

## 시스템 구성

```
┌──────────────────────────────┐         HTTP POST          ┌────────────────────────┐
│  드론 측 (라즈베리파이 4)     │  ───────────────────────►  │  메인서버 (FastAPI)    │
│  ─ 카메라 (CSI Module 3)     │   /api/drone-data           │  ─ SQLite DB           │
│  ─ Edge AI 분류 (TFLite)     │   { drone_id, type,         │  ─ 이미지 파일 저장    │
│  ─ 가상 GPS (랜덤 워크)      │     lat, lon, alt,          │  ─ 위험도 산정         │
│  ─ 송신 루프 (Python)        │     analysis, image_b64 }   │  ─ /api/dashboard/*    │
└──────────────────────────────┘                              └───────────┬────────────┘
                                                                          │ fetch
                                                          ┌───────────────▼────────────┐
                                                          │  대시보드 (Vite + React)    │
                                                          │  ─ 광역 뷰 (재난 5건)      │
                                                          │  ─ 미니어처 뷰 (SVG)        │
                                                          └────────────────────────────┘
```

- **드론 측**: 카메라 영상 → Edge AI 분류기(현재는 mock 분류기) → 가상 GPS와 함께 서버로 송신
- **메인서버**: 드론 데이터 수신·저장, 광역/미니어처 데이터 SSOT 역할
- **대시보드**: React + react-leaflet 기반, 광역 → 한국항공대 클릭 → 미니어처 풀스크린

상세 설계: [docs/project.md](docs/project.md), [docs/A2_Architecture.md](docs/A2_Architecture.md), [docs/dashboard.md](docs/dashboard.md).

---

## 디렉토리 구조

```
docs/                           설계 문서 (project, A2_Architecture, dashboard)
server/                         메인서버 (FastAPI + Vite + React)
├── main.py                     FastAPI 엔트리
├── database.py / models.py     SQLite + Pydantic
├── miniature_map.py            광역 + 미니어처 데이터 SSOT
├── scripts/                    OSM/VWorld/공공데이터 수집 스크립트
└── dashboard/                  Vite + React 19 + TS + react-leaflet
edge/                           라즈베리파이 (드론 측)
├── camera/{base,mock}.py       CameraSource ABC + MockCameraSource
├── classifier/{base,mock}.py   Classifier ABC + MockClassifier
├── pipeline/                   GPS / sender / trigger / loop
└── fixtures/manifest.json      9개 시나리오 라벨 (미니어처 5 + 확장 4)
```

---

## 빠른 시작

### 1. 메인서버 셋업 (Windows / Linux / macOS)

```bash
git clone git@github.com:Minsu059/drone.git
cd drone

# Python 가상환경
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 백엔드 의존성
pip install -r server/requirements.txt
pip install osmnx                          # 도로 그래프 (광역 진입 경로용)

# 프론트엔드 (선택 — 대시보드 띄울 때만)
cd server/dashboard
npm install
cd ../..
```

서버 실행:

```bash
# 터미널 1 — FastAPI (포트 8000)
cd server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 터미널 2 — Vite dev (포트 5173, /api는 :8000으로 proxy)
cd server/dashboard
npm run dev
```

브라우저: http://localhost:5173

### 2. 라즈베리파이 셋업

```bash
ssh pi@<라즈베리파이_IP>     # 또는 pi@dronepi.local

cd ~
git clone git@github.com:Minsu059/drone.git
cd drone

python3 -m venv drone
source drone/bin/activate

pip install requests numpy pillow
```

### 3. 드론 → 서버 송신 구동

라즈베리파이에서:

```bash
cd ~/drone
source drone/bin/activate

python -m edge.pipeline.loop \
    --server-url http://<메인서버_IP>:8000/api/drone-data \
    --interval 3 \
    --order round_robin
```

옵션:
- `--server-url`: 메인서버 주소 (LAN: `http://192.168.x.x:8000/...`, 외부 노출 시: ngrok URL)
- `--interval`: 송신 주기 (초). 기본 3초.
- `--order`: `round_robin`(무한 순환) 또는 `scenario_sequence`(9 fixture 1회 순회)
- `--max-iters N`: N번 후 자동 종료 (디버깅)
- `--no-image`: disaster_report 이미지 첨부 생략

`Ctrl+C`로 종료.

---

## 메인서버를 외부에서 접근 가능하게 (라즈베리파이가 다른 네트워크에서 송신할 때)

라즈베리파이가 메인서버와 같은 LAN이 아니면 메인서버가 외부에 노출돼야 함. 세 가지 옵션:

### 옵션 A — ngrok (즉시, 추천)

1. 가입: https://ngrok.com/
2. 설치 (Windows): `winget install Ngrok.Ngrok` 또는 ngrok.com에서 다운로드
3. 인증 토큰 등록: `ngrok config add-authtoken <YOUR_TOKEN>`
4. 터널 실행: `ngrok http 8000`
5. 출력에서 `Forwarding https://abc123.ngrok-free.app -> http://localhost:8000` 확인
6. 라즈베리파이에서 `--server-url https://abc123.ngrok-free.app/api/drone-data` 로 사용

⚠ 무료 티어는 ngrok 재시작 시 도메인이 바뀜. 시연 직전 한 번 띄우는 식.

### 옵션 B — Cloudflare Tunnel (영구 도메인 무료)

1. Cloudflare 계정 + 도메인 (도메인 없으면 `*.trycloudflare.com` 임시 사용 가능)
2. cloudflared 설치 → `cloudflared tunnel login` → `cloudflared tunnel create drone`
3. config.yml 작성:
   ```yaml
   tunnel: <UUID>
   credentials-file: <경로>
   ingress:
     - hostname: drone.example.com
       service: http://localhost:8000
     - service: http_status:404
   ```
4. DNS 등록 → `cloudflared tunnel run drone`
5. 라즈베리파이: `--server-url https://drone.example.com/api/drone-data`

### 옵션 C — 포트포워딩 + DDNS

라우터 관리자 권한이 있을 때만 가능. 보안 주의 (HTTPS 직접 적용 필요).

1. 라우터 설정에서 외부 8000 → 내부 메인서버 IP:8000 포워딩
2. DDNS (예: DuckDNS, No-IP) 설정으로 고정 도메인 확보
3. 라즈베리파이: `--server-url http://<DDNS도메인>:8000/api/drone-data`

---

## Edge AI 모델 plug-in

현재 `edge/classifier/mock.py`의 `MockClassifier`가 fixture 라벨을 그대로 반환한다. 실제 모델로 교체하려면:

### 1. 인터페이스 계약

`edge/classifier/base.py` 의 `Classifier` ABC를 그대로 따른다.

```python
from edge.classifier.base import Classifier, ClassifyResult
import numpy as np

class TFLiteClassifier(Classifier):
    def __init__(self, model_path: str):
        # tflite_runtime.Interpreter 또는 tensorflow.lite.Interpreter 로 .tflite 로드
        ...

    def classify(self, image: np.ndarray, meta: dict | None = None) -> ClassifyResult:
        # image: BGR uint8, shape (H, W, 3). 기본 480x640.
        # meta는 무시 (mock 전용).
        ...
        return {
            "person_count": 3,
            "collapse_rate": 72.5,            # 0~100
            "road_status": "blocked",         # "normal" | "congested" | "blocked"
            "fire_detected": True,
            "fire_confidence": 0.94,          # 0.0~1.0
            "disaster_type": "earthquake",    # "earthquake" | "flood" | "fire" | "landslide" | "none"
            "inference_ms": 120,
        }
```

> **스키마는 flat**. `fire_detected` + `fire_confidence` 별도 필드. nested(`fire: {detected, confidence}`) 아님.

### 2. loop.py 에서 교체

`edge/pipeline/loop.py`의 다음 부분만 바꾸면 됨:

```python
# Before
from edge.classifier.mock import MockClassifier
clf = MockClassifier(args.manifest)

# After
from edge.classifier.tflite_runner import TFLiteClassifier
clf = TFLiteClassifier(model_path="path/to/model.tflite")
```

### 3. Mock과 실제 모델 A/B 비교

같은 fixture 이미지에 두 분류기를 돌려 출력 차이를 측정 → 도메인 적응 필요 여부 판단.

```python
# 권장: 학습 전 fixture에 실제 데이터셋 발췌 이미지를 채워두면 비교 의미가 커짐.
# edge/fixtures/images/aihub/, mendeley/ 폴더에 manifest 경로대로 저장.
```

상세는 [docs/A2_Architecture.md](docs/A2_Architecture.md) §3, §7 참조.

---

## 외부 데이터 수집 (선택)

대시보드 광역 뷰에 OSM 도로망, 행정구역, 공공 인프라(대피소/소방서/병원)를 표시하려면:

```bash
# OSM 도로망 (한국항공대 반경 5km)
python server/scripts/download_osm.py

# VWorld 행정구역 (회원가입 + 인증키 필요)
export VWORLD_API_KEY="<발급받은_키>"
python server/scripts/download_vworld_boundary.py

# 공공데이터 (data.go.kr 에서 CSV 3개 받아 data/raw/ 에 저장 후)
python server/scripts/filter_public_data.py all
```

상세 가이드: [server/scripts/README.md](server/scripts/README.md)

---

## 데이터 흐름

1. **위치 송신** — 매 `interval`초마다 `{type: "position", lat, lon, alt, timestamp}` POST. 대시보드 드론 마커 실시간 이동.
2. **재난 송신** — 분류 결과가 트리거 조건(`fire_detected` / `collapse_rate ≥ 30` / `person_count ≥ 1` / `road_status == "blocked"`) 만족 시 `{type: "disaster_report", lat, lon, alt, timestamp, analysis: {...}, image_base64}` POST.
3. **서버** — `drone_position` / `disaster_report` 테이블 저장 + 이미지 파일 보관.
4. **대시보드** — 1초마다 `/api/dashboard/wide`, `/api/dashboard/miniature` polling, 위험도 0~100 산정 후 시각화.

---

## 라이선스 / 출처 표기

본 프로젝트는 다음 외부 데이터를 사용한다. 대시보드 푸터에 출처 명시:

- 지도 데이터 © OpenStreetMap contributors (ODbL)
- 위성영상 © VWorld (국토교통부)
- 공공데이터 © 행정안전부 / 소방청 / 보건복지부 (data.go.kr)

코드 자체는 별도 명시 없는 한 본 리포 작성자(@Minsu059) 권리.
