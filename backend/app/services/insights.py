from __future__ import annotations

from typing import Any

PRODUCT_NAME = "UrbanMind"
CATEGORY = "Neighborhood Mobility Intelligence"
CATEGORY_RU = "Платформа цифрового двойника города"


def describe_traffic_signal(metrics: dict[str, Any], language: str = "en") -> list[str]:
    avg_speed = float(metrics.get("average_speed_kmh", 0.0) or 0.0)
    avg_wait = float(metrics.get("average_waiting_seconds", 0.0) or 0.0)
    vehicle_count = int(metrics.get("max_vehicle_count", 0) or 0)
    signal_count = int(metrics.get("traffic_light_count", 0) or 0)

    signals_ru: list[str] = []
    if avg_speed < 20:
        signals_ru.append("Локальная мобильность под нагрузкой, выпуск очередей замедлен.")
    else:
        signals_ru.append("Коридор умеренно свободен, но точечная настройка фаз сохранит запас пропускной способности.")

    if avg_wait > 20:
        signals_ru.append("Средние задержки сосредоточены на пиковых перекрестках и подъездах к школам.")
    else:
        signals_ru.append("Время ожидания остается контролируемым, что позволяет провести безопасную оптимизацию сигналов.")

    if vehicle_count > 30:
        signals_ru.append("Уличная сеть испытывает повышенную нагрузку, особенно вокруг центральных узлов.")
    if signal_count > 0:
        signals_ru.append(f"{signal_count} светофорных кластеров активно в анализируемой зоне района.")

    if language == "ru":
        return signals_ru

    signals_en: list[str] = []
    if avg_speed < 20:
        signals_en.append("Local mobility is under pressure and queue discharge is slow.")
    else:
        signals_en.append("The corridor is moderately fluid, but small timing adjustments can preserve headroom.")

    if avg_wait > 20:
        signals_en.append("Average delays are concentrated at peak local intersections and school-access segments.")
    else:
        signals_en.append("Wait times remain manageable, leaving room for a low-risk signal adjustment.")

    if vehicle_count > 30:
        signals_en.append("The street network is seeing significant demand pressure, especially around central intersections.")
    if signal_count > 0:
        signals_en.append(f"{signal_count} signal clusters are active in the analyzed neighborhood mesh.")

    return signals_en


def build_neighborhood_summary(metrics: dict[str, Any], candidate: dict[str, Any] | None = None, language: str = "en") -> dict[str, Any]:
    candidate_label_en = (candidate or {}).get("label_en") or (candidate or {}).get("label") or (candidate or {}).get("id") or "signal timing adjustment"
    candidate_label_ru = (candidate or {}).get("label_ru") or (candidate or {}).get("label") or candidate_label_en
    candidate_summary = (candidate or {}).get("summary") or (candidate or {}).get("description") or ""
    avg_speed = float(metrics.get("average_speed_kmh", 0.0) or 0.0)
    avg_wait = float(metrics.get("average_waiting_seconds", 0.0) or 0.0)

    focus_en = "school-access and community-corridor flow"
    focus_ru = "коридор школьного доступа и районные потоки"
    if "school" in (candidate_summary or "").lower() or "школ" in (candidate_summary or "").lower():
        focus_en = "school-access corridor"
        focus_ru = "коридор школьного доступа"
    elif "clinic" in (candidate_summary or "").lower() or "поликлиник" in (candidate_summary or "").lower():
        focus_en = "clinic and public-service trip flow"
        focus_ru = "поток к поликлиникам и социальным объектам"

    headline_en = f"{PRODUCT_NAME} helps neighborhood teams optimize mobility before congestion affects daily life."
    headline_ru = f"{PRODUCT_NAME} помогает городским службам оптимизировать мобильность до того, как заторы повлияют на повседневную жизнь."

    context_en = (
        f"This {CATEGORY} view measures how the street network behaves under real traffic demand, using average speed of {avg_speed:.2f} km/h "
        f"and waiting time of {avg_wait:.2f} seconds as the key operational signals."
    )
    context_ru = (
        f"Этот режим {CATEGORY_RU} оценивает поведение улично-дорожной сети под реальной нагрузкой, "
        f"используя среднюю скорость {avg_speed:.2f} км/ч и время ожидания {avg_wait:.2f} с как ключевые операционные сигналы."
    )

    recommendation_en = f"{PRODUCT_NAME} identifies {candidate_label_en} as the most effective local intervention within the current simulation."
    recommendation_ru = f"{PRODUCT_NAME} определяет «{candidate_label_ru}» как наиболее эффективную локальную меру в текущей симуляции."

    return {
        "product_name": PRODUCT_NAME,
        "category": CATEGORY_RU if language == "ru" else CATEGORY,
        "category_en": CATEGORY,
        "category_ru": CATEGORY_RU,
        "headline": headline_ru if language == "ru" else headline_en,
        "headline_en": headline_en,
        "headline_ru": headline_ru,
        "focus": focus_ru if language == "ru" else focus_en,
        "focus_en": focus_en,
        "focus_ru": focus_ru,
        "signals": describe_traffic_signal(metrics, language=language),
        "signals_en": describe_traffic_signal(metrics, language="en"),
        "signals_ru": describe_traffic_signal(metrics, language="ru"),
        "recommendation": recommendation_ru if language == "ru" else recommendation_en,
        "recommendation_en": recommendation_en,
        "recommendation_ru": recommendation_ru,
        "context": context_ru if language == "ru" else context_en,
        "context_en": context_en,
        "context_ru": context_ru,
    }


def describe_product_positioning(language: str = "en") -> dict[str, Any]:
    positioning_en = f"{PRODUCT_NAME} is a {CATEGORY} platform for neighborhood mobility planning, signal timing optimization, and public-space resilience."
    positioning_ru = f"{PRODUCT_NAME} — {CATEGORY_RU} для планирования мобильности районов, оптимизации светофорных фаз и устойчивости городской среды."

    value_en = [
        "Explainable traffic intervention recommendations",
        "Local government and mahalla decision support",
        "Low-risk, evidence-based mobility optimization",
    ]
    value_ru = [
        "Объяснимые рекомендации по транспортным мерам",
        "Поддержка принятия решений для хокимиятов и махаллей",
        "Низкорисковая, научно обоснованная оптимизация мобильности",
    ]

    return {
        "product_name": PRODUCT_NAME,
        "category": CATEGORY_RU if language == "ru" else CATEGORY,
        "category_en": CATEGORY,
        "category_ru": CATEGORY_RU,
        "positioning": positioning_ru if language == "ru" else positioning_en,
        "positioning_en": positioning_en,
        "positioning_ru": positioning_ru,
        "value": value_ru if language == "ru" else value_en,
        "value_en": value_en,
        "value_ru": value_ru,
    }
