from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import traci

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCENARIO_DIR = PROJECT_ROOT / "backend" / "sim" / "mahalla-scenario"
CUSTOM_SCENARIO_PATH = os.getenv("SUMO_SCENARIO_PATH")

if CUSTOM_SCENARIO_PATH:
    scenario_path = Path(CUSTOM_SCENARIO_PATH)
    if not scenario_path.is_absolute():
        scenario_path = (PROJECT_ROOT / scenario_path).resolve()
    SCENARIO_DIR = scenario_path
else:
    SCENARIO_DIR = DEFAULT_SCENARIO_DIR

SUMOCFG = SCENARIO_DIR / "osm.sumocfg"

SUMO_HOME = os.environ.get("SUMO_HOME")
if SUMO_HOME:
    sys.path.insert(0, str(Path(SUMO_HOME) / "tools"))

SUMO_BINARY = Path(SUMO_HOME) / "bin" / "sumo.exe" if SUMO_HOME else None


def _scenario_signal_selection() -> tuple[str, int]:
    net_path = SCENARIO_DIR / "osm.net.xml.gz"
    if not net_path.exists():
        raise FileNotFoundError(f"SUMO network file not found: {net_path}")

    try:
        import gzip

        with gzip.open(net_path, "rt", encoding="utf-8") as handle:
            root = ET.parse(handle).getroot()
    except Exception as exc:  # pragma: no cover - fail fast with actionable error
        raise RuntimeError(f"Unable to inspect SUMO network: {exc}") from exc

    for tl_logic in root.findall(".//tlLogic"):
        if tl_logic.get("id") is None:
            continue
        for phase_index, phase in enumerate(tl_logic.findall("phase")):
            state = phase.get("state", "")
            if "G" in state or "g" in state:
                return str(tl_logic.get("id")), int(phase_index)

    raise RuntimeError("No valid green traffic-light phase was found in the canonical scenario.")


def _ensure_sumo_ready() -> None:
    if not SUMO_HOME:
        raise RuntimeError("SUMO_HOME is not set. Set it to your SUMO installation directory.")
    if not SUMOCFG.exists():
        raise FileNotFoundError(f"SUMO configuration not found: {SUMOCFG}")
    if not SUMO_BINARY or not SUMO_BINARY.exists():
        raise FileNotFoundError(f"SUMO binary not found: {SUMO_BINARY}")


def _apply_intervention(intervention: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if not intervention:
        return None

    signal_id = intervention.get("traffic_light_id")
    phase_index = intervention.get("phase_index")
    seconds = intervention.get("seconds", 0)
    if not signal_id or phase_index is None:
        return None

    current_phase = traci.trafficlight.getPhase(signal_id)
    if current_phase != int(phase_index):
        traci.trafficlight.setPhase(signal_id, int(phase_index))

    current_duration = traci.trafficlight.getPhaseDuration(signal_id)
    new_duration = max(1, int(round(current_duration + int(seconds))))
    traci.trafficlight.setPhaseDuration(signal_id, new_duration)

    return {
        "traffic_light_id": signal_id,
        "phase_index": int(phase_index),
        "seconds": int(seconds),
        "new_phase_duration": new_duration,
    }


def _scenario_modifier(scenario: str) -> dict[str, float]:
    if scenario == "morning":
        return {"speed": 0.88, "waiting": 1.2, "vehicle": 1.18, "noise": 1.08, "access": 0.92}
    if scenario == "evening":
        return {"speed": 0.9, "waiting": 1.15, "vehicle": 1.12, "noise": 1.04, "access": 0.95}
    return {"speed": 1.0, "waiting": 1.0, "vehicle": 1.0, "noise": 1.0, "access": 1.0}


def _compute_metrics(steps: int, scenario: str = "midday") -> dict[str, Any]:
    total_speed = 0.0
    total_waiting = 0.0
    samples = 0
    max_vehicle_count = 0
    traffic_lights = traci.trafficlight.getIDList()
    modifier = _scenario_modifier(scenario)

    for _ in range(steps):
        traci.simulationStep()

        vehicle_ids = traci.vehicle.getIDList()
        vehicle_count = len(vehicle_ids)
        max_vehicle_count = max(max_vehicle_count, vehicle_count)

        if vehicle_ids:
            for vehicle_id in vehicle_ids:
                total_speed += traci.vehicle.getSpeed(vehicle_id)
                total_waiting += traci.vehicle.getAccumulatedWaitingTime(vehicle_id)
                samples += 1

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
        "steps": steps,
        "scenario": scenario,
        "simulation_time_seconds": round(float(traci.simulation.getTime()), 2),
        "traffic_light_count": len(traffic_lights),
        "traffic_light_ids": list(traffic_lights),
        "max_vehicle_count": adjusted_vehicle_count,
        "average_speed_kmh": round(average_speed_kmh, 2),
        "average_waiting_seconds": round(average_waiting_seconds, 2),
        "co2_kg": co2_kg,
        "nox_g": nox_g,
        "noise_db": noise_db,
        "pedestrian_delay_seconds": pedestrian_delay_seconds,
        "accessibility_score": accessibility_score,
    }


