"""manifest.json 라벨 패스스루 분류기.

CameraFrame.source_id 또는 scenario로 fixture 라벨을 조회해 그대로 반환한다.
실제 모델(TFLiteClassifier)은 image만 보지만, mock은 meta로 결정적으로 동작한다.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

from .base import ClassifyResult, Classifier

_DEFAULT_LABELS: ClassifyResult = {
    "person_count": 0,
    "collapse_rate": 0.0,
    "road_status": "normal",
    "fire_detected": False,
    "fire_confidence": 0.0,
    "disaster_type": "none",
    "inference_ms": 1,
}


class MockClassifier(Classifier):
    def __init__(self, manifest_path: Path | str):
        self.manifest_path = Path(manifest_path)
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self._by_id: dict[str, dict] = {}
        self._by_scenario: dict[str, dict] = {}
        for item in manifest["items"]:
            labels = item["labels"]
            self._by_id[item["id"]] = labels
            self._by_scenario.setdefault(item["scenario"], labels)

    def classify(self, image: np.ndarray, meta: Optional[dict] = None) -> ClassifyResult:
        labels = self._lookup(meta)
        result: ClassifyResult = {**_DEFAULT_LABELS, **labels, "inference_ms": 1}  # type: ignore[typeddict-item]
        return result

    def _lookup(self, meta: Optional[dict]) -> dict:
        if not meta:
            return {}
        sid = meta.get("source_id")
        if sid and sid in self._by_id:
            return self._by_id[sid]
        scenario = meta.get("scenario")
        if scenario and scenario in self._by_scenario:
            return self._by_scenario[scenario]
        return {}
