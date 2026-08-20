from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict
from app.services.spatial.models import SpatialScopeRef, CrossDistrictContext
from app.services.calibration.models import CalibrationStatusRecord, ModelVsRealityRecord, ValidationMetrics


class EvidenceStatus(TypedDict, total=False):
    level: Literal["LOW", "MODERATE", "HIGH"]
    score: int  # 0 to 100
    criteria_breakdown: Dict[str, Any]
    explanation_en: str
    explanation_ru: str


class NextActionRecord(TypedDict, total=False):
    action_code: str
    title_en: str
    title_ru: str
    description_en: str
    description_ru: str
    rationale_en: str
    rationale_ru: str
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    target_location: str


class ExecutiveSummary(TypedDict, total=False):
    scenario_name: str
    scenario_name_ru: str
    policy_name: str
    policy_name_ru: str
    recommended_intervention: str
    recommended_intervention_ru: str
    primary_result: str
    primary_result_ru: str
    environmental_result: str
    environmental_result_ru: str
    main_tradeoff: str
    main_tradeoff_ru: str
    evidence_level: Literal["LOW", "MODERATE", "HIGH"]
    confidence: Literal["high", "medium", "low"]
    recommendation: str
    recommendation_ru: str
    next_action_title: str
    next_action_title_ru: str


class PolicyAudit(TypedDict, total=False):
    policy_id: str
    policy_name: str
    policy_name_ru: str
    objective_question: str
    objective_question_ru: str
    why_won: str
    why_won_ru: str
    policy_weights: Dict[str, float]
    winning_intervention_id: str
    winning_intervention_label: str
    winning_intervention_label_ru: str
    policy_score: float
    mobility_score: float
    environment_score: float
    accessibility_score: float
    constraint_status: Literal["PASS", "VIOLATION"]
    constraint_violations_en: List[str]
    constraint_violations_ru: List[str]


class MetricComparisonRow(TypedDict, total=False):
    key: str
    name_en: str
    name_ru: str
    unit: str
    baseline: float
    optimized: float
    absolute_change: float
    percentage_change: Optional[float]
    direction: Literal["minimize", "maximize"]
    is_improvement: bool
    provenance: str  # "DIRECT" | "SIMULATED" | "OBSERVED" | "ESTIMATED" | "FALLBACK"


class TradeoffBreakdown(TypedDict, total=False):
    improved: List[Dict[str, Any]]
    worsened: List[Dict[str, Any]]
    unchanged: List[Dict[str, Any]]
    constraint_violations: List[str]
    verdict_en: str
    verdict_ru: str


class RobustnessEvidence(TypedDict, total=False):
    state: Literal["NOT_EVALUATED", "SINGLE_RUN", "MULTI_SEED"]
    sample_count: int
    seeds: List[int]
    stats: Dict[str, Dict[str, float]]  # metric_key -> {mean, std_dev, ci_95_low, ci_95_high, min, max}
    is_statistically_significant: bool
    methodology_note_en: str
    methodology_note_ru: str


class MethodologyRecord(TypedDict, total=False):
    network_name: str
    simulation_engine: str
    emission_model: str
    duration_steps: int
    warmup_steps: int
    measurement_steps: int
    demand_scenario: str
    policy_framework: str
    optimization_method: str
    statistical_method: str


class LimitationsRecord(TypedDict, total=False):
    modeled_caveats_en: List[str]
    modeled_caveats_ru: List[str]
    observed_data_caveats_en: List[str]
    observed_data_caveats_ru: List[str]
    derived_indicator_caveats_en: List[str]
    derived_indicator_caveats_ru: List[str]
    data_classes_summary: Dict[str, str]


class DecisionReport(TypedDict, total=False):
    report_id: str
    experiment_id: str
    scenario_id: str
    policy_id: str
    active_policy: str
    intervention_id: str
    created_at: str
    spatial_scope: SpatialScopeRef
    cross_district_context: Optional[CrossDistrictContext]
    executive_summary: ExecutiveSummary
    baseline_metrics: Dict[str, Any]
    optimized_metrics: Dict[str, Any]
    metric_deltas: Dict[str, Any]
    policy_score: float
    policy_score_breakdown: Dict[str, float]
    policy_audit: PolicyAudit
    policy_comparison: Optional[Dict[str, Any]]
    candidate_ranking: Optional[List[Dict[str, Any]]]
    why_won: str
    why_won_ru: str
    metric_comparison: List[MetricComparisonRow]
    tradeoffs: TradeoffBreakdown
    robustness: RobustnessEvidence
    evidence_status: EvidenceStatus
    calibration_status: CalibrationStatusRecord
    model_vs_reality: ModelVsRealityRecord
    validation_summary: ValidationMetrics
    next_action: NextActionRecord
    confidence: Literal["high", "medium", "low"]
    methodology: MethodologyRecord
    limitations: LimitationsRecord
    ai_analysis: Optional[Dict[str, Any]]
    recommendation: str
    recommendation_verdict_en: str
    recommendation_verdict_ru: str
    municipal_disclaimer_en: str
    municipal_disclaimer_ru: str
