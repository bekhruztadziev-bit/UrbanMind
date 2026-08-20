import React from 'react'
import { INTERVENTION_LABELS_RU } from '../../utils/normalize'

const PROFILES_RU = {
  'Demo Burst': 'Экспресс-демо',
  'Fast Evaluation': 'Быстрая оценка',
  'Standard Evaluation': 'Стандартная оценка',
  'Extended Evaluation': 'Расширенная оценка',
  'Custom': 'Пользовательский',
}

const PROFILES_DESC_RU = {
  'Demo Burst': 'Быстрая интерактивная симуляция (300 шагов, без прогрева)',
  'Fast Evaluation': 'Экспресс-оценка (100 шагов прогрев + 200 измерение)',
  'Standard Evaluation': 'Стабильное сравнение (300 шагов прогрев + 600 измерение)',
  'Extended Evaluation': 'Глубокий анализ коридора (600 шагов прогрев + 1200 измерение)',
  'Custom': 'Ручная настройка параметров симуляции',
}

export function ExperimentBuilder({
  t = {},
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
    const name = isRu ? (PROFILES_RU[p.id] || p.id) : p.id
    const stepsUnit = isRu ? 'шагов' : 'steps'
    return `${name} (${p.steps || p.measurement_steps} ${stepsUnit})`
  }

  const getProfileDesc = () => {
    if (isRu && PROFILES_DESC_RU[simulationProfile]) {
      return PROFILES_DESC_RU[simulationProfile]
    }
    return SIMULATION_PROFILES.find(p => p.id === simulationProfile)?.desc
  }

  const titleText = isRu ? 'Конструктор сценариев и экспериментов' : (t.experimentBuilder || 'Scenario & Experiment Builder')
  const eyebrowText = isRu ? 'МОДЕЛИРОВАНИЕ И БЕНЧМАРКИНГ' : 'SIMULATION & BENCHMARKING'
  const analysisTypeLabel = isRu ? 'Тип анализа' : (t.analysisType || 'Analysis Type')
  const quickWhatIfLabel = isRu ? 'Экспресс-сценарий' : (t.quickWhatIf || 'Quick What-If')
  const experimentTabLabel = isRu ? 'Эксперимент' : (t.experimentTab || 'Experiment')
  const nameLabel = analysisType === 'scenario'
    ? (isRu ? 'Название сценария (необязательно)' : (t.scenarioName || 'Scenario Name (optional)'))
    : (isRu ? 'Название эксперимента (необязательно)' : (t.experimentName || 'Experiment Name (optional)'))
  const placeholderText = analysisType === 'scenario'
    ? (isRu ? 'напр. Пик загруженности' : 'e.g., Rush hour intervention')
    : (isRu ? 'напр. Комплексный бенчмарк коридора' : (t.experimentNamePlaceholder || 'e.g., Corridor benchmark'))
  const trafficLevelsLabel = isRu ? 'Уровни трафика' : (t.trafficLevels || 'Traffic Levels')
  const profileLabel = isRu ? 'Профиль симуляции' : (t.simulationProfile || 'Simulation Profile')
  const interventionsLabel = isRu ? 'Выбор мер и вмешательств' : (t.interventionSel || 'Interventions')
  const ctaButtonText = analysisType === 'scenario'
    ? (isRu ? 'Запустить сценарий' : (t.runScenario || 'Run Scenario'))
    : (isRu ? 'Запустить симуляцию' : (t.runExperiment || 'Run Simulation'))

  return (
    <div className="panel-card experiment-builder" style={{
      background: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(20px)',
      border: '1px solid rgba(255, 255, 255, 0.12)',
      borderRadius: '16px',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.08)',
      padding: '1.25rem',
      color: '#f8fafc',
    }}>
      {/* Eyebrow & Title */}
      <div style={{ marginBottom: '1.1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.3rem' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#38bdf8', boxShadow: '0 0 8px #38bdf8', display: 'inline-block' }}></span>
          <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: '#7dd3fc', fontWeight: 700 }}>
            {eyebrowText}
          </span>
        </div>
        <h3 style={{ fontSize: '1.15rem', color: '#ffffff', fontWeight: 700, margin: 0, letterSpacing: '-0.01em' }}>
          {titleText}
        </h3>
      </div>

      {/* Analysis Type Toggle (Segmented Control) */}
      <div className="control-group" style={{ marginBottom: '1rem' }}>
        <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700, display: 'block', marginBottom: '0.4rem' }}>
          {analysisTypeLabel}
        </label>
        <div className="segmented-control" style={{
          display: 'flex',
          gap: '0.35rem',
          background: 'rgba(10, 15, 29, 0.85)',
          padding: '0.3rem',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}>
          <button 
            type="button"
            style={{
              flex: 1,
              border: analysisType === 'scenario' ? '1px solid #38bdf8' : '1px solid transparent',
              background: analysisType === 'scenario' ? 'linear-gradient(135deg, rgba(14, 165, 233, 0.25) 0%, rgba(2, 132, 199, 0.15) 100%)' : 'transparent',
              color: analysisType === 'scenario' ? '#38bdf8' : '#94a3b8',
              padding: '0.5rem 0.6rem',
              borderRadius: '9px',
              fontWeight: analysisType === 'scenario' ? 700 : 500,
              fontSize: '0.84rem',
              cursor: 'pointer',
              boxShadow: analysisType === 'scenario' ? '0 0 14px rgba(56, 189, 248, 0.25)' : 'none',
              transition: 'all 0.2s ease',
            }}
            onClick={() => setAnalysisType('scenario')}
          >
            {quickWhatIfLabel}
          </button>
          <button 
            type="button"
            style={{
              flex: 1,
              border: analysisType === 'experiment' ? '1px solid #38bdf8' : '1px solid transparent',
              background: analysisType === 'experiment' ? 'linear-gradient(135deg, rgba(14, 165, 233, 0.25) 0%, rgba(2, 132, 199, 0.15) 100%)' : 'transparent',
              color: analysisType === 'experiment' ? '#38bdf8' : '#94a3b8',
              padding: '0.5rem 0.6rem',
              borderRadius: '9px',
              fontWeight: analysisType === 'experiment' ? 700 : 500,
              fontSize: '0.84rem',
              cursor: 'pointer',
              boxShadow: analysisType === 'experiment' ? '0 0 14px rgba(56, 189, 248, 0.25)' : 'none',
              transition: 'all 0.2s ease',
            }}
            onClick={() => setAnalysisType('experiment')}
          >
            {experimentTabLabel}
          </button>
        </div>
      </div>

      {/* Experiment / Scenario Name */}
      <div className="control-group" style={{ marginBottom: '1rem' }}>
        <label htmlFor="exp-name" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700, display: 'block', marginBottom: '0.4rem' }}>
          {nameLabel}
        </label>
        <input
          id="exp-name"
          type="text"
          value={experimentName}
          onChange={e => setExperimentName(e.target.value)}
          placeholder={placeholderText}
          disabled={isRunning}
          style={{
            width: '100%',
            background: 'rgba(10, 15, 29, 0.75)',
            border: '1px solid rgba(255, 255, 255, 0.14)',
            borderRadius: '10px',
            padding: '0.6rem 0.85rem',
            color: '#f8fafc',
            fontSize: '0.88rem',
            boxSizing: 'border-box',
            outline: 'none',
            transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
          }}
          onFocus={e => {
            e.target.style.borderColor = '#38bdf8'
            e.target.style.boxShadow = '0 0 0 3px rgba(56, 189, 248, 0.2)'
          }}
          onBlur={e => {
            e.target.style.borderColor = 'rgba(255, 255, 255, 0.14)'
            e.target.style.boxShadow = 'none'
          }}
        />
      </div>

      {/* Traffic Levels */}
      <div className="control-group" style={{ marginBottom: '1rem' }}>
        <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700, display: 'block', marginBottom: '0.4rem' }}>
          {trafficLevelsLabel}
        </label>
        <div className="checkbox-group" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.45rem' }}>
          {TRAFFIC_LEVELS.map(level => {
            const isChecked = selectedTrafficLevels.includes(level)
            return (
              <label 
                key={level} 
                className={`checkbox-option ${isChecked ? 'checked' : ''}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.35rem',
                  padding: '0.5rem 0.3rem',
                  borderRadius: '10px',
                  border: isChecked ? '1px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.1)',
                  background: isChecked ? 'linear-gradient(135deg, rgba(14, 165, 233, 0.22) 0%, rgba(2, 132, 199, 0.12) 100%)' : 'rgba(30, 41, 59, 0.6)',
                  color: isChecked ? '#38bdf8' : '#cbd5e1',
                  fontWeight: isChecked ? 700 : 500,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  boxShadow: isChecked ? '0 0 12px rgba(56, 189, 248, 0.25)' : 'none',
                  transition: 'all 0.2s ease',
                  userSelect: 'none',
                }}
              >
                <input
                  type={analysisType === 'scenario' ? 'radio' : 'checkbox'}
                  checked={isChecked}
                  onChange={() => toggleTrafficLevel(level)}
                  disabled={isRunning}
                  name="traffic-level"
                  style={{ accentColor: '#38bdf8', width: '13px', height: '13px', margin: 0 }}
                />
                <span>{level}×</span>
              </label>
            )
          })}
        </div>
      </div>

      {/* Simulation Profile */}
      <div className="control-group" style={{ marginBottom: '1rem' }}>
        <label htmlFor="exp-profile" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700, display: 'block', marginBottom: '0.4rem' }}>
          {profileLabel}
        </label>
        <select
          id="exp-profile"
          value={simulationProfile}
          onChange={e => setSimulationProfile(e.target.value)}
          disabled={isRunning}
          style={{
            width: '100%',
            background: 'rgba(10, 15, 29, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.14)',
            borderRadius: '10px',
            padding: '0.6rem 0.85rem',
            color: '#f8fafc',
            fontSize: '0.86rem',
            outline: 'none',
            cursor: 'pointer',
          }}
        >
          {SIMULATION_PROFILES.map(p => (
            <option key={p.id} value={p.id} style={{ background: '#0f172a', color: '#f8fafc' }}>
              {getProfileLabel(p)}
            </option>
          ))}
        </select>
        <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '0.35rem', lineHeight: 1.4 }}>
          {getProfileDesc()}
        </div>
        
        {simulationProfile === 'Custom' && (
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem' }}>
            <div style={{ flex: 1 }}>
              <label htmlFor="warmup-steps" style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>{isRu ? 'Шаги прогрева' : 'Warm-up Steps'}</label>
              <input
                id="warmup-steps"
                type="number"
                value={warmupSteps}
                onChange={e => setWarmupSteps(Number(e.target.value))}
                min="0"
                step="100"
                disabled={isRunning}
                style={{ width: '100%', marginTop: '0.2rem', padding: '0.45rem', background: 'rgba(10,15,29,0.85)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', color: '#fff', fontSize: '0.82rem' }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label htmlFor="measurement-steps" style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>{isRu ? 'Шаги измерения' : 'Measurement Steps'}</label>
              <input
                id="measurement-steps"
                type="number"
                value={measurementSteps}
                onChange={e => setMeasurementSteps(Number(e.target.value))}
                min="100"
                step="100"
                disabled={isRunning}
                style={{ width: '100%', marginTop: '0.2rem', padding: '0.45rem', background: 'rgba(10,15,29,0.85)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', color: '#fff', fontSize: '0.82rem' }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Interventions Checklist */}
      <div className="control-group" style={{ marginBottom: '1rem' }}>
        <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700, display: 'block', marginBottom: '0.4rem' }}>
          {interventionsLabel}
        </label>
        {registryLoading ? (
          <p className="traffic-legend muted" style={{ marginTop: '0.35rem' }}>{t.loadingInterventions || (isRu ? 'Загрузка реестра мер…' : 'Loading intervention registry…')}</p>
        ) : registryError ? (
          <div className="error-box" style={{ marginTop: '0.35rem' }}>{registryError}</div>
        ) : (
          <div className="intervention-checklist" style={{
            display: 'grid',
            gap: '0.45rem',
            maxHeight: '290px',
            overflowY: 'auto',
            paddingRight: '0.25rem',
          }}>
            {interventionRegistry.map(iv => {
              const isSim = iv.evaluation_mode === 'SIMULATED'
              const badgeClass = isSim ? 'provenance-badge simulated' : 'provenance-badge estimated'
              const badgeText = isRu ? (isSim ? 'СМОДЕЛИРОВАНО' : 'ОЦЕНЕНО') : (isSim ? 'SIMULATED' : 'ESTIMATED')
              const isChecked = selectedInterventionIds.includes(iv.id)
              const rawLabel = iv.label || iv.id
              const labelRu = iv.label_ru || INTERVENTION_LABELS_RU[rawLabel] || rawLabel
              const label = isRu ? labelRu : (iv.label_en || rawLabel)

              return (
                <label 
                  key={iv.id} 
                  className={`intervention-option ${isChecked ? 'checked' : ''}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '0.6rem',
                    padding: '0.6rem 0.85rem',
                    borderRadius: '10px',
                    border: isChecked ? '1px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.09)',
                    background: isChecked ? 'linear-gradient(135deg, rgba(14, 165, 233, 0.18) 0%, rgba(2, 132, 199, 0.1) 100%)' : 'rgba(30, 41, 59, 0.55)',
                    boxShadow: isChecked ? '0 0 16px rgba(56, 189, 248, 0.2)' : 'none',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    userSelect: 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flex: 1, minWidth: 0 }}>
                    <input
                      type={analysisType === 'scenario' ? 'radio' : 'checkbox'}
                      checked={isChecked}
                      onChange={() => toggleIntervention(iv.id)}
                      disabled={isRunning}
                      name="intervention-id"
                      style={{ accentColor: '#38bdf8', width: '14px', height: '14px', flexShrink: 0 }}
                    />
                    <span className="iv-label" style={{
                      fontSize: '0.84rem',
                      fontWeight: isChecked ? 600 : 400,
                      color: isChecked ? '#ffffff' : '#cbd5e1',
                      lineHeight: 1.35,
                    }}>
                      {label}
                    </span>
                  </div>
                  <span className={badgeClass} style={{
                    fontSize: '0.68rem',
                    padding: '2px 7px',
                    borderRadius: '6px',
                    fontWeight: 700,
                    letterSpacing: '0.04em',
                    flexShrink: 0,
                    background: isSim ? 'rgba(56, 189, 248, 0.16)' : 'rgba(245, 158, 11, 0.16)',
                    color: isSim ? '#38bdf8' : '#fbbf24',
                    border: isSim ? '1px solid rgba(56, 189, 248, 0.35)' : '1px solid rgba(245, 158, 11, 0.35)',
                  }}>
                    {badgeText}
                  </span>
                </label>
              )
            })}
          </div>
        )}
      </div>

      {/* Condition Preview Glassmorphic Box */}
      <div className="condition-preview" style={{
        background: conditionBlocked 
          ? 'rgba(239, 68, 68, 0.15)' 
          : conditionWarning 
            ? 'rgba(245, 158, 11, 0.15)' 
            : 'linear-gradient(135deg, rgba(14, 165, 233, 0.16) 0%, rgba(2, 132, 199, 0.08) 100%)',
        border: `1px solid ${conditionBlocked ? 'rgba(239, 68, 68, 0.45)' : conditionWarning ? 'rgba(245, 158, 11, 0.45)' : 'rgba(56, 189, 248, 0.4)'}`,
        borderRadius: '12px',
        padding: '0.75rem 1rem',
        fontSize: '0.84rem',
        marginBottom: '1rem',
        color: '#f8fafc',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
      }}>
        {isRu ? (
          <span>
            <strong style={{ color: '#38bdf8', fontWeight: 700 }}>{selectedTrafficLevels.length}</strong> ур. трафика × <strong style={{ color: '#38bdf8', fontWeight: 700 }}>{selectedInterventionIds.length || 1}</strong> мер = <strong style={{ color: '#38bdf8', fontWeight: 700 }}>{conditionCount}</strong> усл.
          </span>
        ) : (
          <span>
            <strong style={{ color: '#38bdf8', fontWeight: 700 }}>{selectedTrafficLevels.length}</strong> traffic levels × <strong style={{ color: '#38bdf8', fontWeight: 700 }}>{selectedInterventionIds.length || 1}</strong> interventions = <strong style={{ color: '#38bdf8', fontWeight: 700 }}>{conditionCount}</strong> conditions
          </span>
        )}
        {conditionBlocked && <div style={{ color: '#f87171', marginTop: '0.35rem', fontWeight: 600 }}>{t.conditionLimitExceeded || 'Превышает лимит условий'}</div>}
        {conditionWarning && !conditionBlocked && <div style={{ color: '#fbbf24', marginTop: '0.35rem', fontWeight: 600 }}>{t.conditionWarning || 'Большая партия'}</div>}
      </div>

      {/* CTA Run Button */}
      <div className="button-stack">
        <button
          type="button"
          className="accent-glow-btn"
          onClick={runExperimentNow}
          disabled={!canRun || isRunning}
          style={{
            width: '100%',
            padding: '0.8rem 1rem',
            justifyContent: 'center',
            fontSize: '0.95rem',
            fontWeight: 700,
            color: '#ffffff',
            background: isRunning 
              ? 'rgba(30, 41, 59, 0.8)' 
              : 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
            border: isRunning 
              ? '1px solid rgba(255, 255, 255, 0.15)' 
              : '1px solid rgba(56, 189, 248, 0.6)',
            borderRadius: '11px',
            boxShadow: isRunning 
              ? 'none' 
              : '0 4px 20px rgba(2, 132, 199, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.25)',
            cursor: (!canRun || isRunning) ? 'not-allowed' : 'pointer',
            opacity: (!canRun && !isRunning) ? 0.45 : 1,
            transition: 'all 0.2s ease',
          }}
        >
          {isRunning ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.6rem' }}>
              <svg className="spin-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
              </svg>
              {analysisType === 'scenario' ? (isRu ? 'Выполнение сценария…' : 'Running Scenario…') : (isRu ? 'Выполнение симуляции…' : 'Running Simulation…')}
            </span>
          ) : (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              <span>🚀</span>
              <span>{ctaButtonText}</span>
            </span>
          )}
        </button>
      </div>
    </div>
  )
}
