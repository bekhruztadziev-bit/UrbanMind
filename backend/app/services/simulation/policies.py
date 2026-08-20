from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

MetricDirection = Literal["minimize", "maximize"]

METRIC_DIRECTIONS: Dict[str, MetricDirection] = {
    # Mobility metrics
    "average_waiting_seconds": "minimize",
    "mean_completed_vehicle_waiting_seconds": "minimize",
    "mean_active_vehicle_waiting_seconds": "minimize",
    "average_travel_time_seconds": "minimize",
    "mean_queue_length_meters": "minimize",
    "stops_per_vehicle": "minimize",
    "throughput_vehicles_per_hour": "maximize",
    "average_speed_kmh": "maximize",
    "max_vehicle_count": "minimize",
    
    # Environmental metrics
    "co2_kg": "minimize",
    "nox_g": "minimize",
    "sumo_co2_kg": "minimize",
    "sumo_nox_g": "minimize",
    "noise_db": "minimize",
    
    # Accessibility & Safety metrics
    "pedestrian_delay_seconds": "minimize",
    "accessibility_score": "maximize",
}


@dataclass
class PolicyConstraint:
    metric: str
    max_allowed_worsening_pct: float  # e.g. 20.0 means metric cannot worsen by more than 20%
    description_en: str
    description_ru: str


@dataclass
class PolicyDefinition:
    policy_id: str
    name: str
    name_ru: str
    description: str
    description_ru: str
    icon: str
    
    # Decision Question
    objective_question: str = ""
    objective_question_ru: str = ""
    
    # Primary evaluation dimensions
    primary_dimensions: List[str] = field(default_factory=list)
    
    # "Why This Won" summary template
    why_won_template: str = ""
    why_won_template_ru: str = ""

    # High-level component weights (must sum to 1.0)
    objective_weights: Dict[str, float] = field(default_factory=dict)  # {"mobility": 0.45, "environment": 0.35, "accessibility": 0.20}
    
    # Sub-metric internal weights within each component
    mobility_metric_weights: Dict[str, float] = field(default_factory=dict)
    environment_metric_weights: Dict[str, float] = field(default_factory=dict)
    accessibility_metric_weights: Dict[str, float] = field(default_factory=dict)
    
    # Constraints
    constraints: List[PolicyConstraint] = field(default_factory=list)
    normalization_method: str = "baseline_relative_percentage"


# Canonical Policies
FLOW_POLICY = PolicyDefinition(
    policy_id="flow",
    name="FLOW (Mobility Priority)",
    name_ru="ТРАФИК (Приоритет мобильности)",
    description="Minimize congestion, travel delays, and vehicle stops while maximizing throughput.",
    description_ru="Минимизация заторов, задержек и остановок с максимизацией пропускной способности.",
    icon="🚗",
    objective_question="Which candidate best improves traffic mobility?",
    objective_question_ru="Какой вариант лучше всего повышает транспортную мобильность?",
    primary_dimensions=[
        "average_waiting_seconds",
        "average_travel_time_seconds",
        "mean_queue_length_meters",
        "stops_per_vehicle",
        "throughput_vehicles_per_hour",
        "average_speed_kmh",
    ],
    why_won_template="Strongest mobility improvement across delay, travel time, and throughput.",
    why_won_template_ru="Наибольшее улучшение мобильности по задержкам, времени в пути и пропускной способности.",
    objective_weights={
        "mobility": 0.80,
        "environment": 0.10,
        "accessibility": 0.10,
    },
    mobility_metric_weights={
        "average_waiting_seconds": 0.30,
        "average_travel_time_seconds": 0.25,
        "stops_per_vehicle": 0.15,
        "mean_queue_length_meters": 0.15,
        "throughput_vehicles_per_hour": 0.10,
        "average_speed_kmh": 0.05,
    },
    environment_metric_weights={
        "co2_kg": 0.60,
        "nox_g": 0.40,
    },
    accessibility_metric_weights={
        "pedestrian_delay_seconds": 0.60,
        "accessibility_score": 0.40,
    },
    constraints=[
        PolicyConstraint(
            metric="co2_kg",
            max_allowed_worsening_pct=25.0,
            description_en="Emissions must not increase by more than 25%",
            description_ru="Выбросы CO₂ не должны увеличиваться более чем на 25%",
        )
    ],
)

