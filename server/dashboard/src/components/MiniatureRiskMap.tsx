/**
 * 미니어처 SVG 위험도 맵.
 *
 * 배경: "미니어처 실사화.pdf" 에서 추출한 도시 디오라마 이미지를 그대로 사용.
 * 그 위에 디오라마 명세 좌표(viewBox 1200×920) 기준으로 동적 레이어를 오버레이:
 *   - buildings[id].collapseProbability → 건물 위험도 오버레이 + 배지
 *   - road_incidents[]                 → 도로 incident 아이콘
 *   - drone.x/y                        → 드론 마커
 */
import { useState } from 'react';
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

// ============================================================
// 진입 경로 — 시연용 하드코딩 (viewBox 좌표)
//   - ENTRY: 우측 진입로 (이동경로 예시.png 의 "진입" 화살표)
//   - OBSTACLES: 도로 위 차량 장애물 — 경로가 우회
//   - ROUTES: 건물별 진입로→입구 최적 경로 (미리 입력, 알고리즘 없음)
// ============================================================

const ENTRY: [number, number] = [1180, 575];

// 도로 차단 #1 — 공원 바로 아래 4차선 도로 전면 차단 (차량).
// 경로는 이 구간을 따라 주행하지 않는다 (H동만 1회 직각 횡단).
const BLOCKED_ROAD = { x1: 240, x2: 720, y: 575, label: '도로 전면 차단' };
const CAR = { x: 490, y: 575 };

// 도로 차단 #2 — 우상단 C동 바로 아래 교차로, 나무 쓰러짐.
const TREE_BLOCK = { x: 970, y: 250, label: '교차로 차단' };

// 건물별 진입 경로 — ENTRY 에서 도로를 따라 건물 입구 앞까지.
// 차단 #1(공원 아래 도로)·차단 #2(C동 아래 교차로)를 모두 회피.
//   A·B·C·D·F → x770 세로도로로 올라가 상단 도로 이용 (차단 #2 좌측)
//   G          → x970 세로도로 (나무 아래에서 멈춤)
//   H          → 상단 도로 우회 후 x300 도로로 차단구간 직각 횡단
//   I·J        → 차단구간 우측 도로로 진입 (횡단 없음)
const ROUTES: Record<string, [number, number][]> = {
  A: [ENTRY, [770, 575], [770, 250], [200, 250]],
  B: [ENTRY, [770, 575], [770, 250], [620, 250]],
  C: [ENTRY, [770, 575], [770, 250], [900, 250]],
  D: [ENTRY, [770, 575], [770, 250], [150, 250]],
  F: [ENTRY, [770, 575], [770, 415]],
  G: [ENTRY, [970, 575], [970, 415], [1010, 415]],
  H: [ENTRY, [770, 575], [770, 250], [300, 250], [300, 575], [300, 665], [260, 665]],
  I: [ENTRY, [890, 575], [890, 780], [820, 780]],
  J: [ENTRY, [1080, 575], [1080, 615]],
};

function ObstacleCar({ x, y }: { x: number; y: number }) {
  return (
    <g>
      <rect x={x - 34} y={y - 18} width={68} height={36} rx={9}
        fill="#e8a13a" stroke="#1a1206" strokeWidth={2.5} />
      <rect x={x - 19} y={y - 12} width={13} height={24} rx={3} fill="#2a2620" />
      <rect x={x + 7} y={y - 12} width={12} height={24} rx={3} fill="#2a2620" />
    </g>
  );
}

// 공원 아래 4차선 전면 차단 — 도로 위 빨간 차단 바 + 차량.
function BlockedRoad() {
  const { x1, x2, y, label } = BLOCKED_ROAD;
  const cx = (x1 + x2) / 2;
  return (
    <g>
      <rect x={x1} y={y - 20} width={x2 - x1} height={40} rx={5}
        fill="rgba(255,59,48,0.30)" stroke="#ff4b3a" strokeWidth={2.5} strokeDasharray="11 7" />
      <ObstacleCar x={CAR.x} y={CAR.y} />
      <rect x={cx - 80} y={y + 28} width={160} height={28} rx={6}
        fill="rgba(40,6,4,0.94)" stroke="#ff4b3a" strokeWidth={1.5} />
      <text x={cx} y={y + 47} textAnchor="middle" fontSize={15} fontWeight={800} fill="#ff6f5e">
        {label}
      </text>
    </g>
  );
}

