# EXPERIMENT_RUNNER_AUDIT.md

## Executive Verdict

**READY WITH CORRECTIONS**

---

## 1. Architecture Findings

The Multi-Scenario Experiment Runner is cleanly implemented and properly integrated into the UrbanMind system without regressing or modifying pre-existing features:

* **Layering and Orchestration:** `backend/app/services/simulation/experiment_runner.py` acts strictly as an orchestrator. It imports from `session.py` (for TraCI execution) and `metrics.py` (for metric calculations and heuristic formulas), avoiding any duplication of simulation logic.
* **Control Caching Lifecycle:** Control simulations are cached in an in-memory dictionary (`control_cache`) scoped strictly to the execution lifetime of `run_experiment()`. There is zero cache leakage across independent API calls.
* **Partial Failure Handling:** Individual condition failures (e.g. TraCI exceptions during specific intervention runs) are isolated via `try...except` blocks. Failed conditions record `status: "FAILED"` with the specific error message, while remaining conditions continue executing. The experiment summary accurately transitions to `PARTIALLY_COMPLETED`.
* **Data Contracts:** All payloads adhere to TypedDict and Pydantic schemas with `schema_version = 1`, ensuring structured exports and backward compatibility.
* **API Validation:** Endpoint `/api/experiments/run` validates input ranges (maximum 50 conditions, maximum 10 traffic multipliers, duration between 1 and 10,000 steps).

---

## 2. Evidence-Type Findings: Simulated vs Heuristic Interventions

### Canonical Registry Breakdown

| Intervention | Evaluation Mode | SUMO Actually Executed? | Heuristic Formula Used? | Included in Robustness Analysis? |
| :--- | :--- | :--- | :--- | :--- |
| **Extend main green phase (5s)** | `SIMULATED` | **YES** | **NO** | **YES** |
| **Extend main green phase (10s)** | `SIMULATED` | **YES** | **NO** | **YES** |
| **Reduce competing phase (-5s)** | `SIMULATED` | **YES** | **NO** | **YES** |
| **Bus-priority corridor** | `HEURISTIC` | **NO** | **YES** | **YES** |
| **Pedestrian priority window** | `HEURISTIC` | **NO** | **YES** | **YES** |
| **School-zone speed calming** | `HEURISTIC` | **NO** | **YES** | **YES** |
| **Short-stay curb rotation** | `HEURISTIC` | **NO** | **YES** | **YES** |

### Frontend UI Evaluation

1. **Results Matrix:** Displays evaluation mode badges (`SUMO` / `Heuristic`) for each row. The footnote explicitly states: *"% shown vs same-demand control. Green = improved, red = worse. Heuristic values are formula-based estimates."*
2. **Intervention Effect View:** Displays per-intervention bar charts across traffic demand levels with explicit `SUMO` vs `Heuristic` badges on each card and a disclaimer footnote.
3. **Robustness Summary:** Shows `SUMO` and `Heuristic` badges on each card, but aggregates all interventions into a single sorted list based on `effectiveCount`. Because heuristic formulas hardcode static reduction multipliers (e.g. `waiting * 0.76` for bus priority), heuristic interventions are mathematically guaranteed to achieve 100% effectiveness across all traffic demand levels, which can artificially position them above real SUMO simulations.
4. **History & Exports:** Both JSON and CSV exports explicitly output the `evaluation_mode` column for every condition.

### Conclusion on Evidence Separation

**B. clearly labeled but still aggregated**

The evidence types are clearly labeled with badges, footnotes, and metadata across all UI views and exports. However, in the Robustness Summary, they remain aggregated in a unified ranking where deterministic formula artifacts compete directly against dynamic SUMO physics.

---

## 3. Methodological Findings: Robustness Analysis

