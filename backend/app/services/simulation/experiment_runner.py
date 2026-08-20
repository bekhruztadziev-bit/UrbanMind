"""
Experiment Runner — Multi-Scenario Experiment Orchestrator
==========================================================
Generates the Cartesian product of (traffic_levels × interventions),
runs each condition as a same-demand control vs intervention comparison,
and returns a structured ExperimentResult.

Key design decisions:
- Control simulations are computed ONCE per (traffic_multiplier, duration) and cached
  in an in-memory dict for the duration of a single experiment run.
- No duplicate simulation logic: reuses session.py and metrics.py exclusively.
- Partial failure is explicit: each ExperimentCondition carries its own status.
- HEURISTIC interventions are labeled as such and never implied to be SUMO-run.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.services.simulation.interventions import get_candidate_interventions, INTERVENTION_LABELS_RU, INTERVENTION_CATEGORIES_RU
from app.services.simulation.metrics import METRIC_PROVENANCE, calculate_metrics
from app.services.simulation.models import (
    ExperimentCondition,
    ExperimentMetadata,
    ExperimentRequest,
    ExperimentResult,
    ExperimentSummary,
    SimulationMetrics,
)
from app.services.simulation.session import _scenario_signal_selection, run_simulation
from app.services.simulation.statistics import compute_sample_statistics

# Metrics compared in every condition delta
_DELTA_METRICS = [
    "average_speed_kmh",
    "average_waiting_seconds",
    "average_travel_time_seconds",
    "mean_queue_length_meters",
    "stops_per_vehicle",
    "throughput_vehicles_per_hour",
    "mean_completed_vehicle_waiting_seconds",
    "mean_active_vehicle_waiting_seconds",
    "max_vehicle_count",
    "co2_kg",
    "nox_g",
    "noise_db",
    "pedestrian_delay_seconds",
    "accessibility_score",
]

# Maximum allowed number of conditions to prevent runaway workloads
MAX_CONDITIONS = 50

# Robustness "effective" criterion — must be documented for transparency
EFFECTIVE_CRITERION = (
    "An intervention is 'effective' in a demand condition if its delta for "
    "average_waiting_seconds is negative (waiting time is reduced vs control)."
)


def compute_statistical_summary(metrics_list: List[SimulationMetrics]) -> Dict[str, Dict[str, Any]]:
    """
    Compute mean, std_dev, min, max, and 95% confidence interval across multiple seed runs.
    """
    if not metrics_list:
        return {}

    numeric_keys = [
        "average_speed_kmh", "average_waiting_seconds", "average_travel_time_seconds",
        "mean_queue_length_meters", "stops_per_vehicle", "throughput_vehicles_per_hour",
        "co2_kg", "nox_g", "accessibility_score", "max_vehicle_count"
    ]

    stats: Dict[str, Dict[str, Any]] = {}

    for key in numeric_keys:
        values = [float(m.get(key, 0.0) or 0.0) for m in metrics_list if m.get(key) is not None]
        if not values:
            continue

        stats[key] = compute_sample_statistics(values, allow_negative_ci=True)

    return stats


def _build_intervention_map(signal_id: str, phase_index: int) -> Dict[str, dict]:
    """Return a dict of {intervention_id: intervention_def} from the canonical registry."""
    candidates = get_candidate_interventions(signal_id, phase_index)
    result = {}
    for cand in candidates:
        cid = f"{cand.get('type')}_{cand.get('seconds', 0)}s_{cand.get('category')}"
        result[cid] = cand
    return result


def _compute_deltas(control: SimulationMetrics, scenario: SimulationMetrics) -> dict:
    """Compute absolute and percentage deltas between control and scenario metrics."""
    deltas = {}
    for key in _DELTA_METRICS:
        base_val = float(control.get(key, 0.0) or 0.0)
        scen_val = float(scenario.get(key, 0.0) or 0.0)
        absolute = round(scen_val - base_val, 4)
        percentage = round((absolute / base_val * 100), 2) if base_val else None
        deltas[key] = {"absolute": absolute, "percentage": percentage}
    return deltas


def _run_control(traffic_multiplier: float, duration: int, warmup_steps: int = 0, measurement_steps: int = 0, scenario: str = "midday") -> SimulationMetrics:
    """Run a control simulation (no intervention) at the given demand level."""
    raw = run_simulation({
        "steps": duration,
        "warmup_steps": warmup_steps,
        "measurement_steps": measurement_steps or duration,
        "scenario": scenario,
        "intervention": None,
        "traffic_multiplier": traffic_multiplier,
    })
    return calculate_metrics(raw)


def _run_scenario_condition(
    traffic_multiplier: float,
    duration: int,
    intervention_def: dict,
    control_metrics: SimulationMetrics,
    warmup_steps: int = 0,
    measurement_steps: int = 0,
    scenario: str = "midday",
) -> SimulationMetrics:
    """Run one concrete SUMO condition for a registered intervention."""
    raw = run_simulation({
        "steps": duration,
        "warmup_steps": warmup_steps,
        "measurement_steps": measurement_steps or duration,
        "scenario": scenario,
        "intervention": intervention_def,
        "traffic_multiplier": traffic_multiplier,
    })
    return calculate_metrics(raw)


def run_experiment(request: ExperimentRequest) -> ExperimentResult:
    """
    Main experiment orchestration entry point.

    For each (traffic_level × intervention):
      1. Run the control simulation once per demand level (cached).
      2. Run or estimate the scenario.
      3. Compute deltas.
      4. Store the ExperimentCondition.

    Partial failures are caught per-condition; the experiment continues.
    """
    name = str(request.get("name", "Unnamed Experiment") or "Unnamed Experiment").strip()
    traffic_levels: List[float] = list(request.get("traffic_levels", [1.0]))
    intervention_ids: List[str] = list(request.get("intervention_ids", []))
    duration: int = int(request.get("duration", 300))
    warmup_steps: int = int(request.get("warmup_steps", 0))
    measurement_steps: int = int(request.get("measurement_steps", duration))
    
    # If warmup_steps and measurement_steps are explicitly supplied via new UI, they take precedence.
    # We update duration if necessary.
    if "warmup_steps" in request or "measurement_steps" in request:
        duration = warmup_steps + measurement_steps

    simulation_profile: Optional[str] = request.get("simulation_profile")
    scenario: str = "midday"

    # Validation
    if not traffic_levels:
        raise ValueError("At least one traffic level is required.")
    if duration <= 0 or duration > 10000:
        raise ValueError(f"Invalid duration: {duration}. Must be 1–10000.")
    for tl in traffic_levels:
        if tl <= 0.0 or tl > 10.0:
            raise ValueError(f"Invalid traffic level: {tl}. Must be 0.01–10.0.")
    total_conditions = len(traffic_levels) * max(len(intervention_ids), 1)
    if total_conditions > MAX_CONDITIONS:
        raise ValueError(
            f"Experiment would generate {total_conditions} conditions "
            f"(max {MAX_CONDITIONS}). Reduce traffic levels or interventions."
        )

    # Resolve intervention registry
    try:
        signal_id, phase_index = _scenario_signal_selection()
    except Exception as exc:
        raise RuntimeError(f"Cannot load SUMO network for intervention registry: {exc}") from exc

    intervention_map = _build_intervention_map(signal_id, phase_index)

    # Legacy ID compatibility map
    legacy_aliases = {
        "tc_20kmh": "school_zone_slowdown_0s_safety",
        "signal_p5": "extend_green_5s_signal_timing",
        "signal_p10": "extend_green_10s_signal_timing",
        "signal_m5": "reduce_green_-5s_signal_timing",
        "bus_p8": "bus_priority_8s_transit",
        "ped_p6": "pedestrian_priority_6s_active_mobility",
        "park_t10": "parking_turnover_10s_curb_management",
        "green_wave": "green_wave_coordination_0s_signal_timing",
    }

    # Resolve requested intervention defs (validate IDs)
    requested_interventions: List[Tuple[str, dict]] = []
    for raw_iid in intervention_ids:
        iid = legacy_aliases.get(raw_iid, raw_iid)
        if iid not in intervention_map:
            raise ValueError(f"Unknown intervention_id: '{raw_iid}'. "
                             f"Valid IDs: {sorted(intervention_map.keys())}")
        requested_interventions.append((iid, intervention_map[iid]))

    # If no interventions requested, run baseline-only conditions
    if not requested_interventions:
        requested_interventions = []  # conditions will just be control comparisons

    experiment_id = str(uuid.uuid4())[:8].upper()
    created_at = datetime.now(timezone.utc).isoformat()

    # In-memory control cache: (traffic_multiplier, duration) → SimulationMetrics
    control_cache: Dict[Tuple[float, int], SimulationMetrics] = {}

    conditions: List[ExperimentCondition] = []
    completed = 0
    failed = 0
    skipped = 0

    # Generate Cartesian product: traffic_levels × interventions
    for traffic_multiplier in traffic_levels:
        # --- Control simulation (cached per demand level) ---
        cache_key = (traffic_multiplier, duration)
        if cache_key not in control_cache:
            try:
                control_cache[cache_key] = _run_control(traffic_multiplier, duration, warmup_steps, measurement_steps, scenario)
            except Exception as exc:
                # If control fails, all conditions at this level must be skipped
                for iid, idef in (requested_interventions or [("none", None)]):
                    cond_id = f"{experiment_id}_{traffic_multiplier:.1f}x_{iid}"
                    conditions.append({
                        "condition_id": cond_id,
                        "traffic_multiplier": traffic_multiplier,
                        "intervention_id": iid if iid != "none" else None,
                        "intervention_label": idef.get("label", "Control") if idef else "Control",
                        "evaluation_mode": "SKIPPED",
                        "control_metrics": None,
                        "scenario_metrics": None,
                        "metric_deltas": None,
                        "metric_provenance": METRIC_PROVENANCE,
                        "status": "SKIPPED",
                        "error": f"Control simulation failed: {exc}",
                    })
                    skipped += 1
                continue

        control_metrics = control_cache[cache_key]

        # --- Per-intervention conditions ---
        iter_interventions = requested_interventions if requested_interventions else []

        for iid, idef in iter_interventions:
            cond_id = f"{experiment_id}_{traffic_multiplier:.1f}x_{iid}"
            eval_mode = idef.get("evaluation_mode", "HEURISTIC")
            try:
                scenario_metrics = _run_scenario_condition(
                    traffic_multiplier, duration, idef, control_metrics, warmup_steps, measurement_steps, scenario
                )
                deltas = _compute_deltas(control_metrics, scenario_metrics)
                conditions.append({
                    "condition_id": cond_id,
                    "traffic_multiplier": traffic_multiplier,
                    "intervention_id": iid,
                    "intervention_label": idef.get("label", iid),
                    "evaluation_mode": eval_mode,
                    "control_metrics": control_metrics,
                    "scenario_metrics": scenario_metrics,
                    "metric_deltas": deltas,
                    "metric_provenance": METRIC_PROVENANCE,
                    "status": "COMPLETED",
                    "error": None,
                })
                completed += 1
            except Exception as exc:
                conditions.append({
                    "condition_id": cond_id,
                    "traffic_multiplier": traffic_multiplier,
                    "intervention_id": iid,
                    "intervention_label": idef.get("label", iid),
                    "evaluation_mode": eval_mode,
                    "control_metrics": control_metrics,
                    "scenario_metrics": None,
                    "metric_deltas": None,
                    "metric_provenance": METRIC_PROVENANCE,
                    "status": "FAILED",
                    "error": str(exc),
                })
                failed += 1

    total = completed + failed + skipped

    # Experiment-level status
    if failed == 0 and skipped == 0 and completed > 0:
        exp_status = "COMPLETED"
    elif completed == 0:
        exp_status = "FAILED"
    else:
        exp_status = "PARTIALLY_COMPLETED"

    summary: ExperimentSummary = {
        "total": total,
        "completed": completed,
        "failed": failed,
        "skipped": skipped,
        "status": exp_status,
    }

    metadata: ExperimentMetadata = {
        "urbanmind_version": "1.0.0",
        "scenario_network": "mahalla-scenario/osm.sumocfg",
        "random_seed": None,
        "sumo_version": None,
        "effective_criterion": EFFECTIVE_CRITERION,
        "simulation_profile": simulation_profile,
    }

    return {
        "experiment_id": experiment_id,
        "schema_version": 1,
        "name": name,
        "created_at": created_at,
        "duration": duration,
        "traffic_levels": traffic_levels,
        "intervention_ids": intervention_ids,
        "conditions": conditions,
        "summary": summary,
        "metadata": metadata,
        "metric_provenance": METRIC_PROVENANCE,
    }


def get_interventions_registry() -> List[dict]:
    """
    Return the full intervention registry with evaluation modes and bilingual labels.
    Used by the frontend to populate the experiment builder.
    """
    try:
        signal_id, phase_index = _scenario_signal_selection()
    except Exception:
        # Fallback: return interventions without signal-specific fields
        signal_id, phase_index = "unknown", 0

    candidates = get_candidate_interventions(signal_id, phase_index)
    result = []
    for cand in candidates:
        cid = f"{cand.get('type')}_{cand.get('seconds', 0)}s_{cand.get('category')}"
        label_en = cand.get("label_en") or cand.get("label", cid)
        label_ru = cand.get("label_ru") or INTERVENTION_LABELS_RU.get(label_en, label_en)
        cat_en = cand.get("category", "mobility")
        cat_ru = cand.get("category_ru") or INTERVENTION_CATEGORIES_RU.get(cat_en, cat_en)
        result.append({
            "id": cid,
            "label": label_en,
            "label_en": label_en,
            "label_ru": label_ru,
            "type": cand.get("type"),
            "category": cat_en,
            "category_ru": cat_ru,
            "seconds": cand.get("seconds", 0),
            "evaluation_mode": cand.get("evaluation_mode", "HEURISTIC"),
        })
    return result
