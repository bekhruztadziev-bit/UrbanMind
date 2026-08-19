import os
import sys
import threading
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Tuple

import traci

from app.services.simulation.models import SimulationRequest, RawSimulationResult

PROJECT_ROOT = Path(__file__).resolve().parents[4]
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

# Global lock to ensure only one TraCI instance runs at a time
# This addresses the global TraCI coupling and blocking simulation calls.
_traci_lock = threading.Lock()


def _scenario_signal_selection() -> Tuple[str, int]:
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

    intervention_type = intervention.get("type")

    if intervention_type in ["extend_green", "reduce_green"]:
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
            "type": intervention_type,
            "traffic_light_id": signal_id,
            "phase_index": int(phase_index),
            "seconds": int(seconds),
            "new_phase_duration": new_duration,
        }
        
    elif intervention_type == "school_zone_slowdown":
        speed_limit_mps = float(intervention.get("speed_limit_mps", 5.5))
        # Apply traffic calming to typical residential lanes (speed between ~20 and 50 km/h)
        applied_lanes = 0
        for lane_id in traci.lane.getIDList():
            current_speed = traci.lane.getMaxSpeed(lane_id)
            # 6.0 m/s is ~21 km/h, 14.0 m/s is ~50.4 km/h
            if 6.0 <= current_speed <= 14.0:
                traci.lane.setMaxSpeed(lane_id, speed_limit_mps)
                applied_lanes += 1
                
        return {
            "type": intervention_type,
            "speed_limit_mps": speed_limit_mps,
            "applied_lanes_count": applied_lanes
        }

    return None


