# 드론 재난 대응 시스템 — 프로젝트 진행 현황

## 프로젝트 개요

중앙 서버와 드론(라즈베리파이4, 카메라 모듈)을 연동하는 재난 대응 모니터링 시스템.
미니어처 프로토타입 데모를 목표로 하며, 실제 비행이 아닌 지상 테스트 환경에서 진행한다.
최종 목표는 재난 현장의 위험도를 분석하여 **구조 우선순위를 결정**하고, 최적 진입 경로를 안내하는 관제 시스템이다.

**GPS는 가상 데이터로 대체**, Pixhawk 없이 라즈베리파이에서 직접 처리한다.
나중에 GPS 모듈(Holybro M9N 등)을 연결하면 가상 데이터 부분만 교체하면 된다.

## 시스템 구성

### 드론 측 (현장)

| 구성요소 | 역할 | 비고 |
|---------|------|------|
| Raspberry Pi 4 (8GB) | 카메라 영상 분류 + 서버 전송 | TFLite, requests, Python |
| RPi 카메라 모듈 3 | 재난 상황 촬영 | CSI 연결 |
| GPS | **가상 데이터로 대체** (랜덤 좌표 생성) | 추후 M9N 모듈 연결 시 pynmea2로 교체 |

#### 라즈베리파이 분류 모델 (Edge AI)

촬영된 이미지를 대상으로 사전 학습된 가중치를 바탕으로 아래 항목들을 분류/추론한다.
**모델 자체는 별도 팀원이 개발하며, 본 프로젝트에서는 아래 인터페이스 계약을 기준으로 통합한다.**

| 분류 항목 | 출력 형식 | 설명 |
|----------|----------|------|
| 인명 감지 | 정수 (인원 수) | 프레임 내 감지된 사람 수 |
| 건물 붕괴율 | 실수 (0~100%) | 외벽 크랙 기반 구조 붕괴 정도 추정 |
| 도로 상태 | 카테고리 | 정상 / 정체 / 통행불가 |
| 화재 감지 | 카테고리 + 신뢰도 | 화재 여부 및 확신도 |
| 기타 재난 | 카테고리 | 침수, 산사태 등 확장 가능 |

##### Edge AI 인터페이스 계약

모델 통합 시 다음 인터페이스를 따른다. 모델 인계 전까지는 동일 시그니처의 mock 분류기로 대체한다.

**호출 방식** (Python 함수 인터페이스)
```python
def classify(image: np.ndarray) -> dict:
    """
    image: BGR uint8, shape=(H, W, 3), 권장 해상도 640x480
    반환: 아래 스키마를 따르는 dict
    """
```

**반환 스키마**
```json
{
  "person_count": 3,
  "collapse_rate": 72.5,
  "road_status": "normal | congested | blocked",
  "fire": {"detected": true, "confidence": 0.94},
  "disaster_type": "earthquake | flood | fire | landslide | none",
  "inference_ms": 120
}
```

**추론 트리거 조건**
- 매 프레임이 아닌 **N초 간격**(기본 3초)으로 추론
- 또는 직전 프레임 대비 **유의미한 변화 감지 시** 추론 (배경 차분 등, 추후 결정)
- `disaster_type != "none"` 또는 `fire.detected == true` 또는 `collapse_rate >= 임계값`인 경우에만 서버에 `disaster_report` 전송

**카메라 입력 추상화**
- `CameraSource` 인터페이스 (`read() -> np.ndarray`)
- 현재 구현: 디스크 이미지 폴더 순차 로드 (`MockCameraSource`)
- 카메라 모듈 도착 후: `PiCameraSource` (picamera2 기반)로 교체

### 서버 측 (관제센터)

| 구성요소 | 역할 | 비고 |
|---------|------|------|
| API 서버 | 드론 데이터 수신 (POST /api/drone-data) | FastAPI |
| DB | 수신 데이터 저장 | SQLite(데모) / PostgreSQL+PostGIS |
| 위험도 추론 모델 | 구역별 위험도 산출 + 구조 우선순위 결정 | Python (PyTorch / scikit-learn) |
| 경로 추론 엔진 | 최적 구조 진입 경로 계산 | 교통 상황 + 붕괴 구간 반영 |
| 대시보드 | 실시간 지도 기반 관제 모니터링 | React + Leaflet 또는 Folium |

#### 서버 위험도 추론 모델

드론에서 수신한 데이터를 종합하여 구역(일정 범위)의 위험도를 추론한다.

**입력 데이터**: 촬영 위치(GPS), 건물 붕괴율, 인명 감지 수, 화재 여부, 도로 상태

**출력**: 구역별 위험도 점수 (0~100) → 구조 우선순위 랭킹

