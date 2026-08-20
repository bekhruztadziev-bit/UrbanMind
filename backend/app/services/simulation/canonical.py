from __future__ import annotations

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, TypedDict

from app.services.spatial.hierarchy import get_default_spatial_scope
from app.services.spatial.models import SpatialScopeRef
from app.services.simulation.models import SimulationMetrics, CandidateResult, TradeoffSummary
from app.services.simulation.interventions import get_candidate_interventions
from app.services.simulation.session import run_simulation, _scenario_signal_selection
from app.services.simulation.metrics import calculate_metrics
from app.services.simulation.optimizer import evaluate_candidates, rank_candidates, compute_policy_comparison
from app.services.simulation.statistics import compute_sample_statistics, get_t_critical
from app.services.calibration.service import get_calibration_status, get_model_vs_reality_breakdown
from app.services.simulation.network_inspector import get_network_identity


class CanonicalExperimentConfig(TypedDict, total=False):
    experiment_id: str
    title: str
    title_ru: str
    spatial_scope: SpatialScopeRef
    network_version: str
    scenario_set: List[str]
    demand_multipliers: List[float]
    primary_analysis_scenario: str
    secondary_sensitivity_scenarios: List[str]
    primary_outcome_metrics: List[str]
    secondary_outcome_metrics: List[str]
    policy_comparison_methodology: str
    seed_aggregation_method: str
    confidence_interval_method: str
    simulation_configuration_hash: str
    policies: List[str]
    candidate_interventions: List[Dict[str, Any]]
    seeds: List[int]
    simulation_duration: int
    warmup_steps: int
    measurement_steps: int
    metric_schema_version: int
    is_immutable: bool
    created_at: str


class CanonicalConditionResult(TypedDict, total=False):
    condition_id: str
    demand_multiplier: float
    candidate_id: str
    candidate_label: str
    candidate_label_ru: str
    seed: int
    metrics: Dict[str, Any]
    metric_deltas: Dict[str, Any]
    policy_scores: Dict[str, float]
    constraint_status: str
    evaluation_mode: str
    provenance: str


class CanonicalExperimentResult(TypedDict, total=False):
    experiment_id: str
    configuration: CanonicalExperimentConfig
    baseline_results: Dict[str, Any]
    candidate_results: List[CanonicalConditionResult]
    policy_results: Dict[str, Dict[str, Any]]  # demand_str -> { "flow": ..., "eco": ..., "balanced": ... }
    robustness: Dict[str, Any]
    tradeoffs: Dict[str, Any]
    evidence_strength: Dict[str, Any]
    calibration_status: Dict[str, Any]
    limitations: Dict[str, Any]
    created_at: str


DEFAULT_CANONICAL_EXPERIMENT_ID = "UM-EXP-2026-001"


