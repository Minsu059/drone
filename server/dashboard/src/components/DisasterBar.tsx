/** 화면 하단 재난 목록 바 — 위험도순 가로 카드. 클릭 시 선택. */
import { useMemo } from 'react';
import type { VirtualDisaster } from '../data/mockData';
import { riskScoreToColor } from '../utils/coords';
import { computeRisk } from '../utils/risk';
import { TYPE_COLOR, TYPE_ICON } from '../utils/disasterMeta';

interface Props {
  disasters: VirtualDisaster[];
  focusedId: string | null;
  onSelect: (id: string) => void;
}

export function DisasterBar({ disasters, focusedId, onSelect }: Props) {
  const sorted = useMemo(
    () =>
      disasters
        .map((d) => ({ d, risk: computeRisk(d) }))
        .sort((a, b) => b.risk.total - a.risk.total),
    [disasters],
  );

  return (
    <div className="disaster-bar">
      <div className="disaster-bar-head">
        <span className="disaster-bar-title">재난 목록</span>
        <span className="disaster-bar-count">{disasters.length}건 · 위험도순</span>
      </div>
      <div className="disaster-bar-track">
        {sorted.map(({ d, risk }) => {
          const active = focusedId === d.id;
          const Icon = TYPE_ICON[d.disaster_type];
          return (
            <button
              key={d.id}
              type="button"
              className={`disaster-card${active ? ' active' : ''}`}
              onClick={() => onSelect(d.id)}
            >
              <span
                className="disaster-card-icon"
                style={{ background: TYPE_COLOR[d.disaster_type] }}
                aria-hidden
              >
                <Icon size={13} color="#fff" strokeWidth={2.4} />
              </span>
              <span className="disaster-card-name">{d.description}</span>
              <span
                className="disaster-card-score"
                style={{ color: riskScoreToColor(risk.total) }}
              >
                {risk.total}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
