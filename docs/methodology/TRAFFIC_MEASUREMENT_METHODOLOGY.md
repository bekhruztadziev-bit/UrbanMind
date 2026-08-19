# Traffic Measurement Methodology

This document outlines the UrbanMind v3 methodology for measuring and extracting traffic delay metrics from SUMO simulations.

## 1. Primary Metrics

UrbanMind tracks the following primary performance metrics during each simulation run:

- **Wait Time (Stopped Time)**: The total accumulated time a vehicle has spent moving slower than 0.1 m/s (effectively stopped). This does not include time lost to slowing down without stopping. Extracted using `traci.vehicle.getAccumulatedWaitingTime()`.
- **Average Speed**: The mean speed of vehicles in the network across all tracking steps.
- **Max Vehicle Count**: The peak number of vehicles concurrently present on the network during the measurement window.

## 2. Measurement Cohorts

Metrics are divided into two distinct, non-overlapping measurement cohorts:

### 2.1 Completed-Trip Cohort
- **Definition**: Vehicles that successfully reach their destination and arrive during the measurement window (`traci.simulation.getArrivedIDList()`).
- **Characteristics**: These measurements represent vehicles that have completed their journey. The extracted `waiting_seconds` represents the wait time experienced by the vehicle throughout its journey within the measurement window. However, this introduces **survivorship bias** at high congestion levels, as permanently stuck vehicles never arrive.
- **Canonical Field**: `mean_completed_vehicle_waiting_seconds`

### 2.2 Active-Vehicle Cohort
- **Definition**: Vehicles that remain on the network at the exact boundary when the measurement window concludes.
- **Characteristics**: These measurements are **right-censored**. The extracted `waiting_seconds` is a snapshot of the wait time accumulated up to the final simulation step. It does not account for the delay the vehicle might experience if the simulation continued. It is critical for capturing long-tail gridlock that prevents vehicles from arriving.
- **Canonical Field**: `mean_active_vehicle_waiting_seconds`

*(Note: Never sum the counts of these two cohorts to represent "total vehicles" as they are measured at different points in the lifecycle and represent fundamentally different sets. A vehicle cannot be in both cohorts simultaneously at the end boundary, but combining them does not represent a meaningful "total" due to the dynamic nature of spawn/arrival rates.)*

## 3. Heuristic / Legacy Metrics

- **Step-Weighted Wait (legacy)**: `average_waiting_seconds` is calculated using `traci.vehicle.getAccumulatedWaitingTime()` at every observation step, aggregating the strict stationary time (velocity `< 0.1m/s`). This remains as a legacy heuristic.

## 4. Warm-up Phase Handling

The simulation enforces a strict warm-up boundary.
- Vehicles arriving during the warm-up phase are **excluded** from the Completed-Trip cohort.
- Time loss accumulated during the warm-up phase is **subtracted** from vehicles that carry over into the measurement phase. This ensures that the Active-Vehicle and Completed-Trip cohorts only reflect delay incurred during the actual measurement window.
- This is achieved by snapshotting vehicle state at `step == warmup_steps`.

## 5. Architectural Constraints

- **Determinism**: The simulation must be perfectly deterministic. `run_diagnostics.py` and validation tests continuously verify that identical seeds and parameters produce identical time-loss values.
- **Numeric Invariance**: We use the exact output of `getAccumulatedWaitingTime()` to maintain the validity of prior heuristic analyses and interventions. Numerical invariance guarantees that historical benchmarks remain valid.
