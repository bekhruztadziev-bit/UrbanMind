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
import { PilotWorkspace } from './components/Pilots/PilotWorkspace'
import { DecisionReportModal } from './components/Reports/DecisionReportModal'
import { CaseStudyModal } from './components/CaseStudy/CaseStudyModal'
import { AmbientBackground } from './components/Common/AmbientBackground'
import { HeroIntro } from './components/Common/HeroIntro'
import { generateDecisionReport } from './api/client'
import './App.css'



const fallbackDistrict = {
  name: 'Tashkent Central Corridor',
  bounds: {
    name: 'Tashkent Central Corridor',
    southwest: [41.3080, 69.2550],
    northeast: [41.3250, 69.2780],
    polygon: [
      [41.3080, 69.2550],
      [41.3080, 69.2780],
      [41.3250, 69.2780],
      [41.3250, 69.2550],
    ],
  },
  urban_context: {
    name: 'Tashkent',
    center: [41.2995, 69.2401],
    display_bounds: {
      southwest: [41.24, 69.12],
      northeast: [41.38, 69.38],
    },
    simulation_region: {
      name: 'Tashkent Central Corridor',
      southwest: [41.3080, 69.2550],
      northeast: [41.3250, 69.2780],
    },
  },
  intersections: [
    { id: 'demo_signal_group_a', name: 'Signal Group A (demonstration)', coords: [41.3168, 69.2666], traffic_light_ids: [], spatial_provenance: 'PRODUCT_DEMO_LABEL' },
    { id: 'demo_signal_group_b', name: 'Signal Group B (demonstration)', coords: [41.3182, 69.2684], traffic_light_ids: [], spatial_provenance: 'PRODUCT_DEMO_LABEL' },
  ],
  roads: [],
  // Offline fallback is a visual shell, not a spatial evidence source.
  facilities: [],
  monitoring_stations: [],
}

