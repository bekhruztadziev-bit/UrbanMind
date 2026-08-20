import app.services.calibration.service as calibration_service
from app.services.calibration.mappings import MovementMapping, MovementMappingRegistry
from app.services.calibration.service import (
    compute_validation_metrics,
    evaluate_field_calibration,
    import_field_observation_dataset,
    validate_field_observations,
)
from app.services.simulation.network_inspector import get_network_identity


def _record(intersection_id="test_ix_1", approach_id="north", movement="through", count=100, timestamp="2026-08-20T08:00:00Z", measurement_window_id="SIM-CAL:test_ix_1"):
    return {
        "timestamp": timestamp, "intersection_id": intersection_id, "approach_id": approach_id,
        "movement": movement, "interval_minutes": 15, "vehicle_count": count,
        "measurement_window_id": measurement_window_id,
        "vehicle_class": "passenger_car", "source": "manual field survey", "quality": "STANDARD_TELEMETRY", "notes": "",
    }


def _dataset(dataset_id, purpose, campaign_id, simulation_campaign_id, observations):
    return {
        "dataset_id": dataset_id,
        "purpose": purpose,
        "campaign_id": campaign_id,
        "simulation_campaign_id": simulation_campaign_id,
        "observations": observations,
    }


def _registry():
    identity = get_network_identity()
    records = []
    for index in range(1, 5):
        records.append(MovementMapping(
            mapping_id=f"map-{index}", city_id="test-city", district_id="test-district", corridor_id="test-corridor",
            intersection_id=f"test_ix_{index}", intersection_name=f"Test {index}", approach_id="north",
            approach_name="North", movement="through", incoming_edge=f"in-{index}", outgoing_edge=f"out-{index}",
            lane_ids=(f"in-{index}_0",), signal_id=f"signal-{index}", enabled=True, notes="Test-only verified mapping",
            network_version=identity["network_version"], configuration_hash=identity["network_sha256"],
            incoming_lane_ids=(f"in-{index}_0",), verification_status="ENABLED",
            verification_method="TEST_FIXTURE", verified_at="2026-08-20T00:00:00Z", verified_by="test-suite",
        ))
    return MovementMappingRegistry(records)


def test_mapping_validated_json_import(monkeypatch):
    monkeypatch.setattr(calibration_service, "get_mapping_registry", _registry)
    result = validate_field_observations(_dataset("CAL-JSON", "CALIBRATION", "FIELD-CAL", "SIM-CAL", [_record()]))
    assert result["is_valid"] is True
    assert result["observations"][0]["mapping_id"] == "map-1"
    assert result["diagnostics"][0]["status"] == "ACCEPTED"


def test_csv_import_and_duplicate_diagnostic(monkeypatch):
    monkeypatch.setattr(calibration_service, "get_mapping_registry", _registry)
    header = "dataset_id,purpose,campaign_id,simulation_campaign_id,timestamp,measurement_window_id,intersection_id,approach_id,movement,interval_minutes,vehicle_count,vehicle_class,source,quality,notes"
    row = "CAL-CSV,CALIBRATION,FIELD-CAL,SIM-CAL,2026-08-20T08:00:00Z,SIM-CAL:test_ix_1,test_ix_1,north,through,15,100,passenger_car,manual,STANDARD_TELEMETRY,ok"
    result = validate_field_observations({"format": "csv", "csv_text": f"{header}\n{row}\n{row}"})
    assert result["is_valid"] is False
    assert len(result["observations"]) == 1
    assert "Duplicate observation record." in result["validation_errors"][-1]


def test_invalid_or_unmapped_records_are_rejected(monkeypatch):
    monkeypatch.setattr(calibration_service, "get_mapping_registry", _registry)
    invalid = _record(intersection_id="unknown", movement="invalid", count=-1)
    result = validate_field_observations(_dataset("BAD", "NOT_HOLDOUT", "FIELD-BAD", "SIM-BAD", [invalid]))
    assert result["is_valid"] is False
    assert result["diagnostics"][0]["status"] == "REJECTED"
    assert any("No enabled, verified SUMO movement mapping" in error for error in result["validation_errors"])


