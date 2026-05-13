/**
 * 미니어처 위험도 맵 + 슬롯 컨트롤 컨테이너.
 * - 슬롯 목록 1회 fetch
 * - 누적 state 1초 폴링
 * - 슬롯 전환/리셋 POST → 응답을 즉시 state로 반영
 *
 * 모달 안에서 마운트되어 폴링이 자동 시작/정지.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  fetchRiskMapState,
  fetchSlotList,
  resetRiskMap,
  setActiveSlot,
  type RiskMapState,
  type SlotMeta,
} from '../api/dashboard';
import { MiniatureRiskMap } from './MiniatureRiskMap';
import { SlotControlPanel } from './SlotControlPanel';

const POLL_INTERVAL_MS = 1000;

export function RiskMapContainer() {
  const [slots, setSlots] = useState<SlotMeta[]>([]);
  const [state, setState] = useState<RiskMapState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const mountedRef = useRef(true);

  // 슬롯 메타 1회 + 초기 state
  useEffect(() => {
    mountedRef.current = true;
    Promise.all([fetchSlotList(), fetchRiskMapState()])
      .then(([slotList, s]) => {
        if (!mountedRef.current) return;
        setSlots(slotList.slots);
        setState(s);
      })
      .catch((err: unknown) => {
        if (!mountedRef.current) return;
        setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // 폴링
  useEffect(() => {
    const tick = () => {
      fetchRiskMapState()
        .then((s) => {
          if (mountedRef.current) setState(s);
        })
        .catch(() => {
          // 폴링 중 일시 오류는 무시 (다음 tick에서 회복)
        });
    };
    const handle = window.setInterval(tick, POLL_INTERVAL_MS);
    return () => window.clearInterval(handle);
  }, []);

  const handleSelect = useCallback((slotId: string) => {
    setBusy(true);
    setError(null);
    setActiveSlot(slotId)
      .then((s) => {
        if (mountedRef.current) setState(s);
      })
      .catch((err: unknown) => {
        if (mountedRef.current) {
          setError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (mountedRef.current) setBusy(false);
      });
  }, []);

  const handleReset = useCallback(() => {
    setBusy(true);
    setError(null);
    resetRiskMap()
      .then((s) => {
        if (mountedRef.current) setState(s);
      })
      .catch((err: unknown) => {
        if (mountedRef.current) {
          setError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (mountedRef.current) setBusy(false);
      });
  }, []);

  if (!state || slots.length === 0) {
    return (
      <div className="risk-map-loading">
        {error ? (
          <>
            <strong>슬롯 상태 로딩 실패</strong>
            <code>{error}</code>
          </>
        ) : (
          '미니어처 위험도 상태 불러오는 중…'
        )}
      </div>
    );
  }

  return (
    <div className="risk-map-layout">
      <div className="risk-map-canvas">
        <MiniatureRiskMap state={state} />
      </div>
      <SlotControlPanel
        slots={slots}
        activeSlotId={state.active_slot_id}
        onSelect={handleSelect}
        onReset={handleReset}
        busy={busy}
        error={error}
      />
    </div>
  );
}
