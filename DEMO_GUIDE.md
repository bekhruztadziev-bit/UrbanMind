# MahallaMind Demo Guide

## Product Statement

**MahallaMind** is a neighborhood mobility intelligence platform that combines an interactive digital twin with explainable traffic optimization to help local planners and stakeholders make informed decisions about corridor-level interventions.

The system compares realistic local signal timing, transit priority, pedestrian safety, and curb management strategies—then explains *why* one option is recommended instead of hiding the logic behind a black box.

---

## Demo Flow (7-10 minutes)

### 1. **Opening Context** (1 minute)
"This is a neighborhood in a Central Asian city. It has schools, clinics, a market, bus stops, and residential areas. Every day, residents navigate traffic through these six key intersections. Traffic congestion affects school runs, clinic visits, vendor access, and daily life."

*Show the map screen with the neighborhood highlighted and all facilities visible.*

### 2. **Current Conditions** (2 minutes)
- Click the **Analyze** button to fetch baseline metrics
- Point out the key metrics:
  - **Avg Speed**: ~18-22 km/h (typical for busy local corridors)
  - **Avg Waiting**: ~8-12 seconds per vehicle at signals
  - **CO2 & NOx**: Environmental impact from idling and stop-start traffic
  - **Accessibility**: Currently at ~85-90% (room for improvement in school and clinic access)

**Narrative**: "Right now, residents experience moderate delays and the neighborhood generates emissions. There's opportunity to improve without major construction—just smarter signal timing and priority adjustments."

### 3. **Exploring the Problem** (2 minutes)
- Hover over **School Junction** to show that two schools are near this intersection
- Explain: "This intersection is central to morning school runs and clinic visits. Students and staff face predictable 10-15 second waits."
- Show the three scenario buttons: **Morning, Midday, Evening**
  - Explain that morning peak (7-8am) has different characteristics than midday or evening
  - *Optional: Try a different scenario to show how patterns shift*

### 4. **Running Optimization** (2 minutes)
- Click **Optimize**
- Explain: "We're comparing 7 different local interventions against the baseline—from signal timing changes to bus priority and pedestrian safety zones."
- Wait for results to load (typically 30-60 seconds depending on SUMO backend)

### 5. **Reviewing Results** (2 minutes)
- Point to the **Recommended Intervention** card:
  - Note the score and improvement metrics
  - Highlight the delta values (waiting time change, speed change, etc.)

**Example narrative**: "The system recommends extending the green phase for the main direction by 10 seconds. This reduces average waiting from 10 seconds to 7 seconds—that's a 30% improvement. Speed improves slightly, emissions go down, and pedestrian crossing safety is maintained."

- Point to **Why This Choice?**:
  - Show the explanation text, which ties back to the neighborhood context:
    - "This intervention targets the main commercial hub where traffic is most congested"
    - "It balances delay reduction with environmental and safety outcomes"
  - Highlight the confidence level and expected impact

### 6. **Exploring Alternatives** (1 minute)
- Scroll through the **3 Intervention Options** cards
- Show how each has different tradeoffs:
  - Some prioritize speed, others prioritize emissions or pedestrian safety
  - Each is grounded in real neighborhood functions (schools, markets, clinics, bus routes)

**Narrative**: "All three are valid. The recommendation is based on a balanced scoring system, but stakeholders might weight outcomes differently. A school administrator might prefer the pedestrian-priority option; a market vendor might prefer curb-management improvements."

### 7. **Closing Context** (1 minute)
- Show the **MAHALLAMIND position** card:
  - Emphasize that this is *decision support*, not a mandate
  - The strongest choice is the one that improves the corridor while keeping the district legible, safe, and accessible
- Optional: Switch to **FAQ** page to show the deeper logic behind the model

---

## Key Talking Points

- **Not a black box**: Every recommendation is tied to specific metrics and neighborhood context
- **Neighborhood-grounded**: Facilities (schools, clinics, markets, transit) are named and considered
- **Multi-objective**: Balances delay, emissions, safety, and economic vitality instead of optimizing for just speed
- **Explainable**: Before/after metrics clearly show what residents can expect
- **Stakeholder-friendly**: Written for local planners, community leaders, and decision-makers—not just engineers

---

## Demo Troubleshooting

### Backend is offline or slow
- The app will show **offline preview mode** with fallback demo data
- Metrics will be estimated, not real simulation data
- Explain: "In production, this would connect to actual traffic sensors and SUMO simulation. For demo, we're showing the interface with representative data."

### SUMO not installed
- Backend will fail to run `/api/optimize` and `/api/metrics`
- Ensure `SUMO_HOME` environment variable is set before starting backend:
  ```bash
  set SUMO_HOME=C:/Users/user/Downloads/sumo-win64-1.27.1/sumo-1.27.1
  cd backend
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```

### Frontend shows blank map
- Check browser console (F12) for errors
- Ensure backend is running on `http://localhost:8000`
- Verify vite dev server is running: `npm run dev -- --host 0.0.0.0`

### Scenario switching has no effect
- Scenario modifiers apply to metrics estimation. Real SUMO simulation picks a representative baseline.
- After clicking **Analyze** or **Optimize**, try switching scenarios and re-running to see differences

---

## Demo Hardware Recommendations

- **Laptop/Desktop**: 2+ GB RAM, modern browser (Chrome, Firefox, Safari, Edge)
- **Display**: 1920×1080 or higher; the map needs space to breathe
- **Network**: Works on localhost; can be deployed to a local network if needed
- **Backend simulation**: Expect 30-60 second optimization runs; cache results if presenting multiple scenarios

---

## Deployment & Production Notes

See [DEPLOYMENT.md](DEPLOYMENT.md) for full setup, scaling, and production considerations.

---

## Post-Demo Discussion Questions

For stakeholders after the demo:

1. **Does this match your experience?** (Reality check against their local knowledge)
2. **Which metric matters most to you?** (Latency, emissions, safety, access, commerce)
3. **How confident would you be in testing this intervention locally?** (Feasibility discussion)
4. **What data would you want to see in a real deployment?** (Sensor network, real-time feedback)
5. **How could this integrate with your existing planning tools?** (Interop and workflow)

---

## License & Attribution

MahallaMind is a hackathon MVP. Map data is from OpenStreetMap and Leaflet. Traffic simulation uses SUMO (Simulation of Urban Mobility). Facility and intersection data are illustrative and represent a typical Central Asian neighborhood pattern.

---

*Last updated: 2026-08-15*
