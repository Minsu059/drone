import { useEffect, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  CircleMarker,
  Circle,
  Popup,
  GeoJSON,
  LayersControl,
  LayerGroup,
  useMap,
} from 'react-leaflet';
import type L from 'leaflet';
import type { FeatureCollection } from 'geojson';
import {
  type DisasterType,
  type VirtualDisaster,
} from '../data/mockData';
import type {
  WideDashboardResponse,
  InfraResponse,
  InfraPoint,
} from '../api/dashboard';
import { riskScoreToColor } from '../utils/coords';
import { computeRisk } from '../utils/risk';
import {
  DRONE_ICON,
  DISASTER_ICONS,
  INFRA_ICONS,
  SHELTER_COLOR,
  SHELTER_STROKE,
} from '../utils/mapIcons';

interface Props {
  wide: WideDashboardResponse;
  boundary: FeatureCollection;
  infra: InfraResponse;
  onZoneClick: (zoneName: string) => void;
  focusedDisasterId: string | null;
}

const BOUNDARY_STYLE = {
  color: '#7ba7c4',
  weight: 1,
  fillColor: '#7ba7c4',
  fillOpacity: 0.05,
};

function InfraPopup({ p, label }: { p: InfraPoint; label: string }) {
  const addr = (p['주소'] ?? p['도로명전체주소'] ?? '') as string;
  return (
    <div className="popup">
      <div className="popup-title">{p.name}</div>
      <div className="popup-meta">
        {label} · KAU 직선거리 {Math.round(p.distance_m)}m
      </div>
      {addr && <div className="popup-addr">{addr}</div>}
    </div>
  );
}

const DISASTER_LABEL: Record<DisasterType, string> = {
  fire: '화재',
  flood: '침수',
  earthquake: '지진',
  landslide: '산사태',
};

