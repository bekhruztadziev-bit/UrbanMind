# URBANMIND MOTION SYSTEM (URBANMIND_MOTION_SYSTEM_006)

## 1. Executive Summary & Core Principle

**Core Principle:** *Motion explains what changed.*

UrbanMind is a professional neighborhood mobility intelligence and urban digital twin platform. All user-interface motion is designed as an analytical instrument: precise, restrained, spatial, and state-driven. No decorative or cartoonish animations are permitted.

Every animation answers one of the key analytical questions:
- **What just appeared?** (e.g., Staged dashboard hierarchy, candidate cards)
- **What changed?** (e.g., Smooth metric interpolation upon scenario recalculation)
- **What is currently active?** (e.g., Restrained expanding halo on selected intersection marker)
- **What is processing?** (e.g., SUMO simulation spinner, AI reasoning progress indicator)
- **What completed?** (e.g., Subtle highlight on newly simulated recommendation)

---

## 2. Centralized Motion Tokens (`frontend/src/utils/motion.js`)

All interface transitions derive from a unified, centralized set of motion tokens implemented via the **Web Animations API (WAAPI)**:

```javascript
export const MOTION = {
  instant: 120,          // Rapid micro-feedback (badges, focus)
  fast: 180,             // Exit transitions, button state changes
  normal: 280,           // Component entrance, card highlights
  emphasis: 420,         // Numerical value interpolation, panel reveals
  reveal: 520,           // Staged initial load phases
  staggerSmall: 45,      // Candidate cards, sidebar items
  staggerMedium: 70,     // AI analytical sections, matrix rows
  easeStandard: 'cubic-bezier(0.2, 0, 0, 1)',
  easeEmphasized: 'cubic-bezier(0.16, 1, 0.3, 1)',
  easeExit: 'cubic-bezier(0.4, 0, 1, 1)',
}
```

---

## 3. Component Motion Architecture

### 3.1 Initial Dashboard Load (Staged Reveal Hierarchy)
Rather than a single jarring fade, the initial dashboard mounts in 5 distinct hierarchical phases:
1. **Phase 1 (0ms):** Primary dashboard shell and navigation bar render.
2. **Phase 2 (60ms):** Map viewport fades and reveals with geometric corridor boundary.
3. **Phase 3 (140ms):** Live metrics grid reveals with animated numerical values.
4. **Phase 4 (220ms):** Recommendation panel and candidate intervention list stagger in.
5. **Phase 5 (300ms):** Environmental monitoring panel and contextual insights settle.

### 3.2 Map Spatial Motion (`MapView.jsx`)
- **Selected Marker Halo:** When an intersection is selected, an expanding ring (`markerSelectionHalo`) expands once (650ms, `cubic-bezier(0.16, 1, 0.3, 1)`) and calmly fades out, leaving the active marker cleanly highlighted.
- **No Global Pulsing:** Markers that are not active do not pulse, preventing visual noise.
- **Corridor Boundary:** Clean geometric polygon with static neon glow for optimal GIS readability.

### 3.3 Metric Animation (`MetricsGrid.jsx` & `useAnimatedNumber`)
- When simulation runs or scenarios change, metrics smoothly interpolate (`previous -> interpolated -> new`) over 420ms using an ease-out quartic curve.
- Numbers settle precisely on the backend float value without endless oscillation.
- Metric cards receive a subtle single-pulse highlight when values update.

### 3.4 Candidate / Intervention Reveal (`CandidateList.jsx`)
- When optimization completes, candidate cards stagger into view with 45ms offsets (`opacity: 0 -> 1, translateY: 8px -> 0`).
- Clicking a candidate card triggers a brief highlight and smoothly updates the map selection.

### 3.5 AI Analysis Reveal (`AIExplanation.jsx`)
- **Analyzing State:** Displays a restrained spinner with `"Generating AI corridor trade-off reasoning…"`.
- **Completion State:** Sequentially reveals the 4 analytical sections with 70ms stagger:
  1. *Strategic Assessment*
  2. *Corridor Findings & Signal Focus*
  3. *Projected Operational Impact*
  4. *Operational Caveats & Trade-offs*

### 3.6 Button Interactions & Focus States (`App.css`)
- **Hover:** Subtle 1px translation (`translateY(-1px)`) and background brightening.
- **Active / Pressed:** Immediate tactile compression (`transform: scale(0.98)`).
- **Focus-Visible:** Accessible 2px cyan outline (`outline: 2px solid var(--accent-primary)`).
- **Disabled:** Zero movement, `opacity: 0.5`, `cursor: not-allowed`.

### 3.7 Hero Intro Menu & Bilingual Language Switcher (`HeroIntro.jsx`)
- Entrance modal features smooth zoom-in entrance (`scale(0.92) -> scale(1)` over 400ms).
- Includes instant bilingual toggle (`🇷🇺 RU` / `🇬🇧 EN`) at the top of the modal with active state indicators.
- Quick navigation cards feature subtle 2px hover lifts with cyan glow.

---

## 4. Accessibility & Reduced Motion

The motion system strictly honors user accessibility settings:
- `isReducedMotion()` checks `window.matchMedia('(prefers-reduced-motion: reduce)')`.
- CSS `@media (prefers-reduced-motion: reduce)` resets all animation durations to `0.01ms` and disables transforms.
- State changes, numbers, and data remain immediately visible and 100% functional.

---

## 5. Verification Checklist & QA Results

| Motion System Component | Target Behavior | Result |
| :--- | :--- | :--- |
| **INITIAL LOAD MOTION** | Staged 5-phase hierarchical entrance (0–300ms) | **PASS** |
| **MAP INTERACTION MOTION** | Restrained single-pulse halo on selected intersection (650ms) | **PASS** |
| **SCENARIO TRANSITION** | Coordinated recalculation highlight and card update | **PASS** |
| **METRIC TRANSITION** | Smooth numerical interpolation via `useAnimatedNumber` | **PASS** |
| **CANDIDATE REVEAL** | Sequential 45ms staggered entrance for candidate cards | **PASS** |
| **SIMULATION STATE MOTION** | Clear READY → RUNNING → COMPLETE transition | **PASS** |
| **AI ANALYSIS REVEAL** | 4-part analytical section sequential stagger (70ms) | **PASS** |
| **BUTTON FEEDBACK** | Instant hover, scale(0.98) press, and focus ring | **PASS** |
| **HERO INTRO & LANG TOGGLE** | Smooth modal zoom, responsive RU/EN switcher | **PASS** |
| **REDUCED MOTION** | Zero motion under `prefers-reduced-motion` | **PASS** |
| **NO MOTION JANK** | 60fps WAAPI transforms and opacity only | **PASS** |
| **OVERALL MOTION SYSTEM** | Cohesive, professional analytical instrument | **PASS** |
