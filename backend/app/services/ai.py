from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def _fallback_explanation(baseline: dict[str, Any], candidates: list[dict[str, Any]], best: dict[str, Any] | None = None) -> dict[str, Any]:
    best_name = best.get("id", "best intervention") if best else "best intervention"
    signal_id = (best or {}).get("intervention", {}).get("traffic_light_id") if best else None
    signal_focus = (
        f"Signal focus: {signal_id}. The recommendation targets the busiest junction cluster to reduce queue spillback and shorten delay across the neighborhood corridor."
        if signal_id
        else "Signal focus: the most effective intervention across the simulated corridor, balancing mobility and neighborhood access."
    )
    return {
        "recommendation": (
            f"AI analysis unavailable; recommendation is based on simulation metrics for {signal_id or 'the selected signal'} and is optimized across delay, emissions, accessibility, and safety."
        ),
        "reasoning": (
            f"The deterministic simulation compared the baseline against {len(candidates)} candidate interventions. "
            f"The selected recommendation is {best_name} because the measured metrics were strongest across travel time, queueing, emissions, and pedestrian access. "
            f"{signal_focus}"
        ),
        "tradeoffs": [
            "Simulation-based recommendation has no live field validation.",
            "Some measures improve travel flow while others improve safety or emissions; the final plan is a balance rather than a pure speed maximizer.",
            "Actual operational impact should be confirmed with on-site observation.",
        ],
        "confidence": "low",
        "signal_focus": signal_focus,
        "best_signal_id": signal_id,
        "scope": "Multi-objective neighborhood optimization across mobility, emissions, and access outcomes.",
        "expected_impact": "Likely meaningful corridor improvement: lower delay, reduced queue pressure, lower emissions, and safer access for pedestrians and local trips.",
    }


def _provider_available() -> bool:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return bool(api_key)


def explain_results(baseline: dict[str, Any], candidates: list[dict[str, Any]], best: dict[str, Any] | None = None) -> dict[str, Any]:
    best_name = best.get("id", "best intervention") if best else "best intervention"
    signal_id = (best or {}).get("intervention", {}).get("traffic_light_id") if best else None
    baseline_wait = float(baseline.get("average_waiting_seconds", 0) or 0)
    baseline_speed = float(baseline.get("average_speed_kmh", 0) or 0)
    best_wait = float(best.get("metrics", {}).get("average_waiting_seconds", baseline_wait) if best else baseline_wait) or baseline_wait
    best_speed = float(best.get("metrics", {}).get("average_speed_kmh", baseline_speed) if best else baseline_speed) or baseline_speed
    signal_focus = (
        f"Signal focus: {signal_id}. The chosen intervention targets the most congested junction cluster in the corridor, where queues build fastest and waiting times are most sensitive to phase length and access changes."
        if signal_id
        else "Signal focus: the intervention with the strongest measured performance across neighborhood mobility, emissions, and access outcomes."
    )
    fallback = _fallback_explanation(baseline, candidates, best)
    if not _provider_available():
        return fallback

    try:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("AI API key missing")

        try:
            import google.generativeai as genai
        except Exception:
            try:
                from google import genai as google_genai  # type: ignore
            except Exception as exc:  # pragma: no cover
                raise RuntimeError(f"AI dependency missing: {exc}") from exc
            else:
                client = google_genai.Client(api_key=api_key)
                model_name = os.getenv("AI_MODEL", "gemini-2.0-flash")
                response = client.models.generate_content(
                    model=model_name,
                    contents=(
                        "Generate concise JSON with recommendation, reasoning, tradeoffs, confidence. "
                        "Use only the provided simulation metrics. "
                        f"Baseline speed: {baseline_speed}; baseline wait: {baseline_wait}; best intervention: {best_name}; best speed: {best_speed}; best wait: {best_wait}."
                    ),
                )
                text = getattr(response, "text", "") or ""
                if not text:
                    raise RuntimeError("Empty AI response")
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.strip("`")
                    if cleaned.lower().startswith("json"):
                        cleaned = cleaned[4:].strip()
                payload = json.loads(cleaned)
                return payload if isinstance(payload, dict) else fallback

        genai.configure(api_key=api_key)
        model_name = os.getenv("AI_MODEL", "gemini-2.0-flash")
        model = genai.GenerativeModel(model_name)

        best_desc = best.get("description", "best measured intervention") if best else "best measured intervention"
        best_delta = best.get("delta", {}) if best else {}
        prompt = (
            "You are generating a short operational recommendation from simulation metrics only. "
            "Do not claim real-world impact beyond these measured results. "
            f"Baseline average speed: {baseline_speed} km/h. Baseline average waiting: {baseline_wait} seconds. "
            f"Best measured intervention: {best_desc}. "
            f"Best average speed: {best_speed} km/h. Best average waiting: {best_wait} seconds. "
            f"Improvement deltas: {best_delta}. "
            "Provide concise JSON with keys: recommendation, reasoning, tradeoffs, confidence. "
            "The recommendation should mention that the result is based on the simulation and not field data."
        )

        response = model.generate_content(prompt)
        text = getattr(response, "text", "")
        if not text:
            raise RuntimeError("Empty AI response")

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        payload = json.loads(cleaned)
        if not isinstance(payload, dict):
            raise ValueError("AI response was not a JSON object")
        return payload
    except Exception:
        return fallback


def propose_interventions(context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return only deterministic, valid intervention definitions within the allowed action space."""
    allowed = [
        {"type": "extend_green", "seconds": 5},
        {"type": "extend_green", "seconds": 10},
        {"type": "reduce_green", "seconds": 5},
    ]
    return allowed
