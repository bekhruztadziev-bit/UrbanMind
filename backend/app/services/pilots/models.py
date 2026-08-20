from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict
from app.services.spatial.models import SpatialScopeRef


PilotStatus = Literal["DRAFT", "ANALYSIS", "REVIEW", "FIELD_VALIDATION", "COMPLETED"]


class PilotCase(TypedDict, total=False):
    id: str
    title: str
    title_ru: str
    spatial_scope: SpatialScopeRef
    problem_statement: str
    problem_statement_ru: str
    objective: str
    objective_ru: str
    status: PilotStatus
    active_policy: str
    baseline_summary: Dict[str, Any]
    scenarios_tested: List[str]
    experiments: List[str]
    decision_reports: List[str]
    recommended_option: Dict[str, Any]
    evidence_strength: Literal["LOW", "MODERATE", "HIGH"]
    calibration_status: Literal["UNCALIBRATED", "PARTIALLY_CALIBRATED", "CALIBRATED", "VALIDATED"]
    next_action: Dict[str, Any]
    target_stakeholder: str
    created_at: str
    updated_at: str
