import { useMemo } from 'react';
import {
  MINIATURE_ZONES,
  MINIATURE_BUILDINGS,
  MINIATURE_DISASTERS,
  MINIATURE_ROAD_NODES,
  MINIATURE_ROAD_EDGES,
  MINIATURE_BLOCKED_ROADS,
  MINIATURE_CONGESTED_ROADS,
  type RoadEdge,
  type MiniatureDisasterType,
} from '../data/mockData';
import { collapseRateToColor } from '../utils/coords';

const SVG_W = 1200;
const SVG_H = 800;
const PAD = 80;
const METER_PER_DEG_LAT = 111_000;

const DISASTER_COLOR: Record<MiniatureDisasterType, string> = {
  road_saturated: '#f59e0b',
  road_damage: '#7c2d12',
  fire: '#dc2626',
};

const DISASTER_LABEL: Record<MiniatureDisasterType, string> = {
  road_saturated: '도로 포화',
  road_damage: '도로 파괴',
  fire: '화재',
};

function ek(e: RoadEdge): string {
  return `${e[0]}-${e[1]}`;
}

function buildProjection() {
  const allLats: number[] = [];
  const allLons: number[] = [];

  Object.values(MINIATURE_ROAD_NODES).forEach(([la, lo]) => {
    allLats.push(la);
    allLons.push(lo);
  });
  MINIATURE_ZONES.forEach((z) => {
    allLats.push(z.center[0]);
    allLons.push(z.center[1]);
  });
  MINIATURE_BUILDINGS.forEach((b) => {
    allLats.push(b.lat);
    allLons.push(b.lon);
  });
  MINIATURE_DISASTERS.forEach((d) => {
    allLats.push(d.lat);
    allLons.push(d.lon);
  });

  const latMin = Math.min(...allLats);
  const latMax = Math.max(...allLats);
  const lonMin = Math.min(...allLons);
  const lonMax = Math.max(...allLons);

  const innerW = SVG_W - 2 * PAD;
  const innerH = SVG_H - 2 * PAD;
  const svgPerMeter = innerH / ((latMax - latMin) * METER_PER_DEG_LAT);

  function gps(lat: number, lon: number): [number, number] {
    const x = PAD + ((lon - lonMin) / (lonMax - lonMin)) * innerW;
    const y = PAD + ((latMax - lat) / (latMax - latMin)) * innerH;
    return [x, y];
  }

  function meters(m: number): number {
    return m * svgPerMeter;
  }

  return { gps, meters };
}

