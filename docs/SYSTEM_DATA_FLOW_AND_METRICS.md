# UrbanMind — System Architecture, Data Flow & Metrics Provenance

This document establishes the **Data Integrity & Traceability Layer** for UrbanMind, outlining how every metric is sourced, processed, and visualized across the digital twin platform.

---

## 1. Data Provenance & Integrity Layer

Every metric displayed in UrbanMind is explicitly tagged with a provenance class to guarantee scientific transparency:

| Provenance Tag | Source | Description | Example Metrics |
| :--- | :--- | :--- | :--- |
| **`DIRECT`** | SUMO TraCI / Simulation | Directly measured from microscopic physical vehicle trajectories | Speed, Delay, Travel Time, Queue Length, Stops/Veh |
| **`SIMULATED`** | SUMO HBEFA Model | Physical emission / energy models executed during simulation | CO₂ (kg), NOx (g), PMx (mg), Fuel (ml) |
| **`OBSERVED`** | WAQI / Uzhydromet API | Real-time sensor telemetry from physical stations | PM2.5, PM10, NO₂, AQI, Temperature, Humidity |
| **`ESTIMATED`** | Multi-Objective Formula | Deterministic mathematical formulas balancing multiple urban factors | Accessibility Score (%), Pedestrian Delay (s) |
| **`FALLBACK`** | Calibrated Reference | Used when SUMO or external APIs are unreachable (explicitly flagged) | Calibrated baseline for offline demonstrations |

```text
SOURCE (TraCI / WAQI) 
    ↓
PROCESSING (metrics.py / optimizer.py) 
    ↓
STRUCTURED METRIC ({ value, unit, source, provenance, confidence, is_simulated }) 
    ↓
UI (MetricsGrid, RecommendationPanel, MapView)
```

---

## 2. Traffic Flow & Microscopic Simulation Pipeline

UrbanMind interfaces directly with **Eclipse SUMO (Simulation of Urban MObility)** via **TraCI (Traffic Control Interface)**.

### Monitored Traffic Metrics
* **Average Delay ($s$)**: Total accumulated waiting time ($v < 0.1\text{ m/s}$) for completed and active trips.
* **Travel Time ($s$)**: Duration from vehicle departure on boundary edge to completion of trip across the corridor.
* **Queue Length ($m$)**: Halting vehicle count across corridor lanes multiplied by average vehicle spatial headway ($7.5\text{ m}$).
* **Stops per Vehicle**: Count of speed deceleration transitions ($v > 0.5\text{ m/s} \to v < 0.1\text{ m/s}$) divided by active fleet.
* **Throughput ($\text{veh/h}$)**: Normalized arrival rate of completed vehicles per hour of simulation window.
* **HBEFA Emissions**: Real-time vehicle-level calculation of $\text{CO}_2$, $\text{NO}_x$, $\text{PM}_x$, and Fuel Consumption.

---

## 3. Green-Wave Corridor Coordination Experiment

The primary corridor optimization scenario applies coordinated green wave progression across connected signals along the Tashkent Central Corridor (`cluster_1` through `cluster_6`):

### Mathematical Formulation
For progressive signal coordination at target speed $v_{\text{target}} \approx 40\text{ km/h}$ ($11.1\text{ m/s}$):
$$\Delta \phi_i = \frac{d_{i, i-1}}{v_{\text{target}}} \pmod C$$
where:
* $\Delta \phi_i$ = coordinated phase offset at intersection $i$
* $d_{i, i-1}$ = distance between intersection $i-1$ and $i$
* $C$ = cycle length

### Baseline vs. Optimized Comparison
Improvement percentages are calculated strictly from actual simulation outputs:
* **For reductions (Delay, Travel Time, Queue, Stops, Emissions)**:
  $$\text{Improvement } (\%) = \frac{\text{Baseline} - \text{Optimized}}{\text{Baseline}} \times 100$$
* **For increases (Speed, Throughput, Accessibility)**:
  $$\text{Improvement } (\%) = \frac{\text{Optimized} - \text{Baseline}}{\text{Baseline}} \times 100$$

---

## 4. Environmental Telemetry Integration

* **Primary Provider**: WAQI API aggregating official Uzhydromet monitoring stations in Tashkent (Chilanzar Station `@14722`, Amir Temur Square, Sergeli, Olmazor, Yakkasaray).
* **Data Quality States**:
  * `LIVE`: Telemetry timestamp $< 2\text{ hours}$ old.
  * `RECENT`: Telemetry timestamp between $2\text{ and }6\text{ hours}$ old.
  * `STALE`: Telemetry timestamp $> 6\text{ hours}$ old.
  * `UNAVAILABLE`: Station offline or network unreachable (no fake values fabricated).

---

## 5. Developer & Setup Guide

### Environment Requirements
* **Node.js**: v18+
* **Python**: 3.11+
* **Eclipse SUMO**: v1.20+ (with `SUMO_HOME` environment variable configured)

### Installation & Run Commands

#### 1. Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Set SUMO_HOME (example path on Windows)
$env:SUMO_HOME = "C:\Users\user\Downloads\sumo-win64-1.27.1\sumo-1.27.1"

# Run FastAPI Server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend
```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

#### 3. Automated Tests
```powershell
cd backend
.\.venv\Scripts\pytest.exe test_simulation.py test_experiment.py -v
```

### Environment Variables
| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `SUMO_HOME` | Root directory of Eclipse SUMO installation | `C:\sumo-1.27.1` |
| `WAQI_API_TOKEN` | API token for World Air Quality Index | Optional (falls back gracefully) |
| `GEMINI_API_KEY` | Google Gemini API key for contextual analysis | Optional (falls back gracefully) |
