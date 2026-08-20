from typing import Any, List, Tuple, Dict, Optional

from app.services.simulation.models import (
    SimulationMetrics, CandidateResult, OptimizationResult, CandidateDelta, TradeoffSummary,
    PolicyScoreBreakdown, PolicyComparisonItem
)
from app.services.simulation.interventions import get_intervention_effect_summary, INTERVENTION_LABELS_RU, INTERVENTION_CATEGORIES_RU
from app.services.simulation.policies import get_policy, evaluate_policy_score, PolicyDefinition, POLICIES


def analyze_tradeoffs(delta: CandidateDelta, language: str = "en") -> TradeoffSummary:
    """
    Categorize metrics into improved, worsened, and unchanged dimensions based on semantic direction.
    """
    improved: List[Dict[str, Any]] = []
    worsened: List[Dict[str, Any]] = []
    unchanged: List[Dict[str, Any]] = []

    metrics_config = [
        {"key": "average_waiting_seconds", "name_en": "Delay", "name_ru": "Задержка", "unit": "s", "higher_is_better": False, "pct_key": "delay_improvement_pct"},
        {"key": "average_travel_time_seconds", "name_en": "Travel Time", "name_ru": "Время в пути", "unit": "s", "higher_is_better": False, "pct_key": "travel_time_improvement_pct"},
        {"key": "stops_per_vehicle", "name_en": "Stops / Veh", "name_ru": "Остановок на автомобиль", "unit": "", "higher_is_better": False, "pct_key": "stops_improvement_pct"},
        {"key": "mean_queue_length_meters", "name_en": "Queue Length", "name_ru": "Длина очереди", "unit": "m", "higher_is_better": False, "pct_key": "queue_improvement_pct"},
        {"key": "throughput_vehicles_per_hour", "name_en": "Throughput", "name_ru": "Пропускная способность", "unit": "veh/h", "higher_is_better": True, "pct_key": "throughput_improvement_pct"},
        {"key": "co2_kg", "name_en": "CO₂ Emissions", "name_ru": "Выбросы CO₂", "unit": "kg", "higher_is_better": False, "pct_key": "emissions_improvement_pct"},
    ]

    for m in metrics_config:
        pct = delta.get(m["pct_key"]) if m.get("pct_key") else None
        name = m["name_ru"] if language == "ru" else m["name_en"]

        if pct is not None:
            val_pct = float(pct)
            item_data = {
                "name": name,
                "name_en": m["name_en"],
                "name_ru": m["name_ru"],
                "change_pct": val_pct,
                "metric": m["key"],
            }
            if val_pct > 2.0:
                improved.append(item_data)
            elif val_pct < -2.0:
                worsened.append(item_data)
            else:
                unchanged.append(item_data)

    if len(improved) >= 3 and len(worsened) == 0:
        verdict_en = "Uniform corridor improvement across all operational and environmental dimensions."
        verdict_ru = "Комплексное улучшение показателей коридора по всем транспортным и экологическим параметрам."
    elif len(improved) > len(worsened):
        verdict_en = f"Net positive corridor performance: {len(improved)} indicators improved with manageable trade-offs in {len(worsened)}."
        verdict_ru = f"Положительный суммарный эффект: улучшение по {len(improved)} ключевым метрикам при умеренных компромиссах в {len(worsened)}."
    elif len(worsened) > len(improved):
        verdict_en = "Trade-off heavy: benefits in specific areas are offset by increased delays elsewhere."
        verdict_ru = "Высокая цена компромисса: локальные улучшения нивелируются ростом задержек на других участках."
    else:
        verdict_en = "Balanced operational profile with minor trade-offs."
        verdict_ru = "Сбалансированный профиль с незначительными изменениями параметров."

    return {
        "improved": improved,
        "worsened": worsened,
        "unchanged": unchanged,
        "verdict_en": verdict_en,
        "verdict_ru": verdict_ru,
    }


