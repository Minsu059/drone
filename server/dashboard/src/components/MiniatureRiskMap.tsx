/**
 * 미니어처 SVG 위험도 맵.
 * 원본: docs/ui-mock/drone-risk-map.html (디자인 레퍼런스)
 *
 * 좌표/색상/구조는 원본 SVG와 동일.
 * 동적 데이터는 props.state (백엔드 /api/view-slot/state 응답)로 주입.
 *   - sections[id].riskLevel   → 섹션 폴리곤 색상/라벨
 *   - buildings[id].collapseProbability → 건물 내부 % 표기
 *   - road_incidents[]         → 도로 incident 아이콘+카드
 *   - drone.x/y                → 드론 마커 위치
 */
import type { RiskMapState, RoadIncident, IncidentType, BuildingId } from '../api/dashboard';

const VIEW_BOX_W = 1200;
const VIEW_BOX_H = 675;

const RISK_STYLES: Record<1 | 2 | 3 | 4, { label: string; color: string }> = {
  1: { label: '낮음',     color: '#24d36b' },
  2: { label: '주의',     color: '#ffd63d' },
  3: { label: '높음',     color: '#ff942d' },
  4: { label: '매우 높음', color: '#ff3b30' },
};

const SECTION_SHAPES: Record<string, string> = {
  A: '228,46 950,46 950,176 228,176',
  B: '376,245 644,245 644,410 376,410',
  C: '798,261 1126,261 1126,410 798,410',
  D: '148,486 438,486 438,618 148,618',
  E: '740,486 1080,486 1080,618 740,618',
};

const SECTION_LABEL_POS: Record<string, [number, number]> = {
  A: [244, 75],
  B: [392, 274],
  C: [814, 290],
  D: [164, 515],
  E: [756, 515],
};

interface BuildingShape {
  id: BuildingId;
  x: number;
  y: number;
  width: number;
  height: number;
  name: string;
}

const BUILDING_SHAPES: BuildingShape[] = [
  { id: 'topLeft',     x: 250, y: 70,  width: 280, height: 88,  name: '건물' },
  { id: 'topRight',    x: 658, y: 70,  width: 270, height: 88,  name: '건물' },
  { id: 'center',      x: 400, y: 268, width: 220, height: 126, name: '건물' },
  { id: 'rightMiddle', x: 820, y: 284, width: 284, height: 112, name: '건물' },
  { id: 'bottomLeft',  x: 168, y: 506, width: 250, height: 92,  name: '건물' },
  { id: 'bottomRight', x: 760, y: 506, width: 300, height: 92,  name: '건물' },
];

interface IncidentTypeConfig {
  label: string;
  cardWidth: number;
  cardFill: string;
  cardStroke: string;
}

const INCIDENT_CONFIG: Record<IncidentType, IncidentTypeConfig> = {
  traffic:    { label: '차량혼잡',   cardWidth: 124, cardFill: 'rgba(83, 56, 14, 0.92)',  cardStroke: '#ffc247' },
  fallenTree: { label: '나무 쓰러짐', cardWidth: 148, cardFill: 'rgba(20, 74, 40, 0.92)',  cardStroke: '#4de46e' },
  rubble:     { label: '건물 잔해',   cardWidth: 128, cardFill: 'rgba(96, 28, 21, 0.92)',  cardStroke: '#ff614c' },
};

// ============================================================
// Incident 아이콘 (SVG path 그룹)
// ============================================================

function RubbleIcon({ x, y }: { x: number; y: number }) {
  const fill = '#8f4b31';
  const stroke = '#ff775f';
  return (
    <g>
      <polygon fill={fill} stroke={stroke} strokeWidth={2}
        points={`${x - 34},${y - 10} ${x - 16},${y - 25} ${x + 4},${y - 8} ${x - 3},${y + 14} ${x - 26},${y + 12}`} />
      <polygon fill={fill} stroke={stroke} strokeWidth={2}
        points={`${x + 6},${y - 18} ${x + 24},${y - 30} ${x + 42},${y - 12} ${x + 34},${y + 8} ${x + 12},${y + 5}`} />
      <polygon fill={fill} stroke={stroke} strokeWidth={2}
        points={`${x - 2},${y + 20} ${x + 20},${y + 5} ${x + 38},${y + 23} ${x + 28},${y + 44} ${x + 4},${y + 38}`} />
    </g>
  );
}

function TrafficIcon({ x, y }: { x: number; y: number }) {
  return (
    <g>
      {[-28, 0, 28].map((offset, idx) => (
        <rect
          key={offset}
          x={x + offset - 13}
          y={y - 10 + (idx % 2) * 5}
          width={26}
          height={16}
          rx={4}
          fill="#e8edf1"
          stroke="#ffc247"
          strokeWidth={2}
        />
      ))}
      <circle cx={x + 48} cy={y - 8} r={5} fill="#ff4b36" />
      <circle cx={x + 48} cy={y + 8} r={5} fill="#ff4b36" />
    </g>
  );
}

