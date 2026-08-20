import { exportReportCsvApi, exportReportHtmlApi } from '../api/client'

export function exportToJson(scenarios) {
  const dataStr = JSON.stringify(scenarios, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)
  triggerDownload(dataUri, `urbanmind-experiments-${Date.now()}.json`)
}

export function exportToCsv(scenarios) {
  if (!scenarios || scenarios.length === 0) return

  // Gather all possible metric keys
  const metricKeys = new Set()
  scenarios.forEach(s => {
    const baseObj = s.control || s.baseline;
    if (baseObj) Object.keys(baseObj).forEach(k => metricKeys.add(k))
    if (s.scenario) Object.keys(s.scenario).forEach(k => metricKeys.add(k))
  })
  
  const metricKeysArr = Array.from(metricKeys)

  // Header row
  const headers = [
    'id',
    'name',
    'timestamp',
    'schema_version',
    'comparison_type',
    'control_traffic_multiplier',
    'scenario_traffic_multiplier',
    'duration',
    'intervention_id',
    'intervention_name',
    'evaluation_mode',
    'metric_provenance',
    ...metricKeysArr.map(k => `control_${k}`),
    ...metricKeysArr.map(k => `scenario_${k}`),
    ...metricKeysArr.map(k => `delta_${k}`),
    ...metricKeysArr.map(k => `delta_pct_${k}`),
  ]

  const rows = scenarios.map(s => {
    const baseObj = s.control || s.baseline;
    const isV2 = s.schema_version >= 2;
    
    const row = [
      s.id,
      s.name,
      s.timestamp,
      s.schema_version || 1,
      isV2 ? 'control_vs_intervention' : 'normal_vs_scenario',
      isV2 ? s.traffic_multiplier : 1.0, // Control traffic multiplier
      s.traffic_multiplier,              // Scenario traffic multiplier
      s.duration,
      s.intervention_id || 'none',
      s.intervention_name || 'No Intervention',
      s.evaluation_mode || 'unknown',
      s.metric_provenance ? JSON.stringify(s.metric_provenance).replace(/,/g, ';') : 'unknown'
    ]

    metricKeysArr.forEach(k => row.push(baseObj?.[k] ?? ''))
    metricKeysArr.forEach(k => row.push(s.scenario?.[k] ?? ''))
    metricKeysArr.forEach(k => row.push(s.deltas?.[k]?.absolute ?? ''))
    metricKeysArr.forEach(k => row.push(s.deltas?.[k]?.percentage == null ? 'N/A' : s.deltas?.[k]?.percentage))

    return row.map(v => typeof v === 'string' && v.includes(',') ? `"${v}"` : v).join(',')
  })

  const csvContent = [headers.join(','), ...rows].join('\n')
  const dataUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent)
  triggerDownload(dataUri, `urbanmind-experiments-${Date.now()}.csv`)
}

function triggerDownload(dataUri, filename) {
  const exportFileDefaultName = filename
  const linkElement = document.createElement('a')
  linkElement.setAttribute('href', dataUri)
  linkElement.setAttribute('download', exportFileDefaultName)
  linkElement.click()
}

/**
 * Export a full ExperimentResult to a single JSON file.
 * Includes all conditions, metrics, deltas, provenance, and metadata.
 */
export function exportExperimentToJson(experiment) {
  if (!experiment) return
  const dataStr = JSON.stringify(experiment, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)
  triggerDownload(dataUri, `urbanmind-experiment-${experiment.experiment_id || Date.now()}.json`)
}

/**
 * Export a full ExperimentResult to CSV.
 * One row per condition. Columns: experiment metadata + condition + all control/scenario/delta metrics.
 */
