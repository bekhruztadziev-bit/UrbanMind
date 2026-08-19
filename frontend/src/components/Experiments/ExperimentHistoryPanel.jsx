import React from 'react'

export function ExperimentHistoryPanel({ t, experiments, onReopen, onRemove, onClear }) {
  if (experiments.length === 0) {
    return (
      <div className="panel-card" style={{ marginTop: '0.75rem' }}>
        <p className="traffic-legend muted">{t.noExperimentsYet}</p>
      </div>
    )
  }

  return (
    <div className="panel-card" style={{ marginTop: '0.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <h3 style={{ margin: 0 }}>{t.experimentHistory}</h3>
        <button type="button" className="ghost-button" style={{ fontSize: '0.78rem', padding: '0.35rem 0.7rem' }} onClick={onClear}>
          {t.clearHistory}
        </button>
      </div>
      <div style={{ display: 'grid', gap: '0.5rem', maxHeight: '320px', overflowY: 'auto' }}>
        {experiments.map(exp => {
          const statusColor = exp.summary?.status === 'COMPLETED' ? '#10b981' : exp.summary?.status === 'PARTIALLY_COMPLETED' ? '#f59e0b' : '#ef4444'
          return (
            <div key={exp.experiment_id} style={{ background: 'rgba(248,250,252,0.9)', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '0.6rem 0.8rem' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#0f172a' }}>{exp.name}</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.15rem' }}>
                    {exp.traffic_levels?.length}× traffic · {exp.conditions?.length} conditions ·&nbsp;
                    <span style={{ color: statusColor, fontWeight: 600 }}>{exp.summary?.status}</span>
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{new Date(exp.created_at).toLocaleString()}</div>
                </div>
                <div style={{ display: 'flex', gap: '0.4rem', flexShrink: 0 }}>
                  <button
                    type="button"
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', borderRadius: '8px' }}
                    onClick={() => onReopen(exp)}
                  >
                    {t.view}
                  </button>
                  <button
                    type="button"
                    className="ghost-button"
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', borderRadius: '8px', background: 'rgba(239,68,68,0.08)', color: '#991b1b', border: '1px solid rgba(239,68,68,0.2)' }}
                    onClick={() => onRemove(exp.experiment_id)}
                  >
                    {t.remove}
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
