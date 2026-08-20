from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env", override=True)
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=True)


def _rule_based_summary(
    baseline: dict[str, Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    best: dict[str, Any] | None = None,
    experiment_context: dict[str, Any] | None = None,
    language: str = "en"
) -> dict[str, Any]:
    """
    Deterministic rule-based summary when AI provider credentials are not available or fail.
    Explicitly labeled as RULE-BASED SUMMARY (never pretended to be AI).
    """
    base = baseline or {}
    cands = candidates or []
    best_obj = best or {}

    best_name = best_obj.get("label") or best_obj.get("id") or "Intervention"
    signal_id = (best_obj.get("intervention") or {}).get("traffic_light_id")

    base_wait = float(base.get("mean_completed_vehicle_waiting_seconds") or base.get("average_waiting_seconds", 24.0) or 24.0)
    best_metrics = best_obj.get("metrics") or {}
    opt_wait = float(best_metrics.get("mean_completed_vehicle_waiting_seconds") or best_metrics.get("average_waiting_seconds", base_wait) or base_wait)
    wait_reduction = max(0.0, round(base_wait - opt_wait, 1))

    base_tt = float(base.get("average_travel_time_seconds", 58.4) or 58.4)
    opt_tt = float(best_metrics.get("average_travel_time_seconds", base_tt) or base_tt)
    tt_reduction = max(0.0, round(base_tt - opt_tt, 1))

    base_stops = float(base.get("stops_per_vehicle", 1.42) or 1.42)
    opt_stops = float(best_metrics.get("stops_per_vehicle", base_stops) or base_stops)

    tradeoff_summary = best_obj.get("tradeoff_summary") or {}
    improved_list = [
        item.get("name") if isinstance(item, dict) else str(item)
        for item in tradeoff_summary.get("improved", [])
    ]
    worsened_list = [
        item.get("name") if isinstance(item, dict) else str(item)
        for item in tradeoff_summary.get("worsened", [])
    ]

    if language == "ru":
        key_improvements = [
            f"Сокращение средней задержки на {wait_reduction} с по сравнению с базовым сценарием.",
            f"Сокращение общего времени в пути на {tt_reduction} с.",
            f"Снижение числа остановок на авто с {base_stops:.2f} до {opt_stops:.2f}.",
        ]
        if improved_list:
            key_improvements.append(f"Положительная динамика: {', '.join(improved_list)}.")

        tradeoffs = [
            "Моделирование основано на симуляционных данных SUMO без натурных дорожных датчиков.",
            "Приоритет основного коридора может незначительно увеличить время выезда с прилегающих второстепенных улиц.",
        ]
        if worsened_list:
            tradeoffs.append(f"Возможные локальные компромиссы: {', '.join(worsened_list)}.")

        concerns = [
            "Необходима полевая калибровка детекторов перед физическим перепрограммированием контроллеров.",
            "Следует отслеживать очереди на второстепенных направлениях в часы пик.",
        ]

        cand_count = len(cands) if cands else 1
        summary = (
            f"Правило-ориентированная оценка: на основе детерминированного анализа {cand_count} сценариев "
            f"наилучшим решением является «{best_name}». Оно обеспечивает сбалансированное улучшение коридора."
        )

        recommendation = (
            f"Рекомендуется применить стратегию «{best_name}» для центрального коридора с последующим мониторингом задержек."
        )

        return {
            "status": "FALLBACK",
            "provider": "rule_based_fallback",
            "provenance": "ПРАВИЛО-ОРИЕНТИРОВАННОЕ РЕЗЮМЕ",
            "is_ai": False,
            "summary": summary,
            "key_improvements": key_improvements,
            "tradeoffs": tradeoffs,
            "concerns": concerns,
            "recommendation": recommendation,
            "confidence": "medium",
            "signal_focus": f"Узел {signal_id or 'Центральный коридор'}",
            "scope": "Детерминированная оптимизация задержек и выбросов",
            "expected_impact": f"Снижение задержки на {wait_reduction} с, сокращение времени в пути на {tt_reduction} с.",
            "reasoning": summary,
        }

    key_improvements = [
        f"Average delay reduced by {wait_reduction}s vs baseline.",
        f"Corridor travel time reduced by {tt_reduction}s.",
        f"Stops per vehicle reduced from {base_stops:.2f} to {opt_stops:.2f}.",
    ]
    if improved_list:
        key_improvements.append(f"Positive dimensions: {', '.join(improved_list)}.")

    tradeoffs = [
        "Results are derived from SUMO simulation physics and require on-site validation.",
        "Prioritizing main corridor progression may slightly increase side-street approach wait times.",
    ]
    if worsened_list:
        tradeoffs.append(f"Potential localized trade-offs: {', '.join(worsened_list)}.")

    concerns = [
        "Field sensor calibration recommended prior to deployment in controller hardware.",
        "Monitor cross-street queue lengths during peak hour transitions.",
    ]

    cand_count = len(cands) if cands else 1
    summary = (
        f"Rule-based assessment: deterministic evaluation across {cand_count} candidates indicates "
        f"that '{best_name}' provides the optimal balance of throughput, travel time, and emission reductions."
    )

    recommendation = (
        f"Implement '{best_name}' as the coordinated signal timing strategy along the central corridor."
    )

    return {
        "status": "FALLBACK",
        "provider": "rule_based_fallback",
        "provenance": "RULE-BASED SUMMARY",
        "is_ai": False,
        "summary": summary,
        "key_improvements": key_improvements,
        "tradeoffs": tradeoffs,
        "concerns": concerns,
        "recommendation": recommendation,
        "confidence": "medium",
        "signal_focus": f"Signal {signal_id or 'Central Corridor'}",
        "scope": "Multi-objective corridor timing and emissions optimization",
        "expected_impact": f"Delay reduced by {wait_reduction}s, travel time reduced by {tt_reduction}s.",
        "reasoning": summary,
    }


def _provider_available() -> bool:
    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        return False
    if api_key in ["", "your-gemini-api-key-here", "your-google-api-key-here"]:
        return False
    return len(api_key) >= 10


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Robust JSON extraction from LLM response text."""
    if not text:
        return None
    cleaned = text.strip()

    # Check for markdown code blocks
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned, re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Direct search for JSON object
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return None


def explain_results(
    baseline: dict[str, Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    best: dict[str, Any] | None = None,
    experiment_context: dict[str, Any] | None = None,
    language: str = "en"
) -> dict[str, Any]:
    """
    Generate research-grade AI interpretation of actual simulation / experiment results.
    If credentials are missing or the provider fails, gracefully returns a transparent RULE-BASED SUMMARY.
    """
    base = baseline or {}
    cands = candidates or []
    best_obj = best or {}

    fallback = _rule_based_summary(base, cands, best_obj, experiment_context=experiment_context, language=language)

    if not _provider_available():
        return fallback

    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")).strip()
    model_name = os.getenv("AI_MODEL", "gemini-3.7-flash")

    best_name = best_obj.get("label") or best_obj.get("id") or "Intervention"
    signal_id = (best_obj.get("intervention") or {}).get("traffic_light_id")

    base_wait = float(base.get("mean_completed_vehicle_waiting_seconds") or base.get("average_waiting_seconds", 0) or 0)
    base_tt = float(base.get("average_travel_time_seconds", 0) or 0)
    base_speed = float(base.get("average_speed_kmh", 0) or 0)
    base_stops = float(base.get("stops_per_vehicle", 0) or 0)
    base_tp = float(base.get("throughput_vehicles_per_hour", 0) or 0)
    base_co2 = float(base.get("sumo_co2_kg") or base.get("co2_kg", 0) or 0)

    best_metrics = best_obj.get("metrics") or {}
    best_wait = float(best_metrics.get("mean_completed_vehicle_waiting_seconds") or best_metrics.get("average_waiting_seconds", base_wait) or base_wait)
    best_tt = float(best_metrics.get("average_travel_time_seconds", base_tt) or base_tt)
    best_speed = float(best_metrics.get("average_speed_kmh", base_speed) or base_speed)
    best_stops = float(best_metrics.get("stops_per_vehicle", base_stops) or base_stops)
    best_tp = float(best_metrics.get("throughput_vehicles_per_hour", base_tp) or base_tp)
    best_co2 = float(best_metrics.get("sumo_co2_kg") or best_metrics.get("co2_kg", base_co2) or base_co2)

    best_delta = best_obj.get("delta") or {}

    delay_imp = best_delta.get("delay_improvement_pct")
    if delay_imp is None and base_wait > 0:
        delay_imp = round(((base_wait - best_wait) / base_wait) * 100, 1)

    tt_imp = best_delta.get("travel_time_improvement_pct")
    if tt_imp is None and base_tt > 0:
        tt_imp = round(((base_tt - best_tt) / base_tt) * 100, 1)

    stops_imp = best_delta.get("stops_improvement_pct")
    if stops_imp is None and base_stops > 0:
        stops_imp = round(((base_stops - best_stops) / base_stops) * 100, 1)

    tp_imp = best_delta.get("throughput_improvement_pct")
    if tp_imp is None and base_tp > 0:
        tp_imp = round(((best_tp - base_tp) / base_tp) * 100, 1)

    co2_imp = best_delta.get("emissions_improvement_pct")
    if co2_imp is None and base_co2 > 0:
        co2_imp = round(((base_co2 - best_co2) / base_co2) * 100, 1)

    lang_instruction = (
        "CRITICAL: ALL string fields in the returned JSON must be written in fluent, professional Russian (на грамотном русском языке)."
        if language == "ru"
        else "All string fields in the returned JSON must be written in fluent, professional English."
    )

    prompt = f"""You are UrbanMind AI, a transportation intelligence system analyzing real SUMO microscopic simulation results for the Tashkent Central Corridor.

Strictly return ONLY a valid JSON object without markdown fences or extraneous text.
{lang_instruction}

Required JSON schema:
{{
  "summary": "1-2 concise sentences summarizing the overall outcome and primary impact.",
  "key_improvements": ["Specific quantified improvement 1", "Specific quantified improvement 2", "Specific quantified improvement 3"],
  "tradeoffs": ["Operational caveat or trade-off 1", "Operational caveat or trade-off 2"],
  "concerns": ["Limitation or what city planners should monitor 1", "Limitation 2"],
  "recommendation": "A cautious, actionable recommendation based on the observed simulation evidence.",
  "confidence": "high" | "medium" | "low"
}}

Simulation Data Context:
- Evaluated Corridor: Tashkent Central Corridor (Signals: cluster_1 through cluster_6)
- Target Signal/Node: {signal_id or 'Corridor Progression Axis'}
- Total Interventions Evaluated: {len(cands)}
- Selected Strategy: {best_name}
- Baseline Performance: Delay={base_wait:.1f}s, Travel Time={base_tt:.1f}s, Speed={base_speed:.1f}km/h, Stops/Veh={base_stops:.2f}, Throughput={base_tp:.0f}veh/h, CO2={base_co2:.1f}kg
- Optimized Performance: Delay={best_wait:.1f}s, Travel Time={best_tt:.1f}s, Speed={best_speed:.1f}km/h, Stops/Veh={best_stops:.2f}, Throughput={best_tp:.0f}veh/h, CO2={best_co2:.1f}kg
- Percentage Changes: Delay={delay_imp}%, Travel Time={tt_imp}%, Stops={stops_imp}%, Throughput={tp_imp}%, CO2={co2_imp}%
"""

    try:
        raw_text = None
        candidate_models = ["gemini-3.6-flash", model_name, "gemini-3.1-pro-preview"]
        unique_models = list(dict.fromkeys([m for m in candidate_models if m]))

        # 1. Try google.genai Client
        try:
            from google import genai as google_genai
            client = google_genai.Client(api_key=api_key)
            for m in unique_models:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=prompt,
                    )
                    raw_text = getattr(response, "text", "") or ""
                    if raw_text:
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # 2. Try google.generativeai if genai client failed
        if not raw_text:
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=api_key)
                for m in unique_models:
                    try:
                        model = legacy_genai.GenerativeModel(m)
                        response = model.generate_content(prompt)
                        raw_text = getattr(response, "text", "") or ""
                        if raw_text:
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        if not raw_text:
            return fallback

        payload = _extract_json_from_text(raw_text)
        if not payload or not isinstance(payload, dict):
            return fallback

        # Validate structured fields
        summary = str(payload.get("summary") or fallback["summary"])
        key_improvements = payload.get("key_improvements")
        if not isinstance(key_improvements, list) or not key_improvements:
            key_improvements = fallback["key_improvements"]

        tradeoffs = payload.get("tradeoffs")
        if not isinstance(tradeoffs, list) or not tradeoffs:
            tradeoffs = fallback["tradeoffs"]

        concerns = payload.get("concerns")
        if not isinstance(concerns, list) or not concerns:
            concerns = fallback["concerns"]

        recommendation = str(payload.get("recommendation") or fallback["recommendation"])
        confidence = str(payload.get("confidence") or "high")
        if confidence not in ["high", "medium", "low"]:
            confidence = "medium"

        return {
            "status": "COMPLETE",
            "provider": "gemini",
            "provenance": "ИИ-АНАЛИЗ" if language == "ru" else "AI ANALYSIS",
            "is_ai": True,
            "summary": summary,
            "key_improvements": [str(x) for x in key_improvements],
            "tradeoffs": [str(x) for x in tradeoffs],
            "concerns": [str(x) for x in concerns],
            "recommendation": recommendation,
            "confidence": confidence,
            "signal_focus": f"Узел {signal_id or 'Центральный коридор'}" if language == "ru" else f"Signal {signal_id or 'Central Corridor'}",
            "scope": "Моделирование и оптимизация центрального коридора" if language == "ru" else "Central corridor simulation & optimization",
            "expected_impact": f"Delay {delay_imp}%, Travel Time {tt_imp}%",
            "reasoning": summary,
        }
    except Exception:
        return fallback


def propose_interventions(context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return only deterministic, valid intervention definitions within the allowed action space."""
    return [
        {"type": "green_wave_coordination", "target_speed_kmh": 40.0},
        {"type": "extend_green", "seconds": 5},
        {"type": "extend_green", "seconds": 10},
        {"type": "reduce_green", "seconds": 5},
    ]
