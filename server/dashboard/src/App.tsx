import { useEffect, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import { WideView } from './components/WideView';
import { MiniatureModal } from './components/MiniatureModal';
import { RiskMapContainer } from './components/RiskMapContainer';
import { DisasterBar } from './components/DisasterBar';
import { DisasterDetail } from './components/DisasterDetail';
import type { FeatureCollection } from 'geojson';
import {
  fetchWideDashboard,
  fetchMiniatureDashboard,
  fetchBoundary,
  fetchInfra,
  fetchDisasters,
  type WideDashboardResponse,
  type MiniatureDashboardResponse,
  type InfraResponse,
  type DisastersResponse,
} from './api/dashboard';

// 라즈베리파이 실시간 재난/드론 폴링 주기 (ms) — 드론 이동을 매끄럽게 보이도록 짧게
const DISASTER_POLL_MS = 1000;

export default function App() {
  const [wide, setWide] = useState<WideDashboardResponse | null>(null);
  const [miniature, setMiniature] = useState<MiniatureDashboardResponse | null>(null);
  const [boundary, setBoundary] = useState<FeatureCollection | null>(null);
  const [infra, setInfra] = useState<InfraResponse | null>(null);
  const [live, setLive] = useState<DisastersResponse>({
    disasters: [],
    routes: [],
    drones: [],
  });
  const [loadError, setLoadError] = useState<string | null>(null);

  const [miniatureZone, setMiniatureZone] = useState<string | null>(null);
  const [focusedDisasterId, setFocusedDisasterId] = useState<string | null>(null);

  // 정적 데이터 — 1회 로드
  useEffect(() => {
    Promise.all([
      fetchWideDashboard(),
      fetchMiniatureDashboard(),
      fetchBoundary(),
      fetchInfra(),
    ])
      .then(([w, m, b, i]) => {
        setWide(w);
        setMiniature(m);
        setBoundary(b);
        setInfra(i);
      })
      .catch((err: unknown) => {
        setLoadError(err instanceof Error ? err.message : String(err));
      });
  }, []);

  // 실시간 재난 — 3초 폴링
  useEffect(() => {
    let alive = true;
    const tick = () => {
      fetchDisasters()
        .then((d) => {
          if (alive) setLive(d);
        })
        .catch(() => {
          // 폴링 중 일시 오류는 무시 (다음 tick에서 회복)
        });
    };
    tick();
    const handle = window.setInterval(tick, DISASTER_POLL_MS);
    return () => {
      alive = false;
      window.clearInterval(handle);
    };
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

  if (!wide || !miniature || !boundary || !infra) {
    return <div className="app-loading">대시보드 데이터 불러오는 중…</div>;
  }

  const focusedDisaster =
    live.disasters.find((d) => d.id === focusedDisasterId) ?? null;
  const focusedRoute = live.routes.find(
    (r) => r.disaster_id === focusedDisasterId,
  );

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
        <div className="app-main-col">
          <div className="app-map">
            <WideView
              wide={wide}
              boundary={boundary}
              infra={infra}
              disasters={live.disasters}
              routes={live.routes}
              liveDrones={live.drones}
              onZoneClick={(zone) => setMiniatureZone(zone)}
              focusedDisasterId={focusedDisasterId}
            />
          </div>
          <DisasterBar
            disasters={live.disasters}
            focusedId={focusedDisasterId}
            onSelect={handleSelectDisaster}
          />
        </div>
        <DisasterDetail disaster={focusedDisaster} route={focusedRoute} />
      </main>
      <footer className="app-footer">
        © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors
        {' · '}행정구역 © <a href="https://www.vworld.kr" target="_blank" rel="noreferrer">VWorld</a> (국토교통부)
        {' · '}공공데이터 © 행정안전부·소방청·심평원 (<a href="https://www.data.go.kr" target="_blank" rel="noreferrer">data.go.kr</a>)
      </footer>
      <MiniatureModal
        open={miniatureZone !== null}
        zoneName={miniatureZone}
        onClose={() => setMiniatureZone(null)}
      >
        <RiskMapContainer />
      </MiniatureModal>
    </div>
  );
}