function FallenTreeIcon({ x, y }: { x: number; y: number }) {
  return (
    <g>
      <ellipse cx={x} cy={y + 12} rx={64} ry={13} fill="rgba(4, 9, 8, 0.28)" />
      <line x1={x - 45} y1={y + 15} x2={x + 38} y2={y - 13}
        stroke="#8b5a32" strokeWidth={9} strokeLinecap="round" />
      <line x1={x - 10} y1={y + 3} x2={x - 30} y2={y - 16}
        stroke="#a8733d" strokeWidth={4} strokeLinecap="round" />
      <line x1={x + 10} y1={y - 4} x2={x + 2} y2={y - 27}
        stroke="#a8733d" strokeWidth={4} strokeLinecap="round" />
      <line x1={x + 22} y1={y - 8} x2={x + 49} y2={y - 25}
        stroke="#a8733d" strokeWidth={4} strokeLinecap="round" />
      <polygon points={`${x - 58},${y + 19} ${x - 42},${y - 6} ${x - 16},${y + 4} ${x - 28},${y + 29}`}
        fill="rgba(58, 139, 67, 0.92)" stroke="#8ff08d" strokeWidth={1.5} />
      <polygon points={`${x - 26},${y + 8} ${x - 8},${y - 22} ${x + 18},${y - 9} ${x + 8},${y + 20}`}
        fill="rgba(58, 139, 67, 0.92)" stroke="#8ff08d" strokeWidth={1.5} />
      <polygon points={`${x + 10},${y - 2} ${x + 36},${y - 34} ${x + 62},${y - 14} ${x + 45},${y + 12}`}
        fill="rgba(58, 139, 67, 0.92)" stroke="#8ff08d" strokeWidth={1.5} />
    </g>
  );
}

function IncidentCard({ incident, config }: { incident: RoadIncident; config: IncidentTypeConfig }) {
  const cardX = incident.labelX ?? incident.x + 24;
  const cardY = incident.labelY ?? incident.y - 19;
  return (
    <g>
      <rect
        x={cardX}
        y={cardY}
        width={config.cardWidth}
        height={38}
        rx={6}
        fill={config.cardFill}
        stroke={config.cardStroke}
        strokeWidth={2}
      />
      <text
        x={cardX + 20}
        y={cardY + 25}
        className="risk-incident-label"
      >
        {config.label}
      </text>
    </g>
  );
}

// ============================================================
// Main component
// ============================================================

interface Props {
  state: RiskMapState;
}

