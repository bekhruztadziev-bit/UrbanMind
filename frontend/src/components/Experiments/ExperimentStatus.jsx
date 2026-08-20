import React from 'react'

const STATUS_CONFIG_EN = {
  IDLE: { color: '#64748b', bg: 'rgba(100,116,139,0.12)', label: 'Ready to Run' },
  READY: { color: '#64748b', bg: 'rgba(100,116,139,0.12)', label: 'Ready to Run' },
  CONFIGURING: { color: '#38bdf8', bg: 'rgba(56,189,248,0.12)', label: 'Configuring Parameters' },
  RUNNING: { color: '#f59e0b', bg: 'rgba(245,158,11,0.15)', label: 'Running SUMO Simulation…' },
  COMPLETED: { color: '#10b981', bg: 'rgba(16,185,129,0.15)', label: 'Simulation Completed' },
  PARTIALLY_COMPLETED: { color: '#f59e0b', bg: 'rgba(245,158,11,0.15)', label: 'Partially Completed' },
  FAILED: { color: '#ef4444', bg: 'rgba(239,68,68,0.15)', label: 'Simulation Failed' },
  ERROR: { color: '#ef4444', bg: 'rgba(239,68,68,0.15)', label: 'Execution Error' },
}

const STATUS_CONFIG_RU = {
  IDLE: { color: '#94a3b8', bg: 'rgba(100,116,139,0.12)', label: 'Готово к запуску' },
  READY: { color: '#94a3b8', bg: 'rgba(100,116,139,0.12)', label: 'Готово к запуску' },
  CONFIGURING: { color: '#38bdf8', bg: 'rgba(56,189,248,0.12)', label: 'Настройка параметров' },
  RUNNING: { color: '#f59e0b', bg: 'rgba(245,158,11,0.15)', label: 'Выполнение симуляции SUMO…' },
  COMPLETED: { color: '#34d399', bg: 'rgba(16,185,129,0.15)', label: 'Симуляция завершена' },
  PARTIALLY_COMPLETED: { color: '#fbbf24', bg: 'rgba(245,158,11,0.15)', label: 'Частично завершено' },
  FAILED: { color: '#f87171', bg: 'rgba(239,68,68,0.15)', label: 'Ошибка выполнения' },
  ERROR: { color: '#f87171', bg: 'rgba(239,68,68,0.15)', label: 'Ошибка симуляции' },
}

export function ExperimentStatus({ status = 'READY', summary = null, language = 'en' }) {
  const isRu = language === 'ru'
  const config = isRu ? STATUS_CONFIG_RU : STATUS_CONFIG_EN
  const cfg = config[status] || config.READY

  const isRunning = status === 'RUNNING'

  return (
    <div className="experiment-status-bar" style={{
      background: cfg.bg,
      border: `1px solid ${cfg.color}35`,
      borderRadius: '12px',
      padding: '0.75rem 1.1rem',
      display: 'flex',
      alignItems: 'center',
      gap: '1rem',
      flexWrap: 'wrap',
      boxShadow: isRunning ? '0 0 20px rgba(245, 158, 11, 0.2)' : 'none',
      transition: 'all 0.3s ease',
    }}>
      {isRunning && (
        <svg className="spin-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={cfg.color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
        </svg>
      )}
      <strong style={{ color: cfg.color, fontSize: '0.92rem', letterSpacing: '0.01em' }}>{cfg.label}</strong>
      {summary && status !== 'READY' && status !== 'IDLE' && (
        <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          {isRu ? (
            <>
              Завершено условий: <strong style={{ color: 'var(--text-primary)' }}>{summary.completed}</strong> из <strong>{summary.total}</strong>
              {summary.failed > 0 && <span style={{ color: '#f87171', marginLeft: '0.5rem' }}>· {summary.failed} с ошибкой</span>}
              {summary.skipped > 0 && <span style={{ color: '#94a3b8', marginLeft: '0.5rem' }}>· {summary.skipped} пропущено</span>}
            </>
          ) : (
            <>
              <strong style={{ color: 'var(--text-primary)' }}>{summary.completed}</strong> / <strong>{summary.total}</strong> conditions completed
              {summary.failed > 0 && <span style={{ color: '#f87171', marginLeft: '0.5rem' }}>· {summary.failed} failed</span>}
              {summary.skipped > 0 && <span style={{ color: '#94a3b8', marginLeft: '0.5rem' }}>· {summary.skipped} skipped</span>}
            </>
          )}
        </span>
      )}
    </div>
  )
}
