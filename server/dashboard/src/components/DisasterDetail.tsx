/** 우측 상세 패널 — 선택된 재난의 위험도 분석 + 구조 출동 정보. */
import { Truck, Route as RouteIcon, Clock } from 'lucide-react';
import type { VirtualDisaster } from '../data/mockData';
import type { RouteInfo } from '../api/dashboard';
import { riskScoreToColor } from '../utils/coords';
import { computeRisk } from '../utils/risk';
import { TYPE_LABEL, TYPE_COLOR, TYPE_ICON } from '../utils/disasterMeta';

interface Props {
  disaster: VirtualDisaster | null;
  route: RouteInfo | undefined;
}

export function DisasterDetail({ disaster, route }: Props) {
  if (!disaster) {
    return (
      <aside className="detail-panel detail-panel-empty">
        <div className="detail-empty-msg">
          지도의 재난 마커나
          <br />
          하단 목록에서 재난을 선택하세요
        </div>
      </aside>
    );
  }

  const risk = computeRisk(disaster);
  const Icon = TYPE_ICON[disaster.disaster_type];
  const hasRoute = route != null && route.fire_station != null;

  return (
    <aside className="detail-panel">
      <header className="detail-head">
        <span
          className="detail-icon"
          style={{ background: TYPE_COLOR[disaster.disaster_type] }}
          aria-hidden
        >
          <Icon size={18} color="#fff" strokeWidth={2.4} />
        </span>
        <div className="detail-head-text">
          <div className="detail-title">{disaster.description}</div>
          <div className="detail-sub">
            {TYPE_LABEL[disaster.disaster_type]} · 영향반경 {disaster.impact_radius_m}m
          </div>
        </div>
      </header>

      <section className="detail-section">
        <h3 className="detail-section-title">위험도 분석</h3>
        <table className="risk-table">
          <thead>
            <tr>
              <th>항목</th>
              <th>값</th>
              <th>점수</th>
            </tr>
          </thead>
          <tbody>
            {risk.items.map((it) => (
              <tr key={it.label}>
                <td>{it.label}</td>
                <td>{it.raw}</td>
                <td>
                  <b>{it.score}</b>
                  <span className="risk-max">/{it.max}</span>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={2}>종합 위험도</td>
              <td>
                <b style={{ color: riskScoreToColor(risk.total) }}>{risk.total}</b>
                <span className="risk-max">/100</span>
              </td>
            </tr>
          </tfoot>
        </table>
      </section>

      <section className="detail-section">
        <h3 className="detail-section-title">구조 출동</h3>
        {hasRoute ? (
          <div className="detail-dispatch">
            <div className="dispatch-row">
              <Truck size={15} className="dispatch-icon" />
              <span className="dispatch-label">출동 소방서</span>
              <b className="dispatch-value">{route!.fire_station}</b>
            </div>
            <div className="dispatch-row">
              <RouteIcon size={15} className="dispatch-icon" />
              <span className="dispatch-label">경로 거리</span>
              <b className="dispatch-value">
                {(route!.distance_m / 1000).toFixed(1)} km
              </b>
            </div>
            <div className="dispatch-row">
              <Clock size={15} className="dispatch-icon" />
              <span className="dispatch-label">예상 도착</span>
              <b className="dispatch-value">{route!.eta_min} 분</b>
            </div>
          </div>
        ) : (
          <div className="detail-nodispatch">경로 정보 없음</div>
        )}
      </section>
    </aside>
  );
}
