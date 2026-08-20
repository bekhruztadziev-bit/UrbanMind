import pytest
from unittest.mock import patch, MagicMock

from app.services.simulation.models import SimulationMetrics, RawSimulationResult, SimulationRequest
from app.services.simulation.metrics import calculate_metrics, estimate_candidate_metrics
from app.services.simulation.interventions import get_candidate_interventions
from app.services.simulation.optimizer import evaluate_candidates, rank_candidates
from app.services.simulation.policies import evaluate_policy_score, BALANCED_POLICY
from app.services.simulation import session
from app.services.simulation.session import run_simulation


def test_metrics_calculation():
    raw_result: RawSimulationResult = {
        "steps": 3,
        "scenario": "midday",
        "simulation_time_seconds": 300.0,
        "traffic_light_count": 2,
        "traffic_light_ids": ["tl_1", "tl_2"],
        "total_speed": 20.0, # 10m/s * 2 samples
        "total_waiting": 10.0, # 5s * 2 samples
        "samples": 2,
        "max_vehicle_count": 2,
    }

    metrics = calculate_metrics(raw_result)
    
    assert metrics["steps"] == 3
    assert metrics["scenario"] == "midday"
    assert metrics["traffic_light_count"] == 2
    assert metrics["max_vehicle_count"] == 2
    
    # average_speed_mps = 20 / 2 = 10. 10 * 3.6 = 36 km/h. Midday modifier = 1.0.
    assert metrics["average_speed_kmh"] == 36.0
    # average_waiting = 10 / 2 = 5.0s
    assert metrics["average_waiting_seconds"] == 5.0
    assert metrics["simulation_time_seconds"] == 300.0


def test_metrics_derived_formulas():
    baseline = {
        "steps": 300,
        "scenario": "midday",
        "simulation_time_seconds": 300.0,
        "traffic_light_count": 5,
        "traffic_light_ids": ["1", "2"],
        "max_vehicle_count": 100,
        "average_speed_kmh": 20.0,
        "average_waiting_seconds": 30.0,
        "co2_kg": 150.0,
        "nox_g": 80.0,
        "noise_db": 65.0,
        "pedestrian_delay_seconds": 25.0,
        "accessibility_score": 50.0
    }
    
    intervention = {"type": "school_zone_slowdown", "category": "safety"}
    estimated = estimate_candidate_metrics(baseline, intervention)
    
    # Check that estimated metrics applied the multipliers correctly
    # speed * 0.9 = 18.0
    assert estimated["average_speed_kmh"] == 18.0
    # wait * 0.82 = 24.6
    assert estimated["average_waiting_seconds"] == 24.6


def test_metrics_edge_cases():
    # Test zero vehicles
    raw_result: RawSimulationResult = {
        "steps": 1,
        "scenario": "midday",
        "simulation_time_seconds": 10.0,
        "traffic_light_count": 0,
        "traffic_light_ids": [],
        "total_speed": 0.0,
        "total_waiting": 0.0,
        "samples": 0,
        "max_vehicle_count": 0,
    }

    metrics = calculate_metrics(raw_result)
    assert metrics["average_speed_kmh"] == 0.0
    assert metrics["average_waiting_seconds"] == 0.0


def test_interventions_registry():
    interventions = get_candidate_interventions("tl_1", 0)
    assert len(interventions) == 4
    
    # Check structure
    for i in interventions:
        assert "type" in i
        assert "category" in i
        assert "label" in i
        assert "seconds" in i
        assert "evaluation_mode" in i
        if i["type"] in ["extend_green", "reduce_green"]:
            assert "traffic_light_id" in i
            assert "phase_index" in i
        assert i["evaluation_mode"] == "SIMULATED"


def test_simulation_requires_sumo(monkeypatch):
    monkeypatch.setattr(session, "SUMO_HOME", None)
    with pytest.raises(RuntimeError, match="SUMO_HOME"):
        run_simulation({"steps": 1, "measurement_steps": 1, "scenario": "midday"})


def test_optimizer_scoring_and_ranking():
    baseline = {
        "average_waiting_seconds": 30.0,
        "average_speed_kmh": 25.0,
        "co2_kg": 50.0,
        "pedestrian_delay_seconds": 15.0,
        "accessibility_score": 80.0
    }
    
    m1 = {
        "average_waiting_seconds": 15.0, # 50% improvement
        "average_speed_kmh": 32.0,
        "co2_kg": 45.0,
        "pedestrian_delay_seconds": 12.0,
        "accessibility_score": 85.0
    }
    eval1 = evaluate_policy_score(baseline, m1, BALANCED_POLICY)
    
    m2 = {
        "average_waiting_seconds": 45.0, # 50% worsening
        "average_speed_kmh": 15.0,
        "co2_kg": 65.0,
        "pedestrian_delay_seconds": 22.0,
        "accessibility_score": 60.0
    }
    eval2 = evaluate_policy_score(baseline, m2, BALANCED_POLICY)
    
    assert eval1["overall_score"] > eval2["overall_score"] # m1 should be better (higher score)

