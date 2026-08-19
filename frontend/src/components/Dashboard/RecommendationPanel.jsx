import React from 'react'

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

export function RecommendationPanel({ t, selectedCandidate, language, onTestInExplore }) {
  const isRu = language === 'ru'
  const isSimulated = selectedCandidate?.evaluation_mode === 'SIMULATED'
  const modeLabel = isSimulated
    ? (isRu ? 'СМОДЕЛИРОВАНО' : 'SIMULATED')
    : (isRu ? 'ОЦЕНЕНО' : 'ESTIMATED')

  const formatDelta = (val, suffix = '') => {
    if (val === undefined || val === null || isNaN(val)) return '0.00' + suffix
    const num = Number(val)
    const sign = num > 0 ? '+' : ''
    return `${sign}${num.toFixed(2)}${suffix}`
  }

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

  return (
    <div className="panel-card">
      <div className="card-header-with-badge">
        <h3>{t.recommendedIntervention || 'Recommended Intervention'}</h3>
        {selectedCandidate?.evaluation_mode && (
          <span className={`provenance-badge ${isSimulated ? 'simulated' : 'estimated'}`}>
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
          <div className="two-col mt-3">
            <div><span>{t.speed || 'Speed'}</span><strong>{selectedCandidate.metrics.average_speed_kmh.toFixed(2)} km/h</strong></div>
            <div><span>{t.timeLossCompleted || 'Time Loss'}</span><strong>{(selectedCandidate.metrics.mean_completed_vehicle_waiting_seconds ?? selectedCandidate.metrics.average_waiting_seconds).toFixed(2)} s</strong></div>
            <div><span>CO2</span><strong>{(selectedCandidate.metrics.co2_kg ?? 0).toFixed(1)} kg</strong></div>
            <div><span>{t.access || 'Access'}</span><strong>{(selectedCandidate.metrics.accessibility_score ?? 100).toFixed(0)}%</strong></div>
            <div><span>{t.deltaSpeed || 'Δ Speed'}</span><strong>{formatDelta(selectedCandidate.delta.average_speed_kmh, ' km/h')}</strong></div>
            <div><span>{t.deltaWait || 'Δ Wait'}</span><strong>{formatDelta(selectedCandidate.delta.mean_completed_vehicle_waiting_seconds ?? selectedCandidate.delta.average_waiting_seconds, ' s')}</strong></div>
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

