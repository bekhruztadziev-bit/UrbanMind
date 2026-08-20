/**
 * Data normalization layer for UrbanMind frontend.
 * Ensures that all responses from the backend conform to safe defaults
 * and prevents React runtime errors or blank/blue screens caused by unexpected shapes.
 */

export const INTERVENTION_LABELS_RU = {
  'Green-wave corridor coordination (40 km/h)': 'Координированная «зеленая волна» (40 км/ч)',
  'Extend main green phase (+5s)': 'Продление зеленой фазы (+5 с)',
  'Extend main green phase (+10s)': 'Продление зеленой фазы (+10 с)',
  'Reduce competing phase (-5s)': 'Сокращение конкурирующей фазы (-5 с)',
  'Bus-priority corridor (+8s)': 'Коридор с приоритетом автобусов (+8 с)',
  'Pedestrian priority window (+6s)': 'Окно приоритета пешеходов (+6 с)',
  'School-zone speed calming (30 km/h)': 'Успокоение трафика в школьной зоне (30 км/ч)',
  'Short-stay curb rotation (15 min)': 'Ротация парковки короткого пребывания (15 мин)',
  'Green-wave corridor coordination': 'Координированная «зеленая волна» (40 км/ч)',
  'Extend main green phase': 'Продление основной зеленой фазы',
  'Reduce competing phase': 'Сокращение конкурирующей фазы',
  'Bus-priority corridor': 'Коридор с приоритетом автобусов',
  'Pedestrian priority window': 'Окно приоритета пешеходов',
  'School-zone speed calming': 'Успокоение трафика в школьной зоне (30 км/ч)',
  'Short-stay curb rotation': 'Ротация парковки короткого пребывания',
  'Green Wave Coordination': 'Координированная «зеленая волна» (40 км/ч)',
  'green_wave_coordination': 'Координированная «зеленая волна»',
  'extend_green': 'Продление зеленой фазы',
  'reduce_green': 'Сокращение конкурирующей фазы',
  'bus_priority': 'Коридор с приоритетом автобусов',
  'pedestrian_priority': 'Окно приоритета пешеходов',
  'school_zone_slowdown': 'Успокоение трафика в школьной зоне',
  'parking_turnover': 'Ротация парковки короткого пребывания',
}

export const METRIC_NAMES_RU = {
  'Delay': 'Задержка',
  'Travel Time': 'Время в пути',
  'Stops / Veh': 'Остановки на авто',
  'Stops / Vehicle': 'Остановки на авто',
  'Queue Length': 'Длина очереди',
  'Throughput': 'Пропускная способность',
  'CO₂ Emissions': 'Выбросы CO₂',
  'CO2 Emissions': 'Выбросы CO₂',
  'average_waiting_seconds': 'Задержка',
  'mean_completed_vehicle_waiting_seconds': 'Задержка завершенных поездок',
  'mean_active_vehicle_waiting_seconds': 'Задержка активных ТС',
  'average_travel_time_seconds': 'Время в пути',
  'stops_per_vehicle': 'Остановки на авто',
  'mean_queue_length_meters': 'Длина очереди',
  'throughput_vehicles_per_hour': 'Пропускная способность',
  'co2_kg': 'Выбросы CO₂',
  'sumo_co2_kg': 'Выбросы CO₂',
  'nox_g': 'Выбросы NOₓ',
  'sumo_nox_g': 'Выбросы NOₓ',
  'noise_db': 'Уровень шума',
  'pedestrian_delay_seconds': 'Задержка пешеходов',
  'accessibility_score': 'Доступность',
}

export const METRIC_NAMES_EN = {
  'Задержка': 'Delay',
  'Время в пути': 'Travel Time',
  'Остановки на авто': 'Stops / Veh',
  'Длина очереди': 'Queue Length',
  'Пропускная способность': 'Throughput',
  'Выбросы CO₂': 'CO₂ Emissions',
  'Выбросы NOₓ': 'NOₓ Emissions',
  'Уровень шума': 'Noise Level',
  'Задержка пешеходов': 'Pedestrian Delay',
  'Доступность': 'Accessibility',
}

/**
 * Safely parse any value to a valid finite number.
 * Never returns NaN, null, or undefined.
 */
export function safeNumber(val, defaultVal = 0, decimals = null) {
  if (val === null || val === undefined) return defaultVal
  const num = Number(val)
  if (isNaN(num) || !isFinite(num)) return defaultVal
  if (decimals !== null && typeof decimals === 'number') {
    return Number(num.toFixed(decimals))
  }
  return num
}