def test_optimizer_best_candidate_selection():
    baseline = {
        "steps": 10, "scenario": "midday", "simulation_time_seconds": 10.0,
        "traffic_light_count": 1, "traffic_light_ids": ["tl_1"], "max_vehicle_count": 10,
        "average_speed_kmh": 20.0, "average_waiting_seconds": 30.0, "co2_kg": 100.0,
        "nox_g": 50.0, "noise_db": 60.0, "pedestrian_delay_seconds": 20.0, "accessibility_score": 60.0
    }
    interventions = get_candidate_interventions("tl_1", 0)
    
    # Mock evaluations
    candidate_results = []
    for count, entry in enumerate(interventions):
        speed = 25.0 if count == 0 else 15.0
        waiting = 20.0 if count == 0 else 40.0
        metrics = {
            "steps": 10, "scenario": "midday", "simulation_time_seconds": 10.0,
            "traffic_light_count": 1, "traffic_light_ids": ["tl_1"], "max_vehicle_count": 10,
            "average_speed_kmh": speed, "average_waiting_seconds": waiting, "co2_kg": 90.0,
            "nox_g": 40.0, "noise_db": 55.0, "pedestrian_delay_seconds": 15.0, "accessibility_score": 70.0
        }
        candidate_results.append((entry, metrics))
        
    evaluated = evaluate_candidates(baseline, candidate_results)
    res = rank_candidates("midday", baseline, evaluated)
    
    assert res["baseline"]["average_speed_kmh"] == 20.0
    assert len(res["candidates"]) == 4
    assert len(res["ranked_candidates"]) == 4
    
    assert res["best_candidate"] is not None
    assert "selected_reason" in res["best_candidate"]


@patch("app.services.simulation.session.traci")
@patch("app.services.simulation.session._ensure_sumo_ready")
def test_session_lifecycle(mock_ensure, mock_traci_session):
    mock_traci_session.trafficlight.getIDList.return_value = []
    mock_traci_session.vehicle.getIDList.return_value = []
    mock_traci_session.simulation.getTime.return_value = 5.0
    
    request: SimulationRequest = {"steps": 5, "scenario": "midday"}
    result = run_simulation(request)
    
    # Verify traci start and close are called
    mock_ensure.assert_called_once()
    mock_traci_session.start.assert_called_once()
    assert mock_traci_session.simulationStep.call_count == 5
    mock_traci_session.close.assert_called_once()
    
    assert result["steps"] == 5
    assert result["simulation_time_seconds"] == 5.0


@patch("app.services.simulation.session.traci")
@patch("app.services.simulation.session._ensure_sumo_ready")
def test_session_lifecycle_exception(mock_ensure, mock_traci_session):
    mock_traci_session.simulationStep.side_effect = Exception("Sim failed")
    
    request: SimulationRequest = {"steps": 5, "scenario": "midday"}
    with pytest.raises(Exception):
        run_simulation(request)
    
    mock_traci_session.start.assert_called_once()
    # Close should be called even on exception because of the try...finally block
    mock_traci_session.close.assert_called_once()


@patch("app.services.simulation.service.run_simulation")
def test_scenario_workflow_delta_calculation(mock_run_sim):
    # Mock baseline and scenario results
    def run_sim_side_effect(req):
        mult = req.get("traffic_multiplier", 1.0)
        return {
            "steps": 10, "scenario": "midday", "simulation_time_seconds": 10.0,
            "traffic_light_count": 1, "traffic_light_ids": ["tl_1"], 
            "max_vehicle_count": int(10 * mult),
            "total_speed": 200.0 * mult, 
            "total_waiting": 300.0 * mult,
            "samples": int(10 * mult) if mult > 0 else 1,
        }

    mock_run_sim.side_effect = run_sim_side_effect
    
    request = {
        "duration": 300,
        "traffic_multiplier": 1.2,
        "intervention_id": None
    }
    
    from app.services.simulation.service import run_scenario_workflow
    result = run_scenario_workflow(request)
    
    assert "normal_baseline" in result
    assert "control" in result
    assert "scenario" in result
    assert "deltas" in result
    
    # 10 vehicles originally -> 12 max_vehicle_count in scenario
    # control max_vehicle_count is 12 because multiplier is 1.2
    assert result["control"]["max_vehicle_count"] == 12
    assert result["scenario"]["max_vehicle_count"] == 12
    
    assert result["deltas"]["max_vehicle_count"]["absolute"] == 0
    assert result["deltas"]["max_vehicle_count"]["percentage"] == 0.0
