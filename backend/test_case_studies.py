import os
import pytest

os.environ.setdefault("SUMO_HOME", r"C:\Users\user\Downloads\sumo-win64-1.27.1\sumo-1.27.1")

from app.services.case_studies.generator import generate_case_study, DEFAULT_CANONICAL_CASE_ID
from app.services.case_studies.service import get_canonical_case_study, list_case_studies, create_case_study
from app.services.case_studies.exporter import export_case_study_csv, export_case_study_html


@pytest.fixture(scope="module")
def canonical_cs():
    return get_canonical_case_study(language="en")


def test_canonical_case_study_generation(canonical_cs):
    assert canonical_cs["case_id"] == DEFAULT_CANONICAL_CASE_ID
    assert "Configured Demonstration Corridor" in canonical_cs["title"]
    assert len(canonical_cs["problem_statement"]) > 20
    assert canonical_cs["spatial_scope"]["id"] == "central_corridor"
    assert canonical_cs["selected_candidate"]["id"] is not None
    assert "why_won" in canonical_cs["selected_candidate"]
    assert canonical_cs["calibration_status"]["status"] in ("UNCALIBRATED", "PARTIALLY_CALIBRATED", "CALIBRATED", "VALIDATED")
    assert canonical_cs["prediction_vs_reality"]["validation_status"] == "PENDING_FIELD_DEPLOYMENT"
    assert len(canonical_cs["what_we_know_en"]) > 0
    assert len(canonical_cs["what_we_do_not_know_en"]) > 0


def test_case_study_reproducibility_and_provenance(canonical_cs):
    repro = canonical_cs.get("reproducibility_record", {})
    assert "simulation_configuration_hash" in repro
    assert repro.get("sample_size") == 3
    assert repro.get("degrees_of_freedom") == 2
    assert repro.get("t_critical") == pytest.approx(4.303, 0.01)
    assert repro.get("aggregation_method") == "IMPROVEMENT_OF_MEAN_METRICS"

    prov = canonical_cs.get("provenance_views", {})
    assert "delay" in prov
    assert "Student-t" in prov["delay"]["statistical_method"]


def test_case_study_primary_and_secondary_outcomes(canonical_cs):
    prim = canonical_cs.get("primary_outcomes", [])
    assert len(prim) >= 4
    delay_outcome = next((p for p in prim if p["key"] == "average_waiting_seconds"), None)
    assert delay_outcome is not None
    assert delay_outcome["baseline"] >= 0
    assert delay_outcome["optimized"] >= 0
    assert delay_outcome["provenance"] == "SIMULATED"
    assert delay_outcome["t_critical"] == pytest.approx(4.303, 0.01)

    sec = canonical_cs.get("secondary_outcomes", [])
    assert len(sec) >= 3


def test_case_study_epistemic_statements(canonical_cs):
    ep = canonical_cs.get("epistemic_statements", [])
    assert len(ep) >= 3
    categories = {e["category"] for e in ep}
    assert "SIMULATED" in categories
    assert "DERIVED" in categories
    assert "ASSUMPTION" in categories


def test_case_study_bilingual_support(canonical_cs):
    assert len(canonical_cs.get("title_ru", "")) > 0
    assert len(canonical_cs.get("problem_statement_ru", "")) > 0
    assert len(canonical_cs.get("what_we_know_ru", [])) > 0
    assert len(canonical_cs.get("what_we_do_not_know_ru", [])) > 0


def test_case_study_csv_exporter(canonical_cs):
    csv_text = export_case_study_csv(canonical_cs)
    assert "URBANMIND CASE STUDY AUDIT REPORT" in csv_text
    assert canonical_cs["case_id"] in csv_text
    assert "REPRODUCIBILITY & AUDIT RECORD" in csv_text
    assert "PRIMARY OUTCOME METRICS" in csv_text
    assert "EPISTEMIC FACTUAL CLASSIFICATION" in csv_text


def test_case_study_html_exporter(canonical_cs):
    html_text = export_case_study_html(canonical_cs, language="en")
    assert "<!DOCTYPE html>" in html_text
    assert "URBANMIND" in html_text
    assert canonical_cs["case_id"] in html_text
    assert "1. Problem Statement" in html_text
    assert "2. Primary Mobility Outcomes" in html_text
    assert "3. Epistemic Classification" in html_text
    assert "What We Know" in html_text
    assert "What We Do Not Yet Know" in html_text
