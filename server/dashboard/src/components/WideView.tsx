import { MapContainer, TileLayer, CircleMarker, Circle, Popup } from 'react-leaflet';
import {
  WIDE_VIEW,
  VIRTUAL_DRONES,
  VIRTUAL_DISASTERS,
  VIRTUAL_ZONE_RISKS,
  type DisasterType,
} from '../data/mockData';
import { riskScoreToColor } from '../utils/coords';

interface Props {
  onZoneClick: (zoneName: string) => void;
}

const DISASTER_COLOR: Record<DisasterType, string> = {
  fire: '#dc2626',
  flood: '#2563eb',
  earthquake: '#a16207',
  landslide: '#7c3aed',
};

export function WideView({ onZoneClick }: Props) {
  return (
    <MapContainer
      center={WIDE_VIEW.center}
      zoom={WIDE_VIEW.zoom}
      style={{ width: '100%', height: '100%' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {/* 구역별 위험도 히트맵 (행정구역 GeoJSON은 Phase 4에서 교체) */}
      {VIRTUAL_ZONE_RISKS.map((zone) => {
        const color = riskScoreToColor(zone.risk_score);
        return (
          <Circle
            key={zone.name}
            center={zone.center}
            radius={500}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: 0.25,
              weight: zone.has_miniature ? 3 : 1,
              dashArray: zone.has_miniature ? '6 4' : undefined,
            }}
            eventHandlers={{
              click: () => {
                if (zone.has_miniature) onZoneClick(zone.name);
              },
            }}
          >
            <Popup>
              <div className="popup">
                <strong>{zone.name}</strong>
                <br />
                위험도: <b>{zone.risk_score}</b> / 100
                {zone.has_miniature && (
                  <>
                    <br />
                    <button
                      type="button"
                      className="popup-btn"
                      onClick={() => onZoneClick(zone.name)}
                    >
                      미니어처 뷰 열기 →
                    </button>
                  </>
                )}
              </div>
            </Popup>
          </Circle>
        );
      })}

      {/* 가상 드론 (회색) */}
      {VIRTUAL_DRONES.map((d) => (
        <CircleMarker
          key={d.drone_id}
          center={[d.lat, d.lon]}
          radius={6}
          pathOptions={{
            color: '#374151',
            fillColor: '#9ca3af',
            fillOpacity: 0.9,
            weight: 2,
          }}
        >
          <Popup>
            <div className="popup">
              <strong>{d.drone_id}</strong>
              <br />
              순찰: {d.area}
              <br />
              <span className="tag tag-virtual">virtual</span>
            </div>
          </Popup>
        </CircleMarker>
      ))}

      {/* 가상 재난 */}
      {VIRTUAL_DISASTERS.map((dis) => {
        const color = DISASTER_COLOR[dis.disaster_type];
        return (
          <CircleMarker
            key={dis.id}
            center={[dis.lat, dis.lon]}
            radius={10}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: 0.7,
              weight: 2,
            }}
          >
            <Popup>
              <div className="popup">
                <strong>{dis.description}</strong>
                <br />
                유형: {dis.disaster_type}
                <br />
                인명: <b>{dis.person_count}</b>명
                <br />
                붕괴율: <b>{dis.collapse_rate}</b>%
                <br />
                도로: {dis.road_status}
                {dis.fire_detected && (
                  <>
                    <br />
                    화재 확신도: {(dis.fire_confidence * 100).toFixed(0)}%
                  </>
                )}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
