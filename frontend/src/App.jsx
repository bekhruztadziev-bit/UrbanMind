import { useEffect, useMemo, useState } from 'react'
import L from 'leaflet'
import { CircleMarker, MapContainer, Marker, Polygon, Popup, Polyline, TileLayer } from 'react-leaflet'
import { fetchHealth, fetchMahalla, fetchMetrics, fetchOptimize } from './api'
import './App.css'

const translations = {
  en: {
    appTitle: 'MAHALLAMIND',
    headerTitle: 'Interactive mahalla digital twin',
    apiOnline: 'API online',
    dashboard: 'Dashboard',
    faq: 'FAQ',
    selectedLocation: 'Selected location',
    trafficLights: 'Traffic lights',
    targetSignal: 'Target signal',
    selectedSignal: 'Selected signal',
    localFacility: 'Local facility',
    neighborhoodCopy: 'Local flow is shown across the active neighborhood corridor, with signal focus and contextual access mapped to the roads residents actually use.',
    avgSpeed: 'Avg. speed',
    waiting: 'Waiting',
    liveFlow: 'Live flow',
    peak: 'Peak',
    signals: 'Signals',
    access: 'Access',
    analyze: 'Analyze',
    optimizing: 'Optimizing…',
    analyzing: 'Analyzing…',
    optimize: 'Optimize',
    baseline: 'Baseline',
    peakVehicles: 'Peak vehicles',
    recommendedIntervention: 'Recommended intervention',
    runOptimization: 'Run optimization to compare intervention candidates.',
    whyChoice: 'Why this choice?',
    explanationAfter: 'AI explanation appears after optimization.',
    mahallaPosition: 'MAHALLAMIND position',
    neighborhoodMobilityIntelligence: 'Neighborhood mobility intelligence',
    interventionOptions: '3 intervention options',
    speed: 'Speed',
    wait: 'Wait',
    deltaSpeed: 'Δ speed',
    deltaWait: 'Δ wait',
    confidence: 'Confidence',
    bestSignalId: 'Best signal ID',
    signalFocus: 'Signal focus: the most effective corridor timing change in the current scenario.',
    optimizationScope: 'Optimization scope: local signal timing only.',
    expectedImpact: 'Expected impact: modest delay reduction and improved discharge at the main bottleneck.',
    neighborhoodPlatform: 'MAHALLAMIND is a neighborhood mobility intelligence platform for local signal and flow decisions.',
    neighborhoodContext: 'It helps neighborhood teams act before congestion affects daily movement and access.',
    backendOffline: 'Backend unavailable; offline preview is shown.',
    fallbackSelection: 'not selected',
    backToDashboard: 'Back to dashboard',
    language: 'RU',
    scenario: 'Scenario',
    morning: 'Morning peak',
    midday: 'Midday',
    evening: 'Evening peak',
    faqPageTitle: 'Frequently asked questions',
    faqPageIntro: 'This page explains how the model works, what it measures, and how neighborhood-level decisions are evaluated in practice.',
    faqSections: [
      {
        q: 'What is the analysis area?',
        a: 'The analysis area is the local neighborhood corridor and its main access links. It covers only the physically relevant district, so the intervention remains understandable and actionable for local decision-makers.',
      },
      {
        q: 'Why are the traffic-light icons removed?',
        a: 'The map is designed to emphasize the neighborhood operating context rather than decorative control symbols. This makes the area easier to read and keeps the focus on the actual intervention logic.',
      },
      {
        q: 'Why are the vehicles no longer animated?',
        a: 'Animated vehicle markers add visual noise and can suggest unrealistic motion across water or non-road features. A simplified map reads more clearly and avoids misleading interpretations.',
      },
      {
        q: 'What does optimization compare?',
        a: 'It evaluates realistic local interventions such as phase changes, pedestrian priority, bus priority, and safety-oriented adjustments using delay, emissions, accessibility, and network throughput as decision criteria.',
      },
      {
        q: 'What is the purpose of the dashboard?',
        a: 'The dashboard supports quick comparison between current conditions and recommended interventions so a user can assess whether a local mobility change improves flow without losing clarity or public access.',
      },
      {
        q: 'How should I interpret the results?',
        a: 'Use the recommended option as a decision support input, not as an unquestioned mandate. The strongest choice is the one that improves the corridor while keeping the district legible, safe, and accessible.',
      },
    ],
  },
  ru: {
    appTitle: 'MAHALLAMIND',
    headerTitle: 'Интерактивная цифровая двойня района',
    apiOnline: 'API онлайн',
    dashboard: 'Панель',
    faq: 'FAQ',
    selectedLocation: 'Выбранный участок',
    trafficLights: 'Светофоры',
    targetSignal: 'Целевой сигнал',
    selectedSignal: 'Выбранный сигнал',
    localFacility: 'Локальный объект',
    neighborhoodCopy: 'Поток отображается по активному коридору района, а приоритет и доступность привязаны к дорогам, которыми пользуются жители.',
    avgSpeed: 'Средняя скорость',
    waiting: 'Ожидание',
    liveFlow: 'Поток',
    peak: 'Пик',
    signals: 'Сигналы',
    access: 'Доступ',
    analyze: 'Анализ',
    optimizing: 'Оптимизация…',
    analyzing: 'Анализ…',
    optimize: 'Оптимизировать',
    baseline: 'Базовый сценарий',
    peakVehicles: 'Пик транспорта',
    recommendedIntervention: 'Рекомендуемое решение',
    runOptimization: 'Запустите оптимизацию, чтобы сравнить варианты вмешательства.',
    whyChoice: 'Почему этот вариант?',
    explanationAfter: 'Объяснение ИИ появится после оптимизации.',
    mahallaPosition: 'Позиция MAHALLAMIND',
    neighborhoodMobilityIntelligence: 'Интеллект мобильности района',
    interventionOptions: '3 варианта вмешательства',
    speed: 'Скорость',
    wait: 'Ожидание',
    deltaSpeed: 'Δ скорость',
    deltaWait: 'Δ ожидание',
    confidence: 'Уверенность',
    bestSignalId: 'Лучший сигнал ID',
    signalFocus: 'Фокус сигнала: наиболее эффективное изменение фаз коридора в текущем сценарии.',
    optimizationScope: 'Объём оптимизации: локальная настройка сигналов.',
    expectedImpact: 'Ожидаемый эффект: умеренное снижение задержек и улучшение выпуска транспорта на главном узком месте.',
    neighborhoodPlatform: 'MAHALLAMIND — платформа интеллектуальной мобильности района для локальных решений по сигналам и потокам.',
    neighborhoodContext: 'Она помогает местным командам действовать до того, как заторы начнут влиять на повседневное движение и доступность.',
    backendOffline: 'Сервер недоступен; показан офлайн-превью.',
    fallbackSelection: 'не выбрано',
    backToDashboard: 'Назад к панели',
    language: 'EN',
    scenario: 'Сценарий',
    morning: 'Утренний пик',
    midday: 'Полдень',
    evening: 'Вечерний пик',
    faqPageTitle: 'Часто задаваемые вопросы',
    faqPageIntro: 'Эта страница объясняет, как работает модель, какие показатели она оценивает и как принимаются решения на уровне района.',
    faqSections: [
      {
        q: 'Что входит в зону анализа?',
        a: 'В зону анализа входят локальный районный коридор и основные точки доступа. Она охватывает только ту территорию, которая реально влияет на движение и решения местных органов, чтобы сценарий оставался понятным и применимым на практике.',
      },
      {
        q: 'Почему значки светофоров убраны?',
        a: 'Карта теперь подчеркивает контекст района и логику вмешательства, а не декоративные элементы управления. Это делает карту более читаемой и помогает сосредоточиться на реальном решении.',
      },
      {
        q: 'Почему машины больше не анимированы?',
        a: 'Анимированные маркеры создают визуальный шум и могут вводить в заблуждение, будто транспорт движется по воде или вне дорог. Упрощённая карта лучше передаёт реальную структуру района и снижает ложные интерпретации.',
      },
      {
        q: 'Что именно сравнивает оптимизация?',
        a: 'Она сравнивает реалистичные локальные меры — изменение фаз светофора, приоритет пешеходам, приоритет общественному транспорту и меры по повышению безопасности — на основе задержек, выбросов, доступности и пропускной способности.',
      },
      {
        q: 'Какова цель панели управления?',
        a: 'Панель нужна для быстрого сравнения текущих условий и рекомендуемого решения, чтобы пользователь мог понять, улучшает ли локальная мера поток без потери ясности и общественной доступности.',
      },
      {
        q: 'Как правильно интерпретировать результаты?',
        a: 'Рекомендуемый вариант следует воспринимать как инструмент поддержки решения, а не как безусловную команду. Лучшее решение — это то, которое снижает задержки и сохраняет понятность, безопасность и доступность района.',
      },
    ],
  },
}

