import { MapContainer, TileLayer, CircleMarker, Circle, Polyline, Popup } from 'react-leaflet';
import {
  MINIATURE_VIEW,
  MINIATURE_ZONES,
  MINIATURE_BUILDINGS,
  MINIATURE_DISASTERS,
  MINIATURE_ROAD_NODES,
  MINIATURE_ROAD_EDGES,
  MINIATURE_BLOCKED_ROADS,
  MINIATURE_CONGESTED_ROADS,
  type RoadEdge,
  type MiniatureDisasterType,
} from '../data/mockData';
import { collapseRateToColor } from '../utils/coords';

const DISASTER_COLOR: Record<MiniatureDisasterType, string> = {
  road_saturated: '#f59e0b',
  road_damage: '#7c2d12',
  fire: '#dc2626',
};

const DISASTER_LABEL: Record<MiniatureDisasterType, string> = {
  road_saturated: '도로 포화',
  road_damage: '도로 파괴',
  fire: '화재',
};

function edgeKey(e: RoadEdge): string {
  return `${e[0]}-${e[1]}`;
}

export function MiniatureView() {
  const blockedSet = new Set(MINIATURE_BLOCKED_ROADS.map(edgeKey));
  const congestedSet = new Set(MINIATURE_CONGESTED_ROADS.map(edgeKey));

  return (
    <MapContainer
      center={MINIATURE_VIEW.center}
      zoom={MINIATURE_VIEW.zoom}
      style={{ width: '100%', height: '100%' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {/* 미니어처 구역 (얇은 점선 원) */}
      {MINIATURE_ZONES.map((z) => (
        <Circle
          key={z.key}
          center={z.center}
          radius={z.radius_m}
          pathOptions={{
            color: '#3b82f6',
            fillColor: '#3b82f6',
            fillOpacity: 0.05,
            weight: 1,
            dashArray: '4 4',
          }}
        >
          <Popup>
            <div className="popup">
              <strong>{z.name}</strong>
              <br />
              {z.description}
            </div>
          </Popup>
        </Circle>
      ))}

      {/* 도로 엣지 */}
      {MINIATURE_ROAD_EDGES.map((e) => {
        const k = edgeKey(e);
        const blocked = blockedSet.has(k);
        const congested = congestedSet.has(k);
        const color = blocked ? '#dc2626' : congested ? '#f59e0b' : '#6b7280';
        const weight = blocked ? 5 : congested ? 4 : 3;
        const dashArray = blocked ? '8 6' : undefined;
        const status = blocked ? '차단' : congested ? '정체' : '정상';
        return (
          <Polyline
            key={k}
            positions={[MINIATURE_ROAD_NODES[e[0]], MINIATURE_ROAD_NODES[e[1]]]}
            pathOptions={{ color, weight, dashArray, opacity: 0.85 }}
          >
            <Popup>
              <div className="popup">
                <strong>{e[0]} ↔ {e[1]}</strong>
                <br />
                상태: {status}
              </div>
            </Popup>
          </Polyline>
        );
      })}

      {/* 도로 노드 */}
      {Object.entries(MINIATURE_ROAD_NODES).map(([id, pos]) => (
        <CircleMarker
          key={id}
          center={pos}
          radius={3}
          pathOptions={{
            color: '#374151',
            fillColor: '#ffffff',
            fillOpacity: 1,
            weight: 1,
          }}
        >
          <Popup>
            <div className="popup">노드 {id}</div>
          </Popup>
        </CircleMarker>
      ))}

      {/* 건물 (collapse_rate 색상) */}
      {MINIATURE_BUILDINGS.map((b) => {
        const color = collapseRateToColor(b.collapse_rate);
        return (
          <CircleMarker
            key={b.name}
            center={[b.lat, b.lon]}
            radius={8}
            pathOptions={{
              color: '#1f2937',
              fillColor: color,
              fillOpacity: 0.9,
              weight: 2,
            }}
          >
            <Popup>
              <div className="popup">
                <strong>{b.name}</strong>
                <br />
                구역: {b.zone}
                <br />
                붕괴율: <b>{b.collapse_rate}</b>%
              </div>
            </Popup>
          </CircleMarker>
        );
      })}

      {/* 미니어처 재난 */}
      {MINIATURE_DISASTERS.map((d) => {
        const color = DISASTER_COLOR[d.type];
        return (
          <CircleMarker
            key={d.key}
            center={[d.lat, d.lon]}
            radius={11}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: 0.7,
              weight: 2,
            }}
          >
            <Popup>
              <div className="popup">
                <strong>{DISASTER_LABEL[d.type]}</strong>
                <br />
                위치: {d.zone}
                <br />
                {d.description}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
