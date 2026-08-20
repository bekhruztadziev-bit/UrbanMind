from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.services.pilots.models import PilotCase, PilotStatus
from app.services.spatial.hierarchy import get_default_spatial_scope


# In-memory pilot registry initialized as a planning workspace, not evidence.
_PILOT_CASES_DB: Dict[str, PilotCase] = {
    "PILOT-TASHKENT-CENTRAL-01": {
        "id": "PILOT-TASHKENT-CENTRAL-01",
        "title": "Configured Demonstration Corridor: Signal Scenario Workspace",
        "title_ru": "Настроенный демонстрационный коридор: рабочее пространство сценариев сигналов",
        "spatial_scope": get_default_spatial_scope(),
        "problem_statement": "Draft workspace for collecting field observations and evaluating a future corridor signal pilot.",
            "problem_statement_ru": "Черновое рабочее пространство для сбора натурных данных и оценки будущего пилотного проекта по управлению сигналами на коридоре.",
        "objective": "Evaluate signal coordination strategies under BALANCED policy to minimize corridor delays and vehicle stops while maintaining pedestrian crossing safety.",
        "objective_ru": "Оценка стратегий координации светофоров по политике БАЛАНС для минимизации задержек и остановок при сохранении безопасности пешеходов.",
        "status": "DRAFT",
        "active_policy": "balanced",
        "baseline_summary": {},
        "scenarios_tested": [],
        "experiments": [],
        "decision_reports": [],
        "recommended_option": {},
        "evidence_strength": "NOT_AVAILABLE",
        "calibration_status": "UNCALIBRATED",
        "next_action": {
            "action_code": "FIELD_DETECTOR_VALIDATION",
            "title_en": "Plan verified temporary turning-count validation",
            "title_ru": "Спланировать проверку поворотных потоков с помощью временных детекторов",
            "description_en": "Verify baseline vehicle arrival rates and queue discharge dynamics prior to permanent controller programming.",
            "description_ru": "Проверка фактической интенсивности и динамики схода очередей перед перепрограммированием дорожных контроллеров.",
            "priority": "HIGH",
        },
        "target_stakeholder": "Tashkent City Department of Transport (Toshkent shahar Transport boshqarmasi)",
        "created_at": "2026-08-20T08:00:00Z",
        "updated_at": "2026-08-20T10:00:00Z",
    }
}


def list_pilot_cases() -> List[PilotCase]:
    """Return all registered municipal pilot cases."""
    return list(_PILOT_CASES_DB.values())


def get_pilot_case(pilot_id: str) -> Optional[PilotCase]:
    """Retrieve a single pilot case by ID."""
    return _PILOT_CASES_DB.get(pilot_id)


def create_pilot_case(payload: Dict[str, Any]) -> PilotCase:
    """Create and persist a new municipal pilot case."""
    now = datetime.now(timezone.utc).isoformat()
    pid = payload.get("id") or f"PILOT-{uuid.uuid4().hex[:8].upper()}"

    pilot: PilotCase = {
        "id": pid,
        "title": payload.get("title") or "Municipal Traffic Optimization Pilot",
        "title_ru": payload.get("title_ru") or "Муниципальный пилотный проект оптимизации",
        "spatial_scope": payload.get("spatial_scope") or get_default_spatial_scope(),
        "problem_statement": payload.get("problem_statement") or "Corridor congestion and signal delay optimization.",
        "problem_statement_ru": payload.get("problem_statement_ru") or "Оптимизация задержек и заторов на коридоре.",
        "objective": payload.get("objective") or "Evaluate multi-objective intervention options.",
        "objective_ru": payload.get("objective_ru") or "Оценка вариантов мер по заданным критериям.",
        "status": payload.get("status") or "DRAFT",
        "active_policy": payload.get("active_policy") or "balanced",
        "baseline_summary": payload.get("baseline_summary") or {},
        "scenarios_tested": payload.get("scenarios_tested") or ["midday"],
        "experiments": payload.get("experiments") or [],
        "decision_reports": payload.get("decision_reports") or [],
        "recommended_option": payload.get("recommended_option") or {},
        "evidence_strength": payload.get("evidence_strength") or "NOT_AVAILABLE",
        "calibration_status": payload.get("calibration_status") or "UNCALIBRATED",
        "next_action": payload.get("next_action") or {
            "action_code": "FIELD_VALIDATION",
            "title_en": "Collect baseline turning movement counts",
            "title_ru": "Сбор натурных подсчетов интенсивности",
            "priority": "HIGH",
        },
        "target_stakeholder": payload.get("target_stakeholder") or "Municipal Transport Department",
        "created_at": now,
        "updated_at": now,
    }

    _PILOT_CASES_DB[pid] = pilot
    return pilot


def update_pilot_case(pilot_id: str, payload: Dict[str, Any]) -> Optional[PilotCase]:
    """Update fields on an existing pilot case."""
    pilot = _PILOT_CASES_DB.get(pilot_id)
    if not pilot:
        return None

    allowed_fields = [
        "title", "title_ru", "problem_statement", "problem_statement_ru",
        "objective", "objective_ru", "status", "active_policy",
        "baseline_summary", "scenarios_tested", "experiments",
        "decision_reports", "recommended_option", "evidence_strength",
        "calibration_status", "next_action", "target_stakeholder"
    ]

    for f in allowed_fields:
        if f in payload:
            pilot[f] = payload[f]  # type: ignore

    pilot["updated_at"] = datetime.now(timezone.utc).isoformat()
    _PILOT_CASES_DB[pilot_id] = pilot
    return pilot