/**
 * Safely format a number to a fixed decimal string.
 * Never throws TypeError or returns 'NaN'.
 */
export function formatSafeNumber(val, decimals = 1, defaultStr = '—') {
  if (val === null || val === undefined) return defaultStr
  const num = Number(val)
  if (isNaN(num) || !isFinite(num)) return defaultStr
  return num.toFixed(decimals)
}

export function translateInterventionSummaryToRu(summaryEn, labelRu = '') {
  if (!summaryEn) return ''
  const s = summaryEn.toLowerCase()
  if (s.includes('green-wave') || s.includes('green wave') || s.includes('зелен')) {
    return 'Координированная «зеленая волна» по коридору: Данная мера координирует сдвиги фаз и время горения зеленого сигнала по всему коридору для непрерывного безостановочного проезда и снижения задержек.'
  }
  if (s.includes('bus') || s.includes('автобус')) {
    return 'Коридор с приоритетом автобусов: Данная мера отдает приоритет автобусному коридору и улучшает доступность общественного транспорта без блокировки локальной сети.'
  }
  if (s.includes('pedestrian') || s.includes('пешеход')) {
    return 'Окно приоритета пешеходов: Данная мера обеспечивает пешеходам и школьникам более безопасный и предсказуемый интервал перехода.'
  }
  if (s.includes('school') || s.includes('школ')) {
    return 'Успокоение трафика в школьной зоне: Данная мера снижает риски в наиболее уязвимой зоне района за счет успокоения движения и улучшения видимости.'
  }
  if (s.includes('curb') || s.includes('parking') || s.includes('парковк')) {
    return 'Ротация парковки короткого пребывания: Данная мера улучшает оборачиваемость парковочных мест и снижает помехи от маневров у местных точек притяжения.'
  }
  if (s.includes('reduce') || s.includes('сокращен')) {
    return 'Сокращение конкурирующей фазы: Данная мера оптимизирует баланс фаз на перекрестке, высвобождая дополнительное время для основного потока.'
  }
  if (s.includes('extend') || s.includes('продлен')) {
    return 'Продление основной зеленой фазы: Данная мера увеличивает пропускную способность главного направления коридора в пиковые интервалы.'
  }
  return summaryEn
}

export function normalizeMetrics(raw = {}) {
  if (!raw || typeof raw !== 'object') {
    return {
      steps: 300,
      warmup_steps: 0,
      measurement_steps: 300,
      scenario: 'midday',
      average_speed_kmh: 0,
      average_waiting_seconds: 0,
      mean_completed_vehicle_waiting_seconds: 0,
      mean_active_vehicle_waiting_seconds: 0,
      average_travel_time_seconds: 0,
      stops_per_vehicle: 0,
      mean_queue_length_meters: 0,
      throughput_vehicles_per_hour: 0,
      max_vehicle_count: 0,
      traffic_light_count: 0,
      traffic_light_ids: [],
      co2_kg: 0,
      nox_g: 0,
      noise_db: 0,
      pedestrian_delay_seconds: 0,
      accessibility_score: 100,
      sumo_co2_kg: 0,
      sumo_nox_g: 0,
      is_fallback: false,
      structured_metrics: null,
    }
  }

  const avgWait = safeNumber(raw.average_waiting_seconds, 0)
  const meanCompleted = raw.mean_completed_vehicle_waiting_seconds != null
    ? safeNumber(raw.mean_completed_vehicle_waiting_seconds, avgWait)
    : avgWait
  const meanActive = raw.mean_active_vehicle_waiting_seconds != null
    ? safeNumber(raw.mean_active_vehicle_waiting_seconds, avgWait)
    : avgWait

  return {
    steps: safeNumber(raw.steps, 300),
    warmup_steps: safeNumber(raw.warmup_steps, 0),
    measurement_steps: safeNumber(raw.measurement_steps, 300),
    scenario: String(raw.scenario || 'midday'),
    average_speed_kmh: safeNumber(raw.average_speed_kmh, 0),
    average_waiting_seconds: avgWait,
    mean_completed_vehicle_waiting_seconds: meanCompleted,
    mean_active_vehicle_waiting_seconds: meanActive,
    average_travel_time_seconds: safeNumber(raw.average_travel_time_seconds, 0),
    stops_per_vehicle: safeNumber(raw.stops_per_vehicle, 0),
    mean_queue_length_meters: safeNumber(raw.mean_queue_length_meters, 0),
    throughput_vehicles_per_hour: safeNumber(raw.throughput_vehicles_per_hour, 0),
    max_vehicle_count: safeNumber(raw.max_vehicle_count, 0),
    traffic_light_count: safeNumber(raw.traffic_light_count, 0),
    traffic_light_ids: Array.isArray(raw.traffic_light_ids) ? raw.traffic_light_ids : [],
    co2_kg: safeNumber(raw.co2_kg, 0),
    nox_g: safeNumber(raw.nox_g, 0),
    noise_db: safeNumber(raw.noise_db, 0),
    pedestrian_delay_seconds: safeNumber(raw.pedestrian_delay_seconds, 0),
    accessibility_score: safeNumber(raw.accessibility_score, 100),
    sumo_co2_kg: safeNumber(raw.sumo_co2_kg, 0),
    sumo_nox_g: safeNumber(raw.sumo_nox_g, 0),
    is_fallback: Boolean(raw.is_fallback),
    structured_metrics: raw.structured_metrics || null,
  }
}

