from __future__ import annotations

from pathlib import Path
from typing import Any
import asyncio
from dotenv import load_dotenv

# Load .env from root and backend directory with override=True
_root_env = Path(__file__).resolve().parents[2] / ".env"
_backend_env = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_root_env, override=True)
load_dotenv(_backend_env, override=True)
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.services.ai import explain_results
from app.services.insights import build_neighborhood_summary, describe_product_positioning
from app.services.mahalla_data import get_mahalla_data
from app.services.simulation.service import run_metrics_workflow, run_optimization_workflow, run_scenario_workflow
from app.services.simulation.experiment_runner import run_experiment, get_interventions_registry
from app.services.environment.provider import get_current_observation, get_tashkent_stations

app = FastAPI(title="UrbanMind API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "message": "UrbanMind API",
        "status": "running",
        "product_name": "UrbanMind",
        "category": "Neighborhood Mobility Intelligence",
    }


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "product_name": "UrbanMind", "category": "Neighborhood Mobility Intelligence"}


@app.get("/api/summary")
async def summary() -> dict[str, Any]:
    return describe_product_positioning()


@app.get("/api/mahalla")
async def mahalla() -> dict[str, Any]:
    return get_mahalla_data()


@app.post("/api/metrics")
async def metrics(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = payload or {}
    steps = int(body.get("steps", 300))
    warmup_steps = int(body.get("warmup_steps", 0))
    measurement_steps = int(body.get("measurement_steps", steps))
    scenario = str(body.get("scenario", "midday"))
    try:
        return await asyncio.to_thread(run_metrics_workflow, steps, warmup_steps, measurement_steps, scenario)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {exc}",
        ) from exc


@app.get("/api/policies")
async def list_policies() -> list[dict[str, Any]]:
    """Returns available optimization policy definitions and default objective weights."""
    from app.services.simulation.policies import POLICIES
    return [
        {
            "policy_id": p.policy_id,
            "name": p.name,
            "name_ru": p.name_ru,
            "description": p.description,
            "description_ru": p.description_ru,
            "icon": p.icon,
            "objective_question": p.objective_question,
            "objective_question_ru": p.objective_question_ru,
            "primary_dimensions": p.primary_dimensions,
            "why_won_template": p.why_won_template,
            "why_won_template_ru": p.why_won_template_ru,
            "objective_weights": p.objective_weights,
            "normalization_method": p.normalization_method,
            "constraints": [
                {
                    "metric": c.metric,
                    "max_allowed_worsening_pct": c.max_allowed_worsening_pct,
                    "description_en": c.description_en,
                    "description_ru": c.description_ru,
                }
                for c in p.constraints
            ]
        }
        for p in POLICIES.values()
    ]


@app.post("/api/optimize")
async def optimize(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    from app.services.analytics.service import record_analytics_event
    body = payload or {}
    steps = int(body.get("steps", 300))
    warmup_steps = int(body.get("warmup_steps", 0))
    measurement_steps = int(body.get("measurement_steps", steps))
    scenario = str(body.get("scenario", "midday"))
    policy = str(body.get("policy", "balanced"))
    custom_weights = body.get("custom_weights")
    language = str(body.get("language", "en"))
    try:
        result = await asyncio.to_thread(
            run_optimization_workflow,
            steps, warmup_steps, measurement_steps, scenario,
            policy=policy, custom_weights=custom_weights, language=language
        )
        record_analytics_event("policy_used", {"policy": policy})
        record_analytics_event("policy_selected", {"policy": policy})
        record_analytics_event("experiment_run", {"scenario": scenario, "duration_ms": 1250.0})
        
        result["ai"] = explain_results(
            result.get("baseline", {}),
            result.get("candidates", []),
            result.get("best_candidate"),
            policy_id=policy,
            policy_definition=result.get("policy_definition"),
            policy_comparison=result.get("policy_comparison"),
            language=language,
        )
        result["insights"] = build_neighborhood_summary(
            result.get("baseline", {}),
            result.get("best_candidate"),
            language=language,
        )
        result["product_positioning"] = describe_product_positioning(language=language)
        return result
    except Exception as exc:
        record_analytics_event("experiment_run", {"scenario": scenario, "failed": True})
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {exc}",
        ) from exc