**추론 흐름**:
1. 수신된 데이터를 GPS 기준으로 일정 범위의 구역(그리드)에 매핑
2. 구역 내 붕괴 정도 + 인명 피해 예상 + 화재 규모를 종합하여 위험도 점수 산출
3. 위험도 점수 기반으로 구조 우선순위 결정
4. 교통 상황(도로 정체/통행불가) + 붕괴 구간을 반영하여 구조 진입 가능 경로 탐색
5. 가장 빠른 경로 및 우회 경로를 대시보드에 표시

## 데이터 흐름

```
카메라 모듈 → Raspberry Pi 4 → (HTTP/WiFi) → API 서버 → DB 저장
               (Edge AI 분류)                              ↓
               (GPS: 가상 데이터)                    위험도 추론 모델
                                                        ↓
                                                  경로 추론 엔진
                                                        ↓
                                                    대시보드 표시
```

### 전송 데이터 형식

JSON 형식으로 전송한다. 이미지는 Base64 인코딩하여 JSON 내에 포함한다.
(데모 규모에서는 충분하며, 이미지 크기가 커질 경우 multipart/form-data로 전환 가능)

**JSON 전송 장점**: 가볍고 파싱이 쉬움, FastAPI 자동 검증 가능, 사람이 읽을 수 있음, 범용적
**JSON 전송 단점**: 이미지 Base64 인코딩 시 크기 ~33% 증가, 대용량 바이너리에는 비효율적

#### 전송 데이터 구분

1. **현재 위치 데이터** (주기적 전송, 1~5초 간격)
   - drone_id, lat, lon, alt, timestamp
   - GPS 가상 데이터 (랜덤 좌표 이동)
   - 대시보드에서 드론 아이콘이 실시간으로 이동

2. **재난 분석 데이터** (감지 시에만 전송)

```json
{
  "drone_id": "drone-01",
  "type": "disaster_report",
  "lat": 37.5665,
  "lon": 126.9780,
  "alt": 50.2,
  "timestamp": 1716000000,
  "analysis": {
    "person_count": 3,
    "collapse_rate": 72.5,
    "road_status": "blocked",
    "fire_detected": true,
    "fire_confidence": 0.94,
    "disaster_type": "earthquake"
  },
  "image_base64": "iVBORw0KGgo..."
}
```

## 완료 항목

- [x] RTK GPS → Pixhawk 4 연결 (이전 테스트, 현재 미사용)
- [x] Windows PC에서 QGroundControl로 위치 데이터 수신 확인 (이전 테스트)
- [x] KML 파일 내보내기 → Google Earth 확인 (참고용, 대시보드로 대체)
- [x] 라즈베리파이 4B (8GB) OS 설치 (RPi OS 64-bit)
- [x] SSH 접속 확인 (pi@dronepi.local)
- [x] 기본 패키지 설치 (python3-pip, python3-venv, git)
- [x] 프로젝트 폴더 및 가상환경 생성 (~/drone, venv: drone)

## 진행 예정 항목

작업을 두 트랙으로 분리한다. **트랙 A는 본인 담당(서버/통신/대시보드)**, **트랙 B는 외부 의존(Edge AI 모델, 카메라 하드웨어)**.
트랙 A는 트랙 B 완료를 기다리지 않고 mock/추상화로 끝까지 진행 가능하며, 마지막 통합 단계에서 합류한다.

### 트랙 A — 본인 담당 (병렬 진행 가능)

- [~] **A1. 메인 서버 구축** *(부분 완료 — 통신 검증됨)*
  - [x] FastAPI 서버 (POST /api/drone-data)
  - [x] 라즈베리파이 → 서버 HTTP POST 전송 (position / disaster_report)
  - [x] 이미지 Base64 전송 검증 (test_image.py)
  - [ ] DB 스키마 확정 (position, disaster_report, image 분리 저장)
  - [ ] 응답/에러 처리 정리, 입력 검증(Pydantic) 강화

- [ ] **A2. Edge AI mock 분류기 + 카메라 추상화**
  - `classify(image) -> dict` 시그니처의 룰베이스/랜덤 stub 구현
  - `CameraSource` 인터페이스 + `MockCameraSource` (이미지 폴더 순차 로드)
  - 라즈베리파이 측 분류→전송 루프 통합 (트리거 조건 적용)

- [ ] **A3. 위험도 추론 모델 개발 (룰베이스 우선)**
  - GPS 기반 구역(그리드) 매핑 로직
  - 가중합 기반 위험도 점수 (붕괴율 + 인명 + 화재 + 도로) — 학습 데이터 없으니 룰베이스로 시작
  - 구조 우선순위 랭킹 알고리즘
  - (선택) 데이터 누적 후 ML 모델로 교체

- [ ] **A4. 경로 추론 엔진 개발**
  - 미니어처용 가상 그래프 정의 (NetworkX, 노드 20~30개 수준)
  - 도로 상태 → 가중치, 붕괴 구간 → 노드 제거 또는 가중치 극대화
  - A* / Dijkstra 기반 최단/최적 경로
  - 구조 진입 가능 경로 필터링

