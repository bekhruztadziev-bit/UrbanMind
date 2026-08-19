# Measurement Semantics Audit 002

## 1. Background
In Audit 001, we discovered that the canonical metrics previously referred to as "waiting time" were actually measuring **Time Loss** (`traci.vehicle.getTimeLoss()`). 

- `getTimeLoss()` measures the accumulated time lost relative to the maximum speed of the edge. It includes time spent decelerating, moving slowly due to congestion, and being fully stopped.
- `getAccumulatedWaitingTime()` measures strictly the time spent at velocity zero (or `< 0.1 m/s`).

## 2. Objective
This surgical correction task aimed to:
1. Rename the canonical fields in the codebase and data contracts to reflect their true semantic meaning (`time_loss_seconds`) rather than `waiting_seconds`.
2. Define the mutually exclusive and exhaustive measurement cohorts precisely (completed-trip vs. active-vehicle).
3. Document any remaining limitations, such as interval selection and right-censoring in the active cohort.
4. Guarantee numeric invariance, meaning no formulas or measurement calculations were altered; only the terminology was corrected.

## 3. Cohort Definitions
- **Completed-Trip Cohort**: Vehicles that complete their route within the measurement window (`traci.simulation.getArrivedIDList()`). Their time loss is an exact, uncensored measurement covering their entire journey.
- **Active-Vehicle Cohort**: Vehicles that are still on the network at the end of the measurement window. Their time loss is right-censored, representing accumulated loss up to the final simulation step.

## 4. Execution Summary
- **Backend Models**: `SimulationMetrics` fields updated to use `mean_completed_vehicle_time_loss_seconds` and `mean_active_vehicle_time_loss_seconds`. The old `_waiting_seconds` fields are preserved as deprecated aliases for backward compatibility.
- **Backend Tests**: Smoke tests (`test_sim_smoke.py`) were modified to strictly assert that the numerical results of the new canonical names are identical to the deprecated aliases.
- **Frontend Assets**: Component metadata, UI labels, and locale translations (`en.json`, `ru.json`) were updated to correctly present the metrics as "Time Loss" rather than generic "Wait".

## 5. Known Limitations
- The active-vehicle measurement remains right-censored, as it snapshot's a vehicle's accumulated time loss prior to its arrival. 
- While `average_waiting_seconds` (the step-weighted metric) uses `getAccumulatedWaitingTime()`, it serves as a legacy heuristic and continues to be labeled as "Step-weighted wait (legacy)".

## 6. Conclusion
The terminology is now semantically accurate and defensible. The numerical outcomes of the optimization pipeline remain unchanged, achieving the goal of this surgical correction.
