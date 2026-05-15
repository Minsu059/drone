/** 재난 타입별 표시 메타 — 라벨/색상/아이콘. 여러 컴포넌트 공용. */
import { Flame, Droplets, Activity, Mountain, type LucideIcon } from 'lucide-react';
import type { DisasterType } from '../data/mockData';

export const TYPE_LABEL: Record<DisasterType, string> = {
  fire: '화재',
  flood: '침수',
  earthquake: '지진',
  landslide: '산사태',
};

export const TYPE_COLOR: Record<DisasterType, string> = {
  fire: '#dc2626',
  flood: '#2563eb',
  earthquake: '#a16207',
  landslide: '#7c3aed',
};

export const TYPE_ICON: Record<DisasterType, LucideIcon> = {
  fire: Flame,
  flood: Droplets,
  earthquake: Activity,
  landslide: Mountain,
};
