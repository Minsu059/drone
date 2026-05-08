/**
 * 미니어처 로컬 좌표 ↔ GPS 변환.
 * 미니어처 1m ↔ GPS 80m (스케일 1:80)
 * 자세한 정책: docs/dashboard.md 좌표 매핑 정책
 */

const CENTER_LAT = 37.6000;
const CENTER_LON = 126.8645;
const SCALE = 80; // 미니어처 실물 1m → GPS 80m

export function localToGps(xMeter: number, yMeter: number): [number, number] {
  const lat = CENTER_LAT + (yMeter * SCALE) / 111_000;
  const lon =
    CENTER_LON +
    (xMeter * SCALE) / (111_000 * Math.cos((CENTER_LAT * Math.PI) / 180));
  return [lat, lon];
}

/** 위험도(0~100) → 색상 (노랑→주황→빨강) */
export function riskScoreToColor(score: number): string {
  if (score >= 75) return '#dc2626'; // 빨강
  if (score >= 50) return '#ea580c'; // 주황
  if (score >= 25) return '#f59e0b'; // 황주
  return '#facc15';                   // 노랑
}

/** 붕괴율(0~100) → 색상 (회색→빨강) */
export function collapseRateToColor(rate: number): string {
  if (rate >= 70) return '#7f1d1d';
  if (rate >= 40) return '#dc2626';
  if (rate >= 15) return '#f59e0b';
  return '#9ca3af';
}
