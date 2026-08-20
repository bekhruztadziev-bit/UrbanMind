# UrbanMind Technical Facts

A summary of the verified technical architecture and behavior of UrbanMind v3, for use in answering technical questions from judges or technical audiences.

## 1. Simulation Architecture
- **Engine**: Eclipse SUMO (Simulation of Urban MObility) v1.27.1.
- **Integration**: TraCI (Traffic Control Interface) in Python.
- **Network**: Based on OpenStreetMap data, imported using netconvert.
- **Demand Generation**: Randomized but deterministically seeded trips. Currently scales globally via a baseline demand multiplier (e.g. 1.2x = 20% more baseline traffic).

## 2. Measurement Metrics
- **Completed Trip Time Loss**: Measures the average time lost by vehicles that successfully reached their destination. This is the primary metric for long-term network efficiency.
- **Active Vehicle Time Loss**: Measures the current time loss of vehicles still in the network. This is the primary metric for real-time congestion.
- **Environmental Data**: Integrates live PM2.5, PM10, AQI, Temperature, and Humidity readings from Uzhydromet (via WAQI/AQICN) with fallback to IQAir.
- **Emissions**: Collects the active scenario's SUMO/TraCI tailpipe-emission outputs (mg/s per vehicle). These are modeled outputs; the repository does not verify or assert a particular HBEFA version.

## 3. Simulation Profiles (Duration)
- **Demo Burst (300 steps)**: Quick simulation run; its results remain simulated and may be transient.
- **Standard Evaluation (900 steps)**: Longer simulation run; it is not field validation.
- **Extended Evaluation (1800 steps)**: Longer diagnostic simulation; no real-world validation claim follows from it.

## 4. Why Traffic Calming Works Best
At high demand multipliers (1.2x to 1.4x), the Yakkabog district's tight grid experiences "queue spillback"—where vehicles waiting at one intersection back up into the previous intersection, blocking cross-traffic. 
Reducing speed limits (Traffic Calming) forces vehicles to arrive at downstream intersections more gradually. This creates larger headways, prevents the sudden gridlocks that cause spillback, and effectively "meters" the flow, leading to a counter-intuitive but mathematically verifiable reduction in total average time loss.

## 5. System Limitations
- Backend API (`/api/experiments/run`) blocks while SUMO is executing. Concurrent HTTP requests wait for the `_traci_lock`.
- Generative AI is used exclusively for *explaining* simulation phenomena and providing heuristics, not for running the simulation. If the AI provider is down, the system gracefully falls back to raw data presentation.
- Real-world environmental data depends on external APIs (WAQI/IQAir); gracefully displays 'UNAVAILABLE' without fabricating data if connections fail.
