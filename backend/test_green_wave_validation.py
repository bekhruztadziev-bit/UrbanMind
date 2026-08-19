import pytest
from unittest.mock import patch, MagicMock

from app.services.simulation.session import (
    haversine_distance_meters,
    calculate_green_wave_offsets,
    _apply_intervention,
    CORRIDOR_SIGNAL_ORDER,
)
from app.services.simulation.optimizer import analyze_tradeoffs
from app.services.simulation.experiment_runner import compute_statistical_summary
from app.services.simulation.models import CandidateDelta, SimulationMetrics


def test_haversine_distance():
    # Amir Temur to School Junction in Tashkent
    coord1 = (41.3168, 69.2666)
    coord2 = (41.3182, 69.2684)
    dist = haversine_distance_meters(coord1, coord2)
    assert 180.0 < dist < 240.0, f"Expected distance ~210m, got {dist}"


def test_green_wave_offsets_calculation():
    # Target speed 40 km/h (~11.11 m/s), cycle length 90s
    offsets = calculate_green_wave_offsets(target_speed_kmh=40.0, cycle_length=90)
    
    assert len(offsets) == len(CORRIDOR_SIGNAL_ORDER)
    assert "cluster_1" in offsets
    assert offsets["cluster_1"]["offset_seconds"] == 0
    assert offsets["cluster_1"]["distance_meters"] == 0.0

    # Ensure all offsets are within cycle range [0, 89]
    for sig_id, data in offsets.items():
        assert 0 <= data["offset_seconds"] < 90
        assert data["cycle_length"] == 90
        assert data["target_speed_kmh"] == 40.0


def test_green_wave_cycle_wrapping():
    # Long artificial distance that wraps multiple cycles
    test_sequence = [
        {"signal_id": "sig_a", "name": "A", "coords": (41.3000, 69.2000)},
        {"signal_id": "sig_b", "name": "B", "coords": (41.3200, 69.2200)}, # ~2.8 km
    ]
    offsets = calculate_green_wave_offsets(target_speed_kmh=36.0, cycle_length=60, signal_sequence=test_sequence)
    assert 0 <= offsets["sig_b"]["offset_seconds"] < 60


@patch("app.services.simulation.session.traci")
def test_green_wave_apply_intervention_valid_and_invalid(mock_traci):
    # Mock only 2 signals present in SUMO network
    mock_traci.trafficlight.getIDList.return_value = ["cluster_1", "cluster_2"]
    mock_traci.trafficlight.getPhaseDuration.return_value = 30

    intervention = {
        "type": "green_wave_coordination",
        "target_speed_kmh": 40.0,
    }
    result = _apply_intervention(intervention)

    assert result is not None
    assert result["type"] == "green_wave_coordination"
    assert result["coordinated_signals_count"] == 2
    assert len(result["applied_signals"]) == 2


def test_tradeoff_analysis_classification():
    delta: CandidateDelta = {
        "average_waiting_seconds": -5.2,
        "delay_improvement_pct": 21.5,
        "average_travel_time_seconds": -8.4,
        "travel_time_improvement_pct": 14.3,
        "stops_per_vehicle": -0.6,
        "stops_improvement_pct": 38.0,
        "mean_queue_length_meters": -4.0,
        "queue_improvement_pct": 10.5,
        "throughput_vehicles_per_hour": 60.0,
        "throughput_improvement_pct": 11.2,
        "co2_kg": -1.8,
        "emissions_improvement_pct": 12.4,
        "accessibility_score": 2.0,
        "max_vehicle_count": 0,
        "average_speed_kmh": 3.5,
        "nox_g": -0.2,
        "noise_db": -0.5,
        "pedestrian_delay_seconds": 0.0,
    }

    summary = analyze_tradeoffs(delta, language="en")
    assert len(summary["improved"]) >= 5
    assert len(summary["worsened"]) == 0
    assert "Uniform corridor improvement" in summary["verdict_en"]

    # Test trade-off scenario
    tradeoff_delta: CandidateDelta = {
        "average_waiting_seconds": -3.0,
        "delay_improvement_pct": 12.0,
        "average_travel_time_seconds": -2.0,
        "travel_time_improvement_pct": 5.0,
        "stops_per_vehicle": 0.2,
        "stops_improvement_pct": -8.5, # worsened
        "mean_queue_length_meters": 2.0,
        "queue_improvement_pct": -5.2, # worsened
        "throughput_vehicles_per_hour": 10.0,
        "throughput_improvement_pct": 2.0, # unchanged
        "co2_kg": 0.0,
        "emissions_improvement_pct": 0.0, # unchanged
        "accessibility_score": 0.0,
        "max_vehicle_count": 0,
        "average_speed_kmh": 0.5,
        "nox_g": 0.0,
        "noise_db": 0.0,
        "pedestrian_delay_seconds": 0.0,
    }

    tradeoff_summary = analyze_tradeoffs(tradeoff_delta, language="ru")
    assert len(tradeoff_summary["improved"]) == 2
    assert len(tradeoff_summary["worsened"]) == 2
    assert len(tradeoff_summary["verdict_ru"]) > 10


def test_statistical_summary_multi_seed():
    m1: SimulationMetrics = {
        "average_speed_kmh": 28.0,
        "average_waiting_seconds": 22.0,
        "average_travel_time_seconds": 55.0,
        "stops_per_vehicle": 1.2,
        "throughput_vehicles_per_hour": 520.0,
    }
    m2: SimulationMetrics = {
        "average_speed_kmh": 30.0,
        "average_waiting_seconds": 20.0,
        "average_travel_time_seconds": 51.0,
        "stops_per_vehicle": 1.0,
        "throughput_vehicles_per_hour": 560.0,
    }
    m3: SimulationMetrics = {
        "average_speed_kmh": 29.0,
        "average_waiting_seconds": 21.0,
        "average_travel_time_seconds": 53.0,
        "stops_per_vehicle": 1.1,
        "throughput_vehicles_per_hour": 540.0,
    }

    stats = compute_statistical_summary([m1, m2, m3])

    assert stats["average_speed_kmh"]["mean"] == 29.0
    assert stats["average_speed_kmh"]["min"] == 28.0
    assert stats["average_speed_kmh"]["max"] == 30.0
    assert stats["average_speed_kmh"]["std_dev"] == 1.0
    assert stats["average_speed_kmh"]["sample_count"] == 3
    assert stats["average_waiting_seconds"]["mean"] == 21.0