* **Criterion Implementation:** `effective = waiting_time_delta < 0` (i.e. scenario waiting time is less than same-demand control waiting time).
* **Completed Conditions Only:** Yes, verified. Conditions with `status !== "COMPLETED"` return `effective: null` and are excluded from `completedCount` and `effectiveCount`.
* **Heuristic Inclusions:** Yes, heuristic conditions are currently evaluated and scored.
* **Criterion Sufficiency:** The single-variable criterion (`waiting_time_delta < 0`) is a defensible initial indicator of congestion delay reduction, but it does not account for cross-corridor spillover, pedestrian delay increases, or emissions tradeoffs.
* **UI Transparency:** The UI displays the criterion prominently: *"Criterion: Effective = waiting time reduced vs same-demand control"*.

---

## 4. Experiment Metadata Audit

| Field | Audit Status | Description |
| :--- | :--- | :--- |
| `urbanmind_version` | **Inferred / Static** | Set statically to `"1.0.0"`. |
| `scenario_network` | **Known** | Path reference `"mahalla-scenario/osm.sumocfg"`. |
| `duration` | **Known & Accurate** | Integer steps recorded directly from request. |
| `traffic_levels` | **Known & Accurate** | Exact array of float multipliers evaluated. |
| `intervention_ids` | **Known & Accurate** | Canonical IDs recorded. |
| `random_seed` | **Unavailable / Recorded as `None`** | SUMO seed is not currently captured from the config or TraCI runtime. Correctly exported as `None`/empty rather than falsified. |
| `sumo_version` | **Unavailable / Recorded as `None`** | SUMO runtime version is not queried during execution. Correctly exported as `None`/empty rather than falsified. |

---

## 5. Control Caching Audit

* **Cache Key:** `(traffic_multiplier, duration)` tuple in python dictionary.
* **Scope & Isolation:** Instantiated as a local variable inside `run_experiment()`. It lives only during the synchronous thread execution of that specific experiment call. There is zero state leakage between distinct experiment requests.
* **Duration Sensitivity:** Duration is included in the cache key.
* **Demand Matching:** For $N$ interventions at traffic demand $1.2\times$, the baseline control simulation at $1.2\times$ runs exactly once and is reused across all $N$ candidate evaluations.
* **Numerical Invariance:** Confirmed that control caching produces bit-for-bit identical results to re-running control every iteration.

---

## 6. Cartesian-Product Correctness

* For $N$ traffic levels and $M$ interventions, the runner generates exactly $N \times M$ conditions.
* Condition IDs follow the deterministic format: `{experiment_id}_{traffic_multiplier}x_{intervention_id}`.
* The frontend builder preview (`N levels × M interventions = K conditions`) exactly reflects the backend condition matrix.
* Upper-bound safeguards: Warning at $>20$ conditions, hard rejection at $>50$ conditions.

---

## 7. Same-Demand Control Methodology

Every condition enforces strict same-demand comparison semantics:
$$\text{control} = (\text{demand}=T, \text{duration}=D, \text{intervention}=\text{None})$$
$$\text{scenario} = (\text{demand}=T, \text{duration}=D, \text{intervention}=I)$$
$$\Delta = \text{scenario} - \text{control}$$

This ensures that the delta isolates the true marginal impact of the intervention at traffic level $T$, rather than confounding intervention impact with demand escalation.

---

## 8. Reproducibility Findings

A live reproducibility test was executed on the local SUMO installation (`v1.27.1`):
* **Experiment Setup:** 2 traffic levels (`1.0×`, `1.2×`), 1 simulated intervention (`extend_green_5s_signal_timing`), duration = 50 steps.
* **Execution:** Experiment A and Experiment B run sequentially with real TraCI instances.
* **Result:** **100% Identical Output.**
  * `average_speed_kmh`: 41.82 km/h (A) == 41.82 km/h (B)
  * `average_waiting_seconds`: 1.94 s (A) == 1.94 s (B)
  * `max_vehicle_count`: 28 (A) == 28 (B)
  * `co2_kg`, `nox_g`, `noise_db`, `accessibility_score`: identical to 4 decimal places.

---

## 9. Export Findings

* **JSON Export:** Serializes full `ExperimentResult` containing experiment metadata, summary counts, metric provenance map, and all conditions with raw control, scenario, and percentage deltas.
* **CSV Export:** Outputs a tabular structure (1 row per condition) with 21 columns including `experiment_id`, `traffic_multiplier`, `intervention_label`, `evaluation_mode`, `status`, and complete control/scenario/delta metrics.
* **Auditability:** External researchers can immediately filter CSV rows by `evaluation_mode == "SIMULATED"` vs `"HEURISTIC"`.

