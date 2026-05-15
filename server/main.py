import base64
import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi import HTTPException
from models import DroneData, DetectionBatch, ViewSlotRequest
from database import init_db, get_connection
import miniature_map as mm
import view_slot as vs
import routing

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

app = FastAPI(title="드론 재난 대응 시스템 API")

# CORS — Vite dev (5173) + 빌드 후 동일 호스트(8000) 모두 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

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


# ============================================================
# Dashboard 라우트 — 정적 가상 데이터를 frontend에 노출
# 데이터 소스: miniature_map.py (SSOT)
# ============================================================

@app.get("/api/dashboard/wide")
async def dashboard_wide():
    return {
        "view": {
            "center": list(mm.WIDE_VIEW["center"]),
            "zoom": mm.WIDE_VIEW["zoom"],
        },
        "drones": mm.VIRTUAL_DRONES,
        "disasters": mm.VIRTUAL_DISASTERS,
        "miniature_entry": {
            **mm.MINIATURE_ENTRY_POINT,
            "center": list(mm.MINIATURE_ENTRY_POINT["center"]),
        },
    }


_BOUNDARY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "admin_boundary_kau_region.geojson"
)


def _load_boundary() -> dict:
    """VWorld 행정구역 GeoJSON. 파일 없으면 빈 FeatureCollection."""
    try:
        with open(_BOUNDARY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"type": "FeatureCollection", "features": []}


# 모듈 로드 시 1회만 디스크에서 읽어 캐싱 (1MB, 정적 데이터)
_BOUNDARY_CACHE = _load_boundary()


@app.get("/api/dashboard/boundary")
async def dashboard_boundary():
    """KAU 인근 읍면동 행정구역 경계 (VWorld). 광역 뷰 폴리곤 레이어용."""
    return _BOUNDARY_CACHE


_INFRA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "public")
_INFRA_FILES = {
    "shelters": "shelters_kau_10km.json",
    "fire_stations": "fire_stations_kau_10km.json",
    "hospitals": "hospitals_kau_10km.json",
}


def _load_infra() -> dict:
    """공공 인프라 (대피소/소방서/병원) — filter_public_data.py 산출물.
    파일 없으면 해당 키는 빈 리스트."""
    result: dict = {}
    for key, fname in _INFRA_FILES.items():
        try:
            with open(os.path.join(_INFRA_DIR, fname), encoding="utf-8") as f:
                result[key] = json.load(f)
        except FileNotFoundError:
            result[key] = []
    return result


_INFRA_CACHE = _load_infra()


@app.get("/api/dashboard/infra")
async def dashboard_infra():
    """공공 인프라 — 대피소/소방서/병원 (KAU 10km). 광역 뷰 토글 레이어용."""
    return _INFRA_CACHE


# 경로 추론 — 각 재난별 최근접 119안전센터 골든타임 경로 (서버 시작 시 1회 계산)
_ROUTES_CACHE = routing.compute_routes(
    mm.VIRTUAL_DISASTERS, _INFRA_CACHE["fire_stations"]
)


@app.get("/api/dashboard/routes")
async def dashboard_routes():
    """각 재난 → 최근접 119안전센터 경로 (차단/정체 회피). 광역 경로 레이어용."""
    return {"routes": _ROUTES_CACHE}


@app.get("/api/dashboard/miniature")
async def dashboard_miniature():
    return {
        "view": {
            "center": list(mm.MINIATURE_VIEW["center"]),
            "zoom": mm.MINIATURE_VIEW["zoom"],
        },
        "zones": [
            {**z, "center": list(z["center"])} for z in mm.MINIATURE_ZONES
        ],
        "buildings": mm.MINIATURE_BUILDINGS,
        "disasters": mm.MINIATURE_DISASTERS,
        "road_nodes": {k: list(v) for k, v in mm.MINIATURE_ROAD_NODES.items()},
        "road_edges": [list(e) for e in mm.MINIATURE_ROAD_EDGES],
        "blocked_roads": [list(e) for e in mm.MINIATURE_BLOCKED_ROADS],
        "congested_roads": [list(e) for e in mm.MINIATURE_CONGESTED_ROADS],
    }


# ============================================================
# 미니어처 view_slot — 누적 SVG 상태 + 수동 슬롯 전환
# ============================================================

@app.get("/api/view-slot/slots")
async def view_slot_list():
    """대시보드 슬롯 버튼 패널이 받을 메타 목록."""
    return {"slots": vs.list_slots(), "active_slot_id": vs.get_map_state()["active_slot_id"]}


@app.get("/api/view-slot/state")
async def view_slot_state():
    """누적된 미니어처 SVG 상태 (sections/buildings/road_incidents/drone)."""
    return vs.get_map_state()


@app.post("/api/view-slot")
async def view_slot_set(req: ViewSlotRequest):
    try:
        return vs.set_active_slot(req.slot_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/view-slot/reset")
async def view_slot_reset():
    return vs.reset()


@app.post("/api/detections")
async def receive_detections(batch: DetectionBatch):
    """edge가 보낸 detection rows를 현재 활성 슬롯으로 태깅 + 누적 갱신."""
    rows = [d.model_dump() for d in batch.detections]
    applied = vs.apply_detections(rows)
    return {"status": "ok", "applied": applied, "state": vs.get_map_state()}
