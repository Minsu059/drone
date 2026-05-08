import base64
import os

from fastapi import FastAPI
from fastapi.responses import Response
from models import DroneData
from database import init_db, get_connection

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

app = FastAPI(title="드론 재난 대응 시스템 API")

init_db()


@app.post("/api/drone-data")
async def receive_drone_data(data: DroneData):
    conn = get_connection()
    cursor = conn.cursor()

    if data.type == "position":
        cursor.execute(
            "INSERT INTO drone_position (drone_id, lat, lon, alt, timestamp) VALUES (?, ?, ?, ?, ?)",
            (data.drone_id, data.lat, data.lon, data.alt, data.timestamp),
        )
        conn.commit()
        conn.close()
        return {"status": "ok", "type": "position", "drone_id": data.drone_id}

    elif data.type == "disaster_report":
        analysis = data.analysis or {}
        if hasattr(analysis, "model_dump"):
            analysis = analysis.model_dump()

        cursor.execute(
            """INSERT INTO disaster_report
            (drone_id, lat, lon, alt, timestamp, person_count, collapse_rate,
             road_status, fire_detected, fire_confidence, disaster_type, image_base64)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.drone_id,
                data.lat,
                data.lon,
                data.alt,
                data.timestamp,
                analysis.get("person_count", 0),
                analysis.get("collapse_rate", 0.0),
                analysis.get("road_status", "normal"),
                int(analysis.get("fire_detected", False)),
                analysis.get("fire_confidence", 0.0),
                analysis.get("disaster_type", ""),
                data.image_base64,
            ),
        )
        conn.commit()
        report_id = cursor.lastrowid

        # 이미지가 있으면 파일로도 저장
        if data.image_base64:
            try:
                img_bytes = base64.b64decode(data.image_base64)
                img_path = os.path.join(IMAGES_DIR, f"report_{report_id}.jpg")
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
            except Exception:
                pass

        conn.close()
        return {"status": "ok", "type": "disaster_report", "drone_id": data.drone_id, "report_id": report_id}

    conn.close()
    return {"status": "error", "message": f"unknown type: {data.type}"}


@app.get("/api/positions/{drone_id}")
async def get_positions(drone_id: str, limit: int = 100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM drone_position WHERE drone_id = ? ORDER BY timestamp DESC LIMIT ?",
        (drone_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/reports")
async def get_reports(limit: int = 50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, drone_id, lat, lon, alt, timestamp, person_count, collapse_rate, road_status, fire_detected, fire_confidence, disaster_type, created_at FROM disaster_report ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/reports/{report_id}/image")
async def get_report_image(report_id: int):
    img_path = os.path.join(IMAGES_DIR, f"report_{report_id}.jpg")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return Response(content=f.read(), media_type="image/jpeg")
    return {"status": "error", "message": "image not found"}


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "서버 정상 동작 중"}