ECO_POLICY = PolicyDefinition(
    policy_id="eco",
    name="ECO (Environmental Priority)",
    name_ru="ЭКО (Приоритет экологии)",
    description="Minimize simulated emissions (CO₂, NOₓ), idling, and fuel consumption across the corridor.",
    description_ru="Минимизация моделируемых выбросов (CO₂, NOₓ), холостого хода и расхода топлива.",
    icon="🌱",
    objective_question="Which candidate best reduces modeled transportation environmental impact?",
    objective_question_ru="Какой вариант лучше всего снижает расчетное экологическое воздействие транспорта?",
    primary_dimensions=[
        "co2_kg",
        "nox_g",
        "noise_db",
        "stops_per_vehicle",
        "average_waiting_seconds",
    ],
    why_won_template="Largest modeled emissions reduction (CO₂, NOₓ, fuel) while remaining within traffic constraints.",
    why_won_template_ru="Максимальное снижение расчетных выбросов (CO₂, NOₓ, топлива) при соблюдении ограничений по потоку.",
    objective_weights={
        "mobility": 0.15,
        "environment": 0.75,
        "accessibility": 0.10,
    },
    mobility_metric_weights={
        "average_waiting_seconds": 0.30,
        "average_travel_time_seconds": 0.20,
        "stops_per_vehicle": 0.30,  # Stops directly burn fuel
        "mean_queue_length_meters": 0.10,
        "throughput_vehicles_per_hour": 0.05,
        "average_speed_kmh": 0.05,
    },
    environment_metric_weights={
        "co2_kg": 0.50,
        "nox_g": 0.35,
        "noise_db": 0.15,
    },
    accessibility_metric_weights={
        "pedestrian_delay_seconds": 0.50,
        "accessibility_score": 0.50,
    },
    constraints=[
        PolicyConstraint(
            metric="average_waiting_seconds",
            max_allowed_worsening_pct=30.0,
            description_en="Corridor delay must not increase by more than 30%",
            description_ru="Задержка на коридоре не должна увеличиваться более чем на 30%",
        )
    ],
)

BALANCED_POLICY = PolicyDefinition(
    policy_id="balanced",
    name="BALANCED (Multi-Objective Compromise)",
    name_ru="БАЛАНС (Многокритериальный компромисс)",
    description="Holistic balance of corridor flow, emission reductions, and local pedestrian accessibility.",
    description_ru="Сбалансированное сочетание мобильности коридора, снижения выбросов и безопасности пешеходов.",
    icon="⚖️",
    objective_question="Which candidate provides the strongest compromise between mobility, environment, and accessibility?",
    objective_question_ru="Какой вариант обеспечивает наилучший компромисс между мобильностью, экологией и доступностью?",
    primary_dimensions=[
        "average_waiting_seconds",
        "average_travel_time_seconds",
        "co2_kg",
        "nox_g",
        "pedestrian_delay_seconds",
        "accessibility_score",
    ],
    why_won_template="Best combined multi-objective policy score across mobility, environment, and accessibility.",
    why_won_template_ru="Наилучший суммарный баланс по мобильности, экологии и безопасности пешеходов.",
    objective_weights={
        "mobility": 0.45,
        "environment": 0.35,
        "accessibility": 0.20,
    },
    mobility_metric_weights={
        "average_waiting_seconds": 0.30,
        "average_travel_time_seconds": 0.25,
        "stops_per_vehicle": 0.20,
        "mean_queue_length_meters": 0.15,
        "throughput_vehicles_per_hour": 0.10,
    },
    environment_metric_weights={
        "co2_kg": 0.55,
        "nox_g": 0.35,
        "noise_db": 0.10,
    },
    accessibility_metric_weights={
        "pedestrian_delay_seconds": 0.50,
        "accessibility_score": 0.50,
    },
    constraints=[
        PolicyConstraint(
            metric="average_waiting_seconds",
            max_allowed_worsening_pct=20.0,
            description_en="Delay must not increase by more than 20%",
            description_ru="Задержка не должна увеличиваться более чем на 20%",
        ),
        PolicyConstraint(
            metric="co2_kg",
            max_allowed_worsening_pct=20.0,
            description_en="Emissions must not increase by more than 20%",
            description_ru="Выбросы не должны увеличиваться более чем на 20%",
        ),
    ],
)

