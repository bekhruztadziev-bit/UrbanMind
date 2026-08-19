from typing import Any, List

INTERVENTION_LABELS_RU = {
    "Green-wave corridor coordination": "Координированная «зеленая волна» по коридору",
    "Extend main green phase": "Продление основной зеленой фазы",
    "Reduce competing phase": "Сокращение конкурирующей фазы",
    "Bus-priority corridor": "Коридор с приоритетом автобусов",
    "Pedestrian priority window": "Окно приоритета пешеходов",
    "School-zone speed calming": "Успокоение трафика в школьной зоне",
    "Short-stay curb rotation": "Ротация парковки короткого пребывания",
}

INTERVENTION_CATEGORIES_RU = {
    "signal_timing": "настройка сигналов",
    "transit": "общественный транспорт",
    "active_mobility": "активная мобильность",
    "safety": "безопасность",
    "curb_management": "управление парковкой",
    "mobility": "мобильность",
}

def get_candidate_interventions(signal_id: str, phase_index: int) -> List[dict[str, Any]]:
    """
    Returns the canonical registry of the currently implemented intervention candidates.
    There must be exactly one source of truth for intervention definitions.
    """
    return [
        {
            "type": "green_wave_coordination",
            "category": "signal_timing",
            "label": "Green-wave corridor coordination",
            "seconds": 0,
            "traffic_light_id": signal_id,
            "phase_index": phase_index,
            "target_speed_kmh": 40.0,
            "evaluation_mode": "SIMULATED",
        },
        {
            "type": "extend_green",
            "category": "signal_timing",
            "label": "Extend main green phase",
            "seconds": 5,
            "traffic_light_id": signal_id,
            "phase_index": phase_index,
            "evaluation_mode": "SIMULATED",
        },
        {
            "type": "extend_green",
            "category": "signal_timing",
            "label": "Extend main green phase",
            "seconds": 10,
            "traffic_light_id": signal_id,
            "phase_index": phase_index,
            "evaluation_mode": "SIMULATED",
        },
        {
            "type": "reduce_green",
            "category": "signal_timing",
            "label": "Reduce competing phase",
            "seconds": -5,
            "traffic_light_id": signal_id,
            "phase_index": phase_index,
            "evaluation_mode": "SIMULATED",
        },
        {
            "type": "bus_priority",
            "category": "transit",
            "label": "Bus-priority corridor",
            "seconds": 8,
            "evaluation_mode": "HEURISTIC",
        },
        {
            "type": "pedestrian_priority",
            "category": "active_mobility",
            "label": "Pedestrian priority window",
            "seconds": 6,
            "evaluation_mode": "HEURISTIC",
        },
        {
            "type": "school_zone_slowdown",
            "category": "safety",
            "label": "School-zone speed calming",
            "speed_limit_mps": 5.5,
            "seconds": 0,
            "evaluation_mode": "SIMULATED",
        },
        {
            "type": "parking_turnover",
            "category": "curb_management",
            "label": "Short-stay curb rotation",
            "seconds": 10,
            "evaluation_mode": "HEURISTIC",
        },
    ]

def get_intervention_effect_summary(category: str, action_text: str, wait_change: float, language: str = "en") -> str:
    if language == "ru":
        effect_map_ru = {
            "signal_timing": "Данная мера координирует сдвиги фаз и время горения зеленого сигнала по всему коридору для непрерывного безостановочного проезда и снижения задержек.",
            "transit": "Данная мера отдает приоритет автобусному коридору и улучшает доступность общественного транспорта без блокировки локальной сети.",
            "active_mobility": "Данная мера обеспечивает пешеходам и школьникам более безопасный и предсказуемый интервал перехода.",
            "safety": "Данная мера снижает риски в наиболее уязвимой зоне района за счет успокоения движения и улучшения видимости.",
            "curb_management": "Данная мера улучшает оборачиваемость парковочных мест и снижает помехи от маневров у местных точек притяжения.",
        }
        effect = effect_map_ru.get(category, "Данная мера изменяет условия движения в районе, улучшая локальную мобильность и доступность.")
        action_ru = INTERVENTION_LABELS_RU.get(action_text, action_text)
        return (
            f"{action_ru}: {effect} "
            f"Ожидаемое влияние на ожидание: {wait_change:.2f} с по сравнению с базовым сценарием, с учетом локального доступа и экологических факторов."
        )

    effect_map = {
        "signal_timing": "This intervention coordinates signal phase offsets and green intervals along the corridor for continuous unhalted progression and delay minimization.",
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
