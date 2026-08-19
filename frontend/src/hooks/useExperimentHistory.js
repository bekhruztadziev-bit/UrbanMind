import { useState, useEffect } from 'react'

const STORAGE_KEY = 'urbanmind_experiment_history'
const MAX_HISTORY = 20

export function useExperimentHistory() {
  const [experiments, setExperiments] = useState([])

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) setExperiments(JSON.parse(stored))
    } catch { /* silently ignore */ }
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(experiments))
    } catch { /* silently ignore */ }
  }, [experiments])

  const saveExperiment = (result) => {
    setExperiments(prev => {
      const next = [result, ...prev].slice(0, MAX_HISTORY)
      return next
    })
  }

  const removeExperiment = (id) => {
    setExperiments(prev => prev.filter(e => e.experiment_id !== id))
  }

  const clearHistory = () => setExperiments([])

  return { experiments, saveExperiment, removeExperiment, clearHistory }
}
