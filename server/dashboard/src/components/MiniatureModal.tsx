import { useEffect, type ReactNode } from 'react';

interface Props {
  open: boolean;
  zoneName?: string | null;
  onClose: () => void;
  children?: ReactNode;
}

export function MiniatureModal({ open, zoneName, onClose, children }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-header">
        <button type="button" className="modal-back" onClick={onClose}>
          ← 광역으로 돌아가기
        </button>
        <h2 className="modal-title">
          {zoneName ?? '한국항공대'} 미니어처 뷰
        </h2>
        <button
          type="button"
          className="modal-close"
          onClick={onClose}
          aria-label="닫기 (ESC)"
          title="닫기 (ESC)"
        >
          ×
        </button>
      </div>
      <div className="modal-map">
        {children}
      </div>
    </div>
  );
}
