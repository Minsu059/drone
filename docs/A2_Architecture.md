# A2 — Edge AI Mock 분류기 + 카메라 추상화 설계

> 목적: 실제 Edge AI 모델(트랙 B1)과 카메라 모듈(트랙 B2)이 도착하기 전에,
> 라즈베리파이 측 **분류 → 트리거 → 서버 전송** 루프를 끝까지 검증할 수 있는 mock 레이어를 구축한다.
> 모델/카메라 인계 시점에는 **인터페이스 교체만으로 실제 구현으로 전환**되도록 설계한다.

## 1. 설계 원칙

1. **인터페이스 우선**: `CameraSource`, `Classifier` 두 추상 클래스만 통합 코드가 의존한다. 구현체는 mock/실제 자유롭게 교체.
2. **fixture 기반 mock**: 단순 랜덤 대신, **라벨이 부여된 실제 이미지 fixture**를 순차 로드하여 결정적(deterministic) 결과를 뱉는다. 시나리오 재현·디버깅이 쉬움.
3. **데이터셋 두 갈래 활용**:
   - AI Hub 지진 데이터셋 + Mendeley 튀르키예 UAV → **트랙 B1 모델 학습용 (메인 용도)**
   - 동일 데이터셋의 일부를 라벨링하여 **A2 fixture로도 재활용** (mock 출력의 사실성 ↑)
4. **미니어처 시나리오 5종 매핑 명시**: 미니어처에서 만든 상황이 분류 스키마의 어떤 필드/값에 대응되는지 표로 박아둔다. 이 표가 곧 **B1 모델의 라벨 가이드**가 된다.

---

## 2. 컴포넌트 구조

```
~/drone/edge/
├── camera/
│   ├── base.py              # CameraSource (ABC)
│   ├── mock.py              # MockCameraSource (fixture 폴더 기반)
│   └── pi.py                # PiCameraSource (B2 도착 후 구현)
├── classifier/
│   ├── base.py              # Classifier (ABC)
│   ├── mock.py              # MockClassifier (fixture 라벨 그대로 반환)
│   ├── rule.py              # RuleClassifier (선택, 단순 룰베이스 백업)
│   └── tflite_runner.py     # TFLiteClassifier (B1 인계 후 구현)
├── pipeline/
│   ├── trigger.py           # disaster_report 전송 조건
│   ├── sender.py            # 서버 POST (test_client.py 로직 흡수)
│   └── loop.py              # 메인 루프: capture → classify → trigger → send
└── fixtures/
    ├── manifest.json        # 시나리오/라벨 인덱스
    └── images/              # 실제 이미지 (데이터셋 발췌 + 미니어처 촬영분)
```

---

## 3. 인터페이스 계약 (재확인)

### `CameraSource`

```python
class CameraSource(ABC):
    @abstractmethod
    def read(self) -> tuple[np.ndarray, dict]:
        """
        반환: (image_bgr, meta)
            image_bgr: BGR uint8, (H, W, 3)
            meta: {"source_id": str, "scenario": str | None, ...}
                  - mock에서는 scenario 라벨도 함께 흘려보내, 검증/디버깅에 사용
                  - PiCameraSource에서는 scenario=None
        """
```

### `Classifier`

```python
class Classifier(ABC):
    @abstractmethod
    def classify(self, image: np.ndarray, meta: dict | None = None) -> dict:
        """반환 스키마: project.md의 'Edge AI 인터페이스 계약' 섹션 참조"""
```

> **중요**: `MockClassifier`는 `meta.scenario`를 보고 `fixtures/manifest.json`의 라벨을 그대로 반환한다.
> 즉 mock은 "이미 라벨이 박힌 fixture를 통과시키는 패스스루"로 동작 → 결정적·재현 가능.
> 실제 `TFLiteClassifier`는 `meta`를 무시하고 `image`만으로 추론.

---

## 4. 미니어처 시나리오 ↔ 분류 출력 매핑

미니어처 5개 구성요소 각각에 대해, mock이 뱉을 라벨과 B1 모델이 학습해야 할 라벨을 미리 박아둔다.

| 미니어처 시나리오 | person_count | collapse_rate | road_status | fire_detected | disaster_type | 비고 |
|------------------|-------------|---------------|-------------|---------------|---------------|------|
| **건물 크랙** (외벽 균열) | 0 | 15~40 | normal | false | earthquake | 경미한 지진 피해, 구조 우선순위 낮음 |
| **건물 붕괴** (전/부분 붕괴) | 0~3 | 60~95 | normal/blocked | false | earthquake | 인명 피해 가능성 ↑, 구조 우선순위 최상 |
| **도로 표지판 무너짐** | 0 | 0~10 | congested | false | earthquake | 통행 가능하나 속도 저하 |
| **도로 붕괴** (싱크홀/도로 함몰) | 0 | 0 | blocked | false | earthquake | 우회 경로 필요 |
| **차량 포화** (정체) | 0 | 0 | congested | false | none | 비-재난 상황, 경로 가중치만 영향 |

> **확장 슬롯**: 화재(`fire_detected=true`), 침수(`disaster_type="flood"`), 산사태는 미니어처 미구현이므로
> 데이터셋 발췌 이미지로만 fixture를 채워 mock에서 흘려본다.
> 인명(`person_count > 0`)은 미니어처에 미니어처 인형 배치 가능 시 추가.

---

