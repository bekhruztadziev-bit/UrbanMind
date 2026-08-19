import React from 'react'

const STATUS_CONFIG = {
  READY: { color: '#64748b', bg: 'rgba(100,116,139,0.12)', label: 'Ready' },
  RUNNING: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: 'Running…' },
  COMPLETED: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', label: 'Completed' },
  PARTIALLY_COMPLETED: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: 'Partially Completed' },
  FAILED: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'Failed' },
}

export function ExperimentStatus({ status, summary }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.READY

  return (
    <div className="experiment-status-bar" style={{ background: cfg.bg, border: `1px solid ${cfg.color}30`, borderRadius: '12px', padding: '0.65rem 1rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
      {status === 'RUNNING' && (
        <span className="spin-icon" style={{ display: 'inline-block', fontSize: '1.1rem' }}>⟳</span>
      )}
      <strong style={{ color: cfg.color, fontSize: '0.92rem' }}>{cfg.label}</strong>
      {summary && status !== 'READY' && (
        <span style={{ fontSize: '0.82rem', color: '#475569' }}>
          {summary.completed} / {summary.total} conditions completed
          {summary.failed > 0 && <span style={{ color: '#ef4444', marginLeft: '0.5rem' }}>· {summary.failed} failed</span>}
          {summary.skipped > 0 && <span style={{ color: '#94a3b8', marginLeft: '0.5rem' }}>· {summary.skipped} skipped</span>}
        </span>
      )}
    </div>
  )
}
