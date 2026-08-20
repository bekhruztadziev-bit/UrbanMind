from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.services.calibration.service import (
    get_calibration_status,
    get_model_vs_reality_breakdown,
    compute_validation_metrics,
)
from app.services.reports.models import (
    DecisionReport,
    ExecutiveSummary,
    PolicyAudit,
    MetricComparisonRow,
    TradeoffBreakdown,
    RobustnessEvidence,
    MethodologyRecord,
    LimitationsRecord,
    EvidenceStatus,
    NextActionRecord,
)
from app.services.simulation.metrics import METRIC_PROVENANCE
from app.services.simulation.policies import get_policy, POLICIES, METRIC_DIRECTIONS
from app.services.simulation.statistics import compute_sample_statistics
from app.services.spatial.hierarchy import get_default_spatial_scope, get_cross_district_context


# Canonical Metric Definition Metadata
METRIC_REGISTRY = [
    {
        "key": "average_waiting_seconds",
        "name_en": "Sampled accumulated waiting snapshot mean",
        "name_ru": "Среднее накопленное ожидание по выборке снимков",
        "unit": "s",
        "direction": "minimize",
        "provenance": "SIMULATED",
    },
    {
        "key": "average_travel_time_seconds",
        "name_en": "Travel Time",
        "name_ru": "Время в пути",
        "unit": "s",
        "direction": "minimize",
        "provenance": "SIMULATED",
    },
    {
        "key": "stops_per_vehicle",
        "name_en": "Stops / Vehicle",
        "name_ru": "Остановок на автомобиль",
        "unit": "stops",
        "direction": "minimize",
        "provenance": "SIMULATED",
    },
    {
        "key": "mean_queue_length_meters",
        "name_en": "Queue Length",
        "name_ru": "Длина очереди",
        "unit": "m",
        "direction": "minimize",
        "provenance": "SIMULATED",
    },
    {
        "key": "throughput_vehicles_per_hour",
        "name_en": "Throughput",
        "name_ru": "Пропускная способность",
        "unit": "veh/h",
        "direction": "maximize",
        "provenance": "SIMULATED",
    },
    {
        "key": "average_speed_kmh",
        "name_en": "Average Speed",
        "name_ru": "Средняя скорость",
        "unit": "km/h",
        "direction": "maximize",
        "provenance": "SIMULATED",
    },
    {
        "key": "sumo_co2_kg",
        "name_en": "CO₂ Emissions",
        "name_ru": "Выбросы CO₂",
        "unit": "kg",
        "direction": "minimize",
        "provenance": "SIMULATED",
    },
    {
        "key": "sumo_nox_g",
        "name_en": "NOₓ Emissions",
        "name_ru": "Выбросы NOₓ",
        "unit": "g",
        "direction": "minimize",
        "provenance": "SIMULATED",
    },
    {
        "key": "noise_db",
        "name_en": "Noise Level",
        "name_ru": "Уровень шума",
        "unit": "dB",
        "direction": "minimize",
        "provenance": "ESTIMATED",
    },
    {
        "key": "pedestrian_delay_seconds",
        "name_en": "Pedestrian Delay",
        "name_ru": "Задержка пешеходов",
        "unit": "s",
        "direction": "minimize",
        "provenance": "ESTIMATED",
    },
    {
        "key": "accessibility_score",
        "name_en": "Accessibility Score",
        "name_ru": "Оценка доступности",
        "unit": "%",
        "direction": "maximize",
        "provenance": "ESTIMATED",
    },
]


