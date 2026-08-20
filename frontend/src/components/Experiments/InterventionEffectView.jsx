import React, { useState } from 'react'
import { safeNumber, formatSafeNumber, INTERVENTION_LABELS_RU } from '../../utils/normalize'

const EVAL_BADGE = {
  SIMULATED: { label: 'SIMULATED', className: 'provenance-badge simulated' },
  HEURISTIC: { label: 'ESTIMATED', className: 'provenance-badge estimated' },
}

export function InterventionEffectView({ result, t = {} }) {
  const [focusMetric, setFocusMetric] = useState('mean_completed_vehicle_waiting_seconds')

  if (!result || !result.conditions || !Array.isArray(result.conditions) || result.conditions.length === 0) {
    return <div className="panel-card empty-state"><p>{t?.noData || 'No data.'}</p></div>
  }

  const trafficLevels = [...new Set(result.conditions.map(c => c?.traffic_multiplier).filter(v => v != null))].sort((a, b) => a - b)

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

  const METRIC_LABELS = {
    mean_completed_vehicle_waiting_seconds: t?.timeLossCompleted || 'Completed-Trip Mean Time Loss',
    mean_active_vehicle_waiting_seconds: t?.timeLossActive || 'Active-Vehicle Mean Time Loss',
    average_waiting_seconds: t?.waitingLegacy || 'Step-weighted wait (legacy)',
    average_speed_kmh: t?.speed || 'Avg Speed',
    max_vehicle_count: t?.peakVehicles || 'Peak Vehicles',
    sumo_co2_kg: 'CO₂',
    sumo_nox_g: 'NOₓ',
    co2_kg: 'CO₂ est.',
    nox_g: 'NOₓ est.',
    noise_db: 'Noise est.',
    pedestrian_delay_seconds: 'Pedestrian Delay',
    accessibility_score: t?.access || 'Accessibility',
  }

  const higherWorse = ['mean_completed_vehicle_waiting_seconds', 'mean_active_vehicle_waiting_seconds', 'average_waiting_seconds', 'max_vehicle_count', 'sumo_co2_kg', 'sumo_nox_g', 'co2_kg', 'nox_g', 'noise_db', 'pedestrian_delay_seconds']

  return (
    <div className="panel-card full-width-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
        <h3 style={{ margin: 0 }}>{t?.interventionEffect || 'Intervention Effect by Demand Level'}</h3>
        <select
          value={focusMetric}
          onChange={e => setFocusMetric(e.target.value)}
          style={{ fontSize: '0.85rem', padding: '0.35rem 0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}
        >
          {Object.entries(METRIC_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '0.75rem' }}>
        {interventions.map(iv => {
          const badge = EVAL_BADGE[iv.evaluation_mode] || EVAL_BADGE.HEURISTIC
          return (
            <div key={iv.id} className="panel-card" style={{ background: 'var(--bg-card)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <strong style={{ fontSize: '0.88rem', color: 'var(--text-primary)' }}>{iv.label}</strong>
                <span className={badge.className}>
                  {badge.label}
                </span>
              </div>
              <div style={{ display: 'grid', gap: '0.35rem' }}>
                {trafficLevels.map(tl => {
                  const cond = condIndex[`${tl}|${iv.id}`]
                  const pct = cond?.metric_deltas?.[focusMetric]?.percentage
                  const abs = cond?.metric_deltas?.[focusMetric]?.absolute
                  const isHigherWorse = higherWorse.includes(focusMetric)
                  const improved = abs != null ? (isHigherWorse ? abs < 0 : abs > 0) : null
                  const barColor = improved === true ? '#34d399' : improved === false ? '#f87171' : 'var(--text-muted)'
                  const pctWidth = pct != null && !isNaN(pct) ? Math.min(Math.abs(Number(pct)), 50) * 2 : 0

                  return (
                    <div key={tl} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem' }}>
                      <span style={{ width: '2.8rem', color: 'var(--text-secondary)', flexShrink: 0 }}>{tl}×</span>
                      {cond?.status !== 'COMPLETED' ? (
                        <span style={{ color: 'var(--text-muted)' }}>—</span>
                      ) : (
                        <>
                          <div style={{ flex: 1, height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${pctWidth}%`, height: '100%', background: barColor, borderRadius: '3px', transition: 'width 0.3s' }} />
                          </div>
                          <span style={{ width: '4.5rem', textAlign: 'right', color: barColor, fontWeight: 600 }}>
                            {pct != null && !isNaN(pct) ? `${pct > 0 ? '+' : ''}${Number(pct).toFixed(1)}%` : 'N/A'}
                          </span>
                        </>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
      <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
        % change vs same-demand control. Green = improved, red = worse. Heuristic values are formula estimates, not direct measurements.
      </p>
    </div>
  )
}
