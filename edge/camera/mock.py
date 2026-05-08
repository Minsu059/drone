"""fixture 폴더 + manifest.json 기반 결정적 카메라 소스.

manifest.items 의 image 파일이 없으면 시나리오별 색의 placeholder 이미지를 자동 생성한다 — 이미지가
도착하기 전에도 파이프라인 통합 검증이 가능하게.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image

from .base import CameraFrame, CameraSource

OrderMode = Literal["round_robin", "scenario_sequence"]

# 시나리오별 placeholder 색 (BGR uint8). 시각적으로 구분만 되면 충분.
_SCENARIO_COLOR_BGR: dict[str, tuple[int, int, int]] = {
    "building_crack":     (180, 180, 180),
    "building_collapse":  (60, 60, 60),
    "road_signage_down":  (50, 180, 200),
    "road_collapse":      (30, 50, 100),
    "vehicle_saturated":  (50, 100, 200),
    "fire":               (0, 50, 220),
    "flood":              (220, 100, 30),
    "landslide":          (60, 80, 100),
    "normal":             (220, 220, 220),
}
_PLACEHOLDER_HW = (480, 640)


class MockCameraSource(CameraSource):
    """manifest.json 기반 카메라 소스.

    order:
      - "round_robin": 모든 fixture를 순환 (회귀 테스트용)
      - "scenario_sequence": manifest 순서 그대로 1회 순회 (시연 리허설용)
    """

    def __init__(self, manifest_path: Path | str, order: OrderMode = "round_robin"):
        self.manifest_path = Path(manifest_path)
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.items: list[dict] = manifest["items"]
        if not self.items:
            raise ValueError(f"manifest 비어있음: {self.manifest_path}")
        self.order = order
        self._index = 0
        self._fixture_root = self.manifest_path.parent

    def read(self) -> CameraFrame:
        if self.order == "scenario_sequence" and self._index >= len(self.items):
            raise RuntimeError("scenario_sequence 모두 소진됨")

        item = self.items[self._index % len(self.items)]
        self._index += 1

        image_path = self._fixture_root / item["path"]
        if image_path.exists():
            with Image.open(image_path) as im:
                arr = np.array(im.convert("RGB"))
            # PIL은 RGB, 우리 인터페이스는 BGR
            arr = arr[:, :, ::-1].copy()
        else:
            arr = self._placeholder(item.get("scenario", ""))

        return CameraFrame(
            image=arr,
            source_id=item["id"],
            scenario=item.get("scenario"),
        )

    @staticmethod
    def _placeholder(scenario: str) -> np.ndarray:
        bgr = _SCENARIO_COLOR_BGR.get(scenario, (128, 128, 128))
        h, w = _PLACEHOLDER_HW
        arr = np.empty((h, w, 3), dtype=np.uint8)
        arr[:, :] = bgr
        return arr
