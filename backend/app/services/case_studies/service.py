from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.services.case_studies.models import CaseStudy
from app.services.case_studies.generator import generate_case_study, DEFAULT_CANONICAL_CASE_ID
from app.services.simulation.canonical import (
    load_canonical_case_study_artifact,
    write_canonical_experiment_artifact,
)


_CASE_STUDIES_STORE: Dict[str, CaseStudy] = {}


def get_canonical_case_study(language: str = "en") -> CaseStudy:
    """Return the locked conference snapshot; ordinary navigation never reruns SUMO."""
    if DEFAULT_CANONICAL_CASE_ID not in _CASE_STUDIES_STORE:
        cs = load_canonical_case_study_artifact()
        if cs is None:
            raise RuntimeError(
                "Canonical Case Study artifact is unavailable or stale. "
                "Use the deliberate developer/admin canonical rerun action to regenerate it."
            )
        cs["artifact_type"] = "PRECOMPUTED_SIMULATION_ARTIFACT"
        _CASE_STUDIES_STORE[DEFAULT_CANONICAL_CASE_ID] = cs
    return _CASE_STUDIES_STORE[DEFAULT_CANONICAL_CASE_ID]


def list_case_studies(language: str = "en") -> List[CaseStudy]:
    """Lists all registered case studies."""
    canonical = get_canonical_case_study(language=language)
    return list(_CASE_STUDIES_STORE.values())


def get_case_study(case_id: str, language: str = "en") -> Optional[CaseStudy]:
    """Retrieves a single case study by ID."""
    if case_id == DEFAULT_CANONICAL_CASE_ID:
        return get_canonical_case_study(language=language)
    return _CASE_STUDIES_STORE.get(case_id)


def create_case_study(data: Dict[str, Any], language: str = "en") -> CaseStudy:
    """Creates or derives a new CaseStudy."""
    case_id = data.get("case_id") or f"UM-CS-2026-{len(_CASE_STUDIES_STORE) + 1:03d}"
    cs = generate_case_study(
        canonical_experiment=data.get("experiment"),
        decision_report=data.get("report"),
        case_id=case_id,
        language=language
    )
    _CASE_STUDIES_STORE[case_id] = cs
    return cs


def rerun_canonical_case_study_artifact(language: str = "en") -> CaseStudy:
    """Explicit developer/admin operation; never called by normal case navigation."""
    write_canonical_experiment_artifact(language=language)
    cs = load_canonical_case_study_artifact()
    if cs is None:
        raise RuntimeError("Canonical artifact was written but its Case Study snapshot could not be verified.")
    _CASE_STUDIES_STORE[DEFAULT_CANONICAL_CASE_ID] = cs
    return cs
