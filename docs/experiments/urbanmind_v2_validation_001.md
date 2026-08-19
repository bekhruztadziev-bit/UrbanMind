# UrbanMind v2 Validation Experiment 001

## Research question
> **How does the effectiveness of the three simulation-backed UrbanMind interventions change as traffic demand increases?**
> Which intervention performs best at different traffic-demand levels, and does the relative effectiveness of each intervention remain stable as demand increases?

This is a **deterministic comparative simulation analysis**, not a statistically powered field experiment.

## Experimental design
- **Traffic levels**: 0.8×, 1.0×, 1.2×, 1.4×
- **Interventions**: Signal +5s, Signal -5s, Traffic-calming speed restriction
- **Duration**: 300 steps
- **Controls**: Same-demand baseline for each level
- **Seed/configuration**: Deterministic SUMO standard configuration

## Intervention definitions
- **Signal +5s**: Extends the green phase duration of the target intersection by 5 seconds using TraCI.
- **Signal -5s**: Reduces the green phase duration of the target intersection by 5 seconds using TraCI.
- **Traffic-calming speed restriction**: A simulated safety measure. At runtime, TraCI selects residential lanes with limits between 21 and 50 km/h and overrides them to 20 km/h (5.5 m/s). It does not explicitly model new pedestrian demand or individual speed bumps.

## Results

### Average observed waiting time (s)
*(Note: Current metric is step-wise aggregated across active vehicles rather than strict per-vehicle departure delay)*
| Demand | Intervention | Control | Intervention | Δ | % Δ |
| ------ | ------------ | ------: | -----------: | -: | --: |
| 0.8× | Signal +5s | 6.91 | 6.97 | 0.06 | 0.87% |
| 0.8× | Signal -5s | 6.91 | 6.87 | -0.04 | -0.58% |
| 0.8× | Traffic-calming speed restriction | 6.91 | 6.55 | -0.36 | -5.21% |
| 1.0× | Signal +5s | 7.02 | 7.07 | 0.05 | 0.71% |
| 1.0× | Signal -5s | 7.02 | 6.84 | -0.18 | -2.56% |
| 1.0× | Traffic-calming speed restriction | 7.02 | 7.1 | 0.08 | 1.14% |
| 1.2× | Signal +5s | 8.04 | 7.24 | -0.8 | -9.95% |
| 1.2× | Signal -5s | 8.04 | 6.71 | -1.33 | -16.54% |
| 1.2× | Traffic-calming speed restriction | 8.04 | 7.16 | -0.88 | -10.95% |
| 1.4× | Signal +5s | 7.06 | 7.28 | 0.22 | 3.12% |
| 1.4× | Signal -5s | 7.06 | 7.24 | 0.18 | 2.55% |
| 1.4× | Traffic-calming speed restriction | 7.06 | 6.5 | -0.56 | -7.93% |


### Average speed (km/h)
| Demand | Intervention | Control | Intervention | Δ | % Δ |
| ------ | ------------ | ------: | -----------: | -: | --: |
| 0.8× | Signal +5s | 40.19 | 39.98 | -0.21 | -0.52% |
| 0.8× | Signal -5s | 40.19 | 39.98 | -0.21 | -0.52% |
| 0.8× | Traffic-calming speed restriction | 40.19 | 36.24 | -3.95 | -9.83% |
| 1.0× | Signal +5s | 40.68 | 40.33 | -0.35 | -0.86% |
| 1.0× | Signal -5s | 40.68 | 40.76 | 0.08 | 0.2% |
| 1.0× | Traffic-calming speed restriction | 40.68 | 36.37 | -4.31 | -10.59% |
| 1.2× | Signal +5s | 39.49 | 40.05 | 0.56 | 1.42% |
| 1.2× | Signal -5s | 39.49 | 40.53 | 1.04 | 2.63% |
| 1.2× | Traffic-calming speed restriction | 39.49 | 36.23 | -3.26 | -8.26% |
| 1.4× | Signal +5s | 40.18 | 40.04 | -0.14 | -0.35% |
| 1.4× | Signal -5s | 40.18 | 39.93 | -0.25 | -0.62% |
| 1.4× | Traffic-calming speed restriction | 40.18 | 36.09 | -4.09 | -10.18% |