const fallbackMahalla = {
  name: 'Yakkabog District (offline preview)',
  bounds: {
    name: 'Yakkabog District',
    southwest: [41.3052, 69.2564],
    northeast: [41.3276, 69.2804],
    polygon: [
      [41.3052, 69.2564],
      [41.3052, 69.2804],
      [41.3276, 69.2804],
      [41.3276, 69.2564],
    ],
  },
  intersections: [
    { id: 'intersection_1', name: 'Central Crossroads', coords: [39.0842, 66.8615], traffic_light_ids: ['cluster_1'] },
    { id: 'intersection_2', name: 'School Junction', coords: [39.0886, 66.8668], traffic_light_ids: ['cluster_2'] },
    { id: 'intersection_3', name: 'Market Roundabout', coords: [39.0809, 66.8531], traffic_light_ids: ['cluster_3'] },
  ],
  roads: [
    [[39.074, 66.846], [39.096, 66.846]],
    [[39.074, 66.861], [39.096, 66.861]],
    [[39.074, 66.879], [39.096, 66.879]],
    [[39.0815, 66.846], [39.0815, 66.879]],
    [[39.089, 66.846], [39.089, 66.879]],
  ],
  facilities: [
    { id: 'school_1', type: 'school', name: 'District School', coords: [39.0883, 66.8661] },
    { id: 'clinic_1', type: 'clinic', name: 'Community Clinic', coords: [39.0821, 66.8576] },
    { id: 'kindergarten_1', type: 'kindergarten', name: 'Kindergarten #2', coords: [39.0851, 66.8504] },
    { id: 'bus_stop_1', type: 'bus_stop', name: 'Market Stop', coords: [39.0901, 66.8584] },
  ],
}

