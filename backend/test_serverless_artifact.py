from app.services.simulation import service


def test_locked_canonical_optimization_supports_cloud_policies(monkeypatch):
    monkeypatch.setattr(service, "_is_sumo_available", lambda: False)

    for policy in ("flow", "eco", "balanced"):
        result = service.run_optimization_workflow(policy=policy, language="en")
        assert result["evidence_mode"] == "PRECOMPUTED_SIMULATION_ARTIFACT"
        assert result["runtime_status"] == "SUMO_UNAVAILABLE_LOCKED_EVIDENCE"
        assert result["baseline"]["is_fallback"] is False
        assert result["ranked_candidates"]
        assert result["best_candidate"]["id"] == result["ranked_candidates"][0]["id"]
        assert set(result["policy_comparison"]) == {"flow", "eco", "balanced"}


def test_locked_canonical_optimization_does_not_claim_custom_evidence(monkeypatch):
    monkeypatch.setattr(service, "_is_sumo_available", lambda: False)

    try:
        service.run_optimization_workflow(policy="custom", language="en")
    except RuntimeError as exc:
        assert "Custom policy optimization requires a live SUMO runtime" in str(exc)
    else:
        raise AssertionError("Custom policy must not reuse a non-custom evidence set")


def test_locked_canonical_metrics_supply_nonzero_baseline_for_cloud_dashboard(monkeypatch):
    monkeypatch.setattr(service, "_is_sumo_available", lambda: False)

    result = service.run_metrics_workflow()

    assert result["evidence_mode"] == "PRECOMPUTED_SIMULATION_ARTIFACT"
    assert result["runtime_status"] == "SUMO_UNAVAILABLE_LOCKED_EVIDENCE"
    assert result["is_fallback"] is False
    assert result["average_speed_kmh"] > 0
    assert result["average_waiting_seconds"] > 0
    assert result["average_travel_time_seconds"] > 0
