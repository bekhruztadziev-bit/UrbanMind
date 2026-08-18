from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.services.ai import explain_results
from app.services.insights import build_neighborhood_summary, describe_product_positioning
from app.services.mahalla_data import get_mahalla_data
from app.services.sumo_runner import optimize_interventions, run_simulation

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
    scenario = str(body.get("scenario", "midday"))
    try:
        return run_simulation(steps=steps, scenario=scenario)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {exc}",
        ) from exc


@app.post("/api/optimize")
async def optimize(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = payload or {}
    steps = int(body.get("steps", 300))
    scenario = str(body.get("scenario", "midday"))
    try:
        result = optimize_interventions(steps=steps, scenario=scenario)
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