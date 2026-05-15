/**
 * Leaflet divIcon (HTML 기반) 생성기.
 * Lucide React 아이콘을 정적 SVG 문자열로 렌더링하여 마커에 삽입.
 */

import L from 'leaflet';
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement, type ComponentType } from 'react';
import {
  Flame,
  Droplets,
  Activity,
  Mountain,
  Hospital,
  Construction,
  type LucideProps,
} from 'lucide-react';
import type { DisasterType } from '../data/mockData';

type LucideIcon = ComponentType<LucideProps>;

const DISASTER_ICON_COMP: Record<DisasterType, LucideIcon> = {
  fire: Flame,
  flood: Droplets,
  earthquake: Activity,
  landslide: Mountain,
};

const DISASTER_BG: Record<DisasterType, string> = {
  fire: '#dc2626',
  flood: '#2563eb',
  earthquake: '#a16207',
  landslide: '#7c3aed',
};

const DISASTER_BADGE_PX = 42;
const DISASTER_GLYPH_PX = 24;
const DRONE_BADGE_PX = 46;

function lucideSvg(Comp: LucideIcon, size: number): string {
  return renderToStaticMarkup(
    createElement(Comp, {
      size,
      color: '#ffffff',
      strokeWidth: 2.4,
    }),
  );
}

function disasterIcon(type: DisasterType): L.DivIcon {
  const svg = lucideSvg(DISASTER_ICON_COMP[type], DISASTER_GLYPH_PX);
  const bg = DISASTER_BG[type];
  const html = `<div class="map-marker map-marker-${type}" style="background:${bg}">${svg}</div>`;
  return L.divIcon({
    html,
    className: 'map-marker-wrap',
    iconSize: [DISASTER_BADGE_PX, DISASTER_BADGE_PX],
    iconAnchor: [DISASTER_BADGE_PX / 2, DISASTER_BADGE_PX / 2],
    popupAnchor: [0, -DISASTER_BADGE_PX / 2 + 2],
  });
}

const DRONE_SVG = `
<svg viewBox="0 0 24 24" fill="none" width="${DRONE_BADGE_PX - 8}" height="${DRONE_BADGE_PX - 8}" xmlns="http://www.w3.org/2000/svg" stroke-linecap="round">
  <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="1.5"/>
  <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="6" cy="6" r="2.5" fill="currentColor" opacity="0.85"/>
  <circle cx="18" cy="6" r="2.5" fill="currentColor" opacity="0.85"/>
  <circle cx="6" cy="18" r="2.5" fill="currentColor" opacity="0.85"/>
  <circle cx="18" cy="18" r="2.5" fill="currentColor" opacity="0.85"/>
  <rect x="9.5" y="9.5" width="5" height="5" rx="1" fill="currentColor"/>
</svg>
`.trim();

function droneIcon(extraClass: string, wrapClass: string): L.DivIcon {
  const html = `<div class="map-marker ${extraClass}">${DRONE_SVG}</div>`;
  return L.divIcon({
    html,
    className: wrapClass,
    iconSize: [DRONE_BADGE_PX, DRONE_BADGE_PX],
    iconAnchor: [DRONE_BADGE_PX / 2, DRONE_BADGE_PX / 2],
    popupAnchor: [0, -DRONE_BADGE_PX / 2 + 2],
  });
}

// 라즈베리파이 실시간 드론 — 파란 배지. live-drone-move 클래스로 위치 변경 시
// transform transition 을 걸어 폴링 간 이동을 매끄럽게 표현.
export const LIVE_DRONE_ICON: L.DivIcon = droneIcon(
  'map-marker-live-drone',
  'map-marker-wrap live-drone-move',
);
export const DISASTER_ICONS: Record<DisasterType, L.DivIcon> = {
  fire: disasterIcon('fire'),
  flood: disasterIcon('flood'),
  earthquake: disasterIcon('earthquake'),
  landslide: disasterIcon('landslide'),
};

// 사이드바·범례 등에서 React 컴포넌트로 직접 쓰고 싶을 때
export const DISASTER_LUCIDE: Record<DisasterType, LucideIcon> = DISASTER_ICON_COMP;

// ============================================================
// 공공 인프라 마커 (소방서·병원). 대피소는 수가 많아 CircleMarker 사용.
// ============================================================

export type InfraKind = 'fire_station' | 'hospital';

const INFRA_BADGE_PX = 28;
const INFRA_GLYPH_PX = 16;

// 병원 — Hospital 아이콘 배지 (파랑)
function hospitalIcon(): L.DivIcon {
  const svg = lucideSvg(Hospital, INFRA_GLYPH_PX);
  const html = `<div class="map-marker map-marker-infra" style="background:#2563eb">${svg}</div>`;
  return L.divIcon({
    html,
    className: 'map-marker-wrap',
    iconSize: [INFRA_BADGE_PX, INFRA_BADGE_PX],
    iconAnchor: [INFRA_BADGE_PX / 2, INFRA_BADGE_PX / 2],
    popupAnchor: [0, -INFRA_BADGE_PX / 2 + 2],
  });
}

// 소방서 — "119" 텍스트 pill (아이콘보다 가시성 ↑)
const FIRE_PILL_W = 38;
const FIRE_PILL_H = 22;
function fireStationIcon(): L.DivIcon {
  const html = `<div class="map-marker-119">119</div>`;
  return L.divIcon({
    html,
    className: 'map-marker-wrap',
    iconSize: [FIRE_PILL_W, FIRE_PILL_H],
    iconAnchor: [FIRE_PILL_W / 2, FIRE_PILL_H / 2],
    popupAnchor: [0, -FIRE_PILL_H / 2 + 2],
  });
}

// 대피소 CircleMarker 색상 (노랑)
export const SHELTER_COLOR = '#facc15';
export const SHELTER_STROKE = '#a16207';

export const INFRA_ICONS: Record<InfraKind, L.DivIcon> = {
  fire_station: fireStationIcon(),
  hospital: hospitalIcon(),
};

// 도로 통제 포인트 — 주황 경고 배지
const BLOCKAGE_BADGE_PX = 26;
function blockageIcon(): L.DivIcon {
  const svg = lucideSvg(Construction, 15);
  const html = `<div class="map-marker map-marker-blockage" style="background:#ea580c">${svg}</div>`;
  return L.divIcon({
    html,
    className: 'map-marker-wrap',
    iconSize: [BLOCKAGE_BADGE_PX, BLOCKAGE_BADGE_PX],
    iconAnchor: [BLOCKAGE_BADGE_PX / 2, BLOCKAGE_BADGE_PX / 2],
    popupAnchor: [0, -BLOCKAGE_BADGE_PX / 2 + 2],
  });
}

export const BLOCKAGE_COLOR = '#ea580c';
export const BLOCKAGE_ICON: L.DivIcon = blockageIcon();
