from typing import Any, List

def get_candidate_interventions(signal_id: str, phase_index: int) -> List[dict[str, Any]]:
    """
    Returns the canonical registry of the currently implemented intervention candidates.
    There must be exactly one source of truth for intervention definitions.
    """
    return [
        {"type": "extend_green", "category": "signal_timing", "label": "Extend main green phase", "seconds": 5, "traffic_light_id": signal_id, "phase_index": phase_index, "evaluation_mode": "SIMULATED"},
        {"type": "extend_green", "category": "signal_timing", "label": "Extend main green phase", "seconds": 10, "traffic_light_id": signal_id, "phase_index": phase_index, "evaluation_mode": "SIMULATED"},
        {"type": "reduce_green", "category": "signal_timing", "label": "Reduce competing phase", "seconds": -5, "traffic_light_id": signal_id, "phase_index": phase_index, "evaluation_mode": "SIMULATED"},
        {"type": "bus_priority", "category": "transit", "label": "Bus-priority corridor", "seconds": 8, "evaluation_mode": "HEURISTIC"},
        {"type": "pedestrian_priority", "category": "active_mobility", "label": "Pedestrian priority window", "seconds": 6, "evaluation_mode": "HEURISTIC"},
        {"type": "school_zone_slowdown", "category": "safety", "label": "School-zone speed calming", "speed_limit_mps": 5.5, "seconds": 0, "evaluation_mode": "SIMULATED"},
        {"type": "parking_turnover", "category": "curb_management", "label": "Short-stay curb rotation", "seconds": 10, "evaluation_mode": "HEURISTIC"},
    ]

def get_intervention_effect_summary(category: str, action_text: str, wait_change: float) -> str:
    effect_map = {
        "signal_timing": "This intervention reallocates signal time to reduce queues and smooth discharge through the busiest junction.",
        "transit": "This intervention prioritizes the bus corridor and improves access for public transport without fully blocking the local network.",
        "active_mobility": "This intervention gives pedestrians and school-access trips a safer, more predictable crossing window.",
        "safety": "This intervention reduces risk in the most sensitive local area by creating calmer traffic and better visibility.",
        "curb_management": "This intervention improves curb turnover and reduces friction from stop-start circulation around the local access points.",
    }
    effect = effect_map.get(category, "This intervention changes the neighborhood operating conditions in a way that improves local mobility and access.")
    return (
        f"{action_text}: {effect} "
        f"Expected waiting impact: {wait_change:.2f}s vs baseline, with local access and environmental tradeoffs considered."
    )
