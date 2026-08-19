import { useState, useEffect } from 'react'
import { fetchInterventions, runExperiment } from '../api/client'

const TRAFFIC_LEVELS = [0.8, 1.0, 1.2, 1.4]
const DURATION_OPTIONS = [300, 600, 900]
const MAX_CONDITIONS_WARN = 20
const MAX_CONDITIONS_HARD = 50

export function useExperiment() {
  // Builder state
  const [experimentName, setExperimentName] = useState('')
  const [selectedTrafficLevels, setSelectedTrafficLevels] = useState([1.0])
  const [selectedInterventionIds, setSelectedInterventionIds] = useState([])
  
  const SIMULATION_PROFILES = [
    { id: 'Demo Burst', steps: 300, warmup_steps: 0, measurement_steps: 300, desc: 'Fast interactive simulation (No warm-up)' },
    { id: 'Standard Evaluation', steps: 900, warmup_steps: 300, measurement_steps: 600, desc: 'Stable comparison (300 warm-up + 600 measurement)' },
    { id: 'Extended Evaluation', steps: 1800, warmup_steps: 600, measurement_steps: 1200, desc: 'Long-run validation (600 warm-up + 1200 measurement)' },
    { id: 'Custom', steps: 0, warmup_steps: 0, measurement_steps: 300, desc: 'Custom configured' }
  ]
  const [simulationProfile, setSimulationProfile] = useState(SIMULATION_PROFILES[1].id)
  const [warmupSteps, setWarmupSteps] = useState(SIMULATION_PROFILES[1].warmup_steps)
  const [measurementSteps, setMeasurementSteps] = useState(SIMULATION_PROFILES[1].measurement_steps)
  
  // When profile changes, update the explicit step inputs
  const handleProfileChange = (profileId) => {
    setSimulationProfile(profileId)
    const profile = SIMULATION_PROFILES.find(p => p.id === profileId)
    if (profile && profile.id !== 'Custom') {
      setWarmupSteps(profile.warmup_steps)
      setMeasurementSteps(profile.measurement_steps)
    }
  }

  const duration = warmupSteps + measurementSteps

  // Registry
  const [interventionRegistry, setInterventionRegistry] = useState([])
  const [registryLoading, setRegistryLoading] = useState(false)
  const [registryError, setRegistryError] = useState('')

  // Execution state
  const [status, setStatus] = useState('READY') // READY | RUNNING | COMPLETED | FAILED | PARTIALLY_COMPLETED
  const [experimentResult, setExperimentResult] = useState(null)
  const [displayedResult, setDisplayedResult] = useState(null)
  const [runError, setRunError] = useState('')

  // Load intervention registry on mount
  useEffect(() => {
    setRegistryLoading(true)
    fetchInterventions()
      .then(data => {
        setInterventionRegistry(data)
        setRegistryError('')
      })
      .catch(err => setRegistryError(err.message || 'Failed to load interventions'))
      .finally(() => setRegistryLoading(false))
  }, [])

  const [analysisType, setAnalysisType] = useState('scenario') // 'scenario' | 'experiment'

  const conditionCount = selectedTrafficLevels.length * Math.max(selectedInterventionIds.length, 1)
  const conditionWarning = conditionCount > MAX_CONDITIONS_WARN
  const conditionBlocked = conditionCount > MAX_CONDITIONS_HARD

  const toggleTrafficLevel = (level) => {
    setSelectedTrafficLevels(prev => {
      if (analysisType === 'scenario') return [level]
      return prev.includes(level) ? prev.filter(l => l !== level) : [...prev, level]
    })
  }

  const toggleIntervention = (id) => {
    setSelectedInterventionIds(prev => {
      if (analysisType === 'scenario') return [id]
      return prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    })
  }

  // Ensure constraints when switching types
  useEffect(() => {
    if (analysisType === 'scenario') {
      if (selectedTrafficLevels.length > 1) setSelectedTrafficLevels([selectedTrafficLevels[0]])
      if (selectedInterventionIds.length > 1) setSelectedInterventionIds([selectedInterventionIds[0]])
    }
  }, [analysisType])

  const canRun = selectedTrafficLevels.length > 0 && selectedInterventionIds.length > 0 && !conditionBlocked

  const runExperimentNow = async () => {
    if (!canRun) return
    setStatus('RUNNING')
    setRunError('')
    setExperimentResult(null)
    try {
      const result = await runExperiment({
        name: experimentName.trim() || (analysisType === 'scenario' ? 'Unnamed Scenario' : 'Unnamed Experiment'),
        traffic_levels: selectedTrafficLevels,
        intervention_ids: selectedInterventionIds,
        duration,
        warmup_steps: warmupSteps,
        measurement_steps: measurementSteps,
        simulation_profile: simulationProfile,
      })
      setExperimentResult(result)
      const s = result?.summary?.status
      if (s === 'COMPLETED') setStatus('COMPLETED')
      else if (s === 'PARTIALLY_COMPLETED') setStatus('PARTIALLY_COMPLETED')
      else setStatus('FAILED')
    } catch (err) {
      setRunError(err.message || 'Simulation failed')
      setStatus('FAILED')
    }
  }

  const reset = () => {
    setStatus('READY')
    setExperimentResult(null)
    setRunError('')
  }

  return {
    // Config
    analysisType, setAnalysisType,
    experimentName, setExperimentName,
    selectedTrafficLevels, toggleTrafficLevel, setSelectedTrafficLevels,
    selectedInterventionIds, toggleIntervention, setSelectedInterventionIds,
    simulationProfile, setSimulationProfile: handleProfileChange, SIMULATION_PROFILES,
    warmupSteps, setWarmupSteps,
    measurementSteps, setMeasurementSteps,
    duration,
    // Registry
    interventionRegistry, registryLoading, registryError,
    // Matrix preview
    conditionCount, conditionWarning, conditionBlocked,
    // Execution
    status, experimentResult, displayedResult, setDisplayedResult, runError,
    canRun,
    runExperimentNow,
    reset,
    // Constants
    TRAFFIC_LEVELS,
    DURATION_OPTIONS,
  }
}
