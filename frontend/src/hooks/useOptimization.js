import { useState, useMemo, useEffect, useRef } from 'react'
import { fetchMetrics, fetchOptimize, fetchAIExplanation } from '../api/client'

const defaultMetrics = {
  average_speed_kmh: 0,
  average_waiting_seconds: 0,
  max_vehicle_count: 0,
  traffic_light_count: 0,
}

export function useOptimization(mahalla, scenario, language = 'en') {
  const [metrics, setMetrics] = useState(defaultMetrics)
  const [optResult, setOptResult] = useState(null)
  const [selectedCandidateId, setSelectedCandidateId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [optError, setOptError] = useState('')

  // Explicit AI Analysis states: 'READY' | 'ANALYZING' | 'COMPLETE' | 'ERROR' | 'FALLBACK'
  const [aiState, setAiState] = useState('READY')
  const [aiData, setAiData] = useState(null)
  const [aiError, setAiError] = useState('')
  const prevLangRef = useRef(language)

  const handleAnalyze = async () => {
    setLoading(true)
    setOptError('')
    try {
      const data = await fetchMetrics({ steps: 300, scenario, language })
      setMetrics(data)
      setOptResult(null)
      setSelectedCandidateId(null)
      setAiState('READY')
      setAiData(null)
    } catch (err) {
      setOptError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleOptimize = async (onSuccess) => {
    setLoading(true)
    setOptError('')
    try {
      const data = await fetchOptimize({ steps: 300, scenario, language })
      setOptResult(data)
      setMetrics(data.baseline)
      setSelectedCandidateId(data.best_candidate?.id || null)
      if (data.ai) {
        setAiData(data.ai)
        setAiState(data.ai.status === 'FALLBACK' ? 'FALLBACK' : 'COMPLETE')
      } else {
        setAiState('READY')
      }
      if (onSuccess) onSuccess(data)
    } catch (err) {
      setOptError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRunAIExplanation = async (targetLang = language) => {
    if (!optResult) return
    setAiState('ANALYZING')
    setAiError('')
    try {
      const explanation = await fetchAIExplanation({
        baseline: optResult.baseline || metrics,
        candidates: optResult.ranked_candidates || optResult.candidates || [],
        best_candidate: selectedCandidate || optResult.best_candidate,
        language: targetLang,
      })
      setAiData(explanation)
      setAiState(explanation.status === 'FALLBACK' ? 'FALLBACK' : 'COMPLETE')
    } catch (err) {
      setAiError(err.message || 'AI assessment service unavailable')
      setAiState('ERROR')
    }
  }

  // When language switches (e.g. EN <-> RU), dynamically re-evaluate AI explanation if an optimization result exists
  useEffect(() => {
    if (prevLangRef.current !== language) {
      prevLangRef.current = language
      if (optResult && (aiData || optResult.ai)) {
        handleRunAIExplanation(language)
      }
    }
  }, [language, optResult])

  const selectedCandidate = useMemo(() => {
    if (!optResult) return null
    const list = optResult.ranked_candidates || []
    if (selectedCandidateId) {
      return list.find((candidate) => candidate.id === selectedCandidateId) || optResult.best_candidate || null
    }
    return optResult.best_candidate || null
  }, [optResult, selectedCandidateId])

  return {
    metrics,
    setMetrics,
    optResult,
    setOptResult,
    selectedCandidateId,
    setSelectedCandidateId,
    selectedCandidate,
    loading,
    optError,
    aiState,
    aiData,
    aiError,
    handleRunAIExplanation,
    handleAnalyze,
    handleOptimize
  }
}
