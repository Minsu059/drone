import { useMemo } from 'react';
import {
  Flame,
  Droplets,
  Activity,
  Mountain,
  type LucideIcon,
} from 'lucide-react';
import { type VirtualDisaster, type DisasterType, type RoadStatus } from '../data/mockData';
import { riskScoreToColor } from '../utils/coords';
import { computeRisk } from '../utils/risk';

const TYPE_LABEL: Record<DisasterType, string> = {
  fire: '화재',
  flood: '침수',
  earthquake: '지진',
  landslide: '산사태',
};

const TYPE_COLOR: Record<DisasterType, string> = {
  fire: '#dc2626',
  flood: '#2563eb',
  earthquake: '#a16207',
  landslide: '#7c3aed',
};

const TYPE_ICON: Record<DisasterType, LucideIcon> = {
  fire: Flame,
  flood: Droplets,
  earthquake: Activity,
  landslide: Mountain,
};

const ROAD_LABEL: Record<RoadStatus, string> = {
  normal: '도로 정상',
  congested: '도로 정체',
  blocked: '도로 차단',
};

interface Props {
  disasters: VirtualDisaster[];
  focusedId: string | null;
  onSelect: (id: string) => void;
}

export function DisasterSidebar({ disasters, focusedId, onSelect }: Props) {
  const sorted = useMemo(
    () =>
      disasters
        .map((d) => ({ d, risk: computeRisk(d) }))
        .sort((a, b) => b.risk.total - a.risk.total),
    [disasters],
  );

  return (
    <aside className="sidebar">
      <header className="sidebar-header">
        <h2 className="sidebar-title">재난 목록</h2>
        <span className="sidebar-count">{disasters.length}건</span>
      </header>
      <div className="sidebar-hint">위험도 내림차순 · 행 클릭 시 지도 이동</div>
      <ul className="disaster-list">
        {sorted.map(({ d, risk }) => {
          const active = focusedId === d.id;
          const scoreColor = riskScoreToColor(risk.total);
          const Icon = TYPE_ICON[d.disaster_type];
          return (
            <li
              key={d.id}
              className={`disaster-item${active ? ' active' : ''}`}
              onClick={() => onSelect(d.id)}
            >
              <span
                className="disaster-icon-wrap"
                style={{ background: TYPE_COLOR[d.disaster_type] }}
                aria-hidden
              >
                <Icon size={14} color="#fff" strokeWidth={2.4} />
              </span>
              <div className="disaster-main">
                <div className="disaster-name">{d.description}</div>
                <div className="disaster-meta">
                  {TYPE_LABEL[d.disaster_type]} · 인명 {d.person_count}명 ·{' '}
                  {ROAD_LABEL[d.road_status]}
                </div>
              </div>
              <div className="disaster-score" style={{ color: scoreColor }}>
                <span className="score-num">{risk.total}</span>
                <span className="score-max">/100</span>
              </div>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
