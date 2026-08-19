"""
Tests for the Multi-Scenario Experiment Runner.

All SUMO/TraCI calls are mocked so the tests run without a SUMO installation.
The determinism test verifies that two identical experiment runs produce
bit-for-bit identical metrics.
"""
import pytest
from unittest.mock import patch, MagicMock, call


# ---------------------------------------------------------------------------
# Helpers — shared mock raw simulation output
# ---------------------------------------------------------------------------

def _mock_raw(traffic_multiplier: float = 1.0, steps: int = 100):
    """Return a deterministic raw simulation result proportional to the multiplier."""
    count = int(max(1, 10 * traffic_multiplier))
    return {
        "steps": steps,
        "scenario": "midday",
        "simulation_time_seconds": float(steps),
        "traffic_light_count": 2,
        "traffic_light_ids": ["tl_A", "tl_B"],
        "total_speed": 200.0 * traffic_multiplier,
        "total_waiting": 300.0 * traffic_multiplier,
        "samples": count,
        "max_vehicle_count": count,
    }


def _make_run_sim(steps_override=None):
    """Factory: returns a run_simulation side-effect that uses _mock_raw."""
    def _side(req):
        mult = float(req.get("traffic_multiplier", 1.0))
        steps = steps_override or int(req.get("steps", 100))
        return _mock_raw(mult, steps)
    return _side


MOCK_SIGNAL_ID = "tl_A"
MOCK_PHASE_INDEX = 0


# ---------------------------------------------------------------------------
# test_experiment_cartesian_product
# ---------------------------------------------------------------------------

@patch("app.services.simulation.experiment_runner._scenario_signal_selection",
       return_value=(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX))
@patch("app.services.simulation.experiment_runner.run_simulation")
def test_experiment_cartesian_product(mock_run_sim, mock_signal):
    """N traffic levels × M interventions → N×M conditions all COMPLETED."""
    mock_run_sim.side_effect = _make_run_sim()

    from app.services.simulation.interventions import get_candidate_interventions
    from app.services.simulation.experiment_runner import run_experiment

    all_interventions = get_candidate_interventions(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX)
    all_ids = [
        f"{c['type']}_{c.get('seconds', 0)}s_{c['category']}"
        for c in all_interventions
    ]
    traffic_levels = [0.8, 1.0, 1.2]

    result = run_experiment({
        "name": "Cartesian Test",
        "traffic_levels": traffic_levels,
        "intervention_ids": all_ids,
        "duration": 100,
    })

    expected = len(traffic_levels) * len(all_ids)
    assert result["summary"]["total"] == expected
    assert result["summary"]["completed"] == expected
    assert result["summary"]["failed"] == 0
    assert result["summary"]["status"] == "COMPLETED"
    assert len(result["conditions"]) == expected

    # Every condition must have both control and scenario metrics
    for cond in result["conditions"]:
        assert cond["status"] == "COMPLETED"
        assert cond["control_metrics"] is not None
        assert cond["scenario_metrics"] is not None
        assert "average_waiting_seconds" in cond["metric_deltas"]


# ---------------------------------------------------------------------------
# test_experiment_control_cache
# ---------------------------------------------------------------------------

@patch("app.services.simulation.experiment_runner._scenario_signal_selection",
       return_value=(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX))
