from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict
from app.services.spatial.models import SpatialScopeRef


CalibrationStatus = Literal["UNCALIBRATED", "PARTIALLY_CALIBRATED", "CALIBRATED", "VALIDATED"]
DataQuality = Literal["HIGH_PRECISION", "STANDARD_TELEMETRY", "ESTIMATED_PROXY", "SYNTHETIC_CALIBRATION"]


class CalibrationDataset(TypedDict, total=False):
    dataset_id: str
    source: str  # e.g., "Uzhydromet Physical Sensor", "Tashkent Manual Traffic Count", "SUMO Microscopic Engine"
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
    correlation: Optional[float]  # Pearson correlation coefficient r [-1, 1]
    is_applicable: bool
    methodology_note: str


class CalibrationStatusRecord(TypedDict, total=False):
    status: CalibrationStatus
    traffic_calibrated: bool
    air_quality_calibrated: bool
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
    category: Literal["OBSERVED", "SIMULATED", "DERIVED"]
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
