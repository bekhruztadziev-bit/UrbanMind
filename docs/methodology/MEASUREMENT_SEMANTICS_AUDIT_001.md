# UrbanMind Measurement Semantics Audit 001

## Executive Verdict
**VALID WITH CORRECTIONS**

The measurement framework successfully isolates vehicle cohorts and respects the warm-up boundary. However, the current terminology significantly misrepresents the underlying SUMO semantics, and the documentation contains methodological claims about "censoring" that are incorrect and must be revised.

## 1. SUMO time-loss semantics
The documentation claims the new metric uses `traci.vehicle.getTimeLoss()`, which represents true delay (actual travel time minus ideal free-flow travel time). 
However, the actual implementation uses `traci.vehicle.getAccumulatedWaitingTime()`. In SUMO, this explicitly measures **stopped time** (cumulative time spent moving slower than 0.1 m/s). It does *not* include time lost due to deceleration, acceleration, driving slowly behind other vehicles, or slowing down for traffic lights without fully stopping. 

## 2. Completed-vehicle metric definition
`mean_completed_vehicle_waiting_seconds` tracks the accumulated waiting time (stopped time) of vehicles that successfully arrive during the measurement window. 
Because it subtracts the wait time accumulated during the warm-up phase, it strictly measures the waiting time accumulated *during the measurement window* by vehicles that happened to finish their trip during the measurement window. It does not measure the full-trip wait time.

## 3. Active-vehicle metric definition
`mean_active_vehicle_waiting_seconds` measures the waiting time accumulated *during the measurement window* by all vehicles that are still active on the network at the exact final step of the measurement window. 
It does not include vehicles that departed and arrived entirely within the measurement window (they are in the completed cohort). It can be directly compared to the completed-vehicle metric, as both measure stopped time accumulated strictly during the measurement phase.

## 4. Legacy metric definition
`average_waiting_seconds` is a step-weighted aggregation. It sums the accumulated waiting time of *all active vehicles at every step*, divided by the total number of active vehicle-steps (samples). 
It is not a per-vehicle metric. It functions as a proxy for "average network queue density" or "average accumulated wait time of the current network population." It remains useful for real-time dashboard dials and legacy heuristic compatibility, but it is mathematically inappropriate for direct trip-delay comparisons.

## 5. Cohort and censoring analysis
The claim that the completed-vehicle metric "eliminates the censoring artifact" is false. By only measuring vehicles that successfully arrive, the metric introduces **survivorship bias**. In heavily saturated conditions (e.g., 1.4× demand), vehicles traversing major bottlenecks or traveling long distances become permanently stuck and never arrive. The completed cohort therefore becomes disproportionately composed of short, local trips that avoided the worst congestion. As a result, the completed-vehicle metric will systematically *understate* congestion at extreme demand levels.

## 6. Warm-up boundary analysis
The warm-up methodology correctly implements a "snapshot" framework (Design C). By tracking `start_wait` at the warm-up boundary, the measurement phase strictly records incremental waiting time. This means a vehicle's pre-warm-up state does not contaminate the measurement phase. While this breaks the definition of "total trip time," it is a highly defensible approach for evaluating the performance of the network specifically during the measurement snapshot.

## 7. Teleportation/incomplete-trip handling
SUMO teleports vehicles that are stuck for >300s. If a teleporting vehicle arrives at its destination during the measurement window, it will trigger `getArrivedIDList()` and be included in the completed cohort. However, `getAccumulatedWaitingTime()` ceases to increase while a vehicle is teleporting. Thus, teleported vehicles will artificially lower the mean waiting time of the completed cohort. 

## 8. Metric terminology recommendations
The current variable names are acceptable but slightly misleading in their documentation descriptions.
- `mean_completed_vehicle_waiting_seconds` should conceptually be understood as `mean_arrived_vehicle_window_waiting_seconds`.
- The frontend label "Completed-Trip Mean Delay" is factually incorrect because it measures stopped time, not true delay, and it only measures the portion of the trip that occurred within the window. 
- Recommended frontend label: "Completed-Trip Wait (Window)" or "Mean Arrived Wait".

## 9. Numerical diagnostic
A controlled 900-step (300 warm-up) simulation run yielded the following trend as demand increased from 1.0× to 1.4×:

- **1.0× Demand:** 
  - Completed Count: 270
  - Active Count: 93
  - Mean Completed Wait: 7.77 s
  - Mean Active Wait: 11.14 s
  - Legacy Average: 10.47 s
- **1.2× Demand:** 
  - Completed Count: 336
  - Active Count: 109
  - Mean Completed Wait: 7.98 s
  - Mean Active Wait: 10.55 s
  - Legacy Average: 10.51 s
- **1.4× Demand:** 
  - Completed Count: 379
  - Active Count: 132
  - Mean Completed Wait: 8.75 s
  - Mean Active Wait: 12.48 s
  - Legacy Average: 11.64 s

While throughput still largely scales linearly at 1.4× in this scenario, the completed-vehicle wait time remains persistently and structurally lower than the active-vehicle wait time. If demand is increased to a point of critical gridlock, the completed metric will plateau while the active metric diverges exponentially, confirming the survivorship bias.

## 10. Intervention-ranking sensitivity
Because the completed-vehicle metric truncates long tail delays at high demand, it artificially favors interventions that throughput a high volume of local traffic over interventions that resolve severe structural gridlock. 
- If using `average_waiting_seconds`, interventions are rewarded for reducing overall network queuing.
- If using `mean_completed_vehicle_waiting_seconds`, interventions are rewarded for ensuring short trips finish quickly, even if long trips are permanently sacrificed. 
These differing optimization targets mean the "best" intervention will frequently change depending on which metric is chosen, particularly when analyzing traffic-calming interventions that trade off local speed for overall flow.

## 11. Documentation claims that need correction
The following claims in `TRAFFIC_MEASUREMENT_METHODOLOGY.md` and `urbanmind_v3_measurement_validation_001.md` must be corrected:
- **"Calculated using `traci.vehicle.getTimeLoss`"**: False. It uses `getAccumulatedWaitingTime`.
- **"Eliminates the censoring artifact"**: False. It replaces step-weighted inflation with survivorship bias.
- **"Strict, mathematically correct measurement of trip delay"**: False. It measures window-bounded stopped time, not full-trip true delay.
- **"Actual experience of a commuter who completes their journey"**: False. It ignores the wait time they experienced during warm-up.

## 12. Recommended measurement framework
1. **Retain the two-phase (Design C) snapshot methodology.** It correctly evaluates the network's steady-state performance during the measurement window.
2. **Switch to `getTimeLoss()`** if the goal is to evaluate true delay (actual vs ideal travel time).
3. **Report both Arrived and Active cohorts together.** Neither metric provides a complete picture of extreme congestion on its own.
4. **Clarify UX labels** so users understand they are seeing "Stopped Time" (or "Time Loss") rather than "Total Trip Delay".
