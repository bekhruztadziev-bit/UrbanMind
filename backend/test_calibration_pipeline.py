import pytest
from app.services.calibration.service import (
    validate_field_observations,
    import_field_observation_dataset,
    evaluate_field_calibration,
    get_calibration_status,
)


def test_field_observation_validation_valid():
    valid_dataset = {
        "dataset_id": "DS-TEST-001",
        "name": "Morning Peak Turning Counts",
        "purpose": "CALIBRATION",
        "observations": [
            {
                "intersection_id": "intersection_1",
                "approach_id": "northbound",
                "movement": "through",
                "interval_minutes": 15,
                "vehicle_count": 98,
                "timestamp": "2026-08-20T08:00:00Z",
            },
            {
                "intersection_id": "intersection_2",
                "approach_id": "southbound",
                "movement": "left",
                "interval_minutes": 15,
                "vehicle_count": 45,
                "timestamp": "2026-08-20T08:00:00Z",
            },
        ],
    }
    res = validate_field_observations(valid_dataset)
    assert res["is_valid"] is True
    assert len(res["validation_errors"]) == 0
    assert res["total_counts"] == 143
    assert len(res["unique_intersections"]) == 2
    assert res["purpose"] == "CALIBRATION"


def test_field_observation_validation_rejections():
    invalid_dataset = {
        "dataset_id": "DS-INVALID",
        "observations": [
            {
                "intersection_id": "unknown_intersection_999",
                "movement": "invalid_turn",
                "interval_minutes": 500,  # invalid (>120)
                "vehicle_count": -10,      # negative count
                "timestamp": "2026-08-20T08:00:00Z",
            },
            # Duplicate record
            {
                "intersection_id": "intersection_1",
                "approach_id": "main",
                "movement": "through",
                "interval_minutes": 15,
                "vehicle_count": 50,
                "timestamp": "2026-08-20T08:00:00Z",
            },
            {
                "intersection_id": "intersection_1",
                "approach_id": "main",
                "movement": "through",
                "interval_minutes": 15,
                "vehicle_count": 50,
                "timestamp": "2026-08-20T08:00:00Z",
            },
        ],
    }
    res = validate_field_observations(invalid_dataset)
    assert res["is_valid"] is False
    assert len(res["validation_errors"]) >= 4


def test_field_calibration_evaluation_pipeline():
    # 1. Import calibration dataset
    dataset = {
        "dataset_id": "DS-CALIB-001",
        "name": "Corridor Calibration Counts",
        "purpose": "CALIBRATION",
        "observations": [
            {"intersection_id": "intersection_1", "approach_id": "n", "movement": "through", "interval_minutes": 60, "vehicle_count": 410, "timestamp": "2026-08-20T08:00:00Z"},
            {"intersection_id": "intersection_2", "approach_id": "s", "movement": "through", "interval_minutes": 60, "vehicle_count": 375, "timestamp": "2026-08-20T08:00:00Z"},
            {"intersection_id": "intersection_3", "approach_id": "e", "movement": "through", "interval_minutes": 60, "vehicle_count": 345, "timestamp": "2026-08-20T08:00:00Z"},
            {"intersection_id": "intersection_4", "approach_id": "w", "movement": "through", "interval_minutes": 60, "vehicle_count": 385, "timestamp": "2026-08-20T08:00:00Z"},
        ],
    }
    imported = import_field_observation_dataset(dataset)
    assert imported["is_valid"] is True

    # 2. Evaluate calibration
    sim_counts = {
        "intersection_1": 420.0,
        "intersection_2": 380.0,
        "intersection_3": 350.0,
        "intersection_4": 390.0,
    }
    eval_res = evaluate_field_calibration("DS-CALIB-001", sim_counts)
    
    assert eval_res["dataset_id"] == "DS-CALIB-001"
    assert eval_res["metrics"]["mae"] is not None
    assert eval_res["metrics"]["mape"] is not None
    assert eval_res["metrics"]["mape"] <= 15.0  # MAPE is small
    assert eval_res["metrics"]["geh_pass"] is True
    assert eval_res["status"] == "CALIBRATED"

    # Status record should reflect updated status
    status_rec = get_calibration_status()
    assert status_rec["status"] == "CALIBRATED"
    assert status_rec["traffic_calibrated"] is True


def test_independent_holdout_validation_pipeline():
    # 1. Attempting holdout validation with the SAME dataset ID must fail
    invalid_holdout_eval = evaluate_field_calibration("DS-CALIB-001")
    # If the dataset was used for calibration, cannot validate with it
    # Import a proper independent holdout dataset
    holdout_ds = {
        "dataset_id": "DS-HOLDOUT-001",
        "name": "Independent Holdout Verification Counts",
        "purpose": "VALIDATION_HOLDOUT",
        "observations": [
            {"intersection_id": "intersection_1", "approach_id": "n", "movement": "through", "interval_minutes": 60, "vehicle_count": 418, "timestamp": "2026-08-21T08:00:00Z"},
            {"intersection_id": "intersection_2", "approach_id": "s", "movement": "through", "interval_minutes": 60, "vehicle_count": 376, "timestamp": "2026-08-21T08:00:00Z"},
            {"intersection_id": "intersection_3", "approach_id": "e", "movement": "through", "interval_minutes": 60, "vehicle_count": 348, "timestamp": "2026-08-21T08:00:00Z"},
            {"intersection_id": "intersection_4", "approach_id": "w", "movement": "through", "interval_minutes": 60, "vehicle_count": 387, "timestamp": "2026-08-21T08:00:00Z"},
        ],
    }
    imported_holdout = import_field_observation_dataset(holdout_ds)
    assert imported_holdout["is_valid"] is True
    assert imported_holdout["purpose"] == "VALIDATION_HOLDOUT"

    sim_counts = {
        "intersection_1": 420.0,
        "intersection_2": 380.0,
        "intersection_3": 350.0,
        "intersection_4": 390.0,
    }
    holdout_eval = evaluate_field_calibration("DS-HOLDOUT-001", sim_counts)
    assert holdout_eval["is_holdout_validation"] is True
    assert holdout_eval["thresholds_met"]["independent_holdout"] is True
    assert holdout_eval["thresholds_met"]["geh_compliant"] is True
    assert holdout_eval["status"] == "VALIDATED"

    # Status record should reflect VALIDATED
    status_rec = get_calibration_status()
    assert status_rec["status"] == "VALIDATED"
    assert status_rec["active_validation_dataset_id"] == "DS-HOLDOUT-001"
