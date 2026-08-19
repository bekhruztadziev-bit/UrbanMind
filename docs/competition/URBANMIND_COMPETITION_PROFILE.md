# UrbanMind Competition Demo Profile

## Setup for Public Demonstrations

UrbanMind is designed to perform live, interactive simulation of urban mobility interventions. To ensure reliability, clarity, and scientific integrity during public presentations (e.g. ICTWEEK), the following competition profile should be observed.

### 1. Presentation Mode
- Before presenting, navigate to the Experiments tab and click **"Enter Presentation Mode"**.
- This hides the top navigation bar and broadens the view, directing audience focus purely to the simulation matrix and results.

### 2. Flagship Preset (The "Clear Win")
- Click **"Load Competition Demo Preset"** to configure the optimal demo state.
- **Traffic Levels**: `[0.8, 1.0, 1.2, 1.4]` (Demonstrating scale)
- **Simulation Profile**: `Standard Evaluation (900 steps)` (Dampens transient artifacts and establishes a stable control baseline)
- **Interventions Selected**:
  - `Extend main green phase (+5s)`
  - `Reduce competing phase (-5s)`
  - `School-zone speed calming`

### 3. Key Talking Points
- **Traffic Calming Effect**: Highlight the Traffic Calming intervention, especially at **1.4x demand**. Explain that in a dense grid with high demand, reducing raw speed prevents queue spillback and unblocks intersections, counter-intuitively improving total average wait times across the network.
- **Signal Timing Limitations**: Acknowledge that the +5s and -5s signal modifications yield mixed results. Explain that this reflects real-world complexities—adjusting a single intersection's timing often pushes the bottleneck to the next intersection unless the entire corridor is synchronized. This demonstrates UrbanMind's ability to reveal unintended consequences.
- **Simulation Fidelity**: Mention the 900-step Standard Evaluation profile. Explain that initial wait times are lower as the network fills, but a longer evaluation window accurately captures the steady-state reality of the network.

### 4. Technical Constraints
- The backend relies on SUMO via TraCI.
- Do not run concurrent experiments from multiple browser tabs on a single backend instance (TraCI is single-threaded).
- `Departure-based Wait` provides a strict per-vehicle diagnostic, but the primary metric presented is the UI's `Average observed waiting time (s)`, which aggregates active vehicle states across simulation steps.
