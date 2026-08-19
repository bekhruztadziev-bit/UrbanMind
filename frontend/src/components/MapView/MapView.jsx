import React, { useMemo } from 'react'
import L from 'leaflet'
import { CircleMarker, MapContainer, Marker, Polygon, Popup, Polyline, TileLayer } from 'react-leaflet'
import { getMapBounds, getCityBounds, getBoundaryCube } from '../../utils/geo'

export function MapView({ mahalla, selectedId, setSelectedId, language }) {
  const mapBounds = useMemo(() => getMapBounds(mahalla), [mahalla])
  const cityBounds = useMemo(() => getCityBounds(mahalla), [mahalla])
  const isRu = language === 'ru'

  const selectedIntersection = useMemo(() => {
    if (!mahalla) return null
    return mahalla.intersections?.find((item) => item.id === selectedId) || (mahalla.intersections ? mahalla.intersections[0] : null)
  }, [mahalla, selectedId])

  const mapCenter = selectedIntersection ? [selectedIntersection.coords[0], selectedIntersection.coords[1]] : [41.317, 69.267]

  if (!mahalla) return null

  const corridorPolygon = mahalla.bounds?.polygon || [
    [41.3080, 69.2550],
    [41.3080, 69.2780],
    [41.3250, 69.2780],
    [41.3250, 69.2550],
  ]

  return (
    <div className="map-view-wrapper" style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* Floating Corridor Zone Glass Badge */}
      <div className="map-floating-badge" style={{
        position: 'absolute',
        top: '12px',
        left: '12px',
        zIndex: 1000,
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(56, 189, 248, 0.3)',
        borderRadius: '10px',
        padding: '0.5rem 0.85rem',
        fontSize: '0.78rem',
        color: '#f8fafc',
        boxShadow: '0 4px 16px rgba(0,0,0,0.35)',
        pointerEvents: 'none',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.2rem'
      }}>
        <span style={{ fontWeight: 600, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#38bdf8', boxShadow: '0 0 8px #38bdf8', display: 'inline-block' }}></span>
          {isRu ? 'Зона анализа: Центральный коридор Ташкента' : 'Corridor Zone: Central Tashkent'}
        </span>
        <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>
          {isRu ? '📡 Станции экомониторинга: Узгидромет / WAQI' : '📡 Air Quality Sensors: Uzhydromet / WAQI'}
        </span>
      </div>

      <MapContainer
        center={mapCenter}
        bounds={cityBounds || mapBounds}
        boundsOptions={{ padding: [24, 24] }}
        scrollWheelZoom
        className="map-container"
        zoom={14}
        minZoom={11}
        maxZoom={18}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Clean geometric corridor boundary with cyan glow */}
        <Polygon
          positions={corridorPolygon}
          pathOptions={{
            color: '#0284c7',
            weight: 2,
            opacity: 0.85,
            fillColor: '#0ea5e9',
            fillOpacity: 0.05,
            dashArray: '6, 8',
          }}
        />

        {/* Facilities */}
        {mahalla.facilities && mahalla.facilities.map((facility) => (
          <CircleMarker
            key={facility.id}
            center={facility.coords}
            radius={5}
            pathOptions={{
              color: '#059669',
              fillColor: '#10b981',
              fillOpacity: 0.85,
              weight: 1.5,
            }}
          >
            <Popup>
              <strong style={{ color: '#0f172a' }}>{facility.name}</strong><br />
              <span style={{ color: '#64748b', fontSize: '0.78rem' }}>{facility.type}</span>
            </Popup>
          </CircleMarker>
        ))}

        {/* Intersections */}
        {mahalla.intersections && mahalla.intersections.map((intersection) => {
          const isSelected = selectedIntersection?.id === intersection.id
          return (
            <Marker
              key={intersection.id}
              position={intersection.coords}
              eventHandlers={{ click: () => setSelectedId(intersection.id) }}
              icon={
                new L.DivIcon({
                  className: 'intersection-marker-wrap',
                  html: `<span class="intersection-marker ${isSelected ? 'active' : ''}"></span>`,
                  iconSize: [12, 12],
                  iconAnchor: [6, 6],
                })
              }
            >
              <Popup>
                <strong style={{ color: '#0f172a' }}>{intersection.name}</strong><br />
                <span style={{ color: '#64748b', fontSize: '0.78rem' }}>
                  {intersection.traffic_light_ids.length} {isRu ? 'кластер светофоров' : 'traffic-light cluster'}
                </span>
              </Popup>
            </Marker>
          )
        })}

        {/* Monitoring Stations */}
        {mahalla.monitoring_stations && mahalla.monitoring_stations.map((station) => (
          <Marker
            key={station.id}
            position={station.coords}
            icon={
              new L.DivIcon({
                className: 'station-marker-wrap',
                html: `<div class="station-marker">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"/><path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"/><circle cx="12" cy="12" r="2"/><path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"/><path d="M19.1 4.9C23 8.8 23 15.2 19.1 19.1"/>
                  </svg>
                </div>`,
                iconSize: [22, 22],
                iconAnchor: [11, 11],
              })
            }
          >
            <Popup>
              <strong style={{ color: '#0f172a' }}>{station.name}</strong><br />
              <span style={{ fontSize: '11px', color: '#64748b' }}>{station.source}</span>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}