export function normalizeCandidateDelta(rawDelta = {}) {
  if (!rawDelta || typeof rawDelta !== 'object') {
    return {
      average_speed_kmh: 0,
      average_waiting_seconds: 0,
      average_travel_time_seconds: 0,
      mean_queue_length_meters: 0,
      stops_per_vehicle: 0,
      throughput_vehicles_per_hour: 0,
      mean_completed_vehicle_waiting_seconds: 0,
      max_vehicle_count: 0,
      co2_kg: 0,
      nox_g: 0,
      noise_db: 0,
      pedestrian_delay_seconds: 0,
      accessibility_score: 0,
      sumo_co2_kg: 0,
      sumo_nox_g: 0,
      delay_improvement_pct: 0,
      travel_time_improvement_pct: 0,
      queue_improvement_pct: 0,
      stops_improvement_pct: 0,
      throughput_improvement_pct: 0,
      emissions_improvement_pct: 0,
    }
  }

  return {
    average_speed_kmh: safeNumber(rawDelta.average_speed_kmh, 0),
    average_waiting_seconds: safeNumber(rawDelta.average_waiting_seconds, 0),
    average_travel_time_seconds: safeNumber(rawDelta.average_travel_time_seconds, 0),
    mean_queue_length_meters: safeNumber(rawDelta.mean_queue_length_meters, 0),
    stops_per_vehicle: safeNumber(rawDelta.stops_per_vehicle, 0),
    throughput_vehicles_per_hour: safeNumber(rawDelta.throughput_vehicles_per_hour, 0),
    mean_completed_vehicle_waiting_seconds: safeNumber(rawDelta.mean_completed_vehicle_waiting_seconds, 0),
    max_vehicle_count: safeNumber(rawDelta.max_vehicle_count, 0),
    co2_kg: safeNumber(rawDelta.co2_kg, 0),
    nox_g: safeNumber(rawDelta.nox_g, 0),
    noise_db: safeNumber(rawDelta.noise_db, 0),
    pedestrian_delay_seconds: safeNumber(rawDelta.pedestrian_delay_seconds, 0),
    accessibility_score: safeNumber(rawDelta.accessibility_score, 0),
    sumo_co2_kg: safeNumber(rawDelta.sumo_co2_kg, 0),
    sumo_nox_g: safeNumber(rawDelta.sumo_nox_g, 0),
    delay_improvement_pct: safeNumber(rawDelta.delay_improvement_pct, 0),
    travel_time_improvement_pct: safeNumber(rawDelta.travel_time_improvement_pct, 0),
    queue_improvement_pct: safeNumber(rawDelta.queue_improvement_pct, 0),
    stops_improvement_pct: safeNumber(rawDelta.stops_improvement_pct, 0),
    throughput_improvement_pct: safeNumber(rawDelta.throughput_improvement_pct, 0),
    emissions_improvement_pct: safeNumber(rawDelta.emissions_improvement_pct, 0),
  }
}

