from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict
from app.services.spatial.models import SpatialScopeRef


CalibrationStatus = Literal["UNCALIBRATED", "PARTIALLY_CALIBRATED", "CALIBRATED", "VALIDATED"]
DatasetPurpose = Literal["CALIBRATION", "VALIDATION_HOLDOUT"]
DataQuality = Literal["HIGH_PRECISION", "STANDARD_TELEMETRY", "ESTIMATED_PROXY", "SYNTHETIC_CALIBRATION"]
FieldMovement = Literal["through", "left", "right", "u_turn"]
VehicleType = Literal["passenger_car", "bus", "truck", "motorcycle", "all"]


class FieldObservationRecord(TypedDict, total=False):
    observation_id: str
    dataset_id: str
    purpose: DatasetPurpose
    timestamp: str
    measurement_window_id: str
    spatial_scope: SpatialScopeRef
    intersection_id: str
    approach_id: str
    movement: FieldMovement
    mapping_id: str
    interval_minutes: int
    vehicle_count: int
    vehicle_class: VehicleType
    source: str
    quality: DataQuality
    notes: str
    observation_content_hash: str


class FieldObservationDataset(TypedDict, total=False):
    dataset_id: str
    name: str
    description: str
    campaign_id: str
    simulation_campaign_id: str
    purpose: DatasetPurpose
    uploaded_at: str
    spatial_scope: SpatialScopeRef
    observations: List[FieldObservationRecord]
    is_valid: bool
    validation_errors: List[str]
    diagnostics: List[Dict[str, Any]]
    mapping_coverage: Dict[str, Any]
    total_counts: int
    unique_intersections: List[str]
    time_window: str
    dataset_content_hash: str
    observation_content_hashes: List[str]


class CalibrationDataset(TypedDict, total=False):
    dataset_id: str
    source: str
    source_type: Literal["PHYSICAL_SENSOR", "MANUAL_COUNT", "RADAR_DETECTOR", "SIMULATION_OUTPUT", "SYNTHETIC"]
    timestamp: str
    spatial_scope: SpatialScopeRef
    metric: str
    observed_value: Optional[float]
    simulated_value: Optional[float]
    error: Optional[float]
    unit: str
    quality: DataQuality
    is_available: bool
    notes: str


class ValidationMetrics(TypedDict, total=False):
    metric_name: str
    unit: str
    sample_count: int
    mae: Optional[float]          # Mean Absolute Error
    rmse: Optional[float]         # Root Mean Squared Error
    mape: Optional[float]         # Mean Absolute Percentage Error (%)
    bias: Optional[float]         # Mean Error (positive = overestimating, negative = underestimating)
    mean_bias_error: Optional[float]
    correlation: Optional[float]  # Pearson correlation coefficient r [-1, 1]
    geh_mean: Optional[float]     # Mean GEH statistic
    geh_max: Optional[float]      # Max GEH statistic
    geh_pct_under_5: Optional[float] # % of links with GEH < 5.0
    geh_pass: Optional[bool]      # UrbanMind configured GEH acceptance criterion
    is_applicable: bool
    methodology_note: str


class CalibrationStatusRecord(TypedDict, total=False):
    status: CalibrationStatus
    traffic_calibrated: bool
    air_quality_calibrated: bool
    active_calibration_dataset_id: Optional[str]
    active_validation_dataset_id: Optional[str]
    explanation_en: str
    explanation_ru: str
    active_datasets_count: int
    observed_sources: List[str]
    modeled_sources: List[str]
    methodology_caveats_en: List[str]
    methodology_caveats_ru: List[str]


class MetricClassification(TypedDict, total=False):
    key: str
    name_en: str
    name_ru: str
    category: Literal["OBSERVED", "SIMULATED", "DERIVED", "ASSUMPTION"]
    source: str
    source_ru: str
    value: Any
    unit: str
    calibration_state: str
    description_en: str
    description_ru: str


class ModelVsRealityRecord(TypedDict, total=False):
    observed_metrics: List[MetricClassification]
    simulated_metrics: List[MetricClassification]
    derived_metrics: List[MetricClassification]
    traffic_calibration_summary_en: str
    traffic_calibration_summary_ru: str
    air_calibration_summary_en: str
    air_calibration_summary_ru: str


class CalibrationEvaluationResult(TypedDict, total=False):
    dataset_id: str
    purpose: DatasetPurpose
    status: CalibrationStatus
    previous_status: CalibrationStatus
    is_holdout_validation: bool
    calibration_dataset_id: Optional[str]
    validation_dataset_id: Optional[str]
    metrics: ValidationMetrics
    geh_summary: Optional[Dict[str, Any]]
    thresholds_met: Dict[str, bool]
    summary_en: str
    summary_ru: str
    evaluated_at: str


class PredictionVsRealityItem(TypedDict, total=False):
    metric: str
    metric_ru: str
    observed: float
    predicted: float
    absolute_error: float
    relative_error_pct: float
    geh: Optional[float]
    pass_fail: bool
    dataset_id: str
    purpose: str
    validation_status: str


class FieldValidationProtocol(TypedDict, total=False):
    protocol_id: str
    title_en: str
    title_ru: str
    recommended_duration_days: int
    sampling_interval_min: int
    intersections: List[str]
    approaches: List[str]
    movements: List[str]
    time_windows: List[str]
    vehicle_classes: List[str]
    context_fields: List[str]
    description_en: str
    description_ru: str