### Peak vehicles
| Demand | Intervention | Control | Intervention | Δ | % Δ |
| ------ | ------------ | ------: | -----------: | -: | --: |
| 0.8× | Signal +5s | 71 | 73 | 2.0 | 2.82% |
| 0.8× | Signal -5s | 71 | 73 | 2.0 | 2.82% |
| 0.8× | Traffic-calming speed restriction | 71 | 78 | 7.0 | 9.86% |
| 1.0× | Signal +5s | 86 | 88 | 2.0 | 2.33% |
| 1.0× | Signal -5s | 86 | 87 | 1.0 | 1.16% |
| 1.0× | Traffic-calming speed restriction | 86 | 94 | 8.0 | 9.3% |
| 1.2× | Signal +5s | 110 | 112 | 2.0 | 1.82% |
| 1.2× | Signal -5s | 110 | 108 | -2.0 | -1.82% |
| 1.2× | Traffic-calming speed restriction | 110 | 116 | 6.0 | 5.45% |
| 1.4× | Signal +5s | 122 | 126 | 4.0 | 3.28% |
| 1.4× | Signal -5s | 122 | 126 | 4.0 | 3.28% |
| 1.4× | Traffic-calming speed restriction | 122 | 131 | 9.0 | 7.38% |


### CO₂ (kg)
| Demand | Intervention | Control | Intervention | Δ | % Δ |
| ------ | ------------ | ------: | -----------: | -: | --: |
| 0.8× | Signal +5s | 50.58 | 51.88 | 1.3 | 2.57% |
| 0.8× | Signal -5s | 50.58 | 51.78 | 1.2 | 2.37% |
| 0.8× | Traffic-calming speed restriction | 50.58 | 54.59 | 4.01 | 7.93% |
| 1.0× | Signal +5s | 59.99 | 61.28 | 1.29 | 2.15% |
| 1.0× | Signal -5s | 59.99 | 60.44 | 0.45 | 0.75% |
| 1.0× | Traffic-calming speed restriction | 59.99 | 65.03 | 5.04 | 8.4% |
| 1.2× | Signal +5s | 75.84 | 76.32 | 0.48 | 0.63% |
| 1.2× | Signal -5s | 75.84 | 73.34 | -2.5 | -3.3% |
| 1.2× | Traffic-calming speed restriction | 75.84 | 78.73 | 2.89 | 3.81% |
| 1.4× | Signal +5s | 82.35 | 85.03 | 2.68 | 3.25% |
| 1.4× | Signal -5s | 82.35 | 84.99 | 2.64 | 3.21% |
| 1.4× | Traffic-calming speed restriction | 82.35 | 87.39 | 5.04 | 6.12% |


### NOₓ (g)
| Demand | Intervention | Control | Intervention | Δ | % Δ |
| ------ | ------------ | ------: | -----------: | -: | --: |
| 0.8× | Signal +5s | 25.33 | 25.98 | 0.65 | 2.57% |
| 0.8× | Signal -5s | 25.33 | 25.93 | 0.6 | 2.37% |
| 0.8× | Traffic-calming speed restriction | 25.33 | 27.33 | 2.0 | 7.9% |
| 1.0× | Signal +5s | 30.03 | 30.68 | 0.65 | 2.16% |
| 1.0× | Signal -5s | 30.03 | 30.25 | 0.22 | 0.73% |
| 1.0× | Traffic-calming speed restriction | 30.03 | 32.55 | 2.52 | 8.39% |
| 1.2× | Signal +5s | 37.96 | 38.2 | 0.24 | 0.63% |
| 1.2× | Signal -5s | 37.96 | 36.7 | -1.26 | -3.32% |
| 1.2× | Traffic-calming speed restriction | 37.96 | 39.4 | 1.44 | 3.79% |
| 1.4× | Signal +5s | 41.21 | 42.55 | 1.34 | 3.25% |
| 1.4× | Signal -5s | 41.21 | 42.53 | 1.32 | 3.2% |
| 1.4× | Traffic-calming speed restriction | 41.21 | 43.73 | 2.52 | 6.12% |


### Noise (dB)
| Demand | Intervention | Control | Intervention | Δ | % Δ |
| ------ | ------------ | ------: | -----------: | -: | --: |
| 0.8× | Signal +5s | 56.84 | 56.88 | 0.04 | 0.07% |
| 0.8× | Signal -5s | 56.84 | 56.88 | 0.04 | 0.07% |
| 0.8× | Traffic-calming speed restriction | 56.84 | 57.54 | 0.7 | 1.23% |
| 1.0× | Signal +5s | 56.76 | 56.82 | 0.06 | 0.11% |
| 1.0× | Signal -5s | 56.76 | 56.74 | -0.02 | -0.04% |
| 1.0× | Traffic-calming speed restriction | 56.76 | 57.54 | 0.78 | 1.37% |
| 1.2× | Signal +5s | 57.01 | 56.88 | -0.13 | -0.23% |
| 1.2× | Signal -5s | 57.01 | 56.77 | -0.24 | -0.42% |
| 1.2× | Traffic-calming speed restriction | 57.01 | 57.57 | 0.56 | 0.98% |
| 1.4× | Signal +5s | 56.85 | 56.88 | 0.03 | 0.05% |
| 1.4× | Signal -5s | 56.85 | 56.9 | 0.05 | 0.09% |
| 1.4× | Traffic-calming speed restriction | 56.85 | 57.56 | 0.71 | 1.25% |