export function normalizeTradeoffSummary(tradeoff = {}) {
  if (!tradeoff || typeof tradeoff !== 'object') {
    return {
      improved: [],
      worsened: [],
      unchanged: [],
      verdict_en: 'Balanced operational profile.',
      verdict_ru: 'Сбалансированный операционный профиль.',
    }
  }

  const normalizeItem = (item) => {
    if (!item) return null
    if (typeof item === 'string') {
      const nameRu = METRIC_NAMES_RU[item] || item
      const nameEn = METRIC_NAMES_EN[item] || item
      return { name: item, name_en: nameEn, name_ru: nameRu, change_pct: 0, metric: '' }
    }
    const rawName = String(item.name || item.metric || 'Metric')
    const nameRu = String(item.name_ru || METRIC_NAMES_RU[rawName] || rawName)
    const nameEn = String(item.name_en || METRIC_NAMES_EN[rawName] || rawName)
    return {
      name: rawName,
      name_en: nameEn,
      name_ru: nameRu,
      change_pct: safeNumber(item.change_pct, 0),
      metric: String(item.metric || ''),
    }
  }

  return {
    improved: Array.isArray(tradeoff.improved) ? tradeoff.improved.map(normalizeItem).filter(Boolean) : [],
    worsened: Array.isArray(tradeoff.worsened) ? tradeoff.worsened.map(normalizeItem).filter(Boolean) : [],
    unchanged: Array.isArray(tradeoff.unchanged) ? tradeoff.unchanged.map(normalizeItem).filter(Boolean) : [],
    verdict_en: String(tradeoff.verdict_en || 'Balanced operational profile.'),
    verdict_ru: String(tradeoff.verdict_ru || 'Сбалансированный операционный профиль.'),
  }
}

export function normalizePolicyBreakdown(pb = {}) {
  if (!pb || typeof pb !== 'object') return null
  return {
    policy_id: String(pb.policy_id || 'balanced'),
    policy_name: String(pb.policy_name || 'BALANCED'),
    policy_name_ru: String(pb.policy_name_ru || 'БАЛАНС'),
    overall_score: safeNumber(pb.overall_score, 0),
    ranking_score: safeNumber(pb.ranking_score, 0),
    mobility_score: safeNumber(pb.mobility_score, 0),
    environment_score: safeNumber(pb.environment_score, 0),
    accessibility_score: safeNumber(pb.accessibility_score, 0),
    weights: pb.weights && typeof pb.weights === 'object' ? pb.weights : { mobility: 0.45, environment: 0.35, accessibility: 0.20 },
    is_valid: Boolean(pb.is_valid !== false),
    constraint_violations_en: Array.isArray(pb.constraint_violations_en) ? pb.constraint_violations_en.map(String) : [],
    constraint_violations_ru: Array.isArray(pb.constraint_violations_ru) ? pb.constraint_violations_ru.map(String) : [],
    metric_deltas: pb.metric_deltas && typeof pb.metric_deltas === 'object' ? pb.metric_deltas : {},
  }
}

export function normalizePolicyComparison(pc = {}) {
  if (!pc || typeof pc !== 'object') return null
  const result = {}
  for (const [key, item] of Object.entries(pc)) {
    if (item && typeof item === 'object') {
      result[key] = {
        policy_id: String(item.policy_id || key),
        policy_name: String(item.policy_name || key.toUpperCase()),
        policy_name_ru: String(item.policy_name_ru || key.toUpperCase()),
        icon: String(item.icon || '🎯'),
        objective_question: String(item.objective_question || ''),
        objective_question_ru: String(item.objective_question_ru || ''),
        why_won: String(item.why_won || ''),
        why_won_en: String(item.why_won_en || item.why_won || ''),
        why_won_ru: String(item.why_won_ru || item.why_won || ''),
        best_candidate_id: String(item.best_candidate_id || ''),
        best_candidate_label: String(item.best_candidate_label || item.best_candidate_id || ''),
        best_candidate_score: safeNumber(item.best_candidate_score, 0),
        overall_score: safeNumber(item.overall_score, 0),
        mobility_score: safeNumber(item.mobility_score, 0),
        environment_score: safeNumber(item.environment_score, 0),
        accessibility_score: safeNumber(item.accessibility_score, 0),
        average_waiting_seconds: safeNumber(item.average_waiting_seconds, 0),
        average_travel_time_seconds: safeNumber(item.average_travel_time_seconds, 0),
        co2_kg: safeNumber(item.co2_kg, 0),
        throughput_vehicles_per_hour: safeNumber(item.throughput_vehicles_per_hour, 0),
        stops_per_vehicle: safeNumber(item.stops_per_vehicle, 0),
        delay_improvement_pct: safeNumber(item.delay_improvement_pct, 0),
        emissions_improvement_pct: safeNumber(item.emissions_improvement_pct, 0),
        throughput_improvement_pct: safeNumber(item.throughput_improvement_pct, 0),
        stops_improvement_pct: safeNumber(item.stops_improvement_pct, 0),
        tradeoffs: normalizeTradeoffSummary(item.tradeoffs),
      }
    }
  }
  return result
}