## 5. 데이터셋 활용 전략

| 데이터셋 | 트랙 B1 (모델 학습) | A2 mock fixture |
|---------|---------------------|------------------|
| **AI Hub 지진/건물붕괴** | 메인 학습 셋 — collapse_rate 회귀 + disaster_type 분류 | 각 라벨대로 5~10장 발췌 → fixture로 사용 |
| **Mendeley 튀르키예 UAV** | UAV 시점 학습 (실제 드론 시점과 가장 유사) | 항공뷰 fixture 5~10장 발췌 |
| **미니어처 자체 촬영** | (선택) 도메인 적응용 fine-tuning | 카메라 도착 후 직접 촬영, 핵심 fixture |

### fixture 라벨 부여 방식 — `manifest.json`

```json
{
  "version": 1,
  "items": [
    {
      "id": "aihub_collapse_001",
      "path": "images/aihub/collapse_001.jpg",
      "scenario": "building_collapse",
      "source": "aihub_earthquake",
      "labels": {
        "person_count": 0,
        "collapse_rate": 78.0,
        "road_status": "blocked",
        "fire_detected": false,
        "fire_confidence": 0.02,
        "disaster_type": "earthquake"
      }
    },
    {
      "id": "mini_crack_003",
      "path": "images/miniature/crack_003.jpg",
      "scenario": "building_crack",
      "source": "miniature",
      "labels": {
        "person_count": 0,
        "collapse_rate": 25.0,
        "road_status": "normal",
        "fire_detected": false,
        "fire_confidence": 0.01,
        "disaster_type": "earthquake"
      }
    }
  ]
}
```

라벨링 부담은 작음 — fixture는 30~50장 수준이면 충분. **시연 시나리오에 맞춰 큐레이션**하는 것이 핵심.

---

## 6. 메인 루프 흐름

```
loop.py:
    cam = MockCameraSource("fixtures/manifest.json", order="round_robin" | "scenario_sequence")
    clf = MockClassifier()      # 또는 TFLiteClassifier(model_path)
    sender = ReportSender(SERVER_URL, drone_id="drone-01")
    gps = MockGPS(...)          # 가상 GPS

    while True:
        image, meta = cam.read()
        result = clf.classify(image, meta)
        pos = gps.read()

        sender.send_position(pos)             # 항상 (주기 2s)
        if should_trigger(result):            # trigger.py
            sender.send_disaster(pos, result, image)

        sleep(INFERENCE_INTERVAL_S)           # 기본 3초
```

### `should_trigger(result)` 기본 룰

```python
def should_trigger(r: dict) -> bool:
    return (
        r["fire"]["detected"]
        or r["collapse_rate"] >= 30
        or r["person_count"] >= 1
        or r["road_status"] == "blocked"
    )
```

(임계값은 project.md TBD 표 그대로. 운영 중 튜닝.)

### MockCameraSource 순서 모드

- `round_robin`: manifest의 모든 이미지를 순환 — 일반 회귀 테스트용
- `scenario_sequence`: 데모 시나리오 스크립트(예: `["normal", "crack", "collapse", "road_blocked"]`)대로 순회 — 시연 리허설용

---

## 7. 통합 후 교체 지점

| 컴포넌트 | A2 단계 | 인계 후 |
|---------|---------|---------|
| `CameraSource` | `MockCameraSource` (fixture) | `PiCameraSource` (picamera2) |
| `Classifier` | `MockClassifier` (manifest 라벨 패스스루) | `TFLiteClassifier` (.tflite) |
| 그 외 (loop / sender / trigger / GPS) | 그대로 사용 | 그대로 사용 |

> **검증 방법**: 인계 후 `MockClassifier`와 `TFLiteClassifier`를 동일 fixture에 돌려 결과 차이를 측정.
> 큰 괴리가 있으면 B1 모델의 도메인 적응 필요(미니어처/UAV 시점 fine-tuning 등).

---

## 8. 작업 순서 (A2 내부)

1. `edge/` 디렉토리 + 빈 ABC 파일 생성, `pyproject` 또는 venv에 의존성 정리
2. `MockGPS`, `ReportSender` 작성 (test_client.py 로직 정리해서 흡수)
3. `CameraSource` ABC + `MockCameraSource` 구현
4. `Classifier` ABC + `MockClassifier` 구현
5. `fixtures/manifest.json` 초기 5~10장 — 데이터셋 발췌로 채워 동작 확인
6. `loop.py` 통합 + 서버 수신 로그로 검증
7. 미니어처 완성 후 직접 촬영분으로 fixture 보강
8. (B1 인계 시) `TFLiteClassifier` 추가, `MockClassifier`와 A/B 비교

---

## 9. 미해결 / 결정 필요

- **fixture 저장소**: 데이터셋 라이선스 확인 필요. AI Hub는 재배포 제한이 있을 수 있어 fixture를 git에 올리지 말고 별도 다운로드 스크립트로 처리하는 게 안전.
- **이미지 해상도**: 현재 `test_image.py`는 320×240. B1 모델 요구 해상도(640×480 권장) 정해지면 `CameraSource.read()`에서 통일.
- **인명 라벨**: 미니어처에 인형 배치 여부 미정. 배치 안 하면 mock에서만 person_count 시연.
- **fire / flood / landslide**: 미니어처 미구현. 데이터셋 발췌 fixture만으로 흘려볼지, 시연 범위에서 제외할지 결정.
