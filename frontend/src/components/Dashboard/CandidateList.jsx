import React, { useEffect, useRef } from 'react'
import { animateEnter } from '../../utils/motion'

export function CandidateList({ t, optResult, selectedCandidate, setSelectedCandidateId, getIntersectionForTrafficLight, setSelectedId }) {
  const listRef = useRef(null)

  useEffect(() => {
    if (listRef.current) {
      animateEnter(listRef.current)
    }
  }, [optResult])

  const renderHeader = () => {
    if (!optResult?.ranked_candidates?.length) {
      return <h3>{t.interventions || 'Interventions'}</h3>
    }
    const total = optResult.ranked_candidates.length
    const simulated = optResult.ranked_candidates.filter(c => c.evaluation_mode === 'SIMULATED').length
    const estimated = total - simulated
    
    const totalStr = total === 1 ? t.oneIntervention : t.interventionOptions.replace('{total}', total)
    const simStr = simulated === 1 ? t.oneSimulated : t.simulatedCount.replace('{count}', simulated)
    const estStr = estimated === 1 ? t.oneEstimated : t.estimatedCount.replace('{count}', estimated)
    
    return <h3>{totalStr} · {simStr} · {estStr}</h3>
  }

  return (
    <div className="panel-card full-width-card" ref={listRef}>
      {renderHeader()}
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
              {candidate.evaluation_mode && (
                <span className={`provenance-badge ${candidate.evaluation_mode.toLowerCase()}`} style={{ display: 'inline-block', width: 'fit-content', marginTop: '-4px' }}>
                  {candidate.evaluation_mode === 'HEURISTIC' ? 'ESTIMATED' : candidate.evaluation_mode}
                </span>
              )}
              <p>{candidate.summary || candidate.description}</p>
              <div className="candidate-stats">
                <span>{t.speed}: {candidate.metrics.average_speed_kmh.toFixed(2)} km/h</span>
                <span>{t.timeLossCompleted || 'Time Loss'}: {(candidate.metrics.mean_completed_vehicle_waiting_seconds ?? candidate.metrics.average_waiting_seconds).toFixed(2)} s</span>
                <span>Δ CO2: {(candidate.delta.sumo_co2_kg ?? candidate.delta.co2_kg ?? 0).toFixed(2)}</span>
                <span>Δ NOx: {(candidate.delta.sumo_nox_g ?? candidate.delta.nox_g ?? 0).toFixed(2)}</span>
              </div>
            </button>
          ))
        ) : (
          <p>{t.runOptimization}</p>
        )}
      </div>
    </div>
  )
}