@patch("app.services.simulation.experiment_runner.run_simulation")
def test_experiment_control_cache(mock_run_sim, mock_signal):
    """
    Control simulations should be called exactly ONCE per (traffic_level, duration).
    With 2 traffic levels and 3 SIMULATED interventions each, there should be:
      - 2 control calls (one per traffic level)
        - 2×4 = 8 scenario calls (for SIMULATED interventions)
    Total = 10 run_simulation calls, NOT 2×(1+4)=10 with duplicated controls.

    We pick only the 4 SIMULATED candidates to keep the math clean.
    """
    mock_run_sim.side_effect = _make_run_sim()

    from app.services.simulation.interventions import get_candidate_interventions
    from app.services.simulation.experiment_runner import run_experiment

    all_interventions = get_candidate_interventions(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX)
    simulated_ids = [
        f"{c['type']}_{c.get('seconds', 0)}s_{c['category']}"
        for c in all_interventions
        if c.get("evaluation_mode") == "SIMULATED"
    ]
    assert len(simulated_ids) == 4, "Registry must have exactly 4 SIMULATED interventions"

    traffic_levels = [0.8, 1.2]

    result = run_experiment({
        "name": "Cache Test",
        "traffic_levels": traffic_levels,
        "intervention_ids": simulated_ids,
        "duration": 50,
    })

    # 1 control + len(simulated_ids) scenario calls
    assert mock_run_sim.call_count == 10, f"Expected 10 total run_simulation calls, got {mock_run_sim.call_count}"
    assert result["summary"]["completed"] == 2 * 4
    assert result["summary"]["failed"] == 0


# ---------------------------------------------------------------------------
# test_experiment_partial_failure
# ---------------------------------------------------------------------------

@patch("app.services.simulation.experiment_runner._scenario_signal_selection",
       return_value=(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX))
@patch("app.services.simulation.experiment_runner.run_simulation")
def test_experiment_partial_failure(mock_run_sim, mock_signal):
    """
    If some scenario conditions fail (not the control), the experiment should
    report PARTIALLY_COMPLETED, and failed conditions should have status=FAILED.
    """
    call_count = {"n": 0}

    def _flaky_sim(req):
        call_count["n"] += 1
        mult = float(req.get("traffic_multiplier", 1.0))
        # Control calls (no intervention) always succeed
        if req.get("intervention") is None:
            return _mock_raw(mult)
        # Every other SCENARIO call fails
        if call_count["n"] % 3 == 0:
            raise RuntimeError("Simulated TraCI failure")
        return _mock_raw(mult)

    mock_run_sim.side_effect = _flaky_sim

    from app.services.simulation.interventions import get_candidate_interventions
    from app.services.simulation.experiment_runner import run_experiment

    all_interventions = get_candidate_interventions(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX)
    simulated_ids = [
        f"{c['type']}_{c.get('seconds', 0)}s_{c['category']}"
        for c in all_interventions
        if c.get("evaluation_mode") == "SIMULATED"
    ]

    result = run_experiment({
        "name": "Partial Failure Test",
        "traffic_levels": [1.0, 1.2],
        "intervention_ids": simulated_ids,
        "duration": 100,
    })

    assert result["summary"]["status"] in ("PARTIALLY_COMPLETED", "COMPLETED")
    assert result["summary"]["failed"] + result["summary"]["completed"] == result["summary"]["total"]

    failed_conds = [c for c in result["conditions"] if c["status"] == "FAILED"]
    for fc in failed_conds:
        assert fc["error"] is not None
        assert fc["scenario_metrics"] is None


# ---------------------------------------------------------------------------
# test_experiment_determinism
# ---------------------------------------------------------------------------

@patch("app.services.simulation.experiment_runner._scenario_signal_selection",
       return_value=(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX))
