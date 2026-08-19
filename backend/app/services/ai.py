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
        "status": "FALLBACK",
        "provider": "deterministic_fallback",
        "provenance": "ANALYTICAL INTERPRETATION",
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
    if not api_key:
        return False
    key = api_key.strip()
    if key in ["", "your-gemini-api-key-here", "your-google-api-key-here"]:
        return False
    return True


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

    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")).strip()
    model_name = os.getenv("AI_MODEL", "gemini-2.0-flash")
    best_desc = best.get("description", best_name) if best else best_name
    best_delta = best.get("delta", {}) if best else {}

    prompt = (
        "You are an urban mobility intelligence AI interpreting traffic simulation results. "
        "Strictly return valid JSON only (no markdown, no backticks). "
        "JSON structure: {\n"
        '  "recommendation": "string (mention this is based on simulation, not live field measurement)",\n'
        '  "reasoning": "string with detailed explanation of why this intervention was selected",\n'
        '  "tradeoffs": ["string 1", "string 2", "string 3"],\n'
        '  "confidence": "high" | "medium" | "low",\n'
        '  "signal_focus": "string detailing targeted traffic lights",\n'
        '  "scope": "string describing scope of timing and flow optimization",\n'
        '  "expected_impact": "string describing expected local benefit"\n'
        "}\n\n"
        f"Context:\n"
        f"- Target Signal: {signal_id or 'Corridor bottleneck'}\n"
        f"- Baseline average speed: {baseline_speed:.2f} km/h, average wait: {baseline_wait:.2f} s\n"
        f"- Selected Best Intervention: {best_desc}\n"
        f"- Best average speed: {best_speed:.2f} km/h, average wait: {best_wait:.2f} s\n"
        f"- Improvement deltas: {best_delta}\n"
        f"- Number of candidates evaluated: {len(candidates)}"
    )

    try:
        raw_text = None
        
        # Try google-genai first
        try:
            from google import genai as google_genai
            client = google_genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            raw_text = getattr(response, "text", "") or ""
        except Exception:
            # Fall back to google.generativeai
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            raw_text = getattr(response, "text", "") or ""

        if not raw_text:
            raise RuntimeError("Empty response from AI provider")

        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            # Ensure tradeoffs is list
            tradeoffs = payload.get("tradeoffs")
            if isinstance(tradeoffs, str):
                tradeoffs = [tradeoffs]
            elif not isinstance(tradeoffs, list):
                tradeoffs = fallback["tradeoffs"]

            return {
                "status": "COMPLETE",
                "provider": "gemini",
                "provenance": "ANALYTICAL INTERPRETATION",
                "recommendation": str(payload.get("recommendation") or fallback["recommendation"]),
                "reasoning": str(payload.get("reasoning") or fallback["reasoning"]),
                "tradeoffs": tradeoffs,
                "confidence": str(payload.get("confidence") or "medium"),
                "signal_focus": str(payload.get("signal_focus") or signal_focus),
                "best_signal_id": signal_id,
                "scope": str(payload.get("scope") or fallback["scope"]),
                "expected_impact": str(payload.get("expected_impact") or fallback["expected_impact"]),
            }
        return fallback
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