def evaluate_candidates(
    baseline: SimulationMetrics,
    candidate_results: List[Tuple[dict[str, Any], SimulationMetrics]],
    policy_id: str = "balanced",
    custom_weights: Optional[Dict[str, float]] = None,
    language: str = "en"
) -> List[CandidateResult]:
    """
    Evaluate candidate interventions against the baseline under the selected optimization policy.
    Computes normalized multi-objective dimensional scores and constraint compliance.
    """
    policy = get_policy(policy_id, custom_weights)
    candidates = []
    base_speed = float(baseline.get("average_speed_kmh", 1.0) or 1.0)
    base_wait = float(baseline.get("average_waiting_seconds", 1.0) or 1.0)
    base_tt = float(baseline.get("average_travel_time_seconds", 1.0) or 1.0)
    base_queue = float(baseline.get("mean_queue_length_meters", 1.0) or 1.0)
    base_stops = float(baseline.get("stops_per_vehicle", 1.0) or 1.0)
    base_tp = float(baseline.get("throughput_vehicles_per_hour", 1.0) or 1.0)
    base_co2 = float(baseline.get("sumo_co2_kg", 0.0) or 0.0)

    for entry, metrics in candidate_results:
        cand_speed = float(metrics.get("average_speed_kmh", 0.0) or 0.0)
        cand_wait = float(metrics.get("average_waiting_seconds", 0.0) or 0.0)
        cand_tt = float(metrics.get("average_travel_time_seconds", 0.0) or 0.0)
        cand_queue = float(metrics.get("mean_queue_length_meters", 0.0) or 0.0)
        cand_stops = float(metrics.get("stops_per_vehicle", 0.0) or 0.0)
        cand_tp = float(metrics.get("throughput_vehicles_per_hour", 0.0) or 0.0)
        cand_co2 = float(metrics.get("sumo_co2_kg", 0.0) or 0.0)

        # Percentage improvements (positive = improvement)
        delay_imp = round(((base_wait - cand_wait) / base_wait) * 100.0, 1) if base_wait > 0 else 0.0
        tt_imp = round(((base_tt - cand_tt) / base_tt) * 100.0, 1) if base_tt > 0 else 0.0
        queue_imp = round(((base_queue - cand_queue) / base_queue) * 100.0, 1) if base_queue > 0 else 0.0
        stops_imp = round(((base_stops - cand_stops) / base_stops) * 100.0, 1) if base_stops > 0 else 0.0
        tp_imp = round(((cand_tp - base_tp) / base_tp) * 100.0, 1) if base_tp > 0 else 0.0
        co2_imp = round(((base_co2 - cand_co2) / base_co2) * 100.0, 1) if base_co2 > 0 else 0.0

        delta: CandidateDelta = {
            "average_speed_kmh": round(cand_speed - base_speed, 2),
            "average_waiting_seconds": round(cand_wait - base_wait, 2),
            "average_travel_time_seconds": round(cand_tt - base_tt, 2),
            "mean_queue_length_meters": round(cand_queue - base_queue, 2),
            "stops_per_vehicle": round(cand_stops - base_stops, 2),
            "throughput_vehicles_per_hour": round(cand_tp - base_tp, 1),
            "mean_completed_vehicle_waiting_seconds": round((metrics.get("mean_completed_vehicle_waiting_seconds") or 0.0) - (baseline.get("mean_completed_vehicle_waiting_seconds") or 0.0), 2) if metrics.get("mean_completed_vehicle_waiting_seconds") is not None else None,
            "max_vehicle_count": metrics.get("max_vehicle_count", 0) - baseline.get("max_vehicle_count", 0),
            "co2_kg": round(cand_co2 - base_co2, 2),
            "nox_g": round((metrics.get("nox_g", 0.0) or 0.0) - (baseline.get("nox_g", 0.0) or 0.0), 2),
            "noise_db": round((metrics.get("noise_db", 0.0) or 0.0) - (baseline.get("noise_db", 0.0) or 0.0), 2),
            "pedestrian_delay_seconds": round((metrics.get("pedestrian_delay_seconds", 0.0) or 0.0) - (baseline.get("pedestrian_delay_seconds", 0.0) or 0.0), 2),
            "accessibility_score": round((metrics.get("accessibility_score", 0.0) or 0.0) - (baseline.get("accessibility_score", 0.0) or 0.0), 2),
            "sumo_co2_kg": round((metrics.get("sumo_co2_kg", 0.0) or 0.0) - (baseline.get("sumo_co2_kg", 0.0) or 0.0), 4),
            "sumo_nox_g": round((metrics.get("sumo_nox_g", 0.0) or 0.0) - (baseline.get("sumo_nox_g", 0.0) or 0.0), 4),
            "delay_improvement_pct": delay_imp,
            "travel_time_improvement_pct": tt_imp,
            "queue_improvement_pct": queue_imp,
            "stops_improvement_pct": stops_imp,
            "throughput_improvement_pct": tp_imp,
            "emissions_improvement_pct": co2_imp,
        }

        category = entry.get("category", "mobility")
        action_text = entry.get("label", entry.get("type", "unknown").replace("_", " ").title())
        wait_change = abs(delta["average_waiting_seconds"])
        summary_en = get_intervention_effect_summary(category, action_text, wait_change, language="en")
        summary_ru = get_intervention_effect_summary(category, action_text, wait_change, language="ru")
        summary = summary_ru if language == "ru" else summary_en
        label_ru = INTERVENTION_LABELS_RU.get(action_text, action_text)
        label_display = label_ru if language == "ru" else action_text

        clean_intervention = {
            "type": entry.get("type"),
            "category": category,
            "label": action_text,
            "seconds": int(entry.get("seconds", 0)),
            "traffic_light_id": entry.get("traffic_light_id"),
            "phase_index": entry.get("phase_index"),
            "evaluation_mode": entry.get("evaluation_mode", "HEURISTIC"),
        }

        tradeoff = analyze_tradeoffs(delta, language=language)
        policy_eval = evaluate_policy_score(baseline, metrics, policy)

        candidate: CandidateResult = {
            "id": f"{entry.get('type')}_{entry.get('seconds', 0)}s_{category}",
            "label": label_display,
            "label_en": action_text,
            "label_ru": label_ru,
            "category": category,
            "category_label": INTERVENTION_CATEGORIES_RU.get(category, category) if language == "ru" else category,
            "category_ru": INTERVENTION_CATEGORIES_RU.get(category, category),
            "type": entry.get("type", ""),
            "description": summary,
            "summary": summary,
            "summary_en": summary_en,
            "summary_ru": summary_ru,
            "evaluation_mode": entry.get("evaluation_mode", "HEURISTIC"),
            "intervention": clean_intervention,
            "metrics": metrics,
            "delta": delta,
            "score": policy_eval["overall_score"],
            "tradeoff_summary": tradeoff,
            "policy_breakdown": policy_eval,
        }
        candidates.append(candidate)
    return candidates


