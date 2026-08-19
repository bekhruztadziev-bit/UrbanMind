import React from 'react'

export function AIExplanation({ t, optResult, aiState = 'READY', aiData = null, aiError = '', onRunAIExplanation }) {
  const currentAI = aiData || optResult?.ai

  return (
    <>
      <div className="panel-card ai-explanation-panel">
        <div className="card-header-with-badge">
          <h3>{t.whyChoice || 'Why this choice?'}</h3>
          <span className="provenance-badge estimated" title="AI-generated interpretation from simulation data">
            {t.aiInterpretation || 'ANALYTICAL INTERPRETATION'}
          </span>
        </div>

        {!optResult ? (
          <p className="traffic-legend muted">{t.explanationAfter || 'Run optimization to generate AI-assisted decision explanation.'}</p>
        ) : aiState === 'ANALYZING' ? (
          <div className="ai-loading-state">
            <svg className="spin-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
            </svg>
            <span>{t.generatingAI || 'Generating AI corridor trade-off reasoning…'}</span>
          </div>
        ) : aiState === 'ERROR' ? (
          <div className="ai-error-state">
            <p className="error-text">{aiError || t.aiErrorPrompt || 'Unable to connect to AI reasoning service.'}</p>
            {onRunAIExplanation && (
              <button type="button" className="ghost-button mt-2" onClick={onRunAIExplanation}>
                {t.retryAI || 'Retry AI Analysis'}
              </button>
            )}
          </div>
        ) : currentAI ? (
          <div className="ai-content-body">
            <p className="ai-recommendation"><strong>{currentAI.recommendation}</strong></p>
            {currentAI.signal_focus && <p className="selection-reason">{currentAI.signal_focus}</p>}
            {currentAI.scope && <p className="traffic-legend muted">{currentAI.scope}</p>}
            {currentAI.reasoning && <p className="ai-reasoning-text">{currentAI.reasoning}</p>}
            
            {Array.isArray(currentAI.tradeoffs) && currentAI.tradeoffs.length > 0 && (
              <div className="ai-tradeoffs-section">
                <span className="tradeoffs-title">{t.tradeoffs || 'Key Trade-offs & Operational Notes:'}</span>
                <ul className="tradeoffs-list">
                  {currentAI.tradeoffs.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="ai-meta-row">
              <span className="confidence">
                {t.confidence || 'Confidence'}: <strong>{currentAI.confidence || 'medium'}</strong>
              </span>
              {currentAI.provider === 'deterministic_fallback' && (
                <span className="status-note">{t.deterministicFallbackActive || 'Deterministic Fallback Active'}</span>
              )}
            </div>

            {currentAI.expected_impact && (
              <p className="traffic-legend muted">{currentAI.expected_impact}</p>
            )}

            {onRunAIExplanation && (
              <button type="button" className="ghost-button mt-3" onClick={onRunAIExplanation}>
                {t.refreshAI || 'Re-evaluate with AI'}
              </button>
            )}
          </div>
        ) : (
          <div className="ai-ready-state">
            <p className="traffic-legend muted">
              {t.readyForAI || 'Optimization complete. Request deep AI operational reasoning.'}
            </p>
            {onRunAIExplanation && (
              <button type="button" className="accent mt-2" onClick={onRunAIExplanation}>
                {t.runAIAnalysis || 'Run AI Analysis'}
              </button>
            )}
          </div>
        )}
      </div>

      <div className="panel-card">
        <h3>{t.mahallaPosition || 'URBANMIND position'}</h3>
        <p className="recommendation-tag">{t.neighborhoodMobilityIntelligence || 'Urban digital twin platform'}</p>
        <p>{optResult?.insights?.headline || t.neighborhoodPlatform || 'URBANMIND is a digital twin platform for local signal and flow decisions.'}</p>
        <p className="selection-reason">{optResult?.insights?.context || t.neighborhoodContext || 'It helps urban teams act before congestion affects daily movement and access.'}</p>
      </div>
    </>
  )
}