CUSTOM_POLICY_TEMPLATE = PolicyDefinition(
    policy_id="custom",
    name="CUSTOM (Configurable Objectives)",
    name_ru="ПОЛЬЗОВАТЕЛЬСКАЯ (Настраиваемые цели)",
    description="Configurable municipal objective weights across traffic, environment, and accessibility.",
    description_ru="Настраиваемые веса приоритетов по транспорту, экологии и доступности.",
    icon="⚙️",
    objective_question="Which candidate best satisfies user-configured municipal objective weights?",
    objective_question_ru="Какой вариант лучше всего отвечает заданным муниципальным весам целей?",
    primary_dimensions=[
        "average_waiting_seconds",
        "co2_kg",
        "accessibility_score",
    ],
    why_won_template="Optimized to custom municipal objective weighting across mobility, environment, and accessibility.",
    why_won_template_ru="Оптимизировано под заданные веса целей по мобильности, экологии и доступности.",
    objective_weights={
        "mobility": 0.34,
        "environment": 0.33,
        "accessibility": 0.33,
    },
    mobility_metric_weights={
        "average_waiting_seconds": 0.30,
        "average_travel_time_seconds": 0.25,
        "stops_per_vehicle": 0.20,
        "mean_queue_length_meters": 0.15,
        "throughput_vehicles_per_hour": 0.10,
    },
    environment_metric_weights={
        "co2_kg": 0.60,
        "nox_g": 0.40,
    },
    accessibility_metric_weights={
        "pedestrian_delay_seconds": 0.50,
        "accessibility_score": 0.50,
    },
    constraints=[],
)

POLICIES: Dict[str, PolicyDefinition] = {
    "flow": FLOW_POLICY,
    "eco": ECO_POLICY,
    "balanced": BALANCED_POLICY,
    "custom": CUSTOM_POLICY_TEMPLATE,
}



