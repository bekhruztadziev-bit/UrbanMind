import { useState, useMemo, useEffect, useRef } from 'react'
import { fetchMetrics, fetchOptimize, fetchAIExplanation } from '../api/client'
import { normalizeMetrics, normalizeOptimizationResult, normalizeAIResponse } from '../utils/normalize'

const defaultMetrics = normalizeMetrics({})

export function useOptimization(mahalla, scenario, language = 'en') {
  const [metrics, setMetrics] = useState(defaultMetrics)
  const [optResult, setOptResult] = useState(null)
  const [selectedCandidateId, setSelectedCandidateId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [optError, setOptError] = useState('')

  // Explicit AI Analysis states: 'IDLE' | 'READY' | 'ANALYZING' | 'COMPLETE' | 'ERROR' | 'FALLBACK'
  const [aiState, setAiState] = useState('IDLE')
  const [aiData, setAiData] = useState(null)
  const [aiError, setAiError] = useState('')
  const prevLangRef = useRef(language)

  const handleAnalyze = async () => {
    setLoading(true)
    setOptError('')
    try {
      const data = await fetchMetrics({ steps: 300, scenario, language })
      const normalized = normalizeMetrics(data)
      setMetrics(normalized)
      setOptResult(null)
      setSelectedCandidateId(null)
      setAiState('IDLE')
      setAiData(null)
    } catch (err) {
      setOptError(err.message || 'Simulation analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const handleOptimize = async (onSuccess) => {
    setLoading(true)
    setOptError('')
    try {
      const data = await fetchOptimize({ steps: 300, scenario, language })
      const normalized = normalizeOptimizationResult(data)
      setOptResult(normalized)
      setMetrics(normalized.baseline)
      setSelectedCandidateId(normalized.best_candidate?.id || null)

      // If backend returned pre-computed AI analysis, normalize it; otherwise set state to READY for user trigger
      if (normalized.ai) {
        setAiData(normalized.ai)
        setAiState(normalized.ai.is_ai ? 'COMPLETE' : 'FALLBACK')
      } else {
        setAiState('READY')
        setAiData(null)
      }

      if (onSuccess) onSuccess(normalized)
    } catch (err) {
      setOptError(err.message || 'Optimization workflow failed')
    } finally {
      setLoading(false)
    }
  }

  const handleRunAIExplanation = async (targetLang = language) => {
    if (!optResult) return
    setAiState('ANALYZING')
    setAiError('')
    try {
      const payload = {
        baseline: optResult.baseline || metrics,
        candidates: optResult.ranked_candidates || optResult.candidates || [],
        best_candidate: selectedCandidate || optResult.best_candidate,
        language: targetLang,
      }
      const explanation = await fetchAIExplanation(payload)
      const normalized = normalizeAIResponse(explanation)
      setAiData(normalized)
      setAiState(normalized?.is_ai ? 'COMPLETE' : 'FALLBACK')
    } catch (err) {
      setAiError(err.message || 'AI assessment service unavailable')
      setAiState('ERROR')
    }
  }

  // When language switches (e.g. EN <-> RU), dynamically re-evaluate AI explanation if an optimization result exists
  useEffect(() => {
    if (prevLangRef.current !== language) {
      prevLangRef.current = language
      if (optResult && aiData) {
        handleRunAIExplanation(language)
      }
    }
  }, [language, optResult])

  const selectedCandidate = useMemo(() => {
    if (!optResult) return null
    const list = optResult.ranked_candidates || []
    if (selectedCandidateId) {
      return list.find((candidate) => candidate?.id === selectedCandidateId) || optResult.best_candidate || null
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