### Pedestrian delay (s)
| Demand | Intervention | Control | Intervention | Δ | % Δ |
| ------ | ------------ | ------: | -----------: | -: | --: |
| 0.8× | Signal +5s | 17.1 | 17.53 | 0.43 | 2.51% |
| 0.8× | Signal -5s | 17.1 | 17.48 | 0.38 | 2.22% |
| 0.8× | Traffic-calming speed restriction | 17.1 | 18.35 | 1.25 | 7.31% |
| 1.0× | Signal +5s | 20.15 | 20.57 | 0.42 | 2.08% |
| 1.0× | Signal -5s | 20.15 | 20.27 | 0.12 | 0.6% |
| 1.0× | Traffic-calming speed restriction | 20.15 | 21.78 | 1.63 | 8.09% |
| 1.2× | Signal +5s | 25.38 | 25.44 | 0.06 | 0.24% |
| 1.2× | Signal -5s | 25.38 | 24.42 | -0.96 | -3.78% |
| 1.2× | Traffic-calming speed restriction | 25.38 | 26.21 | 0.83 | 3.27% |
| 1.4× | Signal +5s | 27.37 | 28.26 | 0.89 | 3.25% |
| 1.4× | Signal -5s | 27.37 | 28.24 | 0.87 | 3.18% |
| 1.4× | Traffic-calming speed restriction | 27.37 | 28.93 | 1.56 | 5.7% |


### Accessibility score
| Demand | Intervention | Control | Intervention | Δ | % Δ |
| ------ | ------------ | ------: | -----------: | -: | --: |
| 0.8× | Signal +5s | 88.67 | 88.56 | -0.11 | -0.12% |
| 0.8× | Signal -5s | 88.67 | 88.62 | -0.05 | -0.06% |
| 0.8× | Traffic-calming speed restriction | 88.67 | 87.37 | -1.3 | -1.47% |
| 1.0× | Signal +5s | 88.8 | 88.64 | -0.16 | -0.18% |
| 1.0× | Signal -5s | 88.8 | 88.93 | 0.13 | 0.15% |
| 1.0× | Traffic-calming speed restriction | 88.8 | 87.12 | -1.68 | -1.89% |
| 1.2× | Signal +5s | 87.78 | 88.43 | 0.65 | 0.74% |
| 1.2× | Signal -5s | 87.78 | 88.91 | 1.13 | 1.29% |
| 1.2× | Traffic-calming speed restriction | 87.78 | 87.03 | -0.75 | -0.85% |
| 1.4× | Signal +5s | 88.59 | 88.42 | -0.17 | -0.19% |
| 1.4× | Signal -5s | 88.59 | 88.39 | -0.2 | -0.23% |
| 1.4× | Traffic-calming speed restriction | 88.59 | 87.34 | -1.25 | -1.41% |


## Primary analysis (Average observed waiting time)
Average observed waiting time is the primary measure of effectiveness. Lower is better (negative Δ is effective).

## Robustness summary
**Signal +5s**
Effective at: 1 / 4 demand levels
**Signal -5s**
Effective at: 3 / 4 demand levels
**Traffic-calming speed restriction**
Effective at: 3 / 4 demand levels


## Demand-response analysis
**Signal +5s**: Wait time % changes across demand (0.8x -> 1.4x): [0.87, 0.71, -9.95, 3.12]

**Signal -5s**: Wait time % changes across demand (0.8x -> 1.4x): [-0.58, -2.56, -16.54, 2.55]

**Traffic-calming speed restriction**: Wait time % changes across demand (0.8x -> 1.4x): [-5.21, 1.14, -10.95, -7.93]

## Reproducibility information
- **Experiment ID**: 04371F7F
- **Date/Time**: 2026-08-18T18:00:52.507504+00:00
- **Duration**: 300 steps
- **Determinism Verified**: YES
- **Runtime**: 135.02s
- **SUMO Version**: 1.27.1
- **Canonical Scenario**: `mahalla-scenario`


## Limitations
- **SUMO model vs reality**: Vehicles perfectly comply; does not model complex behavioral responses.
- **Deterministic single-seed experiment**: Results represent a single simulation path, not a statistically robust distribution.
- **Absence of explicit pedestrian demand**: Cannot natively test active mobility effects.
- **Absence of bus/parking behavior**: Missing transit mapping limits evaluating multi-modal shifts.
- **Traffic-demand scaling assumptions**: Uniform scaling multiplier does not perfectly reflect real peak-hour directional flow shifts.


## Future experimental improvements
- Multiple seeds and repeated trials for statistical inference.
- Longer simulation horizons (e.g., full 24-hour profiles).
- Calibrated emission models using localized vehicle fleets.
- Richer demand data integrating transit and pedestrians.
- Real-world field validation to anchor simulation estimates.
