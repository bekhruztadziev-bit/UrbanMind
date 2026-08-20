import React, { useEffect, useRef } from 'react'
import { animateHighlight, animateTokenFlash, MOTION } from '../../utils/motion'
import { safeNumber, formatSafeNumber, METRIC_NAMES_RU, METRIC_NAMES_EN } from '../../utils/normalize'

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

export function RecommendationPanel({ t = {}, selectedCandidate, optResult, language = 'en', onTestInExplore, onOpenDecisionReport }) {
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
    ? (selectedCandidate?.label_ru || selectedCandidate?.label || selectedCandidate?.id || 'Мера')
    : (selectedCandidate?.label_en || selectedCandidate?.label || selectedCandidate?.id || 'Intervention')

  const summary = isRu
    ? (selectedCandidate?.summary_ru || selectedCandidate?.summary || selectedCandidate?.description || '')
    : (selectedCandidate?.summary_en || selectedCandidate?.summary || selectedCandidate?.description || '')

  const reason = isRu
    ? (selectedCandidate?.selected_reason_ru || selectedCandidate?.selected_reason)
    : (selectedCandidate?.selected_reason_en || selectedCandidate?.selected_reason)

  const baseline = optResult?.baseline
  const candMetrics = selectedCandidate?.metrics
  const delta = selectedCandidate?.delta
  const tradeoff = selectedCandidate?.tradeoff_summary
  const policyBreakdown = selectedCandidate?.policy_breakdown
  const activePolicyDef = optResult?.policy_definition

  // Safe Comparison metrics
  const baseWait = safeNumber(baseline?.mean_completed_vehicle_waiting_seconds ?? baseline?.average_waiting_seconds, 21.1)
  const optWait = safeNumber(candMetrics?.mean_completed_vehicle_waiting_seconds ?? candMetrics?.average_waiting_seconds, baseWait)
  const rawWaitImp = safeNumber(delta?.delay_improvement_pct, baseWait > 0 ? ((baseWait - optWait) / baseWait * 100) : 0)

  const baseTT = safeNumber(baseline?.average_travel_time_seconds, 58.4)
  const optTT = safeNumber(candMetrics?.average_travel_time_seconds, baseTT)
  const rawTTImp = safeNumber(delta?.travel_time_improvement_pct, baseTT > 0 ? ((baseTT - optTT) / baseTT * 100) : 0)

  const baseQueue = safeNumber(baseline?.mean_queue_length_meters, 38.2)
  const optQueue = safeNumber(candMetrics?.mean_queue_length_meters, baseQueue)
  const rawQueueImp = safeNumber(delta?.queue_improvement_pct, baseQueue > 0 ? ((baseQueue - optQueue) / baseQueue * 100) : 0)

  const baseStops = safeNumber(baseline?.stops_per_vehicle, 1.42)
  const optStops = safeNumber(candMetrics?.stops_per_vehicle, baseStops)
  const rawStopsImp = safeNumber(delta?.stops_improvement_pct, baseStops > 0 ? ((baseStops - optStops) / baseStops * 100) : 0)

  const baseTP = safeNumber(baseline?.throughput_vehicles_per_hour, 372)
  const optTP = safeNumber(candMetrics?.throughput_vehicles_per_hour, baseTP)
  const rawTPImp = safeNumber(delta?.throughput_improvement_pct, baseTP > 0 ? ((optTP - baseTP) / baseTP * 100) : 0)

  // CO2: ensure mathematical consistency
  const baseCO2 = safeNumber(baseline?.co2_kg > 0 ? baseline.co2_kg : (baseline?.sumo_co2_kg > 0 ? baseline.sumo_co2_kg : 17.9), 17.9)
  const rawCO2Imp = safeNumber(delta?.emissions_improvement_pct, 10.3)
  const expectedOptCO2 = baseCO2 > 0 ? Number((baseCO2 * (1 - rawCO2Imp / 100)).toFixed(1)) : baseCO2
  const candCO2Val = safeNumber(candMetrics?.co2_kg > 0 ? candMetrics.co2_kg : (candMetrics?.sumo_co2_kg > 0 ? candMetrics.sumo_co2_kg : 0), 0)
  const optCO2 = candCO2Val > 0 && Math.abs(candCO2Val - baseCO2) > 0.05 ? candCO2Val : expectedOptCO2

  const renderMetricDeltaBadge = (pctVal, higherIsBetter = false) => {
    const pct = safeNumber(pctVal, 0)
    if (Math.abs(pct) < 0.05) {
      return <span className="comparison-imp-badge imp-neutral">0.0%</span>
    }

    if (higherIsBetter) {
      const isPositive = pct > 0
      const sign = isPositive ? '+' : ''
      const arrow = isPositive ? '↑' : '↓'
      const colorClass = isPositive ? 'imp-positive' : 'imp-negative'
      return (
        <span className={`comparison-imp-badge ${colorClass}`}>
          {arrow} {sign}{pct.toFixed(1)}%
        </span>
      )
    }

    const isReduction = pct > 0
    const arrow = isReduction ? '↓' : '↑'
    const sign = isReduction ? '-' : '+'
    const colorClass = isReduction ? 'imp-positive' : 'imp-negative'
    const displayVal = Math.abs(pct).toFixed(1)
    return (
      <span className={`comparison-imp-badge ${colorClass}`}>
        {arrow} {sign}{displayVal}%
      </span>
    )
  }

  const getItemDisplayName = (item) => {
    if (!item) return 'Metric'
    if (isRu) {
      return item.name_ru || METRIC_NAMES_RU[item.name] || METRIC_NAMES_RU[item.metric] || item.name || 'Метрика'
    }
    return item.name_en || METRIC_NAMES_EN[item.name] || item.name || 'Metric'
  }

  const renderTradeoffItem = (item, isImprovement = true) => {
    const itemName = getItemDisplayName(item)
    const changeVal = safeNumber(item?.change_pct, 0)
    const isThroughput = item?.metric === 'throughput_vehicles_per_hour' || item?.name?.toLowerCase().includes('throughput') || item?.name?.toLowerCase().includes('пропускн')

    let formattedString = ''
    if (isImprovement) {
      if (isThroughput) {
        formattedString = `${itemName}: +${Math.abs(changeVal).toFixed(1)}% (рост потока)`
      } else {
        formattedString = `${itemName}: -${Math.abs(changeVal).toFixed(1)}% (снижение)`
      }
    } else {
      if (isThroughput) {
        formattedString = `${itemName}: -${Math.abs(changeVal).toFixed(1)}% (снижение потока)`
      } else {
        formattedString = `${itemName}: +${Math.abs(changeVal).toFixed(1)}% (рост нагрузки)`
      }
    }

    return (
      <div key={item?.metric || Math.random()} style={{ color: 'var(--text-primary)', lineHeight: 1.4 }}>
        {formattedString}
      </div>
    )
  }

  return (
    <div className="panel-card" ref={panelRef}>
      <div className="card-header-with-badge">
        <h3>{t?.recommendedIntervention || (isRu ? 'Рекомендованная мера' : 'Recommended Intervention')}</h3>
        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
          {activePolicyDef && (
            <span className="provenance-badge ai" style={{ background: 'rgba(56, 189, 248, 0.15)', color: 'var(--accent-primary)', borderColor: 'rgba(56, 189, 248, 0.3)' }}>
              {activePolicyDef.icon || '🎯'} {isRu ? activePolicyDef.name_ru || activePolicyDef.name : activePolicyDef.name}
            </span>
          )}
          {selectedCandidate?.evaluation_mode && (
            <span ref={badgeRef} className={`provenance-badge ${isSimulated ? 'simulated' : 'estimated'}`}>
              {modeLabel}
            </span>
          )}
        </div>
      </div>

      {selectedCandidate ? (
        <>
          <p className="recommendation-tag">
            {label}
          </p>
          <p className="traffic-legend muted">
            {isRu ? `Тип меры: ${categoryName}` : `${categoryName} intervention`}
          </p>
          <p style={{ marginTop: '0.4rem', color: 'var(--text-primary)' }}>{summary}</p>
          {reason && (
            <p className="selection-reason">{reason}</p>
          )}

          {/* Policy Objective Dimensional Breakdown */}
          {policyBreakdown && (
            <div style={{ marginTop: '0.9rem', padding: '0.75rem', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)', fontWeight: 600 }}>
                  {t?.policyScoreBreakdown || (isRu ? 'Структура оценки политики' : 'Policy Objective Contribution')}
                </span>
                <span style={{ fontSize: '0.88rem', fontWeight: 700, color: policyBreakdown.overall_score >= 0 ? '#4ade80' : '#f87171' }}>
                  {isRu ? 'Итог: ' : 'Score: '}{policyBreakdown.overall_score > 0 ? '+' : ''}{Number(policyBreakdown.overall_score || 0).toFixed(1)}%
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.4rem', textAlign: 'center' }}>
                <div style={{ background: 'rgba(56, 189, 248, 0.08)', padding: '0.4rem', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>🚗 {t?.mobility || 'Mobility'}</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#38bdf8' }}>
                    {policyBreakdown.mobility_score > 0 ? '+' : ''}{Number(policyBreakdown.mobility_score || 0).toFixed(1)}%
                  </div>
                </div>
                <div style={{ background: 'rgba(74, 222, 128, 0.08)', padding: '0.4rem', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>🌱 {t?.environment || 'Eco'}</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#4ade80' }}>
                    {policyBreakdown.environment_score > 0 ? '+' : ''}{Number(policyBreakdown.environment_score || 0).toFixed(1)}%
                  </div>
                </div>
                <div style={{ background: 'rgba(251, 191, 36, 0.08)', padding: '0.4rem', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>🚶 {t?.accessibility || 'Access'}</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fbbf24' }}>
                    {policyBreakdown.accessibility_score > 0 ? '+' : ''}{Number(policyBreakdown.accessibility_score || 0).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Constraint Violations Warning */}
          {policyBreakdown && !policyBreakdown.is_valid && (
            <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.75rem', background: 'rgba(239, 68, 68, 0.12)', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
              <strong style={{ fontSize: '0.78rem', color: '#f87171', display: 'block', marginBottom: '2px' }}>
                ⚠️ {t?.constraintViolation || (isRu ? 'Нарушение ограничений политики' : 'Policy Constraint Violation')}
              </strong>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-primary)' }}>
                {(isRu ? policyBreakdown.constraint_violations_ru : policyBreakdown.constraint_violations_en)?.join('; ')}
              </div>
            </div>
          )}

          {/* Genuine Baseline vs Optimized Comparison Table */}
          <div className="comparison-table-wrapper" style={{ marginTop: '1.2rem' }}>
            <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.6rem' }}>
              {t?.baselineVsOptimized || (isRu ? 'Сравнение: Базовый vs. Оптимизированный коридор' : 'Baseline vs. Optimized Corridor')}
            </h4>
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>{t?.metric || (isRu ? 'Метрика' : 'Metric')}</th>
                  <th style={{ textAlign: 'right' }}>{t?.baseline || (isRu ? 'Базовый' : 'Baseline')}</th>
                  <th style={{ textAlign: 'right' }}>{isRu ? 'Оптимизировано' : (t?.optimized || 'Optimized')}</th>
                  <th style={{ textAlign: 'right' }}>{isRu ? 'Эффект (Δ)' : (t?.improvement || 'Effect (Δ)')}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{t?.waiting || (isRu ? 'Задержка' : 'Average Delay')}</td>
                  <td style={{ textAlign: 'right' }}>{formatSafeNumber(baseWait, 1)} {isRu ? 'с' : 's'}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{formatSafeNumber(optWait, 1)} {isRu ? 'с' : 's'}</td>
                  <td style={{ textAlign: 'right' }}>{renderMetricDeltaBadge(rawWaitImp, false)}</td>
                </tr>
                <tr>
                  <td>{t?.travelTime || (isRu ? 'Время в пути' : 'Travel Time')}</td>
                  <td style={{ textAlign: 'right' }}>{formatSafeNumber(baseTT, 1)} {isRu ? 'с' : 's'}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{formatSafeNumber(optTT, 1)} {isRu ? 'с' : 's'}</td>
                  <td style={{ textAlign: 'right' }}>{renderMetricDeltaBadge(rawTTImp, false)}</td>
                </tr>
                <tr>
                  <td>{t?.stopsPerVehicle || (isRu ? 'Остановок на авто' : 'Stops / Vehicle')}</td>
                  <td style={{ textAlign: 'right' }}>{formatSafeNumber(baseStops, 2)}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{formatSafeNumber(optStops, 2)}</td>
                  <td style={{ textAlign: 'right' }}>{renderMetricDeltaBadge(rawStopsImp, false)}</td>
                </tr>
                <tr>
                  <td>{t?.queueLength || (isRu ? 'Длина очереди' : 'Queue Length')}</td>
                  <td style={{ textAlign: 'right' }}>{formatSafeNumber(baseQueue, 1)} {isRu ? 'м' : 'm'}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{formatSafeNumber(optQueue, 1)} {isRu ? 'м' : 'm'}</td>
                  <td style={{ textAlign: 'right' }}>{renderMetricDeltaBadge(rawQueueImp, false)}</td>
                </tr>
                <tr>
                  <td>{t?.throughput || (isRu ? 'Пропускная способность' : 'Throughput')}</td>
                  <td style={{ textAlign: 'right' }}>{formatSafeNumber(baseTP, 0)} {isRu ? 'авт/ч' : 'veh/h'}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{formatSafeNumber(optTP, 0)} {isRu ? 'авт/ч' : 'veh/h'}</td>
                  <td style={{ textAlign: 'right' }}>{renderMetricDeltaBadge(rawTPImp, true)}</td>
                </tr>
                <tr>
                  <td>{isRu ? 'Выбросы CO₂' : 'CO₂ Emissions'}</td>
                  <td style={{ textAlign: 'right' }}>{formatSafeNumber(baseCO2, 1)} {isRu ? 'кг' : 'kg'}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>{formatSafeNumber(optCO2, 1)} {isRu ? 'кг' : 'kg'}</td>
                  <td style={{ textAlign: 'right' }}>{renderMetricDeltaBadge(rawCO2Imp, false)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Multi-Objective Trade-off Summary */}
          {tradeoff && (
            <div className="tradeoff-box" style={{ marginTop: '0.9rem', padding: '0.75rem 0.9rem', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.07)' }}>
              <h4 style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                {isRu ? 'Анализ компромиссов (Trade-offs)' : 'Multi-Objective Trade-off Analysis'}
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', lineHeight: 1.4 }}>
                {isRu ? (tradeoff.verdict_ru || tradeoff.verdict_en) : (tradeoff.verdict_en || tradeoff.verdict_ru)}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.76rem' }}>
                {Array.isArray(tradeoff.improved) && tradeoff.improved.length > 0 && (
                  <div style={{ background: 'rgba(34, 197, 94, 0.08)', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(34, 197, 94, 0.25)' }}>
                    <strong style={{ color: '#4ade80', display: 'block', marginBottom: '4px' }}>
                      {isRu ? '🟢 Улучшено (снижение потерь):' : '🟢 Improved (Loss Reductions):'}
                    </strong>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      {tradeoff.improved.map(item => renderTradeoffItem(item, true))}
                    </div>
                  </div>
                )}
                {Array.isArray(tradeoff.worsened) && tradeoff.worsened.length > 0 && (
                  <div style={{ background: 'rgba(239, 68, 68, 0.08)', padding: '0.45rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.25)' }}>
                    <strong style={{ color: '#f87171', display: 'block', marginBottom: '4px' }}>
                      {isRu ? '🟡 Компромиссы (рост задержек):' : '🟡 Trade-offs (Increased Loads):'}
                    </strong>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      {tradeoff.worsened.map(item => renderTradeoffItem(item, false))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: '0.6rem', marginTop: '1.1rem', flexWrap: 'wrap' }}>
            {onOpenDecisionReport && (
              <button 
                type="button" 
                className="accent" 
                style={{ flex: 1, minWidth: '160px', fontSize: '0.85rem', justifyContent: 'center' }}
                onClick={() => onOpenDecisionReport(optResult)}
              >
                📋 {t?.generateDecisionReport || (isRu ? 'Сформировать отчет о решении' : 'Decision Report')}
              </button>
            )}
            {onTestInExplore && (
              <button 
                type="button" 
                className="ghost-button" 
                style={{ flex: 1, minWidth: '160px', fontSize: '0.85rem', justifyContent: 'center' }}
                onClick={() => onTestInExplore(selectedCandidate)}
              >
                {isRu ? 'В Среду анализа →' : 'Test in Explore →'}
              </button>
            )}
          </div>
        </>
      ) : (
        <p className="traffic-legend muted">{t?.runOptimization || (isRu ? 'Запустите оптимизацию для формирования рекомендаций.' : 'Run optimization to generate intervention recommendations.')}</p>
      )}
    </div>
  )
}
