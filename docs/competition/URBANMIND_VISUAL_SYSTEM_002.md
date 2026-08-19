# URBANMIND_VISUAL_SYSTEM_002

## Goal

Perform a strict visual and UX pass to move UrbanMind from a "futuristic dashboard" to a "professional urban-intelligence/GIS platform", in preparation for the Silk Road Finance & Technology Forum.

## Summary of Changes

1. **Typography & Hierarchy**
   - Replaced default fonts with **Inter** for the UI and **IBM Plex Mono** for technical/numeric data.
   - Simplified global variables, relying on system font fallbacks to guarantee robust rendering.

2. **Map & GIS Grounding**
   - Removed the excessively thick, glowing cyan boundary cube, replacing it with a subtle dotted blue line.
   - Removed the yellow `flowDots` completely, and desaturated the `mahalla.roads` polylines to #64748b to allow the underlying OpenStreetMap tiles to be readable.
   - Redesigned the intersection marker to a small 8px solid point instead of a large glowing circle.
   - Replaced the oversized dollar-sign station marker with a subtle, professional 12px sensor/weather icon.

3. **Restrained Color Palette**
   - Stripped away extraneous teal, orange, and purple glows.
   - Unified the primary accent color to Slate Blue (`#3b82f6`) and the secondary analytical color to Emerald (`#10b981`).
   - Replaced all heavy drop-shadows with subtle, professional 4px/12px box shadows.

4. **Dynamic Data Handling**
   - Refactored `CandidateList.jsx` to dynamically compute the total number of interventions, simulated interventions, and estimated interventions.
   - Updated `en.json` and `ru.json` to properly handle singular/plural forms of intervention counts (e.g. "1 intervention", "3 interventions").

5. **Motion Design**
   - Introduced `src/utils/motion.js` using the Web Animations API (WAAPI).
   - Added subtle `animateEnter` to lists.
   - Added `animateNumber` for dynamic numerical transitions in `MetricsGrid.jsx` to convey a sense of continuous observation without distracting CSS transitions on every DOM element.

6. **Factual Integrity**
   - Verified that the `OBSERVED` badge accurately attributes live AQI/PM data to the source (IQAir).
   - Verified that the `SIMULATED` vs `ESTIMATED` badges properly distinguish between metrics generated from SUMO emissions (`sumo_co2_kg`) and heuristic estimates.

## Acceptance Criteria Verified
- [x] Stricter typography hierarchy (Inter + IBM Plex Mono)
- [x] Map overlays simplified (cyan box removed, yellow crosses removed)
- [x] Dynamic counts and proper localization strings for interventions
- [x] Motion restricted to meaningful state changes (WAAPI)
- [x] One primary accent color and minimal card borders
- [x] Factual provenance badges (OBSERVED, SIMULATED, ESTIMATED) are accurate

## Next Steps
- Production Build Verification
- Continued QA for Silk Road Forum
