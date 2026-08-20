import pytest
from app.services.reports.generator import generate_decision_report, _build_metric_comparison
from app.services.reports.models import DecisionReport


@pytest.fixture
def mock_optimization_result():
    return {
        "scenario": "midday",
        "policy": "balanced",
        "baseline": {
            "steps": 300,
            "warmup_steps": 0,
            "average_speed_kmh": 22.5,
            "average_waiting_seconds": 25.0,
            "average_travel_time_seconds": 120.0,
            "stops_per_vehicle": 1.4,
            "mean_queue_length_meters": 18.2,
            "throughput_vehicles_per_hour": 1800.0,
            "co2_kg": 18.5,
            "nox_g": 38.0,
            "noise_db": 68.5,
            "pedestrian_delay_seconds": 12.0,
            "accessibility_score": 75.0,
        },
        "best_candidate": {
            "id": "green_wave_coordination_0s_signal_timing",
            "label": "Green Wave Coordination (40 km/h)",
            "label_ru": "Зеленая волна (40 км/ч)",
            "evaluation_mode": "SIMULATED",
            "metrics": {
                "steps": 300,
                "warmup_steps": 0,
                "average_speed_kmh": 27.2,
                "average_waiting_seconds": 18.0,
                "average_travel_time_seconds": 96.0,
                "stops_per_vehicle": 0.8,
                "mean_queue_length_meters": 11.5,
                "throughput_vehicles_per_hour": 2100.0,
                "co2_kg": 15.2,
                "nox_g": 32.1,
                "noise_db": 66.8,
                "pedestrian_delay_seconds": 12.5,
                "accessibility_score": 78.0,
            },
            "policy_breakdown": {
                "overall_score": 14.8,
                "mobility_score": 22.4,
                "environment_score": 12.1,
                "accessibility_score": 2.5,
                "is_valid": True,
                "constraint_violations_en": [],
                "constraint_violations_ru": [],
            },
            "tradeoff_summary": {
                "improved": [
                    {"name": "Average Delay", "name_ru": "Задержка", "value": -28.0, "unit": "%"},
                    {"name": "CO2 Emissions", "name_ru": "Выбросы CO2", "value": -17.8, "unit": "%"},
                ],
                "worsened": [
                    {"name": "Pedestrian Delay", "name_ru": "Задержка пешеходов", "value": +4.1, "unit": "%"},
                ],
                "unchanged": [],
                "verdict_en": "Strong mobility and emission gains with minor cross-street impact.",
                "verdict_ru": "Значительный выигрыш в задержках и выбросах при минимальном влиянии на пешеходов.",
            },
            "robustness_sample_count": 5,
            "robustness_seeds": [42, 101, 2024, 3033, 4044],
            "robustness_stats": {
                "average_waiting_seconds": {
                    "mean": 18.1,
                    "std_dev": 0.45,
                    "ci_95_low": 17.7,
                    "ci_95_high": 18.5,
                    "min": 17.5,
                    "max": 18.8,
                }
            }
        },
        "ai": {
            "provenance": "AI ANALYSIS",
            "summary": "Coordinated progression provides significant travel time benefits.",
            "recommendation": "Deploy offset timing with standard detector validation.",
        }
    }


def test_generate_decision_report_structure(mock_optimization_result):
    """Verify that generate_decision_report builds all required sections."""
    report = generate_decision_report(mock_optimization_result, policy_id="balanced")

    assert "report_id" in report
    assert report["report_id"].startswith("REP-")
    assert report["policy_id"] == "balanced"
    assert report["scenario_id"] == "midday"

    # Spatial Scope
    assert "spatial_scope" in report
    assert report["spatial_scope"]["id"] == "central_corridor"
    assert report["spatial_scope"]["city_name"] == "Tashkent"

    # Executive Summary
    exec_s = report["executive_summary"]
    assert "recommended_intervention" in exec_s
    assert "Green Wave" in exec_s["recommended_intervention"]
    assert "28.0%" in exec_s["primary_result"]
    assert "17.8%" in exec_s["environmental_result"]
    assert exec_s["confidence"] == "high"

    # Policy Audit
    audit = report["policy_audit"]
    assert audit["policy_id"] == "balanced"
    assert audit["policy_score"] == 14.8
    assert audit["mobility_score"] == 22.4
    assert audit["environment_score"] == 12.1
    assert audit["constraint_status"] == "PASS"

    # Metric Comparison
    metrics = report["metric_comparison"]
    assert len(metrics) >= 10
    delay_row = next(r for r in metrics if r["key"] == "average_waiting_seconds")
    assert delay_row["baseline"] == 25.0
    assert delay_row["optimized"] == 18.0
    assert delay_row["percentage_change"] == -28.0
    assert delay_row["is_improvement"] is True
    assert delay_row["provenance"] == "SIMULATED"

    co2_row = next(r for r in metrics if r["key"] == "sumo_co2_kg")
    assert co2_row["provenance"] == "SIMULATED"
    assert co2_row["is_improvement"] is True

    # Robustness
    robustness = report["robustness"]
    assert robustness["sample_count"] == 5
    assert len(robustness["seeds"]) == 5
    assert "average_waiting_seconds" in robustness["stats"]
    assert robustness["stats"]["average_waiting_seconds"]["ci_95_low"] == 17.7

    # Methodology & Limitations
    methodology = report["methodology"]
    assert "SUMO" in methodology["simulation_engine"]
    assert methodology["duration_steps"] == 300

    limitations = report["limitations"]
    assert len(limitations["modeled_caveats_en"]) >= 2
    assert "DIRECT" in limitations["data_classes_summary"]
    assert "SIMULATED" in limitations["data_classes_summary"]
    assert "OBSERVED" in limitations["data_classes_summary"]