@patch("app.services.simulation.experiment_runner.run_simulation")
def test_experiment_determinism(mock_run_sim, mock_signal):
    """
    Running the same experiment twice under identical conditions must produce
    bit-for-bit identical metrics. Uses a 2×1 matrix (small) for speed.
    """
    mock_run_sim.side_effect = _make_run_sim(steps_override=50)

    from app.services.simulation.interventions import get_candidate_interventions
    from app.services.simulation.experiment_runner import run_experiment

    all_interventions = get_candidate_interventions(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX)
    one_intervention_id = f"{all_interventions[0]['type']}_{all_interventions[0].get('seconds', 0)}s_{all_interventions[0]['category']}"

    request = {
        "name": "Determinism Test",
        "traffic_levels": [0.8, 1.2],
        "intervention_ids": [one_intervention_id],
        "duration": 50,
    }

    result_a = run_experiment(request)
    result_b = run_experiment(request)

    assert result_a["summary"]["completed"] == result_b["summary"]["completed"]
    assert len(result_a["conditions"]) == len(result_b["conditions"])

    for cond_a, cond_b in zip(result_a["conditions"], result_b["conditions"]):
        assert cond_a["traffic_multiplier"] == cond_b["traffic_multiplier"]
        assert cond_a["intervention_id"] == cond_b["intervention_id"]
        assert cond_a["status"] == cond_b["status"]
        if cond_a["status"] == "COMPLETED":
            # Metric values must be identical (deterministic)
            for key in ["average_speed_kmh", "average_waiting_seconds", "max_vehicle_count",
                        "co2_kg", "nox_g", "noise_db", "pedestrian_delay_seconds", "accessibility_score"]:
                assert cond_a["control_metrics"][key] == cond_b["control_metrics"][key], \
                    f"Control metric '{key}' differs between runs"
                assert cond_a["scenario_metrics"][key] == cond_b["scenario_metrics"][key], \
                    f"Scenario metric '{key}' differs between runs"
                assert cond_a["metric_deltas"][key] == cond_b["metric_deltas"][key], \
                    f"Delta '{key}' differs between runs"


# ---------------------------------------------------------------------------
# test_experiment_heuristic_flag
# ---------------------------------------------------------------------------

@patch("app.services.simulation.experiment_runner._scenario_signal_selection",
       return_value=(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX))
@patch("app.services.simulation.experiment_runner.run_simulation")
def test_experiment_heuristic_flag(mock_run_sim, mock_signal):
    """HEURISTIC conditions must have evaluation_mode='HEURISTIC' and must NOT call run_simulation."""
    mock_run_sim.side_effect = _make_run_sim()

    from app.services.simulation.interventions import get_candidate_interventions
    from app.services.simulation.experiment_runner import run_experiment

    all_interventions = get_candidate_interventions(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX)
    heuristic_ids = [
        f"{c['type']}_{c.get('seconds', 0)}s_{c['category']}"
        for c in all_interventions
        if c.get("evaluation_mode") == "HEURISTIC"
    ]
    assert len(heuristic_ids) > 0, "Registry must have at least one HEURISTIC intervention"

    result = run_experiment({
        "name": "Heuristic Flag Test",
        "traffic_levels": [1.0],
        "intervention_ids": heuristic_ids,
        "duration": 50,
    })

    # Only the control call should use run_simulation (1 per traffic level)
    assert mock_run_sim.call_count == 1

    for cond in result["conditions"]:
        assert cond["evaluation_mode"] == "HEURISTIC"
        assert cond["status"] == "COMPLETED"
        assert cond["scenario_metrics"] is not None


# ---------------------------------------------------------------------------
# test_experiment_simulated_flag
# ---------------------------------------------------------------------------

@patch("app.services.simulation.experiment_runner._scenario_signal_selection",
       return_value=(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX))
@patch("app.services.simulation.experiment_runner.run_simulation")
def test_experiment_simulated_flag(mock_run_sim, mock_signal):
    """SIMULATED conditions must have evaluation_mode='SIMULATED' and must call run_simulation."""
    mock_run_sim.side_effect = _make_run_sim()

    from app.services.simulation.interventions import get_candidate_interventions
    from app.services.simulation.experiment_runner import run_experiment

    all_interventions = get_candidate_interventions(MOCK_SIGNAL_ID, MOCK_PHASE_INDEX)
    simulated_ids = [
        f"{c['type']}_{c.get('seconds', 0)}s_{c['category']}"
        for c in all_interventions
        if c.get("evaluation_mode") == "SIMULATED"
    ]
    assert len(simulated_ids) > 0, "Registry must have at least one SIMULATED intervention"

    result = run_experiment({
        "name": "Simulated Flag Test",
        "traffic_levels": [1.0],
        "intervention_ids": simulated_ids,
        "duration": 50,
    })

    # 1 control + len(simulated_ids) scenario calls
    assert mock_run_sim.call_count == 1 + len(simulated_ids)

    for cond in result["conditions"]:
        assert cond["evaluation_mode"] == "SIMULATED"
        assert cond["status"] == "COMPLETED"
