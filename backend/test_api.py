import os

from fastapi.testclient import TestClient

os.environ.setdefault("SUMO_HOME", r"C:\Users\user\Downloads\sumo-win64-1.27.1\sumo-1.27.1")

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_metrics_endpoint_returns_real_data():
    response = client.post("/api/metrics")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["steps"] >= 1
    assert "average_speed_kmh" in payload
    assert "average_waiting_seconds" in payload
    assert "co2_kg" in payload
    assert "nox_g" in payload
    assert "noise_db" in payload
    assert "pedestrian_delay_seconds" in payload
    assert "accessibility_score" in payload
    assert "traffic_light_count" in payload
    assert payload["traffic_light_count"] >= 0


def test_optimize_endpoint_returns_candidates_and_best():
    response = client.post("/api/optimize")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "baseline" in payload
    assert "candidates" in payload and len(payload["candidates"]) >= 1
    assert "best_candidate" in payload
    assert payload["best_candidate"]["id"]
    assert payload["best_candidate"]["category"]
    assert "co2_kg" in payload["baseline"]
    assert "accessibility_score" in payload["baseline"]


def test_optimize_handles_ai_unavailable_fallback():
    previous = os.environ.get("GEMINI_API_KEY")
    os.environ.pop("GEMINI_API_KEY", None)
    try:
        response = client.post("/api/optimize")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert "ai" in payload
        ai = payload["ai"]
        assert "AI analysis unavailable" in ai["recommendation"] or "AI analysis unavailable" in ai["reasoning"]
        assert "signal_focus" in ai
        assert "best_signal_id" in ai
    finally:
        if previous is not None:
            os.environ["GEMINI_API_KEY"] = previous


def test_optimize_explanation_contains_signal_specific_reasoning():
    response = client.post("/api/optimize")
    assert response.status_code == 200, response.text
    payload = response.json()
    ai = payload["ai"]
    assert "signal_focus" in ai
    assert isinstance(ai["signal_focus"], str)
    assert len(ai["signal_focus"]) > 10


def test_ai_explain_endpoint():
    payload = {
        "baseline": {"average_speed_kmh": 25.0, "average_waiting_seconds": 30.0},
        "candidates": [{"id": "extend_green_5s_mobility"}],
        "best_candidate": {"id": "extend_green_5s_mobility", "description": "Extend Green Phase by 5s"},
    }
    response = client.post("/api/ai/explain", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "recommendation" in data
    assert "reasoning" in data
    assert "tradeoffs" in data
    assert isinstance(data["tradeoffs"], list)
    assert "provenance" in data
    assert data["provenance"] == "ANALYTICAL INTERPRETATION"