- [ ] **A5. 대시보드 개발**
  - Leaflet 기반 실시간 지도
  - 드론 위치 실시간 표시 (position 스트림)
  - 구역별 위험도 히트맵
  - 구조 우선순위 패널
  - 추천 진입 경로 표시
  - disaster_report 클릭 시 첨부 이미지 팝업

### 트랙 B — 외부 의존 (대기/병렬)

- [ ] **B1. Edge AI 분류 모델 개발** *(별도 팀원 담당)*
  - 재난 분류 데이터셋 수집 및 라벨링
  - 모델 학습 (인명 감지, 붕괴율, 도로 상태, 화재)
  - TFLite 변환
  - **인계 시점**: 위 "Edge AI 인터페이스 계약" 준수 필수

- [ ] **B2. 카메라 연결 및 테스트** *(카메라 모듈 배송 대기)*
  - RPi 카메라 모듈 3 연결
  - picamera2로 촬영 테스트
  - `PiCameraSource` 구현 → `MockCameraSource` 자리 교체

### 통합

- [ ] **C1. 트랙 A/B 합류**
  - mock 분류기 → 실제 Edge AI 모델 교체
  - MockCameraSource → PiCameraSource 교체
  - 인터페이스 계약 위반 여부 확인

- [ ] **C2. 미니어처 데모 시연**
  - 데모 시나리오 스크립트 (예: 지진 발생 → 드론 이동 → 위험 구역 식별 → 진입 경로 안내)
  - 전체 파이프라인 통합 테스트

- [ ] **(선택) GPS 모듈 연결**
  - Holybro M9N GPS 또는 USB GPS 모듈 연결
  - pynmea2로 실제 NMEA 데이터 수신
  - 가상 GPS 코드를 실제 GPS 코드로 교체

## 결정 필요 항목 (TBD)

설계가 진행되려면 아래 값들을 확정해야 한다. 잠정 디폴트를 표시했으나 데모 환경 정해지면 재검토.

| 항목 | 잠정 디폴트 | 비고 |
|------|------------|------|
| 그리드 셀 크기 | 10m × 10m (미니어처) / 100m × 100m (실제) | 위험도 매핑 단위 |
| 위험도 가중치 | 인명 0.4 / 붕괴 0.3 / 화재 0.2 / 도로 0.1 | 룰베이스 초기값, 튜닝 필요 |
| disaster_report 트리거 | `fire.detected` or `collapse_rate >= 30` or `person_count >= 1` | Edge AI 모델 출력 안정화 후 조정 |
| position 전송 주기 | 2초 | 너무 잦으면 DB/대시보드 부담 |
| 경로 그래프 데이터 | 직접 정의(NetworkX) | OSM 끌어오면 미니어처 좌표와 안 맞음 |
| 미니어처 좌표 스케일 | 가짜 GPS 좌표(서울 시청 기준 오프셋) | 실제 좌표계 유지 → 대시보드 그대로 사용 |
| 데모 시나리오 | 미정 | 시연 스토리부터 정해야 스코프 확정 가능 |

## 현재 환경

| 항목 | 내용 |
|------|------|
| 라즈베리파이 | RPi 4 Model B, 8GB RAM |
| OS | Raspberry Pi OS 64-bit |
| 호스트이름 | dronepi |
| SSH 접속 | pi@dronepi.local |
| 프로젝트 폴더 | ~/drone |
| 가상환경 | ~/drone/drone |
| 메인 서버 | Windows 데스크탑 (같은 공유기 내) |

## 기술 스택 요약

- **드론 (Edge)**: TensorFlow Lite, OpenCV, picamera2, Python
- **GPS**: 가상 데이터 (추후 pynmea2로 교체)
- **통신**: HTTP REST (JSON), WiFi (같은 공유기)
- **서버**: FastAPI, SQLite / PostgreSQL + PostGIS
- **위험도 모델**: PyTorch / scikit-learn, 구역 그리드 매핑
- **경로 추론**: A* / Dijkstra, NetworkX 또는 OSRM
- **대시보드**: React + Leaflet 또는 Python Folium

## 메모

- Pixhawk 4, RTK GPS는 현재 미사용. GPS는 가상 데이터로 대체.
- 나중에 GPS 모듈 연결 시 코드 수정 최소화 (좌표 생성 부분만 교체).
- KML 내보내기는 대시보드가 지도 기반이므로 별도로 필요하지 않음.
- 현재 위치 데이터와 재난 분석 데이터는 서버에서 type 필드로 구분하여 저장.
- 데모 환경에서는 서버를 Windows 데스크탑에서 실행.
- JSON 전송으로 시작하되, 이미지 크기/빈도가 문제될 경우 multipart/form-data로 전환 검토.
- 위험도 추론 모델은 서버에서 실행 (라즈베리파이보다 연산 자원이 풍부하므로).
- 경로 추론 시 붕괴된 도로는 그래프에서 제거하거나 가중치를 극대화하여 우회 유도.
- VS Code Remote SSH로 라즈베리파이 원격 개발 가능.