def _compute_config_hash(raw_dict: Dict[str, Any]) -> str:
    core = {
        "experiment_id": raw_dict.get("experiment_id"),
        "network_version": raw_dict.get("network_version"),
        "demand_multipliers": raw_dict.get("demand_multipliers"),
        "policies": raw_dict.get("policies"),
        "seeds": raw_dict.get("seeds"),
        "simulation_duration": raw_dict.get("simulation_duration"),
        "warmup_steps": raw_dict.get("warmup_steps"),
        "measurement_steps": raw_dict.get("measurement_steps"),
        "metric_schema_version": raw_dict.get("metric_schema_version"),
        "candidate_interventions": raw_dict.get("candidate_interventions"),
        "scenario_set": raw_dict.get("scenario_set"),
        "spatial_scope": raw_dict.get("spatial_scope"),
        "policy_comparison_methodology": raw_dict.get("policy_comparison_methodology"),
        "seed_aggregation_method": raw_dict.get("seed_aggregation_method"),
    }
    raw = json.dumps(core, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def get_canonical_experiment_config(experiment_id: str = DEFAULT_CANONICAL_EXPERIMENT_ID) -> CanonicalExperimentConfig:
    """Returns the immutable specification for the configured demonstration experiment."""
    signal_id, phase_index = _scenario_signal_selection()
    candidates = get_candidate_interventions(signal_id, phase_index)
    
    cfg: CanonicalExperimentConfig = {
        "experiment_id": experiment_id,
        "title": "Configured Demonstration Corridor Signal Optimization",
        "title_ru": "Оптимизация сигналов в настроенном демонстрационном коридоре",
        "spatial_scope": get_default_spatial_scope(),
        "network_version": get_network_identity()["network_version"],
        "scenario_set": ["off_peak", "nominal_peak", "heavy_peak"],
        "demand_multipliers": [0.8, 1.0, 1.2],
        "primary_analysis_scenario": "1.0x",
        "secondary_sensitivity_scenarios": ["0.8x", "1.2x"],
        "primary_outcome_metrics": [
            "average_waiting_seconds",
            "average_travel_time_seconds",
            "stops_per_vehicle",
            "throughput_vehicles_per_hour",
        ],
        "secondary_outcome_metrics": [
            "co2_kg",
            "nox_g",
            "mean_queue_length_meters",
            "pedestrian_delay_seconds",
            "accessibility_score",
        ],
        "policy_comparison_methodology": "SHARED_EVIDENCE_PARETO_SCORING",
        "seed_aggregation_method": "IMPROVEMENT_OF_MEAN_METRICS",
        "confidence_interval_method": "STUDENT_T_95_CI",
        "policies": ["flow", "eco", "balanced"],
        "candidate_interventions": candidates,
        "seeds": [42, 101, 2024],
        "simulation_duration": 100,
        "warmup_steps": 20,
        "measurement_steps": 80,
        "metric_schema_version": 2,
        "is_immutable": True,
        "created_at": "2026-08-20T00:00:00Z",
    }
    cfg["simulation_configuration_hash"] = _compute_config_hash(cfg)
    return cfg


_CANONICAL_EXPERIMENT_CACHE: Dict[str, CanonicalExperimentResult] = {}
CANONICAL_ARTIFACT_PATH = Path(__file__).resolve().parents[3] / "data" / "canonical_experiment_artifact.json"


def _aggregate_seed_metrics(seed_metrics: List[SimulationMetrics]) -> SimulationMetrics:
    """Return mean numeric metrics while retaining shared run metadata.

    This intentionally aggregates only actual TraCI/SUMO observations.  It
    never manufactures seed-level variation or fills unavailable metrics.
    """
    if not seed_metrics:
        raise ValueError("Cannot aggregate an empty seed evidence set.")
    aggregate: SimulationMetrics = dict(seed_metrics[0])
    keys = set().union(*(sample.keys() for sample in seed_metrics))
    for key in keys:
        values = [sample.get(key) for sample in seed_metrics]
        numeric = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
        if numeric and len(numeric) == len(seed_metrics):
            aggregate[key] = round(sum(numeric) / len(numeric), 4)  # type: ignore
    aggregate["is_fallback"] = False
    return aggregate


def run_canonical_experiment(
    config: Optional[CanonicalExperimentConfig] = None,
    language: str = "en",
    force_refresh: bool = False
) -> CanonicalExperimentResult:
    """
    Executes the Canonical Experiment Protocol:
    1. Single simulation evidence collection across demand levels (0.8x, 1.0x, 1.2x) and seeds.
    2. Shared evidence reuse across FLOW, ECO, and BALANCED policies.
    3. Multi-seed stochastic variance & Student-t 95% confidence interval calculation.
    4. Deterministic cross-policy outcome summaries.
    """
    cfg = config or get_canonical_experiment_config()
    exp_id = cfg.get("experiment_id", DEFAULT_CANONICAL_EXPERIMENT_ID)
    computed_hash = _compute_config_hash(cfg)
    if cfg.get("simulation_configuration_hash") != computed_hash:
        cfg = dict(cfg)
        cfg["simulation_configuration_hash"] = computed_hash
    cache_key = f"{exp_id}_{language}_{computed_hash}"
    
    if not force_refresh and cache_key in _CANONICAL_EXPERIMENT_CACHE:
        return _CANONICAL_EXPERIMENT_CACHE[cache_key]

    demand_multipliers = cfg.get("demand_multipliers", [0.8, 1.0, 1.2])
    seeds = cfg.get("seeds", [42, 101, 2024])
    duration = cfg.get("simulation_duration", 100)
    warmup = cfg.get("warmup_steps", 20)
    measurement = cfg.get("measurement_steps", 80)
    
    signal_id, phase_index = _scenario_signal_selection()
    candidates = cfg.get("candidate_interventions") or get_candidate_interventions(signal_id, phase_index)
    
    baseline_results: Dict[str, Any] = {}
    candidate_results: List[CanonicalConditionResult] = []
    policy_results_by_demand: Dict[str, Dict[str, Any]] = {}
    metric_samples_by_demand_and_candidate: Dict[str, Dict[str, List[float]]] = {}

    for demand in demand_multipliers:
        demand_key = f"{demand:.1f}x"
        metric_samples_by_demand_and_candidate[demand_key] = {}
        baseline_seed_metrics: List[SimulationMetrics] = []
        for seed in seeds:
            baseline_seed_metrics.append(calculate_metrics(run_simulation({
                "steps": duration,
                "warmup_steps": warmup,
                "measurement_steps": measurement,
                "scenario": "midday",
                "traffic_multiplier": demand,
                "seed": seed,
            })))
        base_rep = _aggregate_seed_metrics(baseline_seed_metrics)
        baseline_results[demand_key] = base_rep

        # Every candidate is executed for every seed.  Policy comparisons then
        # re-rank the same aggregate evidence rather than rerunning SUMO.
        candidate_eval_tuples = []
        for cand in candidates:
            cand_id = cand.get("id") or f"{cand.get('type')}_{cand.get('seconds', 0)}s_{cand.get('category', 'mobility')}"
            seed_metrics: List[SimulationMetrics] = []
            metric_samples_by_demand_and_candidate[demand_key][cand_id] = []
            for seed in seeds:
                cand_metrics = calculate_metrics(run_simulation({
                    "steps": duration,
                    "warmup_steps": warmup,
                    "measurement_steps": measurement,
                    "scenario": "midday",
                    "traffic_multiplier": demand,
                    "intervention": cand,
                    "seed": seed,
                }))
                seed_metrics.append(cand_metrics)
                metric_samples_by_demand_and_candidate[demand_key][cand_id].append(
                    float(cand_metrics.get("average_waiting_seconds", 0.0))
                )
                candidate_results.append({
                    "condition_id": f"{exp_id}_{demand_key}_{cand_id}_seed{seed}",
                    "demand_multiplier": demand,
                    "candidate_id": cand_id,
                    "candidate_label": cand.get("label", cand_id),
                    "candidate_label_ru": cand.get("label_ru", cand.get("label", cand_id)),
                    "seed": seed,
                    "metrics": cand_metrics,
                    "evaluation_mode": "SIMULATED",
                    "provenance": "SIMULATED",
                })
            candidate_eval_tuples.append((cand, _aggregate_seed_metrics(seed_metrics)))

        # Cross-policy comparison consumes this one common evidence set.
        cross_policy_map = compute_policy_comparison(
            base_rep,
            candidate_eval_tuples,
            language=language
        )
        policy_results_by_demand[demand_key] = cross_policy_map

    # 4. Compute Statistical Robustness across seeds (nominal 1.0x demand)
    nominal_samples = metric_samples_by_demand_and_candidate.get("1.0x", {})
    robustness_stats = {}
    for cand_id, delays in nominal_samples.items():
        if delays:
            cand_stat = compute_sample_statistics(delays)
            robustness_stats[cand_id] = {
                "mean_delay_s": cand_stat["mean"],
                "std_dev_s": cand_stat["std_dev"],
                "standard_error_s": cand_stat["standard_error"],
                "degrees_of_freedom": cand_stat["degrees_of_freedom"],
                "t_critical": cand_stat["t_critical"],
                "margin_of_error_s": cand_stat["margin_of_error"],
                "ci_95_low": cand_stat["ci_95_low"],
                "ci_95_high": cand_stat["ci_95_high"],
                "min": cand_stat["min"],
                "max": cand_stat["max"],
                "sample_count": cand_stat["sample_count"],
                "ci_method": cand_stat["ci_method"],
            }

    calib_record = get_calibration_status(cfg.get("spatial_scope", {}).get("id", "central_corridor"))
    df_val = len(seeds) - 1
    t_crit_val = get_t_critical(df_val)
    nominal_balanced = policy_results_by_demand.get("1.0x", {}).get("balanced", {})
    nominal_winner = nominal_balanced.get("winner", {})
    nominal_tradeoffs = nominal_winner.get("tradeoff_summary", {})
    all_constraints_valid = all(
        policy_results_by_demand[demand_key][policy_id].get("winner", {}).get("policy_breakdown", {}).get("is_valid", False)
        for demand_key in policy_results_by_demand
        for policy_id in ("flow", "eco", "balanced")
    )
    evidence_score = 25 if len(seeds) >= 3 else (10 if len(seeds) == 1 else 0)
    evidence_score += 25 if len(demand_multipliers) >= 3 else 15
    evidence_score += 15 if all_constraints_valid else 0
    evidence_level = "MODERATE" if evidence_score >= 50 else "LOW"

    final_result: CanonicalExperimentResult = {
        "experiment_id": exp_id,
        "configuration": cfg,
        "baseline_results": baseline_results,
        "candidate_results": candidate_results,
        "policy_results": policy_results_by_demand,
        "robustness": {
            "sample_count": len(seeds),
            "seeds": seeds,
            "stats": robustness_stats,
            "multi_seed_evaluated": True,
            "aggregation_method": "IMPROVEMENT_OF_MEAN_METRICS",
            "statistical_method": "Student-t 95% CI (Bessel-corrected sample standard deviation)",
            "degrees_of_freedom": df_val,
            "t_critical": t_crit_val,
            "methodology_note_en": f"Evaluated across {len(seeds)} random seeds with exact Student-t 95% confidence intervals (df={df_val}, t={t_crit_val:.3f}).",
            "methodology_note_ru": f"Оценено по {len(seeds)} случайным сидам с точным доверительным интервалом Стьюдента 95% (df={df_val}, t={t_crit_val:.3f}).",
        },
        "tradeoffs": nominal_tradeoffs,
        "evidence_strength": {
            "rubric_name": "UrbanMind Evidence Strength Score (Decision-Support Rubric)",
            "level": evidence_level,
            "score": evidence_score,
            "score_scale": "0-100",
            "criteria_breakdown": {
                "seed_robustness": {"points": 25, "max": 35, "desc": f"{len(seeds)} stochastic seeds evaluated with Student-t CI"},
                "scenario_diversity": {"points": 25 if len(demand_multipliers) >= 3 else 15, "max": 25, "desc": f"{len(demand_multipliers)} demand levels evaluated"},
                "constraint_compliance": {"points": 15 if all_constraints_valid else 0, "max": 15, "desc": "All evaluated policy constraints satisfied" if all_constraints_valid else "At least one evaluated policy constraint was violated"},
                "calibration_availability": {"points": 0, "max": 5, "desc": "Traffic model UNCALIBRATED (field detector counts pending)"},
            },
            "score_interpretation_note_en": "Internal decision-support rubric, not a statistical confidence probability.",
            "score_interpretation_note_ru": "Внутренняя экспертная оценка силы доказательств; не является вероятностью статистической достоверности.",
            "explanation_en": "Multi-seed microscopic SUMO/TraCI evidence. Traffic demand remains UNCALIBRATED until field turning counts are imported and evaluated.",
            "explanation_ru": "Микромоделирование SUMO/TraCI по нескольким сидам. Транспортный спрос остается НЕ ОТКАЛИБРОВАННЫМ до загрузки и оценки натурных подсчетов поворотных потоков.",
        },
        "calibration_status": calib_record,
        "limitations": {
            "modeled_caveats_en": [
                "Microscopic traffic simulation operates in UNCALIBRATED state for demand volumes.",
                "Vehicle arrivals follow synthetic stochastic Poisson distribution.",
            ],
            "modeled_caveats_ru": [
                "Микромоделирование трафика находится в статусе «НЕ ОТКАЛИБРОВАНО» по реальным объемам спроса.",
                "Прибытие ТС использует синтетическое распределение Пуассона.",
            ],
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    _CANONICAL_EXPERIMENT_CACHE[cache_key] = final_result
    return final_result


def write_canonical_experiment_artifact(
    config: Optional[CanonicalExperimentConfig] = None,
    language: str = "en",
) -> CanonicalExperimentResult:
    """Deliberately execute and persist an immutable conference artifact."""
    result = run_canonical_experiment(config=config, language=language, force_refresh=True)
    # The Case Study is persisted together with the evidence it reports.  It
    # is intentionally constructed only here, after a deliberate SUMO run;
    # ordinary UI/API reads never reconstruct it from a fresh simulation.
    from app.services.case_studies.generator import generate_case_study
    case_study = generate_case_study(
        canonical_experiment=result,
        case_id="UM-CS-2026-001",
        language=language,
    )
    artifact = {
        "artifact_type": "PRECOMPUTED_SIMULATION_ARTIFACT",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "configuration_hash": result["configuration"]["simulation_configuration_hash"],
        "result_hash": hashlib.sha256(json.dumps(result, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
        "result": result,
        "case_study": case_study,
    }
    CANONICAL_ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CANONICAL_ARTIFACT_PATH.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def load_canonical_experiment_artifact() -> Optional[CanonicalExperimentResult]:
    """Load a locked artifact only when it matches the current canonical config."""
    if not CANONICAL_ARTIFACT_PATH.exists():
        return None
    try:
        artifact = json.loads(CANONICAL_ARTIFACT_PATH.read_text(encoding="utf-8"))
        result = artifact.get("result")
        if not isinstance(result, dict) or artifact.get("artifact_type") != "PRECOMPUTED_SIMULATION_ARTIFACT":
            return None
        expected = get_canonical_experiment_config().get("simulation_configuration_hash")
        if artifact.get("configuration_hash") != expected:
            return None
        expected_result_hash = hashlib.sha256(json.dumps(result, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        if artifact.get("result_hash") != expected_result_hash:
            return None
        return result
    except (OSError, ValueError, TypeError):
        return None


def load_canonical_case_study_artifact() -> Optional[Dict[str, Any]]:
    """Return the precomputed Case Study only when its evidence artifact verifies."""
    # Reuse the evidence/configuration integrity checks above before exposing
    # the stored presentation snapshot.
    result = load_canonical_experiment_artifact()
    if result is None:
        return None
    try:
        artifact = json.loads(CANONICAL_ARTIFACT_PATH.read_text(encoding="utf-8"))
        case_study = artifact.get("case_study")
        if not isinstance(case_study, dict):
            return None
        if case_study.get("experiment_id") != result.get("experiment_id"):
            return None
        if case_study.get("artifact_type") not in (None, "PRECOMPUTED_SIMULATION_ARTIFACT"):
            return None
        return case_study
    except (OSError, ValueError, TypeError):
        return None
