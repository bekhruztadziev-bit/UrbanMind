from __future__ import annotations

from typing import Any

PRODUCT_NAME = "MahallaMind"
CATEGORY = "Neighborhood Mobility Intelligence"


def describe_traffic_signal(metrics: dict[str, Any]) -> list[str]:
    avg_speed = float(metrics.get("average_speed_kmh", 0.0) or 0.0)
    avg_wait = float(metrics.get("average_waiting_seconds", 0.0) or 0.0)
    vehicle_count = int(metrics.get("max_vehicle_count", 0) or 0)
    signal_count = int(metrics.get("traffic_light_count", 0) or 0)

    signals: list[str] = []
    if avg_speed < 20:
        signals.append("Local mobility is under pressure and queue discharge is slow.")
    else:
        signals.append("The corridor is moderately fluid, but small timing adjustments can preserve headroom.")

    if avg_wait > 20:
        signals.append("Average delays are concentrated at peak local intersections and school-access segments.")
    else:
        signals.append("Wait times remain manageable, leaving room for a low-risk signal adjustment.")

    if vehicle_count > 30:
        signals.append("The street network is seeing significant demand pressure, especially around central intersections.")
    if signal_count > 0:
        signals.append(f"{signal_count} signal clusters are active in the analyzed neighborhood mesh.")

    return signals


def build_neighborhood_summary(metrics: dict[str, Any], candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    candidate_label = (candidate or {}).get("label") or (candidate or {}).get("id") or "signal timing adjustment"
    candidate_summary = (candidate or {}).get("summary") or (candidate or {}).get("description") or ""
    avg_speed = float(metrics.get("average_speed_kmh", 0.0) or 0.0)
    avg_wait = float(metrics.get("average_waiting_seconds", 0.0) or 0.0)

    focus = "school-access and community-corridor flow"
    if "school" in (candidate_summary or "").lower():
        focus = "school-access corridor"
    elif "clinic" in (candidate_summary or "").lower():
        focus = "clinic and public-service trip flow"

    return {
        "product_name": PRODUCT_NAME,
        "category": CATEGORY,
        "headline": f"{PRODUCT_NAME} helps neighborhood teams optimize mobility before congestion affects daily life.",
        "focus": focus,
        "signals": describe_traffic_signal(metrics),
        "recommendation": (
            f"{PRODUCT_NAME} identifies {candidate_label} as the most effective local intervention within the current simulation."
        ),
        "context": (
            f"This {CATEGORY} view measures how the street network behaves under real traffic demand, using average speed of {avg_speed:.2f} km/h "
            f"and waiting time of {avg_wait:.2f} seconds as the key operational signals."
        ),
    }


def describe_product_positioning() -> dict[str, Any]:
    return {
        "product_name": PRODUCT_NAME,
        "category": CATEGORY,
        "positioning": (
            f"{PRODUCT_NAME} is a {CATEGORY} platform for neighborhood mobility planning, signal timing optimization, and public-space resilience."
        ),
        "value": [
            "Explainable traffic intervention recommendations",
            "Local government and mahalla decision support",
            "Low-risk, evidence-based mobility optimization",
        ],
    }
