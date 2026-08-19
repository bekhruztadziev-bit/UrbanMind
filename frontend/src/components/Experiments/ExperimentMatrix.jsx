import React, { useState } from 'react'

const METRICS = [
  { key: 'mean_completed_vehicle_waiting_seconds', label: 'Completed-Trip Mean Delay (s)', higherWorse: true },
  { key: 'mean_active_vehicle_waiting_seconds', label: 'Active-Vehicle Mean Delay (s)', higherWorse: true },
  { key: 'average_waiting_seconds', label: 'Step-weighted observed waiting (s)', higherWorse: true },
  { key: 'average_speed_kmh', label: 'Avg Speed (km/h)', higherWorse: false },
  { key: 'max_vehicle_count', label: 'Peak Vehicles', higherWorse: true },
  { key: 'sumo_co2_kg', label: 'CO₂ (kg)', higherWorse: true },
  { key: 'sumo_nox_g', label: 'NOₓ (g)', higherWorse: true },
  { key: 'co2_kg', label: 'CO₂ est. (kg)', higherWorse: true },
  { key: 'nox_g', label: 'NOₓ est. (g)', higherWorse: true },
  { key: 'noise_db', label: 'Noise est. (dB)', higherWorse: true },
  { key: 'pedestrian_delay_seconds', label: 'Ped. Delay (s)', higherWorse: true },
  { key: 'accessibility_score', label: 'Accessibility', higherWorse: false },
]

const EVAL_BADGE = {
  SIMULATED: { label: 'SIMULATED', className: 'provenance-badge simulated' },
  HEURISTIC: { label: 'ESTIMATED', className: 'provenance-badge estimated' },
}

function cellStyle(delta, higherWorse) {
  if (delta == null) return {}
  const improved = higherWorse ? delta < 0 : delta > 0
  const worsened = higherWorse ? delta > 0 : delta < 0
  if (improved) return { background: 'rgba(16,185,129,0.12)', color: '#065f46' }
  if (worsened) return { background: 'rgba(239,68,68,0.10)', color: '#991b1b' }
  return {}
}

export function ExperimentMatrix({ result }) {
  const [selectedMetric, setSelectedMetric] = useState('mean_completed_vehicle_waiting_seconds')

  if (!result || !result.conditions || result.conditions.length === 0) {
    return <div className="panel-card empty-state"><p>{t.noData || 'No conditions to display.'}</p></div>
  }

  const metricDef = METRICS.find(m => m.key === selectedMetric) || METRICS[0]
  const trafficLevels = [...new Set(result.conditions.map(c => c.traffic_multiplier))].sort((a, b) => a - b)

  // Build intervention rows: unique intervention labels in order they appear
  const interventionRows = []
  const seen = new Set()
  for (const cond of result.conditions) {
    const key = cond.intervention_id || '__control__'
    if (!seen.has(key)) {
      seen.add(key)
      interventionRows.push({
        id: cond.intervention_id,
        label: cond.intervention_label,
        evaluation_mode: cond.evaluation_mode,
      })
    }
  }

  // Index conditions by (traffic_multiplier, intervention_id)
  const condIndex = {}
  for (const cond of result.conditions) {
    const key = `${cond.traffic_multiplier}|${cond.intervention_id}`
    condIndex[key] = cond
  }

  return (
    <div className="panel-card full-width-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
        <h3 style={{ margin: 0 }}>{t.resultsMatrix || 'Results Matrix'}</h3>
        <select
          value={selectedMetric}
          onChange={e => setSelectedMetric(e.target.value)}
          style={{ fontSize: '0.85rem', padding: '0.35rem 0.6rem', borderRadius: '8px', border: '1px solid #cbd5e1' }}
        >
          {METRICS.map(m => <option key={m.key} value={m.key}>{m.label}</option>)}
        </select>
      </div>

      <div className="comparison-table" style={{ overflowX: 'auto' }}>
        <table style={{ fontSize: '0.83rem', borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', padding: '0.5rem 0.7rem', borderBottom: '2px solid #e2e8f0' }}>{t.interventionHeader || 'Intervention'}</th>
              <th style={{ textAlign: 'center', padding: '0.5rem 0.7rem', borderBottom: '2px solid #e2e8f0', fontSize: '0.72rem', color: '#64748b' }}>{t.typeHeader || 'Type'}</th>
              {trafficLevels.map(tl => (
                <th key={tl} style={{ textAlign: 'center', padding: '0.5rem 0.7rem', borderBottom: '2px solid #e2e8f0' }}>
                  {tl}×
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Control row */}
            <tr style={{ background: 'rgba(248,250,252,0.8)' }}>
              <td style={{ padding: '0.5rem 0.7rem', fontWeight: 700, color: '#0f172a' }}>{t.controlNoIntervention || 'Control (no intervention)'}</td>
              <td style={{ textAlign: 'center', padding: '0.5rem 0.7rem' }}>—</td>
              {trafficLevels.map(tl => {
                // Find first condition at this traffic level to get control metrics
                const cond = result.conditions.find(c => c.traffic_multiplier === tl && c.control_metrics)
                const val = cond?.control_metrics?.[selectedMetric]
                return (
                  <td key={tl} style={{ textAlign: 'center', padding: '0.5rem 0.7rem', fontWeight: 600 }}>
                    {val != null ? Number(val).toFixed(1) : '—'}
                  </td>
                )
              })}
            </tr>

            {/* Intervention rows */}
            {interventionRows.map(row => {
              const badge = EVAL_BADGE[row.evaluation_mode] || EVAL_BADGE.HEURISTIC
              return (
                <tr key={row.id || 'none'}>
                  <td style={{ padding: '0.5rem 0.7rem', color: '#1f2937' }}>{row.label}</td>
                  <td style={{ textAlign: 'center', padding: '0.5rem 0.7rem' }}>
                    <span className={badge.className} style={{ display: 'inline-block' }}>
                      {badge.label}
                    </span>
                  </td>
                  {trafficLevels.map(tl => {
                    const cond = condIndex[`${tl}|${row.id}`]
                    if (!cond || cond.status !== 'COMPLETED') {
                      return (
                        <td key={tl} style={{ textAlign: 'center', padding: '0.5rem 0.7rem', color: '#94a3b8' }}>
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
                        <div style={{ fontWeight: 600 }}>{val != null ? Number(val).toFixed(1) : '—'}</div>
                        {pct != null && (
                          <div style={{ fontSize: '0.7rem', opacity: 0.85 }}>
                            {pct > 0 ? '+' : ''}{pct.toFixed(1)}%
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
      <p style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.5rem' }}>
        % shown vs same-demand control. Green = improved, red = worse. Heuristic values are formula-based estimates.
      </p>
    </div>
  )
}
