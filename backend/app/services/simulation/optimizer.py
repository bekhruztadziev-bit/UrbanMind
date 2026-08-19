from typing import Any, List, Tuple

from app.services.simulation.models import SimulationMetrics, CandidateResult, OptimizationResult, CandidateDelta
from app.services.simulation.interventions import get_intervention_effect_summary, INTERVENTION_LABELS_RU, INTERVENTION_CATEGORIES_RU


def _candidate_score(metrics: SimulationMetrics) -> float:
    """Lower is better. The score balances operational delay, environmental cost, and mobility access."""
    waiting = float(metrics.get("average_waiting_seconds", 0.0))
    speed = float(metrics.get("average_speed_kmh", 0.0))
    co2 = float(metrics.get("co2_kg", 0.0))
    pedestrian_delay = float(metrics.get("pedestrian_delay_seconds", 0.0))
    access = float(metrics.get("accessibility_score", 100.0))
    stops = float(metrics.get("stops_per_vehicle", 1.0))
    queue = float(metrics.get("mean_queue_length_meters", 30.0))
    return (waiting * 0.45) - (speed * 0.15) + (co2 * 0.18) + (stops * 4.0) + (queue * 0.05) + (pedestrian_delay * 0.08) - (access * 0.12)


def evaluate_candidates(baseline: SimulationMetrics, candidate_results: List[Tuple[dict[str, Any], SimulationMetrics]], language: str = "en") -> List[CandidateResult]:
    candidates = []
    base_speed = float(baseline.get("average_speed_kmh", 1.0) or 1.0)
    base_wait = float(baseline.get("average_waiting_seconds", 1.0) or 1.0)
    base_tt = float(baseline.get("average_travel_time_seconds", 1.0) or 1.0)
    base_queue = float(baseline.get("mean_queue_length_meters", 1.0) or 1.0)
    base_stops = float(baseline.get("stops_per_vehicle", 1.0) or 1.0)
    base_tp = float(baseline.get("throughput_vehicles_per_hour", 1.0) or 1.0)
    base_co2 = float(baseline.get("co2_kg", 1.0) or 1.0)

    for entry, metrics in candidate_results:
        cand_speed = float(metrics.get("average_speed_kmh", 0.0) or 0.0)
        cand_wait = float(metrics.get("average_waiting_seconds", 0.0) or 0.0)
        cand_tt = float(metrics.get("average_travel_time_seconds", 0.0) or 0.0)
        cand_queue = float(metrics.get("mean_queue_length_meters", 0.0) or 0.0)
        cand_stops = float(metrics.get("stops_per_vehicle", 0.0) or 0.0)
        cand_tp = float(metrics.get("throughput_vehicles_per_hour", 0.0) or 0.0)
        cand_co2 = float(metrics.get("co2_kg", 0.0) or 0.0)

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
        summary = get_intervention_effect_summary(category, action_text, wait_change, language=language)
        label_display = INTERVENTION_LABELS_RU.get(action_text, action_text) if language == "ru" else action_text

        clean_intervention = {
            "type": entry.get("type"),
            "category": category,
            "label": action_text,
            "seconds": int(entry.get("seconds", 0)),
            "traffic_light_id": entry.get("traffic_light_id"),
            "phase_index": entry.get("phase_index"),
            "evaluation_mode": entry.get("evaluation_mode", "HEURISTIC"),
        }

        candidate: CandidateResult = {
            "id": f"{entry.get('type')}_{entry.get('seconds', 0)}s_{category}",
            "label": label_display,
            "label_en": action_text,
            "label_ru": INTERVENTION_LABELS_RU.get(action_text, action_text),
            "category": category,
            "category_label": INTERVENTION_CATEGORIES_RU.get(category, category) if language == "ru" else category,
            "type": entry.get("type", ""),
            "description": summary,
            "summary": summary,
            "evaluation_mode": entry.get("evaluation_mode", "HEURISTIC"),
            "intervention": clean_intervention,
            "metrics": metrics,
            "delta": delta,
            "score": _candidate_score(metrics),
        }
        candidates.append(candidate)
    return candidates


def rank_candidates(scenario: str, baseline: SimulationMetrics, candidates: List[CandidateResult], language: str = "en") -> OptimizationResult:
    ranked = sorted(candidates, key=lambda item: (item["score"], item["metrics"]["average_waiting_seconds"], -item["metrics"]["average_speed_kmh"]))
    best = ranked[0]
    
    if best.get("type") == "green_wave_coordination":
        reason_ru = "Выбрано, так как координация фаз коридора обеспечивает максимальное сокращение времени в пути и числа остановок по всей центральной оси Ташкента."
        reason_en = "Selected because green-wave corridor coordination minimizes travel time and stop frequency across the primary central Tashkent corridor."
    elif language == "ru":
        reason_ru = "Выбрано, так как обеспечивает оптимальный баланс задержек, выбросов и доступности по всему району."
        reason_en = "Selected because it balances delay, emissions, and accessibility across the neighborhood."
    else:
        reason_ru = "Выбрано на основе многокритериальной оптимизации задержек и выбросов."
        reason_en = "Selected because it balances delay, emissions, and accessibility across the neighborhood instead of optimizing only for a single junction."

    best["selected_reason"] = reason_ru if language == "ru" else reason_en
    best["selected_reason_ru"] = reason_ru

    return {
        "scenario": scenario,
        "baseline": baseline,
        "candidates": candidates,
        "ranked_candidates": ranked,
        "best_candidate": best,
    }
