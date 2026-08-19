import React, { useState } from 'react'
import { Header } from '../Header/Header'
import { ExperimentBuilder } from './ExperimentBuilder'
import { ExperimentStatus } from './ExperimentStatus'
import { ExperimentMatrix } from './ExperimentMatrix'
import { InterventionEffectView } from './InterventionEffectView'
import { RobustnessSummary } from './RobustnessSummary'
import { exportExperimentToJson, exportExperimentToCsv } from '../../utils/export'

const RESULT_TABS = [
  { id: 'matrix', label: 'Results Matrix' },
  { id: 'effect', label: 'Intervention Effect' },
  { id: 'robustness', label: 'Robustness' },
]

export function ExperimentsPage({
  t,
  language = 'en',
  setCurrentView,
  toggleLanguage,
  experiment,
  experimentHistory,
}) {
  const isRu = language === 'ru'
  const {
    experimentName, setExperimentName,
    selectedTrafficLevels, toggleTrafficLevel,
    selectedInterventionIds, toggleIntervention,
    simulationProfile, setSimulationProfile, SIMULATION_PROFILES,
    duration,
    interventionRegistry, registryLoading, registryError,
    conditionCount, conditionWarning, conditionBlocked,
    status, experimentResult, runError,
    canRun, runExperimentNow, reset,
    TRAFFIC_LEVELS,
    analysisType, setAnalysisType,
    displayedResult, setDisplayedResult
  } = experiment

  const RESULT_TABS = [
    { id: 'matrix', label: t.resultsMatrixTab || (isRu ? 'Матрица результатов' : 'Results Matrix') },
    { id: 'effect', label: t.interventionEffectTab || (isRu ? 'Эффект мер' : 'Intervention Effect') },
    { id: 'robustness', label: t.robustnessTab || (isRu ? 'Устойчивость' : 'Robustness') },
  ]

  const [activeTab, setActiveTab] = useState('matrix')
  const [presentationMode, setPresentationMode] = useState(false)

  // When a new result comes in, show it and save to history
  const activeResult = displayedResult || experimentResult

  React.useEffect(() => {
    if (experimentResult && status !== 'RUNNING') {
      setDisplayedResult(experimentResult)
      experimentHistory.saveExperiment(experimentResult)
    }
  }, [experimentResult, status])

  return (
    <div className={`app-shell experiments-shell ${presentationMode ? 'presentation-mode' : ''}`} style={{ display: 'block', maxWidth: '1460px', margin: '0 auto', padding: presentationMode ? '0.5rem' : '1.1rem', minHeight: '100vh', background: 'var(--bg-base)' }}>
      {!presentationMode && (
        <Header
          t={t}
          language={language}
          currentView="explore"
          setCurrentView={setCurrentView}
          toggleLanguage={toggleLanguage}
        />
      )}
      
      {presentationMode && (
        <div style={{ textAlign: 'right', marginBottom: '0.5rem' }}>
          <button type="button" className="ghost-button" style={{ fontSize: '0.8rem' }} onClick={() => setPresentationMode(false)}>
            {t.exitPresentation || (isRu ? 'Выйти из режима презентации' : 'Exit Presentation Mode')}
          </button>
        </div>
      )}

      <main style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 340px) minmax(0, 1fr)', gap: '1.25rem', marginTop: '1rem' }}>
        {/* Left: Builder + Presets */}
        <aside>
          <ExperimentBuilder
            t={t}
            language={language}
            analysisType={analysisType}
            setAnalysisType={setAnalysisType}
            experimentName={experimentName}
            setExperimentName={setExperimentName}
            selectedTrafficLevels={selectedTrafficLevels}
            toggleTrafficLevel={toggleTrafficLevel}
            selectedInterventionIds={selectedInterventionIds}
            toggleIntervention={toggleIntervention}
            simulationProfile={simulationProfile}
            setSimulationProfile={setSimulationProfile}
            SIMULATION_PROFILES={SIMULATION_PROFILES}
            duration={duration}
            interventionRegistry={interventionRegistry}
            registryLoading={registryLoading}
            registryError={registryError}
            conditionCount={conditionCount}
            conditionWarning={conditionWarning}
            conditionBlocked={conditionBlocked}
            status={status}
            canRun={canRun}
            runExperimentNow={runExperimentNow}
            TRAFFIC_LEVELS={TRAFFIC_LEVELS}
          />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
            <button
              type="button"
              className="ghost-button"
              onClick={() => {
                setExperimentName(isRu ? 'Бенчмарк для жюри' : 'Competition Benchmark')
                experiment.setSelectedTrafficLevels([0.8, 1.0, 1.2, 1.4])
                experiment.setSelectedInterventionIds(['tc_20kmh', 'signal_p5', 'signal_m5'])
                experiment.setSimulationProfile('Standard Evaluation')
              }}
              style={{ fontSize: '0.82rem', background: 'rgba(30, 41, 59, 0.8)', border: '1px solid rgba(255,255,255,0.1)' }}
            >
              {t.loadPreset || (isRu ? 'Загрузить демо-пресет' : 'Load Competition Demo Preset')}
            </button>
            {!presentationMode && (
              <button
                type="button"
                className="ghost-button"
                onClick={() => setPresentationMode(true)}
                style={{ fontSize: '0.82rem' }}
              >
                {t.enterPresentation || (isRu ? 'Режим презентации' : 'Enter Presentation Mode')}
              </button>
            )}
          </div>
        </aside>

        {/* Right: Status + Results */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <ExperimentStatus status={status} summary={activeResult?.summary} />

          {runError && <div className="error-box panel-card">{runError}</div>}

          {activeResult && status !== 'RUNNING' && (
            <>
              {/* Export + reset row */}
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button type="button" className="ghost-button" style={{ fontSize: '0.82rem' }} onClick={() => exportExperimentToJson(activeResult)}>
                  {t.exportJson}
                </button>
                <button type="button" className="ghost-button" style={{ fontSize: '0.82rem' }} onClick={() => exportExperimentToCsv(activeResult)}>
                  {t.exportCsv}
                </button>
                {displayedResult && displayedResult !== experimentResult && (
                  <button type="button" style={{ fontSize: '0.82rem' }} onClick={() => setDisplayedResult(null)}>
                    ← {t.backToLatest}
                  </button>
                )}
                <button type="button" className="ghost-button" style={{ fontSize: '0.82rem' }} onClick={() => { reset(); setDisplayedResult(null) }}>
                  {t.newExperiment}
                </button>
              </div>

              {/* Experiment metadata pill */}
              <div className="panel-card" style={{ padding: '0.7rem 1rem', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                <strong style={{ color: '#fff' }}>{activeResult.name}</strong>
                {' · '}<span style={{ color: 'var(--accent-primary)' }}>{activeResult.experiment_id}</span>
                {' · '}{activeResult.metadata?.simulation_profile || 'Custom'} ({activeResult.duration} steps)
                {' · '}{activeResult.created_at ? new Date(activeResult.created_at).toLocaleString() : ''}
              </div>

              {/* Tab bar */}
              <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.2rem' }}>
                {RESULT_TABS.map(tab => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    style={{
                      background: 'none', border: 'none', borderBottom: activeTab === tab.id ? '2px solid var(--accent-primary)' : '2px solid transparent',
                      borderRadius: 0, color: activeTab === tab.id ? 'var(--accent-primary)' : 'var(--text-muted)',
                      padding: '0.5rem 0.85rem', fontWeight: activeTab === tab.id ? 700 : 500,
                      cursor: 'pointer', fontSize: '0.88rem', marginBottom: '-2px', boxShadow: 'none',
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {activeTab === 'matrix' && <ExperimentMatrix result={activeResult} t={t} />}
              {activeTab === 'effect' && <InterventionEffectView result={activeResult} t={t} />}
              {activeTab === 'robustness' && <RobustnessSummary result={activeResult} t={t} />}
            </>
          )}

          {!activeResult && status === 'READY' && (
            <div className="panel-card empty-state" style={{ minHeight: '320px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '2rem' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem', opacity: 0.85 }}>🔬</div>
              <h4 style={{ fontSize: '1.1rem', color: '#fff', marginBottom: '0.5rem' }}>
                {isRu ? 'Готово к запуску симуляции' : 'Ready to Run Simulation'}
              </h4>
              <p style={{ color: 'var(--text-muted)', maxWidth: '440px', fontSize: '0.88rem', lineHeight: 1.5 }}>
                {t.experimentEmptyState || (isRu ? 'Настройте параметры сценария слева и нажмите «Запустить симуляцию», чтобы протестировать реакцию коридора на различные сценарии загруженности.' : 'Configure scenario parameters on the left and click "Run Simulation" to evaluate corridor performance under varying traffic levels.')}
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
