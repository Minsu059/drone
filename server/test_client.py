"""
라즈베리파이 → 서버 전송 테스트 스크립트
가상 GPS + 가상 분류 데이터를 서버에 POST한다.
라즈베리파이에서 실행: python3 test_client.py

사용 전 SERVER_URL의 IP를 데스크탑 IP로 변경할 것.
"""

import time
import random
import requests

# ===== 설정 =====
SERVER_URL = "http://서버IP:8000/api/drone-data"  # 데스크탑 IP로 변경
DRONE_ID = "drone-01"
SEND_INTERVAL = 3  # 초

# 시작 좌표 (서울시청 부근)
lat = 37.5665
lon = 126.9780


def send_position(lat, lon):
    """현재 위치 전송 (주기적)"""
    payload = {
        "drone_id": DRONE_ID,
        "type": "position",
        "lat": lat,
        "lon": lon,
        "alt": 50.0,
        "timestamp": time.time(),
    }
    resp = requests.post(SERVER_URL, json=payload, timeout=5)
    print(f"[위치] lat={lat:.4f}, lon={lon:.4f} → {resp.json()}")


def send_disaster_report(lat, lon):
    """재난 분석 데이터 전송 (가상)"""
    payload = {
        "drone_id": DRONE_ID,
        "type": "disaster_report",
        "lat": lat,
        "lon": lon,
        "alt": 50.0,
        "timestamp": time.time(),
        "analysis": {
            "person_count": random.randint(0, 10),
            "collapse_rate": round(random.uniform(0, 100), 1),
            "road_status": random.choice(["normal", "congested", "blocked"]),
            "fire_detected": random.choice([True, False]),
            "fire_confidence": round(random.uniform(0.5, 1.0), 2),
            "disaster_type": random.choice(["earthquake", "flood", "fire", "landslide"]),
        },
    }
    resp = requests.post(SERVER_URL, json=payload, timeout=5)
    print(f"[재난] person={payload['analysis']['person_count']}, "
          f"collapse={payload['analysis']['collapse_rate']}%, "
          f"fire={payload['analysis']['fire_detected']} → {resp.json()}")


if __name__ == "__main__":
    print(f"서버: {SERVER_URL}")
    print(f"드론: {DRONE_ID}")
    print(f"전송 간격: {SEND_INTERVAL}초")
    print("Ctrl+C로 종료\n")

    count = 0
    try:
        while True:
            # 가상 GPS 이동
            lat += random.uniform(-0.0005, 0.0005)
            lon += random.uniform(-0.0005, 0.0005)

            # 매번 위치 전송
            send_position(lat, lon)

            # 5회마다 재난 분석 데이터도 전송
            count += 1
            if count % 5 == 0:
                send_disaster_report(lat, lon)

            time.sleep(SEND_INTERVAL)

    except KeyboardInterrupt:
        print("\n전송 종료")
