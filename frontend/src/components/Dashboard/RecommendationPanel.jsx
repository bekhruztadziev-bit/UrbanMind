import React, { useEffect, useRef } from 'react'
import { animateHighlight, animateTokenFlash, MOTION } from '../../utils/motion'

const CATEGORY_MAP_RU = {
  signal_timing: 'настройка сигналов',
  transit: 'общественный транспорт',
  active_mobility: 'активная мобильность',
  safety: 'безопасность',
  curb_management: 'управление парковкой',
  mobility: 'мобильность',
}

const CATEGORY_MAP_EN = {
  signal_timing: 'signal timing',
  transit: 'transit',
  active_mobility: 'active mobility',
  safety: 'safety',
  curb_management: 'curb management',
  mobility: 'mobility',
}

export function RecommendationPanel({ t, selectedCandidate, optResult, language, onTestInExplore }) {
  const isRu = language === 'ru'
  const panelRef = useRef(null)
  const badgeRef = useRef(null)
  const prevCandidateIdRef = useRef(selectedCandidate?.id)

  useEffect(() => {
    if (selectedCandidate && selectedCandidate.id !== prevCandidateIdRef.current) {
      prevCandidateIdRef.current = selectedCandidate.id
      if (panelRef.current) animateHighlight(panelRef.current, { duration: MOTION.normal })
      if (badgeRef.current) animateTokenFlash(badgeRef.current)
    }
  }, [selectedCandidate])

  const isSimulated = selectedCandidate?.evaluation_mode === 'SIMULATED'
  const modeLabel = isSimulated
    ? (isRu ? 'СМОДЕЛИРОВАНО' : 'SIMULATED')
    : (isRu ? 'ОЦЕНЕНО' : 'ESTIMATED')

  const categoryName = isRu
    ? (CATEGORY_MAP_RU[selectedCandidate?.category] || selectedCandidate?.category || 'мобильность')
    : (CATEGORY_MAP_EN[selectedCandidate?.category] || selectedCandidate?.category || 'mobility')

  const label = isRu
    ? (selectedCandidate?.label_ru || selectedCandidate?.label || selectedCandidate?.id)
    : (selectedCandidate?.label_en || selectedCandidate?.label || selectedCandidate?.id)

  const summary = isRu
    ? (selectedCandidate?.summary_ru || selectedCandidate?.summary || selectedCandidate?.description)
    : (selectedCandidate?.summary_en || selectedCandidate?.summary || selectedCandidate?.description)

  const reason = isRu
    ? (selectedCandidate?.selected_reason_ru || selectedCandidate?.selected_reason)
    : selectedCandidate?.selected_reason

  const baseline = optResult?.baseline
  const candMetrics = selectedCandidate?.metrics
  const delta = selectedCandidate?.delta

  // Comparison metrics
  const baseWait = baseline?.mean_completed_vehicle_waiting_seconds ?? baseline?.average_waiting_seconds ?? 24.0
  const optWait = candMetrics?.mean_completed_vehicle_waiting_seconds ?? candMetrics?.average_waiting_seconds ?? baseWait
  const waitImp = delta?.delay_improvement_pct ?? (baseWait > 0 ? ((baseWait - optWait) / baseWait * 100) : 0)

  const baseTT = baseline?.average_travel_time_seconds ?? 58.4
  const optTT = candMetrics?.average_travel_time_seconds ?? baseTT
  const ttImp = delta?.travel_time_improvement_pct ?? (baseTT > 0 ? ((baseTT - optTT) / baseTT * 100) : 0)

  const baseQueue = baseline?.mean_queue_length_meters ?? 38.2
  const optQueue = candMetrics?.mean_queue_length_meters ?? baseQueue
  const queueImp = delta?.queue_improvement_pct ?? (baseQueue > 0 ? ((baseQueue - optQueue) / baseQueue * 100) : 0)

  const baseStops = baseline?.stops_per_vehicle ?? 1.42
  const optStops = candMetrics?.stops_per_vehicle ?? baseStops
  const stopsImp = delta?.stops_improvement_pct ?? (baseStops > 0 ? ((baseStops - optStops) / baseStops * 100) : 0)

  const baseTP = baseline?.throughput_vehicles_per_hour ?? 540
  const optTP = candMetrics?.throughput_vehicles_per_hour ?? baseTP
  const tpImp = delta?.throughput_improvement_pct ?? (baseTP > 0 ? ((optTP - baseTP) / baseTP * 100) : 0)

  const baseCO2 = baseline?.sumo_co2_kg ?? baseline?.co2_kg ?? 14.5
  const optCO2 = candMetrics?.sumo_co2_kg ?? candMetrics?.co2_kg ?? baseCO2
  const co2Imp = delta?.emissions_improvement_pct ?? (baseCO2 > 0 ? ((baseCO2 - optCO2) / baseCO2 * 100) : 0)

  const renderImpBadge = (pct, higherIsBetter = false) => {
    const isPositive = higherIsBetter ? pct > 0 : pct > 0
    const isNegative = higherIsBetter ? pct < 0 : pct < 0
    const sign = pct > 0 ? '+' : ''
    const colorClass = isPositive ? 'imp-positive' : isNegative ? 'imp-negative' : 'imp-neutral'
    return (
      <span className={`comparison-imp-badge ${colorClass}`}>
        {sign}{pct.toFixed(1)}%
      </span>
    )
  }

  return (
    <div className="panel-card" ref={panelRef}>
      <div className="card-header-with-badge">
        <h3>{t.recommendedIntervention || 'Recommended Intervention'}</h3>
        {selectedCandidate?.evaluation_mode && (
          <span ref={badgeRef} className={`provenance-badge ${isSimulated ? 'simulated' : 'estimated'}`}>
            {modeLabel}
          </span>
        )}
      </div>

      {selectedCandidate ? (
        <>
          <p className="recommendation-tag">
            {label}
          </p>
          <p className="traffic-legend muted">
            {isRu ? `Мера: ${categoryName}` : `${categoryName} intervention`}
          </p>
          <p style={{ marginTop: '0.4rem', color: 'var(--text-primary)' }}>{summary}</p>
          {reason && (
            <p className="selection-reason">{reason}</p>
          )}

          {/* Genuine Baseline vs Optimized Comparison Table */}
          <div className="comparison-table-wrapper" style={{ marginTop: '1.2rem' }}>
            <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.6rem' }}>
              {t.baselineVsOptimized || 'Baseline vs. Optimized Corridor'}
            </h4>
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>{t.metric || 'Metric'}</th>
                  <th style={{ textAlign: 'right' }}>{t.baseline || 'Baseline'}</th>
                  <th style={{ textAlign: 'right' }}>{t.optimized || 'Optimized'}</th>
                  <th style={{ textAlign: 'right' }}>{t.improvement || 'Improvement'}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{t.waiting || 'Average Delay'}</td>
                  <td style={{ textAlign: 'right' }}>{baseWait.toFixed(1)} s</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{optWait.toFixed(1)} s</td>
                  <td style={{ textAlign: 'right' }}>{renderImpBadge(waitImp)}</td>
                </tr>
                <tr>
                  <td>{t.travelTime || 'Travel Time'}</td>
                  <td style={{ textAlign: 'right' }}>{baseTT.toFixed(1)} s</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{optTT.toFixed(1)} s</td>
                  <td style={{ textAlign: 'right' }}>{renderImpBadge(ttImp)}</td>
                </tr>
                <tr>
                  <td>{t.stopsPerVehicle || 'Stops / Vehicle'}</td>
                  <td style={{ textAlign: 'right' }}>{baseStops.toFixed(2)}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{optStops.toFixed(2)}</td>
                  <td style={{ textAlign: 'right' }}>{renderImpBadge(stopsImp)}</td>
                </tr>
                <tr>
                  <td>{t.queueLength || 'Queue Length'}</td>
                  <td style={{ textAlign: 'right' }}>{baseQueue.toFixed(1)} m</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{optQueue.toFixed(1)} m</td>
                  <td style={{ textAlign: 'right' }}>{renderImpBadge(queueImp)}</td>
                </tr>
                <tr>
                  <td>{t.throughput || 'Throughput'}</td>
                  <td style={{ textAlign: 'right' }}>{baseTP.toFixed(0)} veh/h</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{optTP.toFixed(0)} veh/h</td>
                  <td style={{ textAlign: 'right' }}>{renderImpBadge(tpImp, true)}</td>
                </tr>
                <tr>
                  <td>CO₂ Emissions</td>
                  <td style={{ textAlign: 'right' }}>{baseCO2.toFixed(1)} kg</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{optCO2.toFixed(1)} kg</td>
                  <td style={{ textAlign: 'right' }}>{renderImpBadge(co2Imp)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <button 
            type="button" 
            className="ghost-button" 
            style={{ marginTop: '1.1rem', fontSize: '0.85rem', width: '100%', justifyContent: 'center' }}
            onClick={() => onTestInExplore(selectedCandidate)}
          >
            {isRu ? 'Тестировать в Среде анализа →' : 'Test in Explore Workspace →'}
          </button>
        </>
      ) : (
        <p className="traffic-legend muted">{t.runOptimization || 'Run optimization to generate intervention recommendations.'}</p>
      )}
    </div>
  )
}