def run_simulation(request: SimulationRequest) -> RawSimulationResult:
    """Run the canonical MahallaMind SUMO scenario and return pure raw observations."""
    _ensure_sumo_ready()

    # Determine steps based on backwards-compatibility or explicit params
    req_steps = request.get("steps", 300)
    warmup_steps = request.get("warmup_steps", 0)
    
    # If warmup_steps and measurement_steps are explicitly provided, use them.
    # Otherwise, fallback to the legacy `steps` as the entire measurement window
    # with 0 warm-up (preserves exact previous behavior by default).
    if "measurement_steps" in request:
        measurement_steps = request["measurement_steps"]
        total_steps = warmup_steps + measurement_steps
    else:
        measurement_steps = req_steps
        total_steps = warmup_steps + measurement_steps

    scenario = request.get("scenario", "midday")
    intervention = request.get("intervention")

    traffic_multiplier = request.get("traffic_multiplier", 1.0)

    sumo_cmd = [
        str(SUMO_BINARY),
        "-c",
        str(SUMOCFG),
        "--no-step-log",
        "--duration-log.disable",
    ]
    if traffic_multiplier != 1.0:
        sumo_cmd.extend(["--scale", str(traffic_multiplier)])
    if "seed" in request:
        sumo_cmd.extend(["--seed", str(request["seed"])])

    with _traci_lock:
        connected = False
        try:
            traci.start(sumo_cmd)
            connected = True

            if intervention:
                _apply_intervention(intervention)
                
            active_vehicles_start_wait = {}
            active_vehicles_last_wait = {}

            # --- Warm-up phase ---
            for _ in range(warmup_steps):
                traci.simulationStep()
                # Update last wait so we can capture it at exactly the boundary
                # even for vehicles that might depart exactly at the boundary.
                for vehicle_id in traci.vehicle.getIDList():
                    active_vehicles_last_wait[vehicle_id] = traci.vehicle.getAccumulatedWaitingTime(vehicle_id)

            # Capture state at boundary
            for vehicle_id in traci.vehicle.getIDList():
                active_vehicles_start_wait[vehicle_id] = traci.vehicle.getAccumulatedWaitingTime(vehicle_id)

            total_speed = 0.0
            total_waiting = 0.0
            samples = 0
            max_vehicle_count = 0
            traffic_lights = traci.trafficlight.getIDList()
            
            completed_vehicles_wait = []

            # SUMO emission accumulators (mg, accumulated across measurement steps)
            total_co2_mg = 0.0
            total_nox_mg = 0.0
            total_pmx_mg = 0.0
            total_fuel_mg = 0.0
            # --- Measurement phase ---
            for _ in range(measurement_steps):
                traci.simulationStep()

                # Process arrived vehicles (completed trips)
                # getArrivedIDList returns vehicles that arrived *in the last step*
                for vehicle_id in traci.simulation.getArrivedIDList():
                    if vehicle_id in active_vehicles_last_wait:
                        total_delay = active_vehicles_last_wait[vehicle_id]
                        start_delay = active_vehicles_start_wait.get(vehicle_id, 0.0)
                        completed_vehicles_wait.append(total_delay - start_delay)

                vehicle_ids = traci.vehicle.getIDList()
                vehicle_count = len(vehicle_ids)
                max_vehicle_count = max(max_vehicle_count, vehicle_count)
                
                # Reset last_wait dictionary for this step
                active_vehicles_last_wait = {}

                if vehicle_ids:
                    for vehicle_id in vehicle_ids:
                        speed = traci.vehicle.getSpeed(vehicle_id)
                        wt = traci.vehicle.getAccumulatedWaitingTime(vehicle_id)
                        
                        total_speed += speed
                        total_waiting += wt
                        samples += 1
                        
                        active_vehicles_last_wait[vehicle_id] = wt

                        # Collect SUMO emission model outputs (mg/s → mg per step)
                        # TraCI returns mg/s; with default step length 1.0s, value = mg/step
                        try:
                            total_co2_mg += traci.vehicle.getCO2Emission(vehicle_id)
                            total_nox_mg += traci.vehicle.getNOxEmission(vehicle_id)
                            total_pmx_mg += traci.vehicle.getPMxEmission(vehicle_id)
                            total_fuel_mg += traci.vehicle.getFuelConsumption(vehicle_id)
                        except Exception:
                            pass  # Graceful — some vehicle types may not support emissions
                        
            # Determine censored/active vehicle delay
            active_vehicles_wait = []
            for vehicle_id, wt in active_vehicles_last_wait.items():
                start_wait = active_vehicles_start_wait.get(vehicle_id, 0.0)
                active_vehicles_wait.append(wt - start_wait)
                        
            departure_based_vehicle_delay = None
            if active_vehicles_last_wait:
                # Retain the exact original behavior for this legacy per-vehicle tracker
                # (which was added before this refactor, just calculating mean wait at the very last step)
                departure_based_vehicle_delay = sum(active_vehicles_last_wait.values()) / len(active_vehicles_last_wait)

            mean_completed = None
            if completed_vehicles_wait:
                mean_completed = sum(completed_vehicles_wait) / len(completed_vehicles_wait)
                
            mean_active = None
            if active_vehicles_wait:
                mean_active = sum(active_vehicles_wait) / len(active_vehicles_wait)

            return {
                "steps": total_steps,
                "warmup_steps": warmup_steps,
                "measurement_steps": measurement_steps,
                "scenario": scenario,
                "simulation_time_seconds": float(traci.simulation.getTime()),
                "traffic_light_count": len(traffic_lights),
                "traffic_light_ids": list(traffic_lights),
                "total_speed": total_speed,
                "total_waiting": total_waiting,
                "samples": samples,
                "max_vehicle_count": max_vehicle_count,
                "mean_completed_vehicle_waiting_seconds": mean_completed,
                "completed_vehicle_count": len(completed_vehicles_wait),
                "mean_active_vehicle_waiting_seconds": mean_active,
                "active_vehicle_count": len(active_vehicles_last_wait),
                "departure_based_vehicle_delay": departure_based_vehicle_delay,
                "total_co2_mg": total_co2_mg,
                "total_nox_mg": total_nox_mg,
                "total_pmx_mg": total_pmx_mg,
                "total_fuel_mg": total_fuel_mg,
            }
        finally:
            if connected:
                try:
                    traci.close()
                except Exception:
                    pass
