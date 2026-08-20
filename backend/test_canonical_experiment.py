import os
import pytest

os.environ.setdefault("SUMO_HOME", r"C:\Users\user\Downloads\sumo-win64-1.27.1\sumo-1.27.1")

from app.services.simulation.canonical import (
    get_canonical_experiment_config,
    run_canonical_experiment,
    DEFAULT_CANONICAL_EXPERIMENT_ID,
)


@pytest.fixture(scope="module")
def canonical_result():
    cfg = get_canonical_experiment_config()
    cfg["simulation_duration"] = 60
    cfg["warmup_steps"] = 10
    cfg["measurement_steps"] = 50
    cfg["seeds"] = [42, 101, 2024]
    return run_canonical_experiment(cfg, language="en")


def test_canonical_experiment_config_immutability():
    cfg = get_canonical_experiment_config()
    assert cfg["experiment_id"] == DEFAULT_CANONICAL_EXPERIMENT_ID
    assert cfg["is_immutable"] is True
    assert cfg["demand_multipliers"] == [0.8, 1.0, 1.2]
    assert set(cfg["policies"]) == {"flow", "eco", "balanced"}
    assert len(cfg["seeds"]) >= 2
    assert cfg["spatial_scope"]["id"] == "central_corridor"
    assert "simulation_configuration_hash" in cfg
    assert "primary_outcome_metrics" in cfg
    assert "secondary_outcome_metrics" in cfg
    assert "average_waiting_seconds" in cfg["primary_outcome_metrics"]
    assert "co2_kg" in cfg["secondary_outcome_metrics"]


def test_canonical_experiment_execution_shared_evidence(canonical_result):
    assert canonical_result["experiment_id"] == DEFAULT_CANONICAL_EXPERIMENT_ID
    assert "0.8x" in canonical_result["baseline_results"]
    assert "1.0x" in canonical_result["baseline_results"]
    assert "1.2x" in canonical_result["baseline_results"]
    
    # Check policy results exist for each demand level
    for demand_str in ["0.8x", "1.0x", "1.2x"]:
        assert demand_str in canonical_result["policy_results"]
        policy_map = canonical_result["policy_results"][demand_str]
        assert "flow" in policy_map
        assert "eco" in policy_map
        assert "balanced" in policy_map
        
        # Verify deterministic winner and why_won
        for p_id in ["flow", "eco", "balanced"]:
            item = policy_map[p_id]
            assert item["policy_id"] == p_id
            assert "best_candidate_id" in item
            assert item["best_candidate_score"] >= 0 or item["best_candidate_score"] < 0
            assert len(item["why_won"]) > 0


def test_canonical_experiment_robustness_metrics(canonical_result):
    robustness = canonical_result.get("robustness", {})
    assert robustness["sample_count"] >= 2
    assert len(robustness["seeds"]) >= 2
    assert robustness.get("multi_seed_evaluated") is True
    assert "Student-t" in robustness.get("statistical_method", "")
    assert robustness.get("t_critical") == pytest.approx(4.303, 0.01)
    
    stats = robustness.get("stats", {})
    assert len(stats) > 0
    for cand_id, stat in stats.items():
        assert "mean_delay_s" in stat
        assert "std_dev_s" in stat
        assert "ci_95_low" in stat
        assert "ci_95_high" in stat
        assert stat["ci_95_low"] <= stat["ci_95_high"]
        assert "Student-t" in stat.get("ci_method", "")


def test_canonical_experiment_evidence_strength_rubric(canonical_result):
    es = canonical_result.get("evidence_strength", {})
    assert "rubric_name" in es
    assert "Decision-Support Rubric" in es["rubric_name"]
    assert "criteria_breakdown" in es
    assert "seed_robustness" in es["criteria_breakdown"]
    assert "score_interpretation_note_en" in es


def test_canonical_experiment_calibration_status_integrity(canonical_result):
    calib = canonical_result.get("calibration_status", {})
    assert calib["status"] in ("UNCALIBRATED", "PARTIALLY_CALIBRATED", "CALIBRATED", "VALIDATED")
    assert "explanation_en" in calib
    assert len(calib["methodology_caveats_en"]) > 0

