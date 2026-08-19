import { useState, useMemo } from 'react'
import { fetchMetrics, fetchOptimize } from '../api/client'

const defaultMetrics = {
  average_speed_kmh: 0,
  average_waiting_seconds: 0,
  max_vehicle_count: 0,
  traffic_light_count: 0,
}

export function useOptimization(mahalla, scenario) {
  const [metrics, setMetrics] = useState(defaultMetrics)
  const [optResult, setOptResult] = useState(null)
  const [selectedCandidateId, setSelectedCandidateId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [optError, setOptError] = useState('')

  const handleAnalyze = async () => {
    setLoading(true)
    setOptError('')
    try {
      const data = await fetchMetrics({ steps: 300, scenario })
      setMetrics(data)
      setOptResult(null)
      setSelectedCandidateId(null)
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
      const data = await fetchOptimize({ steps: 300, scenario })
      setOptResult(data)
      setMetrics(data.baseline)
      setSelectedCandidateId(data.best_candidate?.id || null)
      if (onSuccess) onSuccess(data)
    } catch (err) {
      setOptError(err.message)
    } finally {
      setLoading(false)
    }
  }

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
    handleAnalyze,
    handleOptimize
  }
}