def test_calibration_and_holdout_require_separate_mapped_datasets(monkeypatch):
    monkeypatch.setattr(calibration_service, "get_mapping_registry", _registry)
    calibration_service._FIELD_DATASETS_STORE.clear()
    calibration_service._ACTIVE_CALIBRATION_STATUS = "UNCALIBRATED"
    calibration_service._ACTIVE_CALIBRATION_DATASET_ID = None
    calibration_service._ACTIVE_VALIDATION_DATASET_ID = None
    observations = [_record(intersection_id=f"test_ix_{index}", count=100 + index, measurement_window_id=f"SIM-CAL:test_ix_{index}") for index in range(1, 5)]
    imported = import_field_observation_dataset(_dataset("CAL-1", "CALIBRATION", "FIELD-CAL", "SIM-CAL", observations))
    assert imported["is_valid"]
    identity = get_network_identity()
    sums = {
        f"map-{index}": {
            "mapping_id": f"map-{index}", "mapping_version": "v1", "interval_minutes": 15,
            "provenance": "SIMULATED", "network_version": identity["network_version"],
            "network_configuration_hash": identity["network_sha256"], "simulation_id": "SIM-CAL",
            "measurement_window_id": f"SIM-CAL:test_ix_{index}", "vehicle_classes": {"passenger_car": 100 + index},
        } for index in range(1, 5)
    }
    calibrated = evaluate_field_calibration("CAL-1", sums)
    assert calibrated["status"] == "CALIBRATED"
    holdout_observations = [
        _record(intersection_id=f"test_ix_{index}", count=100 + index, timestamp="2026-08-21T08:00:00Z", measurement_window_id=f"SIM-HOLDOUT:test_ix_{index}")
        for index in range(1, 5)
    ]
    holdout = import_field_observation_dataset(_dataset("HOLDOUT-1", "VALIDATION_HOLDOUT", "FIELD-HOLDOUT", "SIM-HOLDOUT", holdout_observations))
    assert holdout["is_valid"]
    holdout_sums = {key: {**value, "simulation_id": "SIM-HOLDOUT", "measurement_window_id": value["measurement_window_id"].replace("SIM-CAL", "SIM-HOLDOUT")} for key, value in sums.items()}
    validated = evaluate_field_calibration("HOLDOUT-1", holdout_sums)
    assert validated["status"] == "VALIDATED"
    leaked = evaluate_field_calibration("CAL-1", sums)
    assert leaked["is_holdout_validation"] is False
    assert leaked["status"] == "CALIBRATED"


def test_holdout_with_same_content_or_campaign_is_rejected(monkeypatch):
    monkeypatch.setattr(calibration_service, "get_mapping_registry", _registry)
    calibration_service._FIELD_DATASETS_STORE.clear()
    calibration_service._ACTIVE_CALIBRATION_STATUS = "UNCALIBRATED"
    calibration_service._ACTIVE_CALIBRATION_DATASET_ID = None
    observations = [_record(intersection_id=f"test_ix_{index}", count=100 + index, measurement_window_id=f"SIM-CAL:test_ix_{index}") for index in range(1, 5)]
    import_field_observation_dataset(_dataset("CAL-LEAK", "CALIBRATION", "FIELD-ONE", "SIM-CAL", observations))
    identity = get_network_identity()
    sums = {f"map-{index}": {"mapping_id": f"map-{index}", "mapping_version": "v1", "interval_minutes": 15, "provenance": "SIMULATED", "network_version": identity["network_version"], "network_configuration_hash": identity["network_sha256"], "simulation_id": "SIM-CAL", "measurement_window_id": f"SIM-CAL:test_ix_{index}", "vehicle_classes": {"passenger_car": 100 + index}} for index in range(1, 5)}
    assert evaluate_field_calibration("CAL-LEAK", sums)["status"] == "CALIBRATED"
    import_field_observation_dataset(_dataset("HOLDOUT-LEAK", "VALIDATION_HOLDOUT", "FIELD-ONE", "SIM-HOLDOUT", observations))
    result = evaluate_field_calibration("HOLDOUT-LEAK", sums)
    assert result["thresholds_met"]["independent_holdout"] is False
    assert "Holdout rejected" in result["summary_en"]


def test_validation_metric_and_geh_correctness():
    metrics = compute_validation_metrics([100, 200], [110, 190])
    assert metrics["mae"] == 10.0
    assert metrics["rmse"] == 10.0
    assert metrics["bias"] == 0.0
    assert metrics["mean_bias_error"] == 0.0
    assert metrics["geh_pass"] is True
