"""Edge AI 분류기 추상화.

구현체:
  - MockClassifier: CameraFrame.scenario를 보고 fixtures/manifest.json 라벨을 그대로 반환 (결정적).
  - TFLiteClassifier: .tflite 모델 추론 (B1 인계 후 추가).

반환 스키마는 docs/project.md 'Edge AI 인터페이스 계약' 절을 정본으로 한다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal, Optional, TypedDict

import numpy as np

RoadStatus = Literal["normal", "congested", "blocked"]
DisasterType = Literal["earthquake", "flood", "fire", "landslide", "none"]


class ClassifyResult(TypedDict):
    """flat 스키마 — 사용자 메인서버 코드(test_client.py 등)와 호환."""

    person_count: int
    collapse_rate: float          # 0 ~ 100
    road_status: RoadStatus
    fire_detected: bool
    fire_confidence: float        # 0.0 ~ 1.0
    disaster_type: DisasterType
    inference_ms: int


class Classifier(ABC):
    """단일 프레임 분류기."""

    @abstractmethod
    def classify(self, image: np.ndarray, meta: Optional[dict] = None) -> ClassifyResult:
        """이미지 한 프레임을 분류한다.

        meta: Mock 구현이 fixture 라벨을 찾기 위해 사용 (e.g. {"scenario": "..."}).
              실제 모델은 무시한다.
        """
