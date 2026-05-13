from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Tuple

from .config import TrainConfig
from .utils import validate_yolo_dataset_structure, write_yolo_dataset_yaml


def install_training_dependencies() -> None:
    packages = ["ultralytics", "opencv-python", "pyyaml"]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *packages])


def prepare_dataset_yaml(cfg: TrainConfig) -> Path:
    dataset_root = (cfg.project_root / cfg.dataset_root).resolve()
    dataset_yaml = (cfg.project_root / cfg.dataset_yaml_path).resolve()
    validate_yolo_dataset_structure(dataset_root)
    return write_yolo_dataset_yaml(dataset_root, dataset_yaml, cfg.class_names)


def train_yolo26(cfg: TrainConfig) -> Tuple[Path, Path]:
    from ultralytics import YOLO

    dataset_yaml = prepare_dataset_yaml(cfg)
    project_dir = (cfg.project_root / cfg.project_dir).resolve()
    try:
        model = YOLO(cfg.model_name)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load model '{cfg.model_name}'. "
            "If your environment does not provide this checkpoint, set TrainConfig.model_name "
            "to a valid local path or a supported model name."
        ) from exc

    train_results = model.train(
        data=str(dataset_yaml),
        imgsz=cfg.image_size,
        epochs=cfg.epochs,
        batch=cfg.batch_size,
        workers=cfg.workers,
        device=cfg.device,
        project=str(project_dir),
        name=cfg.run_name,
        patience=cfg.patience,
        seed=cfg.seed,
        exist_ok=cfg.exist_ok,
        pretrained=cfg.pretrained,
        amp=cfg.amp,
    )

    if hasattr(train_results, "save_dir"):
        run_dir = Path(str(train_results.save_dir))
    else:
        run_dir = project_dir / cfg.run_name
    best_weights = run_dir / "weights" / "best.pt"
    return run_dir, best_weights


def export_model(weights_path: Path, export_format: str = "onnx") -> Path:
    from ultralytics import YOLO

    model = YOLO(str(weights_path))
    exported_path = model.export(format=export_format)
    return Path(str(exported_path))
