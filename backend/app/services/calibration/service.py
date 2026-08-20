from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.services.calibration.models import (
    CalibrationDataset,
    CalibrationStatusRecord,
    ModelVsRealityRecord,
    ValidationMetrics,
    MetricClassification,
    FieldObservationRecord,
    FieldObservationDataset,
    CalibrationEvaluationResult,
    CalibrationStatus,
    DatasetPurpose,
    FieldValidationProtocol,
    PredictionVsRealityItem,
)
from app.services.simulation.statistics import evaluate_geh_batch, compute_geh
from app.services.spatial.hierarchy import get_default_spatial_scope
from app.services.calibration.mappings import get_mapping_registry


VALID_MOVEMENTS = {"through", "left", "right", "u_turn"}
# The configured SUMO fleet is passenger-only.  Other field classes are
# retained by the collector upstream but are not yet comparable here.
VALID_VEHICLE_TYPES = {"passenger_car"}
VALID_PURPOSES = {"CALIBRATION", "VALIDATION_HOLDOUT"}
VALID_FIELD_QUALITY_FLAGS = {"HIGH_PRECISION", "STANDARD_TELEMETRY"}


_FIELD_DATASETS_STORE: Dict[str, FieldObservationDataset] = {}
_ACTIVE_CALIBRATION_STATUS: CalibrationStatus = "UNCALIBRATED"
_ACTIVE_CALIBRATION_DATASET_ID: Optional[str] = None
_ACTIVE_VALIDATION_DATASET_ID: Optional[str] = None


def _canonical_observation_payload(record: Dict[str, Any], campaign_id: str, network_version: str) -> Dict[str, Any]:
    """Return only calibration-relevant immutable identity fields for hashing."""
    return {
        "campaign_id": campaign_id,
        "network_version": network_version,
        "mapping_id": record.get("mapping_id"),
        "timestamp": record.get("timestamp"),
        "measurement_window_id": record.get("measurement_window_id"),
        "intersection_id": record.get("intersection_id"),
        "approach_id": record.get("approach_id"),
        "movement": record.get("movement"),
        "interval_minutes": record.get("interval_minutes"),
        "vehicle_class": record.get("vehicle_class"),
        "vehicle_count": record.get("vehicle_count"),
        "source": record.get("source"),
    }