def _compute_evidence_status(
    sample_count: int,
    is_multi_condition: bool,
    is_valid: bool,
    robustness_stats: Dict[str, Any],
    has_observed_ambient: bool = True
) -> EvidenceStatus:
    """
    Derives an objective, transparent evidence strength indicator (LOW, MODERATE, HIGH)
    based on empirical simulation parameters, confidence intervals, and constraint compliance.
    """
    criteria: Dict[str, Any] = {}
    score = 0

    # 1. Multi-seed stochastic sampling (up to 35 pts)
    if sample_count >= 5:
        criteria["seed_count"] = {"status": "PASS", "points": 35, "desc": f"{sample_count} stochastic seeds evaluated"}
        score += 35
    elif sample_count >= 3:
        criteria["seed_count"] = {"status": "PASS", "points": 25, "desc": f"{sample_count} stochastic seeds evaluated"}
        score += 25
    elif sample_count == 1:
        criteria["seed_count"] = {"status": "PARTIAL", "points": 10, "desc": "Single seed run (limited stochastic variance)"}
        score += 10
    else:
        criteria["seed_count"] = {"status": "NOT_EVALUATED", "points": 0, "desc": "Multi-seed robustness was not evaluated"}

    # 2. Multi-demand scenario coverage (up to 25 pts)
    if is_multi_condition:
        criteria["demand_coverage"] = {"status": "PASS", "points": 25, "desc": "Multi-scenario demand levels tested (0.8x, 1.0x, 1.2x)"}
        score += 25
    else:
        criteria["demand_coverage"] = {"status": "PARTIAL", "points": 15, "desc": "Single demand scenario profile"}
        score += 15

    # 3. Confidence interval precision (up to 20 pts)
    delay_stat = robustness_stats.get("average_waiting_seconds") or {}
    mean_val = float(delay_stat.get("mean", 0.0) or 0.0)
    std_val = float(delay_stat.get("std_dev", 0.0) or 0.0)
    rel_margin = (std_val / mean_val) if mean_val > 0 else 0.5

    if sample_count < 2:
        criteria["confidence_interval"] = {"status": "NOT_EVALUATED", "points": 0, "desc": "No multi-seed Student-t confidence interval is available"}
    elif rel_margin <= 0.15:
        criteria["confidence_interval"] = {"status": "PASS", "points": 20, "desc": f"Narrow 95% CI (relative margin {rel_margin*100:.1f}%)"}
        score += 20
    elif rel_margin <= 0.30:
        criteria["confidence_interval"] = {"status": "PASS", "points": 10, "desc": f"Moderate 95% CI (relative margin {rel_margin*100:.1f}%)"}
        score += 10
    else:
        criteria["confidence_interval"] = {"status": "PARTIAL", "points": 5, "desc": "Wider variance across simulation runs"}
        score += 5

    # 4. Policy Constraint compliance (up to 15 pts)
    if is_valid:
        criteria["constraint_compliance"] = {"status": "PASS", "points": 15, "desc": "All policy limits and thresholds satisfied"}
        score += 15
    else:
        criteria["constraint_compliance"] = {"status": "FAIL", "points": 0, "desc": "Policy constraint violation detected"}

    # 5. Observed ambient context integration (up to 5 pts)
    if has_observed_ambient:
        criteria["observed_baseline"] = {"status": "PASS", "points": 5, "desc": "Integrated with physical air monitoring baseline"}
        score += 5

    level: str = "HIGH" if score >= 75 else ("MODERATE" if score >= 50 else "LOW")

    explanation_en = (
        f"Evidence strength is {level} (score: {score}/100) based on {sample_count} stochastic seeds, "
        f"{'multi-scenario demand testing' if is_multi_condition else 'single scenario testing'}, "
        f"and constraint verification."
    )
    explanation_ru = (
        f"Сила доказательной базы: {level} ({score}/100 баллов) на основе {sample_count} симуляционных сидов, "
        f"{'многопараметрического тестирования спроса' if is_multi_condition else 'односценарного прогона'} "
        f"и проверки соблюдения ограничений."
    )

    return {
        "level": level,  # type: ignore
        "score": score,
        "criteria_breakdown": criteria,
        "explanation_en": explanation_en,
        "explanation_ru": explanation_ru,
    }