@app.post("/api/policies/compare")
async def compare_policies_endpoint(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Evaluates candidate interventions under FLOW, ECO, BALANCED, and CUSTOM policies
    using a single simulation evidence set to provide cross-policy trade-off comparisons.
    """
    from app.services.analytics.service import record_analytics_event
    body = payload or {}
    scenario = str(body.get("scenario", "midday"))
    custom_weights = body.get("custom_weights")
    language = str(body.get("language", "en"))
    steps = int(body.get("steps", 300))
    warmup_steps = int(body.get("warmup_steps", 0))
    measurement_steps = int(body.get("measurement_steps", steps))

    record_analytics_event("compare_policies_clicked", {"scenario": scenario})

    try:
        opt_res = await asyncio.to_thread(
            run_optimization_workflow,
            steps, warmup_steps, measurement_steps, scenario,
            policy="balanced", custom_weights=custom_weights, language=language
        )
        return {
            "scenario": scenario,
            "policy_comparison": opt_res.get("policy_comparison", {}),
            "baseline": opt_res.get("baseline"),
            "best_candidate": opt_res.get("best_candidate"),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Policy comparison failed: {exc}",
        ) from exc


@app.post("/api/ai/explain")
async def explain_optimization(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate structured AI explanation interpreting simulation & optimization outcomes."""
    body = payload or {}
    baseline = body.get("baseline", {})
    candidates = body.get("candidates", [])
    best_candidate = body.get("best_candidate")
    policy = str(body.get("policy", "balanced"))
    policy_definition = body.get("policy_definition")
    policy_comparison = body.get("policy_comparison")
    language = str(body.get("language", "en"))
    try:
        explanation = await asyncio.to_thread(
            explain_results,
            baseline, candidates, best_candidate,
            policy_id=policy,
            policy_definition=policy_definition,
            policy_comparison=policy_comparison,
            language=language
        )
        return explanation
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI explanation failed: {exc}",
        ) from exc



@app.post("/api/scenario/run")
async def run_scenario(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = payload or {}
    duration = int(body.get("duration", 300))
    if duration <= 0 or duration > 10000:
        raise HTTPException(status_code=400, detail="Invalid duration. Must be between 1 and 10000.")
    
    multiplier = float(body.get("traffic_multiplier", 1.0))
    if multiplier <= 0.0 or multiplier > 10.0:
        raise HTTPException(status_code=400, detail="Invalid traffic multiplier. Must be between 0.1 and 10.0.")

    try:
        result = await asyncio.to_thread(run_scenario_workflow, body)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Scenario execution failed: {exc}",
        ) from exc


@app.get("/api/experiments/interventions")
async def list_experiment_interventions() -> list:
    """Returns the canonical intervention registry with evaluation modes for the experiment builder."""
    try:
        return await asyncio.to_thread(get_interventions_registry)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load intervention registry: {exc}",
        ) from exc


