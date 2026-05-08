import base64, time, requests

SERVER_URL = "http://172.30.1.69:8000/api/drone-data"

# 테스트용 빨간 사각형 이미지 생성 (카메라 없이)
from PIL import Image
import io

img = Image.new("RGB", (320, 240), color=(255, 0, 0))
buf = io.BytesIO()
img.save(buf, format="JPEG")
img_b64 = base64.b64encode(buf.getvalue()).decode()

print(f"image size: {len(buf.getvalue())} bytes")
print(f"base64 size: {len(img_b64)} chars")

payload = {
    "drone_id": "drone-01",
    "type": "disaster_report",
    "lat": 37.5665, "lon": 126.9780, "alt": 50.0,
    "timestamp": time.time(),
    "analysis": {
        "person_count": 5,
        "collapse_rate": 80.0,
        "road_status": "blocked",
        "fire_detected": True,
        "fire_confidence": 0.95,
        "disaster_type": "earthquake",
    },
    "image_base64": img_b64,
}

resp = requests.post(SERVER_URL, json=payload, timeout=10)
print(f"response: {resp.json()}")
report_id = resp.json().get("report_id")
print(f"\ncheck image: http://172.30.1.69:8000/api/reports/{report_id}/image")
