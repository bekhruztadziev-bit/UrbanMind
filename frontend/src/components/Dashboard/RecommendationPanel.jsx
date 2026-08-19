import React from 'react'

export function RecommendationPanel({ t, selectedCandidate, language, onTestInExplore }) {
  const isSimulated = selectedCandidate?.evaluation_mode === 'SIMULATED'
  const modeLabel = isSimulated ? 'SIMULATED' : 'ESTIMATED'

  const formatDelta = (val, suffix = '') => {
    if (val === undefined || val === null || isNaN(val)) return '0.00' + suffix
    const num = Number(val)
    const sign = num > 0 ? '+' : ''
    return `${sign}${num.toFixed(2)}${suffix}`
  }

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
            {selectedCandidate.label || selectedCandidate.id}
          </p>
          <p className="traffic-legend muted">{selectedCandidate.category || 'mobility'} {language === 'ru' ? 'вмешательство' : 'intervention'}</p>
          <p style={{ marginTop: '0.4rem', color: 'var(--text-primary)' }}>{selectedCandidate.summary || selectedCandidate.description}</p>
          {selectedCandidate.selected_reason && (
            <p className="selection-reason">{selectedCandidate.selected_reason}</p>
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
            {language === 'ru' ? 'Тестировать в Среде анализа →' : 'Test in Explore Workspace →'}
          </button>
        </>
      ) : (
        <p className="traffic-legend muted">{t.runOptimization || 'Run optimization to generate intervention recommendations.'}</p>
      )}
    </div>
  )
}

