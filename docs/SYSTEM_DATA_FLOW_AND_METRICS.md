# UrbanMind — System Architecture, Data Flow & Research-Grade Simulation

This document establishes the **Data Integrity, Green Wave Validation, and Research-Grade Simulation Architecture** for UrbanMind. It outlines how every metric is defined, sourced, calculated, and visualized across the digital twin platform.

---

## 1. Metric Semantics & Provenance Matrix

Every metric displayed in UrbanMind is explicitly classified with verified provenance:

| Metric | Unit | Provenance | Raw Source | Calculation & Aggregation | Edge Cases & Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Average Delay** | $\text{s}$ | `SIMULATED` | TraCI `getAccumulatedWaitingTime` | Sum of waiting time ($v < 0.1\text{ m/s}$) for completed and active trips divided by sample count | Active vehicles are censored at boundary step |
| **Average Travel Time** | $\text{s}$ | `SIMULATED` | TraCI Departure & Arrival times | $t_{\text{arrival}} - t_{\text{departure}}$ across all vehicles completing trips | Vehicles not completing trip are excluded |
| **Queue Length** | $\text{m}$ | `SIMULATED` | TraCI `getLastStepHaltingNumber` | $\sum \text{halting vehicles} \times 7.5\text{ m}$ average vehicle spatial headway | Spatially aggregated across all corridor approach lanes |
| **Stops per Vehicle** | $\text{stops}$ | `SIMULATED` | TraCI `getSpeed` | Count of deceleration transitions ($v > 0.5\text{ m/s} \to v < 0.1\text{ m/s}$) divided by fleet size | Creep flow ($<0.5\text{ m/s}$) may register as continuous stop |
| **Throughput** | $\text{veh/h}$ | `SIMULATED` | TraCI `getArrivedIDList` | $(N_{\text{completed}} / t_{\text{measurement\_hours}})$ | Scaled to 1-hour equivalent window |
| **Average Speed** | $\text{km/h}$ | `SIMULATED` | TraCI `getSpeed` | $(\sum v_i / N_{\text{samples}}) \times 3.6$ | Arithmetic mean of instantaneous step velocities |
| **$\text{CO}_2$ Emissions** | $\text{kg}$ | `SIMULATED` | Configured SUMO/TraCI emission model | Accumulated $\text{CO}_2$ from TraCI `getCO2Emission` ($mg \to kg$) | Scenario emission class/version is not yet verified |
| **$\text{NO}_x$ Emissions** | $\text{g}$ | `SIMULATED` | Configured SUMO/TraCI emission model | Accumulated $\text{NO}_x$ from TraCI `getNOxEmission` ($mg \to g$) | Scenario emission class/version is not yet verified |
| **Accessibility Score** | $\%$ | `ESTIMATED` | Multi-Objective Urban Formula | $\max(0, \min(100, 100 - 0.55 \cdot \text{Wait} - 0.38 \cdot (60 - \text{Speed})))$ | Deterministic planning indicator, not physical sensor |
| **Air Quality ($\text{PM}_{2.5}$)** | $\mu g/\text{m}^3$ | `OBSERVED` | WAQI / Uzhydromet Stations | Direct telemetry from physical monitoring stations in Tashkent | Subject to API uptime and sensor reporting interval |

---

## 2. Green-Wave Corridor Coordination Methodology

Green Wave coordination is not an active canonical candidate until a field-verified signal sequence and corridor geometry are supplied. The repository must not infer a progression order from display labels or opaque network identifiers.

### Mathematical Formulation
Given corridor signal sequence $S = [s_1, s_2, \dots, s_n]$ with cumulative distances $d_i$ from corridor entry, target progression speed $v_{\text{target}} \approx 40\text{ km/h}$ ($11.11\text{ m/s}$), and cycle length $C = 90\text{ s}$:
$$\Delta \phi_i = \text{round}\left(\frac{d_i}{v_{\text{target}}}\right) \pmod C$$

Where geographic distance between nodes is computed via the Haversine formula:
$$d = 2 R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \text{lat}}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta \text{lon}}{2}\right)}\right)$$
with Earth radius $R = 6,371,000\text{ m}$.

### Robustness & Fault Tolerance
* If a signal ID is missing or invalid in the active network, it is safely skipped without halting simulation.
* Signal cycle constraints ($0 \le \Delta \phi_i < C$) are strictly enforced.

---

## 3. Multi-Seed Statistical Robustness

To distinguish genuine physical improvements from stochastic simulation noise, UrbanMind supports multi-seed simulation execution:
* **Seeds**: e.g., $S = [42, 101, 2024]$
* **Sample Mean**: $\bar{x} = \frac{1}{N}\sum x_i$
* **Sample Standard Deviation**: $s = \sqrt{\frac{1}{N-1}\sum (x_i - \bar{x})^2}$
* **95% Confidence Interval**: $\text{CI}_{95} = \left[\bar{x} - t_{0.975,N-1} \frac{s}{\sqrt{N}}, \bar{x} + t_{0.975,N-1} \frac{s}{\sqrt{N}}\right]$ for $N \ge 2$.