export function normalizeCandidate(cand = {}) {
  if (!cand || typeof cand !== 'object') return null

  const id = String(cand.id || 'unknown_candidate')
  const label = String(cand.label || cand.id || 'Intervention')
  const labelEn = String(cand.label_en || label)
  const labelRu = String(cand.label_ru || INTERVENTION_LABELS_RU[label] || INTERVENTION_LABELS_RU[labelEn] || label)

  const rawSummary = String(cand.summary || cand.description || '')
  const summaryEn = String(cand.summary_en || rawSummary)
  const summaryRu = String(cand.summary_ru || translateInterventionSummaryToRu(summaryEn, labelRu))

  return {
    id,
    label,
    label_en: labelEn,
    label_ru: labelRu,
    category: String(cand.category || 'mobility'),
    category_label: String(cand.category_label || cand.category || 'mobility'),
    type: String(cand.type || ''),
    description: rawSummary,
    summary: rawSummary,
    summary_en: summaryEn,
    summary_ru: summaryRu,
    evaluation_mode: String(cand.evaluation_mode || 'HEURISTIC'),
    score: safeNumber(cand.score, 0),
    selected_reason: String(cand.selected_reason || ''),
    selected_reason_ru: String(cand.selected_reason_ru || ''),
    selected_reason_en: String(cand.selected_reason_en || cand.selected_reason || ''),
    why_won: String(cand.why_won || cand.selected_reason || ''),
    why_won_ru: String(cand.why_won_ru || cand.selected_reason_ru || ''),
    why_won_en: String(cand.why_won_en || cand.selected_reason_en || ''),
    intervention: cand.intervention && typeof cand.intervention === 'object' ? cand.intervention : {},
    metrics: normalizeMetrics(cand.metrics),
    delta: normalizeCandidateDelta(cand.delta),
    tradeoff_summary: normalizeTradeoffSummary(cand.tradeoff_summary),
    policy_breakdown: normalizePolicyBreakdown(cand.policy_breakdown),
  }
}


export function normalizeOptimizationResult(opt = {}) {
  if (!opt || typeof opt !== 'object') return null

  const rawCandidates = Array.isArray(opt.candidates) ? opt.candidates : []
  const candidates = rawCandidates.map(normalizeCandidate).filter(Boolean)
  const rawRanked = Array.isArray(opt.ranked_candidates) ? opt.ranked_candidates : candidates
  const ranked = rawRanked.map(normalizeCandidate).filter(Boolean)
  const best = normalizeCandidate(opt.best_candidate) || ranked[0] || null

  return {
    scenario: String(opt.scenario || 'midday'),
    policy: String(opt.policy || 'balanced'),
    policy_definition: opt.policy_definition && typeof opt.policy_definition === 'object' ? opt.policy_definition : null,
    policy_comparison: normalizePolicyComparison(opt.policy_comparison),
    baseline: normalizeMetrics(opt.baseline),
    candidates,
    ranked_candidates: ranked,
    best_candidate: best,
    ai: normalizeAIResponse(opt.ai),
    insights: opt.insights && typeof opt.insights === 'object' ? opt.insights : {},
    product_positioning: opt.product_positioning && typeof opt.product_positioning === 'object' ? opt.product_positioning : {},
  }
}

export function normalizeExperimentCondition(c = {}) {
  if (!c || typeof c !== 'object') return null

  const metricDeltas = {}
  if (c.metric_deltas && typeof c.metric_deltas === 'object') {
    for (const [key, val] of Object.entries(c.metric_deltas)) {
      if (val && typeof val === 'object') {
        metricDeltas[key] = {
          absolute: safeNumber(val.absolute, 0),
          percentage: val.percentage != null ? safeNumber(val.percentage, 0) : null,
        }
      }
    }
  }

  const rawLabel = String(c.intervention_label || c.intervention_id || 'Control')
  const labelRu = INTERVENTION_LABELS_RU[rawLabel] || rawLabel

  return {
    condition_id: String(c.condition_id || 'cond'),
    traffic_multiplier: safeNumber(c.traffic_multiplier, 1.0),
    intervention_id: c.intervention_id ? String(c.intervention_id) : null,
    intervention_label: rawLabel,
    intervention_label_ru: labelRu,
    evaluation_mode: String(c.evaluation_mode || 'CONTROL'),
    control_metrics: c.control_metrics ? normalizeMetrics(c.control_metrics) : null,
    scenario_metrics: c.scenario_metrics ? normalizeMetrics(c.scenario_metrics) : null,
    metric_deltas: metricDeltas,
    metric_provenance: c.metric_provenance && typeof c.metric_provenance === 'object' ? c.metric_provenance : {},
    status: String(c.status || 'COMPLETED'),
    error: c.error ? String(c.error) : null,
  }
}