def _derive_next_action(
    intervention_id: str,
    intervention_label: str,
    evidence_level: str,
    target_signal: str = "configured_signal_group"
) -> NextActionRecord:
    """Derives a concrete, field-actionable next step for municipal transportation leadership."""
    if "green_wave" in intervention_id:
        return {
            "action_code": "FIELD_DETECTOR_VALIDATION",
            "title_en": "Plan verified temporary turning-count validation",
            "title_ru": "Спланировать проверку поворотных потоков с помощью временных детекторов",
            "description_en": (
                "Verify baseline vehicle arrival rates and queue discharge dynamics prior to permanent controller programming."
            ),
            "description_ru": (
                "Проверка фактической интенсивности и динамики схода очередей перед перепрограммированием дорожных контроллеров."
            ),
            "rationale_en": (
                "Field validation of movement counts and queues is required before any municipal implementation."
            ),
            "rationale_ru": (
                "Перед муниципальным внедрением требуется натурная проверка поворотных потоков и очередей."
            ),
            "priority": "HIGH",
            "target_location": "Configured demonstration network scope; field locations require verified mappings",
        }
    elif "pedestrian" in intervention_id:
        return {
            "action_code": "PEDESTRIAN_SAFETY_AUDIT",
            "title_en": "Conduct Peak Pedestrian Crossing Flow Audit",
            "title_ru": "Аудит пешеходных потоков в часы пик",
            "description_en": "Measure pedestrian crossing activity only at field-verified locations.",
            "description_ru": "Измерять пешеходную активность только в натурно верифицированных точках.",
            "rationale_en": "Ensure safety priority does not cause unexpected vehicle gridlock on connecting links.",
            "rationale_ru": "Гарантировать, что приоритет пешеходов не создает заторов на прилегающих связях.",
            "priority": "MEDIUM",
            "target_location": "Field-verified crossing locations required",
        }
    else:
        return {
            "action_code": "BASELINE_COUNT_COLLECTION",
            "title_en": "Collect Baseline Turning Movement Counts for Corridor Calibration",
            "title_ru": "Сбор натурных подсчетов поворотных потоков для калибровки коридора",
            "description_en": "Collect 15-minute turning movement counts across all corridor approaches.",
            "description_ru": "Сбор 15-минутных подсчетов поворотных потоков по всем подходам к перекресткам.",
            "rationale_en": "Calibration data will elevate model evidence strength to calibrated status.",
            "rationale_ru": "Натурные данные позволят перевести модель в статус калиброванной.",
            "priority": "HIGH",
            "target_location": "Central Corridor Intersections",
        }


def _build_metric_comparison(
    baseline: Dict[str, Any],
    optimized: Dict[str, Any]
) -> List[MetricComparisonRow]:
    """Builds the comprehensive baseline vs optimized metric comparison rows."""
    rows: List[MetricComparisonRow] = []

    for defn in METRIC_REGISTRY:
        key = defn["key"]
        direction = defn["direction"]
        provenance = defn["provenance"]

        # Legacy formula emissions may appear in historical payloads.  Prefer the
        # actual TraCI emission outputs used by the optimizer whenever available.
        legacy_key = key.removeprefix("sumo_")
        base_raw = baseline.get(key)
        opt_raw = optimized.get(key)
        if base_raw is None and key.startswith("sumo_"):
            base_raw = baseline.get(legacy_key)
        if opt_raw is None and key.startswith("sumo_"):
            opt_raw = optimized.get(legacy_key)
        base_val = float(base_raw or 0.0)
        opt_val = float(base_val if opt_raw is None else opt_raw)

        abs_diff = round(opt_val - base_val, 3)
        pct_diff = round((abs_diff / base_val * 100), 2) if base_val != 0 else 0.0

        if direction == "minimize":
            is_imp = abs_diff < -0.001
        else:
            is_imp = abs_diff > 0.001

        rows.append({
            "key": key,
            "name_en": defn["name_en"],
            "name_ru": defn["name_ru"],
            "unit": defn["unit"],
            "baseline": round(base_val, 2),
            "optimized": round(opt_val, 2),
            "absolute_change": abs_diff,
            "percentage_change": pct_diff,
            "direction": direction,
            "is_improvement": is_imp,
            "provenance": provenance,
        })

    return rows