// C동 아래 교차로 — 나무 쓰러짐 차단.
function TreeBlock() {
  const { x, y, label } = TREE_BLOCK;
  return (
    <g>
      <circle cx={x} cy={y} r={54} fill="rgba(255,59,48,0.20)"
        stroke="#ff4b3a" strokeWidth={2.5} strokeDasharray="11 7" />
      <FallenTreeIcon x={x} y={y} />
      <rect x={x - 72} y={y + 42} width={144} height={28} rx={6}
        fill="rgba(40,6,4,0.94)" stroke="#ff4b3a" strokeWidth={1.5} />
      <text x={x} y={y + 61} textAnchor="middle" fontSize={15} fontWeight={800} fill="#ff6f5e">
        {label}
      </text>
    </g>
  );
}

function EntryMarker({ x, y }: { x: number; y: number }) {
  return (
    <g>
      <circle cx={x} cy={y} r={26} fill="none" stroke="#36d1ff" strokeWidth={2} opacity={0.55} />
      <circle cx={x} cy={y} r={15} fill="#36d1ff" stroke="#04222e" strokeWidth={3} />
      <rect x={x - 98} y={y - 16} width={70} height={32} rx={7}
        fill="rgba(6,20,26,0.92)" stroke="#36d1ff" strokeWidth={1.5} />
      <text x={x - 63} y={y + 6} textAnchor="middle" fontSize={16} fontWeight={800} fill="#7fe6ff">
        진입로
      </text>
    </g>
  );
}

function RouteLayer({ route }: { route: [number, number][] }) {
  const pts = route.map(([px, py]) => `${px},${py}`).join(' ');
  const [ex, ey] = route[route.length - 1];
  return (
    <g>
      <polyline points={pts} fill="none" stroke="#36d1ff" strokeOpacity={0.25}
        strokeWidth={18} strokeLinejoin="round" strokeLinecap="round" />
      <polyline points={pts} fill="none" stroke="#41dcff" strokeWidth={6}
        strokeLinejoin="round" strokeLinecap="round" strokeDasharray="20 14">
        <animate attributeName="stroke-dashoffset" from="34" to="0" dur="0.9s" repeatCount="indefinite" />
      </polyline>
      <circle cx={ex} cy={ey} r={13} fill="none" stroke="#41dcff" strokeWidth={4} />
      <circle cx={ex} cy={ey} r={5} fill="#41dcff" />
    </g>
  );
}

// collapseProbability(0~100) → 붕괴도 등급 1~5 (백엔드 시드와 round-trip).
function riskLevel(prob: number): number {
  if (prob >= 80) return 5;
  if (prob >= 60) return 4;
  if (prob >= 40) return 3;
  if (prob >= 20) return 2;
  return 1;
}

// 등급별 스타일 — box(빗금/테두리)는 등급이 오를수록 진한 빨강,
// text(배지 글자)는 어두운 배지 위에서 읽히도록 밝게 유지.
const LEVEL_STYLE: Record<number, { box: string; text: string }> = {
  1: { box: '#e0604d', text: '#ffb59f' },
  2: { box: '#cf3f2b', text: '#ff8e6f' },
  3: { box: '#ab2417', text: '#ff6a4a' },
  4: { box: '#7d1410', text: '#ff5238' },
  5: { box: '#520606', text: '#ff3b28' },
};

const RISK_LEVELS = [1, 2, 3, 4, 5];

