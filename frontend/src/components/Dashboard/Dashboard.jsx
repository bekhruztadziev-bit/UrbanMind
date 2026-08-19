import React from 'react'
import { MetricsGrid } from './MetricsGrid'
import { RecommendationPanel } from './RecommendationPanel'
import { AIExplanation } from './AIExplanation'
import { CandidateList } from './CandidateList'
import { EnvironmentPanel } from './EnvironmentPanel'
import { useEnvironment } from '../../hooks/useEnvironment'
export function Dashboard({
  t,
  language,
  selectedIntersection,
  targetSignalId,
  metrics,
  optResult,
  selectedCandidate,
  setSelectedCandidateId,
  getIntersectionForTrafficLight,
  setSelectedId,
  handleAnalyze,
  handleOptimize,
  loading,
  error,
  setCurrentView,
  onTestInExplore
}) {
  const envData = useEnvironment();

  return (
    <>
      <aside className="sidebar">
        <div className="panel-card">
          <h2>{t.selectedLocation}</h2>
          {selectedIntersection ? (
            <>
              <p className="location-name">{selectedIntersection.name}</p>
              <p>ID: {selectedIntersection.id}</p>
              <p>{t.trafficLights}: {selectedIntersection.traffic_light_ids.length}</p>
              <p className="traffic-legend">{t.targetSignal}: {targetSignalId || t.fallbackSelection}</p>
              <div className="legend-box">
                <div><span className="legend-swatch signal" /> {t.selectedSignal}</div>
                <div><span className="legend-swatch facility" /> {t.localFacility}</div>
              </div>
              <p className="traffic-legend muted">{t.neighborhoodCopy}</p>
            </>
          ) : (
            <p className="traffic-legend muted">{t.fallbackSelection}</p>
          )}
        </div>

        <EnvironmentPanel t={t} language={language} envData={envData} />

        <MetricsGrid t={t} metrics={metrics} optResult={optResult} />

        <div className="panel-card button-stack">
          <button type="button" onClick={handleAnalyze} disabled={loading}>
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                <svg className="spin-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
                </svg>
                {t.analyzing}
              </span>
            ) : t.analyze}
          </button>
          <button type="button" className="accent" onClick={() => handleOptimize()} disabled={loading}>
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                <svg className="spin-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
                </svg>
                {t.optimizing}
              </span>
            ) : t.optimize}
          </button>
        </div>

        {error && <div className="panel-card error-box">{error}</div>}
      </aside>

      <section className="results-panel">
        <RecommendationPanel t={t} language={language} selectedCandidate={selectedCandidate} onTestInExplore={onTestInExplore} />
        <AIExplanation t={t} optResult={optResult} />
        <CandidateList
          t={t}
          optResult={optResult}
          selectedCandidate={selectedCandidate}
          setSelectedCandidateId={setSelectedCandidateId}
          getIntersectionForTrafficLight={getIntersectionForTrafficLight}
          setSelectedId={setSelectedId}
        />
      </section>
    </>
  )
}
