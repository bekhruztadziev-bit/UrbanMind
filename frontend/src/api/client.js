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
  return handleResponse(response)
}

export async function fetchOptimize(payload = {}) {
  const response = await fetch(`${API_BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
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

