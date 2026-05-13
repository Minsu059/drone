/**
 * 미니어처 view_slot 컨트롤 패널.
 * - 슬롯 9개 버튼 (건물 6 + 도로 3): 클릭 시 active 전환
 * - 리셋 버튼: 누적 상태 초기화
 * - 활성 슬롯은 시각적으로 강조
 */
import type { SlotMeta } from '../api/dashboard';

interface Props {
  slots: SlotMeta[];
  activeSlotId: string;
  onSelect: (slotId: string) => void;
  onReset: () => void;
  busy?: boolean;
  error?: string | null;
}

export function SlotControlPanel({
  slots,
  activeSlotId,
  onSelect,
  onReset,
  busy,
  error,
}: Props) {
  const buildingSlots = slots.filter((s) => s.kind === 'building');
  const roadSlots = slots.filter((s) => s.kind === 'road');

  return (
    <aside className="slot-panel" aria-label="카메라 시점 슬롯 컨트롤">
      <header className="slot-panel-header">
        <h3>카메라 시점 슬롯</h3>
        <button
          type="button"
          className="slot-reset"
          onClick={onReset}
          disabled={busy}
          title="누적된 모든 위험도/incident 초기화"
        >
          리셋
        </button>
      </header>

      <section className="slot-group">
        <div className="slot-group-title">건물 붕괴 (6)</div>
        <div className="slot-grid">
          {buildingSlots.map((s) => (
            <button
              key={s.slot_id}
              type="button"
              className={`slot-btn slot-btn-building ${s.slot_id === activeSlotId ? 'is-active' : ''}`}
              onClick={() => onSelect(s.slot_id)}
              disabled={busy}
            >
              {s.label}
            </button>
          ))}
        </div>
      </section>

      <section className="slot-group">
        <div className="slot-group-title">도로 incident (3)</div>
        <div className="slot-grid">
          {roadSlots.map((s) => (
            <button
              key={s.slot_id}
              type="button"
              className={`slot-btn slot-btn-road ${s.slot_id === activeSlotId ? 'is-active' : ''}`}
              onClick={() => onSelect(s.slot_id)}
              disabled={busy}
            >
              {s.label}
            </button>
          ))}
        </div>
      </section>

      {error && <div className="slot-error">{error}</div>}

      <footer className="slot-panel-footer">
        활성 슬롯 = 카메라가 지금 보는 시점.<br />
        다음 detection은 이 슬롯으로 태깅되며 max 누적됩니다.
      </footer>
    </aside>
  );
}