def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Validate that weights are non-negative numbers, reject invalid configs,
    and normalize them to sum to 1.0.
    """
    if not weights or not isinstance(weights, dict):
        raise ValueError("Weights must be a non-empty dictionary.")

    clean: Dict[str, float] = {}
    for k, v in weights.items():
        try:
            num = float(v)
        except (ValueError, TypeError):
            raise ValueError(f"Weight for '{k}' must be a numeric value, got: {v}")
        if num < 0:
            raise ValueError(f"Weight for '{k}' cannot be negative, got: {num}")
        clean[k] = num

    total = sum(clean.values())
    if total <= 0:
        raise ValueError("Total sum of objective weights must be greater than zero.")

    return {k: round(v / total, 4) for k, v in clean.items()}


def get_policy(policy_id: str = "balanced", custom_weights: Optional[Dict[str, float]] = None) -> PolicyDefinition:
    """
    Retrieve policy definition by ID. If 'custom', apply validated custom objective weights.
    """
    pid = (policy_id or "balanced").strip().lower()
    base = POLICIES.get(pid, BALANCED_POLICY)

    if pid == "custom" and custom_weights:
        norm_w = normalize_weights(custom_weights)
        # Ensure all 3 components are present
        final_w = {
            "mobility": norm_w.get("mobility", 0.34),
            "environment": norm_w.get("environment", 0.33),
            "accessibility": norm_w.get("accessibility", 0.33),
        }
        # Re-normalize just in case
        total = sum(final_w.values())
        final_w = {k: round(v / total, 4) for k, v in final_w.items()}

        return PolicyDefinition(
            policy_id="custom",
            name="CUSTOM (Configurable Objectives)",
            name_ru="ПОЛЬЗОВАТЕЛЬСКАЯ (Настраиваемые цели)",
            description=f"Custom weighting: Mobility {final_w['mobility']*100:.0f}%, Eco {final_w['environment']*100:.0f}%, Access {final_w['accessibility']*100:.0f}%",
            description_ru=f"Пользовательские веса: Мобильность {final_w['mobility']*100:.0f}%, Экология {final_w['environment']*100:.0f}%, Доступность {final_w['accessibility']*100:.0f}%",
            icon="⚙️",
            objective_weights=final_w,
            mobility_metric_weights=base.mobility_metric_weights,
            environment_metric_weights=base.environment_metric_weights,
            accessibility_metric_weights=base.accessibility_metric_weights,
            constraints=base.constraints,
            normalization_method=base.normalization_method,
        )

    return base


def normalize_metric_delta(baseline_val: float, scenario_val: float, direction: MetricDirection) -> float:
    """
    Calculate normalized percentage improvement relative to baseline.
    Positive result indicates improvement; negative indicates worsening.
    
    If direction == "minimize" (lower is better):
        R = ((baseline - scenario) / baseline) * 100
    If direction == "maximize" (higher is better):
        R = ((scenario - baseline) / baseline) * 100
    """
    base = float(baseline_val or 0.0)
    scen = float(scenario_val or 0.0)

    if math.isclose(base, 0.0, abs_tol=1e-6):
        if math.isclose(scen, 0.0, abs_tol=1e-6):
            return 0.0
        return 100.0 if (direction == "maximize" and scen > 0) else -100.0

    if direction == "minimize":
        pct = ((base - scen) / base) * 100.0
    else:
        pct = ((scen - base) / base) * 100.0

    # Bound extreme outliers for normalization stability
    return max(-100.0, min(100.0, round(pct, 2)))


def compute_component_scores(
    baseline: Dict[str, Any],
    scenario: Dict[str, Any],
    policy: PolicyDefinition
) -> Tuple[float, float, float, Dict[str, float]]:
    """
    Compute normalized Mobility, Environment, and Accessibility component scores (in % improvement scale),
    as well as individual metric deltas.
    """
    deltas: Dict[str, float] = {}

    def _eval_group(metric_weights: Dict[str, float]) -> float:
        group_score = 0.0
        weight_sum = sum(metric_weights.values())
        if weight_sum <= 0:
            return 0.0

        for metric, w in metric_weights.items():
            dir_ = METRIC_DIRECTIONS.get(metric, "minimize")
            b_val = float(baseline.get(metric, 0.0) or 0.0)
            s_val = float(scenario.get(metric, b_val) or b_val)
            delta_pct = normalize_metric_delta(b_val, s_val, dir_)
            deltas[metric] = delta_pct
            group_score += (w / weight_sum) * delta_pct

        return round(group_score, 2)

    mobility_score = _eval_group(policy.mobility_metric_weights)
    environment_score = _eval_group(policy.environment_metric_weights)
    accessibility_score = _eval_group(policy.accessibility_metric_weights)

    return mobility_score, environment_score, accessibility_score, deltas


def check_constraints(
    baseline: Dict[str, Any],
    scenario: Dict[str, Any],
    policy: PolicyDefinition
) -> Tuple[bool, List[str], List[str]]:
    """
    Evaluate policy constraints.
    Returns (is_valid, violations_en, violations_ru).
    """
    violations_en = []
    violations_ru = []

    for c in policy.constraints:
        dir_ = METRIC_DIRECTIONS.get(c.metric, "minimize")
        b_val = float(baseline.get(c.metric, 0.0) or 0.0)
        s_val = float(scenario.get(c.metric, b_val) or b_val)
        delta_pct = normalize_metric_delta(b_val, s_val, dir_)

        # If delta_pct < -max_allowed_worsening_pct, constraint is violated
        if delta_pct < -c.max_allowed_worsening_pct:
            worsening = abs(delta_pct)
            violations_en.append(
                f"{c.metric} worsened by {worsening:.1f}% (exceeds {c.max_allowed_worsening_pct:.1f}% limit). {c.description_en}"
            )
            violations_ru.append(
                f"{c.metric} ухудшился на {worsening:.1f}% (превышает лимит {c.max_allowed_worsening_pct:.1f}%). {c.description_ru}"
            )

    return len(violations_en) == 0, violations_en, violations_ru


def evaluate_policy_score(
    baseline: Dict[str, Any],
    scenario: Dict[str, Any],
    policy: PolicyDefinition
) -> Dict[str, Any]:
    """
    Calculate comprehensive policy score breakdown and constraint compliance for a candidate.
    """
    mob_score, env_score, acc_score, deltas = compute_component_scores(baseline, scenario, policy)
    is_valid, violations_en, violations_ru = check_constraints(baseline, scenario, policy)

    w_mob = policy.objective_weights.get("mobility", 0.34)
    w_env = policy.objective_weights.get("environment", 0.33)
    w_acc = policy.objective_weights.get("accessibility", 0.33)

    raw_overall = (w_mob * mob_score) + (w_env * env_score) + (w_acc * acc_score)
    overall_score = round(raw_overall, 2)

    # If constraint is violated, apply severe penalty for ranking purposes
    ranking_score = overall_score if is_valid else round(overall_score - 1000.0, 2)

    return {
        "policy_id": policy.policy_id,
        "policy_name": policy.name,
        "policy_name_ru": policy.name_ru,
        "overall_score": overall_score,
        "ranking_score": ranking_score,
        "mobility_score": mob_score,
        "environment_score": env_score,
        "accessibility_score": acc_score,
        "weights": policy.objective_weights,
        "is_valid": is_valid,
        "constraint_violations_en": violations_en,
        "constraint_violations_ru": violations_ru,
        "metric_deltas": deltas,
    }


def generate_why_this_won_explanation(
    policy: PolicyDefinition,
    candidate: Dict[str, Any],
    language: str = "en"
) -> str:
    """
    Generate deterministic, data-grounded explanation for why a winning candidate
    was selected under the given policy objective.
    """
    is_ru = language == "ru"
    pb = candidate.get("policy_breakdown") or {}
    delta = candidate.get("delta") or {}

    delay_imp = delta.get("delay_improvement_pct", 0.0)
    tt_imp = delta.get("travel_time_improvement_pct", 0.0)
    stops_imp = delta.get("stops_improvement_pct", 0.0)
    tp_imp = delta.get("throughput_improvement_pct", 0.0)
    co2_imp = delta.get("emissions_improvement_pct", 0.0)
    overall = pb.get("overall_score", candidate.get("score", 0.0))
    mob_score = pb.get("mobility_score", 0.0)
    env_score = pb.get("environment_score", 0.0)
    acc_score = pb.get("accessibility_score", 0.0)

    pid = policy.policy_id.lower()

    if pid == "flow":
        if is_ru:
            return (
                f"Победитель по политике ТРАФИК (оценка {overall:+.1f}%): обеспечивает максимальное сокращение задержек "
                f"на {delay_imp:+.1f}% и времени в пути на {tt_imp:+.1f}%, с приростом пропускной способности на {tp_imp:+.1f}%."
            )
        return (
            f"FLOW Winner (Score {overall:+.1f}%): Delivers highest mobility improvement across delay ({delay_imp:+.1f}%), "
            f"travel time ({tt_imp:+.1f}%), and corridor throughput ({tp_imp:+.1f}%)."
        )

    elif pid == "eco":
        if is_ru:
            return (
                f"Победитель по политике ЭКО (оценка {overall:+.1f}%): обеспечивает максимальное сокращение расчетных выбросов CO₂ "
                f"на {co2_imp:+.1f}% и снижение числа остановок на {stops_imp:+.1f}%, напрямую минимизируя холостой ход и расход топлива."
            )
        return (
            f"ECO Winner (Score {overall:+.1f}%): Achieves largest modeled emissions reduction ({co2_imp:+.1f}% CO₂) and "
            f"decreases stop frequency by {stops_imp:+.1f}%, directly minimizing fuel consumption and idling."
        )

    elif pid == "custom":
        w = policy.objective_weights
        w_mob = int(w.get("mobility", 0.34) * 100)
        w_env = int(w.get("environment", 0.33) * 100)
        w_acc = int(w.get("accessibility", 0.33) * 100)
        if is_ru:
            return (
                f"Победитель по ПОЛЬЗОВАТЕЛЬСКОЙ политике (оценка {overall:+.1f}%): оптимизировано под заданные веса целей "
                f"(Мобильность {w_mob}%, Экология {w_env}%, Доступность {w_acc}%), дав вклад: Мобильность {mob_score:+.1f}%, Экология {env_score:+.1f}%."
            )
        return (
            f"CUSTOM Winner (Score {overall:+.1f}%): Optimized to configured municipal objective weights "
            f"(Mobility {w_mob}%, Eco {w_env}%, Access {w_acc}%) with contribution: Mobility {mob_score:+.1f}%, Eco {env_score:+.1f}%."
        )

    else:  # balanced
        if is_ru:
            return (
                f"Победитель по политике БАЛАНС (оценка {overall:+.1f}%): обеспечивает наилучший компромисс между сокращением задержек "
                f"(Мобильность {mob_score:+.1f}%), снижением выбросов (Экология {env_score:+.1f}%) и безопасностью пешеходов ({acc_score:+.1f}%)."
            )
        return (
            f"BALANCED Winner (Score {overall:+.1f}%): Provides the strongest multi-objective compromise across "
            f"mobility ({mob_score:+.1f}%), modeled emissions ({env_score:+.1f}%), and pedestrian accessibility ({acc_score:+.1f}%)."
        )

