"""카메라 소스 추상화.

구현체:
  - MockCameraSource: fixtures/manifest.json 라벨 기반 결정적 mock (개발/시연 리허설용)
  - PiCameraSource: picamera2 기반 실제 카메라 (B2 인계 후 추가)

통합 코드(loop.py)는 항상 이 ABC만 의존한다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class CameraFrame:
    """카메라 한 프레임 + 메타데이터.

    image: BGR uint8, shape=(H, W, 3). 권장 해상도 640x480.
    source_id: 프레임 출처 식별자 (fixture id, 또는 카메라 시리얼).
    scenario: Mock 전용 — fixture 라벨 (예: "building_collapse").
              PiCameraSource에서는 None.
    """

    image: np.ndarray
    source_id: str
    scenario: Optional[str] = None


class CameraSource(ABC):
    """매 호출마다 한 프레임을 반환하는 카메라 인터페이스."""

    @abstractmethod
    def read(self) -> CameraFrame:
        """다음 프레임 반환. 소진/실패 시 RuntimeError."""

    def close(self) -> None:
        """리소스 정리. 필요한 구현체에서 오버라이드."""
