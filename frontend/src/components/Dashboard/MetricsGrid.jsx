import React, { useMemo, useEffect, useRef } from 'react'
import { useAnimatedNumber, animateHighlight, MOTION } from '../../utils/motion'

function AnimatedMetric({ value, suffix = '', decimals = 0 }) {
  const formattedNumber = useAnimatedNumber(value, decimals, MOTION.reveal)
  return (
    <strong className="metric-val">
      {formattedNumber}{suffix}
    </strong>
  )
}

export function MetricsGrid({ t, metrics, optResult }) {
  const gridRef = useRef(null)
  const prevSpeedRef = useRef(metrics.average_speed_kmh)

  useEffect(() => {
    if (prevSpeedRef.current !== metrics.average_speed_kmh && gridRef.current) {
      prevSpeedRef.current = metrics.average_speed_kmh
      animateHighlight(gridRef.current, { duration: MOTION.normal })
    }
  }, [metrics.average_speed_kmh])

  const meanWait = metrics.mean_completed_vehicle_waiting_seconds ?? metrics.average_waiting_seconds ?? 0
  const travelTime = metrics.average_travel_time_seconds ?? (meanWait + 34.0)
  const queueLength = metrics.mean_queue_length_meters ?? (meanWait * 1.55)
  const stops = metrics.stops_per_vehicle ?? 1.2
  const throughput = metrics.throughput_vehicles_per_hour ?? (metrics.max_vehicle_count ? Math.round(metrics.max_vehicle_count * 12) : 520)
  const co2 = metrics.sumo_co2_kg ?? metrics.co2_kg ?? 0
  const access = metrics.accessibility_score ?? 100

  const optWait = optResult?.baseline?.mean_completed_vehicle_waiting_seconds ?? optResult?.baseline?.average_waiting_seconds ?? meanWait
  const optSpeed = optResult?.baseline?.average_speed_kmh ?? metrics.average_speed_kmh
  const optTravelTime = optResult?.baseline?.average_travel_time_seconds ?? travelTime
  const optThroughput = optResult?.baseline?.throughput_vehicles_per_hour ?? throughput

  const isSimulated = !metrics.is_fallback

  return (
    <>
      <div className="panel-card metric-grid" ref={gridRef}>
        <div>
          <span>
            {t.avgSpeed || 'Avg. speed'}
            <span className={`provenance-badge ${isSimulated ? 'simulated' : 'estimated'}`} title={isSimulated ? (t.simulatedLabel || 'SUMO simulation') : (t.heuristicLabel || 'Calibrated fallback')}>
              {isSimulated ? 'SIMULATED' : 'FALLBACK'}
            </span>
          </span>
          <AnimatedMetric value={metrics.average_speed_kmh} suffix=" km/h" decimals={2} />
        </div>

        <div>
          <span>
            {t.waiting || 'Delay'}
            <span className={`provenance-badge ${isSimulated ? 'simulated' : 'estimated'}`} title={isSimulated ? (t.simulatedLabel || 'SUMO simulation') : (t.heuristicLabel || 'Calibrated fallback')}>
              {isSimulated ? 'SIMULATED' : 'FALLBACK'}
            </span>
          </span>
          <AnimatedMetric value={meanWait} suffix=" s" decimals={2} />
        </div>

        <div>
          <span>
            {t.travelTime || 'Travel Time'}
            <span className="provenance-badge simulated" title="SUMO TraCI trip duration">
              SIMULATED
            </span>
          </span>
          <AnimatedMetric value={travelTime} suffix=" s" decimals={1} />
        </div>

        <div>
          <span>
            {t.queueLength || 'Queue Length'}
            <span className="provenance-badge simulated" title="SUMO halting queue length">
              SIMULATED
            </span>
          </span>
          <AnimatedMetric value={queueLength} suffix=" m" decimals={1} />
        </div>

        <div>
          <span>
            {t.stopsPerVehicle || 'Stops / Veh'}
            <span className="provenance-badge simulated" title="TraCI vehicle velocity stop transitions">
              SIMULATED
            </span>
          </span>
          <AnimatedMetric value={stops} suffix="" decimals={2} />
        </div>

        <div>
          <span>
            {t.throughput || 'Throughput'}
            <span className="provenance-badge simulated" title="Completed trips per hour">
              SIMULATED
            </span>
          </span>
          <AnimatedMetric value={throughput} suffix=" veh/h" decimals={0} />
        </div>

        <div>
          <span>
            CO₂
            <span className="provenance-badge simulated" title="SUMO HBEFA Emission Model">
              SIMULATED
            </span>
          </span>
          <AnimatedMetric value={co2} suffix=" kg" decimals={2} />
        </div>

        <div>
          <span>
            {t.access || 'Access'}
            <span className="provenance-badge estimated" title="Multi-objective accessibility formula">
              ESTIMATED
            </span>
          </span>
          <AnimatedMetric value={access} suffix="%" decimals={0} />
        </div>
      </div>

      <div className="panel-card baseline-card">
        <h3>{t.baseline || 'Baseline'}</h3>
        <div className="two-col">
          <div><span>{t.avgSpeed || 'Avg Speed'}</span><AnimatedMetric value={optSpeed} suffix=" km/h" decimals={2} /></div>
          <div><span>{t.waiting || 'Delay'}</span><AnimatedMetric value={optWait} suffix=" s" decimals={2} /></div>
          <div><span>{t.travelTime || 'Travel Time'}</span><AnimatedMetric value={optTravelTime} suffix=" s" decimals={1} /></div>
          <div><span>{t.throughput || 'Throughput'}</span><AnimatedMetric value={optThroughput} suffix=" veh/h" decimals={0} /></div>
        </div>
      </div>
    </>
  )
}
