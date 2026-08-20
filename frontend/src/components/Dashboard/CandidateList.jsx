import React, { useEffect, useRef } from 'react'
import { animateEnter, staggerEnter, animateHighlight, MOTION } from '../../utils/motion'
import { safeNumber, formatSafeNumber, INTERVENTION_LABELS_RU, translateInterventionSummaryToRu } from '../../utils/normalize'

export function CandidateList({ t = {}, optResult, selectedCandidate, setSelectedCandidateId, getIntersectionForTrafficLight, setSelectedId, language = 'en' }) {
  const isRu = language === 'ru'
  const containerRef = useRef(null)
  const listRef = useRef(null)

  useEffect(() => {
    if (containerRef.current) {
      animateEnter(containerRef.current, { duration: MOTION.normal })
    }
    if (listRef.current) {
      const cards = listRef.current.querySelectorAll('.candidate-card')
      if (cards.length > 0) {
        staggerEnter(cards, { baseDelay: MOTION.staggerSmall, duration: MOTION.normal, y: 8 })
      }
    }
  }, [optResult])

  const renderHeader = () => {
    if (!optResult?.ranked_candidates?.length) {
      return <h3>{t?.interventions || (isRu ? 'Варианты мер' : 'Interventions')}</h3>
    }
    const total = optResult.ranked_candidates.length
    const simulated = optResult.ranked_candidates.filter(c => c?.evaluation_mode === 'SIMULATED').length
    const estimated = total - simulated
    
    if (isRu) {
      const totalStr = `${total} вариантов мер`
      const simStr = `${simulated} смоделировано`
      const estStr = `${estimated} оценено`
      return <h3>{totalStr} · {simStr} · {estStr}</h3>
    }
    
    const totalStr = total === 1 ? '1 intervention' : `${total} interventions`
    const simStr = simulated === 1 ? '1 simulated' : `${simulated} simulated`
    const estStr = estimated === 1 ? '1 estimated' : `${estimated} estimated`
    
    return <h3>{totalStr} · {simStr} · {estStr}</h3>
  }

  const handleCardClick = (e, candidate) => {
    if (!candidate) return
    animateHighlight(e.currentTarget)
    setSelectedCandidateId(candidate.id)
    if (getIntersectionForTrafficLight && candidate.intervention?.traffic_light_id) {
      const match = getIntersectionForTrafficLight(candidate.intervention.traffic_light_id)
      if (match && setSelectedId) {
        setSelectedId(match.id)
      }
    }
  }

  return (
    <div className="panel-card full-width-card" ref={containerRef}>
      {renderHeader()}
      <div className="candidate-list" ref={listRef}>
        {optResult?.ranked_candidates?.length ? (
          optResult.ranked_candidates.map((candidate) => {
            if (!candidate) return null
            const labelEn = candidate.label_en || candidate.label || candidate.id || 'Intervention'
            const labelRu = candidate.label_ru || INTERVENTION_LABELS_RU[candidate.label] || INTERVENTION_LABELS_RU[labelEn] || labelEn
            const label = isRu ? labelRu : labelEn

            const summaryEn = candidate.summary_en || candidate.summary || candidate.description || ''
            const summaryRu = candidate.summary_ru || translateInterventionSummaryToRu(summaryEn, labelRu)
            const summary = isRu ? summaryRu : summaryEn

            const modeText = candidate.evaluation_mode === 'HEURISTIC'
              ? (isRu ? 'ОЦЕНЕНО' : 'ESTIMATED')
              : (isRu ? 'СМОДЕЛИРОВАНО' : (candidate.evaluation_mode || 'ESTIMATED'))

            const score = safeNumber(candidate.score, 0)
            const speed = safeNumber(candidate.metrics?.average_speed_kmh, 0)
            const waitTime = safeNumber(candidate.metrics?.mean_completed_vehicle_waiting_seconds ?? candidate.metrics?.average_waiting_seconds, 0)
            const co2Delta = safeNumber(candidate.delta?.sumo_co2_kg ?? candidate.delta?.co2_kg, 0)
            const noxDelta = safeNumber(candidate.delta?.sumo_nox_g ?? candidate.delta?.nox_g, 0)

            return (
              <button
                key={candidate.id || Math.random()}
                type="button"
                className={`candidate-card ${selectedCandidate?.id === candidate.id ? 'selected' : ''}`}
                onClick={(e) => handleCardClick(e, candidate)}
              >
                <div className="candidate-header">
                  <strong>{label}</strong>
                  <span>{formatSafeNumber(score, 2)}</span>
                </div>
                {candidate.evaluation_mode && (
                  <span className={`provenance-badge ${(candidate.evaluation_mode || '').toLowerCase()}`} style={{ display: 'inline-block', width: 'fit-content', marginTop: '-4px' }}>
                    {modeText}
                  </span>
                )}
                <p>{summary}</p>
                <div className="candidate-stats">
                  <span>{t?.speed || (isRu ? 'Скорость' : 'Speed')}: {formatSafeNumber(speed, 2)} {isRu ? 'км/ч' : 'km/h'}</span>
                  <span>{t?.timeLossCompleted || (isRu ? 'Ожидание завершенных поездок' : 'Time Loss')}: {formatSafeNumber(waitTime, 2)} {isRu ? 'с' : 's'}</span>
                  <span>Δ CO2: {formatSafeNumber(co2Delta, 2)}</span>
                  <span>Δ NOx: {formatSafeNumber(noxDelta, 2)}</span>
                </div>
              </button>
            )
          })
        ) : (
          <p className="traffic-legend muted">{t?.runOptimization || (isRu ? 'Запустите оптимизацию для сравнения вариантов мер.' : 'Run optimization to compare candidate interventions.')}</p>
        )}
      </div>
    </div>
  )
}
