from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict
from app.services.spatial.models import SpatialScopeRef
from app.services.reports.models import (
    EvidenceStatus,
    NextActionRecord,
    TradeoffBreakdown,
    RobustnessEvidence,
    LimitationsRecord,
)
from app.services.calibration.models import (
    CalibrationStatusRecord,
    ModelVsRealityRecord,
    ValidationMetrics,
    FieldValidationProtocol,
)


class EpistemicStatement(TypedDict, total=False):
    statement_id: str
    text_en: str
    text_ru: str
    category: Literal["OBSERVED", "SIMULATED", "DERIVED", "ASSUMPTION"]
    source: str
    source_ru: str
    notes_en: str
    notes_ru: str


class ProvenanceDetail(TypedDict, total=False):
    metric_name: str
    headline_value: str
    source: str
    experiment_id: str
    scenario: str
    intervention: str
    policy: str
    seeds: List[int]
    aggregation_method: str
    statistical_method: str
    calibration_status: str


class PredictionVsRealityRecord(TypedDict, total=False):
    prediction_metric: str
    predicted_value: float
    observed_outcome: Optional[float]
    absolute_error: Optional[float]
    relative_error_pct: Optional[float]
    validation_status: Literal["PENDING_FIELD_DEPLOYMENT", "CONFIRMED", "DEVIATED", "INSUFFICIENT_DATA"]
    notes_en: str
    notes_ru: str


class CaseStudy(TypedDict, total=False):
    case_id: str                          # e.g., "UM-CS-2026-001"
    experiment_id: str                    # e.g., "UM-EXP-2026-001"
    report_id: str                        # e.g., "UM-REP-2026-001"
    title: str
    title_ru: str
    problem_statement: str
    problem_statement_ru: str
    spatial_scope: SpatialScopeRef
    demand_scenarios_tested: List[str]    # ["0.8x", "1.0x", "1.2x"]
    policy_comparison: Dict[str, Any]     # FLOW vs ECO vs BALANCED comparison
    selected_candidate: Dict[str, Any]
    key_results: Dict[str, Any]
    primary_outcomes: List[Dict[str, Any]]
    secondary_outcomes: List[Dict[str, Any]]
    reproducibility_record: Dict[str, Any]
    provenance_views: Dict[str, ProvenanceDetail]
    epistemic_statements: List[EpistemicStatement]
    tradeoffs: TradeoffBreakdown
    robustness: RobustnessEvidence
    evidence_strength: EvidenceStatus
    calibration_status: CalibrationStatusRecord
    model_vs_reality: ModelVsRealityRecord
    prediction_vs_reality: PredictionVsRealityRecord
    field_validation_protocol: FieldValidationProtocol
    next_action: NextActionRecord
    limitations: LimitationsRecord
    what_we_know_en: List[str]
    what_we_know_ru: List[str]
    what_we_do_not_know_en: List[str]
    what_we_do_not_know_ru: List[str]
    created_at: str


class CaseStudyExport(TypedDict, total=False):
    case_id: str
    filename: str
    format: str
    content: str
