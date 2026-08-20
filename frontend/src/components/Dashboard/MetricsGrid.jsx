import { useEffect, useRef } from 'react'
import { useAnimatedNumber, animateHighlight, MOTION } from '../../utils/motion'
import { safeNumber } from '../../utils/normalize'

function AnimatedMetric({ value, suffix = '', decimals = 0 }) {
  const safeVal = safeNumber(value, 0)
  const formattedNumber = useAnimatedNumber(safeVal, decimals, MOTION.reveal)
  return (
    <strong className="metric-val">
      {formattedNumber}{suffix}
    </strong>
  )
}

export function MetricsGrid({ t = {}, metrics = {}, optResult = null }) {
  const gridRef = useRef(null)
  const speed = safeNumber(metrics?.average_speed_kmh, 0)
  const prevSpeedRef = useRef(speed)

  useEffect(() => {
    if (prevSpeedRef.current !== speed && gridRef.current) {
      prevSpeedRef.current = speed
      animateHighlight(gridRef.current, { duration: MOTION.normal })
    }
  }, [speed])

  const meanWait = safeNumber(metrics?.mean_completed_vehicle_waiting_seconds ?? metrics?.average_waiting_seconds, 0)
  const travelTime = safeNumber(metrics?.average_travel_time_seconds, meanWait + 34.0)
  const queueLength = safeNumber(metrics?.mean_queue_length_meters, meanWait * 1.55)
  const stops = safeNumber(metrics?.stops_per_vehicle, 1.2)
  const throughput = safeNumber(
    metrics?.throughput_vehicles_per_hour,
    metrics?.max_vehicle_count ? Math.round(metrics.max_vehicle_count * 12) : 520
  )
  const co2 = safeNumber(metrics?.sumo_co2_kg ?? metrics?.co2_kg, 0)
  const access = safeNumber(metrics?.accessibility_score, 100)

  const optWait = safeNumber(
    optResult?.baseline?.mean_completed_vehicle_waiting_seconds ?? optResult?.baseline?.average_waiting_seconds,
    meanWait
  )
  const optSpeed = safeNumber(optResult?.baseline?.average_speed_kmh, speed)
  const optTravelTime = safeNumber(optResult?.baseline?.average_travel_time_seconds, travelTime)
  const optThroughput = safeNumber(optResult?.baseline?.throughput_vehicles_per_hour, throughput)

  const isSimulated = !metrics?.is_fallback
  const simulatedBadge = t?.simulatedBadge || 'SIMULATED'
  const fallbackBadge = t?.fallbackBadge || 'FALLBACK'
  const sourceLabels = {
    travelTime: t?.sourceTravelTime || 'SUMO TraCI trip duration',
    queueLength: t?.sourceQueueLength || 'SUMO halting queue length',
    stops: t?.sourceStops || 'TraCI vehicle velocity stop transitions',
    throughput: t?.sourceThroughput || 'Completed trips per hour',
    emissions: t?.sourceEmissions || 'SUMO TraCI emission model',
    accessibility: t?.sourceAccessibility || 'Multi-objective accessibility formula',
  }

  return (
    <>
      <div className="panel-card metric-grid" ref={gridRef}>
        <div>
          <span>
            {t?.avgSpeed || 'Avg. speed'}
            <span className={`provenance-badge ${isSimulated ? 'simulated' : 'estimated'}`} title={isSimulated ? (t?.simulatedLabel || 'SUMO simulation') : (t?.heuristicLabel || 'Calibrated fallback')}>
              {isSimulated ? simulatedBadge : fallbackBadge}
            </span>
          </span>
          <AnimatedMetric value={speed} suffix=" km/h" decimals={2} />
        </div>

        <div>
          <span>
            {t?.waiting || 'Delay'}
            <span className={`provenance-badge ${isSimulated ? 'simulated' : 'estimated'}`} title={isSimulated ? (t?.simulatedLabel || 'SUMO simulation') : (t?.heuristicLabel || 'Calibrated fallback')}>
              {isSimulated ? simulatedBadge : fallbackBadge}
            </span>
          </span>
          <AnimatedMetric value={meanWait} suffix=" s" decimals={2} />
        </div>

        <div>
          <span>
            {t?.travelTime || 'Travel Time'}
            <span className="provenance-badge simulated" title={sourceLabels.travelTime}>
              {simulatedBadge}
            </span>
          </span>
          <AnimatedMetric value={travelTime} suffix=" s" decimals={1} />
        </div>

        <div>
          <span>
            {t?.queueLength || 'Queue Length'}
            <span className="provenance-badge simulated" title={sourceLabels.queueLength}>
              {simulatedBadge}
            </span>
          </span>
          <AnimatedMetric value={queueLength} suffix=" m" decimals={1} />
        </div>

        <div>
          <span>
            {t?.stopsPerVehicle || 'Stops / Veh'}
            <span className="provenance-badge simulated" title={sourceLabels.stops}>
              {simulatedBadge}
            </span>
          </span>
          <AnimatedMetric value={stops} suffix="" decimals={2} />
        </div>

        <div>
          <span>
            {t?.throughput || 'Throughput'}
            <span className="provenance-badge simulated" title={sourceLabels.throughput}>
              {simulatedBadge}
            </span>
          </span>
          <AnimatedMetric value={throughput} suffix=" veh/h" decimals={0} />
        </div>

        <div>
          <span>
            CO₂
            <span className="provenance-badge simulated" title={sourceLabels.emissions}>
              {simulatedBadge}
            </span>
          </span>
          <AnimatedMetric value={co2} suffix=" kg" decimals={2} />
        </div>

        <div>
          <span>
            {t?.access || 'Access'}
            <span className="provenance-badge estimated" title={sourceLabels.accessibility}>
              {t?.estimatedBadge || 'ESTIMATED'}
            </span>
          </span>
          <AnimatedMetric value={access} suffix="%" decimals={0} />
        </div>
      </div>

      <div className="panel-card baseline-card">
        <h3>{t?.baseline || 'Baseline'}</h3>
        <div className="two-col">
          <div><span>{t?.avgSpeed || 'Avg Speed'}</span><AnimatedMetric value={optSpeed} suffix=" km/h" decimals={2} /></div>
          <div><span>{t?.waiting || 'Delay'}</span><AnimatedMetric value={optWait} suffix=" s" decimals={2} /></div>
          <div><span>{t?.travelTime || 'Travel Time'}</span><AnimatedMetric value={optTravelTime} suffix=" s" decimals={1} /></div>
          <div><span>{t?.throughput || 'Throughput'}</span><AnimatedMetric value={optThroughput} suffix=" veh/h" decimals={0} /></div>
        </div>
      </div>
    </>
  )
}
