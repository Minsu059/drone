import { useState } from 'react';
import 'leaflet/dist/leaflet.css';
import { WideView } from './components/WideView';
import { MiniatureModal } from './components/MiniatureModal';

export default function App() {
  const [miniatureZone, setMiniatureZone] = useState<string | null>(null);

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
      <main className="app-map">
        <WideView onZoneClick={(zone) => setMiniatureZone(zone)} />
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
      />
    </div>
  );
}
