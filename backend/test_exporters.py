import pytest
import json
from app.services.reports.generator import generate_decision_report
from app.services.reports.exporter import export_report_json, export_report_csv, export_report_html


@pytest.fixture
def sample_report():
    opt_result = {
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
                    {"name": "Average Delay", "name_ru": "Задержка", "value": -28.0, "unit": "%"}
                ],
                "worsened": [
                    {"name": "Pedestrian Delay", "name_ru": "Задержка пешеходов", "value": +4.1, "unit": "%"}
                ],
                "unchanged": [],
                "verdict_en": "Balanced multi-objective operational profile.",
                "verdict_ru": "Сбалансированный многокритериальный операционный профиль.",
            },
            "robustness_sample_count": 3,
            "robustness_seeds": [42, 101, 2024],
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
    return generate_decision_report(opt_result, policy_id="balanced")


def test_export_report_json(sample_report):
    """Verify JSON export produces valid JSON string containing all required fields."""
    json_str = export_report_json(sample_report)
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data["report_id"] == sample_report["report_id"]
    assert "executive_summary" in data
    assert "policy_audit" in data
    assert "metric_comparison" in data
    assert "robustness" in data
    assert "methodology" in data
    assert "limitations" in data


def test_export_report_csv(sample_report):
    """Verify CSV export contains header, decision brief, model vs reality, metric comparisons, and audit."""
    csv_str = export_report_csv(sample_report)
    assert "URBANMIND DECISION REPORT" in csv_str
    assert "DECISION BRIEF" in csv_str
    assert "MODEL VS REALITY" in csv_str
    assert "POLICY AUDIT & OBJECTIVES" in csv_str
    assert "METRIC COMPARISON" in csv_str
    assert "Average Delay" in csv_str
    assert "ROBUSTNESS & STATISTICAL EVIDENCE" in csv_str
    assert "MUNICIPAL DISCLAIMER" in csv_str


def test_export_report_html_en(sample_report):
    """Verify HTML export produces printable document in English with @media print styling."""
    html = export_report_html(sample_report, language="en")
    assert "<!DOCTYPE html>" in html
    assert "@media print" in html
    assert "MUNICIPAL DECISION REPORT" in html
    assert "Decision Brief" in html
    assert "Model vs Reality" in html
    assert "Key Metrics Comparison" in html
    assert "Statistical Evidence & Robustness" in html
    assert "Methodology & Modeling Assumptions" in html
    assert sample_report["report_id"] in html


def test_export_report_html_ru(sample_report):
    """Verify HTML export produces printable document in Russian."""
    html = export_report_html(sample_report, language="ru")
    assert "ОТЧЕТ О ПРИНЯТИИ РЕШЕНИЯ" in html
    assert "Decision Brief" in html
    assert "Классификация данных" in html
    assert "Сравнение ключевых метрик" in html
    assert "Методология и ограничения" in html



def test_export_report_html_without_ai(sample_report):
    """Verify HTML export functions properly when AI analysis is None."""
    sample_report["ai_analysis"] = None
    html = export_report_html(sample_report, language="en")
    assert "<!DOCTYPE html>" in html
    assert sample_report["report_id"] in html