def test_generate_decision_report_top_level_fields(mock_optimization_result):
    """Verify all top-level attributes requested by municipal specification."""
    report = generate_decision_report(mock_optimization_result, policy_id="balanced")
    assert "intervention_id" in report
    assert "baseline_metrics" in report
    assert "optimized_metrics" in report
    assert "metric_deltas" in report
    assert "policy_score" in report
    assert "policy_score_breakdown" in report
    assert "confidence" in report
    assert "recommendation" in report
    assert report["policy_score_breakdown"]["mobility"] == 22.4

    # Evidence Status & Scoring
    assert "evidence_status" in report
    ev = report["evidence_status"]
    assert ev["level"] in ["LOW", "MODERATE", "HIGH"]
    assert 0 <= ev["score"] <= 100
    assert "seed_count" in ev["criteria_breakdown"]

    # Calibration Status
    assert "calibration_status" in report
    assert report["calibration_status"]["status"] in {
        "UNCALIBRATED", "PARTIALLY_CALIBRATED", "CALIBRATED", "VALIDATED"
    }
    assert isinstance(report["calibration_status"]["traffic_calibrated"], bool)

    # Model vs Reality
    assert "model_vs_reality" in report
    mvr = report["model_vs_reality"]
    assert len(mvr["observed_metrics"]) >= 2
    assert len(mvr["simulated_metrics"]) >= 3
    assert len(mvr["derived_metrics"]) >= 2

    # Next Action
    assert "next_action" in report
    assert report["next_action"]["action_code"] == "FIELD_DETECTOR_VALIDATION"
    assert report["next_action"]["priority"] == "HIGH"

    # Municipal Disclaimer
    assert "municipal_disclaimer_en" in report
    assert "simulation-supported" in report["municipal_disclaimer_en"].lower()
    assert "municipal_disclaimer_ru" in report



def test_generate_decision_report_from_experiment():
    """Verify decision report generation directly from a multi-scenario experiment result."""
    experiment_result = {
        "experiment_id": "EXP-MUNICIPAL-2026",
        "name": "Corridor Peak Capacity Benchmark",
        "scenario": "evening_peak",
        "duration": 300,
        "traffic_levels": [0.8, 1.0, 1.2],
        "conditions": [
            {
                "condition_id": "c1",
                "traffic_multiplier": 1.0,
                "intervention_id": "control",
                "intervention_label": "Control (Baseline)",
                "evaluation_mode": "DIRECT",
                "status": "COMPLETED",
                "control_metrics": {
                    "average_speed_kmh": 20.0,
                    "average_waiting_seconds": 30.0,
                    "average_travel_time_seconds": 130.0,
                    "stops_per_vehicle": 1.6,
                    "throughput_vehicles_per_hour": 1700.0,
                    "co2_kg": 20.0,
                },
                "scenario_metrics": {
                    "average_speed_kmh": 20.0,
                    "average_waiting_seconds": 30.0,
                    "average_travel_time_seconds": 130.0,
                    "stops_per_vehicle": 1.6,
                    "throughput_vehicles_per_hour": 1700.0,
                    "co2_kg": 20.0,
                },
                "metric_deltas": {},
            },
            {
                "condition_id": "c2",
                "traffic_multiplier": 1.0,
                "intervention_id": "green_wave_coordination_0s_signal_timing",
                "intervention_label": "Green Wave Coordination",
                "evaluation_mode": "SIMULATED",
                "status": "COMPLETED",
                "control_metrics": {
                    "average_speed_kmh": 20.0,
                    "average_waiting_seconds": 30.0,
                    "average_travel_time_seconds": 130.0,
                    "stops_per_vehicle": 1.6,
                    "throughput_vehicles_per_hour": 1700.0,
                    "co2_kg": 20.0,
                },
                "scenario_metrics": {
                    "average_speed_kmh": 26.0,
                    "average_waiting_seconds": 20.0,
                    "average_travel_time_seconds": 95.0,
                    "stops_per_vehicle": 0.9,
                    "throughput_vehicles_per_hour": 2050.0,
                    "co2_kg": 16.5,
                },
                "metric_deltas": {
                    "average_waiting_seconds": {"percentage": -33.3},
                    "average_travel_time_seconds": {"percentage": -26.9},
                    "throughput_vehicles_per_hour": {"percentage": 20.5},
                    "co2_kg": {"percentage": -17.5},
                },
            },
        ],
        "summary": {"status": "COMPLETED", "total": 2, "completed": 2, "failed": 0},
    }

    report = generate_decision_report(experiment_result, policy_id="balanced")
    assert report["experiment_id"] == "EXP-MUNICIPAL-2026"
    assert report["intervention_id"] == "green_wave_coordination_0s_signal_timing"
    assert report["policy_audit"]["constraint_status"] == "PASS"
    assert len(report["metric_comparison"]) >= 10
    # These are two experiment conditions, not independent stochastic seed
    # samples. The report must not invent a confidence interval from them.
    assert report["robustness"]["sample_count"] == 0
    assert report["robustness"]["state"] == "NOT_EVALUATED"


def test_generate_decision_report_bilingual_ru(mock_optimization_result):
    """Verify decision report generation in Russian."""
    report = generate_decision_report(mock_optimization_result, policy_id="balanced", language="ru")
    assert "Ташкент" in report["executive_summary"]["scenario_name_ru"]
    assert "БАЛАНС" in report["executive_summary"]["policy_name_ru"]
    assert "Зеленая волна" in report["executive_summary"]["recommended_intervention_ru"]