const defaultMetrics = {
  average_speed_kmh: 0,
  average_waiting_seconds: 0,
  max_vehicle_count: 0,
  traffic_light_count: 0,
}

function App() {
  const [health, setHealth] = useState(null)
  const [mahalla, setMahalla] = useState(null)
  const [scenario, setScenario] = useState('midday')
  const [selectedId, setSelectedId] = useState('intersection_1')
  const [selectedCandidateId, setSelectedCandidateId] = useState(null)
  const [metrics, setMetrics] = useState(defaultMetrics)
  const [optResult, setOptResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [language, setLanguage] = useState('en')
  const [currentView, setCurrentView] = useState('dashboard')

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [healthResponse, mahallaResponse] = await Promise.all([
          fetchHealth(),
          fetchMahalla(),
        ])
        setHealth(healthResponse)
        setMahalla(mahallaResponse)
      } catch (err) {
        setHealth({ ok: false })
        setMahalla(fallbackMahalla)
        setError(t.backendOffline)
      }
    }

    loadInitialData()
  }, [])

  const getIntersectionForTrafficLight = (trafficLightId) => {
    if (!mahalla || !trafficLightId) return null
    return mahalla.intersections.find((item) => item.traffic_light_ids.includes(trafficLightId)) || null
  }

  const selectedIntersection = useMemo(() => {
    if (!mahalla) return null
    return mahalla.intersections.find((item) => item.id === selectedId) || mahalla.intersections[0]
  }, [mahalla, selectedId])

  const selectedCandidate = useMemo(() => {
    if (!optResult) return null
    const list = optResult.ranked_candidates || []
    if (selectedCandidateId) {
      return list.find((candidate) => candidate.id === selectedCandidateId) || optResult.best_candidate || null
    }
    return optResult.best_candidate || null
  }, [optResult, selectedCandidateId])

  const targetSignalId = selectedCandidate?.intervention?.traffic_light_id || selectedIntersection?.traffic_light_ids?.[0] || null
  const t = translations[language]

  const handleAnalyze = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await fetchMetrics({ steps: 300, scenario })
      setMetrics(data)
      setOptResult(null)
      setSelectedCandidateId(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!optResult?.best_candidate || !mahalla) return
    const match = getIntersectionForTrafficLight(optResult.best_candidate.intervention?.traffic_light_id)
    if (match) {
      setSelectedId(match.id)
    }
  }, [optResult, mahalla])

  const handleOptimize = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await fetchOptimize({ steps: 300, scenario })
      setOptResult(data)
      setMetrics(data.baseline)
      setSelectedCandidateId(data.best_candidate?.id || null)
      setSelectedId('intersection_1')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const mapCenter = selectedIntersection ? [selectedIntersection.coords[0], selectedIntersection.coords[1]] : [41.317, 69.267]
  const mapBounds = useMemo(() => {
    const bounds = mahalla?.bounds
    if (!bounds) return null
    return [bounds.southwest, bounds.northeast]
  }, [mahalla])

  const boundaryPolygon = useMemo(() => {
    if (!mahalla?.bounds?.polygon) return []
    return mahalla.bounds.polygon
  }, [mahalla])

  const boundaryBounds = useMemo(() => {
    const bounds = mahalla?.bounds
    if (!bounds?.southwest || !bounds?.northeast) return null
    return {
      sw: [bounds.southwest[0], bounds.southwest[1]],
      ne: [bounds.northeast[0], bounds.northeast[1]],
    }
  }, [mahalla])

  const boundaryCube = useMemo(() => {
    if (!boundaryBounds) return null
    const { sw, ne } = boundaryBounds
    const latSpan = ne[0] - sw[0]
    const lngSpan = ne[1] - sw[1]
    const skewLat = latSpan * 0.18
    const skewLng = lngSpan * 0.18

    const topLeft = [sw[0] + latSpan * 0.06, sw[1] + lngSpan * 0.08]
    const topRight = [ne[0] + latSpan * 0.06, sw[1] + lngSpan * 0.08]
    const farRight = [ne[0] + skewLat, ne[1] + skewLng]
    const farLeft = [sw[0] - skewLat, ne[1] - skewLng]
    const bottomLeft = [sw[0], sw[1]]
    const bottomRight = [ne[0], ne[1]]

    return {
      outer: [
        bottomLeft,
        topLeft,
        topRight,
        farRight,
        bottomRight,
        farLeft,
      ],
      inner: [
        [bottomLeft[0] + latSpan * 0.12, bottomLeft[1] + lngSpan * 0.12],
        [topLeft[0] + latSpan * 0.08, topLeft[1] + lngSpan * 0.08],
        [topRight[0] + latSpan * 0.08, topRight[1] + lngSpan * 0.08],
        [farRight[0] - skewLat * 0.12, farRight[1] - skewLng * 0.12],
        [bottomRight[0] - latSpan * 0.12, bottomRight[1] - lngSpan * 0.12],
        [farLeft[0] + skewLat * 0.12, farLeft[1] + skewLng * 0.12],
      ],
    }
  }, [boundaryBounds])

  const flowDots = useMemo(() => {
    if (!mahalla?.roads) return []

    const points = []

    mahalla.roads.forEach((road, roadIndex) => {
      for (let i = 0; i < road.length - 1; i += 1) {
        const start = road[i]
        const end = road[i + 1]
        const totalSteps = Math.max(18, Math.round(Math.hypot(end[0] - start[0], end[1] - start[1]) * 9000))

        for (let step = 0; step <= totalSteps; step += 1) {
          const ratio = step / totalSteps
          const lat = start[0] + (end[0] - start[0]) * ratio
          const lng = start[1] + (end[1] - start[1]) * ratio
          const laneOffset = (roadIndex % 2 === 0 ? 1 : -1) * 0.00008
          const offsetAngle = ((roadIndex % 3) + 1) * 0.35
          const offsetLat = Math.cos(offsetAngle) * laneOffset
          const offsetLng = Math.sin(offsetAngle) * laneOffset

          points.push({
            id: `road-${roadIndex}-segment-${i}-dot-${step}`,
            coords: [lat + offsetLat, lng + offsetLng],
            radius: 2.2 + ((step + roadIndex) % 3) * 0.35,
          })
        }
      }
    })

    return points
  }, [mahalla])

  const liveVehicleCount = useMemo(() => {
    const peak = Number.isFinite(metrics.max_vehicle_count) ? metrics.max_vehicle_count : 0
    return peak ? Math.max(12, Math.round(peak * 0.7)) : 0
  }, [metrics.max_vehicle_count])

  if (!mahalla) {
    return <div className="app-shell loading">Loading MahallaMind…</div>
  }

  if (currentView === 'faq') {
    return (
      <div className="app-shell faq-shell">
        <header className="topbar topbar-faq">
          <div className="brand-wrap">
            <div className="brand-mark">M</div>
            <div>
              <p className="eyebrow">MAHALLAMIND</p>
              <h1>{t.faqPageTitle}</h1>
            </div>
          </div>
          <div className="topbar-actions">
            <button type="button" className="ghost-button" onClick={() => setCurrentView('dashboard')}>{t.backToDashboard}</button>
            <button type="button" className="language-toggle" onClick={() => setLanguage((value) => (value === 'en' ? 'ru' : 'en'))}>{t.language}</button>
          </div>
        </header>

        <main className="faq-page">
          <p className="faq-intro">{t.faqPageIntro}</p>
          <div className="faq-list">
            {t.faqSections.map((item) => (
              <article key={item.q} className="faq-entry">
                <h3>{item.q}</h3>
                <p>{item.a}</p>
              </article>
            ))}
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <div className="map-panel">
        <header className="map-header">
          <div className="brand-wrap">
            <div className="brand-mark">M</div>
            <div>
              <p className="eyebrow">{t.appTitle}</p>
              <h1>{t.headerTitle}</h1>
            </div>
          </div>
          <div className="topbar-actions">
            <div className="scenario-toggle" aria-label={t.scenario}>
              {['morning', 'midday', 'evening'].map((value) => (
                <button
                  key={value}
                  type="button"
                  className={scenario === value ? 'scenario-button active' : 'scenario-button'}
                  onClick={() => setScenario(value)}
                >
                  {t[value]}
                </button>
              ))}
            </div>
            <button type="button" className="ghost-button" onClick={() => setCurrentView('dashboard')}>{t.dashboard}</button>
            <button type="button" className="ghost-button" onClick={() => setCurrentView('faq')}>{t.faq}</button>
            <button type="button" className="language-toggle" onClick={() => setLanguage((value) => (value === 'en' ? 'ru' : 'en'))}>{t.language}</button>
          </div>
        </header>

        <MapContainer
          center={mapCenter}
          bounds={mapBounds}
          boundsOptions={{ padding: [24, 24] }}
          scrollWheelZoom
          className="map-container"
          zoom={15}
          minZoom={12}
          maxZoom={18}
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {boundaryCube && (
            <>
              <Polygon
                positions={boundaryCube.outer}
                pathOptions={{
                  color: '#dfe7ee',
                  weight: 3.2,
                  opacity: 1,
                  fillColor: '#facc15',
                  fillOpacity: 0,
                  lineJoin: 'miter',
                  lineCap: 'square',
                  smoothFactor: 0,
                }}
              />
              <Polygon
                positions={boundaryCube.inner}
                pathOptions={{
                  color: '#facc15',
                  weight: 1.6,
                  opacity: 0.95,
                  fillColor: '#facc15',
                  fillOpacity: 0,
                  lineJoin: 'miter',
                  lineCap: 'square',
                  smoothFactor: 0,
                }}
              />
            </>
          )}

          {mahalla.roads.map((road, index) => (
            <Polyline
              key={index}
              positions={road}
              pathOptions={{
                color: '#cbd5e1',
                weight: 2.2,
                opacity: 0.8,
              }}
            />
          ))}

          {flowDots.map((dot) => (
            <CircleMarker
              key={dot.id}
              center={dot.coords}
              radius={dot.radius}
              pathOptions={{
                color: '#fbbf24',
                fillColor: '#facc15',
                fillOpacity: 0.72,
                weight: 0.8,
              }}
            />
          ))}

          {mahalla.facilities.map((facility) => (
            <CircleMarker
              key={facility.id}
              center={facility.coords}
              radius={5.2}
              pathOptions={{
                color: '#6ee7b7',
                fillColor: '#10b981',
                fillOpacity: 0.9,
                weight: 2,
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
                    iconSize: [12, 12],
                    iconAnchor: [6, 6],
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
        </MapContainer>
      </div>

      <aside className="sidebar">
        <div className="panel-card">
          <h2>{t.selectedLocation}</h2>
          {selectedIntersection && (
            <>
              <p className="location-name">{selectedIntersection.name}</p>
              <p>ID: {selectedIntersection.id}</p>
              <p>{t.trafficLights}: {selectedIntersection.traffic_light_ids.length}</p>
              <p className="traffic-legend">{t.targetSignal}: {targetSignalId || t.fallbackSelection}</p>
              <div className="legend-box">
                <div><span className="legend-swatch signal" /> {t.selectedSignal}</div>
                <div><span className="legend-swatch facility" /> {t.localFacility}</div>
              </div>
              <p className="traffic-legend muted">{t.neighborhoodCopy}</p>
            </>
          )}
        </div>

        <div className="panel-card metric-grid">
          <div>
            <span>{t.avgSpeed}</span>
            <strong>{metrics.average_speed_kmh.toFixed(2)} km/h</strong>
          </div>
          <div>
            <span>{t.waiting}</span>
            <strong>{metrics.average_waiting_seconds.toFixed(2)} s</strong>
          </div>
          <div>
            <span>CO2</span>
            <strong>{(metrics.co2_kg ?? 0).toFixed(1)} kg</strong>
          </div>
          <div>
            <span>NOx</span>
            <strong>{(metrics.nox_g ?? 0).toFixed(1)} g</strong>
          </div>
          <div>
            <span>{t.liveFlow}</span>
            <strong>{liveVehicleCount}</strong>
          </div>
          <div>
            <span>{t.peak}</span>
            <strong>{metrics.max_vehicle_count}</strong>
          </div>
          <div>
            <span>{t.signals}</span>
            <strong>{metrics.traffic_light_count}</strong>
          </div>
          <div>
            <span>{t.access}</span>
            <strong>{(metrics.accessibility_score ?? 100).toFixed(0)}%</strong>
          </div>
        </div>

        <div className="panel-card button-stack">
          <button type="button" onClick={handleAnalyze} disabled={loading}>
            {loading ? t.analyzing : t.analyze}
          </button>
          <button type="button" className="accent" onClick={handleOptimize} disabled={loading}>
            {loading ? t.optimizing : t.optimize}
          </button>
        </div>

        {error && <div className="panel-card error-box">{error}</div>}
      </aside>

      <section className="results-panel">
        <div className="panel-card">
          <h3>{t.baseline}</h3>
          <div className="two-col">
            <div><span>{t.avgSpeed}</span><strong>{(optResult?.baseline?.average_speed_kmh ?? metrics.average_speed_kmh).toFixed(2)} km/h</strong></div>
            <div><span>{t.waiting}</span><strong>{(optResult?.baseline?.average_waiting_seconds ?? metrics.average_waiting_seconds).toFixed(2)} s</strong></div>
            <div><span>{t.liveFlow}</span><strong>{liveVehicleCount}</strong></div>
            <div><span>{t.peakVehicles}</span><strong>{optResult?.baseline?.max_vehicle_count ?? metrics.max_vehicle_count}</strong></div>
          </div>
        </div>

        <div className="panel-card">
          <h3>{t.recommendedIntervention}</h3>
          {selectedCandidate ? (
            <>
              <p className="recommendation-tag">{selectedCandidate.label || selectedCandidate.id}</p>
              <p className="traffic-legend muted">{selectedCandidate.category || 'mobility'} {language === 'ru' ? 'вмешательство' : 'intervention'}</p>
              <p>{selectedCandidate.summary || selectedCandidate.description}</p>
              {selectedCandidate.selected_reason && (
                <p className="selection-reason">{selectedCandidate.selected_reason}</p>
              )}
              <div className="two-col">
                <div><span>{t.speed}</span><strong>{selectedCandidate.metrics.average_speed_kmh.toFixed(2)} km/h</strong></div>
                <div><span>{t.wait}</span><strong>{selectedCandidate.metrics.average_waiting_seconds.toFixed(2)} s</strong></div>
                <div><span>CO2</span><strong>{(selectedCandidate.metrics.co2_kg ?? 0).toFixed(1)} kg</strong></div>
                <div><span>{t.access}</span><strong>{(selectedCandidate.metrics.accessibility_score ?? 100).toFixed(0)}%</strong></div>
                <div><span>{t.deltaSpeed}</span><strong>{selectedCandidate.delta.average_speed_kmh.toFixed(2)}</strong></div>
                <div><span>{t.deltaWait}</span><strong>{selectedCandidate.delta.average_waiting_seconds.toFixed(2)}</strong></div>
              </div>
            </>
          ) : (
            <p>{t.runOptimization}</p>
          )}
        </div>

        <div className="panel-card">
          <h3>{t.whyChoice}</h3>
          {optResult?.ai ? (
            <>
              <p><strong>{optResult.ai.recommendation}</strong></p>
              <p className="selection-reason">{optResult.ai.signal_focus || t.signalFocus}</p>
              <p className="traffic-legend muted">{optResult.ai.scope || t.optimizationScope}</p>
              <p>{optResult.ai.reasoning}</p>
              <ul>
                {optResult.ai.tradeoffs.map((item) => <li key={item}>{item}</li>)}
              </ul>
              <p className="confidence">{t.confidence}: {optResult.ai.confidence}</p>
              <p className="traffic-legend muted">{optResult.ai.expected_impact || t.expectedImpact}</p>
              {optResult.ai.best_signal_id ? <p className="traffic-legend muted">{t.bestSignalId}: {optResult.ai.best_signal_id}</p> : null}
            </>
          ) : (
            <p>{t.explanationAfter}</p>
          )}
        </div>

        <div className="panel-card">
          <h3>{t.mahallaPosition}</h3>
          <p className="recommendation-tag">{t.neighborhoodMobilityIntelligence}</p>
          <p>{optResult?.insights?.headline || t.neighborhoodPlatform}</p>
          <p className="selection-reason">{optResult?.insights?.context || t.neighborhoodContext}</p>
        </div>

        <div className="panel-card full-width-card">
          <h3>{t.interventionOptions}</h3>
          <div className="candidate-list">
            {optResult?.ranked_candidates?.length ? (
              optResult.ranked_candidates.map((candidate) => (
                <button
                  key={candidate.id}
                  type="button"
                  className={`candidate-card ${selectedCandidate?.id === candidate.id ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedCandidateId(candidate.id)
                    const match = getIntersectionForTrafficLight(candidate.intervention?.traffic_light_id)
                    if (match) {
                      setSelectedId(match.id)
                    }
                  }}
                >
                  <div className="candidate-header">
                    <strong>{candidate.label || candidate.id}</strong>
                    <span>{candidate.score.toFixed(2)}</span>
                  </div>
                  <p>{candidate.summary || candidate.description}</p>
                  <div className="candidate-stats">
                    <span>{t.speed}: {candidate.metrics.average_speed_kmh.toFixed(2)} km/h</span>
                    <span>{t.wait}: {candidate.metrics.average_waiting_seconds.toFixed(2)} s</span>
                    <span>{t.deltaSpeed}: {candidate.delta.average_speed_kmh.toFixed(2)}</span>
                    <span>{t.deltaWait}: {candidate.delta.average_waiting_seconds.toFixed(2)}</span>
                  </div>
                </button>
              ))
            ) : (
              <p>{t.runOptimization}</p>
            )}
          </div>
        </div>
      </section>

    </div>
  )
}

export default App
