# UrbanMind takeover audit — 20 Aug 2026

## Architecture discovered

React/Vite/Leaflet consumes FastAPI endpoints. FastAPI delegates microscopic runs to SUMO through TraCI, derives metrics, runs the deterministic policy engine, then creates decision reports and Case Study #001. Field-calibration services are separate from simulation execution.

Authoritative traffic evidence is:

`SUMO configuration → TraCI measurement window → seed aggregation → intervention metrics → baseline-relative normalization → policy score/ranking → report/case study/frontend`.

Average delay originates from TraCI vehicle waiting-time measurements during the configured measurement window and is labelled `SIMULATED`. It is not a field observation.

## What works

- SUMO/TraCI can run locally without a fabricated fallback.
- FLOW, ECO, BALANCED, and CUSTOM use deterministic policy weights and deterministic “Why This Won” text.
- Case-study/report/calibration APIs and RU/EN frontend paths exist.
- A local `POST /api/metrics` run returned `is_fallback: false`; its movement-count export was legitimately empty because no production movement mappings are verified.

## Implemented in this audit

- Added a strict, immutable movement-mapping registry with network/configuration identity, verification metadata, audit inspector, and no production mappings assumed.
- Added a warm-up-excluding TraCI vehicle edge-transition movement counter with explicit `SIMULATED` provenance.
- Prevented field-calibration evaluation from accepting caller-supplied simulated counts; it now consumes completed local movement-counter output only.
- Enforced mapping eligibility, interval consistency, network identity, and calibration/holdout separation.
- Removed a shadowed legacy calibration validator.
- Removed invented Pilot workspace KPIs and evidence claims.
- Removed unverified HBEFA-version assertions and corrected simulated-vs-direct documentation.

## Findings

### P0 fixed

- Draft Pilot workspace invented 24.8 s delay, 1,820 veh/h flow, 28% delay reduction, 17.8% CO₂ reduction, and “HIGH (85/100)” evidence. It now renders unavailable evidence and `—` until actual simulation evidence exists.
- No defensible link existed between field observations and SUMO movements. The new registry rejects unverified mappings and leaves the production registry empty until surveyed mappings are approved.

### P1 open

- Deployment configuration is not a verified SUMO-capable production environment. The Vercel configuration does not provide SUMO binaries or `SUMO_HOME`; no deployment credentials or infrastructure were in scope.
- Full pytest execution is currently unbounded/slow. Two exact pytest processes remained CPU-active after several minutes and were stopped. This is not a passing full-suite result.

### P2 open

- Frontend production build emits a >500 kB JavaScript chunk advisory.
- The repository still contains substantial historical and duplicate-era code outside the removed calibration validator; further consolidation should follow field validation, not precede it.

### P3

- Add CI timeouts and split slow SUMO integration tests from fast unit tests.

## Three-policy verification

- FLOW: mobility/environment/accessibility weights `0.80/0.10/0.10`.
- ECO: `0.15/0.75/0.10`.
- BALANCED: `0.45/0.35/0.20`.

All use the same candidate evidence set and baseline-relative direction-aware normalization. Constraints invalidate materially harmful candidates. `backend/test_policy_engine.py` demonstrates a traffic-maximizing candidate winning FLOW while an eco-focused candidate wins ECO; winners are not artificially forced.

## Calibration readiness

The status remains `UNCALIBRATED`. No field counts were fabricated or imported. The schema requires timestamp, intersection, approach, movement, interval, count, vehicle class, source, quality, and notes. `VALIDATED` requires a distinct `VALIDATION_HOLDOUT` dataset. Metrics include MAE, RMSE, MAPE, bias, Pearson correlation, and GEH; configured acceptance criteria are not represented as external standards.

## Verification record

- `backend/test_mapping_registry.py` + `backend/test_movement_counter.py`: **5 passed**.
- `backend/test_policy_engine.py`: **7 passed**.
- Earlier focused calibration/API selection: **16 passed, 1 warning** (Starlette TestClient deprecation).
- A later broader focused invocation collected 35 tests but did not provide a reliable final summary before it was bounded; do not treat it as passed.
- `npm run build`: **passed** (94 modules; existing chunk-size advisory).
- Focused ESLint on touched frontend files: **passed**.
- Browser check against localhost production preview: dashboard and Pilot workspace loaded; no browser console errors; fabricated Pilot KPIs were absent.

## Next milestone

Conduct a municipal field-validation pilot: survey/approve real movement mappings, collect separate calibration and holdout turning counts, run alignment and GEH/statistical evaluation, and only then advance toward `PARTIALLY_CALIBRATED`, `CALIBRATED`, and `VALIDATED`.

## Conference blocker correction addendum

- Production movement-mapping coverage remains exactly zero. Mappings now require an explicit verification-state transition and exact connection topology including the `via` lane, direction, TLS identity, and configuration hash. The TraCI counter records an `incoming → via → outgoing` chain after warm-up rather than edge totals.
- Field imports now require a field campaign, a comparable simulation campaign, and a measurement-window identifier. Calibration rejects mismatched network/configuration/mapping provenance, passenger-class mismatches, and calibration/holdout content, campaign, or observation-window overlap.
- Case Study navigation is artifact-only. `backend/data/canonical_experiment_artifact.json` was generated deliberately from 45 SUMO executions: 3 demand levels × (baseline + 4 implemented interventions) × 3 seeds. The checked snapshot contains 36 candidate evaluations and a verified result hash. Regeneration requires the explicit API confirmation `REGENERATE_CANONICAL_ARTIFACT`.
- In the generated 1.0× evidence, FLOW, ECO, and BALANCED all select `school_zone_slowdown_0s_safety` (presented as “Eligible-lane speed calming (20 km/h)”), with a modeled sampled-waiting value changing from 4.01 s to 3.1733 s. This shared winner is not forced; `test_policy_engine.py` separately demonstrates different FLOW and ECO winners on one shared evidence set when a real trade-off exists.
- Final focused verification: 44 integrity tests passed; 21 API tests passed (three package deprecation warnings); 14 spatial/environment/experiment/pilot tests passed; frontend production build passed with a >500 kB chunk advisory; local browser smoke test opened Case Study #001 from the saved artifact with no console errors.
- The unrestricted full `pytest -q` invocation was bounded and stopped after 37 progress markers without a terminal result while a SUMO child remained active. It must not be reported as passed. Split or mark the long-running live-SUMO scripts before relying on a one-command conference CI gate.
