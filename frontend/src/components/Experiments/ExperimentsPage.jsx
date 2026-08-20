import React, { useState, useEffect } from 'react'
import { Header } from '../Header/Header'
import { ExperimentBuilder } from './ExperimentBuilder'
import { ExperimentStatus } from './ExperimentStatus'
import { ExperimentMatrix } from './ExperimentMatrix'
import { InterventionEffectView } from './InterventionEffectView'
import { RobustnessSummary } from './RobustnessSummary'
import { AIExplanation } from '../Dashboard/AIExplanation'
import { exportExperimentToJson, exportExperimentToCsv } from '../../utils/export'
import { fetchAIExplanation, generateDecisionReport } from '../../api/client'
import { normalizeAIResponse, safeNumber, INTERVENTION_LABELS_RU } from '../../utils/normalize'
import { DecisionReportModal } from '../Reports/DecisionReportModal'

export function ExperimentsPage({
  t = {},
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
    warmupSteps, setWarmupSteps,
    measurementSteps, setMeasurementSteps,
    duration,
    interventionRegistry, registryLoading, registryError,
    conditionCount, conditionWarning, conditionBlocked,
    status, experimentResult, runError, errorDiagnostics,
    canRun, runExperimentNow, reset,
    TRAFFIC_LEVELS,
    analysisType, setAnalysisType,
    displayedResult, setDisplayedResult
  } = experiment

  const RESULT_TABS = [
    { id: 'matrix', label: t.resultsMatrixTab || (isRu ? 'Матрица результатов' : 'Results Matrix') },
    { id: 'effect', label: t.interventionEffectTab || (isRu ? 'Эффект мер' : 'Intervention Effect') },
    { id: 'robustness', label: t.robustnessTab || (isRu ? 'Устойчивость' : 'Robustness') },
    { id: 'ai', label: t.aiAnalysisTab || (isRu ? 'ИИ-Интерпретация' : 'AI Interpretation') },
  ]

  const [activeTab, setActiveTab] = useState('matrix')
  const [presentationMode, setPresentationMode] = useState(false)
  const [showErrorDetails, setShowErrorDetails] = useState(false)

  // AI analysis state for experiment view
  const [expAIState, setExpAIState] = useState('READY')
  const [expAIData, setExpAIData] = useState(null)
  const [expAIError, setExpAIError] = useState('')

  // Decision report modal state
  const [reportModalOpen, setReportModalOpen] = useState(false)
  const [decisionReportData, setDecisionReportData] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)

  // When a new result comes in, show it and save to history
  const activeResult = displayedResult || experimentResult

  useEffect(() => {
    if (experimentResult && status !== 'RUNNING') {
      setDisplayedResult(experimentResult)
      if (experimentHistory?.saveExperiment) {
        experimentHistory.saveExperiment(experimentResult)
      }
      setExpAIState('READY')
      setExpAIData(null)
    }
  }, [experimentResult, status])

  const handleOpenDecisionReport = async () => {
    if (!activeResult) return
    setReportLoading(true)
    try {
      const rep = await generateDecisionReport({
        ...activeResult,
        language: language,
      })
      setDecisionReportData(rep)
      setReportModalOpen(true)
    } catch (err) {
      console.error('Failed to generate decision report:', err)
    } finally {
      setReportLoading(false)
    }
  }

  const handleRunExperimentAI = async (targetLang = language) => {
    if (!activeResult || !activeResult.conditions || activeResult.conditions.length === 0) return
    setExpAIState('ANALYZING')
    setExpAIError('')
    try {
      const completedConditions = activeResult.conditions.filter(c => c.status === 'COMPLETED')
      const baselineCond = activeResult.conditions.find(c => c.traffic_multiplier === 1.0 && c.control_metrics) || activeResult.conditions[0]
      const bestCond = completedConditions.find(c => c.evaluation_mode === 'SIMULATED') || completedConditions[0] || baselineCond

      const formatDelta = (cond) => {
        const deltas = cond?.metric_deltas || {}
        const waitPct = deltas.average_waiting_seconds?.percentage
        const ttPct = deltas.average_travel_time_seconds?.percentage
        const stopsPct = deltas.stops_per_vehicle?.percentage
        const tpPct = deltas.throughput_vehicles_per_hour?.percentage
        const co2Pct = deltas.sumo_co2_kg?.percentage ?? deltas.co2_kg?.percentage

        return {
          delay_improvement_pct: waitPct != null ? -safeNumber(waitPct, 0) : 0,
          travel_time_improvement_pct: ttPct != null ? -safeNumber(ttPct, 0) : 0,
          stops_improvement_pct: stopsPct != null ? -safeNumber(stopsPct, 0) : 0,
          throughput_improvement_pct: tpPct != null ? safeNumber(tpPct, 0) : 0,
          emissions_improvement_pct: co2Pct != null ? -safeNumber(co2Pct, 0) : 0,
          ...deltas,
        }
      }

      const payload = {
        baseline: baselineCond?.control_metrics || baselineCond?.scenario_metrics || {},
        candidates: completedConditions.map(c => {
          const rawLabel = c.intervention_label || c.intervention_id || 'Control'
          return {
            id: c.intervention_id || 'control',
            label: isRu ? (INTERVENTION_LABELS_RU[rawLabel] || rawLabel) : rawLabel,
            label_en: rawLabel,
            label_ru: INTERVENTION_LABELS_RU[rawLabel] || rawLabel,
            metrics: c.scenario_metrics || {},
            delta: formatDelta(c),
            evaluation_mode: c.evaluation_mode,
          }
        }),
        best_candidate: {
          id: bestCond?.intervention_id || 'best',
          label: isRu ? (INTERVENTION_LABELS_RU[bestCond?.intervention_label] || bestCond?.intervention_label) : bestCond?.intervention_label,
          label_en: bestCond?.intervention_label,
          label_ru: INTERVENTION_LABELS_RU[bestCond?.intervention_label] || bestCond?.intervention_label,
          metrics: bestCond?.scenario_metrics || {},
          delta: formatDelta(bestCond),
          evaluation_mode: bestCond?.evaluation_mode,
        },
        language: targetLang,
      }

      const rawAI = await fetchAIExplanation(payload)
      const normalized = normalizeAIResponse(rawAI)
      setExpAIData(normalized)
      setExpAIState(normalized?.is_ai ? 'COMPLETE' : 'FALLBACK')
    } catch (err) {
      setExpAIError(err.message || 'AI explanation service unavailable')
      setExpAIState('ERROR')
    }
  }

  const expOptResultShim = activeResult ? {
    baseline: activeResult.conditions.find(c => c.traffic_multiplier === 1.0 && c.control_metrics)?.control_metrics || activeResult.conditions[0]?.control_metrics || {},
    ranked_candidates: activeResult.conditions.filter(c => c.status === 'COMPLETED').map(c => {
      const deltas = c.metric_deltas || {}
      const rawLabel = c.intervention_label || c.intervention_id || 'Control'
      return {
        id: c.intervention_id || 'control',
        label: isRu ? (INTERVENTION_LABELS_RU[rawLabel] || rawLabel) : rawLabel,
        label_en: rawLabel,
        label_ru: INTERVENTION_LABELS_RU[rawLabel] || rawLabel,
        metrics: c.scenario_metrics || {},
        delta: {
          delay_improvement_pct: deltas.average_waiting_seconds?.percentage != null ? -safeNumber(deltas.average_waiting_seconds.percentage, 0) : 0,
          travel_time_improvement_pct: deltas.average_travel_time_seconds?.percentage != null ? -safeNumber(deltas.average_travel_time_seconds.percentage, 0) : 0,
          stops_improvement_pct: deltas.stops_per_vehicle?.percentage != null ? -safeNumber(deltas.stops_per_vehicle.percentage, 0) : 0,
          throughput_improvement_pct: deltas.throughput_vehicles_per_hour?.percentage != null ? safeNumber(deltas.throughput_vehicles_per_hour.percentage, 0) : 0,
          emissions_improvement_pct: deltas.sumo_co2_kg?.percentage != null ? -safeNumber(deltas.sumo_co2_kg.percentage, 0) : 0,
        },
        evaluation_mode: c.evaluation_mode,
      }
    }),
    best_candidate: (() => {
      const best = activeResult.conditions.find(c => c.evaluation_mode === 'SIMULATED' && c.status === 'COMPLETED') || activeResult.conditions[0]
      if (!best) return null
      const deltas = best.metric_deltas || {}
      const rawLabel = best.intervention_label || best.intervention_id || 'Best'
      return {
        id: best.intervention_id || 'best',
        label: isRu ? (INTERVENTION_LABELS_RU[rawLabel] || rawLabel) : rawLabel,
        label_en: rawLabel,
        label_ru: INTERVENTION_LABELS_RU[rawLabel] || rawLabel,
        metrics: best.scenario_metrics || {},
        delta: {
          delay_improvement_pct: deltas.average_waiting_seconds?.percentage != null ? -safeNumber(deltas.average_waiting_seconds.percentage, 0) : 0,
          travel_time_improvement_pct: deltas.average_travel_time_seconds?.percentage != null ? -safeNumber(deltas.average_travel_time_seconds.percentage, 0) : 0,
          stops_improvement_pct: deltas.stops_per_vehicle?.percentage != null ? -safeNumber(deltas.stops_per_vehicle.percentage, 0) : 0,
          throughput_improvement_pct: deltas.throughput_vehicles_per_hour?.percentage != null ? safeNumber(deltas.throughput_vehicles_per_hour.percentage, 0) : 0,
          emissions_improvement_pct: deltas.sumo_co2_kg?.percentage != null ? -safeNumber(deltas.sumo_co2_kg.percentage, 0) : 0,
        },
        evaluation_mode: best.evaluation_mode,
      }
    })(),
    insights: {
      headline_ru: 'Сравнительный анализ сценариев коридора',
      headline_en: 'Corridor Scenario Comparative Analysis',
      context_ru: `Проведено тестирование ${activeResult.conditions.length} экспериментальных условий при различных уровнях загруженности.`,
      context_en: `Evaluated ${activeResult.conditions.length} conditions across multiple traffic demand levels.`,
      headline: isRu ? 'Сравнительный анализ сценариев коридора' : 'Corridor Scenario Comparative Analysis',
      context: isRu ? `Проведено тестирование ${activeResult.conditions.length} экспериментальных условий при различных уровнях загруженности.` : `Evaluated ${activeResult.conditions.length} conditions across multiple traffic demand levels.`,
    }
  } : null

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

      <main style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 360px) minmax(0, 1fr)', gap: '1.25rem', marginTop: '1rem' }}>
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
            warmupSteps={warmupSteps}
            setWarmupSteps={setWarmupSteps}
            measurementSteps={measurementSteps}
            setMeasurementSteps={setMeasurementSteps}
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
                experiment.setSelectedInterventionIds(['green_wave_coordination_0s_signal_timing', 'extend_green_5s_signal_timing', 'school_zone_slowdown_0s_safety'])
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
        <section style={{ display: 'flex', flexDirection: 'column', gap: '1rem', minWidth: 0 }}>
          <ExperimentStatus status={status} summary={activeResult?.summary} language={language} />

          {/* 1. Running State Card */}
          {status === 'RUNNING' && (
            <div className="panel-card" style={{ padding: '2rem', textAlign: 'center', background: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(20px)', border: '1px solid rgba(56, 189, 248, 0.35)', boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)' }}>
              <div style={{ width: '52px', height: '52px', margin: '0 auto 1.25rem', borderRadius: '50%', background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg className="spin-icon" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
                </svg>
              </div>
              <h3 style={{ fontSize: '1.25rem', color: '#ffffff', fontWeight: 700, marginBottom: '0.5rem' }}>
                {isRu ? 'Выполнение микросимуляции SUMO…' : 'Executing SUMO Microscopic Simulation…'}
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '540px', margin: '0 auto 1.5rem', lineHeight: 1.55 }}>
                {isRu 
                  ? 'Моделирование динамики транспортных потоков, фаз светофоров и профилей выбросов по коридору Ташкента в реальном времени.'
                  : 'Simulating vehicle dynamics, signal coordination, and emission profiles across the Tashkent corridor in real time.'}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', textAlign: 'left', maxWidth: '640px', margin: '0 auto' }}>
                <div style={{ padding: '0.75rem 0.9rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <span style={{ fontSize: '0.72rem', color: '#38bdf8', textTransform: 'uppercase', fontWeight: 700 }}>1. Инициализация</span>
                  <div style={{ fontSize: '0.84rem', color: '#f8fafc', marginTop: '3px' }}>{isRu ? 'Калибровка сети' : 'Network Calibration'}</div>
                </div>
                <div style={{ padding: '0.75rem 0.9rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <span style={{ fontSize: '0.72rem', color: '#38bdf8', textTransform: 'uppercase', fontWeight: 700 }}>2. TraCI Выполнение</span>
                  <div style={{ fontSize: '0.84rem', color: '#f8fafc', marginTop: '3px' }}>{isRu ? `${duration} шагов симуляции` : `${duration} simulation steps`}</div>
                </div>
                <div style={{ padding: '0.75rem 0.9rem', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <span style={{ fontSize: '0.72rem', color: '#38bdf8', textTransform: 'uppercase', fontWeight: 700 }}>3. Метрики и анализ</span>
                  <div style={{ fontSize: '0.84rem', color: '#f8fafc', marginTop: '3px' }}>{isRu ? 'Расчет задержек и CO₂' : 'Delay & CO2 calculation'}</div>
                </div>
              </div>
            </div>
          )}

          {/* 2. Error State Card */}
          {runError && status !== 'RUNNING' && (
            <div className="error-box panel-card" style={{ padding: '1.25rem', border: '1px solid rgba(239, 68, 68, 0.35)', background: 'rgba(239, 68, 68, 0.08)', borderRadius: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <strong style={{ color: '#f87171', fontSize: '0.95rem' }}>
                  {isRu ? 'Ошибка выполнения эксперимента' : 'Experiment Execution Error'}
                </strong>
                <button
                  type="button"
                  className="accent-glow-btn"
                  style={{ fontSize: '0.78rem', padding: '0.4rem 0.85rem' }}
                  onClick={runExperimentNow}
                >
                  🔄 {isRu ? 'Повторить' : 'Retry'}
                </button>
              </div>
              <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.86rem' }}>{runError}</p>

              {errorDiagnostics && (
                <div style={{ marginTop: '0.75rem' }}>
                  <button
                    type="button"
                    className="ghost-button"
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
                    onClick={() => setShowErrorDetails(prev => !prev)}
                  >
                    {showErrorDetails ? (isRu ? 'Скрыть диагностику' : 'Hide Diagnostics') : (isRu ? 'Показать диагностику' : 'View Diagnostics')}
                  </button>
                  {showErrorDetails && (
                    <pre style={{ marginTop: '0.5rem', padding: '0.75rem', background: 'rgba(0,0,0,0.5)', borderRadius: '8px', fontSize: '0.74rem', color: '#cbd5e1', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                      {JSON.stringify(errorDiagnostics, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 3. Results View */}
          {activeResult && activeResult.conditions?.length > 0 && status !== 'RUNNING' && (
            <>
              {/* Export + Reset row */}
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <button
                  type="button"
                  className="accent"
                  style={{ fontSize: '0.82rem' }}
                  onClick={handleOpenDecisionReport}
                  disabled={reportLoading}
                >
                  {reportLoading ? (
                    <span>⏳ {t.generatingDecisionReport || (isRu ? 'Формирование отчета…' : 'Generating Report…')}</span>
                  ) : (
                    <span>📋 {t.generateDecisionReport || (isRu ? 'Сформировать отчет о решении' : 'Generate Decision Report')}</span>
                  )}
                </button>
                <button type="button" className="ghost-button" style={{ fontSize: '0.82rem' }} onClick={() => exportExperimentToJson(activeResult)}>
                  {t.exportJson || (isRu ? 'Экспорт JSON' : 'Export JSON')}
                </button>
                <button type="button" className="ghost-button" style={{ fontSize: '0.82rem' }} onClick={() => exportExperimentToCsv(activeResult)}>
                  {t.exportCsv || (isRu ? 'Экспорт CSV' : 'Export CSV')}
                </button>
                {displayedResult && displayedResult !== experimentResult && (
                  <button type="button" style={{ fontSize: '0.82rem' }} onClick={() => setDisplayedResult(null)}>
                    ← {t.backToLatest || (isRu ? 'Назад к последнему' : 'Back to latest')}
                  </button>
                )}
                <button type="button" className="ghost-button" style={{ fontSize: '0.82rem' }} onClick={() => { reset(); setDisplayedResult(null) }}>
                  {t.newExperiment || (isRu ? 'Новый эксперимент' : 'New Experiment')}
                </button>
              </div>

              {/* Experiment metadata pill */}
              <div className="panel-card" style={{ padding: '0.75rem 1.1rem', fontSize: '0.84rem', color: 'var(--text-secondary)', background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '12px' }}>
                <strong style={{ color: '#fff' }}>{activeResult.name}</strong>
                {' · '}<span style={{ color: '#38bdf8' }}>{activeResult.experiment_id}</span>
                {' · '}{activeResult.metadata?.simulation_profile || 'Custom'} ({activeResult.duration} {isRu ? 'шагов' : 'steps'})
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
                      background: 'none', border: 'none', borderBottom: activeTab === tab.id ? '2px solid #38bdf8' : '2px solid transparent',
                      borderRadius: 0, color: activeTab === tab.id ? '#38bdf8' : 'var(--text-muted)',
                      padding: '0.55rem 0.95rem', fontWeight: activeTab === tab.id ? 700 : 500,
                      cursor: 'pointer', fontSize: '0.88rem', marginBottom: '-2px', boxShadow: 'none',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {activeTab === 'matrix' && <ExperimentMatrix result={activeResult} t={t} />}
              {activeTab === 'effect' && <InterventionEffectView result={activeResult} t={t} />}
              {activeTab === 'robustness' && <RobustnessSummary result={activeResult} t={t} />}
              {activeTab === 'ai' && (
                <AIExplanation
                  t={t}
                  language={language}
                  optResult={expOptResultShim}
                  aiState={expAIState}
                  aiData={expAIData}
                  aiError={expAIError}
                  onRunAIExplanation={handleRunExperimentAI}
                />
              )}
            </>
          )}

          {/* 4. Empty Ready State */}
          {(!activeResult || !activeResult.conditions?.length) && status !== 'RUNNING' && !runError && (
            <div className="panel-card empty-state" style={{ minHeight: '340px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '2.5rem 1.5rem', background: 'rgba(15, 23, 42, 0.75)', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <div style={{ fontSize: '2.8rem', marginBottom: '0.85rem', opacity: 0.9 }}>🔬</div>
              <h4 style={{ fontSize: '1.2rem', color: '#ffffff', fontWeight: 700, marginBottom: '0.5rem' }}>
                {isRu ? 'Готово к запуску симуляции' : 'Ready to Run Simulation'}
              </h4>
              <p style={{ color: 'var(--text-secondary)', maxWidth: '460px', fontSize: '0.9rem', lineHeight: 1.55 }}>
                {t.experimentEmptyState || (isRu ? 'Выберите параметры сценария слева и нажмите «Запустить сценарий», чтобы протестировать реакцию коридора на различные сценарии загруженности.' : 'Configure scenario parameters on the left and click "Run Simulation" to evaluate corridor performance under varying traffic levels.')}
              </p>
            </div>
          )}
        </section>
      </main>

      <DecisionReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        report={decisionReportData}
        language={language}
        t={t}
      />
    </div>
  )
}
