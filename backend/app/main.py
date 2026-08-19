from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.services.ai import explain_results
from app.services.insights import build_neighborhood_summary, describe_product_positioning
from app.services.mahalla_data import get_mahalla_data
import asyncio
from app.services.simulation.service import run_metrics_workflow, run_optimization_workflow, run_scenario_workflow
from app.services.simulation.experiment_runner import run_experiment, get_interventions_registry
from app.services.environment.provider import get_current_observation, get_tashkent_stations

app = FastAPI(title="MahallaMind API")

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
        "message": "MahallaMind API",
        "status": "running",
        "product_name": "MahallaMind",
        "category": "Neighborhood Mobility Intelligence",
    }


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "product_name": "MahallaMind", "category": "Neighborhood Mobility Intelligence"}


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


@app.post("/api/optimize")
async def optimize(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = payload or {}
    steps = int(body.get("steps", 300))
    warmup_steps = int(body.get("warmup_steps", 0))
    measurement_steps = int(body.get("measurement_steps", steps))
    scenario = str(body.get("scenario", "midday"))
    try:
        result = await asyncio.to_thread(run_optimization_workflow, steps, warmup_steps, measurement_steps, scenario)
        result["ai"] = explain_results(
            result.get("baseline", {}),
            result.get("candidates", []),
            result.get("best_candidate"),
        )
        result["insights"] = build_neighborhood_summary(
            result.get("baseline", {}),
            result.get("best_candidate"),
        )
        result["product_positioning"] = describe_product_positioning()
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {exc}",
        ) from exc


@app.post("/api/ai/explain")
async def explain_optimization(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate structured AI explanation interpreting simulation & optimization outcomes."""
    body = payload or {}
    baseline = body.get("baseline", {})
    candidates = body.get("candidates", [])
    best_candidate = body.get("best_candidate")
    try:
        explanation = await asyncio.to_thread(explain_results, baseline, candidates, best_candidate)
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