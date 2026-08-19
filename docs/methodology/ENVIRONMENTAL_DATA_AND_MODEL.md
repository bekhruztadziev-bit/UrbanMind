# Environmental Data & Model Methodology

## Overview
UrbanMind integrates observed macro-scale environmental data with micro-scale emission simulations to provide a holistic view of the urban neighborhood. This document outlines the methodology for data collection, validation, freshness thresholds, and emission simulation.

## Real-World Observation Data
We use WAQI (World Air Quality Index project) as our primary provider to source real-time monitoring data from Uzhydromet stations in Tashkent.

### Data Sources
1. **Primary**: WAQI API (`api.waqi.info`), aggregating data from official Uzhydromet stations (e.g. Chilanzar #14722, US Embassy #8767, etc.).
2. **Secondary (Optional)**: IQAir (`api.airvisual.com`), providing backup city-level data.

### Known Stations
| Station ID | Name | Coordinates | Source |
|---|---|---|---|
| uzhydromet_chilanzar | Chilanzar | [41.2856, 69.2128] | Uzhydromet via WAQI |
| uzhydromet_center | Amir Temur | [41.3111, 69.2797] | Uzhydromet via WAQI |
| uzhydromet_sergeli | Sergeli | [41.2275, 69.2199] | Uzhydromet via WAQI |
| uzhydromet_olmazor | Olmazor | [41.3377, 69.2150] | Uzhydromet via WAQI |
| uzhydromet_yakkasaray | Yakkasaray | [41.2887, 69.2864] | Uzhydromet via WAQI |

### Freshness & Data Quality
Data quality is strictly categorized based on the timestamp of the observation:
* **LIVE**: Data is less than 30 minutes old.
* **RECENT**: Data is between 30 minutes and 3 hours old.
* **STALE**: Data is between 3 hours and 24 hours old.
* **UNAVAILABLE**: Data is older than 24 hours or the API is unreachable.

### Data Provenance & Safety
* **No Fabricated Data**: If an API request fails or the cache expires, UrbanMind falls back to `UNAVAILABLE` rather than generating artificial data or maintaining stale data indefinitely.
* **Observed vs Simulated**: Ambient air quality metrics (PM2.5, PM10, Temperature, AQI) are clearly labeled as "Observed" to prevent conflation with the localized simulation results.

## Emission Simulation Model
UrbanMind utilizes SUMO's native Handbook Emission Factors for Road Transport (HBEFA) version 3/4 continuous models for estimating vehicular emissions based on acceleration, speed, and vehicle class.

### TraCI Collection
Emissions are accumulated per-vehicle per-step during the measurement window via TraCI:
* `traci.vehicle.getCO2Emission(vehID)` (mg/s)
* `traci.vehicle.getNOxEmission(vehID)` (mg/s)
* `traci.vehicle.getPMxEmission(vehID)` (mg/s)
* `traci.vehicle.getFuelConsumption(vehID)` (mg/s)

### Aggregation and Conversion
At the end of the simulation, the total accumulated emissions (in milligrams) are converted into standard units:
* `sumo_co2_kg`: Total CO₂ in kilograms (mg / 1,000,000)
* `sumo_nox_g`: Total NOx in grams (mg / 1,000)

These metrics are explicitly badged as **SIMULATED (SUMO)** in the frontend UI.

### Heuristic Estimates (Legacy)
For backward compatibility or scenarios where SUMO emissions fail to report, UrbanMind retains the following heuristic estimation fallback, which is clearly badged as **ESTIMATED (Heuristic)**:
* `co2_kg = (max_vehicle_count * 0.62) + (average_waiting_seconds * 0.95)`
* `nox_g = (max_vehicle_count * 0.08) + (average_waiting_seconds * 0.12)`

## Reproducibility
* Local interventions directly affect the microscopic flow profile, which accurately triggers changes in SUMO's continuous emission model, allowing reproducible A/B comparisons of signal timing impacts on local tailpipe emissions.