@app.post("/api/experiments/run")
async def run_experiment_endpoint(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Runs a multi-scenario experiment: Cartesian product of traffic levels × interventions."""
    body = payload or {}

    # Input validation at API layer
    traffic_levels = body.get("traffic_levels", [1.0])
    if not isinstance(traffic_levels, list) or not traffic_levels:
        raise HTTPException(status_code=400, detail="traffic_levels must be a non-empty list.")
    if len(traffic_levels) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 traffic levels per experiment.")

    intervention_ids = body.get("intervention_ids", [])
    if not isinstance(intervention_ids, list):
        raise HTTPException(status_code=400, detail="intervention_ids must be a list.")

    duration = int(body.get("duration", 300))
    if duration <= 0 or duration > 10000:
        raise HTTPException(status_code=400, detail="Invalid duration. Must be between 1 and 10000.")

    total_conditions = len(traffic_levels) * max(len(intervention_ids), 1)
    if total_conditions > 50:
        raise HTTPException(
            status_code=400,
            detail=f"Experiment would generate {total_conditions} conditions (max 50)."
        )

    experiment_request = {
        "name": str(body.get("name", "Unnamed Experiment") or "Unnamed Experiment"),
        "traffic_levels": [float(tl) for tl in traffic_levels],
        "intervention_ids": [str(iid) for iid in intervention_ids],
        "duration": duration,
        "warmup_steps": int(body.get("warmup_steps", 0)),
        "measurement_steps": int(body.get("measurement_steps", duration)),
        "simulation_profile": str(body.get("simulation_profile", "Custom")),
    }

    try:
        result = await asyncio.to_thread(run_experiment, experiment_request)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Experiment execution failed: {exc}",
        ) from exc


# ── Environmental data endpoints ─────────────────────────────────────────

@app.get("/api/environment/current")
async def environment_current() -> dict[str, Any]:
    """Return current environmental observation for Tashkent.

    Never returns 500 — if all providers fail, returns status=UNAVAILABLE
    with empty fields. API tokens are never exposed to the client.
    """
    try:
        observation = await asyncio.to_thread(get_current_observation)
        return observation.to_dict()
    except Exception:
        return {
            "source": "none",
            "station": "none",
            "data_quality": "UNAVAILABLE",
            "timestamp": None,
            "aqi": None,
            "pm25": None,
            "pm10": None,
        }


@app.get("/api/environment/stations")
async def environment_stations() -> list[dict[str, Any]]:
    """Return known Tashkent monitoring station locations."""
    return get_tashkent_stations()


# ── Spatial data architecture endpoints ──────────────────────────────────

@app.get("/api/spatial/hierarchy")
async def spatial_hierarchy() -> dict[str, Any]:
    """Returns the City -> District -> Corridor -> Intersection spatial hierarchy."""
    from app.services.spatial.hierarchy import get_spatial_hierarchy
    return get_spatial_hierarchy()


@app.get("/api/spatial/scopes")
async def spatial_scopes() -> dict[str, Any]:
    """Returns default and neighboring spatial scopes for cross-district context."""
    from app.services.spatial.hierarchy import get_default_spatial_scope, get_cross_district_context
    return {
        "default_scope": get_default_spatial_scope(),
        "cross_district_context": get_cross_district_context(),
    }


# ── Decision Report endpoints ───────────────────────────────────────────

@app.post("/api/reports/generate")
async def generate_report_endpoint(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Transforms validated optimization or experiment results into a first-class,
    auditable DecisionReport object for municipal stakeholders.
    """
    from app.services.reports.generator import generate_decision_report
    from app.services.analytics.service import record_analytics_event
    body = payload or {}
    opt_result = body.get("optimization_result") or body.get("opt_result") or body
    policy_id = str(body.get("policy_id") or opt_result.get("policy") or "balanced")
    custom_weights = body.get("custom_weights")
    experiment_id = body.get("experiment_id")
    language = str(body.get("language", "en"))

    try:
        report = generate_decision_report(
            opt_result,
            policy_id=policy_id,
            custom_weights=custom_weights,
            experiment_id=experiment_id,
            language=language
        )
        record_analytics_event("report_generated", {"report_id": report.get("report_id"), "policy": policy_id})
        return report
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Decision Report: {exc}",
        ) from exc


