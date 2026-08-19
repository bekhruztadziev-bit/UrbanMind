import React, { useEffect, useRef } from 'react'
import { animateEnter, staggerEnter, animateHighlight } from '../../utils/motion'

export function CandidateList({ t, optResult, selectedCandidate, setSelectedCandidateId, getIntersectionForTrafficLight, setSelectedId, language = 'en' }) {
  const isRu = language === 'ru'
  const containerRef = useRef(null)
  const listRef = useRef(null)

  useEffect(() => {
    if (containerRef.current) {
      animateEnter(containerRef.current, 40)
    }
    if (listRef.current) {
      const cards = listRef.current.querySelectorAll('.candidate-card')
      if (cards.length > 0) {
        staggerEnter(cards, 60)
      }
    }
  }, [optResult])

  const renderHeader = () => {
    if (!optResult?.ranked_candidates?.length) {
      return <h3>{t.interventions || 'Interventions'}</h3>
    }
    const total = optResult.ranked_candidates.length
    const simulated = optResult.ranked_candidates.filter(c => c.evaluation_mode === 'SIMULATED').length
    const estimated = total - simulated
    
    const totalStr = total === 1 ? (t.oneIntervention || '1 intervention') : (t.interventionOptions ? t.interventionOptions.replace('{total}', total) : `${total} interventions`)
    const simStr = simulated === 1 ? (t.oneSimulated || '1 simulated') : (t.simulatedCount ? t.simulatedCount.replace('{count}', simulated) : `${simulated} simulated`)
    const estStr = estimated === 1 ? (t.oneEstimated || '1 estimated') : (t.estimatedCount ? t.estimatedCount.replace('{count}', estimated) : `${estimated} estimated`)
    
    return <h3>{totalStr} · {simStr} · {estStr}</h3>
  }

  const handleCardClick = (e, candidate) => {
    animateHighlight(e.currentTarget)
    setSelectedCandidateId(candidate.id)
    const match = getIntersectionForTrafficLight(candidate.intervention?.traffic_light_id)
    if (match) {
      setSelectedId(match.id)
    }
  }

  return (
    <div className="panel-card full-width-card" ref={containerRef}>
      {renderHeader()}
      <div className="candidate-list" ref={listRef}>
        {optResult?.ranked_candidates?.length ? (
          optResult.ranked_candidates.map((candidate) => {
            const label = isRu
              ? (candidate.label_ru || candidate.label || candidate.id)
              : (candidate.label_en || candidate.label || candidate.id)
            const summary = isRu
              ? (candidate.summary_ru || candidate.summary || candidate.description)
              : (candidate.summary_en || candidate.summary || candidate.description)
            const modeText = candidate.evaluation_mode === 'HEURISTIC'
              ? (isRu ? 'ОЦЕНЕНО' : 'ESTIMATED')
              : (isRu ? 'СМОДЕЛИРОВАНО' : candidate.evaluation_mode)

            return (
              <button
                key={candidate.id}
                type="button"
                className={`candidate-card ${selectedCandidate?.id === candidate.id ? 'selected' : ''}`}
                onClick={(e) => handleCardClick(e, candidate)}
              >
                <div className="candidate-header">
                  <strong>{label}</strong>
                  <span>{candidate.score.toFixed(2)}</span>
                </div>
                {candidate.evaluation_mode && (
                  <span className={`provenance-badge ${candidate.evaluation_mode.toLowerCase()}`} style={{ display: 'inline-block', width: 'fit-content', marginTop: '-4px' }}>
                    {modeText}
                  </span>
                )}
                <p>{summary}</p>
                <div className="candidate-stats">
                  <span>{t.speed || 'Speed'}: {candidate.metrics.average_speed_kmh.toFixed(2)} km/h</span>
                  <span>{t.timeLossCompleted || 'Time Loss'}: {(candidate.metrics.mean_completed_vehicle_waiting_seconds ?? candidate.metrics.average_waiting_seconds).toFixed(2)} s</span>
                  <span>Δ CO2: {(candidate.delta.sumo_co2_kg ?? candidate.delta.co2_kg ?? 0).toFixed(2)}</span>
                  <span>Δ NOx: {(candidate.delta.sumo_nox_g ?? candidate.delta.nox_g ?? 0).toFixed(2)}</span>
                </div>
              </button>
            )
          })
        ) : (
          <p className="traffic-legend muted">{t.runOptimization || 'Run optimization to compare candidate interventions.'}</p>
        )}
      </div>
    </div>
  )
}

