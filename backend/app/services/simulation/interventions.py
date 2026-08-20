from typing import Any, List

INTERVENTION_LABELS_RU = {
    "Green-wave corridor coordination (40 km/h)": "Координированная «зелёная волна» (40 км/ч)",
    "Extend main green phase (+5s)": "Продление зелёной фазы (+5 с)",
    "Extend main green phase (+10s)": "Продление зелёной фазы (+10 с)",
    "Reduce competing phase (-5s)": "Сокращение конкурирующей фазы (-5 с)",
    "Bus-priority corridor (+8s)": "Коридор с приоритетом автобусов (+8 с)",
    "Pedestrian priority window (+6s)": "Окно приоритета пешеходов (+6 с)",
    "Eligible-lane speed calming (20 km/h)": "Успокоение движения на доступных полосах (20 км/ч)",
    "Short-stay curb rotation (15 min)": "Ротация парковки короткого пребывания (15 мин)",
    "Green-wave corridor coordination": "Координированная «зелёная волна» (40 км/ч)",
    "Extend main green phase": "Продление основной зелёной фазы",
    "Reduce competing phase": "Сокращение конкурирующей фазы",
    "Bus-priority corridor": "Коридор с приоритетом автобусов",
    "Pedestrian priority window": "Окно приоритета пешеходов",
    "Eligible-lane speed calming": "Успокоение движения на доступных полосах",
    "Short-stay curb rotation": "Ротация парковки короткого пребывания",
    "Green Wave Coordination": "Координированная «зелёная волна» (40 км/ч)",
    "green_wave_coordination": "Координированная «зелёная волна»",
    "extend_green": "Продление зелёной фазы",
    "reduce_green": "Сокращение конкурирующей фазы",
    "bus_priority": "Коридор с приоритетом автобусов",
    "pedestrian_priority": "Окно приоритета пешеходов",
    "school_zone_slowdown": "Успокоение трафика в школьной зоне",
    "parking_turnover": "Ротация парковки короткого пребывания",
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
            "type": "extend_green",
            "category": "signal_timing",
            "label": "Extend main green phase (+5s)",
            "label_ru": "Продление зелёной фазы (+5 с)",
            "label_en": "Extend main green phase (+5s)",
            "seconds": 5,
            "traffic_light_id": signal_id,
            "phase_index": phase_index,
            "evaluation_mode": "SIMULATED",
        },
        {
            "type": "extend_green",
            "category": "signal_timing",
            "label": "Extend main green phase (+10s)",
            "label_ru": "Продление зелёной фазы (+10 с)",
            "label_en": "Extend main green phase (+10s)",
            "seconds": 10,
            "traffic_light_id": signal_id,
            "phase_index": phase_index,
            "evaluation_mode": "SIMULATED",
        },
        {
            "type": "reduce_green",
            "category": "signal_timing",
            "label": "Reduce competing phase (-5s)",
            "label_ru": "Сокращение конкурирующей фазы (-5 с)",
            "label_en": "Reduce competing phase (-5s)",
            "seconds": -5,
            "traffic_light_id": signal_id,
            "phase_index": phase_index,
            "evaluation_mode": "SIMULATED",
        },
        {
            "type": "school_zone_slowdown",
            "category": "safety",
            "label": "Eligible-lane speed calming (20 km/h)",
            "label_ru": "Успокоение движения на доступных полосах (20 км/ч)",
            "label_en": "Eligible-lane speed calming (20 km/h)",
            "speed_limit_mps": 5.5,
            "seconds": 0,
            "evaluation_mode": "SIMULATED",
        },
    ]

def get_intervention_effect_summary(category: str, action_text: str, wait_change: float, language: str = "en") -> str:
    if language == "ru":
        effect_map_ru = {
            "signal_timing": "Данная мера координирует сдвиги фаз и время горения зеленого сигнала по всему коридору для непрерывного безостановочного проезда и снижения задержек.",
            "transit": "Данная мера отдает приоритет автобусному коридору и улучшает доступность общественного транспорта без блокировки локальной сети.",
            "active_mobility": "Данная мера обеспечивает пешеходам и школьникам более безопасный и предсказуемый интервал перехода.",
            "safety": "Эта мера ограничивает скорость на подходящих полосах сети; конкретная пространственная зона не верифицирована.",
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
        "safety": "This intervention reduces speed on eligible network lanes; no specific field safety zone is verified.",
        "curb_management": "This intervention improves curb turnover and reduces friction from stop-start circulation around the local access points.",
    }
    effect = effect_map.get(category, "This intervention changes the neighborhood operating conditions in a way that improves local mobility and access.")
    return (
        f"{action_text}: {effect} "
        f"Expected waiting impact: {wait_change:.2f}s vs baseline, with local access and environmental tradeoffs considered."
    )
