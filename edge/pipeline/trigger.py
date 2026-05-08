"""disaster_report 송신 트리거 룰. 임계값은 docs/project.md TBD 표 기준."""
from __future__ import annotations

from edge.classifier.base import ClassifyResult


def should_trigger(
    r: ClassifyResult,
    *,
    collapse_threshold: float = 30.0,
    person_threshold: int = 1,
) -> bool:
    return (
        r["fire_detected"]
        or r["collapse_rate"] >= collapse_threshold
        or r["person_count"] >= person_threshold
        or r["road_status"] == "blocked"
    )
