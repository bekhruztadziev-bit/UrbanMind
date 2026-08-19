import React from 'react'
import { Header } from '../Header/Header'

export function HistoryPage({ t, setCurrentView, toggleLanguage, experimentHistory, setDisplayedResult }) {
  const { experiments, removeExperiment, clearHistory } = experimentHistory

  const handleReopen = (exp) => {
    setDisplayedResult(exp)
    setCurrentView('explore')
  }

  return (
    <div className="app-shell history-shell" style={{ display: 'block', maxWidth: '1460px', margin: '0 auto', padding: '1.1rem', minHeight: '100vh', background: 'var(--bg-base)' }}>
      <Header
        t={t}
        currentView="history"
        setCurrentView={setCurrentView}
        toggleLanguage={toggleLanguage}
      />
      <main style={{ marginTop: '1rem' }}>
        <div className="panel-card" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.5rem', color: 'var(--text-primary)' }}>{t.experimentHistory || 'History'}</h2>
            <button type="button" className="ghost-button" onClick={clearHistory}>
              {t.clearHistory}
            </button>
          </div>

          {experiments.length === 0 ? (
            <div className="empty-state" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', borderRadius: '12px', border: '1px dashed var(--border-color)' }}>
              <p>{t.noExperimentsYet}</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1rem' }}>
              {experiments.map(exp => {
                const statusColor = exp.summary?.status === 'COMPLETED' ? 'var(--accent-secondary)' : exp.summary?.status === 'PARTIALLY_COMPLETED' ? '#fbbf24' : '#f87171'
                const isScenario = exp.conditions?.length === 1
                return (
                  <div key={exp.experiment_id} style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', boxShadow: 'var(--shadow-card)' }}>
                    <div>
                      <div style={{ display: 'inline-block', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: isScenario ? 'var(--badge-observed-text)' : 'var(--badge-simulated-text)', background: isScenario ? 'var(--badge-observed-bg)' : 'var(--badge-simulated-bg)', padding: '0.2rem 0.5rem', borderRadius: '4px', marginBottom: '0.5rem' }}>
                        {isScenario ? (t.scenario || 'Scenario') : (t.experimentTab || 'Experiment')}
                      </div>
                      <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--text-primary)', lineHeight: 1.2 }}>{exp.name}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        {new Date(exp.created_at).toLocaleString()}
                      </div>
                    </div>
                    
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.25)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                        <span>{t.trafficLevels || 'Traffic Levels'}:</span>
                        <strong style={{ fontFamily: 'var(--font-mono)' }}>{exp.traffic_levels?.join(', ')}×</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                        <span>{t.conditions || 'Conditions'}:</span>
                        <strong style={{ fontFamily: 'var(--font-mono)' }}>{exp.conditions?.length}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>{t.status || 'Status'}:</span>
                        <strong style={{ color: statusColor, fontFamily: 'var(--font-mono)' }}>{exp.summary?.status}</strong>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto', paddingTop: '0.5rem' }}>
                      <button
                        type="button"
                        className="accent"
                        style={{ flex: 1 }}
                        onClick={() => handleReopen(exp)}
                      >
                        {t.view}
                      </button>
                      <button
                        type="button"
                        className="ghost-button"
                        style={{ flex: 1, color: '#f87171', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}
                        onClick={() => removeExperiment(exp.experiment_id)}
                      >
                        {t.remove}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