export function MiniatureView() {
  const { gps, meters } = useMemo(() => buildProjection(), []);
  const blockedSet = useMemo(
    () => new Set(MINIATURE_BLOCKED_ROADS.map(ek)),
    [],
  );
  const congestedSet = useMemo(
    () => new Set(MINIATURE_CONGESTED_ROADS.map(ek)),
    [],
  );

  return (
    <div className="miniature-canvas">
      <div className="miniature-bg-placeholder">
        미니어처 사진 자리 — 실물 배송 후 배경 이미지로 교체
      </div>

      <svg
        className="miniature-svg"
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <pattern id="mini-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="1" />
          </pattern>
        </defs>

        {/* 그리드 (이후 미니어처 사진으로 교체 시 이 rect 두 개를 <image>로) */}
        <rect width={SVG_W} height={SVG_H} fill="#0b1220" />
        <rect width={SVG_W} height={SVG_H} fill="url(#mini-grid)" />

        {/* 구역 (점선 원 + 라벨) */}
        {MINIATURE_ZONES.map((z) => {
          const [cx, cy] = gps(z.center[0], z.center[1]);
          const r = meters(z.radius_m);
          return (
            <g key={`zone-${z.key}`}>
              <circle
                cx={cx}
                cy={cy}
                r={r}
                fill="rgba(59, 130, 246, 0.05)"
                stroke="#3b82f6"
                strokeWidth={1}
                strokeDasharray="4 4"
              />
              <text
                x={cx}
                y={cy - r + 18}
                textAnchor="middle"
                className="zone-label"
              >
                {z.key}구역
              </text>
            </g>
          );
        })}

        {/* 도로 엣지 */}
        {MINIATURE_ROAD_EDGES.map((e) => {
          const [n1lat, n1lon] = MINIATURE_ROAD_NODES[e[0]];
          const [n2lat, n2lon] = MINIATURE_ROAD_NODES[e[1]];
          const [x1, y1] = gps(n1lat, n1lon);
          const [x2, y2] = gps(n2lat, n2lon);
          const k = ek(e);
          const blocked = blockedSet.has(k);
          const congested = congestedSet.has(k);
          const stroke = blocked ? '#dc2626' : congested ? '#f59e0b' : '#64748b';
          const w = blocked ? 5 : congested ? 4 : 3;
          const dash = blocked ? '10 6' : undefined;
          const status = blocked ? '차단' : congested ? '정체' : '정상';
          return (
            <line
              key={k}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={stroke}
              strokeWidth={w}
              strokeDasharray={dash}
              strokeLinecap="round"
              opacity={0.9}
            >
              <title>{`도로 ${e[0]} ↔ ${e[1]}\n상태: ${status}`}</title>
            </line>
          );
        })}

        {/* 노드 */}
        {Object.entries(MINIATURE_ROAD_NODES).map(([id, [la, lo]]) => {
          const [cx, cy] = gps(la, lo);
          return (
            <g key={`node-${id}`}>
              <circle
                cx={cx}
                cy={cy}
                r={4}
                fill="#f1f5f9"
                stroke="#334155"
                strokeWidth={1.5}
              />
              <title>{`노드 ${id}`}</title>
            </g>
          );
        })}

        {/* 건물 (사각형, 붕괴율 색상) */}
        {MINIATURE_BUILDINGS.map((b) => {
          const [cx, cy] = gps(b.lat, b.lon);
          const color = collapseRateToColor(b.collapse_rate);
          const size = 30;
          return (
            <g key={`bldg-${b.name}`} className="building">
              <rect
                x={cx - size / 2}
                y={cy - size / 2}
                width={size}
                height={size}
                rx={3}
                fill={color}
                stroke="#0f172a"
                strokeWidth={2}
                opacity={0.92}
              />
              <text
                x={cx}
                y={cy + 4}
                textAnchor="middle"
                className="building-label"
              >
                {b.zone}
              </text>
              <title>{`${b.name}\n구역 ${b.zone}\n붕괴율 ${b.collapse_rate}%`}</title>
            </g>
          );
        })}

        {/* 재난 (강조 원 + 중심) */}
        {MINIATURE_DISASTERS.map((d) => {
          const [cx, cy] = gps(d.lat, d.lon);
          const color = DISASTER_COLOR[d.type];
          return (
            <g key={`dis-${d.key}`}>
              <circle
                cx={cx}
                cy={cy}
                r={20}
                fill={color}
                opacity={0.18}
              />
              <circle
                cx={cx}
                cy={cy}
                r={11}
                fill={color}
                stroke="#0f172a"
                strokeWidth={2}
                opacity={0.95}
              />
              <title>
                {`${DISASTER_LABEL[d.type]}\n위치: ${d.zone}\n${d.description}`}
              </title>
            </g>
          );
        })}

        {/* Legend (우상단) */}
        <g transform={`translate(${SVG_W - 240}, 30)`} className="legend">
          <rect width={220} height={150} rx={6} fill="rgba(15, 23, 42, 0.85)" stroke="#334155" />
          <text x={12} y={22} className="legend-title">범례</text>
          {/* 도로 */}
          <line x1={12} y1={42} x2={42} y2={42} stroke="#64748b" strokeWidth={3} />
          <text x={50} y={46} className="legend-text">정상 도로</text>
          <line x1={12} y1={62} x2={42} y2={62} stroke="#f59e0b" strokeWidth={4} />
          <text x={50} y={66} className="legend-text">정체</text>
          <line x1={12} y1={82} x2={42} y2={82} stroke="#dc2626" strokeWidth={5} strokeDasharray="6 4" />
          <text x={50} y={86} className="legend-text">차단</text>
          {/* 건물 */}
          <rect x={12} y={98} width={16} height={16} fill="#9ca3af" stroke="#0f172a" strokeWidth={1} rx={2} />
          <text x={36} y={111} className="legend-text">건물 (붕괴율 색상)</text>
          {/* 재난 */}
          <circle cx={20} cy={130} r={6} fill="#dc2626" stroke="#0f172a" strokeWidth={1} />
          <text x={36} y={134} className="legend-text">재난 지점</text>
        </g>
      </svg>
    </div>
  );
}
