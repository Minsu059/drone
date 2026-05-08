/**
 * Dashboard API client.
 * 백엔드 server/main.py 의 /api/dashboard/* 라우트와 1:1 매칭.
 * Vite dev 시에는 server.proxy 를 통해 :8000 으로 전달됨.
 */

import type {
  LatLng,
  VirtualDrone,
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

export interface WideDashboardResponse {
  view: ViewConfig;
  drones: VirtualDrone[];
  disasters: VirtualDisaster[];
  miniature_entry: ZoneRisk;
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
