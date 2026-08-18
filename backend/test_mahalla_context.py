from app.services.ai import explain_results
from app.services.mahalla_data import get_mahalla_data


def test_mahalla_bounds_cover_a_broader_neighborhood_context():
    data = get_mahalla_data()
    bounds = data["bounds"]

    assert bounds["southwest"][0] <= 41.308
    assert bounds["northeast"][0] >= 41.325
    assert bounds["southwest"][1] <= 69.258
    assert bounds["northeast"][1] >= 69.276


def test_explain_results_returns_structured_fallback_when_no_ai_key_is_set():
    baseline = {"average_speed_kmh": 18.5, "average_waiting_seconds": 32.0}
    candidates = [{"id": "candidate_a"}, {"id": "candidate_b"}]
    best = {"id": "candidate_a", "metrics": {"average_speed_kmh": 23.4, "average_waiting_seconds": 18.1}}

    explanation = explain_results(baseline, candidates, best)

    assert set(["recommendation", "reasoning", "tradeoffs", "confidence"]).issubset(explanation)
    assert isinstance(explanation["tradeoffs"], list)
    assert explanation["recommendation"]
