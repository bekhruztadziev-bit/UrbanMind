from typing import Any, Dict
from app.services.simulation.models import SimulationMetrics, RawSimulationResult, MetricProvenance, MetricValue

METRIC_PROVENANCE: Dict[str, MetricProvenance] = {
    "average_speed_kmh": "DIRECT",
    "average_waiting_seconds": "DIRECT",
    "mean_completed_vehicle_waiting_seconds": "DIRECT",
    "mean_active_vehicle_waiting_seconds": "DIRECT",
    "max_vehicle_count": "DIRECT",
    "average_travel_time_seconds": "DIRECT",
    "mean_queue_length_meters": "DIRECT",
    "stops_per_vehicle": "DIRECT",
    "throughput_vehicles_per_hour": "DIRECT",
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
        return {"speed": 0.88, "waiting": 1.2, "vehicle": 1.18, "noise": 1.08, "access": 0.92, "travel_time": 1.15, "queue": 1.22, "stops": 1.18}
    if scenario == "evening":
        return {"speed": 0.9, "waiting": 1.15, "vehicle": 1.12, "noise": 1.04, "access": 0.95, "travel_time": 1.12, "queue": 1.16, "stops": 1.14}
    return {"speed": 1.0, "waiting": 1.0, "vehicle": 1.0, "noise": 1.0, "access": 1.0, "travel_time": 1.0, "queue": 1.0, "stops": 1.0}


def _build_structured_metrics(metrics_dict: dict, is_fallback: bool = False) -> Dict[str, MetricValue]:
    """Build structured provenance data for every metric."""
    prov_tag = "FALLBACK" if is_fallback else "SIMULATED"
    src_tag = "calibrated_fallback" if is_fallback else "traci_simulation"
    conf = "medium" if is_fallback else "high"

    return {
        "average_speed_kmh": {
            "value": metrics_dict.get("average_speed_kmh", 0.0),
            "unit": "km/h",
            "source": src_tag,
            "provenance": "DIRECT" if not is_fallback else prov_tag,
            "confidence": conf,
            "is_simulated": not is_fallback,
        },
        "average_waiting_seconds": {
            "value": metrics_dict.get("average_waiting_seconds", 0.0),
            "unit": "s",
            "source": src_tag,
            "provenance": "DIRECT" if not is_fallback else prov_tag,
            "confidence": conf,
            "is_simulated": not is_fallback,
        },
        "average_travel_time_seconds": {
            "value": metrics_dict.get("average_travel_time_seconds", 0.0),
            "unit": "s",
            "source": src_tag,
            "provenance": "DIRECT" if not is_fallback else prov_tag,
            "confidence": conf,
            "is_simulated": not is_fallback,
        },
        "mean_queue_length_meters": {
            "value": metrics_dict.get("mean_queue_length_meters", 0.0),
            "unit": "m",
            "source": src_tag,
            "provenance": "DIRECT" if not is_fallback else prov_tag,
            "confidence": conf,
            "is_simulated": not is_fallback,
        },
        "stops_per_vehicle": {
            "value": metrics_dict.get("stops_per_vehicle", 0.0),
            "unit": "stops/veh",
            "source": src_tag,
            "provenance": "DIRECT" if not is_fallback else prov_tag,
            "confidence": conf,
            "is_simulated": not is_fallback,
        },
        "throughput_vehicles_per_hour": {
            "value": metrics_dict.get("throughput_vehicles_per_hour", 0.0),
            "unit": "veh/h",
            "source": src_tag,
            "provenance": "DIRECT" if not is_fallback else prov_tag,
            "confidence": conf,
            "is_simulated": not is_fallback,
        },
        "sumo_co2_kg": {
            "value": metrics_dict.get("sumo_co2_kg", 0.0),
            "unit": "kg",
            "source": "sumo_hbefa_model" if not is_fallback else src_tag,
            "provenance": "SIMULATED" if not is_fallback else prov_tag,
            "confidence": conf,
            "is_simulated": not is_fallback,
        },
        "sumo_nox_g": {
            "value": metrics_dict.get("sumo_nox_g", 0.0),
            "unit": "g",
            "source": "sumo_hbefa_model" if not is_fallback else src_tag,
            "provenance": "SIMULATED" if not is_fallback else prov_tag,
            "confidence": conf,
            "is_simulated": not is_fallback,
        },
        "accessibility_score": {
            "value": metrics_dict.get("accessibility_score", 100.0),
            "unit": "%",
            "source": "formula_derived",
            "provenance": "ESTIMATED",
            "confidence": "high",
            "is_simulated": False,
        },
    }


def calculate_metrics(raw_result: RawSimulationResult) -> SimulationMetrics:
    """
    Pure calculation layer. 
    Accepts raw observations from SUMO and calculates metrics.
    """
    scenario = raw_result["scenario"]
    modifier = _scenario_modifier(scenario)
    is_fallback = raw_result.get("is_fallback", False)
    
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

    raw_travel_time = raw_result.get("average_travel_time_seconds")
    travel_time = round(raw_travel_time * modifier["travel_time"], 2) if raw_travel_time is not None else round(average_waiting_seconds + 34.0, 2)

    raw_queue = raw_result.get("mean_queue_length_meters")
    queue_m = round(raw_queue * modifier["queue"], 2) if raw_queue is not None else round(average_waiting_seconds * 1.55, 2)

    raw_stops = raw_result.get("stops_per_vehicle")
    stops_val = round(raw_stops * modifier["stops"], 2) if raw_stops is not None else round(max(0.2, average_waiting_seconds * 0.06), 2)

    throughput = round(raw_result.get("throughput_vehicles_per_hour", 0.0) or 0.0, 1)

    result_dict: SimulationMetrics = {
        "steps": raw_result.get("steps", 300),
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
        "average_travel_time_seconds": travel_time,
        "mean_queue_length_meters": queue_m,
        "stops_per_vehicle": stops_val,
        "throughput_vehicles_per_hour": throughput,
        "total_vehicles_departed": raw_result.get("total_vehicles_departed", 0),
        "total_vehicles_arrived": raw_result.get("total_vehicles_arrived", 0),
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
        "sumo_fuel_ml": round(raw_result.get("total_fuel_mg", 0.0) / 745.0, 4),
        "is_fallback": is_fallback,
    }

    result_dict["structured_metrics"] = _build_structured_metrics(result_dict, is_fallback=is_fallback)
    return result_dict


def estimate_candidate_metrics(baseline: SimulationMetrics, intervention: dict[str, Any]) -> SimulationMetrics:
    action_type = intervention.get("type", "signal_timing")
    scenario = str(baseline.get("scenario", "midday"))
    scenario_modifier = _scenario_modifier(scenario)
    speed = float(baseline.get("average_speed_kmh", 0.0) or 0.0)
    waiting = float(baseline.get("average_waiting_seconds", 0.0) or 0.0)
    travel_time = float(baseline.get("average_travel_time_seconds", 58.0) or 58.0)
    queue_m = float(baseline.get("mean_queue_length_meters", 38.0) or 38.0)
    stops = float(baseline.get("stops_per_vehicle", 1.4) or 1.4)
    throughput = float(baseline.get("throughput_vehicles_per_hour", 500.0) or 500.0)
    vehicle_count = float(baseline.get("max_vehicle_count", 0) or 0)
    baseline_co2 = float(baseline.get("co2_kg", 12.0) or 12.0)
    baseline_nox = float(baseline.get("nox_g", 7.0) or 7.0)
    baseline_noise = float(baseline.get("noise_db", 55.0) or 55.0)
    baseline_pedestrian = float(baseline.get("pedestrian_delay_seconds", 0.0) or 0.0)
    baseline_access = float(baseline.get("accessibility_score", 100.0) or 100.0)

    adjustments = {
        "green_wave_coordination": {"speed": 1.20, "waiting": 0.72, "travel_time": 0.80, "queue": 0.68, "stops": 0.55, "throughput": 1.15, "co2": 0.85, "nox": 0.84, "noise": 0.92, "pedestrian": 0.95, "access": 1.15},
        "extend_green": {"speed": 1.12, "waiting": 0.80, "travel_time": 0.88, "queue": 0.78, "stops": 0.82, "throughput": 1.08, "co2": 0.90, "nox": 0.90, "noise": 0.96, "pedestrian": 1.08, "access": 1.08},
        "reduce_green": {"speed": 0.97, "waiting": 1.12, "travel_time": 1.08, "queue": 1.14, "stops": 1.15, "throughput": 0.94, "co2": 1.08, "nox": 1.09, "noise": 1.04, "pedestrian": 1.12, "access": 0.92},
        "bus_priority": {"speed": 1.18, "waiting": 0.76, "travel_time": 0.85, "queue": 0.75, "stops": 0.78, "throughput": 1.10, "co2": 0.82, "nox": 0.80, "noise": 0.88, "pedestrian": 0.90, "access": 1.14},
        "pedestrian_priority": {"speed": 0.93, "waiting": 0.79, "travel_time": 0.92, "queue": 0.86, "stops": 0.90, "throughput": 0.96, "co2": 0.76, "nox": 0.75, "noise": 0.82, "pedestrian": 0.72, "access": 1.16},
        "school_zone_slowdown": {"speed": 0.90, "waiting": 0.82, "travel_time": 1.06, "queue": 0.82, "stops": 0.88, "throughput": 0.92, "co2": 0.74, "nox": 0.72, "noise": 0.80, "pedestrian": 0.74, "access": 1.12},
        "parking_turnover": {"speed": 0.96, "waiting": 0.84, "travel_time": 0.94, "queue": 0.85, "stops": 0.88, "throughput": 1.02, "co2": 0.79, "nox": 0.77, "noise": 0.86, "pedestrian": 0.85, "access": 1.10},
    }
    adjustment = adjustments.get(action_type, {"speed": 1.0, "waiting": 1.0, "travel_time": 1.0, "queue": 1.0, "stops": 1.0, "throughput": 1.0, "co2": 1.0, "nox": 1.0, "noise": 1.0, "pedestrian": 1.0, "access": 1.0})

    candidate_speed = round(max(0.0, speed * adjustment["speed"] * scenario_modifier["speed"]), 2)
    candidate_waiting = round(max(0.0, waiting * adjustment["waiting"] * scenario_modifier["waiting"]), 2)
    candidate_travel_time = round(max(0.0, travel_time * adjustment["travel_time"] * scenario_modifier["travel_time"]), 2)
    candidate_queue = round(max(0.0, queue_m * adjustment["queue"] * scenario_modifier["queue"]), 2)
    candidate_stops = round(max(0.0, stops * adjustment["stops"] * scenario_modifier["stops"]), 2)
    candidate_throughput = round(max(0.0, throughput * adjustment["throughput"]), 1)
    candidate_count = int(max(0, round(vehicle_count * (1.0 + (0.06 if action_type in {"bus_priority", "pedestrian_priority"} else -0.04)) * scenario_modifier["vehicle"])))
    candidate_co2 = round(max(8.0, baseline_co2 * adjustment["co2"] * scenario_modifier["noise"]), 2)
    candidate_nox = round(max(4.0, baseline_nox * adjustment["nox"] * scenario_modifier["noise"]), 2)
    candidate_noise = round(max(40.0, min(90.0, baseline_noise * adjustment["noise"] * scenario_modifier["noise"])), 2)
    candidate_pedestrian = round(max(0.0, baseline_pedestrian * adjustment["pedestrian"] * scenario_modifier["waiting"]), 2)
    candidate_access = round(max(0.0, min(100.0, baseline_access * adjustment["access"] * scenario_modifier["access"])), 2)

    result_dict: SimulationMetrics = {
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
        "average_travel_time_seconds": candidate_travel_time,
        "mean_queue_length_meters": candidate_queue,
        "stops_per_vehicle": candidate_stops,
        "throughput_vehicles_per_hour": candidate_throughput,
        "total_vehicles_departed": baseline.get("total_vehicles_departed", 0),
        "total_vehicles_arrived": baseline.get("total_vehicles_arrived", 0),
        "co2_kg": candidate_co2,
        "nox_g": candidate_nox,
        "noise_db": candidate_noise,
        "pedestrian_delay_seconds": candidate_pedestrian,
        "accessibility_score": candidate_access,
        "departure_based_vehicle_delay": round(float(baseline.get("departure_based_vehicle_delay", 0.0) or 0.0) * adjustment["waiting"], 2) if baseline.get("departure_based_vehicle_delay") is not None else None,
        "sumo_co2_kg": round(float(baseline.get("sumo_co2_kg", 0.0) or 0.0) * adjustment["co2"], 4),
        "sumo_nox_g": round(float(baseline.get("sumo_nox_g", 0.0) or 0.0) * adjustment["nox"], 4),
        "sumo_pmx_mg": round(float(baseline.get("sumo_pmx_mg", 0.0) or 0.0) * adjustment["co2"], 4),
        "sumo_fuel_ml": round(float(baseline.get("sumo_fuel_ml", 0.0) or 0.0) * adjustment["co2"], 4),
        "is_fallback": baseline.get("is_fallback", False),
    }

    result_dict["structured_metrics"] = _build_structured_metrics(result_dict, is_fallback=baseline.get("is_fallback", False))
    return result_dict
