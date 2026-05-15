/**
 * Dashboard API client.
 * 백엔드 server/main.py 의 /api/dashboard/* 라우트와 1:1 매칭.
 * Vite dev 시에는 server.proxy 를 통해 :8000 으로 전달됨.
 */

import type { FeatureCollection } from 'geojson';
import type {
  LatLng,
  VirtualDisaster,
  ZoneRisk,
  MiniatureZone,
  MiniatureBuilding,
  MiniatureDisaster,
  RoadEdge,
} from '../data/mockData';

export interface ViewConfig {
  center: LatLng;
  zoom: number;
}

/** 도로 통제 포인트 — 재난 2차 피해로 통행 차단. 경로가 회피. */
export interface RoadBlockage {
  id: string;
  lat: number;
  lon: number;
  radius_m: number;
  status: string;
  type: string;
  description: string;
}

export interface WideDashboardResponse {
  view: ViewConfig;
  miniature_entry: ZoneRisk;
  road_blockages: RoadBlockage[];
}

export interface MiniatureDashboardResponse {
  view: ViewConfig;
  zones: MiniatureZone[];
  buildings: MiniatureBuilding[];
  disasters: MiniatureDisaster[];
  road_nodes: Record<string, LatLng>;
  road_edges: RoadEdge[];
  blocked_roads: RoadEdge[];
  congested_roads: RoadEdge[];
}

async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) {
    throw new Error(`${url} → ${r.status} ${r.statusText}`);
  }
  // 백엔드 SSOT — tuple/list 형태가 정확하다고 신뢰하고 캐스팅
  return (await r.json()) as T;
}

export function fetchWideDashboard(): Promise<WideDashboardResponse> {
  return getJSON<WideDashboardResponse>('/api/dashboard/wide');
}

export function fetchMiniatureDashboard(): Promise<MiniatureDashboardResponse> {
  return getJSON<MiniatureDashboardResponse>('/api/dashboard/miniature');
}

/** VWorld 읍면동 행정구역 경계 (emd_kor_nm 속성 보유). 광역 폴리곤 레이어용. */
export function fetchBoundary(): Promise<FeatureCollection> {
  return getJSON<FeatureCollection>('/api/dashboard/boundary');
}

/** 공공 인프라 1건 — 데이터셋별 부가 컬럼은 인덱스 시그니처로 수용. */
export interface InfraPoint {
  name: string;
  lat: number;
  lon: number;
  distance_m: number;
  [key: string]: string | number;
}

export interface InfraResponse {
  shelters: InfraPoint[];
  fire_stations: InfraPoint[];
  hospitals: InfraPoint[];
}

/** 공공 인프라 (대피소/소방서/병원, KAU 10km). 광역 토글 레이어용. */
export function fetchInfra(): Promise<InfraResponse> {
  return getJSON<InfraResponse>('/api/dashboard/infra');
}

/** 재난별 최근접 119안전센터 골든타임 경로 1건. */
export interface RouteInfo {
  disaster_id: string;
  fire_station: string | null;
  fire_station_lat?: number;
  fire_station_lon?: number;
  path: [number, number][];
  distance_m: number;
  eta_min: number;
}

/** 실시간 드론 위치 (라즈베리파이 position 송신 → drone_position 최신값). */
export interface LiveDrone {
  drone_id: string;
  lat: number;
  lon: number;
}

/** 라즈베리파이 실시간 재난 + 경로 + 드론 위치. 광역 뷰가 폴링. */
export interface DisastersResponse {
  disasters: VirtualDisaster[];
  routes: RouteInfo[];
  drones: LiveDrone[];
}

export function fetchDisasters(): Promise<DisastersResponse> {
  return getJSON<DisastersResponse>('/api/dashboard/disasters');
}

// ============================================================
// 미니어처 view_slot (누적 SVG 상태 + 수동 슬롯 전환)
// 백엔드 server/view_slot.py 와 1:1 매칭
// ============================================================

export type SlotKind = 'building' | 'road';
export type IncidentType = 'fallenTree' | 'traffic' | 'rubble';
export type BuildingId =
  | 'A' | 'B' | 'C' | 'D' | 'F' | 'G' | 'H' | 'I' | 'J';

export interface SlotMeta {
  slot_id: string;
  label: string;
  kind: SlotKind;
}

export interface SlotsListResponse {
  slots: SlotMeta[];
  active_slot_id: string;
}

export interface RoadIncident {
  id: string;
  type: IncidentType;
  x: number;
  y: number;
  labelX?: number;
  labelY?: number;
  intensity: number;
}

export interface RiskMapState {
  active_slot_id: string;
  buildings: Record<string, { collapseProbability: number }>;
  road_incidents: RoadIncident[];
  drone: { x: number; y: number };
}

async function postJSON<T>(url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    throw new Error(`${url} → ${r.status} ${r.statusText}`);
  }
  return (await r.json()) as T;
}

export function fetchSlotList(): Promise<SlotsListResponse> {
  return getJSON<SlotsListResponse>('/api/view-slot/slots');
}

export function fetchRiskMapState(): Promise<RiskMapState> {
  return getJSON<RiskMapState>('/api/view-slot/state');
}

export function setActiveSlot(slotId: string): Promise<RiskMapState> {
  return postJSON<RiskMapState>('/api/view-slot', { slot_id: slotId });
}

export function resetRiskMap(): Promise<RiskMapState> {
  return postJSON<RiskMapState>('/api/view-slot/reset');
}
