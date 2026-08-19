import React from 'react'

const EVAL_BADGE = {
  SIMULATED: { label: 'SIMULATED', className: 'provenance-badge simulated' },
  HEURISTIC: { label: 'ESTIMATED', className: 'provenance-badge estimated' },
}

export function ExperimentBuilder({
  t,
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

  return (
    <div className="panel-card experiment-builder">
      <h3>{t.experimentBuilder}</h3>

      {/* Analysis Type Toggle */}
      <div className="control-group">
        <label>{t.analysisType || 'Analysis Type'}</label>
        <div className="segmented-control" style={{ display: 'flex', gap: '0.2rem', background: '#e2e8f0', padding: '0.25rem', borderRadius: '8px' }}>
          <button 
            type="button"
            style={{ flex: 1, border: 'none', background: analysisType === 'scenario' ? '#fff' : 'transparent', color: analysisType === 'scenario' ? '#0f172a' : '#64748b', padding: '0.4rem', borderRadius: '6px', fontWeight: analysisType === 'scenario' ? 600 : 500, boxShadow: analysisType === 'scenario' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none', cursor: 'pointer' }}
            onClick={() => setAnalysisType('scenario')}
          >
            {t.quickWhatIf || 'Quick What-If'}
          </button>
          <button 
            type="button"
            style={{ flex: 1, border: 'none', background: analysisType === 'experiment' ? '#fff' : 'transparent', color: analysisType === 'experiment' ? '#0f172a' : '#64748b', padding: '0.4rem', borderRadius: '6px', fontWeight: analysisType === 'experiment' ? 600 : 500, boxShadow: analysisType === 'experiment' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none', cursor: 'pointer' }}
            onClick={() => setAnalysisType('experiment')}
          >
            {t.experimentTab || 'Experiment'}
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
        <label htmlFor="exp-profile">Simulation Profile</label>
        <select
          id="exp-profile"
          value={simulationProfile}
          onChange={e => setSimulationProfile(e.target.value)}
          disabled={isRunning}
        >
          {SIMULATION_PROFILES.map(p => (
            <option key={p.id} value={p.id}>{p.id} ({p.steps} steps)</option>
          ))}
        </select>
        <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem', lineHeight: 1.3 }}>
          {SIMULATION_PROFILES.find(p => p.id === simulationProfile)?.desc}
        </div>
        
        {simulationProfile === 'Custom' && (
          <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem' }}>
            <div style={{ flex: 1 }}>
              <label htmlFor="warmup-steps" style={{ fontSize: '0.8rem' }}>Warm-up Steps</label>
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
              <label htmlFor="measurement-steps" style={{ fontSize: '0.8rem' }}>Measurement Steps</label>
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
        <label>{t.interventionSel}</label>
        {registryLoading ? (
          <p className="traffic-legend muted">{t.loadingInterventions}</p>
        ) : registryError ? (
          <div className="error-box">{registryError}</div>
        ) : (
          <div className="intervention-checklist">
            {interventionRegistry.map(iv => {
              const badge = EVAL_BADGE[iv.evaluation_mode] || EVAL_BADGE.HEURISTIC
              const isChecked = selectedInterventionIds.includes(iv.id)
              return (
                <label key={iv.id} className={`intervention-option ${isChecked ? 'checked' : ''} ${analysisType === 'scenario' && !isChecked && selectedInterventionIds.length > 0 ? 'muted' : ''}`}>
                  <input
                    type={analysisType === 'scenario' ? 'radio' : 'checkbox'}
                    checked={isChecked}
                    onChange={() => toggleIntervention(iv.id)}
                    disabled={isRunning}
                    name="intervention-id"
                  />
                  <span className="iv-label">{iv.label}</span>
                  <span className={badge.className}>
                    {badge.label}
                  </span>
                </label>
              )
            })}
          </div>
        )}
      </div>

      {/* Matrix preview */}
      <div className="condition-preview" style={{
        background: conditionBlocked ? 'rgba(239,68,68,0.08)' : conditionWarning ? 'rgba(245,158,11,0.08)' : 'rgba(15,118,110,0.06)',
        border: `1px solid ${conditionBlocked ? '#ef444430' : conditionWarning ? '#f59e0b30' : '#0f766e30'}`,
        borderRadius: '10px', padding: '0.6rem 0.9rem', fontSize: '0.85rem', marginTop: '0.5rem'
      }}>
        <strong>{selectedTrafficLevels.length}</strong> {t.trafficLevels} × <strong>{selectedInterventionIds.length || 1}</strong> {t.interventions} = <strong>{conditionCount}</strong> {t.conditions}
        {conditionBlocked && <div style={{ color: '#ef4444', marginTop: '0.3rem' }}>{t.conditionLimitExceeded}</div>}
        {conditionWarning && !conditionBlocked && <div style={{ color: '#b45309', marginTop: '0.3rem' }}>{t.conditionWarning}</div>}
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
          ) : (analysisType === 'scenario' ? t.runScenario : t.runExperiment)}
        </button>
      </div>
    </div>
  )
}
