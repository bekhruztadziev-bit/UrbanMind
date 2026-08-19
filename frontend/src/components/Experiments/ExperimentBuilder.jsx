import React from 'react'

const INTERVENTION_LABELS_RU = {
  'Extend main green phase': 'Продление основной зеленой фазы',
  'Reduce competing phase': 'Сокращение конкурирующей фазы',
  'Bus-priority corridor': 'Коридор с приоритетом автобусов',
  'Pedestrian priority window': 'Окно приоритета пешеходов',
  'School-zone speed calming': 'Успокоение трафика в школьной зоне',
  'Short-stay curb rotation': 'Ротация парковки короткого пребывания',
}

const PROFILES_RU = {
  'Fast Evaluation': 'Быстрая оценка',
  'Standard Evaluation': 'Стандартная оценка',
  'Extended Evaluation': 'Расширенная оценка',
  'Custom': 'Пользовательский',
}

const PROFILES_DESC_RU = {
  'Fast Evaluation': 'Экспресс-оценка (100 шагов прогрев + 200 измерение)',
  'Standard Evaluation': 'Стабильное сравнение (300 шагов прогрев + 600 измерение)',
  'Extended Evaluation': 'Глубокий анализ коридора (600 шагов прогрев + 1200 измерение)',
  'Custom': 'Ручная настройка параметров симуляции',
}