function App() {
  const { language, setLanguage, toggleLanguage, t } = useLanguage('en')
  
  const [health, setHealth] = useState(null)
  const [mahalla, setMahalla] = useState(fallbackDistrict)
  const scenario = 'midday'
  const [selectedId, setSelectedId] = useState('demo_signal_group_a')
  const [currentView, setCurrentView] = useState('insights')
  const [globalError, setGlobalError] = useState('')
  const [presentationMode, setPresentationMode] = useState(false)
  const [showIntro, setShowIntro] = useState(() => localStorage.getItem('urbanmind_hide_intro') !== 'true')
  const [dashboardReportModalOpen, setDashboardReportModalOpen] = useState(false)
  const [dashboardReportData, setDashboardReportData] = useState(null)
  const [caseStudyModalOpen, setCaseStudyModalOpen] = useState(false)

  const {
    metrics,
    optResult,
    selectedCandidateId,
    setSelectedCandidateId,
    selectedCandidate,
    loading: optLoading,
    optError,
    activePolicy,
    setActivePolicy,
    customWeights,
    setCustomWeights,
    aiState,
    aiData,
    aiError,
    handleRunAIExplanation,
    handleAnalyze,
    handleOptimize
  } = useOptimization(mahalla, scenario, language)

  const experiment = useExperiment()
  const experimentHistory = useExperimentHistory()

  const handleOpenDashboardDecisionReport = async (resultToReport) => {
    const target = resultToReport || optResult
    if (!target) return
    try {
      const rep = await generateDecisionReport({
        ...target,
        policy_id: activePolicy,
        custom_weights: customWeights,
        language: language,
      })
      setDashboardReportData(rep)
      setDashboardReportModalOpen(true)
    } catch (err) {
      console.error('Failed to generate dashboard decision report:', err)
    }
  }

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
        <FAQ t={t} setCurrentView={setCurrentView} toggleLanguage={toggleLanguage} onOpenIntro={() => setShowIntro(true)} />
        <HeroIntro t={t} language={language} setLanguage={setLanguage} toggleLanguage={toggleLanguage} isOpen={showIntro} onClose={() => setShowIntro(false)} onSelectView={(v) => setCurrentView(v)} />
      </>
    )
  }

  if (currentView === 'explore') {
    return (
      <>
        <AmbientBackground />
        <ExperimentsPage
          t={t}
          language={language}
          setCurrentView={setCurrentView}
          toggleLanguage={toggleLanguage}
          experiment={experiment}
          experimentHistory={experimentHistory}
          presentationMode={presentationMode}
          onOpenIntro={() => setShowIntro(true)}
        />
        <HeroIntro t={t} language={language} setLanguage={setLanguage} toggleLanguage={toggleLanguage} isOpen={showIntro} onClose={() => setShowIntro(false)} onSelectView={(v) => setCurrentView(v)} />
      </>
    )
  }

  if (currentView === 'history') {
    return (
      <>
        <AmbientBackground />
        <HistoryPage
          t={t}
          language={language}
          setCurrentView={setCurrentView}
          toggleLanguage={toggleLanguage}
          experimentHistory={experimentHistory}
          setDisplayedResult={experiment.setDisplayedResult}
          onOpenIntro={() => setShowIntro(true)}
        />
        <HeroIntro t={t} language={language} setLanguage={setLanguage} toggleLanguage={toggleLanguage} isOpen={showIntro} onClose={() => setShowIntro(false)} onSelectView={(v) => setCurrentView(v)} />
      </>
    )
  }

  if (currentView === 'pilots') {
    return (
      <>
        <AmbientBackground />

        <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '1.2rem', minHeight: '100vh', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Header
            t={t}
            currentView={currentView}
            setCurrentView={setCurrentView}
            toggleLanguage={toggleLanguage}
            onOpenIntro={() => setShowIntro(true)}
            onOpenCaseStudy={() => setCaseStudyModalOpen(true)}
          />
          <PilotWorkspace
            language={language}
            t={t}
            onNavigateToDashboard={() => setCurrentView('insights')}
            onNavigateToExplore={() => setCurrentView('explore')}
            onOpenCaseStudy={() => setCaseStudyModalOpen(true)}
            onOpenReport={() => {
              if (optResult) {
                handleOpenDashboardDecisionReport(optResult)
              }
            }}
          />
        </div>
        <HeroIntro t={t} language={language} setLanguage={setLanguage} toggleLanguage={toggleLanguage} isOpen={showIntro} onClose={() => setShowIntro(false)} onSelectView={(v) => setCurrentView(v)} />
        <DecisionReportModal
          isOpen={dashboardReportModalOpen}
          onClose={() => setDashboardReportModalOpen(false)}
          report={dashboardReportData}
          language={language}
          t={t}
        />
        <CaseStudyModal
          isOpen={caseStudyModalOpen}
          onClose={() => setCaseStudyModalOpen(false)}
          language={language}
          t={t}
        />
      </>
    )
  }

  return (

    <>
      <AmbientBackground />
      <HeroIntro t={t} language={language} setLanguage={setLanguage} toggleLanguage={toggleLanguage} isOpen={showIntro} onClose={() => setShowIntro(false)} onSelectView={(v) => setCurrentView(v)} />
      <div className="app-shell">
        <div className="map-panel">
          <Header 
            t={t}
            currentView={currentView} 
            setCurrentView={setCurrentView} 
            toggleLanguage={toggleLanguage} 
            onOpenIntro={() => setShowIntro(true)}
            onOpenCaseStudy={() => setCaseStudyModalOpen(true)}
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
            setSelectedId('demo_signal_group_a')
          })}
          activePolicy={activePolicy}
          onSelectPolicy={setActivePolicy}
          customWeights={customWeights}
          onUpdateCustomWeights={setCustomWeights}
          aiState={aiState}
          aiData={aiData}
          aiError={aiError}
          handleRunAIExplanation={handleRunAIExplanation}
          loading={optLoading}
          error={globalError || optError}
          setCurrentView={setCurrentView}
          onTestInExplore={handleTestInExplore}
          onOpenDecisionReport={handleOpenDashboardDecisionReport}
        />
      </div>

      <DecisionReportModal
        isOpen={dashboardReportModalOpen}
        onClose={() => setDashboardReportModalOpen(false)}
        report={dashboardReportData}
        language={language}
        t={t}
      />
      <CaseStudyModal
        isOpen={caseStudyModalOpen}
        onClose={() => setCaseStudyModalOpen(false)}
        language={language}
        t={t}
      />
    </>
  )
}

export default App
