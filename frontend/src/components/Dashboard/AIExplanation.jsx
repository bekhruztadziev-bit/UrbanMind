import React from 'react'

export function AIExplanation({ t, optResult, aiState = 'READY', aiData = null, aiError = '', onRunAIExplanation }) {
  const currentAI = aiData || optResult?.ai

  return (
    <>
      <div className="panel-card ai-explanation-panel">
        <div className="card-header-with-badge">
          <h3>{t.whyChoice || 'Why this choice?'}</h3>
          <span className="provenance-badge ai" title={t.aiProvenanceDesc || 'AI-generated analytical interpretation from observed & simulated dynamics'}>
            {t.aiAnalysis || 'AI ANALYSIS'}
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
            {/* 1. Assessment */}
            <div className="ai-assessment-block">
              <span className="ai-block-title">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                </svg>
                {t.aiAssessment || 'Strategic Assessment'}
              </span>
              <p className="ai-recommendation"><strong>{currentAI.recommendation}</strong></p>
            </div>

            {/* 2. Key Corridor Findings */}
            <div className="ai-findings-block">
              <span className="tradeoffs-title">{t.aiFindings || 'Corridor Findings & Signal Focus'}</span>
              {currentAI.signal_focus && <p className="selection-reason">{currentAI.signal_focus}</p>}
              {currentAI.reasoning && <p className="ai-reasoning-text">{currentAI.reasoning}</p>}
            </div>

            {/* 3. Expected Impact */}
            {(currentAI.expected_impact || currentAI.scope) && (
              <div className="ai-impact-block">
                <span className="tradeoffs-title">{t.aiExpectedImpact || 'Projected Operational Impact'}</span>
                {currentAI.expected_impact && <p style={{ fontSize: '0.88rem', color: 'var(--text-primary)', marginBottom: '0.3rem' }}>{currentAI.expected_impact}</p>}
                {currentAI.scope && <p className="traffic-legend muted">{currentAI.scope}</p>}
              </div>
            )}

            {/* 4. Operational Caveats & Trade-offs */}
            {Array.isArray(currentAI.tradeoffs) && currentAI.tradeoffs.length > 0 && (
              <div className="ai-caveats-block">
                <span className="ai-block-title">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                  {t.tradeoffs || 'Operational Caveats & Trade-offs'}
                </span>
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