export function normalizeExperimentResult(exp = {}) {
  if (!exp || typeof exp !== 'object') return null

  const conditions = Array.isArray(exp.conditions)
    ? exp.conditions.map(normalizeExperimentCondition).filter(Boolean)
    : []

  const completedCount = conditions.filter(c => c.status === 'COMPLETED').length
  const failedCount = conditions.filter(c => c.status === 'FAILED').length
  const skippedCount = conditions.filter(c => c.status === 'SKIPPED').length

  let expStatus = 'COMPLETED'
  if (failedCount > 0 && completedCount === 0) expStatus = 'FAILED'
  else if (failedCount > 0 || skippedCount > 0) expStatus = 'PARTIALLY_COMPLETED'

  return {
    experiment_id: String(exp.experiment_id || 'EXP'),
    schema_version: safeNumber(exp.schema_version, 1),
    name: String(exp.name || 'Unnamed Experiment'),
    created_at: String(exp.created_at || new Date().toISOString()),
    duration: safeNumber(exp.duration, 300),
    traffic_levels: Array.isArray(exp.traffic_levels)
      ? exp.traffic_levels.map(v => safeNumber(v, 1.0))
      : [1.0],
    intervention_ids: Array.isArray(exp.intervention_ids)
      ? exp.intervention_ids.map(String)
      : [],
    conditions,
    summary: exp.summary && typeof exp.summary === 'object' ? {
      total: safeNumber(exp.summary.total, conditions.length),
      completed: safeNumber(exp.summary.completed, completedCount),
      failed: safeNumber(exp.summary.failed, failedCount),
      skipped: safeNumber(exp.summary.skipped, skippedCount),
      status: String(exp.summary.status || expStatus),
    } : {
      total: conditions.length,
      completed: completedCount,
      failed: failedCount,
      skipped: skippedCount,
      status: expStatus,
    },
    metadata: exp.metadata && typeof exp.metadata === 'object' ? exp.metadata : {},
    metric_provenance: exp.metric_provenance && typeof exp.metric_provenance === 'object' ? exp.metric_provenance : {},
  }
}

export function normalizeAIResponse(ai = {}) {
  if (!ai || typeof ai !== 'object') return null

  const isAi = Boolean(ai.is_ai ?? (ai.provider === 'gemini'))
  const provider = String(ai.provider || (isAi ? 'gemini' : 'rule_based_fallback'))
  const status = String(ai.status || (isAi ? 'COMPLETE' : 'FALLBACK'))

  const toStringArray = (val) => {
    if (Array.isArray(val)) return val.map(String).filter(Boolean)
    if (typeof val === 'string' && val.trim()) return [val.trim()]
    return []
  }

  return {
    status,
    provider,
    provenance: String(ai.provenance || (isAi ? 'AI ANALYSIS' : 'RULE-BASED SUMMARY')),
    is_ai: isAi,
    summary: String(ai.summary || ai.reasoning || ai.recommendation || ''),
    key_improvements: toStringArray(ai.key_improvements).length > 0
      ? toStringArray(ai.key_improvements)
      : (ai.expected_impact ? [String(ai.expected_impact)] : []),
    tradeoffs: toStringArray(ai.tradeoffs),
    concerns: toStringArray(ai.concerns),
    recommendation: String(ai.recommendation || ''),
    confidence: ['high', 'medium', 'low'].includes(String(ai.confidence).toLowerCase())
      ? String(ai.confidence).toLowerCase()
      : 'medium',
    signal_focus: String(ai.signal_focus || ''),
    scope: String(ai.scope || ''),
    expected_impact: String(ai.expected_impact || ''),
    reasoning: String(ai.reasoning || ai.summary || ''),
  }
}
