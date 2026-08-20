import pytest
from app.services.simulation.policies import (
    get_policy, normalize_weights, normalize_metric_delta,
    compute_component_scores, check_constraints, evaluate_policy_score,
    POLICIES, FLOW_POLICY, ECO_POLICY, BALANCED_POLICY
)
from app.services.simulation.optimizer import evaluate_candidates, rank_candidates, compute_policy_comparison


def test_policy_definitions():
    assert "flow" in POLICIES
    assert "eco" in POLICIES
    assert "balanced" in POLICIES
    assert "custom" in POLICIES

    flow = get_policy("flow")
    assert flow.objective_weights["mobility"] == 0.80
    assert flow.objective_weights["environment"] == 0.10

    eco = get_policy("eco")
    assert eco.objective_weights["environment"] == 0.75
    assert eco.objective_weights["mobility"] == 0.15

    balanced = get_policy("balanced")
    assert balanced.objective_weights["mobility"] == 0.45
    assert balanced.objective_weights["environment"] == 0.35
    assert balanced.objective_weights["accessibility"] == 0.20


def test_custom_weights_validation_and_normalization():
    # Valid custom weights
    custom = get_policy("custom", {"mobility": 50, "environment": 30, "accessibility": 20})
    assert custom.policy_id == "custom"
    assert custom.objective_weights["mobility"] == 0.50
    assert custom.objective_weights["environment"] == 0.30
    assert custom.objective_weights["accessibility"] == 0.20

    # Test invalid weights: negative
    with pytest.raises(ValueError, match="cannot be negative"):
        normalize_weights({"mobility": -10, "environment": 50})

    # Test invalid weights: non-numeric
    with pytest.raises(ValueError, match="must be a numeric value"):
        normalize_weights({"mobility": "invalid", "environment": 50})

    # Test invalid weights: zero sum
    with pytest.raises(ValueError, match="greater than zero"):
        normalize_weights({"mobility": 0, "environment": 0, "accessibility": 0})


def test_metric_normalization_directions():
    # Lower is better (minimize): e.g. delay 20s -> 10s is 50% improvement (+50.0)
    delta_delay = normalize_metric_delta(20.0, 10.0, "minimize")
    assert delta_delay == 50.0

    # Delay worsening: 20s -> 25s is 25% worsening (-25.0)
    delta_worse = normalize_metric_delta(20.0, 25.0, "minimize")
    assert delta_worse == -25.0

    # Higher is better (maximize): e.g. throughput 500 -> 600 is 20% improvement (+20.0)
    delta_tp = normalize_metric_delta(500.0, 600.0, "maximize")
    assert delta_tp == 20.0

    # Zero baseline handling
    assert normalize_metric_delta(0.0, 0.0, "minimize") == 0.0
    assert normalize_metric_delta(0.0, 10.0, "maximize") == 100.0
    assert normalize_metric_delta(0.0, 10.0, "minimize") == -100.0


def test_component_scores_and_policy_breakdown():
    baseline = {
        "average_waiting_seconds": 30.0,
        "average_travel_time_seconds": 60.0,
        "stops_per_vehicle": 1.5,
        "mean_queue_length_meters": 40.0,
        "throughput_vehicles_per_hour": 500.0,
        "average_speed_kmh": 20.0,
        "co2_kg": 50.0,
        "nox_g": 200.0,
        "sumo_co2_kg": 50.0,
        "sumo_nox_g": 200.0,
        "noise_db": 68.0,
        "pedestrian_delay_seconds": 15.0,
        "accessibility_score": 80.0,
    }

    # Scenario with massive delay reduction but slightly increased emissions
    scenario_traffic_focus = {
        "average_waiting_seconds": 15.0,  # 50% improvement
        "average_travel_time_seconds": 40.0,  # 33% improvement
        "stops_per_vehicle": 0.8,
        "mean_queue_length_meters": 20.0,
        "throughput_vehicles_per_hour": 600.0,
        "average_speed_kmh": 28.0,
        "co2_kg": 52.0,  # 4% worsening
        "nox_g": 205.0,
        "sumo_co2_kg": 52.0,
        "sumo_nox_g": 205.0,
        "noise_db": 69.0,
        "pedestrian_delay_seconds": 16.0,
        "accessibility_score": 80.0,
    }

    # Under FLOW policy: mobility score dominates
    eval_flow = evaluate_policy_score(baseline, scenario_traffic_focus, FLOW_POLICY)
    assert eval_flow["mobility_score"] > 25.0
    assert eval_flow["overall_score"] > 20.0
    assert eval_flow["is_valid"] is True

    # Under ECO policy: emissions penalty dampens score
    eval_eco = evaluate_policy_score(baseline, scenario_traffic_focus, ECO_POLICY)
    assert eval_eco["overall_score"] < eval_flow["overall_score"]


def test_constraint_violations():
    baseline = {"average_waiting_seconds": 20.0, "co2_kg": 40.0}
    # Severe delay increase (20s -> 35s = 75% worse, violating 20% limit)
    bad_scenario = {"average_waiting_seconds": 35.0, "co2_kg": 35.0}

    is_valid, violations_en, violations_ru = check_constraints(baseline, bad_scenario, BALANCED_POLICY)
    assert is_valid is False
    assert len(violations_en) >= 1
    assert "average_waiting_seconds" in violations_en[0]

    eval_result = evaluate_policy_score(baseline, bad_scenario, BALANCED_POLICY)
    assert eval_result["is_valid"] is False
    assert eval_result["ranking_score"] < -500.0  # severely penalized


