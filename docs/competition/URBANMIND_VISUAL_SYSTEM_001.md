# URBANMIND_VISUAL_SYSTEM_001

## 1. Objective
This report details the implementation of UrbanMind's updated Visual System, focused on elevating the product for the **Silk Road Finance & Technology Forum**. The primary objective was to transition the application from a generic interface to a "smart-city operations center" dashboard that visually communicates precision, modern analytics, and a clear distinction between real-world observations and simulated interventions.

## 2. Core Aesthetic
The application now leverages a dark analytical theme to convey enterprise-grade reliability and high-tech urban intelligence.

- **Background:** `radial-gradient(circle at 50% -10%, #1e293b 0%, #060e17 100%)` creates depth without being overly vibrant or distracting.
- **Card Panels:** Translucent (`rgba(13, 21, 35, 0.75)`) with an elevated blur (`backdrop-filter: blur(12px)`). This creates a layered structure that lets the map peek through subtly without sacrificing readability.
- **Typography:** Uses a crisp monospace font for data values (`font-family: monospace`) to align with the analytical look.
- **Layout:** The layout has been shifted to a **map-first approach**. The map now occupies 60-70% of the viewport on wide screens (`grid-template-columns: minmax(0, 6.5fr) minmax(320px, 3.5fr)`). This emphasizes that all decisions are grounded in real geography.

## 3. Data Provenance & Integrity
A central requirement was ensuring that users are never misled about the nature of the data. 

- **OBSERVED:** Environmental data pulled from real sensors (e.g., Uzhydromet via WAQI) is tagged with a crisp teal `OBSERVED` badge (`rgba(20, 184, 166, 0.12)`).
- **SIMULATED:** Data resulting directly from SUMO continuous traffic and emissions simulations (e.g., CO₂, NOx) is tagged with an indigo `SIMULATED` badge.
- **ESTIMATED:** Data calculated via heuristic or static formulas (when simulations are bypassed or not applicable) is tagged with an amber `ESTIMATED` badge.

These badges replace ambiguous "SIM" or "EST" text and provide a unified `provenance-badge` visual language across all panels (Environment Panel, Metrics Grid, Intervention Effect View, and Candidate List).

## 4. Map & Interaction Enhancements
- **Simulation Boundary:** The analysis zone is now explicitly highlighted using a technical neon-cyan bounding polygon (`#0ea5e9`), contrasting clearly with the dark map tiles and drawing immediate focus to the region of interest.
- **Station Markers:** Air quality monitoring stations are represented by distinct, high-tech square markers with a teal glow (`box-shadow: 0 0 12px var(--accent-teal-glow)`).
- **Intersection Markers:** Intersections (nodes) use a warm amber gradient that transitions to an active cyan gradient when selected.
- **Interactive States:** Buttons and interactive elements feature crisp glows (e.g., `box-shadow: 0 4px 12px var(--accent-blue-glow)`) and subtle translations (`transform: translateY(-1px)`) to provide tactile feedback without bouncy or cartoonish motion. 
- **Loading State:** Optimization actions now display a precise, spinning geometric SVG (`spin-icon`) to signify "Simulating..." or "Analyzing...", replacing static text.

## 5. Next Steps
- Verify visual contrast on large projector screens in preparation for the conference.
- Validate that backend metrics are successfully mapping to the updated provenance badges during active simulation.
- Ensure the map tiles load efficiently in offline/demo modes, if necessary.
