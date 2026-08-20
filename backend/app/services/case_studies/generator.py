from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.case_studies.models import CaseStudy
from app.services.reports.generator import generate_decision_report
from app.services.reports.models import DecisionReport
from app.services.simulation.canonical import DEFAULT_CANONICAL_EXPERIMENT_ID
from app.services.calibration.service import get_field_validation_protocol
from app.services.spatial.hierarchy import get_default_spatial_scope


DEFAULT_CANONICAL_CASE_ID = "UM-CS-2026-001"


def _pct_change(baseline: float, optimized: float) -> float:
    return round(((optimized - baseline) / baseline) * 100.0, 2) if baseline else 0.0


def _outcome_rows(baseline: Dict[str, Any], optimized: Dict[str, Any], delay_stats: Dict[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    primary_specs = [
        ("average_waiting_seconds", "Sampled accumulated waiting snapshot mean", "Среднее накопленное ожидание по выборке снимков", "s", "minimize", "SIMULATED"),
        ("average_travel_time_seconds", "Corridor Travel Time", "Время проезда коридора", "s", "minimize", "SIMULATED"),
        ("stops_per_vehicle", "Stops per Vehicle", "Остановок на автомобиль", "stops/veh", "minimize", "SIMULATED"),
        ("throughput_vehicles_per_hour", "Corridor Throughput", "Пропускная способность", "veh/h", "maximize", "SIMULATED"),
    ]
    secondary_specs = [
        ("sumo_co2_kg", "Modeled CO2 emissions", "Моделируемые выбросы CO2", "kg", "minimize", "SIMULATED"),
        ("sumo_nox_g", "Modeled NOx emissions", "Моделируемые выбросы NOx", "g", "minimize", "SIMULATED"),
        ("mean_queue_length_meters", "Queue Length", "Длина очереди", "m", "minimize", "SIMULATED"),
        ("pedestrian_delay_seconds", "Pedestrian Delay Indicator", "Индикатор задержки пешеходов", "s", "minimize", "DERIVED"),
    ]

    def build(spec: tuple) -> Dict[str, Any]:
        key, name_en, name_ru, unit, direction, provenance = spec
        base = float(baseline.get(key, 0.0) or 0.0)
        opt = float(optimized.get(key, 0.0) or 0.0)
        stats = delay_stats if key == "average_waiting_seconds" else {}
        return {
            "key": key, "name_en": name_en, "name_ru": name_ru, "unit": unit,
            "baseline": round(base, 4), "optimized": round(opt, 4),
            "absolute_delta": round(opt - base, 4), "relative_delta_pct": _pct_change(base, opt),
            "ci_95_low": stats.get("ci_95_low"), "ci_95_high": stats.get("ci_95_high"),
            "t_critical": stats.get("t_critical"), "df": stats.get("degrees_of_freedom"),
            "direction": direction, "is_improvement": opt < base if direction == "minimize" else opt > base,
            "provenance": provenance,
        }

    return [build(spec) for spec in primary_specs], [build(spec) for spec in secondary_specs]


def generate_case_study(
    canonical_experiment: Optional[Dict[str, Any]] = None,
    decision_report: Optional[DecisionReport] = None,
    case_id: str = DEFAULT_CANONICAL_CASE_ID,
    language: str = "en",
) -> CaseStudy:
    """Derive a case study strictly from supplied experiment/report evidence."""
    exp = canonical_experiment or {}
    exp_id = exp.get("experiment_id", DEFAULT_CANONICAL_EXPERIMENT_ID)
    cfg = exp.get("configuration", {})
    nominal = exp.get("policy_results", {}).get("1.0x", {})
    baseline = exp.get("baseline_results", {}).get("1.0x", {})
    winner = nominal.get("balanced", {}).get("winner", {})
    if decision_report is None:
        winner = dict(winner)
        winner["robustness_seeds"] = list(cfg.get("seeds", []))
        winner["robustness_sample_count"] = len(cfg.get("seeds", []))
        decision_report = generate_decision_report({
            "scenario": "nominal_peak", "policy": "balanced", "baseline": baseline,
            "best_candidate": winner, "ranked_candidates": nominal.get("balanced", {}).get("ranking", []),
            "policy_comparison": nominal,
        }, policy_id="balanced", experiment_id=exp_id, language=language)
    rep = decision_report
    optimized = rep.get("optimized_metrics") or winner.get("metrics", {})
    baseline = rep.get("baseline_metrics") or baseline
    robustness = exp.get("robustness") or rep.get("robustness") or {}
    selected_id = rep.get("intervention_id") or winner.get("id")
    delay_stats = robustness.get("stats", {}).get(selected_id, {})
    primary, secondary = _outcome_rows(baseline, optimized, delay_stats)
    delay = primary[0]
    co2 = secondary[0]
    scope = cfg.get("spatial_scope") or rep.get("spatial_scope") or get_default_spatial_scope()
    seeds = cfg.get("seeds", robustness.get("seeds", []))
    calibration = rep.get("calibration_status") or exp.get("calibration_status") or {"status": "UNCALIBRATED", "traffic_calibrated": False}
    selected = rep.get("executive_summary", {})
    label = selected.get("recommended_intervention") or winner.get("label") or selected_id
    label_ru = selected.get("recommended_intervention_ru") or winner.get("label_ru") or label
    delay_reduction = -delay["relative_delta_pct"]
    reproducibility = {
        "experiment_id": exp_id, "network_version": cfg.get("network_version"), "scenario_id": "1.0x",
        "demand_multiplier": 1.0, "policy": "BALANCED", "intervention": selected_id, "seeds": seeds,
        "sample_size": len(seeds), "simulation_duration": cfg.get("simulation_duration"), "warmup_steps": cfg.get("warmup_steps"),
        "measurement_steps": cfg.get("measurement_steps"), "metric_schema_version": cfg.get("metric_schema_version"),
        "simulation_configuration_hash": cfg.get("simulation_configuration_hash"), "aggregation_method": robustness.get("aggregation_method"),
        "statistical_method": robustness.get("statistical_method"), "degrees_of_freedom": delay_stats.get("degrees_of_freedom"),
        "t_critical": delay_stats.get("t_critical"), "created_at": exp.get("created_at"),
    }
    delay_text = f"{delay_reduction:.2f}% modeled reduction in sampled accumulated waiting snapshot mean ({delay['baseline']:.2f} to {delay['optimized']:.2f} {delay['unit']})"
    return {
        "case_id": case_id, "experiment_id": exp_id, "report_id": rep.get("report_id"),
        "title": "Configured Demonstration Corridor: Simulation-Supported Signal Optimization",
        "title_ru": "Настроенный демонстрационный коридор: оптимизация сигналов на основе моделирования",
        "problem_statement": "This case study compares implemented signal-control interventions in an uncalibrated SUMO corridor model.",
        "problem_statement_ru": "В данном кейсе сравниваются реализованные меры управления сигналами в некалиброванной коридорной модели SUMO.",
        "spatial_scope": scope, "demand_scenarios_tested": [f"{value:.1f}x" for value in cfg.get("demand_multipliers", [])],
        "policy_comparison": nominal or rep.get("policy_comparison") or {},
        "selected_candidate": {"id": selected_id, "label": label, "label_ru": label_ru, "policy": rep.get("policy_id", "balanced"), "policy_score": rep.get("policy_score"), "why_won": rep.get("why_won"), "why_won_ru": rep.get("why_won_ru")},
        "key_results": {"delay_reduction_pct": delay_reduction, "co2_reduction_pct": -co2["relative_delta_pct"], "throughput_increase_pct": primary[3]["relative_delta_pct"], "stops_reduction_pct": -primary[2]["relative_delta_pct"]},
        "primary_outcomes": primary, "secondary_outcomes": secondary, "reproducibility_record": reproducibility,
        "provenance_views": {"delay": {"metric_name": "Sampled accumulated waiting snapshot mean", "headline_value": delay_text, "source": "SUMO / TraCI", "experiment_id": exp_id, "seeds": seeds, "statistical_method": robustness.get("statistical_method"), "calibration_status": calibration.get("status")}},
        "epistemic_statements": [
            {"statement_id": "EP-SIM-001", "text_en": f"SUMO/TraCI estimates {delay_text}.", "text_ru": f"SUMO/TraCI оценивает {delay_text}.", "category": "SIMULATED", "source": "Canonical experiment output", "notes_en": "Model output; not a field observation."},
            {"statement_id": "EP-DER-001", "text_en": "Policy scores are deterministic weighted comparisons of the shared simulation evidence.", "text_ru": "Оценки политик — детерминированное взвешенное сравнение общего массива симуляционных данных.", "category": "DERIVED", "source": "UrbanMind policy engine", "notes_en": "Not an observed outcome."},
            {"statement_id": "EP-ASM-001", "text_en": "Traffic demand remains uncalibrated until field turning-count observations are imported and evaluated.", "text_ru": "Транспортный спрос остается некалиброванным до загрузки и оценки натурных подсчетов поворотных потоков.", "category": "ASSUMPTION", "source": "Calibration status", "notes_en": "No traffic field observation is claimed here."},
        ],
        "tradeoffs": rep.get("tradeoffs") or winner.get("tradeoff_summary") or {}, "robustness": robustness,
        "evidence_strength": rep.get("evidence_status") or exp.get("evidence_strength") or {}, "calibration_status": calibration,
        "model_vs_reality": rep.get("model_vs_reality") or {},
        "prediction_vs_reality": {"prediction_metric": "average_waiting_seconds", "predicted_value": optimized.get("average_waiting_seconds"), "observed_outcome": None, "absolute_error": None, "relative_error_pct": None, "validation_status": "PENDING_FIELD_DEPLOYMENT", "notes_en": "No field outcome has been imported."},
        "field_validation_protocol": get_field_validation_protocol(scope.get("id", "central_corridor")), "next_action": rep.get("next_action") or {}, "limitations": rep.get("limitations") or {},
        "what_we_know_en": ["All candidate outcomes shown here originate from SUMO runs.", "Policy rankings reuse a single evidence set."],
        "what_we_know_ru": ["Все представленные результаты кандидатов получены из запусков SUMO.", "Ранжирование политик использует единый массив данных."],
        "what_we_do_not_know_en": ["Real-world traffic performance; the traffic model is uncalibrated.", "Observed post-deployment outcomes."],
        "what_we_do_not_know_ru": ["Реальную транспортную эффективность: модель трафика не откалибрована.", "Натурные результаты после внедрения."],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "PRECOMPUTED_SIMULATION_ARTIFACT",
        "artifact_configuration_hash": cfg.get("simulation_configuration_hash"),
    }