export function ExperimentBuilder({
  t,
  language = 'en',
  analysisType, setAnalysisType,
  experimentName, setExperimentName,
  selectedTrafficLevels, toggleTrafficLevel,
  selectedInterventionIds, toggleIntervention,
  simulationProfile, setSimulationProfile, SIMULATION_PROFILES,
  warmupSteps, setWarmupSteps,
  measurementSteps, setMeasurementSteps,
  duration,
  interventionRegistry, registryLoading, registryError,
  conditionCount, conditionWarning, conditionBlocked,
  status, canRun, runExperimentNow,
  TRAFFIC_LEVELS,
}) {
  const isRunning = status === 'RUNNING'
  const isRu = language === 'ru'

  const getProfileLabel = (p) => {
    if (isRu && PROFILES_RU[p.id]) {
      return `${PROFILES_RU[p.id]} (${p.steps} ${t.steps || 'шагов'})`
    }
    return `${p.id} (${p.steps} steps)`
  }

  const getProfileDesc = () => {
    if (isRu && PROFILES_DESC_RU[simulationProfile]) {
      return PROFILES_DESC_RU[simulationProfile]
    }
    return SIMULATION_PROFILES.find(p => p.id === simulationProfile)?.desc
  }

  return (
    <div className="panel-card experiment-builder">
      <h3>{t.experimentBuilder}</h3>

      {/* Analysis Type Toggle */}
      <div className="control-group">
        <label>{t.analysisType || (isRu ? 'Тип анализа' : 'Analysis Type')}</label>
        <div className="segmented-control" style={{ display: 'flex', gap: '0.35rem', background: 'rgba(15, 23, 42, 0.8)', padding: '0.3rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <button 
            type="button"
            style={{
              flex: 1,
              border: analysisType === 'scenario' ? '1px solid var(--accent-primary)' : '1px solid transparent',
              background: analysisType === 'scenario' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: analysisType === 'scenario' ? '#38bdf8' : 'var(--text-muted)',
              padding: '0.45rem',
              borderRadius: '8px',
              fontWeight: analysisType === 'scenario' ? 600 : 500,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onClick={() => setAnalysisType('scenario')}
          >
            {t.quickWhatIf || (isRu ? 'Экспресс-сценарий' : 'Quick What-If')}
          </button>
          <button 
            type="button"
            style={{
              flex: 1,
              border: analysisType === 'experiment' ? '1px solid var(--accent-primary)' : '1px solid transparent',
              background: analysisType === 'experiment' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: analysisType === 'experiment' ? '#38bdf8' : 'var(--text-muted)',
              padding: '0.45rem',
              borderRadius: '8px',
              fontWeight: analysisType === 'experiment' ? 600 : 500,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onClick={() => setAnalysisType('experiment')}
          >
            {t.experimentTab || (isRu ? 'Эксперимент' : 'Experiment')}
          </button>
        </div>
      </div>

      {/* Experiment Name */}
      <div className="control-group">
        <label htmlFor="exp-name">{analysisType === 'scenario' ? (t.scenarioName || 'Scenario Name') : t.experimentName}</label>
        <input
          id="exp-name"
          type="text"
          value={experimentName}
          onChange={e => setExperimentName(e.target.value)}
          placeholder={t.experimentNamePlaceholder}
          disabled={isRunning}
        />
      </div>

      {/* Traffic Levels */}
      <div className="control-group">
        <label>{t.trafficLevels}</label>
        <div className="checkbox-group">
          {TRAFFIC_LEVELS.map(level => {
            const isChecked = selectedTrafficLevels.includes(level)
            return (
              <label key={level} className={`checkbox-option ${isChecked ? 'checked' : ''} ${analysisType === 'scenario' && !isChecked && selectedTrafficLevels.length > 0 ? 'muted' : ''}`}>
                <input
                  type={analysisType === 'scenario' ? 'radio' : 'checkbox'}
                  checked={isChecked}
                  onChange={() => toggleTrafficLevel(level)}
                  disabled={isRunning}
                  name="traffic-level"
                />
                <span>{level}×</span>
              </label>
            )
          })}
        </div>
      </div>

      {/* Simulation Profile */}
      <div className="control-group">
        <label htmlFor="exp-profile">{t.simulationProfile || (isRu ? 'Профиль симуляции' : 'Simulation Profile')}</label>
        <select
          id="exp-profile"
          value={simulationProfile}
          onChange={e => setSimulationProfile(e.target.value)}
          disabled={isRunning}
        >
          {SIMULATION_PROFILES.map(p => (
            <option key={p.id} value={p.id}>{getProfileLabel(p)}</option>
          ))}
        </select>
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', lineHeight: 1.35 }}>
          {getProfileDesc()}
        </div>
        
        {simulationProfile === 'Custom' && (
          <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem' }}>
            <div style={{ flex: 1 }}>
              <label htmlFor="warmup-steps" style={{ fontSize: '0.8rem' }}>{isRu ? 'Шаги прогрева' : 'Warm-up Steps'}</label>
              <input
                id="warmup-steps"
                type="number"
                value={warmupSteps}
                onChange={e => setWarmupSteps(Number(e.target.value))}
                min="0"
                step="100"
                disabled={isRunning}
                style={{ padding: '0.4rem' }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label htmlFor="measurement-steps" style={{ fontSize: '0.8rem' }}>{isRu ? 'Шаги измерения' : 'Measurement Steps'}</label>
              <input
                id="measurement-steps"
                type="number"
                value={measurementSteps}
                onChange={e => setMeasurementSteps(Number(e.target.value))}
                min="100"
                step="100"
                disabled={isRunning}
                style={{ padding: '0.4rem' }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Interventions */}
      <div className="control-group">
        <label>{t.interventionSel || (isRu ? 'Выбор мер' : 'Interventions')}</label>
        {registryLoading ? (
          <p className="traffic-legend muted">{t.loadingInterventions}</p>
        ) : registryError ? (
          <div className="error-box">{registryError}</div>
        ) : (
          <div className="intervention-checklist">
            {interventionRegistry.map(iv => {
              const isSim = iv.evaluation_mode === 'SIMULATED'
              const badgeClass = isSim ? 'provenance-badge simulated' : 'provenance-badge estimated'
              const badgeText = isSim ? (isRu ? 'СМОДЕЛИРОВАНО' : 'SIMULATED') : (isRu ? 'ОЦЕНЕНО' : 'ESTIMATED')
              const isChecked = selectedInterventionIds.includes(iv.id)
              const label = isRu ? (iv.label_ru || INTERVENTION_LABELS_RU[iv.label] || iv.label) : (iv.label_en || iv.label)

              return (
                <label key={iv.id} className={`intervention-option ${isChecked ? 'checked' : ''} ${analysisType === 'scenario' && !isChecked && selectedInterventionIds.length > 0 ? 'muted' : ''}`}>
                  <input
                    type={analysisType === 'scenario' ? 'radio' : 'checkbox'}
                    checked={isChecked}
                    onChange={() => toggleIntervention(iv.id)}
                    disabled={isRunning}
                    name="intervention-id"
                  />
                  <span className="iv-label">{label}</span>
                  <span className={badgeClass}>
                    {badgeText}
                  </span>
                </label>
              )
            })}
          </div>
        )}
      </div>

      {/* Matrix preview */}
      <div className="condition-preview" style={{
        background: conditionBlocked ? 'rgba(239,68,68,0.12)' : conditionWarning ? 'rgba(245,158,11,0.12)' : 'rgba(56, 189, 248, 0.08)',
        border: `1px solid ${conditionBlocked ? 'rgba(239,68,68,0.3)' : conditionWarning ? 'rgba(245,158,11,0.3)' : 'rgba(56, 189, 248, 0.25)'}`,
        borderRadius: '10px', padding: '0.6rem 0.9rem', fontSize: '0.85rem', marginTop: '0.5rem', color: 'var(--text-secondary)'
      }}>
        {isRu ? (
          <span>
            <strong>{selectedTrafficLevels.length}</strong> ур. трафика × <strong>{selectedInterventionIds.length || 1}</strong> мер = <strong>{conditionCount}</strong> усл.
          </span>
        ) : (
          <span>
            <strong>{selectedTrafficLevels.length}</strong> {t.trafficLevels} × <strong>{selectedInterventionIds.length || 1}</strong> {t.interventions} = <strong>{conditionCount}</strong> {t.conditions}
          </span>
        )}
        {conditionBlocked && <div style={{ color: '#ef4444', marginTop: '0.3rem' }}>{t.conditionLimitExceeded}</div>}
        {conditionWarning && !conditionBlocked && <div style={{ color: '#fbbf24', marginTop: '0.3rem' }}>{t.conditionWarning}</div>}
      </div>

      <div className="button-stack" style={{ marginTop: '0.75rem' }}>
        <button
          type="button"
          className="accent"
          onClick={runExperimentNow}
          disabled={!canRun || isRunning}
        >
          {isRunning ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              <svg className="spin-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
              </svg>
              {analysisType === 'scenario' ? t.runningScenario : t.runningExperiment}
            </span>
          ) : (analysisType === 'scenario' ? (isRu ? 'Запустить сценарий' : 'Run Scenario') : t.runExperiment)}
        </button>
      </div>
    </div>
  )
}
