from typing import Any, Dict
from app.services.simulation.models import SimulationMetrics, RawSimulationResult, MetricProvenance

METRIC_PROVENANCE: Dict[str, MetricProvenance] = {
    "average_speed_kmh": "DIRECT",
    "average_waiting_seconds": "DIRECT",
    "mean_completed_vehicle_waiting_seconds": "DIRECT",
    "mean_active_vehicle_waiting_seconds": "DIRECT",
    "max_vehicle_count": "DIRECT",
    "co2_kg": "ESTIMATED",
    "nox_g": "ESTIMATED",
    "noise_db": "ESTIMATED",
    "pedestrian_delay_seconds": "ESTIMATED",
    "accessibility_score": "ESTIMATED",
    "departure_based_vehicle_delay": "DIRECT",
    # SUMO emission model outputs (from HBEFA via TraCI)
    "sumo_co2_kg": "SIMULATED",
    "sumo_nox_g": "SIMULATED",
    "sumo_pmx_mg": "SIMULATED",
    "sumo_fuel_ml": "SIMULATED",
}
def _scenario_modifier(scenario: str) -> dict[str, float]:
    if scenario == "morning":
        return {"speed": 0.88, "waiting": 1.2, "vehicle": 1.18, "noise": 1.08, "access": 0.92}
    if scenario == "evening":
        return {"speed": 0.9, "waiting": 1.15, "vehicle": 1.12, "noise": 1.04, "access": 0.95}
    return {"speed": 1.0, "waiting": 1.0, "vehicle": 1.0, "noise": 1.0, "access": 1.0}


def calculate_metrics(raw_result: RawSimulationResult) -> SimulationMetrics:
    """
    Pure calculation layer. 
    Accepts raw observations from SUMO and calculates metrics.
    
    DIRECT METRICS:
    - simulation_time_seconds
    - traffic_light_count
    - traffic_light_ids

    DERIVED METRICS:
    - average_speed_kmh
    - average_waiting_seconds
    - max_vehicle_count (adjusted by scenario)

    ESTIMATED/SYNTHETIC METRICS:
    - co2_kg
    - nox_g
    - noise_db
    - pedestrian_delay_seconds
    - accessibility_score
    """
    scenario = raw_result["scenario"]
    modifier = _scenario_modifier(scenario)
    
    total_speed = raw_result["total_speed"]
    total_waiting = raw_result["total_waiting"]
    samples = raw_result["samples"]
    max_vehicle_count = raw_result["max_vehicle_count"]

    average_speed_mps = total_speed / samples if samples else 0.0
    average_speed_kmh = average_speed_mps * 3.6 * modifier["speed"]
    average_waiting_seconds = (total_waiting / samples if samples else 0.0) * modifier["waiting"]
    adjusted_vehicle_count = int(round(max_vehicle_count * modifier["vehicle"]))
    
    co2_kg = round(max(12.5, adjusted_vehicle_count * 0.62 + average_waiting_seconds * 0.95), 2)
    nox_g = round(max(7.5, adjusted_vehicle_count * 0.31 + average_waiting_seconds * 0.48), 2)
    noise_db = round(min(90.0, 53.0 + max(0.0, 60.0 - average_speed_kmh) * 0.18 + average_waiting_seconds * 0.04) * modifier["noise"], 2)
    pedestrian_delay_seconds = round(max(0.0, average_waiting_seconds * 0.42 + adjusted_vehicle_count * 0.2), 2)
    accessibility_score = round(max(0.0, min(100.0, 100 - average_waiting_seconds * 0.55 - max(0.0, 60 - average_speed_kmh) * 0.38)) * modifier["access"], 2)

    return {
        "steps": raw_result.get("steps", raw_result.get("steps", 300)),
        "warmup_steps": raw_result.get("warmup_steps", 0),
        "measurement_steps": raw_result.get("measurement_steps", 0),
        "scenario": scenario,
        "simulation_time_seconds": round(raw_result["simulation_time_seconds"], 2),
        "traffic_light_count": raw_result["traffic_light_count"],
        "traffic_light_ids": raw_result["traffic_light_ids"],
        "max_vehicle_count": adjusted_vehicle_count,
        "average_speed_kmh": round(average_speed_kmh, 2),
        "average_waiting_seconds": round(average_waiting_seconds, 2),
        "mean_completed_vehicle_waiting_seconds": round(raw_result.get("mean_completed_vehicle_waiting_seconds") * modifier["waiting"], 2) if raw_result.get("mean_completed_vehicle_waiting_seconds") is not None else None,
        "completed_vehicle_count": raw_result.get("completed_vehicle_count", 0),
        "mean_active_vehicle_waiting_seconds": round(raw_result.get("mean_active_vehicle_waiting_seconds") * modifier["waiting"], 2) if raw_result.get("mean_active_vehicle_waiting_seconds") is not None else None,
        "active_vehicle_count": raw_result.get("active_vehicle_count", 0),
        "co2_kg": co2_kg,
        "nox_g": nox_g,
        "noise_db": noise_db,
        "pedestrian_delay_seconds": pedestrian_delay_seconds,
        "accessibility_score": accessibility_score,
        "departure_based_vehicle_delay": round(raw_result.get("departure_based_vehicle_delay", 0.0) or 0.0, 2) if raw_result.get("departure_based_vehicle_delay") is not None else None,
        # SUMO emission model outputs: mg → kg/g/ml
        "sumo_co2_kg": round(raw_result.get("total_co2_mg", 0.0) / 1_000_000.0, 4),
        "sumo_nox_g": round(raw_result.get("total_nox_mg", 0.0) / 1_000.0, 4),
        "sumo_pmx_mg": round(raw_result.get("total_pmx_mg", 0.0), 4),
        "sumo_fuel_ml": round(raw_result.get("total_fuel_mg", 0.0) / 745.0, 4),  # mg → ml (gasoline density ~745 mg/ml)
    }


