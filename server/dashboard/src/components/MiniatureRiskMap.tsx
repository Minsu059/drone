/**
 * 미니어처 SVG 위험도 맵.
 *
 * 배경: "미니어처 실사화.pdf" 에서 추출한 도시 디오라마 이미지를 그대로 사용.
 * 그 위에 디오라마 명세 좌표(viewBox 1200×920) 기준으로 동적 레이어를 오버레이:
 *   - buildings[id].collapseProbability → 건물 위험도 오버레이 + 배지
 *   - road_incidents[]                 → 도로 incident 아이콘
 *   - drone.x/y                        → 드론 마커
 */
import miniatureMapUrl from '../assets/miniature-map.png';
import type { RiskMapState, RoadIncident, IncidentType } from '../api/dashboard';

const VIEW_BOX_W = 1200;
const VIEW_BOX_H = 920;

// 건물 footprint (디오라마 명세, viewBox 좌표). 위험도 오버레이용 — E(공원) 제외.
interface BuildingDef {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

const BUILDINGS: BuildingDef[] = [
  { id: 'A', x: 0, y: 0, w: 400, h: 180 },
  { id: 'B', x: 540, y: 0, w: 160, h: 180 },
  { id: 'C', x: 840, y: 0, w: 360, h: 180 },
  { id: 'D', x: 0, y: 320, w: 200, h: 240 },
  { id: 'F', x: 780, y: 320, w: 120, h: 180 },
  { id: 'G', x: 1040, y: 320, w: 160, h: 180 },
  { id: 'H', x: 0, y: 700, w: 480, h: 220 },
  { id: 'I', x: 640, y: 640, w: 180, h: 280 },
  { id: 'J', x: 960, y: 640, w: 240, h: 280 },
];

function riskOverlay(prob: number): string {
  if (prob >= 75) return 'rgba(255, 59, 48, 0.42)';
  if (prob >= 50) return 'rgba(255, 122, 36, 0.38)';
  if (prob >= 25) return 'rgba(255, 200, 50, 0.34)';
  return 'rgba(255, 220, 90, 0.24)';
}
function riskColor(prob: number): string {
  if (prob >= 75) return '#ff3b30';
  if (prob >= 50) return '#ff7a24';
  if (prob >= 25) return '#ffc832';
  return '#ffdc5a';
}

function BuildingRisk({ bd, prob }: { bd: BuildingDef; prob: number }) {
  return (
    <g>
      <rect x={bd.x} y={bd.y} width={bd.w} height={bd.h} fill={riskOverlay(prob)} />
      <rect x={bd.x} y={bd.y} width={bd.w} height={bd.h}
        fill="none" stroke={riskColor(prob)} strokeWidth={3} />
      <rect x={bd.x + 8} y={bd.y + 8} width={112} height={28} rx={5}
        fill="rgba(10, 12, 10, 0.88)" stroke={riskColor(prob)} strokeWidth={1.5} />
      <text x={bd.x + 64} y={bd.y + 27} textAnchor="middle"
        fontSize={14} fontWeight={800} fill={riskColor(prob)}>
        {bd.id}동 {prob}%
      </text>
    </g>
  );
}

// ============================================================
// Incident 아이콘
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

interface IncidentTypeConfig {
  label: string;
  cardWidth: number;
  cardFill: string;
  cardStroke: string;
}

const INCIDENT_CONFIG: Record<IncidentType, IncidentTypeConfig> = {
  traffic: { label: '차량혼잡', cardWidth: 124, cardFill: 'rgba(83, 56, 14, 0.92)', cardStroke: '#ffc247' },
  fallenTree: { label: '나무 쓰러짐', cardWidth: 148, cardFill: 'rgba(20, 74, 40, 0.92)', cardStroke: '#4de46e' },
  rubble: { label: '건물 잔해', cardWidth: 128, cardFill: 'rgba(96, 28, 21, 0.92)', cardStroke: '#ff614c' },
};

function IncidentCard({ incident, config }: { incident: RoadIncident; config: IncidentTypeConfig }) {
  const cardX = incident.labelX ?? incident.x + 24;
  const cardY = incident.labelY ?? incident.y - 19;
  return (
    <g>
      <rect x={cardX} y={cardY} width={config.cardWidth} height={38} rx={6}
        fill={config.cardFill} stroke={config.cardStroke} strokeWidth={2} />
      <text x={cardX + 20} y={cardY + 25} className="risk-incident-label">
        {config.label}
      </text>
    </g>
  );
}

function Drone({ x, y }: { x: number; y: number }) {
  return (
    <g>
      <circle cx={x} cy={y} r={48} fill="none" stroke="rgba(139, 255, 94, 0.62)" strokeWidth={2} />
      <circle cx={x} cy={y} r={27} fill="none" stroke="rgba(139, 255, 94, 0.62)" strokeWidth={2} />
      <path
        d={`M${x} ${y - 13}l10 10h18v8h-18l-10 10-10-10h-18v-8h18z`}
        fill="#f4fff4"
        stroke="#9cff79"
        strokeWidth={2}
      />
      <circle cx={x - 28} cy={y - 3} r={5} fill="#f4fff4" stroke="#9cff79" strokeWidth={2} />
      <circle cx={x + 28} cy={y - 3} r={5} fill="#f4fff4" stroke="#9cff79" strokeWidth={2} />
      <circle cx={x - 28} cy={y + 5} r={5} fill="#f4fff4" stroke="#9cff79" strokeWidth={2} />
      <circle cx={x + 28} cy={y + 5} r={5} fill="#f4fff4" stroke="#9cff79" strokeWidth={2} />
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
      aria-label="미니어처 도시 디오라마 위험도 맵"
    >
      {/* 배경 — PDF 디오라마 이미지 */}
      <image
        href={miniatureMapUrl}
        x={0}
        y={0}
        width={VIEW_BOX_W}
        height={VIEW_BOX_H}
        preserveAspectRatio="none"
      />

      {/* 건물 위험도 오버레이 (붕괴확률 > 0 인 건물만) */}
      <g>
        {BUILDINGS.map((bd) => {
          const prob = state.buildings[bd.id]?.collapseProbability ?? 0;
          if (prob <= 0) return null;
          return <BuildingRisk key={bd.id} bd={bd} prob={prob} />;
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
      <Drone x={state.drone.x} y={state.drone.y} />
    </svg>
  );
}
