/**
 * 재난 위험도 산정.
 *
 * 4개 항목 각 0~25점 → 총 0~100.
 * - 인명 (person_count): 10명 만점 (1명당 2.5점)
 * - 붕괴율 (collapse_rate, 0~100): 그대로 비율로 환산
 * - 화재 확신도 (fire_confidence, 0~1): 비율로 환산
 * - 도로 상태: blocked=25, congested=12, normal=0
 *
 * 가중치는 임의 결정. 실제 시연 데이터 기준으로 추후 조정.
 */

import type { VirtualDisaster, RoadStatus } from '../data/mockData';

export interface RiskItem {
  label: string;
  raw: string;
  score: number;
  max: number;
}

export interface RiskBreakdown {
  total: number;
  items: RiskItem[];
}

const ROAD_PENALTY: Record<RoadStatus, number> = {
  normal: 0,
  congested: 12,
  blocked: 25,
};

const ROAD_LABEL: Record<RoadStatus, string> = {
  normal: '정상',
  congested: '정체',
  blocked: '차단',
};

export function computeRisk(d: VirtualDisaster): RiskBreakdown {
  const personScore = Math.min(25, d.person_count * 2.5);
  const collapseScore = (d.collapse_rate / 100) * 25;
  const fireScore = d.fire_confidence * 25;
  const roadScore = ROAD_PENALTY[d.road_status];

  const items: RiskItem[] = [
    {
      label: '인명',
      raw: `${d.person_count}명`,
      score: Math.round(personScore),
      max: 25,
    },
    {
      label: '붕괴율',
      raw: `${d.collapse_rate.toFixed(0)}%`,
      score: Math.round(collapseScore),
      max: 25,
    },
    {
      label: '화재',
      raw: d.fire_detected
        ? `${(d.fire_confidence * 100).toFixed(0)}%`
        : '미감지',
      score: Math.round(fireScore),
      max: 25,
    },
    {
      label: '도로',
      raw: ROAD_LABEL[d.road_status],
      score: roadScore,
      max: 25,
    },
  ];

  const total = items.reduce((s, it) => s + it.score, 0);
  return { total, items };
}
