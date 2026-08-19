# UrbanMind Interventions Methodology

This document outlines the canonical, simulation-backed interventions modeled in UrbanMind v2. It defines what each intervention represents, how it is implemented in SUMO, and what assumptions and limitations apply.

## 1. School-zone speed calming (`school_zone_slowdown`)

### Urban interpretation
This intervention represents the implementation of traffic calming measures (e.g., speed bumps, lowered speed limits, tightened physical geometry) in residential or school-adjacent areas to improve safety and active mobility.

### SUMO representation
During the simulation initialization, TraCI traverses the entire road network and identifies local residential and collector lanes with existing maximum speed limits between 21 km/h (6.0 m/s) and 50 km/h (14.0 m/s). It overrides these limits, reducing the maximum permissible speed on these lanes to 20 km/h (5.5 m/s).

### Scope
Affects all vehicles traversing the identified residential lanes. Main arterials and high-speed corridors are unaffected.

### Assumptions
- We assume vehicles perfectly comply with the new speed limit (a common limitation of basic microscopic models).
- We assume the existing trips (demand) remain constant and do not immediately re-route to avoid the slower neighborhood, capturing the "Day 1" effect of the intervention.

### Limitations
- This is a *simulation-based estimate*, not a real-world field trial.
- The model does not currently simulate the exact physical implementation (e.g., the deceleration curve over a specific speed bump).
- It does not account for long-term behavioral changes (e.g., drivers shifting to different modes or changing their time of departure).

### Evaluation
The resulting effect is directly measured by observing the aggregate metrics calculated from the modified simulation run: total waiting time, average speed, estimated emissions, and other relevant factors.

---

## 2. Signal Timing Interventions (`extend_green`, `reduce_green`)

### Urban interpretation
Adjusting the local traffic light timing program to favor a congested corridor or reduce wait times at a specific junction.

### SUMO representation
Uses TraCI to directly modify the `PhaseDuration` of the targeted traffic light phase at initialization.

### Scope
Affects the specific intersection and phase specified in the intervention definition.

### Assumptions
- Assumes the modified signal program does not cause catastrophic gridlock elsewhere in the network that cannot be captured in the simulation duration.

### Limitations
- Simulation-based estimate.

### Evaluation
Measured directly via simulation delta compared to the identical-demand control run.