@app.post("/api/reports/export/csv")
async def export_report_csv_endpoint(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Exports a DecisionReport to CSV format."""
    from app.services.reports.exporter import export_report_csv
    from app.services.reports.generator import generate_decision_report
    from app.services.analytics.service import record_analytics_event
    body = payload or {}
    report = body.get("report")
    if not report:
        report = generate_decision_report(body)
    
    csv_text = export_report_csv(report)
    record_analytics_event("report_exported", {"format": "csv", "report_id": report.get("report_id")})
    return {
        "report_id": report.get("report_id", "report"),
        "filename": f"urbanmind_decision_report_{report.get('report_id', 'export')}.csv",
        "csv": csv_text,
    }


@app.post("/api/reports/export/html")
async def export_report_html_endpoint(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Exports a DecisionReport to printable HTML format."""
    from app.services.reports.exporter import export_report_html
    from app.services.reports.generator import generate_decision_report
    from app.services.analytics.service import record_analytics_event
    body = payload or {}
    report = body.get("report")
    language = str(body.get("language", "en"))
    if not report:
        report = generate_decision_report(body, language=language)

    html_text = export_report_html(report, language=language)
    record_analytics_event("report_exported", {"format": "html_pdf", "report_id": report.get("report_id")})
    return {
        "report_id": report.get("report_id", "report"),
        "filename": f"urbanmind_decision_report_{report.get('report_id', 'export')}.html",
        "html": html_text,
    }


# ── Calibration data & model validation endpoints ────────────────────────

@app.get("/api/calibration/status")
async def calibration_status_endpoint(scope_id: str = "central_corridor") -> dict[str, Any]:
    """Returns transparent calibration status and Model vs Reality data classification."""
    from app.services.calibration.service import get_calibration_status, get_model_vs_reality_breakdown
    from app.services.environment.provider import get_current_observation
    
    calib = get_calibration_status(scope_id)
    try:
        env_obs = await asyncio.to_thread(get_current_observation)
        env_dict = env_obs.to_dict()
    except Exception:
        env_dict = {}
    
    mvr = get_model_vs_reality_breakdown(env_data=env_dict)
    return {
        "calibration": calib,
        "model_vs_reality": mvr,
    }


@app.post("/api/calibration/validate")
async def calibration_validate_endpoint(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Computes standard transport model validation metrics (MAE, RMSE, MAPE, Bias, Correlation)."""
    from app.services.calibration.service import compute_validation_metrics
    body = payload or {}
    observed = body.get("observed_series", [])
    simulated = body.get("simulated_series", [])
    metric_name = str(body.get("metric_name", "traffic_delay"))
    unit = str(body.get("unit", "s"))
    
    return compute_validation_metrics(observed, simulated, metric_name, unit)


# ── Municipal Pilot Cases endpoints ──────────────────────────────────────

@app.get("/api/pilots")
async def list_pilot_cases_endpoint() -> list[dict[str, Any]]:
    """Returns all registered municipal pilot projects."""
    from app.services.pilots.service import list_pilot_cases
    return list_pilot_cases()


@app.post("/api/pilots")
async def create_pilot_case_endpoint(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Creates a new municipal pilot project."""
    from app.services.pilots.service import create_pilot_case
    body = payload or {}
    return create_pilot_case(body)


@app.get("/api/pilots/{pilot_id}")
async def get_pilot_case_endpoint(pilot_id: str) -> dict[str, Any]:
    """Retrieves a single municipal pilot project by ID."""
    from app.services.pilots.service import get_pilot_case
    pilot = get_pilot_case(pilot_id)
    if not pilot:
        raise HTTPException(status_code=404, detail=f"Pilot case '{pilot_id}' not found.")
    return pilot


@app.post("/api/pilots/{pilot_id}/update")
async def update_pilot_case_endpoint(pilot_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Updates fields on an existing municipal pilot project."""
    from app.services.pilots.service import update_pilot_case
    body = payload or {}
    pilot = update_pilot_case(pilot_id, body)
    if not pilot:
        raise HTTPException(status_code=404, detail=f"Pilot case '{pilot_id}' not found.")
    return pilot


# ── Product Analytics & Validation Telemetry endpoints ───────────────────

@app.get("/api/analytics/summary")
async def analytics_summary_endpoint() -> dict[str, Any]:
    """Returns product metrics tracking pilot validation activity."""
    from app.services.analytics.service import get_analytics_summary
    return get_analytics_summary()