export function MiniatureRiskMap({ state }: Props) {
  return (
    <svg
      viewBox={`0 0 ${VIEW_BOX_W} ${VIEW_BOX_H}`}
      className="risk-map-svg"
      role="img"
      aria-label="드론 기반 지진 위험도 매핑"
    >
      <defs>
        <pattern id="risk-grid" width="30" height="30" patternUnits="userSpaceOnUse">
          <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(143, 199, 190, 0.1)" strokeWidth={1} />
        </pattern>
      </defs>

      <rect width={VIEW_BOX_W} height={VIEW_BOX_H} fill="#07131a" />
      <rect width={VIEW_BOX_W} height={VIEW_BOX_H} fill="url(#risk-grid)" />

      {/* 섹션 fills */}
      <g>
        {Object.entries(SECTION_SHAPES).map(([id, points]) => {
          const level = (state.sections[id]?.riskLevel ?? 1) as 1 | 2 | 3 | 4;
          const style = RISK_STYLES[level];
          return (
            <polygon key={`fill-${id}`} points={points} fill={style.color} opacity={0.32} />
          );
        })}
      </g>

      {/* 도로 surface (고정) */}
      <g>
        <rect x={28}  y={185} width={1144} height={46}  fill="#18201f" />
        <rect x={28}  y={416} width={1144} height={46}  fill="#18201f" />
        <rect x={250} y={185} width={64}   height={277} fill="#18201f" />
        <rect x={515} y={416} width={64}   height={231} fill="#18201f" />
        <rect x={662} y={185} width={64}   height={462} fill="#18201f" />

        <line x1={28}  y1={208} x2={1172} y2={208} stroke="rgba(235, 247, 232, 0.14)" strokeWidth={1.2} />
        <line x1={28}  y1={439} x2={1172} y2={439} stroke="rgba(235, 247, 232, 0.14)" strokeWidth={1.2} />
        <line x1={282} y1={185} x2={282}  y2={462} stroke="rgba(235, 247, 232, 0.14)" strokeWidth={1.2} />
        <line x1={547} y1={416} x2={547}  y2={647} stroke="rgba(235, 247, 232, 0.14)" strokeWidth={1.2} />
        <line x1={694} y1={185} x2={694}  y2={647} stroke="rgba(235, 247, 232, 0.14)" strokeWidth={1.2} />
      </g>

      {/* 건물 (고정 위치) + 동적 붕괴확률 */}
      <g>
        {BUILDING_SHAPES.map((b) => {
          const prob = state.buildings[b.id]?.collapseProbability ?? 0;
          return (
            <g key={`bldg-${b.id}`}>
              <rect
                x={b.x}
                y={b.y}
                width={b.width}
                height={b.height}
                fill="rgba(30, 95, 153, 0.64)"
                stroke="#1e9bff"
                strokeWidth={2}
                style={{ filter: 'drop-shadow(0 0 8px rgba(30, 155, 255, 0.35))' }}
              />
              <text
                x={b.x + b.width / 2}
                y={b.y + b.height / 2 - 8}
                className="risk-building-text"
              >
                {b.name}
              </text>
              <text
                x={b.x + b.width / 2}
                y={b.y + b.height / 2 + 20}
                className="risk-building-text"
              >
                붕괴확률 {prob}%
              </text>
            </g>
          );
        })}
      </g>

      {/* 섹션 borders + 라벨 (위험도 1~4 동적) */}
      <g>
        {Object.entries(SECTION_SHAPES).map(([id, points]) => {
          const level = (state.sections[id]?.riskLevel ?? 1) as 1 | 2 | 3 | 4;
          const style = RISK_STYLES[level];
          const [lx, ly] = SECTION_LABEL_POS[id];
          return (
            <g key={`border-${id}`}>
              <polygon
                points={points}
                fill="none"
                stroke={style.color}
                strokeWidth={3}
                strokeDasharray="12 8"
              />
              <text x={lx} y={ly} className="risk-section-label">
                {id} 위험도 {level}
              </text>
            </g>
          );
        })}
      </g>

      {/* 도로 incident (동적) */}
      <g>
        {state.road_incidents.map((inc) => {
          const config = INCIDENT_CONFIG[inc.type];
          return (
            <g key={`inc-${inc.id}`}>
              {inc.type === 'rubble' && <RubbleIcon x={inc.x} y={inc.y} />}
              {inc.type === 'traffic' && <TrafficIcon x={inc.x} y={inc.y} />}
              {inc.type === 'fallenTree' && <FallenTreeIcon x={inc.x} y={inc.y} />}
              <IncidentCard incident={inc} config={config} />
            </g>
          );
        })}
      </g>

      {/* 드론 마커 (동적, 활성 슬롯 위치) */}
      <g>
        <circle
          cx={state.drone.x}
          cy={state.drone.y}
          r={48}
          fill="none"
          stroke="rgba(139, 255, 94, 0.58)"
          strokeWidth={2}
        />
        <circle
          cx={state.drone.x}
          cy={state.drone.y}
          r={27}
          fill="none"
          stroke="rgba(139, 255, 94, 0.58)"
          strokeWidth={2}
        />
        <path
          d={`M${state.drone.x} ${state.drone.y - 13}l10 10h18v8h-18l-10 10-10-10h-18v-8h18z`}
          fill="#f4fff4"
          stroke="#9cff79"
          strokeWidth={2}
        />
        <circle cx={state.drone.x - 28} cy={state.drone.y - 3} r={5} fill="#f4fff4" stroke="#9cff79" strokeWidth={2} />
        <circle cx={state.drone.x + 28} cy={state.drone.y - 3} r={5} fill="#f4fff4" stroke="#9cff79" strokeWidth={2} />
        <circle cx={state.drone.x - 28} cy={state.drone.y + 5} r={5} fill="#f4fff4" stroke="#9cff79" strokeWidth={2} />
        <circle cx={state.drone.x + 28} cy={state.drone.y + 5} r={5} fill="#f4fff4" stroke="#9cff79" strokeWidth={2} />
      </g>

      {/* 범례 (고정) */}
      <g transform="translate(970 35)">
        <rect width={200} height={150} rx={8}
          fill="rgba(7, 18, 24, 0.84)" stroke="rgba(152, 224, 208, 0.2)" strokeWidth={1} />
        <text x={16} y={28} className="risk-legend-title">섹션 위험도</text>
        {([1, 2, 3, 4] as const).map((lvl, idx) => {
          const y = 48 + idx * 20;
          const s = RISK_STYLES[lvl];
          return (
            <g key={`lg-${lvl}`}>
              <rect x={16} y={y - 10} width={12} height={12} rx={2} fill={s.color} />
              <text x={38} y={y} className="risk-legend-text">위험도 {lvl} · {s.label}</text>
            </g>
          );
        })}
        <text x={16} y={132} className="risk-legend-text">건물: 붕괴확률 %</text>
      </g>
    </svg>
  );
}
