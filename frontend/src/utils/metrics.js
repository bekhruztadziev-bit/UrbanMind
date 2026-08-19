export const METRIC_METADATA = {
  average_speed_kmh: {
    id: 'average_speed_kmh',
    labelKey: 'avgSpeed',
    direction: 'higher', // higher is better
    unit: 'km/h',
    provenance: 'DIRECT',
    description: 'Average network speed'
  },
  mean_completed_vehicle_time_loss_seconds: {
    id: 'mean_completed_vehicle_time_loss_seconds',
    labelKey: 'timeLossCompleted',
    direction: 'lower',
    unit: 's',
    provenance: 'DIRECT',
    description: 'Mean time loss among vehicles in the completed-trip cohort.'
  },
  mean_active_vehicle_time_loss_seconds: {
    id: 'mean_active_vehicle_time_loss_seconds',
    labelKey: 'timeLossActive',
    direction: 'lower',
    unit: 's',
    provenance: 'DIRECT',
    description: 'Mean accumulated time loss among vehicles in the active-vehicle cohort at the measurement boundary.'
  },
  average_waiting_seconds: {
    id: 'average_waiting_seconds',
    labelKey: 'waitingLegacy',
    direction: 'lower',
    unit: 's',
    provenance: 'DIRECT',
    description: 'Step-weighted waiting indicator.'
  },
  max_vehicle_count: {
    id: 'max_vehicle_count',
    labelKey: 'peakVehicles',
    direction: 'lower',
    unit: 'veh',
    provenance: 'DIRECT',
    description: 'Maximum vehicle count observed.'
  },
  co2_kg: {
    id: 'co2_kg',
    labelKey: 'co2',
    direction: 'lower',
    unit: 'kg',
    provenance: 'ESTIMATED',
    description: 'Estimated CO2 emissions.'
  },
  nox_g: {
    id: 'nox_g',
    labelKey: 'nox',
    direction: 'lower',
    unit: 'g',
    provenance: 'ESTIMATED',
    description: 'Estimated NOx emissions.'
  },
  noise_db: {
    id: 'noise_db',
    labelKey: 'noise',
    direction: 'lower',
    unit: 'dB',
    provenance: 'ESTIMATED',
    description: 'Estimated noise level.'
  },
  pedestrian_delay_s: {
    id: 'pedestrian_delay_s',
    labelKey: 'pedestrianDelay',
    direction: 'lower',
    unit: 's',
    provenance: 'ESTIMATED',
    description: 'Estimated pedestrian delay.'
  },
  accessibility_score: {
    id: 'accessibility_score',
    labelKey: 'accessibility',
    direction: 'higher',
    unit: '/ 100',
    provenance: 'ESTIMATED',
    description: 'Estimated accessibility score.'
  },
}

export function isMetricGood(key, deltaValue) {
  const meta = METRIC_METADATA[key]
  if (!meta || deltaValue === 0 || deltaValue === undefined) return null

  if (meta.direction === 'higher') {
    return deltaValue > 0
  } else {
    return deltaValue < 0
  }
}
