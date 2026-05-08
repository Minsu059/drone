import time, random, requests

SERVER_URL = "http://172.30.1.69:8000/api/drone-data"
DRONE_ID = "drone-01"

lat, lon = 37.5665, 126.9780
count = 0

print(f"Server: {SERVER_URL}")
print("Ctrl+C to stop\n")

try:
    while True:
        lat += random.uniform(-0.0005, 0.0005)
        lon += random.uniform(-0.0005, 0.0005)

        payload = {"drone_id": DRONE_ID, "type": "position",
                   "lat": lat, "lon": lon, "alt": 50.0, "timestamp": time.time()}
        resp = requests.post(SERVER_URL, json=payload, timeout=5)
        print(f"[POS] lat={lat:.4f}, lon={lon:.4f} -> {resp.json()}")

        count += 1
        if count % 5 == 0:
            analysis = {
                "person_count": random.randint(0, 10),
                "collapse_rate": round(random.uniform(0, 100), 1),
                "road_status": random.choice(["normal", "congested", "blocked"]),
                "fire_detected": random.choice([True, False]),
                "fire_confidence": round(random.uniform(0.5, 1.0), 2),
                "disaster_type": random.choice(["earthquake", "flood", "fire", "landslide"]),
            }
            payload2 = {"drone_id": DRONE_ID, "type": "disaster_report",
                        "lat": lat, "lon": lon, "alt": 50.0,
                        "timestamp": time.time(), "analysis": analysis}
            resp2 = requests.post(SERVER_URL, json=payload2, timeout=5)
            print(f"[DST] person={analysis['person_count']}, collapse={analysis['collapse_rate']}% -> {resp2.json()}")

        time.sleep(3)
except KeyboardInterrupt:
    print("\nDone")