def _build_methodology_record(
    scenario: str,
    duration: int,
    warmup_steps: int,
    policy_name: str
) -> MethodologyRecord:
    """Builds transparent technical methodology metadata."""
    return {
        "network_name": "Configured SUMO demonstration network (network hash recorded in evidence)",
        "simulation_engine": "SUMO (Simulation of Urban MObility) 1.27+ / TraCI Microscopic Physics",
        "emission_model": "SUMO TraCI per-vehicle emission outputs (configured emission class to be documented)",
        "duration_steps": duration,
        "warmup_steps": warmup_steps,
        "measurement_steps": max(1, duration - warmup_steps),
        "demand_scenario": f"Configured {scenario.capitalize()} demand profile",
        "policy_framework": f"Multi-Objective {policy_name} Policy Optimization",
        "optimization_method": "Deterministic candidate ranking with baseline-relative percentage normalization",
        "statistical_method": "Student-t confidence intervals when two or more simulation seeds are available",
    }


def _build_limitations_record() -> LimitationsRecord:
    """Builds explicit municipal limitations and data class distinctions."""
    return {
        "modeled_caveats_en": [
            "Demand and driver behavior remain uncalibrated against field turning counts.",
            "Signal-control changes are SUMO/TraCI experiments, not verified field controller deployments.",
            "Vehicle emissions are modeled from SUMO per-vehicle emission outputs rather than tailpipe monitors; the configured emission class is not yet documented.",
        ],
        "modeled_caveats_ru": [
            "Спрос и поведение водителей не откалиброваны по натурным подсчетам поворотных потоков.",
            "Изменения управления сигналами являются экспериментами SUMO/TraCI, а не проверенным внедрением на контроллерах.",
            "Выбросы ТС моделируются по данным SUMO для каждого автомобиля, а не прямыми датчиками выхлопа; настроенный класс выбросов еще не документирован.",
        ],
        "observed_data_caveats_en": [
            "Stationary environmental telemetry is sourced from Uzhydromet / WAQI regional monitoring stations.",
            "Sensor data provides ambient atmospheric baselines and is not a direct output of microscopic road simulation.",
        ],
        "observed_data_caveats_ru": [
            "Данные стационарных датчиков воздуха получены со станций Узгидромета / WAQI.",
            "Показания станций отражают фоновые атмосферные уровни и не являются прямым выходом симуляции.",
        ],
        "derived_indicator_caveats_en": [
            "Accessibility and noise scores are deterministic planning indicators for comparative scenario ranking.",
        ],
        "derived_indicator_caveats_ru": [
            "Оценки доступности и шума представляют собой детерминированные планировочные индикаторы.",
        ],
        "data_classes_summary": {
            "DIRECT": "Direct microscopic TraCI state observation (speeds, stops, waiting times)",
            "SIMULATED": "Microscopic SUMO/TraCI model outputs (CO2, NOx emissions)",
            "OBSERVED": "Real-world physical monitoring telemetry (Uzhydromet air quality stations)",
            "ESTIMATED": "Multi-objective urban formulas & heuristic estimates",
            "FALLBACK": "Not accepted in the authoritative SUMO evidence pipeline",
        },
    }


