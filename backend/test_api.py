import os
from fastapi.testclient import TestClient

os.environ.setdefault("SUMO_HOME", r"C:\Users\user\Downloads\sumo-win64-1.27.1\sumo-1.27.1")

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_interventions_registry_endpoint():
    response = client.get("/api/experiments/interventions")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 1
    assert "id" in payload[0]
    assert "evaluation_mode" in payload[0]


def test_ai_explain_endpoint_en():
    payload = {
        "baseline": {
            "average_speed_kmh": 22.5,
            "average_waiting_seconds": 28.0,
            "average_travel_time_seconds": 65.0,
            "stops_per_vehicle": 1.5,
            "throughput_vehicles_per_hour": 500,
            "co2_kg": 15.0,
        },
        "candidates": [
            {
                "id": "green_wave_coordination_0s_signal_timing",
                "label": "Green Wave Coordination",
                "metrics": {
                    "average_speed_kmh": 26.0,
                    "average_waiting_seconds": 19.5,
                    "average_travel_time_seconds": 52.0,
                    "stops_per_vehicle": 0.9,
                    "throughput_vehicles_per_hour": 580,
                    "co2_kg": 13.2,
                },
                "delta": {
                    "delay_improvement_pct": 30.3,
                    "travel_time_improvement_pct": 20.0,
                    "stops_improvement_pct": 40.0,
                    "throughput_improvement_pct": 16.0,
                    "emissions_improvement_pct": 12.0,
                },
                "tradeoff_summary": {
                    "improved": [{"name": "Delay", "change_pct": 30.3}],
                    "worsened": [],
                },
            }
        ],
        "best_candidate": {
            "id": "green_wave_coordination_0s_signal_timing",
            "label": "Green Wave Coordination",
            "metrics": {
                "average_speed_kmh": 26.0,
                "average_waiting_seconds": 19.5,
                "average_travel_time_seconds": 52.0,
                "stops_per_vehicle": 0.9,
                "throughput_vehicles_per_hour": 580,
                "co2_kg": 13.2,
            },
            "delta": {
                "delay_improvement_pct": 30.3,
                "travel_time_improvement_pct": 20.0,
                "stops_improvement_pct": 40.0,
                "throughput_improvement_pct": 16.0,
                "emissions_improvement_pct": 12.0,
            },
            "tradeoff_summary": {
                "improved": [{"name": "Delay", "change_pct": 30.3}],
                "worsened": [],
            },
        },
        "language": "en",
    }
    response = client.post("/api/ai/explain", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "summary" in data
    assert "key_improvements" in data
    assert isinstance(data["key_improvements"], list)
    assert "tradeoffs" in data
    assert isinstance(data["tradeoffs"], list)
    assert "concerns" in data
    assert isinstance(data["concerns"], list)
    assert "recommendation" in data
    assert "confidence" in data
    assert data["status"] in ["COMPLETE", "FALLBACK"]


def test_ai_explain_endpoint_ru():
    payload = {
        "baseline": {"average_speed_kmh": 20.0, "average_waiting_seconds": 32.0},
        "candidates": [{"id": "extend_green_5s_signal_timing", "label": "Продление фазы"}],
        "best_candidate": {"id": "extend_green_5s_signal_timing", "label": "Продление фазы"},
        "language": "ru",
    }
    response = client.post("/api/ai/explain", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "summary" in data
    assert "recommendation" in data
    assert data["status"] in ["COMPLETE", "FALLBACK"]
    if not data["is_ai"]:
        assert "ПРАВИЛО-ОРИЕНТИРОВАННОЕ" in data["provenance"]


def test_policies_endpoint():
    response = client.get("/api/policies")
    assert response.status_code == 200, response.text
    policies = response.json()
    assert isinstance(policies, list)
    assert len(policies) >= 4
    policy_ids = [p["policy_id"] for p in policies]
    assert "flow" in policy_ids
    assert "eco" in policy_ids
    assert "balanced" in policy_ids
    assert "custom" in policy_ids
    for p in policies:
        assert "objective_question" in p
        assert "primary_dimensions" in p
        assert "why_won_template" in p


def test_policies_compare_endpoint():
    response = client.post("/api/policies/compare", json={"scenario": "midday", "steps": 5, "warmup_steps": 0, "measurement_steps": 5})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "policy_comparison" in data
    comp = data["policy_comparison"]
    assert "flow" in comp
    assert "eco" in comp
    assert "balanced" in comp
    assert "why_won" in comp["flow"]
    assert "why_won" in comp["eco"]
    assert "why_won" in comp["balanced"]



def test_scenario_run_endpoint():
    payload = {
        "intervention_id": "green_wave_coordination_0s_signal_timing",
        "traffic_multiplier": 1.0,
        "duration": 10,
        "warmup_steps": 0,
        "measurement_steps": 10,
    }
    response = client.post("/api/scenario/run", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "control" in data
    assert "scenario" in data
    assert "deltas" in data


def test_experiment_run_endpoint_minimal():
    payload = {
        "name": "Test Mini Experiment",
        "traffic_levels": [1.0],
        "intervention_ids": ["extend_green_5s_signal_timing"],
        "duration": 10,
        "warmup_steps": 0,
        "measurement_steps": 10,
    }
    response = client.post("/api/experiments/run", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "experiment_id" in data
    assert "conditions" in data
    assert len(data["conditions"]) >= 1
    assert "summary" in data
    assert data["summary"]["status"] in ["COMPLETED", "PARTIALLY_COMPLETED"]


def test_spatial_hierarchy_endpoint():
    response = client.get("/api/spatial/hierarchy")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == "tashkent"
    assert "districts" in data
    assert len(data["districts"]) >= 1


def test_spatial_scopes_endpoint():
    response = client.get("/api/spatial/scopes")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "default_scope" in data
    assert data["default_scope"]["id"] == "central_corridor"
    assert "cross_district_context" in data


def test_decision_report_generate_endpoint():
    payload = {
        "scenario": "midday",
        "policy": "balanced",
        "baseline": {"average_waiting_seconds": 25.0, "average_speed_kmh": 22.0, "co2_kg": 18.0},
        "best_candidate": {
            "id": "green_wave",
            "label": "Green Wave",
            "metrics": {"average_waiting_seconds": 18.0, "average_speed_kmh": 28.0, "co2_kg": 15.0},
            "policy_breakdown": {"overall_score": 15.0, "is_valid": True},
            "tradeoff_summary": {"improved": [], "worsened": []},
        },
    }
    response = client.post("/api/reports/generate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "report_id" in data
    assert "executive_summary" in data
    assert "metric_comparison" in data
    assert "policy_audit" in data


def test_decision_report_export_csv_endpoint():
    payload = {
        "scenario": "midday",
        "policy": "balanced",
        "baseline": {"average_waiting_seconds": 25.0, "average_speed_kmh": 22.0},
        "best_candidate": {
            "id": "green_wave",
            "label": "Green Wave",
            "metrics": {"average_waiting_seconds": 18.0, "average_speed_kmh": 28.0},
        },
    }
    response = client.post("/api/reports/export/csv", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "csv" in data
    assert "URBANMIND DECISION REPORT" in data["csv"]


def test_decision_report_export_html_endpoint():
    payload = {
        "scenario": "midday",
        "policy": "balanced",
        "baseline": {"average_waiting_seconds": 25.0, "average_speed_kmh": 22.0},
        "best_candidate": {
            "id": "green_wave",
            "label": "Green Wave",
            "metrics": {"average_waiting_seconds": 18.0, "average_speed_kmh": 28.0},
        },
        "language": "en",
    }
    response = client.post("/api/reports/export/html", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "html" in data
    assert "MUNICIPAL DECISION REPORT" in data["html"]


def test_pilots_endpoints():
    # 1. List
    response = client.get("/api/pilots")
    assert response.status_code == 200, response.text
    pilots = response.json()
    assert isinstance(pilots, list)
    assert len(pilots) >= 1

    # 2. Get
    pilot_id = pilots[0]["id"]
    get_res = client.get(f"/api/pilots/{pilot_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == pilot_id

    # 3. Create
    create_res = client.post("/api/pilots", json={
        "title": "API Test Pilot",
        "status": "DRAFT",
    })
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["title"] == "API Test Pilot"

    # 4. Update
    upd_res = client.post(f"/api/pilots/{created['id']}/update", json={"status": "ANALYSIS"})
    assert upd_res.status_code == 200
    assert upd_res.json()["status"] == "ANALYSIS"


def test_calibration_endpoints():
    # 1. Status
    res = client.get("/api/calibration/status")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "calibration" in data
    assert data["calibration"]["status"] in ("UNCALIBRATED", "PARTIALLY_CALIBRATED", "CALIBRATED", "VALIDATED")
    assert "model_vs_reality" in data
    assert "observed_metrics" in data["model_vs_reality"]


    # 2. Validate
    val_res = client.post("/api/calibration/validate", json={
        "observed_series": [10.0, 20.0, 30.0],
        "simulated_series": [11.0, 19.0, 32.0],
        "metric_name": "delay",
        "unit": "s",
    })
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["sample_count"] == 3
    assert val_data["mae"] is not None


def test_analytics_summary_endpoint():
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "experiments_run" in data
    assert "policies_used" in data
    assert "decision_reports_generated" in data


def test_canonical_experiment_api():
    res = client.get("/api/experiments/canonical")
    assert res.status_code == 200, res.text
    cfg = res.json()
    assert cfg["experiment_id"] == "UM-EXP-2026-001"
    assert cfg["is_immutable"] is True


def test_case_studies_api():
    # 1. Canonical
    can_res = client.get("/api/case-studies/canonical")
    assert can_res.status_code == 200, can_res.text
    cs = can_res.json()
    assert cs["case_id"] == "UM-CS-2026-001"
    assert "Central Tashkent Corridor" in cs["title"]

    # 2. List
    list_res = client.get("/api/case-studies")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Export CSV
    csv_res = client.post("/api/case-studies/export/csv", json={"case_study": cs})
    assert csv_res.status_code == 200
    assert "csv" in csv_res.json()

    # 4. Export HTML
    html_res = client.post("/api/case-studies/export/html", json={"case_study": cs})
    assert html_res.status_code == 200
    assert "<!DOCTYPE html>" in html_res.json()["html"]


def test_field_calibration_api():
    # 1. Import
    import_res = client.post("/api/calibration/import", json={
        "dataset_id": "DS-API-001",
        "name": "API Test Counts",
        "observations": [
            {"intersection_id": "intersection_1", "approach_id": "n", "movement": "through", "interval_minutes": 60, "vehicle_count": 405, "timestamp": "2026-08-20T08:00:00Z"},
            {"intersection_id": "intersection_2", "approach_id": "s", "movement": "through", "interval_minutes": 60, "vehicle_count": 380, "timestamp": "2026-08-20T08:00:00Z"},
        ]
    })
    assert import_res.status_code == 200, import_res.text
    ds = import_res.json()
    assert ds["is_valid"] is True

    # 2. Evaluate
    eval_res = client.post("/api/calibration/evaluate", json={"dataset_id": "DS-API-001"})
    assert eval_res.status_code == 200, eval_res.text
    ev = eval_res.json()
    assert ev["dataset_id"] == "DS-API-001"
    assert ev["status"] in ("PARTIALLY_CALIBRATED", "CALIBRATED")


def test_calibration_protocol_api():
    res = client.get("/api/calibration/protocol")
    assert res.status_code == 200, res.text
    proto = res.json()
    assert "protocol_id" in proto
    assert proto["recommended_duration_days"] >= 1
    assert len(proto["intersections"]) >= 1




