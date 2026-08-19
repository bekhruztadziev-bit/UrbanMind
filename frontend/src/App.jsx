import { useEffect, useMemo, useState } from 'react'
import { fetchHealth, fetchMahalla } from './api/client'
import { useLanguage } from './hooks/useLanguage'
import { useOptimization } from './hooks/useOptimization'
import { useExperiment } from './hooks/useExperiment'
import { useExperimentHistory } from './hooks/useExperimentHistory'

import { Header } from './components/Header/Header'
import { MapView } from './components/MapView/MapView'
import { Dashboard } from './components/Dashboard/Dashboard'
import { FAQ } from './components/FAQ/FAQ'
import { ExperimentsPage } from './components/Experiments/ExperimentsPage'
import { HistoryPage } from './components/History/HistoryPage'
import { AmbientBackground } from './components/Common/AmbientBackground'
import './App.css'

const fallbackDistrict = {
  name: 'Yakkabog District (offline preview)',
  bounds: {
    name: 'Yakkabog District',
    southwest: [41.3052, 69.2564],
    northeast: [41.3276, 69.2804],
    polygon: [
      [41.3052, 69.2564],
      [41.3052, 69.2804],
      [41.3276, 69.2804],
      [41.3276, 69.2564],
    ],
  },
  intersections: [
    { id: 'intersection_1', name: 'Central Crossroads', coords: [39.0842, 66.8615], traffic_light_ids: ['cluster_1'] },
    { id: 'intersection_2', name: 'School Junction', coords: [39.0886, 66.8668], traffic_light_ids: ['cluster_2'] },
    { id: 'intersection_3', name: 'Market Roundabout', coords: [39.0809, 66.8531], traffic_light_ids: ['cluster_3'] },
  ],
  roads: [
    [[39.074, 66.846], [39.096, 66.846]],
    [[39.074, 66.861], [39.096, 66.861]],
    [[39.074, 66.879], [39.096, 66.879]],
    [[39.0815, 66.846], [39.0815, 66.879]],
    [[39.089, 66.846], [39.089, 66.879]],
  ],
  facilities: [
    { id: 'school_1', type: 'school', name: 'District School', coords: [39.0883, 66.8661] },
    { id: 'clinic_1', type: 'clinic', name: 'Community Clinic', coords: [39.0821, 66.8576] },
    { id: 'kindergarten_1', type: 'kindergarten', name: 'Kindergarten #2', coords: [39.0851, 66.8504] },
    { id: 'bus_stop_1', type: 'bus_stop', name: 'Market Stop', coords: [39.0901, 66.8584] },
  ],
}

function App() {
  const { language, toggleLanguage, t } = useLanguage('en')
  
  const [health, setHealth] = useState(null)
  const [mahalla, setMahalla] = useState(null)
  const scenario = 'midday'
  const [selectedId, setSelectedId] = useState('intersection_1')
  const [currentView, setCurrentView] = useState('insights')
  const [globalError, setGlobalError] = useState('')
  const [presentationMode, setPresentationMode] = useState(false)

  const {
    metrics,
    optResult,
    selectedCandidateId,
    setSelectedCandidateId,
    selectedCandidate,
    loading: optLoading,
    optError,
    aiState,
    aiData,
    aiError,
    handleRunAIExplanation,
    handleAnalyze,
    handleOptimize
  } = useOptimization(mahalla, scenario, language)

  const experiment = useExperiment()
  const experimentHistory = useExperimentHistory()

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [healthResponse, mahallaResponse] = await Promise.all([
          fetchHealth(),
          fetchMahalla(),
        ])
        setHealth(healthResponse)
        setMahalla(mahallaResponse)
      } catch (err) {
        setHealth({ ok: false })
        setMahalla(fallbackDistrict)
        setGlobalError(t.backendOffline)
      }
    }

    loadInitialData()
  }, [t.backendOffline])

  const getIntersectionForTrafficLight = (trafficLightId) => {
    if (!mahalla || !trafficLightId) return null
    return mahalla.intersections.find((item) => item.traffic_light_ids.includes(trafficLightId)) || null
  }

  const selectedIntersection = useMemo(() => {
    if (!mahalla) return null
    return mahalla.intersections.find((item) => item.id === selectedId) || mahalla.intersections[0]
  }, [mahalla, selectedId])

  const targetSignalId = selectedCandidate?.intervention?.traffic_light_id || selectedIntersection?.traffic_light_ids?.[0] || null

  useEffect(() => {
    if (!optResult?.best_candidate || !mahalla) return
    const match = getIntersectionForTrafficLight(optResult.best_candidate.intervention?.traffic_light_id)
    if (match) {
      setSelectedId(match.id)
    }
  }, [optResult, mahalla])

  const handleTestInExplore = (candidate) => {
    if (candidate?.id) {
      experiment.setAnalysisType('scenario')
      experiment.setSelectedInterventionIds([candidate.id])
    }
    setCurrentView('explore')
  }

  if (!mahalla) {
    return (
      <>
        <AmbientBackground />
        <div className="app-shell loading">{t.appTitle ? `${t.appTitle}...` : 'Loading UrbanMind…'}</div>
      </>
    )
  }

  if (currentView === 'faq') {
    return (
      <>
        <AmbientBackground />
        <FAQ t={t} setCurrentView={setCurrentView} toggleLanguage={toggleLanguage} />
      </>
    )
  }

  if (currentView === 'explore') {
    return (
      <>
        <AmbientBackground />
        <ExperimentsPage
          t={t}
          setCurrentView={setCurrentView}
          toggleLanguage={toggleLanguage}
          experiment={experiment}
          experimentHistory={experimentHistory}
          presentationMode={presentationMode}
        />
      </>
    )
  }

  if (currentView === 'history') {
    return (
      <>
        <AmbientBackground />
        <HistoryPage
          t={t}
          setCurrentView={setCurrentView}
          toggleLanguage={toggleLanguage}
          experimentHistory={experimentHistory}
          setDisplayedResult={experiment.setDisplayedResult}
        />
      </>
    )
  }

  return (
    <>
      <AmbientBackground />
      <div className="app-shell">
        <div className="map-panel">
          <Header 
            t={t}
            currentView={currentView} 
            setCurrentView={setCurrentView} 
            toggleLanguage={toggleLanguage} 
          />
          <MapView
            mahalla={mahalla}
            selectedId={selectedId}
            setSelectedId={setSelectedId}
            language={language}
          />
        </div>

        <Dashboard
          t={t}
          language={language}
          selectedIntersection={selectedIntersection}
          targetSignalId={targetSignalId}
          metrics={metrics}
          optResult={optResult}
          selectedCandidate={selectedCandidate}
          setSelectedCandidateId={setSelectedCandidateId}
          getIntersectionForTrafficLight={getIntersectionForTrafficLight}
          setSelectedId={setSelectedId}
          handleAnalyze={handleAnalyze}
          handleOptimize={() => handleOptimize((data) => {
            setSelectedId('intersection_1')
          })}
          aiState={aiState}
          aiData={aiData}
          aiError={aiError}
          handleRunAIExplanation={handleRunAIExplanation}
          loading={optLoading}
          error={globalError || optError}
          setCurrentView={setCurrentView}
          onTestInExplore={handleTestInExplore}
        />
      </div>
    </>
  )
}

export default App
