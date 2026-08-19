import React from 'react'
import { Header } from '../Header/Header'

export function HistoryPage({ t, setCurrentView, toggleLanguage, experimentHistory, setDisplayedResult }) {
  const { experiments, saveExperiment, removeExperiment, clearHistory } = experimentHistory

  const handleReopen = (exp) => {
    setDisplayedResult(exp)
    setCurrentView('explore')
  }

  return (
    <div className="app-shell history-shell" style={{ display: 'block', maxWidth: '1460px', margin: '0 auto', padding: '1.1rem', minHeight: '100vh', background: 'linear-gradient(180deg, #f3f6fb 0%, #edf4f9 100%)' }}>
      <Header
        t={t}
        currentView="history"
        setCurrentView={setCurrentView}
        toggleLanguage={toggleLanguage}
      />
      <main style={{ marginTop: '1rem' }}>
        <div className="panel-card" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.5rem', color: '#0f172a' }}>{t.experimentHistory || 'History'}</h2>
            <button type="button" className="ghost-button" onClick={clearHistory}>
              {t.clearHistory}
            </button>
          </div>

          {experiments.length === 0 ? (
            <div className="empty-state" style={{ padding: '3rem', textAlign: 'center', color: '#64748b', background: 'rgba(248,250,252,0.6)', borderRadius: '12px', border: '1px dashed #cbd5e1' }}>
              <p>{t.noExperimentsYet}</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1rem' }}>
              {experiments.map(exp => {
                const statusColor = exp.summary?.status === 'COMPLETED' ? '#10b981' : exp.summary?.status === 'PARTIALLY_COMPLETED' ? '#f59e0b' : '#ef4444'
                const isScenario = exp.conditions?.length === 1
                return (
                  <div key={exp.experiment_id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                    <div>
                      <div style={{ display: 'inline-block', fontSize: '0.7rem', fontWeight: 600, color: isScenario ? '#0f766e' : '#4f46e5', background: isScenario ? 'rgba(15,118,110,0.1)' : 'rgba(79,70,229,0.1)', padding: '0.2rem 0.5rem', borderRadius: '10px', marginBottom: '0.5rem' }}>
                        {isScenario ? (t.scenario || 'Scenario') : (t.experimentTab || 'Experiment')}
                      </div>
                      <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#0f172a', lineHeight: 1.2 }}>{exp.name}</div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>
                        {new Date(exp.created_at).toLocaleString()}
                      </div>
                    </div>
                    
                    <div style={{ fontSize: '0.85rem', color: '#475569', background: '#f8fafc', padding: '0.75rem', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                        <span>{t.trafficLevels || 'Traffic Levels'}:</span>
                        <strong>{exp.traffic_levels?.join(', ')}×</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                        <span>{t.conditions || 'Conditions'}:</span>
                        <strong>{exp.conditions?.length}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>{t.status || 'Status'}:</span>
                        <strong style={{ color: statusColor }}>{exp.summary?.status}</strong>
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
                        style={{ flex: 1, color: '#991b1b', background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.15)' }}
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
