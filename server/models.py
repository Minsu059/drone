from pydantic import BaseModel
from typing import List, Optional


class AnalysisData(BaseModel):
    person_count: int = 0
    collapse_rate: float = 0.0
    road_status: str = "normal"
    fire_detected: bool = False
    fire_confidence: float = 0.0
    disaster_type: str = ""


class DroneData(BaseModel):
    drone_id: str
    type: str  # "position" or "disaster_report"
    lat: float
    lon: float
    alt: float = 0.0
    timestamp: float
    analysis: Optional[AnalysisData] = None
    image_base64: Optional[str] = None


class DetectionRow(BaseModel):
    class_name: str
    confidence: float
    bbox_xyxy: Optional[List[float]] = None


class DetectionBatch(BaseModel):
    drone_id: Optional[str] = None
    timestamp: Optional[float] = None
    inference_ms: Optional[int] = None
    detections: List[DetectionRow]


class ViewSlotRequest(BaseModel):
    slot_id: str
