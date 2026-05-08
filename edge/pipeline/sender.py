"""서버 송신 — position 주기적, disaster_report 트리거 시.

기존 test_client.py 의 JSON 스키마와 호환. 이미지는 numpy BGR → JPEG → base64.
"""
from __future__ import annotations

import base64
import io
import logging
from typing import Optional

import numpy as np
import requests
from PIL import Image

from edge.classifier.base import ClassifyResult

from .gps import GpsReading

logger = logging.getLogger(__name__)


class ReportSender:
    def __init__(self, server_url: str, drone_id: str, timeout: float = 5.0):
        self.server_url = server_url
        self.drone_id = drone_id
        self.timeout = timeout

    def send_position(self, pos: GpsReading) -> dict:
        payload = {
            "drone_id": self.drone_id,
            "type": "position",
            "lat": pos.lat,
            "lon": pos.lon,
            "alt": pos.alt,
            "timestamp": pos.timestamp,
        }
        return self._post(payload)

    def send_disaster(
        self,
        pos: GpsReading,
        analysis: ClassifyResult,
        image: Optional[np.ndarray] = None,
    ) -> dict:
        payload: dict = {
            "drone_id": self.drone_id,
            "type": "disaster_report",
            "lat": pos.lat,
            "lon": pos.lon,
            "alt": pos.alt,
            "timestamp": pos.timestamp,
            "analysis": dict(analysis),
        }
        if image is not None:
            payload["image_base64"] = self._encode_image(image)
        return self._post(payload)

    def _post(self, payload: dict) -> dict:
        try:
            resp = requests.post(self.server_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning("send failed: %s", e)
            return {"error": str(e)}

    @staticmethod
    def _encode_image(image_bgr: np.ndarray) -> str:
        rgb = image_bgr[:, :, ::-1]
        im = Image.fromarray(rgb)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode("ascii")
