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
  setCurrentView,
  toggleLanguage,
  experiment,
  experimentHistory,
}) {
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

  // Handled in HistoryPage now

  return (
    <div className={`app-shell experiments-shell ${presentationMode ? 'presentation-mode' : ''}`} style={{ display: 'block', maxWidth: '1460px', margin: '0 auto', padding: presentationMode ? '0.5rem' : '1.1rem', minHeight: '100vh', background: 'linear-gradient(180deg, #f3f6fb 0%, #edf4f9 100%)' }}>
      {!presentationMode && (
        <Header
          t={t}
          currentView="explore"
          setCurrentView={setCurrentView}
          toggleLanguage={toggleLanguage}
        />
      )}
      
      {presentationMode && (
        <div style={{ textAlign: 'right', marginBottom: '0.5rem' }}>
          <button type="button" className="ghost-button" style={{ fontSize: '0.8rem' }} onClick={() => setPresentationMode(false)}>
            Exit Presentation Mode
          </button>
        </div>
      )}

      <main style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 320px) minmax(0, 1fr)', gap: '1.25rem', marginTop: '1rem' }}>
        {/* Left: Builder + History */}
        <aside>
          <ExperimentBuilder
            t={t}
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
                setExperimentName('Competition Benchmark')
                experiment.setSelectedTrafficLevels([0.8, 1.0, 1.2, 1.4])
                experiment.setSelectedInterventionIds(['tc_20kmh', 'signal_p5', 'signal_m5'])
                experiment.setSimulationProfile('Standard Evaluation')
              }}
              style={{ fontSize: '0.82rem', background: '#e2e8f0' }}
            >
              Load Competition Demo Preset
            </button>
            {!presentationMode && (
              <button
                type="button"
                className="ghost-button"
                onClick={() => setPresentationMode(true)}
                style={{ fontSize: '0.82rem' }}
              >
                Enter Presentation Mode
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
              <div className="panel-card" style={{ padding: '0.6rem 0.9rem', fontSize: '0.8rem', color: '#475569' }}>
                <strong style={{ color: '#0f172a' }}>{activeResult.name}</strong>
                {' · '}{activeResult.experiment_id}
                {' · '}{activeResult.metadata?.simulation_profile || 'Custom'} ({activeResult.duration} steps)
                {' · '}{activeResult.created_at ? new Date(activeResult.created_at).toLocaleString() : ''}
              </div>

              {/* Tab bar */}
              <div style={{ display: 'flex', gap: '0.4rem', borderBottom: '2px solid #e2e8f0', paddingBottom: '0' }}>
                {RESULT_TABS.map(tab => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    style={{
                      background: 'none', border: 'none', borderBottom: activeTab === tab.id ? '2px solid #0f766e' : '2px solid transparent',
                      borderRadius: 0, color: activeTab === tab.id ? '#0f766e' : '#64748b',
                      padding: '0.5rem 0.75rem', fontWeight: activeTab === tab.id ? 700 : 500,
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
            <div className="panel-card empty-state" style={{ minHeight: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <p style={{ color: '#64748b' }}>{t.experimentEmptyState}</p>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
