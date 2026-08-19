import React from 'react'

export function AIExplanation({ t, optResult }) {
  return (
    <>
      <div className="panel-card">
        <h3>{t.whyChoice}</h3>
        {optResult?.ai ? (
          <>
            <p><strong>{optResult.ai.recommendation}</strong></p>
            <p className="selection-reason">{optResult.ai.signal_focus || t.signalFocus}</p>
            <p className="traffic-legend muted">{optResult.ai.scope || t.optimizationScope}</p>
            <p>{optResult.ai.reasoning}</p>
            <ul>
              {optResult.ai.tradeoffs.map((item) => <li key={item}>{item}</li>)}
            </ul>
            <p className="confidence">{t.confidence}: {optResult.ai.confidence}</p>
            <p className="traffic-legend muted">{optResult.ai.expected_impact || t.expectedImpact}</p>
            {optResult.ai.best_signal_id ? <p className="traffic-legend muted">{t.bestSignalId}: {optResult.ai.best_signal_id}</p> : null}
          </>
        ) : (
          <p>{t.explanationAfter}</p>
        )}
      </div>

      <div className="panel-card">
        <h3>{t.mahallaPosition}</h3>
        <p className="recommendation-tag">{t.neighborhoodMobilityIntelligence}</p>
        <p>{optResult?.insights?.headline || t.neighborhoodPlatform}</p>
        <p className="selection-reason">{optResult?.insights?.context || t.neighborhoodContext}</p>
      </div>
    </>
  )
}