def estimate_candidate_metrics(baseline: SimulationMetrics, intervention: dict[str, Any]) -> SimulationMetrics:
    action_type = intervention.get("type", "signal_timing")
    scenario = str(baseline.get("scenario", "midday"))
    scenario_modifier = _scenario_modifier(scenario)
    speed = float(baseline.get("average_speed_kmh", 0.0) or 0.0)
    waiting = float(baseline.get("average_waiting_seconds", 0.0) or 0.0)
    vehicle_count = float(baseline.get("max_vehicle_count", 0) or 0)
    baseline_co2 = float(baseline.get("co2_kg", 12.0) or 12.0)
    baseline_nox = float(baseline.get("nox_g", 7.0) or 7.0)
    baseline_noise = float(baseline.get("noise_db", 55.0) or 55.0)
    baseline_pedestrian = float(baseline.get("pedestrian_delay_seconds", 0.0) or 0.0)
    baseline_access = float(baseline.get("accessibility_score", 100.0) or 100.0)

    adjustments = {
        "extend_green": {"speed": 1.12, "waiting": 0.8, "co2": 0.9, "nox": 0.9, "noise": 0.96, "pedestrian": 1.08, "access": 1.08},
        "reduce_green": {"speed": 0.97, "waiting": 1.12, "co2": 1.08, "nox": 1.09, "noise": 1.04, "pedestrian": 1.12, "access": 0.92},
        "bus_priority": {"speed": 1.18, "waiting": 0.76, "co2": 0.82, "nox": 0.8, "noise": 0.88, "pedestrian": 0.9, "access": 1.14},
        "pedestrian_priority": {"speed": 0.93, "waiting": 0.79, "co2": 0.76, "nox": 0.75, "noise": 0.82, "pedestrian": 0.72, "access": 1.16},
        "school_zone_slowdown": {"speed": 0.9, "waiting": 0.82, "co2": 0.74, "nox": 0.72, "noise": 0.8, "pedestrian": 0.74, "access": 1.12},
        "parking_turnover": {"speed": 0.96, "waiting": 0.84, "co2": 0.79, "nox": 0.77, "noise": 0.86, "pedestrian": 0.85, "access": 1.1},
    }
    adjustment = adjustments.get(action_type, {"speed": 1.0, "waiting": 1.0, "co2": 1.0, "nox": 1.0, "noise": 1.0, "pedestrian": 1.0, "access": 1.0})

    candidate_speed = round(max(0.0, speed * adjustment["speed"] * scenario_modifier["speed"]), 2)
    candidate_waiting = round(max(0.0, waiting * adjustment["waiting"] * scenario_modifier["waiting"]), 2)
    candidate_count = int(max(0, round(vehicle_count * (1.0 + (0.06 if action_type in {"bus_priority", "pedestrian_priority"} else -0.04)) * scenario_modifier["vehicle"])))
    candidate_co2 = round(max(8.0, baseline_co2 * adjustment["co2"] * scenario_modifier["noise"]), 2)
    candidate_nox = round(max(4.0, baseline_nox * adjustment["nox"] * scenario_modifier["noise"]), 2)
    candidate_noise = round(max(40.0, min(90.0, baseline_noise * adjustment["noise"] * scenario_modifier["noise"])), 2)
    candidate_pedestrian = round(max(0.0, baseline_pedestrian * adjustment["pedestrian"] * scenario_modifier["waiting"]), 2)
    candidate_access = round(max(0.0, min(100.0, baseline_access * adjustment["access"] * scenario_modifier["access"])), 2)

    return {
        "steps": baseline.get("steps", 300),
        "warmup_steps": baseline.get("warmup_steps", 0),
        "measurement_steps": baseline.get("measurement_steps", 0),
        "scenario": scenario,
        "simulation_time_seconds": baseline.get("simulation_time_seconds", 0),
        "traffic_light_count": baseline.get("traffic_light_count", 0),
        "traffic_light_ids": baseline.get("traffic_light_ids", []),
        "max_vehicle_count": candidate_count,
        "average_speed_kmh": candidate_speed,
        "average_waiting_seconds": candidate_waiting,
        "mean_completed_vehicle_waiting_seconds": round(baseline.get("mean_completed_vehicle_waiting_seconds") * adjustment["waiting"] * scenario_modifier["waiting"], 2) if baseline.get("mean_completed_vehicle_waiting_seconds") is not None else None,
        "completed_vehicle_count": baseline.get("completed_vehicle_count", 0),
        "mean_active_vehicle_waiting_seconds": round(baseline.get("mean_active_vehicle_waiting_seconds") * adjustment["waiting"] * scenario_modifier["waiting"], 2) if baseline.get("mean_active_vehicle_waiting_seconds") is not None else None,
        "active_vehicle_count": baseline.get("active_vehicle_count", 0),
        "co2_kg": candidate_co2,
        "nox_g": candidate_nox,
        "noise_db": candidate_noise,
        "pedestrian_delay_seconds": candidate_pedestrian,
        "accessibility_score": candidate_access,
        "departure_based_vehicle_delay": round(float(baseline.get("departure_based_vehicle_delay", 0.0) or 0.0) * adjustment["waiting"], 2) if baseline.get("departure_based_vehicle_delay") is not None else None,
        # SUMO emission estimates for heuristic candidates: scale from baseline SUMO values
        "sumo_co2_kg": round(float(baseline.get("sumo_co2_kg", 0.0) or 0.0) * adjustment["co2"], 4),
        "sumo_nox_g": round(float(baseline.get("sumo_nox_g", 0.0) or 0.0) * adjustment["nox"], 4),
        "sumo_pmx_mg": round(float(baseline.get("sumo_pmx_mg", 0.0) or 0.0) * adjustment["co2"], 4),
        "sumo_fuel_ml": round(float(baseline.get("sumo_fuel_ml", 0.0) or 0.0) * adjustment["co2"], 4),
    }