---

## 10. Frontend Interpretation Audit

* **Labels & Badges:** Badges (`SUMO` / `Heuristic`) appear consistently across all views.
* **Potential Semantics Risks:** The phrase "Effective in X / Y demand conditions" in the Robustness Summary can lead a casual viewer to believe that a Heuristic intervention (which gets 4/4 due to fixed formula multiplication) is empirically superior to a SUMO-simulated intervention (which might get 3/4 due to real bottleneck dynamics).

---

## 11. Performance Findings

For an experiment with $N$ traffic levels, $S$ simulated interventions, and $H$ heuristic interventions:
* **SUMO Executions Required:** $N + (N \times S)$ runs.
* **Heuristic Execution Time:** $< 1\text{ ms}$ (pure in-memory float multiplication).
* **Representative Size (4 levels × 3 simulated + 4 heuristic = 28 conditions):**
  * Control simulations: 4 runs
  * Scenario simulations: $4 \times 3 = 12$ runs
  * Total SUMO executions: **16 runs** (reduced from 28 runs without control caching).
  * Execution time on local environment: $\approx 25\text{ seconds}$.
* **Worst-Case Load (50 conditions max cap):** Maximum 40 SUMO runs ($\approx 45\text{ seconds}$), well within reasonable desktop and web execution bounds.

---

## 12. Test and Build Verification

### Backend Automated Tests
Command: `pytest backend/test_simulation.py backend/test_api.py backend/test_experiment.py -v`

* **Collected:** 20 tests
* **Passed:** 20 tests
* **Failed:** 0 tests
* **Skipped:** 0 tests
* **Duration:** 69.87s

### Frontend Build
Command: `npm run build`

* **Status:** Clean production build (`vite v8.2.1`)
* **Modules Transformed:** 90 modules
* **Output:** `dist/index.html` (0.45 kB), `dist/assets/index.css` (23.55 kB), `dist/assets/index.js` (368.45 kB)
* **Errors / Warnings:** 0 errors

*Note: Frontend automated test runner is not configured in this project repository.*

---

## 13. Highest-Priority Corrections

1. **Partition Robustness Summary by Evidence Type:** Separate simulated and heuristic interventions into distinct sections or tabs in the Robustness Summary so that static formula multipliers cannot be misinterpreted as superior to empirical SUMO runs.
2. **Dynamic SUMO Version & Seed Introspection:** Query `traci.getVersion()` or CLI `-V` at runtime to populate `metadata.sumo_version`, and capture the random seed if specified.
3. **Scenario Parameter Support:** Expose the `scenario` parameter (`morning`, `midday`, `evening`) in `ExperimentRequest` instead of hardcoding `"midday"`.
4. **Multi-Objective Robustness Score:** Expand the single-dimensional `waiting_time_delta < 0` rule to optionally consider speed loss and pedestrian delay tradeoffs.
5. **Heuristic Banner in Robustness Card:** Add an explicit notice on heuristic cards indicating that 100% robustness is a property of the fixed formula adjustment.

---

## Research Readiness

### Exploratory Analysis
**YES** — Excellent for local planners exploring relative parameter impacts and visualizing corridor behavior under various demand levels.

### Controlled Simulation Experiments
**YES** — Methodologically sound same-demand control baseline, Cartesian-product generation, control caching, and bit-for-bit reproducible SUMO stepping.

### Publication-Level Quantitative Claims
**NO** — Not without isolating SIMULATED conditions exclusively, documenting the exact SUMO version / random seed, and replacing heuristic corridor estimates with dedicated microscopic network models.

---

## Final Verification Checklist

**Experiment Runner technically correct: YES**

**Simulated vs heuristic evidence adequately distinguished: YES**

**Same-demand control methodology correct: YES**

**Experiment reproducibility adequately documented: NO**

**Exports methodologically interpretable: YES**

**Ready for substantive feature development: YES**