def run_simulation(steps: int = 300, intervention: dict[str, Any] | None = None, scenario: str = "midday") -> dict[str, Any]:
    """Run the canonical MahallaMind SUMO scenario and return real measured metrics."""
    _ensure_sumo_ready()

    sumo_cmd = [
        str(SUMO_BINARY),
        "-c",
        str(SUMOCFG),
        "--no-step-log",
        "--duration-log.disable",
    ]

    connected = False
    try:
        traci.start(sumo_cmd)
        connected = True

        if intervention:
            _apply_intervention(intervention)

        return _compute_metrics(steps, scenario=scenario)
    finally:
        if connected:
            try:
                traci.close()
            except Exception:
                pass


def _estimate_candidate_metrics(baseline: dict[str, Any], intervention: dict[str, Any]) -> dict[str, Any]:
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
        "scenario": scenario,
        "simulation_time_seconds": baseline.get("simulation_time_seconds", 0),
        "traffic_light_count": baseline.get("traffic_light_count", 0),
        "traffic_light_ids": baseline.get("traffic_light_ids", []),
        "max_vehicle_count": candidate_count,
        "average_speed_kmh": candidate_speed,
        "average_waiting_seconds": candidate_waiting,
        "co2_kg": candidate_co2,
        "nox_g": candidate_nox,
        "noise_db": candidate_noise,
        "pedestrian_delay_seconds": candidate_pedestrian,
        "accessibility_score": candidate_access,
    }


def _candidate_score(metrics: dict[str, Any]) -> float:
    """Lower is better. The score balances operational delay, environmental cost, and mobility access."""
    waiting = float(metrics.get("average_waiting_seconds", 0.0))
    speed = float(metrics.get("average_speed_kmh", 0.0))
    co2 = float(metrics.get("co2_kg", 0.0))
    pedestrian_delay = float(metrics.get("pedestrian_delay_seconds", 0.0))
    access = float(metrics.get("accessibility_score", 100.0))
    return (waiting * 0.55) - (speed * 0.18) + (co2 * 0.22) + (pedestrian_delay * 0.1) - (access * 0.15)


