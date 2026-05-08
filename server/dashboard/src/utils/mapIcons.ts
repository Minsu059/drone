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

const DISASTER_BADGE_PX = 32;
const DISASTER_GLYPH_PX = 18;
const DRONE_BADGE_PX = 28;

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

function droneIcon(): L.DivIcon {
  const html = `<div class="map-marker map-marker-drone">${DRONE_SVG}</div>`;
  return L.divIcon({
    html,
    className: 'map-marker-wrap',
    iconSize: [DRONE_BADGE_PX, DRONE_BADGE_PX],
    iconAnchor: [DRONE_BADGE_PX / 2, DRONE_BADGE_PX / 2],
    popupAnchor: [0, -DRONE_BADGE_PX / 2 + 2],
  });
}

// 모듈 레벨 캐시 — 매 렌더마다 재생성하지 않음
export const DRONE_ICON: L.DivIcon = droneIcon();
export const DISASTER_ICONS: Record<DisasterType, L.DivIcon> = {
  fire: disasterIcon('fire'),
  flood: disasterIcon('flood'),
  earthquake: disasterIcon('earthquake'),
  landslide: disasterIcon('landslide'),
};

// 사이드바·범례 등에서 React 컴포넌트로 직접 쓰고 싶을 때
export const DISASTER_LUCIDE: Record<DisasterType, LucideIcon> = DISASTER_ICON_COMP;