def compute_policy_comparison(
    baseline: SimulationMetrics,
    candidate_results: List[Tuple[dict[str, Any], SimulationMetrics]],
    custom_weights: Optional[Dict[str, float]] = None,
    language: str = "en"
) -> Dict[str, PolicyComparisonItem]:
    """
    Evaluate candidate pool under FLOW, ECO, and BALANCED policies (and CUSTOM if configured)
    to demonstrate how differing municipal priorities shift the recommended optimal intervention.
    """
    comparison: Dict[str, PolicyComparisonItem] = {}
    from app.services.simulation.policies import generate_why_this_won_explanation

    policy_ids = ["flow", "eco", "balanced"]
    if custom_weights:
        policy_ids.append("custom")

    for pid in policy_ids:
        policy = get_policy(pid, custom_weights=custom_weights if pid == "custom" else None)
        evaluated = evaluate_candidates(
            baseline,
            candidate_results,
            policy_id=pid,
            custom_weights=custom_weights if pid == "custom" else None,
            language=language
        )
        ranked = sorted(evaluated, key=lambda c: (
            c.get("policy_breakdown", {}).get("ranking_score", c["score"]),
            -c["metrics"].get("average_waiting_seconds", 0.0),
            c["metrics"].get("average_speed_kmh", 0.0)
        ), reverse=True)
        best = ranked[0]
        pb = best.get("policy_breakdown", {})
        delta = best.get("delta", {})

        why_won_en = generate_why_this_won_explanation(policy, best, language="en")
        why_won_ru = generate_why_this_won_explanation(policy, best, language="ru")

        comparison[pid] = {
            "policy_id": pid,
            "policy_name": policy.name,
            "policy_name_ru": policy.name_ru,
            "icon": policy.icon,
            "objective_question": policy.objective_question,
            "objective_question_ru": policy.objective_question_ru,
            "why_won": why_won_ru if language == "ru" else why_won_en,
            "why_won_en": why_won_en,
            "why_won_ru": why_won_ru,
            "best_candidate_id": best["id"],
            "best_candidate_label": best["label_ru"] if language == "ru" else best["label_en"],
            "best_candidate_score": pb.get("overall_score", best["score"]),
            "overall_score": pb.get("overall_score", best["score"]),
            "mobility_score": pb.get("mobility_score", 0.0),
            "environment_score": pb.get("environment_score", 0.0),
            "accessibility_score": pb.get("accessibility_score", 0.0),
            "average_waiting_seconds": float(best["metrics"].get("average_waiting_seconds", 0.0)),
            "average_travel_time_seconds": float(best["metrics"].get("average_travel_time_seconds", 0.0)),
            # Policy scoring and comparison expose the same TraCI/SUMO CO2
            # metric. Legacy derived co2_kg is intentionally not used here.
            "sumo_co2_kg": float(best["metrics"].get("sumo_co2_kg", 0.0)),
            "throughput_vehicles_per_hour": float(best["metrics"].get("throughput_vehicles_per_hour", 0.0)),
            "stops_per_vehicle": float(best["metrics"].get("stops_per_vehicle", 0.0)),
            "delay_improvement_pct": float(delta.get("delay_improvement_pct", 0.0)),
            "emissions_improvement_pct": float(delta.get("emissions_improvement_pct", 0.0)),
            "throughput_improvement_pct": float(delta.get("throughput_improvement_pct", 0.0)),
            "stops_improvement_pct": float(delta.get("stops_improvement_pct", 0.0)),
            "winner": best,
            "ranking": ranked,
            "tradeoffs": best.get("tradeoff_summary"),
        }

    return comparison