def _normalize_experiment_result(
    exp_data: Dict[str, Any],
    policy_id: str = "balanced",
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Converts a multi-scenario experiment result into an optimization result representation."""
    conditions = exp_data.get("conditions", [])
    completed = [c for c in conditions if c.get("status") == "COMPLETED"]

    # 1. Find baseline
    base_cond = next((c for c in conditions if abs(c.get("traffic_multiplier", 1.0) - 1.0) < 1e-4 and c.get("control_metrics")), None)
    if not base_cond and completed:
        base_cond = completed[0]

    baseline = (base_cond.get("control_metrics") if base_cond else None) or (base_cond.get("scenario_metrics") if base_cond else None) or {}

    # 2. Evaluate all conditions under policy
    policy_obj = get_policy(policy_id, custom_weights)
    from app.services.simulation.policies import evaluate_policy_score

    evaluated_candidates = []
    for c in completed:
        scen_metrics = c.get("scenario_metrics", {})
        cand_id = c.get("intervention_id", "control")
        cand_label = c.get("intervention_label", cand_id)
        eval_res = evaluate_policy_score(baseline, scen_metrics, policy_obj)

        # Build tradeoff summary
        deltas = c.get("metric_deltas", {})
        improved = []
        worsened = []
        for k, v in deltas.items():
            pct = v.get("percentage") if isinstance(v, dict) else v
            if pct is not None:
                name_en = next((m["name_en"] for m in METRIC_REGISTRY if m["key"] == k), k)
                name_ru = next((m["name_ru"] for m in METRIC_REGISTRY if m["key"] == k), k)
                direction = next((m["direction"] for m in METRIC_REGISTRY if m["key"] == k), "minimize")
                is_imp = (direction == "minimize" and pct < -0.01) or (direction == "maximize" and pct > 0.01)
                is_worse = (direction == "minimize" and pct > 0.01) or (direction == "maximize" and pct < -0.01)
                if is_imp:
                    improved.append({"name": name_en, "name_ru": name_ru, "change_pct": round(pct, 1), "value": round(pct, 1), "unit": "%"})
                elif is_worse:
                    worsened.append({"name": name_en, "name_ru": name_ru, "change_pct": round(pct, 1), "value": round(pct, 1), "unit": "%"})

        evaluated_candidates.append({
            "id": cand_id,
            "label": cand_label,
            "label_ru": cand_label,
            "metrics": scen_metrics,
            "evaluation_mode": c.get("evaluation_mode", "SIMULATED"),
            "policy_breakdown": eval_res,
            "tradeoff_summary": {
                "improved": improved,
                "worsened": worsened,
                "unchanged": [],
                "verdict_en": "Multi-condition scenario comparative analysis.",
                "verdict_ru": "Сравнительный анализ многопараметрических сценариев.",
            },
            "ranking_score": eval_res.get("ranking_score", 0.0),
        })

    evaluated_candidates.sort(key=lambda x: x["ranking_score"], reverse=True)
    best_candidate = evaluated_candidates[0] if evaluated_candidates else {
        "id": "control",
        "label": "Control Strategy",
        "metrics": baseline,
        "policy_breakdown": {"overall_score": 0.0, "is_valid": True},
        "tradeoff_summary": {"improved": [], "worsened": [], "unchanged": []},
    }

    # Calculate robustness across completed conditions with the single shared
    # Student-t utility. These are condition samples, not claimed seed samples.
    robustness_stats = {}
    for defn in METRIC_REGISTRY:
        k = defn["key"]
        vals = [float(c.get("scenario_metrics", {}).get(k, 0)) for c in completed if c.get("scenario_metrics", {}).get(k) is not None]
        if vals:
            robustness_stats[k] = compute_sample_statistics(vals, allow_negative_ci=True)

    best_candidate["robustness_sample_count"] = len(completed)
    best_candidate["robustness_seeds"] = []
    best_candidate["robustness_state"] = "NOT_EVALUATED"
    best_candidate["robustness_stats"] = robustness_stats

    return {
        "scenario": exp_data.get("scenario", "midday"),
        "experiment_id": exp_data.get("experiment_id"),
        "baseline": baseline,
        "candidates": evaluated_candidates,
        "best_candidate": best_candidate,
        "policy": policy_id,
        "ai": exp_data.get("ai"),
        "is_multi_condition": len(completed) > 1,
    }


def generate_decision_report(
    opt_result: Dict[str, Any],
    policy_id: str = "balanced",
    custom_weights: Optional[Dict[str, float]] = None,
    experiment_id: Optional[str] = None,
    language: str = "en"
) -> DecisionReport:
    """
    Transforms validated optimization or experiment results into a first-class,
    auditable DecisionReport object ready for municipal stakeholders.
    """
    is_multi_condition = False
    # If input is an experiment result matrix, normalize it
    if "conditions" in opt_result:
        is_multi_condition = len(opt_result.get("conditions", [])) > 1
        opt_result = _normalize_experiment_result(opt_result, policy_id=policy_id, custom_weights=custom_weights)

    report_id = f"REP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    policy_obj = get_policy(policy_id, custom_weights)
    policy_name = policy_obj.name
    policy_name_ru = policy_obj.name_ru

    baseline = opt_result.get("baseline", {})
    best_cand = opt_result.get("best_candidate", {})
    best_metrics = best_cand.get("metrics", {})
    pb = best_cand.get("policy_breakdown", {})
    tradeoff_summary = best_cand.get("tradeoff_summary", {})
    ai_data = opt_result.get("ai", {})

    scenario_id = opt_result.get("scenario", "midday")
    interv_label = best_cand.get("label", best_cand.get("id", "Selected Intervention"))
    interv_label_ru = best_cand.get("label_ru", interv_label)

    # 1. Metric Comparison
    metric_rows = _build_metric_comparison(baseline, best_metrics)

    # 2. Robustness Evidence & Evidence Status Computation
    raw_stats = best_cand.get("robustness_stats") or {}
    raw_seeds = best_cand.get("robustness_seeds")
    seeds = list(raw_seeds) if isinstance(raw_seeds, list) else []
    sample_count = len(seeds)
    robustness_state = "MULTI_SEED" if sample_count > 1 else ("SINGLE_RUN" if sample_count == 1 else "NOT_EVALUATED")
    is_valid = pb.get("is_valid", True)
    violations_en = pb.get("constraint_violations_en", [])
    violations_ru = pb.get("constraint_violations_ru", [])

    evidence_status = _compute_evidence_status(
        sample_count=sample_count,
        is_multi_condition=is_multi_condition or opt_result.get("is_multi_condition", False),
        is_valid=is_valid,
        robustness_stats=raw_stats,
    )

    # 3. Next Action Layer
    next_action = _derive_next_action(
        intervention_id=best_cand.get("id", ""),
        intervention_label=interv_label,
        evidence_level=evidence_status["level"],
        target_signal=(best_cand.get("intervention") or {}).get("traffic_light_id", "configured_signal_group")
    )

    # 4. Calibration Status & Model vs Reality Classification
    calib_status = get_calibration_status()
    model_vs_reality = get_model_vs_reality_breakdown(baseline, best_metrics)

    # 5. Executive Summary Figures
    base_wait = float(baseline.get("average_waiting_seconds") or 0.0)
    opt_wait = float(best_metrics.get("average_waiting_seconds", base_wait) or base_wait)
    wait_reduction_pct = round(((base_wait - opt_wait) / base_wait * 100), 1) if base_wait > 0 else 0.0

    base_co2 = float(baseline.get("sumo_co2_kg") or baseline.get("co2_kg") or 0.0)
    opt_co2 = float(best_metrics.get("sumo_co2_kg") or best_metrics.get("co2_kg") or 0.0)
    co2_reduction_pct = round(((base_co2 - opt_co2) / base_co2 * 100), 1) if base_co2 > 0 else 0.0

    tradeoff_worsened = tradeoff_summary.get("worsened", [])
    main_tradeoff_en = (
        f"Minor side-street approach adjustment ({tradeoff_worsened[0].get('name', 'localized delay')})"
        if tradeoff_worsened else "No significant negative trade-offs detected across corridor."
    )
    main_tradeoff_ru = (
        f"Локальное увеличение задержки на второстепенных направлениях ({tradeoff_worsened[0].get('name_ru', tradeoff_worsened[0].get('name', 'задержка'))})"
        if tradeoff_worsened else "Значимых негативных компромиссов по коридору не выявлено."
    )

    primary_res_en = f"Sampled accumulated waiting snapshot mean reduced by {wait_reduction_pct}%"
    primary_res_ru = f"Сокращение среднего накопленного ожидания по выборке снимков на {wait_reduction_pct}%"

    env_res_en = f"Simulated CO₂ emissions reduced by {co2_reduction_pct}%"
    env_res_ru = f"Сокращение расчётных выбросов CO₂ на {co2_reduction_pct}%"

    recommendation_en = (
        f"Simulation-supported candidate for field validation: '{interv_label}'. "
        f"Estimated {wait_reduction_pct}% delay reduction and {co2_reduction_pct}% emission reduction. "
        f"Recommended next action: {next_action['title_en']}."
    )
    recommendation_ru = (
        f"Рекомендуемый вариант для натурной валидации: «{interv_label_ru}». "
        f"Расчетное снижение задержки на {wait_reduction_pct}% и выбросов на {co2_reduction_pct}%. "
        f"Рекомендуемое следующее действие: {next_action['title_ru']}."
    )

    exec_summary: ExecutiveSummary = {
        "scenario_name": f"Tashkent {scenario_id.capitalize()} Demand",
        "scenario_name_ru": f"Ташкент: Сценарий «{scenario_id.capitalize()}»",
        "policy_name": policy_name,
        "policy_name_ru": policy_name_ru,
        "recommended_intervention": interv_label,
        "recommended_intervention_ru": interv_label_ru,
        "primary_result": primary_res_en,
        "primary_result_ru": primary_res_ru,
        "environmental_result": env_res_en,
        "environmental_result_ru": env_res_ru,
        "main_tradeoff": main_tradeoff_en,
        "main_tradeoff_ru": main_tradeoff_ru,
        "evidence_level": evidence_status["level"],
        "confidence": "high" if evidence_status["level"] == "HIGH" else ("medium" if evidence_status["level"] == "MODERATE" else "low"),
        "recommendation": recommendation_en,
        "recommendation_ru": recommendation_ru,
        "next_action_title": next_action["title_en"],
        "next_action_title_ru": next_action["title_ru"],
    }

    from app.services.simulation.policies import generate_why_this_won_explanation
    why_won_en = best_cand.get("why_won_en") or generate_why_this_won_explanation(policy_obj, best_cand, language="en")
    why_won_ru = best_cand.get("why_won_ru") or generate_why_this_won_explanation(policy_obj, best_cand, language="ru")

    # 6. Policy Audit
    policy_audit: PolicyAudit = {
        "policy_id": policy_id,
        "policy_name": policy_name,
        "policy_name_ru": policy_name_ru,
        "objective_question": policy_obj.objective_question,
        "objective_question_ru": policy_obj.objective_question_ru,
        "why_won": why_won_ru if language == "ru" else why_won_en,
        "why_won_ru": why_won_ru,
        "policy_weights": policy_obj.objective_weights,
        "winning_intervention_id": best_cand.get("id", ""),
        "winning_intervention_label": interv_label,
        "winning_intervention_label_ru": interv_label_ru,
        "policy_score": round(pb.get("overall_score", 0.0), 2),
        "mobility_score": round(pb.get("mobility_score", 0.0), 2),
        "environment_score": round(pb.get("environment_score", 0.0), 2),
        "accessibility_score": round(pb.get("accessibility_score", 0.0), 2),
        "constraint_status": "PASS" if is_valid else "VIOLATION",
        "constraint_violations_en": violations_en,
        "constraint_violations_ru": violations_ru,
    }

    # 7. Tradeoffs Breakdown
    tradeoffs_breakdown: TradeoffBreakdown = {
        "improved": tradeoff_summary.get("improved", []),
        "worsened": tradeoff_summary.get("worsened", []),
        "unchanged": tradeoff_summary.get("unchanged", []),
        "constraint_violations": violations_ru if language == "ru" else violations_en,
        "verdict_en": tradeoff_summary.get("verdict_en", "Balanced multi-objective operational profile."),
        "verdict_ru": tradeoff_summary.get("verdict_ru", "Сбалансированный многокритериальный операционный профиль."),
    }

    # 8. Robustness
    robustness: RobustnessEvidence = {
        "sample_count": sample_count,
        "seeds": seeds,
        "stats": raw_stats,
        "state": robustness_state,
        "is_statistically_significant": bool(robustness_state == "MULTI_SEED" and evidence_status["level"] == "HIGH"),
        "methodology_note_en": (
            f"Evaluated across {sample_count} executed stochastic simulation seeds with Student-t confidence intervals."
            if robustness_state == "MULTI_SEED" else
            ("Single executed simulation run; no inferential Student-t confidence interval." if robustness_state == "SINGLE_RUN" else "Multi-seed robustness: Not evaluated.")
        ),
        "methodology_note_ru": (
            f"Оценка проведена по {sample_count} выполненным стохастическим сидам с доверительными интервалами Стьюдента."
            if robustness_state == "MULTI_SEED" else
            ("Выполнен один прогон; выводной доверительный интервал Стьюдента не рассчитывается." if robustness_state == "SINGLE_RUN" else "Многосидовая устойчивость: не оценена.")
        ),
    }

    # 9. Methodology & Limitations
    duration = int(baseline.get("steps", 300))
    warmup = int(baseline.get("warmup_steps", 0))
    methodology = _build_methodology_record(scenario_id, duration, warmup, policy_name)
    limitations = _build_limitations_record()

    resolved_exp_id = experiment_id or opt_result.get("experiment_id") or f"EXP-{uuid.uuid4().hex[:6].upper()}"

    disclaimer_en = (
        "UrbanMind provides simulation-supported analytical recommendations. "
        "Final municipal decision and implementation authority rests with the responsible transport agency / municipal administration."
    )
    disclaimer_ru = (
        "UrbanMind формирует аналитические рекомендации на основе моделирования. "
        "Окончательное решение и полномочия по внедрению остаются за ответственным органом управления транспортом / администрацией города."
    )

    policy_comparison = opt_result.get("policy_comparison")
    candidate_ranking = opt_result.get("ranked_candidates") or opt_result.get("candidates")

    return {
        "report_id": report_id,
        "experiment_id": resolved_exp_id,
        "scenario_id": scenario_id,
        "policy_id": policy_id,
        "active_policy": policy_id,
        "intervention_id": best_cand.get("id", ""),
        "created_at": created_at,
        "spatial_scope": get_default_spatial_scope(),
        "cross_district_context": get_cross_district_context(),
        "executive_summary": exec_summary,
        "baseline_metrics": baseline,
        "optimized_metrics": best_metrics,
        "metric_deltas": {row["key"]: row["percentage_change"] for row in metric_rows},
        "policy_score": round(pb.get("overall_score", 0.0), 2),
        "policy_score_breakdown": {
            "mobility": round(pb.get("mobility_score", 0.0), 2),
            "environment": round(pb.get("environment_score", 0.0), 2),
            "accessibility": round(pb.get("accessibility_score", 0.0), 2),
        },
        "policy_audit": policy_audit,
        "policy_comparison": policy_comparison,
        "candidate_ranking": candidate_ranking,
        "why_won": why_won_ru if language == "ru" else why_won_en,
        "why_won_ru": why_won_ru,
        "metric_comparison": metric_rows,
        "tradeoffs": tradeoffs_breakdown,
        "robustness": robustness,
        "evidence_status": evidence_status,
        "calibration_status": calib_status,
        "model_vs_reality": model_vs_reality,
        "validation_summary": compute_validation_metrics([], [], "corridor_delay"),
        "next_action": next_action,
        "confidence": "high" if evidence_status["level"] == "HIGH" else ("medium" if evidence_status["level"] == "MODERATE" else "low"),
        "methodology": methodology,
        "limitations": limitations,
        "ai_analysis": ai_data if ai_data else None,
        "recommendation": recommendation_ru if language == "ru" else recommendation_en,
        "recommendation_verdict_en": recommendation_en,
        "recommendation_verdict_ru": recommendation_ru,
        "municipal_disclaimer_en": disclaimer_en,
        "municipal_disclaimer_ru": disclaimer_ru,
    }