function BuildingRisk({ bd, prob }: { bd: BuildingDef; prob: number }) {
  const level = riskLevel(prob);
  const style = LEVEL_STYLE[level];
  // 붕괴도 배지 — 건물 footprint 중앙에 배치.
  const cx = bd.x + bd.w / 2;
  const cy = bd.y + bd.h / 2;
  return (
    <g>
      {/* 빗금 박스 — 건물 footprint 를 등급 색 대각 빗금으로 덮음 */}
      <rect x={bd.x} y={bd.y} width={bd.w} height={bd.h} fill={`url(#hatch-${level})`} />
      <rect x={bd.x} y={bd.y} width={bd.w} height={bd.h}
        fill="none" stroke={style.box} strokeWidth={3} />
      {/* 붕괴도 배지 */}
      <rect x={cx - 64} y={cy - 19} width={128} height={38} rx={7}
        fill="rgba(10, 12, 10, 0.9)" stroke={style.text} strokeWidth={1.5} />
      <text x={cx} y={cy + 8} textAnchor="middle"
        fontSize={24} fontWeight={800} fill={style.text}>
        붕괴도 {level}
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
  // 클릭된 건물 — 진입 경로 표시 대상 (같은 건물 다시 클릭 시 해제)
  const [selected, setSelected] = useState<string | null>(null);
  const selectedBd = selected ? BUILDINGS.find((b) => b.id === selected) : null;
  const selectedRoute = selected ? ROUTES[selected] : undefined;

  return (
    <svg
      viewBox={`0 0 ${VIEW_BOX_W} ${VIEW_BOX_H}`}
      className="risk-map-svg"
      role="img"
      aria-label="미니어처 도시 디오라마 위험도 맵"
    >
      {/* 등급별 대각 빗금 패턴 — 건물 footprint fill 용 */}
      <defs>
        {RISK_LEVELS.map((lv) => (
          <pattern
            key={lv}
            id={`hatch-${lv}`}
            patternUnits="userSpaceOnUse"
            width={20}
            height={20}
            patternTransform="rotate(45)"
          >
            <rect width={20} height={20} fill={LEVEL_STYLE[lv].box} fillOpacity={0.16} />
            <line x1={0} y1={0} x2={0} y2={20}
              stroke={LEVEL_STYLE[lv].box} strokeWidth={8} strokeOpacity={0.6} />
          </pattern>
        ))}
      </defs>

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

      {/* 선택 건물 강조 테두리 */}
      {selectedBd && (
        <rect
          x={selectedBd.x - 3}
          y={selectedBd.y - 3}
          width={selectedBd.w + 6}
          height={selectedBd.h + 6}
          fill="none"
          stroke="#41dcff"
          strokeWidth={5}
          strokeDasharray="14 9"
        >
          <animate attributeName="stroke-dashoffset" from="46" to="0" dur="1s" repeatCount="indefinite" />
        </rect>
      )}

      {/* 진입 경로 (선택된 건물) */}
      {selectedRoute && <RouteLayer route={selectedRoute} />}

      {/* 도로 차단 — 공원 아래 4차선 + C동 아래 교차로 */}
      <BlockedRoad />
      <TreeBlock />

      {/* 진입로 마커 */}
      <EntryMarker x={ENTRY[0]} y={ENTRY[1]} />

      {/* 드론 마커 (동적, 활성 슬롯 위치) */}
      <Drone x={state.drone.x} y={state.drone.y} />

      {/* 클릭 레이어 — 건물 선택 → 진입 경로 표시 (최상단 투명 hit area) */}
      <g>
        {BUILDINGS.map((bd) => (
          <rect
            key={`hit-${bd.id}`}
            x={bd.x}
            y={bd.y}
            width={bd.w}
            height={bd.h}
            fill="transparent"
            style={{ cursor: 'pointer' }}
            onClick={() => setSelected((cur) => (cur === bd.id ? null : bd.id))}
          >
            <title>{bd.id}동 — 클릭 시 진입 경로 표시</title>
          </rect>
        ))}
      </g>
    </svg>
  );
}
