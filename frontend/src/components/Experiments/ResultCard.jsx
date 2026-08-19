import React from 'react'

const EVAL_BADGE = {
  SIMULATED: { label: 'SUMO', color: '#0f766e', bg: 'rgba(15,118,110,0.12)' },
  HEURISTIC: { label: 'Heuristic', color: '#b45309', bg: 'rgba(180,83,9,0.12)' },
}

export function ResultCard({
  interventionName,
  simulationProfile,
  controlValue,
  resultValue,
  delta,
  percentage,
  evaluationMode,
  metricLabel = 'Observed Wait (s)',
}) {
  const badge = EVAL_BADGE[evaluationMode] || EVAL_BADGE.HEURISTIC
  const improved = delta < 0
  const worsened = delta > 0

  return (
    <div className="panel-card" style={{ padding: '1rem', borderLeft: `4px solid ${improved ? '#10b981' : worsened ? '#ef4444' : '#cbd5e1'}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h4 style={{ margin: '0 0 0.25rem 0', fontSize: '1rem', color: '#0f172a' }}>{interventionName}</h4>
          <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Profile: {simulationProfile || 'Custom'}
          </div>
        </div>
        <span style={{ fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px', color: badge.color, background: badge.bg, fontWeight: 600 }}>
          {badge.label} Evidence
        </span>
      </div>

      <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1rem' }}>
        <div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Control</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 600, color: '#334155' }}>{controlValue.toFixed(1)}</div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Result</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 600, color: '#0f172a' }}>{resultValue.toFixed(1)}</div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Impact</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: improved ? '#059669' : worsened ? '#dc2626' : '#64748b' }}>
            {percentage > 0 ? '+' : ''}{percentage.toFixed(1)}%
          </div>
        </div>
      </div>
      <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.75rem' }}>
        Metric: {metricLabel}
      </div>
    </div>
  )
}