def rank_candidates(
    scenario: str,
    baseline: SimulationMetrics,
    candidates: List[CandidateResult],
    policy_id: str = "balanced",
    custom_weights: Optional[Dict[str, float]] = None,
    language: str = "en"
) -> OptimizationResult:
    """
    Rank candidate interventions under the selected policy.
    Sorts in descending order of ranking_score (higher positive score is better).
    """
    from app.services.simulation.policies import generate_why_this_won_explanation
    policy = get_policy(policy_id, custom_weights)
    
    # Sort candidates by ranking_score descending (higher composite improvement is better)
    ranked = sorted(
        candidates,
        key=lambda item: (
            item.get("policy_breakdown", {}).get("ranking_score", item["score"]),
            -item["metrics"]["average_waiting_seconds"],
            item["metrics"]["average_speed_kmh"]
        ),
        reverse=True
    )
    best = ranked[0]
    
    why_won_en = generate_why_this_won_explanation(policy, best, language="en")
    why_won_ru = generate_why_this_won_explanation(policy, best, language="ru")

    best["selected_reason"] = why_won_ru if language == "ru" else why_won_en
    best["selected_reason_ru"] = why_won_ru
    best["selected_reason_en"] = why_won_en
    best["why_won"] = why_won_ru if language == "ru" else why_won_en
    best["why_won_ru"] = why_won_ru
    best["why_won_en"] = why_won_en

    return {
        "scenario": scenario,
        "policy": policy.policy_id,
        "policy_definition": {
            "policy_id": policy.policy_id,
            "name": policy.name,
            "name_ru": policy.name_ru,
            "description": policy.description,
            "description_ru": policy.description_ru,
            "icon": policy.icon,
            "objective_question": policy.objective_question,
            "objective_question_ru": policy.objective_question_ru,
            "primary_dimensions": policy.primary_dimensions,
            "objective_weights": policy.objective_weights,
            "normalization_method": policy.normalization_method,
        },
        "baseline": baseline,
        "candidates": candidates,
        "ranked_candidates": ranked,
        "best_candidate": best,
        "why_won": why_won_ru if language == "ru" else why_won_en,
        "why_won_ru": why_won_ru,
        "why_won_en": why_won_en,
    }
