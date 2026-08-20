const API_BASE = '/api'

async function handleResponse(response) {
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'API request failed')
  }
  return response.json()
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE}/health`)
  return handleResponse(response)
}

export async function fetchMahalla() {
  const response = await fetch(`${API_BASE}/mahalla`)
  return handleResponse(response)
}

export async function fetchPolicies() {
  const response = await fetch(`${API_BASE}/policies`)
  return handleResponse(response)
}

export async function fetchComparePolicies(payload = {}) {
  const response = await fetch(`${API_BASE}/policies/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}


export async function fetchMetrics(payload = {}) {
  const response = await fetch(`${API_BASE}/metrics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  try {
    return await handleResponse(response)
  } catch (apiError) {
    // Keep the dashboard usable if the API itself is temporarily unavailable.
    // This is reviewed, locked SUMO evidence—not a generated substitute.
    const fallbackResponse = await fetch('/canonical-optimization.json', { cache: 'no-store' })
    if (!fallbackResponse.ok) throw apiError
    const artifact = await fallbackResponse.json()
    if (!artifact?.baseline || typeof artifact.baseline !== 'object') throw apiError
    return {
      ...artifact.baseline,
      evidence_mode: 'PRECOMPUTED_SIMULATION_ARTIFACT',
      artifact_type: 'PRECOMPUTED_SIMULATION_ARTIFACT',
      runtime_status: 'SUMO_UNAVAILABLE_LOCKED_EVIDENCE',
      artifact_experiment_id: artifact.experiment_id,
      demand_condition: artifact.primary_demand_condition || '1.0x',
    }
  }
}

export async function fetchOptimize(payload = {}) {
  const response = await fetch(`${API_BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  try {
    return await handleResponse(response)
  } catch (apiError) {
    const policy = String(payload.policy || 'balanced').toLowerCase()
    if (policy === 'custom') throw apiError
    const fallbackResponse = await fetch('/canonical-optimization.json', { cache: 'no-store' })
    if (!fallbackResponse.ok) throw apiError
    const artifact = await fallbackResponse.json()
    const evidence = artifact.policies?.[policy]
    if (!evidence) throw apiError
    return {
      ...evidence,
      scenario: payload.scenario || 'midday',
      policy,
      evidence_mode: 'PRECOMPUTED_SIMULATION_ARTIFACT',
      artifact_type: 'PRECOMPUTED_SIMULATION_ARTIFACT',
      runtime_status: 'SUMO_UNAVAILABLE_LOCKED_EVIDENCE',
    }
  }
}

export async function fetchAIExplanation(payload = {}) {
  const response = await fetch(`${API_BASE}/ai/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function fetchScenarioRun(payload = {}) {
  const response = await fetch(`${API_BASE}/scenario/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function fetchInterventions() {
  const response = await fetch(`${API_BASE}/experiments/interventions`)
  return handleResponse(response)
}

export async function runExperiment(payload = {}) {
  const response = await fetch(`${API_BASE}/experiments/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function fetchEnvironmentCurrent() {
  const response = await fetch(`${API_BASE}/environment/current`)
  return handleResponse(response)
}

export async function fetchEnvironmentStations() {
  const response = await fetch(`${API_BASE}/environment/stations`)
  return handleResponse(response)
}

export async function fetchSpatialHierarchy() {
  const response = await fetch(`${API_BASE}/spatial/hierarchy`)
  return handleResponse(response)
}

export async function fetchSpatialScopes() {
  const response = await fetch(`${API_BASE}/spatial/scopes`)
  return handleResponse(response)
}

export async function generateDecisionReport(payload = {}) {
  const response = await fetch(`${API_BASE}/reports/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function exportReportCsvApi(payload = {}) {
  const response = await fetch(`${API_BASE}/reports/export/csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function exportReportHtmlApi(payload = {}) {
  const response = await fetch(`${API_BASE}/reports/export/html`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function fetchCalibrationStatus(scopeId = 'central_corridor') {
  const response = await fetch(`${API_BASE}/calibration/status?scope_id=${encodeURIComponent(scopeId)}`)
  return handleResponse(response)
}

export async function validateCalibration(payload = {}) {
  const response = await fetch(`${API_BASE}/calibration/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function fetchPilotCases() {
  const response = await fetch(`${API_BASE}/pilots`)
  return handleResponse(response)
}

export async function fetchPilotCase(pilotId) {
  const response = await fetch(`${API_BASE}/pilots/${encodeURIComponent(pilotId)}`)
  return handleResponse(response)
}

export async function createPilotCase(payload = {}) {
  const response = await fetch(`${API_BASE}/pilots`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function updatePilotCase(pilotId, payload = {}) {
  const response = await fetch(`${API_BASE}/pilots/${encodeURIComponent(pilotId)}/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function fetchAnalyticsSummary() {
  const response = await fetch(`${API_BASE}/analytics/summary`)
  return handleResponse(response)
}

export async function fetchCanonicalExperiment() {
  const response = await fetch(`${API_BASE}/experiments/canonical`)
  return handleResponse(response)
}

export async function fetchCanonicalCaseStudy(language = 'en') {
  const response = await fetch(`${API_BASE}/case-studies/canonical?language=${encodeURIComponent(language)}`)
  try {
    return await handleResponse(response)
  } catch (apiError) {
    // Vercel deployments without the SUMO runtime can still serve the locked,
    // reviewed canonical artifact shipped with the frontend. This is not a
    // synthetic fallback: it is the same precomputed simulation evidence used
    // by the backend artifact-backed Case Study endpoint.
    const fallbackResponse = await fetch('/canonical-case-study.json', { cache: 'no-store' })
    if (!fallbackResponse.ok) throw apiError
    const fallback = await fallbackResponse.json()
    return {
      ...fallback,
      artifact_type: fallback.artifact_type || 'PRECOMPUTED_SIMULATION_ARTIFACT',
      delivery_mode: 'STATIC_ARTIFACT_FALLBACK',
    }
  }
}

export async function fetchCaseStudies(language = 'en') {
  const response = await fetch(`${API_BASE}/case-studies?language=${encodeURIComponent(language)}`)
  return handleResponse(response)
}

export async function fetchCaseStudy(caseId, language = 'en') {
  const response = await fetch(`${API_BASE}/case-studies/${encodeURIComponent(caseId)}?language=${encodeURIComponent(language)}`)
  return handleResponse(response)
}

export async function generateCaseStudy(payload = {}) {
  const response = await fetch(`${API_BASE}/case-studies/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function exportCaseStudyCsvApi(payload = {}) {
  const response = await fetch(`${API_BASE}/case-studies/export/csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function exportCaseStudyHtmlApi(payload = {}) {
  const response = await fetch(`${API_BASE}/case-studies/export/html`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function importFieldObservations(payload = {}) {
  const response = await fetch(`${API_BASE}/calibration/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function fetchMovementMappings() {
  const response = await fetch(`${API_BASE}/mappings`)
  return handleResponse(response)
}

export async function fetchCalibrationTemplate() {
  const response = await fetch(`${API_BASE}/calibration/template`)
  return handleResponse(response)
}

export async function fetchCalibrationDatasets() {
  const response = await fetch(`${API_BASE}/calibration/datasets`)
  return handleResponse(response)
}

export async function evaluateCalibration(payload = {}) {
  const response = await fetch(`${API_BASE}/calibration/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function fetchCalibrationProtocol(scopeId = 'central_corridor') {
  const response = await fetch(`${API_BASE}/calibration/protocol?scope_id=${encodeURIComponent(scopeId)}`)
  return handleResponse(response)
}