function DisasterPopup({ d }: { d: VirtualDisaster }) {
  const risk = computeRisk(d);
  return (
    <div className="popup">
      <div className="popup-title">{d.description}</div>
      <div className="popup-meta">
        {DISASTER_LABEL[d.disaster_type]} · 영향반경 {d.impact_radius_m}m
      </div>
      <table className="risk-table">
        <thead>
          <tr>
            <th>항목</th>
            <th>값</th>
            <th>점수</th>
          </tr>
        </thead>
        <tbody>
          {risk.items.map((it) => (
            <tr key={it.label}>
              <td>{it.label}</td>
              <td>{it.raw}</td>
              <td>
                <b>{it.score}</b>
                <span className="risk-max">/{it.max}</span>
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan={2}>종합 위험도</td>
            <td>
              <b style={{ color: riskScoreToColor(risk.total) }}>
                {risk.total}
              </b>
              <span className="risk-max">/100</span>
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

interface FocuserProps {
  disasters: VirtualDisaster[];
  focusedId: string | null;
  markerRefs: React.MutableRefObject<Map<string, L.Marker>>;
}

function MapFocuser({ disasters, focusedId, markerRefs }: FocuserProps) {
  const map = useMap();
  useEffect(() => {
    if (!focusedId) return;
    const d = disasters.find((x) => x.id === focusedId);
    if (!d) return;
    const targetZoom = Math.max(map.getZoom(), 15);
    map.flyTo([d.lat, d.lon], targetZoom, { duration: 0.6 });
    const t = window.setTimeout(() => {
      markerRefs.current.get(focusedId)?.openPopup();
    }, 700);
    return () => window.clearTimeout(t);
  }, [focusedId, disasters, map, markerRefs]);
  return null;
}

export function WideView({ wide, boundary, infra, onZoneClick, focusedDisasterId }: Props) {
  const markerRefs = useRef<Map<string, L.Marker>>(new Map());
  const { view, drones, disasters, miniature_entry } = wide;

  return (
    <MapContainer
      center={view.center}
      zoom={view.zoom}
      style={{ width: '100%', height: '100%' }}
      closePopupOnClick={false}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {/* 행정구역 경계 (VWorld 읍면동) */}
      {boundary.features.length > 0 && (
        <GeoJSON
          data={boundary}
          style={BOUNDARY_STYLE}
          onEachFeature={(feature, layer) => {
            const name = feature.properties?.emd_kor_nm as string | undefined;
            if (name) {
              layer.bindTooltip(name, { sticky: true, className: 'boundary-tooltip' });
            }
          }}
        />
      )}

      <MapFocuser
        disasters={disasters}
        focusedId={focusedDisasterId}
        markerRefs={markerRefs}
      />

      {/* 재난 영향 반경 — 외곽 채움 + 점선 테두리로 범위 강조 */}
      {disasters.map((d) => {
        const risk = computeRisk(d);
        const color = riskScoreToColor(risk.total);
        return (
          <Circle
            key={`r-${d.id}`}
            center={[d.lat, d.lon]}
            radius={d.impact_radius_m}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: 0.2,
              weight: 3,
              dashArray: '8 5',
            }}
            interactive={false}
          />
        );
      })}

      {/* 재난 마커 */}
      {disasters.map((d) => (
        <Marker
          key={d.id}
          position={[d.lat, d.lon]}
          icon={DISASTER_ICONS[d.disaster_type]}
          ref={(el) => {
            if (el) markerRefs.current.set(d.id, el);
            else markerRefs.current.delete(d.id);
          }}
        >
          <Popup
            maxWidth={320}
            autoClose={false}
            closeOnClick={false}
          >
            <DisasterPopup d={d} />
          </Popup>
        </Marker>
      ))}

      {/* 가상 드론 */}
      {drones.map((d) => (
        <Marker
          key={d.drone_id}
          position={[d.lat, d.lon]}
          icon={DRONE_ICON}
        >
          <Popup autoClose={false} closeOnClick={false}>
            <div className="popup">
              <div className="popup-title">{d.drone_id}</div>
              <div className="popup-meta">순찰: {d.area}</div>
              <span className="tag tag-virtual">virtual</span>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* 미니어처 진입 마커 */}
      <CircleMarker
        center={miniature_entry.center}
        radius={11}
        pathOptions={{
          color: '#0ea5e9',
          fillColor: '#38bdf8',
          fillOpacity: 0.9,
          weight: 3,
        }}
        eventHandlers={{
          click: () => onZoneClick(miniature_entry.name),
        }}
      >
        <Popup autoClose={false} closeOnClick={false}>
          <div className="popup">
            <div className="popup-title">{miniature_entry.name}</div>
            <div className="popup-meta">미니어처 시연 장소</div>
            <button
              type="button"
              className="popup-btn"
              onClick={() => onZoneClick(miniature_entry.name)}
            >
              미니어처 뷰 열기 →
            </button>
          </div>
        </Popup>
      </CircleMarker>

      {/* 공공 인프라 토글 레이어 (대피소/소방서/병원) */}
      <LayersControl position="topright" collapsed={false}>
        <LayersControl.Overlay name={`🟡 대피소 (${infra.shelters.length})`}>
          <LayerGroup>
            {infra.shelters.map((s, i) => (
              <CircleMarker
                key={`sh-${i}`}
                center={[s.lat, s.lon]}
                radius={5}
                pathOptions={{
                  color: SHELTER_STROKE,
                  fillColor: SHELTER_COLOR,
                  fillOpacity: 0.85,
                  weight: 1.5,
                }}
              >
                <Popup>
                  <InfraPopup p={s} label="대피소" />
                </Popup>
              </CircleMarker>
            ))}
          </LayerGroup>
        </LayersControl.Overlay>

        <LayersControl.Overlay name={`🔴 소방서 (${infra.fire_stations.length})`}>
          <LayerGroup>
            {infra.fire_stations.map((f, i) => (
              <Marker
                key={`fs-${i}`}
                position={[f.lat, f.lon]}
                icon={INFRA_ICONS.fire_station}
              >
                <Popup>
                  <InfraPopup p={f} label="119안전센터" />
                </Popup>
              </Marker>
            ))}
          </LayerGroup>
        </LayersControl.Overlay>

        <LayersControl.Overlay name={`🔵 병원 (${infra.hospitals.length})`}>
          <LayerGroup>
            {infra.hospitals.map((h, i) => (
              <Marker
                key={`hp-${i}`}
                position={[h.lat, h.lon]}
                icon={INFRA_ICONS.hospital}
              >
                <Popup>
                  <InfraPopup p={h} label={(h['종별코드명'] as string) ?? '병원'} />
                </Popup>
              </Marker>
            ))}
          </LayerGroup>
        </LayersControl.Overlay>
      </LayersControl>
    </MapContainer>
  );
}
