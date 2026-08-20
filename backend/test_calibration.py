from __future__ import annotations

import pytest
import app.services.calibration.service as calibration_service
from app.services.calibration.service import (
    compute_validation_metrics,
    get_calibration_status,
    get_model_vs_reality_breakdown,
)


@pytest.fixture(autouse=True)
def reset_calibration_state():
    """Keep status assertions independent of imports performed by other tests."""
    calibration_service._FIELD_DATASETS_STORE.clear()
    calibration_service._ACTIVE_CALIBRATION_STATUS = "UNCALIBRATED"
    calibration_service._ACTIVE_CALIBRATION_DATASET_ID = None
    calibration_service._ACTIVE_VALIDATION_DATASET_ID = None


def test_compute_validation_metrics_identical():
    obs = [10.0, 20.0, 30.0, 40.0]
    sim = [10.0, 20.0, 30.0, 40.0]
    res = compute_validation_metrics(obs, sim, metric_name="delay", unit="s")

    assert res["sample_count"] == 4
    assert res["mae"] == 0.0
    assert res["rmse"] == 0.0
    assert res["mape"] == 0.0
    assert res["bias"] == 0.0
    assert res["correlation"] == 1.0
    assert res["is_applicable"] is True


def test_compute_validation_metrics_with_error():
    obs = [10.0, 20.0, 30.0, 40.0]
    sim = [12.0, 18.0, 33.0, 42.0]
    res = compute_validation_metrics(obs, sim, metric_name="travel_time", unit="s")

    assert res["sample_count"] == 4
    assert res["mae"] == 2.25  # (|2| + |-2| + |3| + |2|) / 4 = 9/4 = 2.25
    assert res["rmse"] > 0
    assert res["bias"] == 1.25  # (2 - 2 + 3 + 2) / 4 = 5/4 = 1.25
    assert res["correlation"] > 0.95
    assert res["is_applicable"] is True



def test_compute_validation_metrics_empty_and_zero():
    # Empty
    res_empty = compute_validation_metrics([], [], metric_name="test")
    assert res_empty["sample_count"] == 0
    assert res_empty["is_applicable"] is False
    assert res_empty["mae"] is None

    # Series with zeros (MAPE should not crash)
    obs_zeros = [0.0, 10.0, 20.0]
    sim_zeros = [2.0, 12.0, 22.0]
    res_zeros = compute_validation_metrics(obs_zeros, sim_zeros, metric_name="queue")
    assert res_zeros["sample_count"] == 3
    assert res_zeros["mae"] == 2.0
    assert res_zeros["mape"] is not None  # Evaluated on non-zero elements


def test_calibration_status():
    status = get_calibration_status("central_corridor")
    assert status["status"] == "UNCALIBRATED"
    assert status["traffic_calibrated"] is False
    assert "UNCALIBRATED" in status["explanation_en"]
    assert "SUMO" in status["modeled_sources"][0]
    assert len(status["methodology_caveats_en"]) >= 2


def test_model_vs_reality_breakdown():
    mvr = get_model_vs_reality_breakdown(
        baseline_metrics={"average_waiting_seconds": 24.0, "co2_kg": 18.0},
        scenario_metrics={"average_waiting_seconds": 18.0, "co2_kg": 15.0},
        env_data={"pm25": 28.4, "temperature": 24.0}
    )

    observed = mvr["observed_metrics"]
    simulated = mvr["simulated_metrics"]
    derived = mvr["derived_metrics"]

    assert any(m["category"] == "OBSERVED" for m in observed)
    assert any(m["category"] == "SIMULATED" for m in simulated)
    assert any(m["category"] == "DERIVED" for m in derived)

    # Check that traffic counts explicitly report unavailable
    traffic_field = next(m for m in observed if m["key"] == "traffic_counts_field")
    assert traffic_field["value"] == "Calibration data unavailable"
    assert traffic_field["calibration_state"] == "UNAVAILABLE"
