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


def test_scenario_run_endpoint():
    payload = {
        "intervention_id": "green_wave_coordination_0s_signal_timing",
        "traffic_multiplier": 1.0,
        "duration": 300,
        "warmup_steps": 0,
        "measurement_steps": 300,
    }
    response = client.post("/api/scenario/run", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "traffic_multiplier" in data
    assert "control_metrics" in data
    assert "scenario_metrics" in data
    assert "metric_deltas" in data


def test_experiment_run_endpoint_minimal():
    payload = {
        "name": "Test Mini Experiment",
        "traffic_levels": [1.0],
        "intervention_ids": ["extend_green_5s_signal_timing"],
        "duration": 300,
        "warmup_steps": 0,
        "measurement_steps": 300,
    }
    response = client.post("/api/experiments/run", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "experiment_id" in data
    assert "conditions" in data
    assert len(data["conditions"]) >= 1
    assert "summary" in data
    assert data["summary"]["status"] in ["COMPLETED", "PARTIALLY_COMPLETED"]
