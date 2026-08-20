from typing import Optional, Any
from app.services.simulation.models import SimulationRequest, SimulationMetrics, OptimizationResult
from app.services.simulation.session import run_simulation, _scenario_signal_selection, _is_sumo_available
from app.services.simulation.metrics import calculate_metrics
from app.services.simulation.interventions import get_candidate_interventions
from app.services.simulation.optimizer import evaluate_candidates, rank_candidates, compute_policy_comparison
from app.services.simulation.policies import get_policy
from app.services.simulation.canonical import _load_locked_canonical_experiment_artifact


def _run_locked_canonical_optimization(policy: str, custom_weights: Optional[dict[str, float]], language: str) -> OptimizationResult:
    """Return a policy reranking from the reviewed canonical SUMO artifact.

    This path is intentionally limited to policies that were evaluated in the
    shared canonical evidence set. It is suitable for serverless presentation
    and policy comparison, but it never claims to be a fresh SUMO execution.
    """
    if policy == "custom":
        raise RuntimeError("Custom policy optimization requires a live SUMO runtime or a separately precomputed custom evidence set.")

    artifact_result = _load_locked_canonical_experiment_artifact()
    if not artifact_result:
        raise RuntimeError("Canonical optimization artifact is unavailable or failed integrity verification.")

    primary_key = "1.0x"
    baseline_results = artifact_result.get("baseline_results") or {}
    policy_results = artifact_result.get("policy_results") or {}
    baseline = baseline_results.get(primary_key)
    primary_policies = policy_results.get(primary_key) or {}
    selected = primary_policies.get(policy)
    if not isinstance(baseline, dict) or not isinstance(selected, dict):
        raise RuntimeError(f"Canonical artifact has no {policy.upper()} evidence for the primary 1.0x demand condition.")

    ranking = selected.get("ranking") or []
    winner = selected.get("winner") or (ranking[0] if ranking else None)
    if not ranking or not isinstance(winner, dict):
        raise RuntimeError("Canonical artifact contains no ranked candidate evidence.")

    policy_definition = get_policy(policy, custom_weights)
    policy_comparison = {
        key: value
        for key, value in primary_policies.items()
        if key in ("flow", "eco", "balanced") and isinstance(value, dict)
    }
    return {
        "scenario": "midday",
        "policy": policy,
        "policy_definition": {
            "policy_id": policy_definition.policy_id,
            "name": policy_definition.name,
            "name_ru": policy_definition.name_ru,
            "description": policy_definition.description,
            "description_ru": policy_definition.description_ru,
            "icon": policy_definition.icon,
            "objective_question": policy_definition.objective_question,
            "objective_question_ru": policy_definition.objective_question_ru,
            "primary_dimensions": policy_definition.primary_dimensions,
            "objective_weights": policy_definition.objective_weights,
            "normalization_method": policy_definition.normalization_method,
        },
        "baseline": baseline,
        "candidates": ranking,
        "ranked_candidates": ranking,
        "best_candidate": winner,
        "why_won": selected.get("why_won_ru" if language == "ru" else "why_won_en", selected.get("why_won", "")),
        "why_won_ru": selected.get("why_won_ru", selected.get("why_won", "")),
        "why_won_en": selected.get("why_won_en", selected.get("why_won", "")),
        "policy_comparison": policy_comparison,
        "evidence_mode": "PRECOMPUTED_SIMULATION_ARTIFACT",
        "artifact_type": "PRECOMPUTED_SIMULATION_ARTIFACT",
        "runtime_status": "SUMO_UNAVAILABLE_LOCKED_EVIDENCE",
        "artifact_experiment_id": artifact_result.get("experiment_id"),
        "demand_condition": primary_key,
        "calibration_status": artifact_result.get("calibration_status"),
        "evidence_strength": artifact_result.get("evidence_strength"),
    }


def run_metrics_workflow(steps: int = 300, warmup_steps: int = 0, measurement_steps: int = 0, scenario: str = "midday", intervention: Optional[dict[str, Any]] = None, simulation_id: Optional[str] = None, seed: Optional[int] = None) -> SimulationMetrics:
    """Return live SUMO metrics or the reviewed canonical baseline in cloud mode.

    A serverless deployment cannot execute SUMO. Returning the locked baseline
    prevents the dashboard from showing zero-valued placeholders while keeping
    the result explicitly tied to precomputed simulation evidence.
    """
    if not _is_sumo_available():
        artifact_result = _load_locked_canonical_experiment_artifact()
        baseline = (artifact_result or {}).get("baseline_results", {}).get("1.0x")
        if not isinstance(baseline, dict):
            raise RuntimeError("Canonical baseline artifact is unavailable or failed integrity verification.")
        return {
            **baseline,
            "evidence_mode": "PRECOMPUTED_SIMULATION_ARTIFACT",
            "artifact_type": "PRECOMPUTED_SIMULATION_ARTIFACT",
            "runtime_status": "SUMO_UNAVAILABLE_LOCKED_EVIDENCE",
            "artifact_experiment_id": artifact_result.get("experiment_id"),
            "demand_condition": "1.0x",
        }

    request: SimulationRequest = {
        "steps": steps,
        "warmup_steps": warmup_steps,
        "measurement_steps": measurement_steps or steps,
        "scenario": scenario,
        "intervention": intervention,
        "simulation_id": simulation_id,
        "seed": seed,
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
    # A Vercel/serverless runtime has no SUMO binary. Reuse only the reviewed
    # canonical SUMO evidence in that environment; never use synthetic values.
    if not _is_sumo_available():
        return _run_locked_canonical_optimization(policy, custom_weights, language)

    # 1. Baseline
    baseline_metrics = run_metrics_workflow(steps, warmup_steps, measurement_steps, scenario)
    
    # 2. Get Candidates
    signal_id, phase_index = _scenario_signal_selection()
    candidates = get_candidate_interventions(signal_id, phase_index)
    
    # 3. Evaluate Candidates to produce Common Evidence Set
    candidate_results_tuples = []
    for candidate in candidates:
        metrics = run_metrics_workflow(steps, warmup_steps, measurement_steps, scenario, candidate)
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
        "intervention": intervention_def,
        "traffic_multiplier": traffic_multiplier,
    }
    scenario_raw = run_simulation(scenario_request)
    scenario_metrics = calculate_metrics(scenario_raw)

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