def _fingerprint(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def compute_validation_metrics(
    observed_series: List[float],
    simulated_series: List[float],
    metric_name: str = "turning_movement_flow",
    unit: str = "veh/h"
) -> ValidationMetrics:
    """
    Computes standard statistical model-validation metrics:
    - MAE: Mean Absolute Error
    - RMSE: Root Mean Squared Error
    - MAPE: Mean Absolute Percentage Error (computed only over strictly positive observed values)
    - Bias: Mean Error (simulated - observed)
    - Pearson Correlation: r
    - GEH: Geoffrey E. Havers statistic (evaluated against UrbanMind's configured acceptance criterion)
    
    Handles empty series and zero/near-zero edge cases safely.
    """
    if not observed_series or not simulated_series:
        return {
            "metric_name": metric_name,
            "unit": unit,
            "sample_count": 0,
            "mae": None,
            "rmse": None,
            "mape": None,
            "bias": None,
            "mean_bias_error": None,
            "correlation": None,
            "geh_mean": None,
            "geh_max": None,
            "geh_pct_under_5": None,
            "geh_pass": False,
            "is_applicable": False,
            "methodology_note": "Insufficient paired data points for validation calculation.",
        }

    if len(observed_series) != len(simulated_series):
        raise ValueError("Observed and simulated series must be explicitly aligned and have equal length.")
    n = len(observed_series)
    obs = [float(x) for x in observed_series]
    sim = [float(x) for x in simulated_series]
    if any(value < 0 for value in obs + sim):
        raise ValueError("Validation flow values must be non-negative.")

    if n == 0:
        return {
            "metric_name": metric_name,
            "unit": unit,
            "sample_count": 0,
            "mae": None,
            "rmse": None,
            "mape": None,
            "bias": None,
            "mean_bias_error": None,
            "correlation": None,
            "geh_mean": None,
            "geh_max": None,
            "geh_pct_under_5": None,
            "geh_pass": False,
            "is_applicable": False,
            "methodology_note": "Zero valid observations.",
        }

    abs_errors = [abs(s - o) for o, s in zip(obs, sim)]
    sq_errors = [(s - o) ** 2 for o, s in zip(obs, sim)]
    raw_errors = [s - o for o, s in zip(obs, sim)]

    mae = round(sum(abs_errors) / n, 2)
    rmse = round(math.sqrt(sum(sq_errors) / n), 2)
    bias = round(sum(raw_errors) / n, 2)

    # MAPE: only compute on non-zero observed entries to avoid division by zero
    valid_mape_pairs = [(o, s) for o, s in zip(obs, sim) if abs(o) > 1e-6]
    if valid_mape_pairs:
        mape_vals = [abs((s - o) / o) * 100.0 for o, s in valid_mape_pairs]
        mape = round(sum(mape_vals) / len(mape_vals), 2)
    else:
        mape = None

    # Pearson Correlation r
    mean_o = sum(obs) / n
    mean_s = sum(sim) / n
    cov = sum((o - mean_o) * (s - mean_s) for o, s in zip(obs, sim))
    var_o = sum((o - mean_o) ** 2 for o in obs)
    var_s = sum((s - mean_s) ** 2 for s in sim)

    if var_o > 1e-9 and var_s > 1e-9:
        correlation = round(cov / (math.sqrt(var_o) * math.sqrt(var_s)), 3)
        correlation = max(-1.0, min(1.0, correlation))
    else:
        correlation = None

    # GEH Batch Evaluation
    pairs = list(zip(sim, obs))
    geh_res = evaluate_geh_batch(pairs, threshold=5.0, required_pass_rate=85.0)

    return {
        "metric_name": metric_name,
        "unit": unit,
        "sample_count": n,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "bias": bias,
        "mean_bias_error": bias,
        "correlation": correlation,
        "geh_mean": geh_res.get("mean_geh"),
        "geh_max": geh_res.get("max_geh"),
        "geh_pct_under_5": geh_res.get("pct_under_5"),
        "geh_pass": geh_res.get("is_criteria_met", False),
        "is_applicable": True,
        "methodology_note": (
            f"Validation metrics calculated over {n} flow pairs. "
            f"GEH < 5.0 in {geh_res.get('pct_under_5', 0)}% of flows (UrbanMind configured criterion informed by traffic-assignment guidance: >= 85%)."
        ),
    }


def parse_field_observation_import(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a JSON dataset or a CSV payload without silently changing values."""
    csv_text = payload.get("csv_text") or (payload.get("content") if str(payload.get("format", "")).lower() == "csv" else None)
    if not csv_text:
        return payload
    try:
        rows = list(csv.DictReader(io.StringIO(str(csv_text))))
    except csv.Error as exc:
        return {"dataset_id": payload.get("dataset_id", ""), "observations": [], "parse_error": f"CSV parse error: {exc}"}
    return {
        "dataset_id": payload.get("dataset_id") or (rows[0].get("dataset_id") if rows else ""),
        "name": payload.get("name", "Field Turning Movement Counts"),
        "description": payload.get("description", ""),
        "purpose": payload.get("purpose") or (rows[0].get("purpose") if rows else ""),
        "campaign_id": payload.get("campaign_id") or (rows[0].get("campaign_id") if rows else ""),
        "simulation_campaign_id": payload.get("simulation_campaign_id") or (rows[0].get("simulation_campaign_id") if rows else ""),
        "observations": rows,
    }


def validate_field_observations(raw_dataset: Dict[str, Any]) -> FieldObservationDataset:
    """Strictly validate genuine field observations against the mapping registry."""
    raw_dataset = parse_field_observation_import(raw_dataset)
    errors: List[str] = []
    diagnostics: List[Dict[str, Any]] = []
    registry = get_mapping_registry()
    dataset_id = str(raw_dataset.get("dataset_id") or "").strip()
    purpose = str(raw_dataset.get("purpose") or "").strip().upper()
    campaign_id = str(raw_dataset.get("campaign_id") or "").strip()
    simulation_campaign_id = str(raw_dataset.get("simulation_campaign_id") or "").strip()
    if not dataset_id:
        errors.append("dataset_id is required.")
    if purpose not in VALID_PURPOSES:
        errors.append("purpose must be exactly CALIBRATION or VALIDATION_HOLDOUT.")
    if not campaign_id:
        errors.append("campaign_id is required and identifies the field-survey campaign.")
    if not simulation_campaign_id:
        errors.append("simulation_campaign_id is required and must identify the comparable SUMO measurement campaign.")
    rows = raw_dataset.get("observations")
    if raw_dataset.get("parse_error"):
        errors.append(str(raw_dataset["parse_error"]))
    if not isinstance(rows, list) or not rows:
        errors.append("Dataset must contain a non-empty observations list.")
        rows = []

    valid_records: List[FieldObservationRecord] = []
    seen = set()
    total_counts = 0
    unique_intersections = set()
    required = {
        "timestamp", "intersection_id", "approach_id", "movement", "interval_minutes",
        "vehicle_count", "vehicle_class", "source", "quality", "notes",
    }
    for index, raw in enumerate(rows, start=1):
        row_errors: List[str] = []
        if not isinstance(raw, dict):
            diagnostics.append({"row": index, "status": "REJECTED", "errors": ["Row is not an object."], "mapping": None})
            errors.append(f"Row {index}: Row is not an object.")
            continue
        missing = sorted(key for key in required if key not in raw or raw.get(key) is None)
        if missing:
            row_errors.append(f"Missing required columns: {', '.join(missing)}.")
        ix = str(raw.get("intersection_id") or "").strip()
        approach = str(raw.get("approach_id") or "").strip()
        movement = str(raw.get("movement") or "").strip().lower()
        mapping = registry.lookup(ix, approach, movement)
        if movement not in VALID_MOVEMENTS:
            row_errors.append(f"Invalid movement '{movement}'.")
        if not ix or not approach:
            row_errors.append("intersection_id and approach_id are required.")
        if mapping is None:
            row_errors.append("No enabled, verified SUMO movement mapping exists for this intersection, approach, and movement.")
        try:
            timestamp = str(raw.get("timestamp") or "")
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            row_errors.append("timestamp must be ISO-8601.")
            timestamp = str(raw.get("timestamp") or "")
        try:
            interval = int(raw.get("interval_minutes"))
            if interval < 1 or interval > 120:
                row_errors.append("interval_minutes must be between 1 and 120.")
        except (TypeError, ValueError):
            interval = 0
            row_errors.append("interval_minutes must be an integer between 1 and 120.")
        try:
            count = int(raw.get("vehicle_count"))
            if isinstance(raw.get("vehicle_count"), bool) or count < 0:
                row_errors.append("vehicle_count must be a non-negative integer.")
        except (TypeError, ValueError):
            count = 0
            row_errors.append("vehicle_count must be a non-negative integer.")
        vehicle_class = str(raw.get("vehicle_class") or "").strip().lower()
        if vehicle_class not in VALID_VEHICLE_TYPES:
            row_errors.append(f"Invalid vehicle_class '{vehicle_class}'.")
        if not str(raw.get("source") or "").strip():
            row_errors.append("source is required.")
        quality = str(raw.get("quality") or "").strip().upper()
        if quality not in VALID_FIELD_QUALITY_FLAGS:
            row_errors.append("quality must be HIGH_PRECISION or STANDARD_TELEMETRY; proxy or synthetic records cannot calibrate the model.")
        window_id = str(raw.get("measurement_window_id") or f"{timestamp}/{interval}m")
        duplicate_key = (window_id, ix, approach, movement, vehicle_class, interval)
        if duplicate_key in seen:
            row_errors.append("Duplicate observation record.")
        seen.add(duplicate_key)
        if row_errors:
            diagnostics.append({"row": index, "status": "REJECTED", "errors": row_errors, "mapping": mapping.serialize() if mapping else None})
            errors.extend(f"Row {index}: {message}" for message in row_errors)
            continue
        observation: FieldObservationRecord = {
            "observation_id": str(raw.get("observation_id") or f"obs_{dataset_id}_{index}"),
            "dataset_id": dataset_id,
            "purpose": purpose,  # type: ignore[typeddict-item]
            "timestamp": timestamp,
            "measurement_window_id": window_id,
            "spatial_scope": raw_dataset.get("spatial_scope") or get_default_spatial_scope(),
            "intersection_id": ix,
            "approach_id": approach,
            "movement": movement,  # type: ignore[typeddict-item]
            "mapping_id": mapping.mapping_id,
            "interval_minutes": interval,
            "vehicle_count": count,
            "vehicle_class": vehicle_class,  # type: ignore[typeddict-item]
            "source": str(raw["source"]).strip(),
            "quality": quality,  # type: ignore[typeddict-item]
            "notes": str(raw.get("notes") or ""),
        }
        if mapping is not None:
            observation["observation_content_hash"] = _fingerprint(
                _canonical_observation_payload(observation, campaign_id, mapping.network_version)
            )
        valid_records.append(observation)
        diagnostics.append({"row": index, "status": "ACCEPTED", "errors": [], "mapping": mapping.serialize()})
        unique_intersections.add(ix)
        total_counts += count
    observation_hashes = sorted(record.get("observation_content_hash", "") for record in valid_records)
    dataset_content_hash = _fingerprint({"campaign_id": campaign_id, "observations": observation_hashes}) if observation_hashes else ""
    return {
        "dataset_id": dataset_id,
        "name": str(raw_dataset.get("name") or "Field Turning Movement Observation Dataset"),
        "description": str(raw_dataset.get("description") or ""),
        "campaign_id": campaign_id,
        "simulation_campaign_id": simulation_campaign_id,
        "purpose": purpose,  # type: ignore[typeddict-item]
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "spatial_scope": raw_dataset.get("spatial_scope") or get_default_spatial_scope(),
        "observations": valid_records,
        "is_valid": not errors and bool(valid_records),
        "validation_errors": errors,
        "diagnostics": diagnostics,
        "mapping_coverage": registry.coverage(),
        "total_counts": total_counts,
        "unique_intersections": sorted(unique_intersections),
        "time_window": str(raw_dataset.get("time_window") or ""),
        "dataset_content_hash": dataset_content_hash,
        "observation_content_hashes": observation_hashes,
    }


def list_field_observation_datasets() -> List[Dict[str, Any]]:
    """Return import metadata without re-exposing every raw field record."""
    return [{
        "dataset_id": dataset.get("dataset_id"), "name": dataset.get("name"),
        "purpose": dataset.get("purpose"), "is_valid": dataset.get("is_valid"),
        "uploaded_at": dataset.get("uploaded_at"), "record_count": len(dataset.get("observations", [])),
        "diagnostic_count": len(dataset.get("diagnostics", [])),
        "mapping_coverage": dataset.get("mapping_coverage"),
    } for dataset in _FIELD_DATASETS_STORE.values()]


def import_field_observation_dataset(dataset_data: Dict[str, Any]) -> FieldObservationDataset:
    """Validates and stores an imported field observation dataset."""
    validated = validate_field_observations(dataset_data)
    existing = _FIELD_DATASETS_STORE.get(validated.get("dataset_id", ""))
    if existing and (
        existing.get("purpose") != validated.get("purpose")
        or existing.get("dataset_content_hash") != validated.get("dataset_content_hash")
    ):
        validated["is_valid"] = False
        validated.setdefault("validation_errors", []).append(
            "dataset_id is immutable after import; observations cannot be relabeled or replaced after allocation."
        )
        return validated
    _FIELD_DATASETS_STORE[validated["dataset_id"]] = validated
    return validated


def evaluate_field_calibration(
    dataset_id: str,
    simulated_counts: Optional[Dict[str, float]] = None
) -> CalibrationEvaluationResult:
    """
    Connects imported field observations to simulation outputs:
    1. Computes error metrics (MAE, RMSE, MAPE, Bias, Pearson r, GEH).
    2. Enforces separation between CALIBRATION and VALIDATION_HOLDOUT datasets.
    3. Prevents transition to VALIDATED using the same dataset used for calibration.
    4. State transitions:
       - UNCALIBRATED: 0 usable field observations.
       - PARTIALLY_CALIBRATED: observations exist, but configured acceptance criteria are not yet met.
       - CALIBRATED: sample >= 4, MAPE <= 15%, Pearson r >= 0.85.
       - VALIDATED: an independent holdout dataset meets UrbanMind's configured
         GEH, MAPE, correlation, and coverage acceptance criteria.
    """
    global _ACTIVE_CALIBRATION_STATUS, _ACTIVE_CALIBRATION_DATASET_ID, _ACTIVE_VALIDATION_DATASET_ID
    prev_status = _ACTIVE_CALIBRATION_STATUS
    
    ds = _FIELD_DATASETS_STORE.get(dataset_id)
    if not ds or not ds.get("is_valid") or not ds.get("observations"):
        return {
            "dataset_id": dataset_id,
            "purpose": "CALIBRATION",
            "status": "UNCALIBRATED",
            "previous_status": prev_status,
            "is_holdout_validation": False,
            "calibration_dataset_id": _ACTIVE_CALIBRATION_DATASET_ID,
            "validation_dataset_id": _ACTIVE_VALIDATION_DATASET_ID,
            "metrics": {
                "metric_name": "traffic_counts",
                "unit": "veh/h",
                "sample_count": 0,
                "is_applicable": False,
                "methodology_note": "Dataset invalid or contains no observations.",
            },
            "thresholds_met": {"mape_under_15": False, "correlation_over_085": False, "coverage_adequate": False, "geh_compliant": False},
            "summary_en": "Calibration failed: invalid or empty dataset. Model remains UNCALIBRATED.",
            "summary_ru": "Калибровка не выполнена: набор данных пуст или содержит ошибки. Статус: НЕ ОТКАЛИБРОВАНО.",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    purpose = ds.get("purpose", "CALIBRATION")
    is_holdout = purpose == "VALIDATION_HOLDOUT"

    calibration_ds = _FIELD_DATASETS_STORE.get(_ACTIVE_CALIBRATION_DATASET_ID or "")
    if is_holdout and calibration_ds:
        calibration_hashes = set(calibration_ds.get("observation_content_hashes", []))
        holdout_hashes = set(ds.get("observation_content_hashes", []))
        calibration_windows = {
            (record.get("mapping_id"), record.get("measurement_window_id"), record.get("interval_minutes"),
             record.get("vehicle_class"), record.get("vehicle_count"))
            for record in calibration_ds.get("observations", [])
        }
        holdout_windows = {
            (record.get("mapping_id"), record.get("measurement_window_id"), record.get("interval_minutes"),
             record.get("vehicle_class"), record.get("vehicle_count"))
            for record in ds.get("observations", [])
        }
        leakage_reason = None
        if ds.get("dataset_content_hash") == calibration_ds.get("dataset_content_hash"):
            leakage_reason = "dataset content hash equals the calibration dataset"
        elif calibration_hashes & holdout_hashes:
            leakage_reason = "observation content overlaps the calibration dataset"
        elif calibration_windows & holdout_windows:
            leakage_reason = "measurement-window/movement/count pairs overlap the calibration dataset"
        elif ds.get("campaign_id") == calibration_ds.get("campaign_id"):
            leakage_reason = "field-survey campaign matches the calibration campaign"
        if leakage_reason:
            return {
                "dataset_id": dataset_id, "purpose": purpose, "status": prev_status,
                "previous_status": prev_status, "is_holdout_validation": True,
                "calibration_dataset_id": _ACTIVE_CALIBRATION_DATASET_ID, "validation_dataset_id": None,
                "metrics": {"metric_name": "turning_movement_flow", "unit": "veh/h", "sample_count": 0, "is_applicable": False,
                            "methodology_note": f"Holdout rejected: {leakage_reason}."},
                "thresholds_met": {"mape_under_15": False, "correlation_over_085": False, "coverage_adequate": False, "geh_compliant": False, "independent_holdout": False},
                "summary_en": f"Holdout rejected because {leakage_reason}.",
                "summary_ru": "Проверочный набор отклонен из-за пересечения с калибровочными наблюдениями.",
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            }

    # Calibration requires simulation values mapped to the same movement as
    # every field record.  Placeholder per-intersection counts would make an
    # unexecuted model appear calibrated, so they are deliberately forbidden.
    sim_lookup = simulated_counts or {}
    if not sim_lookup:
        return {
            "dataset_id": dataset_id,
            "purpose": purpose,
            "status": prev_status,
            "previous_status": prev_status,
            "is_holdout_validation": is_holdout,
            "calibration_dataset_id": _ACTIVE_CALIBRATION_DATASET_ID,
            "validation_dataset_id": _ACTIVE_VALIDATION_DATASET_ID,
            "metrics": {
                "metric_name": "turning_movement_flow",
                "unit": "veh/h",
                "sample_count": 0,
                "is_applicable": False,
                "methodology_note": "Simulation counts are required and must be mapped by intersection|approach|movement.",
            },
            "thresholds_met": {"mape_under_15": False, "correlation_over_085": False, "coverage_adequate": False, "geh_compliant": False, "mapped_simulation_counts": False},
            "summary_en": "Calibration was not evaluated: no movement-mapped SUMO counts were supplied. Model status is unchanged.",
            "summary_ru": "Калибровка не выполнена: не переданы моделируемые SUMO-потоки, сопоставленные с направлением движения. Статус модели не изменен.",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    obs_series: List[float] = []
    sim_series: List[float] = []

    for obs in ds["observations"]:
        mapping_id = str(obs.get("mapping_id") or "")
        sim_entry = sim_lookup.get(mapping_id)
        mapping = get_mapping_registry().by_id(mapping_id)
        if not isinstance(sim_entry, dict):
            return {
                "dataset_id": dataset_id,
                "purpose": purpose,
                "status": prev_status,
                "previous_status": prev_status,
                "is_holdout_validation": is_holdout,
                "calibration_dataset_id": _ACTIVE_CALIBRATION_DATASET_ID,
                "validation_dataset_id": _ACTIVE_VALIDATION_DATASET_ID,
                "metrics": {"metric_name": "turning_movement_flow", "unit": "veh/h", "sample_count": 0, "is_applicable": False, "methodology_note": f"Missing provenance-bearing SUMO count for mapping '{mapping_id}'."},
                "thresholds_met": {"mape_under_15": False, "correlation_over_085": False, "coverage_adequate": False, "geh_compliant": False, "mapped_simulation_counts": False},
                "summary_en": f"Calibration was not evaluated: missing provenance-bearing SUMO count for mapping '{mapping_id}'. Model status is unchanged.",
                "summary_ru": f"Калибровка не выполнена: отсутствует сопоставленный поток SUMO для mapping '{mapping_id}'. Статус модели не изменен.",
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            }
        if (
            mapping is None
            or not mapping.calibration_eligible
            or sim_entry.get("mapping_id") != mapping_id
            or sim_entry.get("provenance") != "SIMULATED"
            or sim_entry.get("interval_minutes") != obs.get("interval_minutes")
            or sim_entry.get("network_version") != mapping.network_version
            or sim_entry.get("network_configuration_hash") != mapping.configuration_hash
            or sim_entry.get("mapping_version") != mapping.mapping_version
            or sim_entry.get("simulation_id") != ds.get("simulation_campaign_id")
            or sim_entry.get("measurement_window_id") != obs.get("measurement_window_id")
            or obs.get("vehicle_class") != "passenger_car"
        ):
            return {
                "dataset_id": dataset_id, "purpose": purpose, "status": prev_status,
                "previous_status": prev_status, "is_holdout_validation": is_holdout,
                "calibration_dataset_id": _ACTIVE_CALIBRATION_DATASET_ID,
                "validation_dataset_id": _ACTIVE_VALIDATION_DATASET_ID,
                "metrics": {"metric_name": "turning_movement_flow", "unit": "veh/h", "sample_count": 0, "is_applicable": False, "methodology_note": "SUMO count provenance, mapping/version, vehicle class, simulation campaign, or measurement window is incompatible with the field observation."},
                "thresholds_met": {"mape_under_15": False, "correlation_over_085": False, "coverage_adequate": False, "geh_compliant": False, "mapped_simulation_counts": False},
                "summary_en": "Calibration was not evaluated: SUMO movement count is not comparable to the observed movement, class, campaign, or measurement window.",
                "summary_ru": "Калибровка не выполнена: поток SUMO несопоставим с наблюдаемым направлением или интервалом.",
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            }
        vehicle_classes = sim_entry.get("vehicle_classes")
        if not isinstance(vehicle_classes, dict) or "passenger_car" not in vehicle_classes:
            return {
                "dataset_id": dataset_id, "purpose": purpose, "status": prev_status, "previous_status": prev_status,
                "is_holdout_validation": is_holdout, "calibration_dataset_id": _ACTIVE_CALIBRATION_DATASET_ID,
                "validation_dataset_id": _ACTIVE_VALIDATION_DATASET_ID,
                "metrics": {"metric_name": "turning_movement_flow", "unit": "veh/h", "sample_count": 0, "is_applicable": False,
                            "methodology_note": "Passenger-class simulation count is unavailable; class-specific calibration is not comparable."},
                "thresholds_met": {"mape_under_15": False, "correlation_over_085": False, "coverage_adequate": False, "geh_compliant": False, "mapped_simulation_counts": False},
                "summary_en": "Calibration was not evaluated: the passenger-only SUMO fleet cannot validate this observation without a passenger-class movement count.",
                "summary_ru": "Калибровка не выполнена: отсутствует сопоставленный поток SUMO для класса passenger_car.",
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            }
        intv = obs.get("interval_minutes", 15)
        scale = 60.0 / max(1, intv)
        obs_hourly = obs.get("vehicle_count", 0) * scale
        try:
            sim_hourly = float(vehicle_classes["passenger_car"]) * scale
        except (KeyError, TypeError, ValueError):
            return {
                "dataset_id": dataset_id, "purpose": purpose, "status": prev_status,
                "previous_status": prev_status, "is_holdout_validation": is_holdout,
                "calibration_dataset_id": _ACTIVE_CALIBRATION_DATASET_ID,
                "validation_dataset_id": _ACTIVE_VALIDATION_DATASET_ID,
                "metrics": {"metric_name": "turning_movement_flow", "unit": "veh/h", "sample_count": 0, "is_applicable": False, "methodology_note": "SUMO movement count must contain numeric vehicle_count."},
                "thresholds_met": {"mape_under_15": False, "correlation_over_085": False, "coverage_adequate": False, "geh_compliant": False, "mapped_simulation_counts": False},
                "summary_en": "Calibration was not evaluated: invalid SUMO movement count payload.",
                "summary_ru": "Калибровка не выполнена: неверный формат потока SUMO.",
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            }

        obs_series.append(obs_hourly)
        sim_series.append(sim_hourly)

    val_metrics = compute_validation_metrics(obs_series, sim_series, "turning_movement_flow", "veh/h")
    
    sample_count = val_metrics.get("sample_count", 0)
    mape = val_metrics.get("mape")
    r = val_metrics.get("correlation")
    geh_pass = val_metrics.get("geh_pass", False)
    geh_pct = val_metrics.get("geh_pct_under_5", 0.0)
    unique_ix_count = len(ds.get("unique_intersections", []))

    mape_ok = mape is not None and mape <= 15.0
    r_ok = r is not None and r >= 0.85
    coverage_ok = unique_ix_count >= 4

    new_status = prev_status

    if is_holdout:
        # Holdout Validation checks
        if _ACTIVE_CALIBRATION_DATASET_ID == dataset_id:
            # Cannot validate using the same dataset
            summary_en = (
                f"Validation Error: Dataset '{dataset_id}' was used for calibration. "
                "The model cannot be marked VALIDATED using the same dataset. An independent holdout dataset is required."
            )
            summary_ru = (
                f"Ошибка валидации: Набор данных '{dataset_id}' использовался для калибровки. "
                "Модель не может быть признана ВАЛИДИРОВАННОЙ по тем же данным. Требуется независимый проверочный набор."
            )
            return {
                "dataset_id": dataset_id,
                "purpose": purpose,
                "status": prev_status,
                "previous_status": prev_status,
                "is_holdout_validation": True,
                "calibration_dataset_id": _ACTIVE_CALIBRATION_DATASET_ID,
                "validation_dataset_id": None,
                "metrics": val_metrics,
                "thresholds_met": {
                    "mape_under_15": mape_ok,
                    "correlation_over_085": r_ok,
                    "coverage_adequate": coverage_ok,
                    "geh_compliant": geh_pass,
                    "independent_holdout": False,
                },
                "summary_en": summary_en,
                "summary_ru": summary_ru,
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            }

        if prev_status not in ("CALIBRATED", "PARTIALLY_CALIBRATED"):
            summary_en = "Holdout validation attempted on UNCALIBRATED model. Calibrate model with calibration dataset first."
            summary_ru = "Попытка валидации на некалиброванной модели. Сначала выполните калибровку."
            new_status = "UNCALIBRATED"
        elif sample_count >= 4 and mape_ok and r_ok and coverage_ok and geh_pass:
            new_status = "VALIDATED"
            _ACTIVE_VALIDATION_DATASET_ID = dataset_id
            _ACTIVE_CALIBRATION_STATUS = new_status
            summary_en = (
                f"Model successfully VALIDATED against independent holdout dataset '{dataset_id}' "
                f"({sample_count} observations across {unique_ix_count} intersections). "
                f"UrbanMind configured GEH criterion met for {geh_pct}% of flows, MAPE: {mape}%, Pearson r: {r}."
            )
            summary_ru = (
                f"Модель успешно ВАЛИДИРОВАНА по независимому набору данных '{dataset_id}' "
                f"({sample_count} наблюдений на {unique_ix_count} перекрестках). "
                f"Настроенный критерий GEH UrbanMind выполнен для {geh_pct}% потоков, MAPE: {mape}%, r: {r}."
            )
        else:
            summary_en = (
                f"Holdout validation completed. Model remains {prev_status} "
                f"(MAPE: {mape or 'N/A'}%, r: {r or 'N/A'}%, GEH pass rate: {geh_pct}%)."
            )
            summary_ru = (
                f"Проверочная валидация завершена. Статус сохранен: {prev_status} "
                f"(MAPE: {mape or 'Н/Д'}%, r: {r or 'Н/Д'}, доля GEH < 5: {geh_pct}%)."
            )
    else:
        # Calibration Dataset evaluation
        if sample_count >= 4 and mape_ok and r_ok and coverage_ok:
            new_status = "CALIBRATED"
            _ACTIVE_CALIBRATION_DATASET_ID = dataset_id
        elif sample_count > 0:
            new_status = "PARTIALLY_CALIBRATED"
            _ACTIVE_CALIBRATION_DATASET_ID = dataset_id
        else:
            new_status = "UNCALIBRATED"

        _ACTIVE_CALIBRATION_STATUS = new_status
        summary_en = (
            f"Calibration evaluated across {sample_count} observations ({unique_ix_count} intersections). "
            f"Status transitioned from {prev_status} to {new_status} (MAPE: {mape or 'N/A'}%, r: {r or 'N/A'})."
        )
        summary_ru = (
            f"Калибровка оценена по {sample_count} натурным наблюдениям ({unique_ix_count} перекрестков). "
            f"Статус изменен с {prev_status} на {new_status} (MAPE: {mape or 'Н/Д'}%, r: {r or 'Н/Д'})."
        )

    return {
        "dataset_id": dataset_id,
        "purpose": purpose,
        "status": new_status,
        "previous_status": prev_status,
        "is_holdout_validation": is_holdout,
        "calibration_dataset_id": _ACTIVE_CALIBRATION_DATASET_ID,
        "validation_dataset_id": _ACTIVE_VALIDATION_DATASET_ID,
        "metrics": val_metrics,
        "thresholds_met": {
            "mape_under_15": mape_ok,
            "correlation_over_085": r_ok,
            "coverage_adequate": coverage_ok,
            "geh_compliant": geh_pass,
            "independent_holdout": is_holdout and (_ACTIVE_CALIBRATION_DATASET_ID != dataset_id),
        },
        "summary_en": summary_en,
        "summary_ru": summary_ru,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_field_validation_protocol(spatial_scope_id: str = "central_corridor") -> FieldValidationProtocol:
    """
    Returns the configurable multi-day field validation protocol for Tashkent Central Corridor.
    """
    return {
        "protocol_id": "UM-FVP-2026-TASHKENT-01",
        "title_en": "Field Validation Readiness Protocol (verification required)",
        "title_ru": "Протокол готовности к натурной валидации (требуется верификация)",
        "recommended_duration_days": 14,
        "sampling_interval_min": 15,
        "intersections": [],
        "approaches": [],
        "movements": ["through", "left", "right", "u_turn"],
        "time_windows": [
            "Morning Peak: 07:30 - 09:30",
            "Midday Off-Peak: 12:00 - 14:00",
            "Evening Peak: 17:30 - 19:30",
        ],
        "vehicle_classes": ["passenger_car"],
        "context_fields": ["weather_condition", "ambient_temperature_c", "road_surface_state", "incident_flags"],
        "description_en": (
            "No field deployment is enabled. Populate this protocol only after verified field-to-SUMO mappings, "
            "a passenger-class comparison contract, and pre-allocated independent campaigns exist."
        ),
        "description_ru": (
            "Натурное развертывание не включено. Заполняйте протокол только после верификации соответствий "
            "поле—SUMO, контракта класса passenger_car и заранее выделенных независимых кампаний."
        ),
    }


def get_calibration_status(spatial_scope_id: str = "central_corridor") -> CalibrationStatusRecord:
    """
    Returns the real, uninflated calibration status for the spatial scope.
    Explicitly reports UNCALIBRATED for microscopic traffic dynamics when field traffic counts
    are unavailable, while acknowledging OBSERVED ambient air telemetry from Uzhydromet / WAQI.
    """
    global _ACTIVE_CALIBRATION_STATUS, _ACTIVE_CALIBRATION_DATASET_ID, _ACTIVE_VALIDATION_DATASET_ID
    
    is_traffic_calib = _ACTIVE_CALIBRATION_STATUS in ("CALIBRATED", "VALIDATED")

    if _ACTIVE_CALIBRATION_STATUS == "UNCALIBRATED":
        exp_en = (
            "Microscopic traffic simulation operates in UNCALIBRATED state. "
            "Network geometry and speed limits match Tashkent Central Corridor, but vehicle movements "
            "are synthetic simulation runs (SUMO TraCI) rather than calibrated against inductive loop/radar counts. "
            "Physical air sensors provide ambient observed baseline only."
        )
        exp_ru = (
            "Микромоделирование трафика находится в статусе «НЕ ОТКАЛИБРОВАНО» (UNCALIBRATED). "
            "Геометрия сети и скоростные лимиты соответствуют Центральному коридору Ташкента, "
            "однако транспортные потоки смоделированы физическим движком SUMO и не откалиброваны по натурным детекторам. "
            "Датчики качества воздуха отражают фоновые натурные уровни."
        )
    elif _ACTIVE_CALIBRATION_STATUS == "PARTIALLY_CALIBRATED":
        exp_en = "Field count observations have been partially imported. Full corridor calibration threshold is in progress."
        exp_ru = "Натурные данные подсчетов частично загружены. Завершается процедура полной калибровки коридора."
    elif _ACTIVE_CALIBRATION_STATUS == "CALIBRATED":
        exp_en = "Corridor traffic volumes are calibrated against validated field turning movement counts."
        exp_ru = "Транспортные объемы коридора откалиброваны по валидированным натурным подсчетам поворотных потоков."
    else:
        exp_en = "Model is VALIDATED against an independent holdout field dataset and UrbanMind's configured GEH acceptance criteria."
        exp_ru = "Модель ВАЛИДИРОВАНА по независимому проверочному набору данных и настроенным критериям приемки GEH UrbanMind."

    return {
        "status": _ACTIVE_CALIBRATION_STATUS,
        "traffic_calibrated": is_traffic_calib,
        "air_quality_calibrated": False,
        "active_calibration_dataset_id": _ACTIVE_CALIBRATION_DATASET_ID,
        "active_validation_dataset_id": _ACTIVE_VALIDATION_DATASET_ID,
        "explanation_en": exp_en,
        "explanation_ru": exp_ru,
        "active_datasets_count": len(_FIELD_DATASETS_STORE) + 2,
        "observed_sources": [
            "Uzhydromet / WAQI Ambient Air Monitoring (Tashkent Central)",
            "OpenStreetMap / Tashkent Municipal Road Geometry",
        ] + [f"Field Dataset: {ds['name']}" for ds in _FIELD_DATASETS_STORE.values()],
        "modeled_sources": [
            "SUMO 1.27.1 Microscopic Physics Engine (TraCI)",
            "SUMO/TraCI emission output collection (configured emission class to be documented)",
        ],
        "methodology_caveats_en": [
            "Simulation tests validate software execution, not real-world transport model accuracy.",
            "Vehicle arrivals follow synthetic Poisson/deterministic demand generators.",
            "Field detector counts must be collected prior to permanent municipal signal re-timing.",
        ],
        "methodology_caveats_ru": [
            "Тесты симуляции подтверждают корректность работы ПО, но не заменяют натурную калибровку.",
            "Генерация потоков использует синтетическое распределение спроса.",
            "Перед изменением рабочих фаз светофоров требуется сбор натурных интенсивностей.",
        ],
    }


def get_model_vs_reality_breakdown(
    baseline_metrics: Optional[Dict[str, Any]] = None,
    scenario_metrics: Optional[Dict[str, Any]] = None,
    env_data: Optional[Dict[str, Any]] = None
) -> ModelVsRealityRecord:
    """
    Classifies all metrics into OBSERVED, SIMULATED, and DERIVED categories,
    preventing non-technical stakeholders from conflating simulation outputs with field measurements.
    """
    base = baseline_metrics or {}
    scen = scenario_metrics or base
    env = env_data or {}

    traffic_obs_value = "Calibration data unavailable" if _ACTIVE_CALIBRATION_STATUS == "UNCALIBRATED" else f"{len(_FIELD_DATASETS_STORE)} datasets active"
    traffic_obs_state = "UNAVAILABLE" if _ACTIVE_CALIBRATION_STATUS == "UNCALIBRATED" else "FIELD_VALIDATED"

    observed_metrics: List[MetricClassification] = [
        {
            "key": "pm25_observed",
            "name_en": "PM2.5 Ambient Concentration",
            "name_ru": "Концентрация PM2.5 (фон)",
            "category": "OBSERVED",
            "source": env.get("source") or "No environmental observation loaded",
            "source_ru": env.get("source") or "Наблюдение окружающей среды не загружено",
            "value": env.get("pm25"),
            "unit": "µg/m³",
            "calibration_state": "OBSERVED_FIELD_DATA" if env.get("pm25") is not None else "UNAVAILABLE",
            "description_en": "External ambient observation when a provider returns a value; otherwise unavailable.",
            "description_ru": "Внешнее фоновое наблюдение при наличии значения от провайдера; иначе недоступно.",
        },
        {
            "key": "ambient_temp_observed",
            "name_en": "Ambient Temperature",
            "name_ru": "Температура воздуха",
            "category": "OBSERVED",
            "source": env.get("source") or "No environmental observation loaded",
            "source_ru": env.get("source") or "Наблюдение окружающей среды не загружено",
            "value": env.get("temperature"),
            "unit": "°C",
            "calibration_state": "OBSERVED_FIELD_DATA" if env.get("temperature") is not None else "UNAVAILABLE",
            "description_en": "External weather observation when a provider returns a value; otherwise unavailable.",
            "description_ru": "Внешнее метеонаблюдение при наличии значения от провайдера; иначе недоступно.",
        },
        {
            "key": "traffic_counts_field",
            "name_en": "Field Turning Movement Counts",
            "name_ru": "Натурные подсчеты интенсивности",
            "category": "OBSERVED",
            "source": "Municipal Detector Registry",
            "source_ru": "Реестр муниципальных детекторов",
            "value": traffic_obs_value,
            "unit": "veh/h",
            "calibration_state": traffic_obs_state,
            "description_en": "Field inductive loop or radar detector feeds for this corridor.",
            "description_ru": "Натурные датчики потока на перекрестках коридора.",
        },
    ]

    simulated_metrics: List[MetricClassification] = [
        {
            "key": "average_waiting_seconds",
            "name_en": "Sampled accumulated waiting snapshot mean",
            "name_ru": "Среднее накопленное ожидание по выборке снимков",
            "category": "SIMULATED",
            "source": "SUMO 1.27.1 (TraCI)",
            "source_ru": "SUMO 1.27.1 (TraCI)",
            "value": scen.get("average_waiting_seconds", 0.0),
            "unit": "s",
            "calibration_state": "SYNTHETIC_MICROSIMULATION",
            "description_en": "Vehicle stopped time accumulated at signalized intersections in simulation.",
            "description_ru": "Суммарное время простоя транспортных средств у светофоров в симуляции.",
        },
        {
            "key": "average_travel_time_seconds",
            "name_en": "Corridor Travel Time",
            "name_ru": "Время проезда коридора",
            "category": "SIMULATED",
            "source": "SUMO 1.27.1 (TraCI)",
            "source_ru": "SUMO 1.27.1 (TraCI)",
            "value": scen.get("average_travel_time_seconds", 0.0),
            "unit": "s",
            "calibration_state": "SYNTHETIC_MICROSIMULATION",
            "description_en": "Mean duration for vehicles to traverse the 1.2 km corridor segment.",
            "description_ru": "Средняя продолжительность движения по участку коридора 1.2 км.",
        },
        {
            "key": "stops_per_vehicle",
            "name_en": "Stops per Vehicle",
            "name_ru": "Остановок на автомобиль",
            "category": "SIMULATED",
            "source": "SUMO 1.27.1 (TraCI)",
            "source_ru": "SUMO 1.27.1 (TraCI)",
            "value": scen.get("stops_per_vehicle", 0.0),
            "unit": "stops/veh",
            "calibration_state": "SYNTHETIC_MICROSIMULATION",
            "description_en": "Frequency of stop-and-go events recorded across all simulated trips.",
            "description_ru": "Частота полных остановок на маршруте в симуляторе.",
        },
        {
            "key": "sumo_co2_kg",
            "name_en": "Modeled CO₂ Emissions",
            "name_ru": "Моделируемые выбросы CO₂",
            "category": "SIMULATED",
            "source": "SUMO/TraCI emission output",
            "source_ru": "Выходные данные выбросов SUMO/TraCI",
            "value": scen.get("sumo_co2_kg", 0.0),
            "unit": "kg",
            "calibration_state": "DOMAIN_MODEL_ESTIMATE",
            "description_en": "Calculated from instantaneous vehicle acceleration, velocity, and fleet composition.",
            "description_ru": "Расчет на основе ускорений, скорости и структуры автопарка.",
        },
        {
            "key": "sumo_nox_g",
            "name_en": "Estimated NOₓ Emissions",
            "name_ru": "Моделируемые выбросы NOₓ",
            "category": "SIMULATED",
            "source": "SUMO/TraCI emission output",
            "source_ru": "Выходные данные выбросов SUMO/TraCI",
            "value": scen.get("sumo_nox_g", 0.0),
            "unit": "g",
            "calibration_state": "DOMAIN_MODEL_ESTIMATE",
            "description_en": "Nitrogen oxides output modeled from vehicle driving cycles.",
            "description_ru": "Оксиды азота, рассчитанные по циклам движения ТС.",
        },
    ]

    derived_metrics: List[MetricClassification] = [
        {
            "key": "policy_score",
            "name_en": "Multi-Objective Policy Score",
            "name_ru": "Многокритериальная оценка политики",
            "category": "DERIVED",
            "source": "UrbanMind Policy Engine",
            "source_ru": "Движок политик UrbanMind",
            "value": scen.get("policy_score"),
            "unit": "%",
            "calibration_state": "WEIGHTED_HEURISTIC",
            "description_en": "Normalized composite weighted index combining mobility, eco, and access gains.",
            "description_ru": "Взвешенный индекс, объединяющий мобильность, экологию и доступность.",
        },
        {
            "key": "accessibility_score",
            "name_en": "Pedestrian Accessibility Index",
            "name_ru": "Индекс доступности для пешеходов",
            "category": "DERIVED",
            "source": "UrbanMind Spatial Model",
            "source_ru": "Пространственная модель UrbanMind",
            "value": scen.get("accessibility_score"),
            "unit": "/100",
            "calibration_state": "WEIGHTED_HEURISTIC",
            "description_en": "Composite index penalizing pedestrian wait times and reward safe crossings.",
            "description_ru": "Индекс удобства и безопасности пешеходных переходов.",
        },
        {
            "key": "composite_recommendation",
            "name_en": "Simulation-Supported Recommendation",
            "name_ru": "Рекомендация на основе симуляции",
            "category": "DERIVED",
            "source": "UrbanMind Decision Intelligence",
            "source_ru": "Интеллект решений UrbanMind",
            "value": "Candidate for field validation",
            "unit": "rank",
            "calibration_state": "DECISION_SUPPORT_OUTPUT",
            "description_en": "Decision support ranking indicating top candidate for real-world pilot validation.",
            "description_ru": "Ранжированный вариант для проверки в рамках натурного пилота.",
        },
    ]

    return {
        "observed_metrics": observed_metrics,
        "simulated_metrics": simulated_metrics,
        "derived_metrics": derived_metrics,
        "traffic_calibration_summary_en": (
            "Observed traffic count data is currently unavailable for this corridor. "
            "Traffic metrics represent microscopic SUMO physics output and must be verified in the field."
        ),
        "traffic_calibration_summary_ru": (
            "Натурные данные интенсивности движения для данного коридора в настоящее время отсутствуют. "
            "Транспортные показатели получены из симулятора SUMO и требуют натурной верификации."
        ),
        "air_calibration_summary_en": (
            "Physical air monitoring stations (Uzhydromet/WAQI) provide real-world ambient baseline context, "
            "while vehicle emissions (CO2, NOx) are modeled by the configured SUMO emission model."
        ),
        "air_calibration_summary_ru": (
            "Посты мониторинга воздуха (Узгидромет/WAQI) передают натурные фоновые данные, "
            "в то время как выбросы ТС (CO2, NOx) рассчитываются настроенной моделью выбросов SUMO."
        ),
    }