---

## 4. Multi-Objective Trade-off Analysis

UrbanMind evaluates interventions across multiple competing urban dimensions:
* **🟢 Improved**: Metrics where relative change exceeds $+2.0\%$ in the desired direction.
* **🟡 Trade-offs (Worsened)**: Metrics where relative change degrades by $> 2.0\%$.
* **⚪ Unchanged**: Metrics remaining within $\pm 2.0\%$ variance.

### Directional Semantics
* **Lower is better**: Average Delay, Travel Time, Queue Length, Stops per Vehicle, $\text{CO}_2$, $\text{NO}_x$, Pedestrian Delay.
* **Higher is better**: Average Speed, Throughput, Accessibility Score.

---

## 5. Policy Optimization Engine & Mathematical Normalization

Rather than treating a single universal metric as "best", UrbanMind utilizes a first-class **Optimization Policy Engine** to evaluate candidate interventions under explicit municipal policy objectives:

### Policy Profiles
1. **`FLOW` (Mobility Priority)**:
   - Weights: $\mathbf{w} = [w_{\text{mob}}=0.80, w_{\text{env}}=0.10, w_{\text{acc}}=0.10]$
   - Objective: Minimize corridor delays, travel times, stops, and queues; maximize throughput.
2. **`ECO` (Environmental Priority)**:
   - Weights: $\mathbf{w} = [w_{\text{mob}}=0.15, w_{\text{env}}=0.75, w_{\text{acc}}=0.10]$
   - Objective: Minimize simulated $\text{CO}_2$, $\text{NO}_x$, noise, and fuel consumption.
3. **`BALANCED` (Holistic Multi-Objective)**:
   - Weights: $\mathbf{w} = [w_{\text{mob}}=0.45, w_{\text{env}}=0.35, w_{\text{acc}}=0.20]$
   - Objective: Multi-objective compromise across corridor progression, emission abatement, and pedestrian accessibility.
4. **`CUSTOM` (Configurable Municipal Weights)**:
   - User-defined non-negative weights $w_{\text{mob}}, w_{\text{env}}, w_{\text{acc}}$ normalized such that $\sum w_i = 1.0$.

### Baseline-Relative Percentage Normalization
To prevent unit mismatch (combining seconds, kilograms, vehicles/hour, decibels), all raw metrics are converted into dimensionless relative improvement percentages:

* For **"Lower is better"** metrics ($m \in \{\text{delay}, \text{travel\_time}, \text{queue}, \text{stops}, \text{CO}_2, \text{NO}_x, \text{noise}, \text{ped\_delay}\}$):
  $$R_m = \frac{x_{m,\text{base}} - x_m}{x_{m,\text{base}}} \times 100$$
* For **"Higher is better"** metrics ($m \in \{\text{speed}, \text{throughput}, \text{accessibility}\}$):
  $$R_m = \frac{x_m - x_{m,\text{base}}}{x_{m,\text{base}}} \times 100$$

### Component & Overall Policy Scoring
Component scores represent arithmetic averages of normalized improvements in each category:
$$S_{\text{mobility}} = \frac{1}{|M_{\text{mob}}|}\sum_{m \in M_{\text{mob}}} R_m, \quad S_{\text{env}} = \frac{1}{|M_{\text{env}}|}\sum_{m \in M_{\text{env}}} R_m, \quad S_{\text{acc}} = \frac{1}{|M_{\text{acc}}|}\sum_{m \in M_{\text{acc}}} R_m$$

The overall policy composite score is:
$$S_{\text{policy}} = w_{\text{mob}} \cdot S_{\text{mob}} + w_{\text{env}} \cdot S_{\text{env}} + w_{\text{acc}} \cdot S_{\text{acc}}$$

### Constraint Enforcement
Candidates violating hard constraints (e.g., maximum allowable delay increase $> 20\%$) are marked as `is_valid = False` and receive a heavy ranking penalty ($-1000.0$) to guarantee they are never recommended over compliant strategies.

---

## 6. Distinction: Simulation Models vs. Physical Sensor Telemetry

> [!IMPORTANT]
> **Scientific Modeling Notice**:
> * **Configured SUMO/TraCI emissions** represent microscopic model estimates based on simulated vehicle speed-acceleration profiles; no particular HBEFA version is asserted without a verified scenario configuration.
> * **WAQI / Uzhydromet readings** represent physical air quality sensor measurements.
> * The platform does not conflate model outputs with empirical ground truth.

---

## 7. Developer & Execution Guide

### Installation & Run Commands

#### 1. Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Configure SUMO_HOME (example Windows path)
$env:SUMO_HOME = "C:\Users\user\Downloads\sumo-win64-1.27.1\sumo-1.27.1"

# Launch FastAPI Server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend
```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

#### 3. Automated Test Suite
```powershell
cd backend
.\.venv\Scripts\pytest.exe test_policy_engine.py test_simulation.py test_green_wave_validation.py test_experiment.py test_ai_service.py -v
```
