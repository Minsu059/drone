import { useEffect, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import { WideView } from './components/WideView';
import { MiniatureModal } from './components/MiniatureModal';
import { MiniatureView } from './components/MiniatureView';
import { DisasterSidebar } from './components/DisasterSidebar';
import {
  fetchWideDashboard,
  fetchMiniatureDashboard,
  type WideDashboardResponse,
  type MiniatureDashboardResponse,
} from './api/dashboard';

export default function App() {
  const [wide, setWide] = useState<WideDashboardResponse | null>(null);
  const [miniature, setMiniature] = useState<MiniatureDashboardResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [miniatureZone, setMiniatureZone] = useState<string | null>(null);
  const [focusedDisasterId, setFocusedDisasterId] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchWideDashboard(), fetchMiniatureDashboard()])
      .then(([w, m]) => {
        setWide(w);
        setMiniature(m);
      })
      .catch((err: unknown) => {
        setLoadError(err instanceof Error ? err.message : String(err));
      });
  }, []);

  const handleSelectDisaster = (id: string) => {
    setFocusedDisasterId((prev) => (prev === id ? null : id));
  };

  if (loadError) {
    return (
      <div className="app-loading app-loading-error">
        <strong>대시보드 데이터 로딩 실패</strong>
        <code>{loadError}</code>
        <small>백엔드 (FastAPI :8000) 가 실행 중인지 확인하세요.</small>
      </div>
    );
  }

  if (!wide || !miniature) {
    return <div className="app-loading">대시보드 데이터 불러오는 중…</div>;
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-title">
          <span className="app-title-main">드론 재난 대응 관제</span>
          <span className="app-title-sub">한국항공대 광역 모니터링</span>
        </div>
        <div className="app-legend">
          <span className="legend-item"><i className="dot dot-virtual" /> 가상 드론</span>
          <span className="legend-item"><i className="dot dot-fire" /> 화재</span>
          <span className="legend-item"><i className="dot dot-flood" /> 침수</span>
          <span className="legend-item"><i className="dot dot-quake" /> 지진</span>
          <span className="legend-item"><i className="dot dot-slide" /> 산사태</span>
        </div>
      </header>
      <main className="app-body">
        <div className="app-map">
          <WideView
            wide={wide}
            onZoneClick={(zone) => setMiniatureZone(zone)}
            focusedDisasterId={focusedDisasterId}
          />
        </div>
        <DisasterSidebar
          disasters={wide.disasters}
          focusedId={focusedDisasterId}
          onSelect={handleSelectDisaster}
        />
      </main>
      <footer className="app-footer">
        © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors
        {' · '}VWorld <span className="footer-tbd">(연동 예정)</span>
        {' · '}공공데이터포털 <span className="footer-tbd">(연동 예정)</span>
      </footer>
      <MiniatureModal
        open={miniatureZone !== null}
        zoneName={miniatureZone}
        onClose={() => setMiniatureZone(null)}
      >
        <MiniatureView miniature={miniature} />
      </MiniatureModal>
    </div>
  );
}
