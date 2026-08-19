import React from 'react'

export function RecommendationPanel({ t, selectedCandidate, language, onTestInExplore }) {
  return (
    <div className="panel-card">
      <h3>{t.recommendedIntervention}</h3>
      {selectedCandidate ? (
        <>
          <p className="recommendation-tag">
            {selectedCandidate.label || selectedCandidate.id}
          </p>
          {selectedCandidate.evaluation_mode && (
            <span className={`eval-badge ${selectedCandidate.evaluation_mode.toLowerCase()}`} style={{ display: 'inline-block', width: 'fit-content', marginBottom: '0.6rem', marginTop: '-0.2rem' }}>
              {selectedCandidate.evaluation_mode}
            </span>
          )}
          <p className="traffic-legend muted">{selectedCandidate.category || 'mobility'} {language === 'ru' ? 'вмешательство' : 'intervention'}</p>
          <p>{selectedCandidate.summary || selectedCandidate.description}</p>
          {selectedCandidate.selected_reason && (
            <p className="selection-reason">{selectedCandidate.selected_reason}</p>
          )}
          <div className="two-col">
            <div><span>{t.speed}</span><strong>{selectedCandidate.metrics.average_speed_kmh.toFixed(2)} km/h</strong></div>
            <div><span>{t.timeLossCompleted || 'Time Loss'}</span><strong>{selectedCandidate.metrics.mean_completed_vehicle_waiting_seconds?.toFixed(2) ?? selectedCandidate.metrics.average_waiting_seconds?.toFixed(2)} s</strong></div>
            <div><span>CO2</span><strong>{(selectedCandidate.metrics.co2_kg ?? 0).toFixed(1)} kg</strong></div>
            <div><span>{t.access}</span><strong>{(selectedCandidate.metrics.accessibility_score ?? 100).toFixed(0)}%</strong></div>
            <div><span>{t.deltaSpeed}</span><strong>{selectedCandidate.delta.average_speed_kmh.toFixed(2)}</strong></div>
            <div><span>{t.deltaWait}</span><strong>{selectedCandidate.delta.mean_completed_vehicle_waiting_seconds?.toFixed(2) ?? selectedCandidate.delta.average_waiting_seconds?.toFixed(2)}</strong></div>
          </div>
          <button 
            type="button" 
            className="ghost-button" 
            style={{ marginTop: '1rem', fontSize: '0.85rem' }}
            onClick={() => onTestInExplore(selectedCandidate)}
          >
            {language === 'ru' ? 'Тестировать в Среде анализа →' : 'Test in Explore Workspace →'}
          </button>
        </>
      ) : (
        <p>{t.runOptimization}</p>
      )}
    </div>
  )
}
