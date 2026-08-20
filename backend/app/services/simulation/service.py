from typing import Optional, Any
from app.services.simulation.models import SimulationRequest, SimulationMetrics, OptimizationResult
from app.services.simulation.session import run_simulation, _scenario_signal_selection
from app.services.simulation.metrics import calculate_metrics, estimate_candidate_metrics
from app.services.simulation.interventions import get_candidate_interventions
from app.services.simulation.optimizer import evaluate_candidates, rank_candidates, compute_policy_comparison


def run_metrics_workflow(steps: int = 300, warmup_steps: int = 0, measurement_steps: int = 0, scenario: str = "midday", intervention: Optional[dict[str, Any]] = None) -> SimulationMetrics:
    """Orchestrates a single simulation run and metric calculation."""
    request: SimulationRequest = {
        "steps": steps,
        "warmup_steps": warmup_steps,
        "measurement_steps": measurement_steps or steps,
        "scenario": scenario,
        "intervention": intervention,
    }
    raw_result = run_simulation(request)
    metrics = calculate_metrics(raw_result)
    return metrics


def run_optimization_workflow(
    steps: int = 300,
    warmup_steps: int = 0,
    measurement_steps: int = 0,
    scenario: str = "midday",
    policy: str = "balanced",
    custom_weights: Optional[dict[str, float]] = None,
    language: str = "en"
) -> OptimizationResult:
    """
    Orchestrates Policy-Based Candidate Optimization:
    1. Runs baseline microscopic simulation once.
    2. Gathers and evaluates candidate interventions into a single evidence set.
    3. Ranks candidates under the active policy.
    4. Computes cross-policy comparison (FLOW, ECO, BALANCED, and CUSTOM if configured)
       reusing the exact same simulation evidence.
    """
    # 1. Baseline
    baseline_metrics = run_metrics_workflow(steps, warmup_steps, measurement_steps, scenario)
    
    # 2. Get Candidates
    signal_id, phase_index = _scenario_signal_selection()
    candidates = get_candidate_interventions(signal_id, phase_index)
    
    # 3. Evaluate Candidates to produce Common Evidence Set
    candidate_results_tuples = []
    for candidate in candidates:
        if candidate.get("evaluation_mode") == "SIMULATED":
            metrics = run_metrics_workflow(steps, warmup_steps, measurement_steps, scenario, candidate)
        else:
            metrics = estimate_candidate_metrics(baseline_metrics, candidate)
        candidate_results_tuples.append((candidate, metrics))
        
    # 4. Assemble and Rank under selected policy
    evaluated_candidates = evaluate_candidates(
        baseline_metrics,
        candidate_results_tuples,
        policy_id=policy,
        custom_weights=custom_weights,
        language=language
    )
    result = rank_candidates(
        scenario,
        baseline_metrics,
        evaluated_candidates,
        policy_id=policy,
        custom_weights=custom_weights,
        language=language
    )

    # 5. Compute cross-policy comparison (FLOW vs ECO vs BALANCED vs CUSTOM)
    result["policy_comparison"] = compute_policy_comparison(
        baseline_metrics,
        candidate_results_tuples,
        custom_weights=custom_weights,
        language=language
    )
    return result


def evaluate_policy_comparison_workflow(
    baseline: SimulationMetrics,
    candidate_results: list[tuple[dict[str, Any], SimulationMetrics]],
    custom_weights: Optional[dict[str, float]] = None,
    language: str = "en"
) -> dict[str, Any]:
    """Evaluates an existing simulation evidence set under all policies without re-running SUMO."""
    return compute_policy_comparison(
        baseline,
        candidate_results,
        custom_weights=custom_weights,
        language=language
    )



def run_scenario_workflow(request: dict[str, Any]) -> dict[str, Any]:
    """Orchestrates baseline vs scenario comparison."""
    scenario = "midday"
    duration = int(request.get("duration", 300))
    warmup_steps = int(request.get("warmup_steps", 0))
    measurement_steps = int(request.get("measurement_steps", duration))
    if "warmup_steps" in request or "measurement_steps" in request:
        duration = warmup_steps + measurement_steps

    traffic_multiplier = float(request.get("traffic_multiplier", 1.0))
    intervention_id = request.get("intervention_id")

    # 1. Normal Baseline (1.0x traffic)
    normal_baseline_request: SimulationRequest = {
        "steps": duration,
        "warmup_steps": warmup_steps,
        "measurement_steps": measurement_steps,
        "scenario": scenario,
        "intervention": None,
        "traffic_multiplier": 1.0,
    }
    normal_baseline_raw = run_simulation(normal_baseline_request)
    normal_baseline_metrics = calculate_metrics(normal_baseline_raw)

    # 2. Control (traffic_multiplier, no intervention)
    control_request: SimulationRequest = {
        "steps": duration,
        "warmup_steps": warmup_steps,
        "measurement_steps": measurement_steps,
        "scenario": scenario,
        "intervention": None,
        "traffic_multiplier": traffic_multiplier,
    }
    control_raw = run_simulation(control_request)
    control_metrics = calculate_metrics(control_raw)

    # 3. Find Intervention if provided
    intervention_def = None
    if intervention_id:
        signal_id, phase_index = _scenario_signal_selection()
        candidates = get_candidate_interventions(signal_id, phase_index)
        for cand in candidates:
            cand_id = f"{cand.get('type')}_{cand.get('seconds', 0)}s_{cand.get('category')}"
            if cand_id == intervention_id:
                intervention_def = cand
                break

    # 4. Scenario Execution
    scenario_request: SimulationRequest = {
        "steps": duration,
        "warmup_steps": warmup_steps,
        "measurement_steps": measurement_steps,
        "scenario": scenario,
        "intervention": intervention_def if intervention_def and intervention_def.get("evaluation_mode") == "SIMULATED" else None,
        "traffic_multiplier": traffic_multiplier,
    }
    scenario_raw = run_simulation(scenario_request)
    scenario_metrics = calculate_metrics(scenario_raw)

    if intervention_def and intervention_def.get("evaluation_mode") == "HEURISTIC":
        scenario_metrics = estimate_candidate_metrics(scenario_metrics, intervention_def)

    # 5. Deltas (Control vs Scenario)
    from app.services.simulation.metrics import METRIC_PROVENANCE
    deltas = {}
    metrics_to_compare = [
        "average_speed_kmh", "average_waiting_seconds", "mean_completed_vehicle_time_loss_seconds",
        "mean_active_vehicle_time_loss_seconds", "max_vehicle_count",
        "co2_kg", "nox_g", "noise_db", "pedestrian_delay_seconds", "accessibility_score"
    ]
    for key in metrics_to_compare:
        base_val = control_metrics.get(key)
        scen_val = scenario_metrics.get(key)
        base_val = base_val if base_val is not None else 0.0
        scen_val = scen_val if scen_val is not None else 0.0
        absolute = round(scen_val - base_val, 2)
        percentage = round((absolute / base_val * 100), 2) if base_val else None
        deltas[key] = {"absolute": absolute, "percentage": percentage}

    return {
        "scenario_metadata": request,
        "normal_baseline": normal_baseline_metrics,
        "control": control_metrics,
        "scenario": scenario_metrics,
        "deltas": deltas,
        "intervention": intervention_def,
        "metric_provenance": METRIC_PROVENANCE,
        "evaluation_mode": intervention_def.get("evaluation_mode") if intervention_def else None
    }
