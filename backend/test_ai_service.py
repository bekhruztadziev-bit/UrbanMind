import os
import pytest
from unittest.mock import patch, MagicMock

from app.services.ai import explain_results, _rule_based_summary, _extract_json_from_text


def test_extract_json_from_text():
    # Raw JSON
    text1 = '{"summary": "Test", "key_improvements": ["A"], "tradeoffs": ["B"], "concerns": ["C"], "recommendation": "Rec", "confidence": "high"}'
    res1 = _extract_json_from_text(text1)
    assert res1 is not None
    assert res1["summary"] == "Test"

    # Markdown code fence JSON
    text2 = 'Here is the analysis:\n```json\n{"summary": "Markdown Test", "key_improvements": ["A"]}\n```\nHope this helps!'
    res2 = _extract_json_from_text(text2)
    assert res2 is not None
    assert res2["summary"] == "Markdown Test"

    # Invalid
    assert _extract_json_from_text("no json here") is None


def test_rule_based_summary_fallback():
    baseline = {
        "average_waiting_seconds": 24.0,
        "average_travel_time_seconds": 58.4,
        "stops_per_vehicle": 1.42,
        "throughput_vehicles_per_hour": 520,
        "co2_kg": 14.5,
    }
    best = {
        "id": "green_wave_coordination_0s_signal_timing",
        "label": "Green-Wave Corridor Coordination",
        "metrics": {
            "average_waiting_seconds": 18.0,
            "average_travel_time_seconds": 46.0,
            "stops_per_vehicle": 0.8,
            "throughput_vehicles_per_hour": 590,
            "co2_kg": 12.8,
        },
        "tradeoff_summary": {
            "improved": [{"name": "Delay", "change_pct": 25.0}],
            "worsened": []
        }
    }
    
    res_en = _rule_based_summary(baseline, [best], best, language="en")
    assert res_en["status"] == "FALLBACK"
    assert res_en["is_ai"] is False
    assert "RULE-BASED SUMMARY" in res_en["provenance"]
    assert len(res_en["key_improvements"]) >= 3
    assert len(res_en["tradeoffs"]) >= 2
    assert len(res_en["concerns"]) >= 2

    res_ru = _rule_based_summary(baseline, [best], best, language="ru")
    assert res_ru["status"] == "FALLBACK"
    assert res_ru["is_ai"] is False
    assert "ПРАВИЛО-ОРИЕНТИРОВАННОЕ РЕЗЮМЕ" in res_ru["provenance"]
    assert len(res_ru["key_improvements"]) >= 3


def test_explain_results_with_credentials_removed():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}):
        baseline = {"average_waiting_seconds": 24.0}
        candidates = [{"id": "test_1"}]
        best = {"id": "test_1", "label": "Test 1"}
        
        res = explain_results(baseline, candidates, best, language="en")
        assert res["status"] == "FALLBACK"
        assert res["is_ai"] is False
        assert "RULE-BASED" in res["provenance"]


def test_explain_results_with_mock_genai_success():
    mock_json_response = """
    ```json
    {
      "summary": "Coordinated green wave timing significantly reduces stop-and-go delays across the main corridor.",
      "key_improvements": ["Delay reduced by 25%", "Emissions reduced by 12%", "Throughput increased by 14%"],
      "tradeoffs": ["Minor queue buildup on cross-streets during rush hour."],
      "concerns": ["Validate detector loop health regularly."],
      "recommendation": "Deploy the 40 km/h green wave offset progression.",
      "confidence": "high"
    }
    ```
    """
    
    mock_response = MagicMock()
    mock_response.text = mock_json_response

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyTestKeyValid123456789"}):
        with patch("google.genai.Client", return_value=mock_client):
            baseline = {"average_waiting_seconds": 24.0, "average_travel_time_seconds": 58.0}
            best = {
                "id": "green_wave",
                "label": "Green Wave",
                "metrics": {"average_waiting_seconds": 18.0, "average_travel_time_seconds": 46.0},
                "delta": {"delay_improvement_pct": 25.0}
            }
            res = explain_results(baseline, [best], best, language="en")
            assert res["status"] == "COMPLETE"
            assert res["is_ai"] is True
            assert res["confidence"] == "high"
            assert len(res["key_improvements"]) == 3
            assert "Deploy the 40 km/h" in res["recommendation"]
