"""시연 맵 초기화 명령어.

누적된 재난(disaster_report)과 드론 위치(drone_position) 데이터를 전부 삭제해
관제맵을 빈 초기 상태로 되돌린다. 시연을 다시 시작하기 전에 실행.

사용:
  python edge/scenario_reset.py                              # 로컬 메인서버
  python edge/scenario_reset.py --server-url http://192.168.0.10:8000
"""
from __future__ import annotations

import argparse
import sys

import requests


def main() -> int:
    p = argparse.ArgumentParser(description="시연 맵 초기화")
    p.add_argument("--server-url", default="http://127.0.0.1:8000",
                   help="메인서버 base URL (기본: http://127.0.0.1:8000)")
    args = p.parse_args()

    url = args.server_url.rstrip("/") + "/api/dashboard/reset"
    try:
        r = requests.post(url, timeout=10)
        r.raise_for_status()
        print(r.json().get("message", "초기화 완료"))
    except requests.RequestException as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
