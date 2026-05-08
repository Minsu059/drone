"""가상 GPS — 한국항공대 인근 랜덤 워크.

추후 실제 GPS 모듈 (pynmea2 + USB GPS) 연결 시 동일한 read() 인터페이스의
NMEA 기반 클래스로 교체한다.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass


@dataclass
class GpsReading:
    lat: float
    lon: float
    alt: float
    timestamp: float


class MockGPS:
    """매 read()마다 step 범위 안에서 랜덤 워크하는 가짜 GPS."""

    def __init__(
        self,
        center: tuple[float, float] = (37.6000, 126.8645),
        alt: float = 50.0,
        step: float = 0.0003,
    ):
        self.lat, self.lon = center
        self.alt = alt
        self.step = step

    def read(self) -> GpsReading:
        self.lat += random.uniform(-self.step, self.step)
        self.lon += random.uniform(-self.step, self.step)
        return GpsReading(self.lat, self.lon, self.alt, time.time())
