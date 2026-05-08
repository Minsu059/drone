"""Edge 메인 루프: 카메라 → 분류 → 트리거 → 송신.

mock 모드 사용 예:
  python -m edge.pipeline.loop \
      --server-url http://192.168.0.10:8000/api/drone-data \
      --interval 3 --max-iters 9 --order scenario_sequence

실제 모드(B1/B2 인계 후)에서는 MockCameraSource → PiCameraSource,
MockClassifier → TFLiteClassifier 로 교체하고 manifest 인자를 제거한다.
"""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from edge.camera.mock import MockCameraSource
from edge.classifier.mock import MockClassifier

from .gps import MockGPS
from .sender import ReportSender
from .trigger import should_trigger

logger = logging.getLogger(__name__)

DEFAULT_MANIFEST = Path(__file__).resolve().parent.parent / "fixtures" / "manifest.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Edge pipeline (mock)")
    p.add_argument("--server-url", required=True,
                   help="예: http://192.168.0.10:8000/api/drone-data")
    p.add_argument("--drone-id", default="drone-01")
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--interval", type=float, default=3.0, help="송신 주기(초)")
    p.add_argument("--order", choices=["round_robin", "scenario_sequence"],
                   default="round_robin")
    p.add_argument("--no-image", action="store_true",
                   help="disaster_report 에 이미지 첨부 안 함 (디버깅용)")
    p.add_argument("--max-iters", type=int, default=0,
                   help="최대 반복 수 (0=무한)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    cam = MockCameraSource(args.manifest, order=args.order)
    clf = MockClassifier(args.manifest)
    gps = MockGPS()
    sender = ReportSender(args.server_url, drone_id=args.drone_id)

    logger.info("loop start (server=%s, interval=%.1fs, order=%s)",
                args.server_url, args.interval, args.order)

    n = 0
    try:
        while True:
            try:
                frame = cam.read()
            except RuntimeError as e:
                logger.info("camera exhausted: %s", e)
                break

            meta = {"source_id": frame.source_id, "scenario": frame.scenario}
            result = clf.classify(frame.image, meta)
            pos = gps.read()

            pos_resp = sender.send_position(pos)
            line_pos = f"[POS] lat={pos.lat:.5f} lon={pos.lon:.5f} -> {pos_resp}"

            if should_trigger(result):
                image = None if args.no_image else frame.image
                dis_resp = sender.send_disaster(pos, result, image=image)
                line_dis = f"[DIS] {frame.scenario} -> {dis_resp}"
            else:
                line_dis = "(no trigger)"

            logger.info("%s | %s", line_pos, line_dis)

            n += 1
            if args.max_iters and n >= args.max_iters:
                logger.info("max-iters reached (%d)", n)
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("interrupted")

    cam.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
