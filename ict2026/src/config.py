from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# Dataset Classes
DISASTER_CLASSES: List[str] = [
    "earthquake_building_level0",
    "earthquake_building_level2",
    "road_collapse_level0",
    "road_collapse_level2",
    "traffic_congestion_level0",
    "traffic_congestion_level2",
    "typhoon_tree_level0",
    "typhoon_tree_level2",
    "rock",
]


@dataclass
class TrainConfig:
    project_root: Path = Path(".")
    dataset_root: Path = Path("data/disaster_dataset")
    dataset_yaml_path: Path = Path("data/disaster_dataset/data.yaml")
    class_names: List[str] = field(default_factory=lambda: DISASTER_CLASSES.copy())
    model_name: str = "yolo26n.pt"
    image_size: int = 512
    epochs: int = 100
    batch_size: int = 16
    workers: int = 4
    device: str = "0"
    project_dir: Path = Path("runs/detect")
    run_name: str = "yolo26_disaster_detector"
    patience: int = 20
    seed: int = 42
    exist_ok: bool = True
    pretrained: bool = True
    amp: bool = True


@dataclass
class InferenceConfig:
    project_root: Path = Path(".")
    model_path: Path = Path("runs/detect/yolo26_disaster_detector/weights/best.pt")
    class_names: List[str] = field(default_factory=lambda: DISASTER_CLASSES.copy())
    image_size: int = 512
    conf_threshold: float = 0.25
    iou_threshold: float = 0.45
    device: str = "cpu"
    camera_width: int = 1280
    camera_height: int = 720
    show_window: bool = True
    window_name: str = "YOLO26 Disaster Detection (Press q to quit)"
    verbose: bool = False
    max_frames: Optional[int] = None
    monitor_log_interval_s: float = 1.0
    detection_log_interval_s: float = 0.3
    no_detection_status_interval_s: float = 5.0
    detection_detail_top_k: int = 3
