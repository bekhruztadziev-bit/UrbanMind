import React from 'react'
import { safeNumber, INTERVENTION_LABELS_RU } from '../../utils/normalize'

// Robustness criterion: "effective" = waiting time delta < 0 (intervention reduces waiting vs control)
// This criterion is documented here and displayed in the UI.
const EFFECTIVE_CRITERION_LABEL = 'Effective = average observed waiting time reduced vs same-demand control'

const EVAL_BADGE = {
  SIMULATED: { label: 'SUMO', color: '#38bdf8', bg: 'rgba(56,189,248,0.16)' },
  HEURISTIC: { label: 'Heuristic', color: '#fbbf24', bg: 'rgba(245,158,11,0.16)' },
}

function robustnessBadge(effective, total) {
  if (total === 0) return { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)', symbol: '—' }
  if (effective === total) return { color: '#34d399', bg: 'rgba(16,185,129,0.15)', symbol: '✓' }
  if (effective === 0) return { color: '#f87171', bg: 'rgba(239,68,68,0.12)', symbol: '✗' }
  return { color: '#fbbf24', bg: 'rgba(245,158,11,0.12)', symbol: '~' }
}

export function RobustnessSummary({ result, t = {} }) {
  if (!result || !result.conditions || !Array.isArray(result.conditions) || result.conditions.length === 0) {
    return <div className="panel-card empty-state"><p>{t?.noData || 'No data.'}</p></div>
  }

  const trafficLevels = [...new Set(result.conditions.map(c => c?.traffic_multiplier).filter(v => v != null))].sort((a, b) => a - b)
  const totalLevels = trafficLevels.length

  // Gather unique interventions
  const interventions = []
  const seen = new Set()
  for (const cond of result.conditions) {
    if (!cond || !cond.intervention_id || seen.has(cond.intervention_id)) continue
    seen.add(cond.intervention_id)
    const rawLabel = cond.intervention_label || cond.intervention_id
    interventions.push({
      id: cond.intervention_id,
      label: cond.intervention_label_ru || INTERVENTION_LABELS_RU[rawLabel] || rawLabel,
      evaluation_mode: cond.evaluation_mode || 'HEURISTIC',
    })
  }

  const condIndex = {}
  for (const cond of result.conditions) {
    if (cond) {
      condIndex[`${cond.traffic_multiplier}|${cond.intervention_id}`] = cond
    }
  }

  const robustnessRows = interventions.map(iv => {
    let effectiveCount = 0
    let completedCount = 0
    const perLevel = trafficLevels.map(tl => {
      const cond = condIndex[`${tl}|${iv.id}`]
      if (!cond || cond.status !== 'COMPLETED') return { tl, effective: null }
      completedCount++
      const delta = cond.metric_deltas?.mean_completed_vehicle_waiting_seconds?.absolute
      const effective = delta != null ? Number(delta) < 0 : null
      if (effective) effectiveCount++
      return {
        tl,
        effective,
        delta,
        pct: cond.metric_deltas?.mean_completed_vehicle_waiting_seconds?.percentage
      }
    })
    return { iv, effectiveCount, completedCount, totalLevels, perLevel }
  })

  // Sort: most effective first
  robustnessRows.sort((a, b) => b.effectiveCount - a.effectiveCount)

  const simulatedRows = robustnessRows.filter(r => r.iv.evaluation_mode === 'SIMULATED')
  const heuristicRows = robustnessRows.filter(r => r.iv.evaluation_mode !== 'SIMULATED')

  const renderRowGroup = (rows, title) => {
    if (rows.length === 0) return null
    return (
      <div style={{ marginBottom: '1.5rem' }}>
        {title && <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#94a3b8' }}>{title}</h4>}
        <div style={{ display: 'grid', gap: '0.6rem' }}>
          {rows.map(({ iv, effectiveCount, completedCount, perLevel }) => {
            const badge = EVAL_BADGE[iv.evaluation_mode] || EVAL_BADGE.HEURISTIC
            const { color, bg, symbol } = robustnessBadge(effectiveCount, completedCount)

            return (
            <div key={iv.id} style={{ background: bg, border: `1px solid ${color}25`, borderRadius: '12px', padding: '0.65rem 0.9rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '1rem', color, fontWeight: 800 }}>{symbol}</span>
                <strong style={{ color: '#f8fafc', fontSize: '0.88rem' }}>{iv.label}</strong>
                <span style={{ fontSize: '0.7rem', padding: '2px 6px', borderRadius: '4px', color: badge.color, background: badge.bg }}>
                  {badge.label}
                </span>
                <span style={{ marginLeft: 'auto', fontSize: '0.82rem', color, fontWeight: 700 }}>
                  Effective in {effectiveCount} / {completedCount} demand conditions
                </span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {perLevel.map(({ tl, effective, pct }) => {
                  const pctNum = pct != null && !isNaN(pct) ? safeNumber(pct, 0) : null
                  return (
                    <span
                      key={tl}
                      style={{
                        fontSize: '0.75rem',
                        padding: '2px 8px',
                        borderRadius: '999px',
                        background: effective === true ? 'rgba(16,185,129,0.15)' : effective === false ? 'rgba(239,68,68,0.12)' : 'rgba(148,163,184,0.15)',
                        color: effective === true ? '#4ade80' : effective === false ? '#f87171' : '#94a3b8',
                      }}
                    >
                      {tl}×{pctNum != null ? ` ${pctNum > 0 ? '+' : ''}${pctNum.toFixed(1)}%` : ' —'}
                    </span>
                  )
                })}
              </div>
            </div>
          )
        })}
        </div>
      </div>
    )
  }

  return (
    <div className="panel-card full-width-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <h3 style={{ marginTop: 0 }}>{t?.robustnessSummary || 'Robustness Summary'}</h3>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          <strong>{t?.criterion || 'Criterion'}:</strong> {EFFECTIVE_CRITERION_LABEL}
        </div>
      </div>
      {renderRowGroup(simulatedRows, 'Simulated Interventions')}
      {renderRowGroup(heuristicRows, 'Heuristic Interventions')}

      <p style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.75rem' }}>
        {t?.disclaimer || 'Waiting time deltas are vs same-demand control. Heuristic values are estimates, not direct SUMO measurements.'}
      </p>
    </div>
  )
}