export function exportExperimentToCsv(experiment) {
  if (!experiment || !experiment.conditions || experiment.conditions.length === 0) return

  const METRIC_KEYS = [
    'average_speed_kmh',
    'mean_completed_vehicle_time_loss_seconds',
    'mean_active_vehicle_time_loss_seconds',
    'average_waiting_seconds',
    'max_vehicle_count',
    'co2_kg',
    'nox_g',
    'noise_db',
    'pedestrian_delay_seconds',
    'accessibility_score'
  ]

  const headers = [
    'experiment_id',
    'schema_version',
    'experiment_name',
    'created_at',
    'duration',
    'traffic_levels',
    'condition_id',
    'traffic_multiplier',
    'intervention_id',
    'intervention_label',
    'evaluation_mode',
    'status',
    'error',
    ...METRIC_KEYS.map(k => `control_${k}`),
    ...METRIC_KEYS.map(k => `scenario_${k}`),
    ...METRIC_KEYS.map(k => `delta_${k}`),
    ...METRIC_KEYS.map(k => `delta_pct_${k}`),
  ]

  const rows = experiment.conditions.map(cond => {
    const row = [
      experiment.experiment_id,
      experiment.schema_version,
      experiment.name,
      experiment.created_at,
      experiment.duration,
      experiment.traffic_levels?.join(';'),
      cond.condition_id,
      cond.traffic_multiplier,
      cond.intervention_id || 'none',
      cond.intervention_label,
      cond.evaluation_mode,
      cond.status,
      cond.error || '',
    ]

    METRIC_KEYS.forEach(k => row.push(cond.control_metrics?.[k] ?? ''))
    METRIC_KEYS.forEach(k => row.push(cond.scenario_metrics?.[k] ?? ''))
    METRIC_KEYS.forEach(k => row.push(cond.metric_deltas?.[k]?.absolute ?? ''))
    METRIC_KEYS.forEach(k => {
      const pct = cond.metric_deltas?.[k]?.percentage
      row.push(pct == null ? 'N/A' : pct)
    })

    return row.map(v => {
      if (v == null) return ''
      const str = String(v)
      return str.includes(',') || str.includes('"') ? `"${str.replace(/"/g, '""')}"` : str
    }).join(',')
  })

  const csvContent = [headers.join(','), ...rows].join('\n')
  const dataUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent)
  triggerDownload(dataUri, `urbanmind-experiment-${experiment.experiment_id || Date.now()}.csv`)
}

/**
 * Export a DecisionReport object to JSON.
 */
export function exportDecisionReportToJson(report) {
  if (!report) return
  const dataStr = JSON.stringify(report, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)
  triggerDownload(dataUri, `urbanmind-decision-report-${report.report_id || Date.now()}.json`)
}

/**
 * Export a DecisionReport object to CSV via the backend exporter API or local CSV construction.
 */
export async function exportDecisionReportToCsv(report) {
  if (!report) return
  try {
    const res = await exportReportCsvApi({ report })
    if (res?.csv) {
      const dataUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(res.csv)
      triggerDownload(dataUri, res.filename || `urbanmind-decision-report-${report.report_id || Date.now()}.csv`)
      return
    }
  } catch (err) {
    console.warn('Backend CSV export failed, falling back to local exporter:', err)
  }

  // Local fallback CSV export
  const lines = [
    `URBANMIND DECISION REPORT,${report.report_id || ''}`,
    `Created At,${report.created_at || ''}`,
    `Scenario,${report.scenario_id || ''}`,
    `Policy,${(report.policy_id || '').toUpperCase()}`,
    '',
    'EXECUTIVE SUMMARY',
    `Recommended Intervention,"${report.executive_summary?.recommended_intervention || ''}"`,
    `Primary Impact,"${report.executive_summary?.primary_result || ''}"`,
    `Environmental Impact,"${report.executive_summary?.environmental_result || ''}"`,
    `Confidence,${report.executive_summary?.confidence || ''}`,
    `Recommendation,"${report.executive_summary?.recommendation || ''}"`,
    '',
    'METRIC COMPARISON',
    'Metric,Baseline,Optimized,Absolute Change,Percentage Change (%),Direction,Is Improvement,Provenance',
  ]

  report.metric_comparison?.forEach(r => {
    lines.push(`"${r.name_en}",${r.baseline},${r.optimized},${r.absolute_change},${r.percentage_change}%,${r.direction},${r.is_improvement ? 'YES' : 'NO'},${r.provenance}`)
  })

  const dataUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(lines.join('\n'))
  triggerDownload(dataUri, `urbanmind-decision-report-${report.report_id || Date.now()}.csv`)
}

/**
 * Export a DecisionReport as a printable PDF / clean formatted HTML window.
 */
export async function exportDecisionReportToPdf(report, language = 'en') {
  if (!report) return
  try {
    const res = await exportReportHtmlApi({ report, language })
    const htmlContent = res?.html
    if (htmlContent) {
      const printWindow = window.open('', '_blank')
      if (printWindow) {
        printWindow.document.open()
        printWindow.document.write(htmlContent)
        printWindow.document.close()
        printWindow.focus()
        setTimeout(() => {
          printWindow.print()
        }, 500)
        return
      }
      const dataUri = 'data:text/html;charset=utf-8,' + encodeURIComponent(htmlContent)
      triggerDownload(dataUri, res.filename || `urbanmind-decision-report-${report.report_id || Date.now()}.html`)
    }
  } catch (err) {
    console.error('Failed to export decision report PDF:', err)
  }
}
