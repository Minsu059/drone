from pathlib import Path
from typing import List, Sequence


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _detect_val_split_name(dataset_root: Path) -> str:
    if (dataset_root / "valid").exists():
        return "valid"
    if (dataset_root / "val").exists():
        return "val"
    raise FileNotFoundError(
        "Validation folder not found. Expected either 'valid' or 'val' in dataset root."
    )


def validate_yolo_dataset_structure(dataset_root: Path) -> None:
    val_split = _detect_val_split_name(dataset_root)
    required_paths = [
        dataset_root / "train" / "images",
        dataset_root / "train" / "labels",
        dataset_root / val_split / "images",
        dataset_root / val_split / "labels",
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        missing_text = "\n".join(missing)
        raise FileNotFoundError(
            "Required YOLO dataset folders are missing:\n"
            f"{missing_text}\n"
            "Expected structure:\n"
            "dataset_root/train/images, dataset_root/train/labels, "
            "dataset_root/valid/images, dataset_root/valid/labels "
            "(or dataset_root/val/images, dataset_root/val/labels)"
        )


def write_yolo_dataset_yaml(
    dataset_root: Path, output_yaml_path: Path, class_names: Sequence[str]
) -> Path:
    ensure_dir(output_yaml_path.parent)
    val_split = _detect_val_split_name(dataset_root)
    lines = [
        f"path: {dataset_root.as_posix()}",
        "train: train/images",
        f"val: {val_split}/images",
    ]
    if (dataset_root / "test" / "images").exists():
        lines.append("test: test/images")

    lines.extend(
        [
            "",
            f"nc: {len(class_names)}",
            f"names: [{', '.join([repr(name) for name in class_names])}]",
            "",
        ]
    )

    yaml_text = "\n".join(lines)
    output_yaml_path.write_text(yaml_text, encoding="utf-8")
    return output_yaml_path


def detections_to_rows(result, class_names: Sequence[str]) -> List[dict]:
    rows: List[dict] = []
    if result.boxes is None or len(result.boxes) == 0:
        return rows

    for box in result.boxes:
        cls_idx = int(box.cls.item())
        conf = float(box.conf.item())
        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
        rows.append(
            {
                "class_id": cls_idx,
                "class_name": class_names[cls_idx] if cls_idx < len(class_names) else str(cls_idx),
                "confidence": round(conf, 4),
                "bbox_xyxy": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            }
        )
    return rows


def draw_boxes(frame_bgr, result, class_names: Sequence[str]):
    import cv2

    if result.boxes is None:
        return frame_bgr

    for box in result.boxes:
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        cls_idx = int(box.cls.item())
        conf = float(box.conf.item())
        class_name = class_names[cls_idx] if cls_idx < len(class_names) else str(cls_idx)
        label = f"{class_name} {conf:.2f}"

        cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (45, 215, 255), 2)
        cv2.rectangle(frame_bgr, (x1, max(0, y1 - 24)), (x2, y1), (45, 215, 255), -1)
        cv2.putText(
            frame_bgr,
            label,
            (x1 + 4, max(14, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (10, 10, 10),
            1,
            cv2.LINE_AA,
        )

    return frame_bgr
