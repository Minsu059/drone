/**
 * Dashboard 데이터 타입 정의.
 *
 * 데이터 자체는 백엔드 server/miniature_map.py 가 단일 진실 소스(SSOT).
 * /api/dashboard/wide, /api/dashboard/miniature 라우트로 fetch.
 * 이 파일은 타입만 보유하며, mock 상수는 더 이상 export하지 않음.
 *
 * 파일명이 mockData인 건 Phase 1 잔재 — 후속에서 src/types/dashboard.ts 등으로 이동 가능.
 */

export type LatLng = [number, number]; // [lat, lon] (Leaflet 표준)

// ============================================================
// 광역 뷰
// ============================================================

export interface VirtualDrone {
  drone_id: string;
  area: string;
  lat: number;
  lon: number;
}

export type DisasterType = 'fire' | 'flood' | 'earthquake' | 'landslide';
export type RoadStatus = 'normal' | 'congested' | 'blocked';

export interface VirtualDisaster {
  id: string;
  lat: number;
  lon: number;
  disaster_type: DisasterType;
  description: string;
  person_count: number;
  collapse_rate: number;
  fire_detected: boolean;
  fire_confidence: number;
  road_status: RoadStatus;
  /** 재난 영향 반경 (m). 광역 뷰 위험도 원 크기. */
  impact_radius_m: number;
}

export interface ZoneRisk {
  name: string;
  center: LatLng;
  risk_score: number; // 0~100
  has_miniature?: boolean;
}

// ============================================================
// 미니어처 뷰
// ============================================================

export interface MiniatureZone {
  key: string;
  name: string;
  center: LatLng;
  radius_m: number;
  description: string;
}

export interface MiniatureBuilding {
  zone: string;
  lat: number;
  lon: number;
  name: string;
  collapse_rate: number; // 0~100
}

export type MiniatureDisasterType = 'road_saturated' | 'road_damage' | 'fire';

export interface MiniatureDisaster {
  key: string;
  zone: string;
  lat: number;
  lon: number;
  type: MiniatureDisasterType;
  description: string;
}

export type RoadEdge = [string, string]; // [from_node, to_node]
