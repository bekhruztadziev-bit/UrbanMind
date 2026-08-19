import React, { useMemo } from 'react'
import L from 'leaflet'
import { CircleMarker, MapContainer, Marker, Polygon, Popup, Polyline, TileLayer } from 'react-leaflet'
import { getMapBounds, getCityBounds, getBoundaryCube } from '../../utils/geo'

export function MapView({ mahalla, selectedId, setSelectedId, language }) {
  const mapBounds = useMemo(() => getMapBounds(mahalla), [mahalla])
  const cityBounds = useMemo(() => getCityBounds(mahalla), [mahalla])
  const boundaryCube = useMemo(() => getBoundaryCube(mahalla), [mahalla])

  const selectedIntersection = useMemo(() => {
    if (!mahalla) return null
    return mahalla.intersections?.find((item) => item.id === selectedId) || (mahalla.intersections ? mahalla.intersections[0] : null)
  }, [mahalla, selectedId])

  const mapCenter = selectedIntersection ? [selectedIntersection.coords[0], selectedIntersection.coords[1]] : [41.317, 69.267]

  if (!mahalla) return null

  return (
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

      {boundaryCube && (
        <Polygon
          positions={boundaryCube.outer}
          pathOptions={{
            color: 'var(--accent-primary, #3b82f6)',
            weight: 2,
            opacity: 0.6,
            fillColor: 'transparent',
            dashArray: '4, 6',
          }}
        />
      )}

      {mahalla.roads.map((road, index) => (
        <Polyline
          key={index}
          positions={road}
          pathOptions={{
            color: '#64748b',
            weight: 1.5,
            opacity: 0.5,
          }}
        />
      ))}

      {mahalla.facilities.map((facility) => (
        <CircleMarker
          key={facility.id}
          center={facility.coords}
          radius={4}
          pathOptions={{
            color: '#10b981',
            fillColor: '#10b981',
            fillOpacity: 0.7,
            weight: 1,
          }}
        >
          <Popup>
            <strong>{facility.name}</strong><br />
            {facility.type}
          </Popup>
        </CircleMarker>
      ))}

      {mahalla.intersections.map((intersection) => {
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
                iconSize: [8, 8],
                iconAnchor: [4, 4],
              })
            }
          >
            <Popup>
              <strong>{intersection.name}</strong><br />
              {intersection.traffic_light_ids.length} {language === 'ru' ? 'кластер светофоров' : 'traffic-light cluster'}
            </Popup>
          </Marker>
        )
      })}

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
              iconSize: [20, 20],
              iconAnchor: [10, 10],
            })
          }
        >
          <Popup>
            <strong>{station.name}</strong><br />
            <span style={{ fontSize: '11px', color: '#64748b' }}>{station.source}</span>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
