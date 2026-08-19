import React, { useMemo, useEffect, useRef } from 'react'
import { animateNumber } from '../../utils/motion'

function AnimatedNumber({ value, suffix = '', decimals = 0 }) {
  const ref = useRef(null)
  const prevValue = useRef(value)

  useEffect(() => {
    if (ref.current && value !== prevValue.current) {
      animateNumber(ref.current, prevValue.current, value, 600)
      prevValue.current = value
    } else if (ref.current && value === prevValue.current) {
      ref.current.textContent = value.toFixed(decimals)
    }
  }, [value, decimals])

  return (
    <strong style={{ display: 'inline-block' }}>
      <span ref={ref}>{value.toFixed(decimals)}</span>
      {suffix}
    </strong>
  )
}

export function MetricsGrid({ t, metrics, optResult }) {
  const liveVehicleCount = useMemo(() => {
    const peak = Number.isFinite(metrics.max_vehicle_count) ? metrics.max_vehicle_count : 0
    return peak ? Math.max(12, Math.round(peak * 0.7)) : 0
  }, [metrics.max_vehicle_count])

  const meanWait = metrics.mean_completed_vehicle_waiting_seconds ?? metrics.average_waiting_seconds ?? 0
  const co2 = metrics.sumo_co2_kg ?? metrics.co2_kg ?? 0
  const nox = metrics.sumo_nox_g ?? metrics.nox_g ?? 0
  const access = metrics.accessibility_score ?? 100

  const optWait = optResult?.baseline?.mean_completed_vehicle_waiting_seconds ?? optResult?.baseline?.average_waiting_seconds ?? meanWait
  const optSpeed = optResult?.baseline?.average_speed_kmh ?? metrics.average_speed_kmh
  const optPeak = optResult?.baseline?.max_vehicle_count ?? metrics.max_vehicle_count

  return (
    <>
      <div className="panel-card metric-grid">
        <div>
          <span>{t.avgSpeed}</span>
          <AnimatedNumber value={metrics.average_speed_kmh} suffix=" km/h" decimals={2} />
        </div>
        <div>
          <span>{t.waiting}</span>
          <AnimatedNumber value={meanWait} suffix=" s" decimals={2} />
        </div>
        <div>
          <span>
            CO₂
            {metrics.sumo_co2_kg !== undefined ? (
              <span className="provenance-badge simulated" title={t.simulatedLabel || 'SUMO simulation'}>SIMULATED</span>
            ) : (
              <span className="provenance-badge estimated" title={t.heuristicLabel || 'Heuristic estimate'}>ESTIMATED</span>
            )}
          </span>
          <AnimatedNumber value={co2} suffix=" kg" decimals={1} />
        </div>
        <div>
          <span>
            NOx
            {metrics.sumo_nox_g !== undefined ? (
              <span className="provenance-badge simulated" title={t.simulatedLabel || 'SUMO simulation'}>SIMULATED</span>
            ) : (
              <span className="provenance-badge estimated" title={t.heuristicLabel || 'Heuristic estimate'}>ESTIMATED</span>
            )}
          </span>
          <AnimatedNumber value={nox} suffix=" g" decimals={1} />
        </div>
        <div>
          <span>{t.liveFlow || 'Live flow'}</span>
          <AnimatedNumber value={liveVehicleCount} decimals={0} />
        </div>
        <div>
          <span>{t.peak || 'Peak'}</span>
          <AnimatedNumber value={metrics.max_vehicle_count} decimals={0} />
        </div>
        <div>
          <span>{t.signals || 'Signals'}</span>
          <AnimatedNumber value={metrics.traffic_light_count} decimals={0} />
        </div>
        <div>
          <span>{t.access || 'Access'}</span>
          <AnimatedNumber value={access} suffix="%" decimals={0} />
        </div>
      </div>

      <div className="panel-card baseline-card">
        <h3>{t.baseline}</h3>
        <div className="two-col">
          <div><span>{t.avgSpeed || 'Avg Speed'}</span><AnimatedNumber value={optSpeed} suffix=" km/h" decimals={2} /></div>
          <div><span>{t.timeLoss || t.waiting || 'Time loss'}</span><AnimatedNumber value={optWait} suffix=" s" decimals={2} /></div>
          <div><span>{t.liveFlow}</span><AnimatedNumber value={liveVehicleCount} decimals={0} /></div>
          <div><span>{t.peakVehicles}</span><AnimatedNumber value={optPeak} decimals={0} /></div>
        </div>
      </div>
    </>
  )
}
