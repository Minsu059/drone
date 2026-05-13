from __future__ import annotations

from collections import Counter
import time
from pathlib import Path
from typing import List, Sequence

from .config import InferenceConfig
from .utils import detections_to_rows, draw_boxes


def _emit(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def _format_seconds(seconds: float) -> str:
    return f"{max(seconds, 0.0):.1f}s"


def _format_class_counts(rows: Sequence[dict]) -> str:
    class_counter = Counter(str(row.get("class_name", "unknown")) for row in rows)
    return ", ".join(
        f"{class_name}x{count}" for class_name, count in class_counter.most_common()
    )


def _format_detection_details(rows: Sequence[dict], top_k: int) -> str:
    if top_k <= 0 or not rows:
        return "-"

    top_rows = sorted(rows, key=lambda row: float(row.get("confidence", 0.0)), reverse=True)[
        :top_k
    ]
    detail_parts: List[str] = []
    for row in top_rows:
        class_name = str(row.get("class_name", "unknown"))
        confidence = float(row.get("confidence", 0.0))
        bbox = row.get("bbox_xyxy", [])
        detail_parts.append(f"{class_name}({confidence:.2f})@{bbox}")
    return " | ".join(detail_parts)


def install_inference_dependencies() -> None:
    import subprocess
    import sys

    packages = ["ultralytics", "opencv-python", "numpy"]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *packages])


def run_realtime_inference(cfg: InferenceConfig) -> None:
    import cv2

    try:
        from picamera2 import Picamera2
    except ImportError as exc:
        raise ImportError(
            "picamera2 is not installed. On Raspberry Pi OS run:\n"
            "sudo apt update && sudo apt install -y python3-picamera2"
        ) from exc

    from ultralytics import YOLO

    model_path = Path(cfg.model_path)
    if not model_path.is_absolute():
        model_path = (cfg.project_root / model_path).resolve()
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = YOLO(str(model_path))

    picam2 = Picamera2()
    camera_config = picam2.create_video_configuration(
        main={"size": (cfg.camera_width, cfg.camera_height), "format": "RGB888"}
    )
    picam2.configure(camera_config)
    picam2.start()
    time.sleep(1.0)

    frame_count = 0
    total_detections = 0
    status_frame_count = 0
    status_detection_count = 0

    session_start_perf = time.perf_counter()
    session_start_wall = time.time()
    last_status_ts = session_start_wall
    last_detection_log_ts = 0.0
    last_no_detection_log_ts = session_start_wall
    last_detection_seen_ts = session_start_wall
    status_interval_s = max(cfg.monitor_log_interval_s, 0.1)
    detection_log_interval_s = max(cfg.detection_log_interval_s, 0.0)
    no_detection_interval_s = max(cfg.no_detection_status_interval_s, 1.0)

    fps_ema = 0.0
    mode_text = "window" if cfg.show_window else "headless"
    stop_hint = "Press 'q' to quit." if cfg.show_window else "Press Ctrl+C to stop."
    _emit(
        "Realtime inference started | "
        f"mode={mode_text} model={model_path.name} "
        f"input={cfg.camera_width}x{cfg.camera_height} {stop_hint}"
    )

    try:
        while True:
            t0 = time.perf_counter()
            frame_rgb = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            results = model.predict(
                source=frame_bgr,
                imgsz=cfg.image_size,
                conf=cfg.conf_threshold,
                iou=cfg.iou_threshold,
                device=cfg.device,
                verbose=cfg.verbose,
            )
            result = results[0]
            rows: List[dict] = detections_to_rows(result, cfg.class_names)
            detection_count = len(rows)

            now_ts = time.time()
            frame_index = frame_count + 1
            frame_count = frame_index

            total_detections += detection_count
            status_frame_count += 1
            status_detection_count += detection_count

            annotated = draw_boxes(frame_bgr, result, cfg.class_names)
            latency_s = max(time.perf_counter() - t0, 1e-6)
            fps = 1.0 / latency_s
            fps_ema = fps if fps_ema == 0.0 else (0.9 * fps_ema + 0.1 * fps)

            if rows:
                last_detection_seen_ts = now_ts
                if now_ts - last_detection_log_ts >= detection_log_interval_s:
                    class_counts = _format_class_counts(rows)
                    top_row = max(rows, key=lambda row: float(row.get("confidence", 0.0)))
                    top_class_name = str(top_row.get("class_name", "unknown"))
                    top_confidence = float(top_row.get("confidence", 0.0))
                    details = _format_detection_details(rows, cfg.detection_detail_top_k)
                    _emit(
                        f"[DETECT] frame={frame_index} count={detection_count} "
                        f"classes={class_counts} top={top_class_name}({top_confidence:.2f})"
                    )
                    _emit(f"         details={details}")
                    last_detection_log_ts = now_ts
            else:
                idle_s = now_ts - last_detection_seen_ts
                if (
                    idle_s >= no_detection_interval_s
                    and now_ts - last_no_detection_log_ts >= no_detection_interval_s
                ):
                    _emit(
                        f"[NO_DETECT] frame={frame_index} idle={_format_seconds(idle_s)} "
                        f"conf>={cfg.conf_threshold:.2f}"
                    )
                    last_no_detection_log_ts = now_ts

            if now_ts - last_status_ts >= status_interval_s:
                elapsed_s = max(now_ts - session_start_wall, 1e-6)
                interval_s = max(now_ts - last_status_ts, 1e-6)
                avg_fps = frame_count / elapsed_s
                interval_fps = status_frame_count / interval_s
                idle_s = now_ts - last_detection_seen_ts
                state = "ACTIVE" if idle_s < no_detection_interval_s else "IDLE"

                _emit(
                    f"[STATUS] frame={frame_index} "
                    f"fps(inst={fps:.1f}, ema={fps_ema:.1f}, interval={interval_fps:.1f}, avg={avg_fps:.1f}) "
                    f"detections(interval={status_detection_count}, total={total_detections}) "
                    f"idle={_format_seconds(idle_s)} state={state}"
                )
                status_frame_count = 0
                status_detection_count = 0
                last_status_ts = now_ts

            cv2.putText(
                annotated,
                f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            if cfg.show_window:
                cv2.imshow(cfg.window_name, annotated)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

            if cfg.max_frames is not None and frame_count >= cfg.max_frames:
                break
    finally:
        elapsed_total_s = max(time.perf_counter() - session_start_perf, 1e-6)
        avg_total_fps = frame_count / elapsed_total_s if frame_count > 0 else 0.0
        _emit(
            f"[SUMMARY] frames={frame_count} elapsed={_format_seconds(elapsed_total_s)} "
            f"avg_fps={avg_total_fps:.1f} total_detections={total_detections}"
        )
        picam2.stop()
        if cfg.show_window:
            cv2.destroyAllWindows()
