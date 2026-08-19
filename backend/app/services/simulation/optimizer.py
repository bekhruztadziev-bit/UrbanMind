from typing import Any, List, Tuple

from app.services.simulation.models import SimulationMetrics, CandidateResult, OptimizationResult
from app.services.simulation.interventions import get_intervention_effect_summary, INTERVENTION_LABELS_RU, INTERVENTION_CATEGORIES_RU


def _candidate_score(metrics: SimulationMetrics) -> float:
    """Lower is better. The score balances operational delay, environmental cost, and mobility access."""
    waiting = float(metrics.get("average_waiting_seconds", 0.0))
    speed = float(metrics.get("average_speed_kmh", 0.0))
    co2 = float(metrics.get("co2_kg", 0.0))
    pedestrian_delay = float(metrics.get("pedestrian_delay_seconds", 0.0))
    access = float(metrics.get("accessibility_score", 100.0))
    return (waiting * 0.55) - (speed * 0.18) + (co2 * 0.22) + (pedestrian_delay * 0.1) - (access * 0.15)


def evaluate_candidates(baseline: SimulationMetrics, candidate_results: List[Tuple[dict[str, Any], SimulationMetrics]], language: str = "en") -> List[CandidateResult]:
    candidates = []
    for entry, metrics in candidate_results:
        delta = {
            "average_speed_kmh": round(metrics["average_speed_kmh"] - baseline["average_speed_kmh"], 2),
            "average_waiting_seconds": round(metrics["average_waiting_seconds"] - baseline["average_waiting_seconds"], 2),
            "mean_completed_vehicle_time_loss_seconds": round((metrics.get("mean_completed_vehicle_time_loss_seconds") or 0) - (baseline.get("mean_completed_vehicle_time_loss_seconds") or 0), 2) if metrics.get("mean_completed_vehicle_time_loss_seconds") is not None else None,
            "mean_active_vehicle_time_loss_seconds": round((metrics.get("mean_active_vehicle_time_loss_seconds") or 0) - (baseline.get("mean_active_vehicle_time_loss_seconds") or 0), 2) if metrics.get("mean_active_vehicle_time_loss_seconds") is not None else None,
            "max_vehicle_count": metrics["max_vehicle_count"] - baseline["max_vehicle_count"],
            "co2_kg": round(metrics["co2_kg"] - baseline["co2_kg"], 2),
            "nox_g": round(metrics["nox_g"] - baseline["nox_g"], 2),
            "noise_db": round(metrics["noise_db"] - baseline["noise_db"], 2),
            "pedestrian_delay_seconds": round(metrics["pedestrian_delay_seconds"] - baseline["pedestrian_delay_seconds"], 2),
            "accessibility_score": round(metrics["accessibility_score"] - baseline["accessibility_score"], 2),
        }

        category = entry.get("category", "mobility")
        action_text = entry.get("label", entry.get("type", "unknown").replace("_", " ").title())
        wait_change = abs(delta["average_waiting_seconds"])
        summary = get_intervention_effect_summary(category, action_text, wait_change, language=language)
        label_display = INTERVENTION_LABELS_RU.get(action_text, action_text) if language == "ru" else action_text

        # Create a clean intervention def to return
        clean_intervention = {
            "type": entry.get("type"),
            "category": category,
            "seconds": int(entry.get("seconds", 0)),
            "traffic_light_id": entry.get("traffic_light_id"),
            "phase_index": entry.get("phase_index"),
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
    if language == "ru":
        best["selected_reason"] = (
            "Выбрано, так как обеспечивает баланс между задержками, выбросами и доступностью по всему району, а не только на отдельном перекрестке."
        )
    else:
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