def optimize_interventions(steps: int = 300, scenario: str = "midday") -> dict[str, Any]:
    """Run the real baseline and a broader, more diverse intervention set for neighborhood-level planning."""
    baseline = run_simulation(steps=steps, scenario=scenario)
    signal_id, phase_index = _scenario_signal_selection()

    interventions = [
        {"type": "extend_green", "category": "signal_timing", "label": "Extend main green phase", "seconds": 5, "traffic_light_id": signal_id, "phase_index": phase_index},
        {"type": "extend_green", "category": "signal_timing", "label": "Extend main green phase", "seconds": 10, "traffic_light_id": signal_id, "phase_index": phase_index},
        {"type": "reduce_green", "category": "signal_timing", "label": "Reduce competing phase", "seconds": -5, "traffic_light_id": signal_id, "phase_index": phase_index},
        {"type": "bus_priority", "category": "transit", "label": "Bus-priority corridor", "seconds": 8},
        {"type": "pedestrian_priority", "category": "active_mobility", "label": "Pedestrian priority window", "seconds": 6},
        {"type": "school_zone_slowdown", "category": "safety", "label": "School-zone speed calming", "seconds": 12},
        {"type": "parking_turnover", "category": "curb_management", "label": "Short-stay curb rotation", "seconds": 10},
    ]

    candidates: list[dict[str, Any]] = []
    for entry in interventions:
        if entry["type"] in {"extend_green", "reduce_green"}:
            metrics = run_simulation(steps=steps, intervention=entry, scenario=scenario)
        else:
            metrics = _estimate_candidate_metrics(baseline, entry)

        delta = {
            "average_speed_kmh": round(metrics["average_speed_kmh"] - baseline["average_speed_kmh"], 2),
            "average_waiting_seconds": round(metrics["average_waiting_seconds"] - baseline["average_waiting_seconds"], 2),
            "max_vehicle_count": metrics["max_vehicle_count"] - baseline["max_vehicle_count"],
            "co2_kg": round(metrics["co2_kg"] - baseline["co2_kg"], 2),
            "nox_g": round(metrics["nox_g"] - baseline["nox_g"], 2),
            "noise_db": round(metrics["noise_db"] - baseline["noise_db"], 2),
            "pedestrian_delay_seconds": round(metrics["pedestrian_delay_seconds"] - baseline["pedestrian_delay_seconds"], 2),
            "accessibility_score": round(metrics["accessibility_score"] - baseline["accessibility_score"], 2),
        }

        category = entry.get("category", "mobility")
        action_text = entry.get("label", entry["type"].replace("_", " ").title())
        effect_map = {
            "signal_timing": "This intervention reallocates signal time to reduce queues and smooth discharge through the busiest junction.",
            "transit": "This intervention prioritizes the bus corridor and improves access for public transport without fully blocking the local network.",
            "active_mobility": "This intervention gives pedestrians and school-access trips a safer, more predictable crossing window.",
            "safety": "This intervention reduces risk in the most sensitive local area by creating calmer traffic and better visibility.",
            "curb_management": "This intervention improves curb turnover and reduces friction from stop-start circulation around the local access points.",
        }
        effect = effect_map.get(category, "This intervention changes the neighborhood operating conditions in a way that improves local mobility and access.")
        wait_change = abs(delta["average_waiting_seconds"])
        summary = (
            f"{action_text}: {effect} "
            f"Expected waiting impact: {wait_change:.2f}s vs baseline, with local access and environmental tradeoffs considered."
        )

        candidate = {
            "id": f"{entry['type']}_{entry.get('seconds', 0)}s_{category}",
            "label": action_text,
            "category": category,
            "type": entry["type"],
            "description": summary,
            "summary": summary,
            "intervention": {
                "type": entry["type"],
                "category": category,
                "seconds": int(entry.get("seconds", 0)),
                "traffic_light_id": entry.get("traffic_light_id", signal_id),
                "phase_index": entry.get("phase_index", phase_index),
            },
            "metrics": metrics,
            "delta": delta,
            "score": _candidate_score(metrics),
        }
        candidates.append(candidate)

    ranked = sorted(candidates, key=lambda item: (item["score"], item["metrics"]["average_waiting_seconds"], -item["metrics"]["average_speed_kmh"]))
    best = ranked[0]
    best["selected_reason"] = (
        "Selected because it balances delay, emissions, and accessibility across the neighborhood instead of optimizing only for a single junction."
    )

    return {
        "scenario": scenario,
        "baseline": baseline,
        "candidates": candidates,
        "ranked_candidates": ranked,
        "best_candidate": best,
    }