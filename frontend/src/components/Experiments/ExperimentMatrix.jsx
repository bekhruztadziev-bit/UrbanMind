import React, { useState } from 'react'
import { safeNumber, formatSafeNumber } from '../../utils/normalize'

const METRICS = [
  { key: 'mean_completed_vehicle_waiting_seconds', label: 'Completed-Trip Mean Delay (s)', higherWorse: true },
  { key: 'mean_active_vehicle_waiting_seconds', label: 'Active-Vehicle Mean Delay (s)', higherWorse: true },
  { key: 'average_waiting_seconds', label: 'Sampled accumulated waiting snapshot mean (s)', higherWorse: true },
  { key: 'average_travel_time_seconds', label: 'Travel Time (s)', higherWorse: true },
  { key: 'stops_per_vehicle', label: 'Stops / Vehicle', higherWorse: true },
  { key: 'mean_queue_length_meters', label: 'Queue Length (m)', higherWorse: true },
  { key: 'throughput_vehicles_per_hour', label: 'Throughput (veh/h)', higherWorse: false },
  { key: 'average_speed_kmh', label: 'Avg Speed (km/h)', higherWorse: false },
  { key: 'max_vehicle_count', label: 'Peak Vehicles', higherWorse: true },
  { key: 'sumo_co2_kg', label: 'CO₂ (kg)', higherWorse: true },
  { key: 'sumo_nox_g', label: 'NOₓ (g)', higherWorse: true },
]

const EVAL_BADGE = {
  SIMULATED: { label: 'SIMULATED', className: 'provenance-badge simulated' },
  HEURISTIC: { label: 'ESTIMATED', className: 'provenance-badge estimated' },
}

function cellStyle(delta, higherWorse) {
  if (delta == null || isNaN(delta)) return {}
  const numDelta = Number(delta)
  if (isNaN(numDelta)) return {}
  const improved = higherWorse ? numDelta < 0 : numDelta > 0
  const worsened = higherWorse ? numDelta > 0 : numDelta < 0
  if (improved) return { background: 'rgba(16,185,129,0.15)', color: '#34d399' }
  if (worsened) return { background: 'rgba(239,68,68,0.15)', color: '#f87171' }
  return {}
}

export function ExperimentMatrix({ result, t = {} }) {
  const [selectedMetric, setSelectedMetric] = useState('mean_completed_vehicle_waiting_seconds')

  if (!result || !result.conditions || !Array.isArray(result.conditions) || result.conditions.length === 0) {
    return <div className="panel-card empty-state"><p>{t?.noData || 'No conditions to display.'}</p></div>
  }

  const metricDef = METRICS.find(m => m.key === selectedMetric) || METRICS[0]
  const trafficLevels = [...new Set(result.conditions.map(c => c?.traffic_multiplier).filter(v => v != null))].sort((a, b) => a - b)

  // Build intervention rows: unique intervention labels in order they appear
  const interventionRows = []
  const seen = new Set()
  for (const cond of result.conditions) {
    if (!cond) continue
    const key = cond.intervention_id || '__control__'
    if (!seen.has(key)) {
      seen.add(key)
      interventionRows.push({
        id: cond.intervention_id,
        label: cond.intervention_label_ru || cond.intervention_label || (cond.intervention_id ? cond.intervention_id : 'Intervention'),
        evaluation_mode: cond.evaluation_mode || 'HEURISTIC',
      })
    }
  }

  // Index conditions by (traffic_multiplier, intervention_id)
  const condIndex = {}
  for (const cond of result.conditions) {
    if (!cond) continue
    const key = `${cond.traffic_multiplier}|${cond.intervention_id}`
    condIndex[key] = cond
  }

  return (
    <div className="panel-card full-width-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
        <h3 style={{ margin: 0 }}>{t?.resultsMatrix || 'Results Matrix'}</h3>
        <select
          value={selectedMetric}
          onChange={e => setSelectedMetric(e.target.value)}
          style={{ fontSize: '0.85rem', padding: '0.35rem 0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}
        >
          {METRICS.map(m => <option key={m.key} value={m.key}>{m.label}</option>)}
        </select>
      </div>

      <div className="comparison-table" style={{ overflowX: 'auto' }}>
        <table style={{ fontSize: '0.83rem', borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', padding: '0.5rem 0.7rem', borderBottom: '2px solid rgba(255,255,255,0.1)' }}>{t?.interventionHeader || 'Intervention'}</th>
              <th style={{ textAlign: 'center', padding: '0.5rem 0.7rem', borderBottom: '2px solid rgba(255,255,255,0.1)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>{t?.typeHeader || 'Type'}</th>
              {trafficLevels.map(tl => (
                <th key={tl} style={{ textAlign: 'center', padding: '0.5rem 0.7rem', borderBottom: '2px solid rgba(255,255,255,0.1)' }}>
                  {tl}×
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Control row */}
            <tr style={{ background: 'rgba(255,255,255,0.03)' }}>
              <td style={{ padding: '0.5rem 0.7rem', fontWeight: 700, color: 'var(--text-primary)' }}>{t?.controlNoIntervention || 'Control (no intervention)'}</td>
              <td style={{ textAlign: 'center', padding: '0.5rem 0.7rem' }}>—</td>
              {trafficLevels.map(tl => {
                const cond = result.conditions.find(c => c?.traffic_multiplier === tl && c?.control_metrics)
                const val = cond?.control_metrics?.[selectedMetric]
                return (
                  <td key={tl} style={{ textAlign: 'center', padding: '0.5rem 0.7rem', fontWeight: 600 }}>
                    {formatSafeNumber(val, 1)}
                  </td>
                )
              })}
            </tr>

            {/* Intervention rows */}
            {interventionRows.map(row => {
              const badge = EVAL_BADGE[row.evaluation_mode] || EVAL_BADGE.HEURISTIC
              return (
                <tr key={row.id || 'none'}>
                  <td style={{ padding: '0.5rem 0.7rem', color: 'var(--text-primary)' }}>{row.label}</td>
                  <td style={{ textAlign: 'center', padding: '0.5rem 0.7rem' }}>
                    <span className={badge.className} style={{ display: 'inline-block' }}>
                      {badge.label}
                    </span>
                  </td>
                  {trafficLevels.map(tl => {
                    const cond = condIndex[`${tl}|${row.id}`]
                    if (!cond || cond.status !== 'COMPLETED') {
                      return (
                        <td key={tl} style={{ textAlign: 'center', padding: '0.5rem 0.7rem', color: 'var(--text-muted)' }}>
                          {cond?.status === 'FAILED' ? '✗' : '—'}
                        </td>
                      )
                    }
                    const val = cond.scenario_metrics?.[selectedMetric]
                    const delta = cond.metric_deltas?.[selectedMetric]?.absolute
                    const style = cellStyle(delta, metricDef.higherWorse)
                    const pct = cond.metric_deltas?.[selectedMetric]?.percentage
                    return (
                      <td key={tl} style={{ textAlign: 'center', padding: '0.5rem 0.7rem', ...style }}>
                        <div style={{ fontWeight: 600 }}>{formatSafeNumber(val, 1)}</div>
                        {pct != null && !isNaN(pct) && (
                          <div style={{ fontSize: '0.7rem', opacity: 0.85 }}>
                            {pct > 0 ? '+' : ''}{safeNumber(pct, 0).toFixed(1)}%
                          </div>
                        )}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
        % shown vs same-demand control. Green = improved, red = worse. Heuristic values are formula-based estimates.
      </p>
    </div>
  )
}