def test_policy_ranking_shifts():
    baseline = {
        "average_speed_kmh": 25.0,
        "average_waiting_seconds": 30.0,
        "average_travel_time_seconds": 60.0,
        "mean_queue_length_meters": 35.0,
        "stops_per_vehicle": 1.4,
        "throughput_vehicles_per_hour": 550.0,
        "co2_kg": 50.0,
        "nox_g": 200.0,
        "sumo_co2_kg": 50.0,
        "sumo_nox_g": 200.0,
        "noise_db": 65.0,
        "pedestrian_delay_seconds": 15.0,
        "accessibility_score": 85.0,
    }

    # Candidate 1: High speed/mobility gains, slight eco cost
    cand1_def = {"type": "extend_green_10s", "label": "Traffic Maximizer", "category": "signal_timing"}
    cand1_metrics = {
        "average_speed_kmh": 32.0,
        "average_waiting_seconds": 18.0,
        "average_travel_time_seconds": 42.0,
        "mean_queue_length_meters": 20.0,
        "stops_per_vehicle": 0.9,
        "throughput_vehicles_per_hour": 660.0,
        "co2_kg": 51.0,
        "nox_g": 204.0,
        "sumo_co2_kg": 51.0,
        "sumo_nox_g": 204.0,
        "noise_db": 66.0,
        "pedestrian_delay_seconds": 17.0,
        "accessibility_score": 82.0,
    }

    # Candidate 2: Major eco/stop reduction, moderate delay gain
    cand2_def = {"type": "eco_calm", "label": "Eco Calm Zone", "category": "safety"}
    cand2_metrics = {
        "average_speed_kmh": 26.0,
        "average_waiting_seconds": 25.0,
        "average_travel_time_seconds": 55.0,
        "mean_queue_length_meters": 30.0,
        "stops_per_vehicle": 0.6,
        "throughput_vehicles_per_hour": 570.0,
        "co2_kg": 38.0,  # 24% CO2 reduction
        "nox_g": 150.0,  # 25% NOx reduction
        "sumo_co2_kg": 38.0,
        "sumo_nox_g": 150.0,
        "noise_db": 58.0,
        "pedestrian_delay_seconds": 12.0,
        "accessibility_score": 95.0,
    }

    cand_tuples = [(cand1_def, cand1_metrics), (cand2_def, cand2_metrics)]

    # Under FLOW: Candidate 1 should rank higher
    opt_flow = rank_candidates(
        "midday", baseline,
        evaluate_candidates(baseline, cand_tuples, policy_id="flow"),
        policy_id="flow"
    )
    assert opt_flow["best_candidate"]["id"] == "extend_green_10s_0s_signal_timing"

    # Under ECO: Candidate 2 should rank higher
    opt_eco = rank_candidates(
        "midday", baseline,
        evaluate_candidates(baseline, cand_tuples, policy_id="eco"),
        policy_id="eco"
    )
    assert opt_eco["best_candidate"]["id"] == "eco_calm_0s_safety"

    # Test cross-policy comparison
    comparison = compute_policy_comparison(baseline, cand_tuples)
    assert "flow" in comparison
    assert "eco" in comparison
    assert "balanced" in comparison
    assert comparison["flow"]["best_candidate_id"] == "extend_green_10s_0s_signal_timing"
    assert comparison["eco"]["best_candidate_id"] == "eco_calm_0s_safety"
    assert "why_won" in comparison["flow"]
    assert "why_won" in comparison["eco"]
    assert "why_won" in comparison["balanced"]
    assert len(comparison["flow"]["why_won"]) > 10


def test_deterministic_why_this_won_generation():
    from app.services.simulation.policies import generate_why_this_won_explanation

    cand = {
        "id": "cand_1",
        "score": 18.5,
        "delta": {
            "delay_improvement_pct": 28.5,
            "travel_time_improvement_pct": 14.2,
            "stops_improvement_pct": 22.0,
            "throughput_improvement_pct": 8.0,
            "emissions_improvement_pct": 12.0,
        },
        "policy_breakdown": {
            "overall_score": 18.5,
            "mobility_score": 24.0,
            "environment_score": 12.0,
            "accessibility_score": 5.0,
        }
    }

    # FLOW explanation in EN and RU
    flow_en = generate_why_this_won_explanation(FLOW_POLICY, cand, language="en")
    flow_ru = generate_why_this_won_explanation(FLOW_POLICY, cand, language="ru")
    assert "FLOW Winner" in flow_en
    assert "28.5%" in flow_en
    assert "Победитель по политике ТРАФИК" in flow_ru
    assert "28.5%" in flow_ru

    # ECO explanation in EN and RU
    eco_en = generate_why_this_won_explanation(ECO_POLICY, cand, language="en")
    eco_ru = generate_why_this_won_explanation(ECO_POLICY, cand, language="ru")
    assert "ECO Winner" in eco_en
    assert "12.0%" in eco_en
    assert "Победитель по политике ЭКО" in eco_ru

    # BALANCED explanation in EN and RU
    bal_en = generate_why_this_won_explanation(BALANCED_POLICY, cand, language="en")
    bal_ru = generate_why_this_won_explanation(BALANCED_POLICY, cand, language="ru")
    assert "BALANCED Winner" in bal_en
    assert "Победитель по политике БАЛАНС" in bal_ru
