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
    { id: 'intersection_1', name: 'Main Square', coords: [41.3168, 69.2666], traffic_light_ids: ['cluster_1'] },
    { id: 'intersection_2', name: 'School Junction', coords: [41.3182, 69.2684], traffic_light_ids: ['cluster_2'] },
    { id: 'intersection_3', name: 'Clinic Roundabout', coords: [41.3157, 69.2692], traffic_light_ids: ['cluster_3'] },
    { id: 'intersection_4', name: 'Market Edge', coords: [41.3149, 69.2638], traffic_light_ids: ['cluster_4'] },
    { id: 'intersection_5', name: 'North Residential Corridor', coords: [41.3199, 69.2718], traffic_light_ids: ['cluster_5'] },
    { id: 'intersection_6', name: 'Bus Terminal Link', coords: [41.3136, 69.2707], traffic_light_ids: ['cluster_6'] },
  ],
  roads: [],
  facilities: [
    { id: 'school_1', type: 'school', name: 'District School', coords: [41.3186, 69.2698] },
    { id: 'clinic_1', type: 'clinic', name: 'Community Clinic', coords: [41.3154, 69.2676] },
    { id: 'kindergarten_1', type: 'kindergarten', name: 'Kindergarten #4', coords: [41.3171, 69.2648] },
    { id: 'bus_stop_1', type: 'bus_stop', name: 'Bus Stop East', coords: [41.3191, 69.2661] },
    { id: 'park_1', type: 'park', name: 'Park', coords: [41.3138, 69.2702] },
    { id: 'facility_1', type: 'administrative', name: 'Mahalla Office', coords: [41.3147, 69.2641] },
    { id: 'facility_2', type: 'public', name: 'Community Center', coords: [41.3198, 69.2709] },
    { id: 'market_1', type: 'market', name: 'Market Square', coords: [41.3128, 69.2645] },
    { id: 'mosque_1', type: 'religious', name: 'Mosque Lane', coords: [41.3213, 69.2727] },
  ],
  monitoring_stations: [
    { id: 'uzhydromet_chilanzar', name: 'Chilanzar', coords: [41.2856, 69.2128], source: 'Uzhydromet' },
    { id: 'uzhydromet_center', name: 'Amir Temur', coords: [41.3111, 69.2797], source: 'Uzhydromet' },
    { id: 'uzhydromet_sergeli', name: 'Sergeli', coords: [41.2275, 69.2199], source: 'Uzhydromet' },
    { id: 'uzhydromet_olmazor', name: 'Olmazor', coords: [41.3377, 69.2150], source: 'Uzhydromet' },
    { id: 'uzhydromet_yakkasaray', name: 'Yakkasaray', coords: [41.2887, 69.2864], source: 'Uzhydromet' },
  ],
}

function App() {
  const { language, setLanguage, toggleLanguage, t } = useLanguage('en')
  
  const [health, setHealth] = useState(null)
  const [mahalla, setMahalla] = useState(fallbackDistrict)
  const scenario = 'midday'
  const [selectedId, setSelectedId] = useState('intersection_1')
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
              } else {
                handleOpenDashboardDecisionReport({
                  scenario: 'evening_peak',
                  policy: activePolicy,
                  baseline: {
                    average_waiting_seconds: 24.8,
                    average_travel_time_seconds: 118.5,
                    average_speed_kmh: 22.1,
                    stops_per_vehicle: 1.45,
                    throughput_vehicles_per_hour: 1820.0,
                    co2_kg: 18.2,
                  },
                  best_candidate: {
                    id: 'green_wave_coordination_0s_signal_timing',
                    label: 'Green Wave Corridor Progression (40 km/h offset)',
                    label_ru: 'Зеленая волна по коридору (смещение фаз под 40 км/ч)',
                    metrics: {
                      average_waiting_seconds: 17.8,
                      average_travel_time_seconds: 92.4,
                      average_speed_kmh: 27.5,
                      stops_per_vehicle: 0.85,
                      throughput_vehicles_per_hour: 2150.0,
                      co2_kg: 15.0,
                    },
                    policy_breakdown: { overall_score: 16.5, mobility_score: 24.0, environment_score: 15.0, accessibility_score: 3.0, is_valid: true },
                    tradeoff_summary: { improved: [{ name: 'Average Delay', change_pct: -28.2 }], worsened: [{ name: 'Side Street Delay', change_pct: 3.5 }] },
                  }
                })
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
            setSelectedId('intersection_1')
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

