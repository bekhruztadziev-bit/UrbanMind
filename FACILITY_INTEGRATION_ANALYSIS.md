# MahallaMind Scenario Logic & Facility Weighting Analysis

**Date**: 2026-08-15  
**Scope**: Analysis of neighborhood-grounded realism in scenario modifiers, facility integration, and intervention weighting

---

## 1. CURRENT SCENARIO MODIFIERS (`_scenario_modifier()` in sumo_runner.py)

### Implementation Overview
The system uses **3 time-of-day scenarios** with multipliers applied to baseline metrics:

```python
{
  "morning":  {"speed": 0.88, "waiting": 1.2, "vehicle": 1.18, "noise": 1.08, "access": 0.92},
  "evening":  {"speed": 0.9, "waiting": 1.15, "vehicle": 1.12, "noise": 1.04, "access": 0.95},
  "midday":   {"speed": 1.0, "waiting": 1.0, "vehicle": 1.0, "noise": 1.0, "access": 1.0}
}
```

### Current Adjustments

| Scenario | Speed | Waiting | Vehicles | Noise | Access |
|----------|-------|---------|----------|-------|--------|
| **Morning** | ↓12% | ↑20% | ↑18% | ↑8% | ↓8% |
| **Evening** | ↓10% | ↑15% | ↑12% | ↑4% | ↓5% |
| **Midday** | — | — | — | — | — |

### Analysis
✅ **Strengths:**
- Captures peak-hour congestion patterns (morning/evening)
- Accounts for increased emissions and noise during peaks
- Recognizes reduced accessibility during peak times

⚠️ **Gaps:**
- **No facility-dependent variability**: Morning speed reduction is uniform across the entire network; doesn't account for school dropoff zones or clinic access times being worse
- **Generic daily pattern**: No distinction between weekday/weekend, special events, or neighborhood-specific peak times
- **Missing micro-locality effects**: Rush hour is treated globally, not considering that school-adjacent corridors experience earlier peaks (7-8am) vs. commercial areas (8-9am)
- **Access reduction is blunt**: 8% morning access reduction doesn't differentiate between school-zone accessibility (should be worse) vs. market or administrative areas

---

## 2. FACILITY DEFINITIONS & CURRENT USAGE (mahalla_data.py)

### Facilities Defined

```python
FACILITIES = [
  {"id": "school_1", "type": "school", "name": "District School", "coords": [41.3186, 69.2698]},
  {"id": "clinic_1", "type": "clinic", "name": "Community Clinic", "coords": [41.3154, 69.2676]},
  {"id": "kindergarten_1", "type": "kindergarten", "name": "Kindergarten #4", "coords": [41.3171, 69.2648]},
  {"id": "bus_stop_1", "type": "bus_stop", "name": "Bus Stop East", "coords": [41.3191, 69.2661]},
  {"id": "park_1", "type": "park", "name": "Park", "coords": [41.3138, 69.2702]},
  {"id": "facility_1", "type": "administrative", "name": "Mahalla Office", "coords": [41.3147, 69.2641]},
  {"id": "facility_2", "type": "public", "name": "Community Center", "coords": [41.3198, 69.2709]},
  {"id": "market_1", "type": "market", "name": "Market Square", "coords": [41.3128, 69.2645]},
  {"id": "mosque_1", "type": "religious", "name": "Mosque Lane", "coords": [41.3213, 69.2727]},
]
```

### Current Usage in Code

📍 **Returned to frontend but NOT used for**:
- Scenario modifier adjustments
- Proximity-based intervention weighting
- Trip pattern generation
- Accessibility scoring by facility type
- Congestion hotspot prediction

### What This Means
✅ The mahalla_data.py provides rich, well-defined spatial context  
❌ But **scenario modifiers and intervention scoring ignore facility locations entirely**  
❌ The "school-zone slowdown" intervention is named for a facility, but uses **generic estimates**, not actual proximity to school_1

---

## 3. INTERVENTION CATEGORIZATION & WEIGHTING (optimize_interventions())

### Intervention Types & Estimates

```python
interventions = [
  # Signal timing (runs actual simulation)
  {"type": "extend_green", "category": "signal_timing", ...},
  
  # All others use _estimate_candidate_metrics() with adjustment multipliers:
  {"type": "bus_priority", "category": "transit", ...},
  {"type": "pedestrian_priority", "category": "active_mobility", ...},
  {"type": "school_zone_slowdown", "category": "safety", ...},
  {"type": "parking_turnover", "category": "curb_management", ...},
]
```

### Adjustment Multipliers

| Intervention Type | Speed | Waiting | CO2 | NOx | Noise | Pedestrian | Access |
|-------------------|-------|---------|-----|-----|-------|-----------|--------|
| **extend_green** | 1.12 | 0.80 | 0.90 | 0.90 | 0.96 | 1.08 | 1.08 |
| **reduce_green** | 0.97 | 1.12 | 1.08 | 1.09 | 1.04 | 1.12 | 0.92 |
| **bus_priority** | 1.18 | 0.76 | 0.82 | 0.80 | 0.88 | 0.90 | 1.14 |
| **pedestrian_priority** | 0.93 | 0.79 | 0.76 | 0.75 | 0.82 | 0.72 | 1.16 |
| **school_zone_slowdown** | 0.90 | 0.82 | 0.74 | 0.72 | 0.80 | 0.74 | 1.12 |
| **parking_turnover** | 0.96 | 0.84 | 0.79 | 0.77 | 0.86 | 0.85 | 1.10 |

### Scoring Function

```python
score = (waiting * 0.55) - (speed * 0.18) + (co2 * 0.22) + (pedestrian_delay * 0.1) - (access * 0.15)
# Lower score is better
# Primary weight: waiting time (55%), then emissions (22%)
# Rewards: speed (18%) and access (15%)
```

### Analysis

✅ **Strengths:**
- Multi-objective optimization (emissions, delay, access all weighted)
- Clear category labels (transit, safety, active_mobility, curb_management)
- All interventions tested against same metrics
- Pedestrian outcomes are explicitly modeled

⚠️ **Critical Gaps:**

1. **Intervention names suggest facility grounding, but location is ignored**
   - `school_zone_slowdown` uses same static multipliers whether the signal is 50m or 500m from school_1
   - No proximity check: `distance_to_facility(signal_id, "school")`
   - No time-based variation: school dropoff (7-8am) vs. regular morning (8-9am)

2. **"Transit" and "pedestrian_priority" are generic, not corridor-specific**
   - `bus_priority` doesn't check if the signal is near bus_stop_1 or on a designated route
   - `pedestrian_priority` doesn't differentiate between a residential street vs. a market square
   - Market Square (facility_1) should get higher pedestrian priority than a residential corridor

3. **Safety interventions lack facility context**
   - School zone slowdown uses fixed 0.90 speed multiplier
   - Doesn't adjust based on distance to school_1, kindergarten_1, or park_1
   - School at 41.3186, 69.2698; Clinic at 41.3154, 69.2676 — but no proximity weighting in the model

4. **Weighting is uniform across all scenarios**
   - School zone slowdown is equally important in "morning" (7-8am peak, school opening) and "evening" (4-5pm peak, less school activity)
   - No temporal sensitivity for facility-based interventions

---

## 4. GAPS WHERE NEIGHBORHOOD CONTEXT COULD BE BETTER INTEGRATED

### Gap 1: Proximity-Aware Scenario Modifiers
**Current**: Morning slowdown applies uniformly everywhere  
**Desired**: Facilities near a signal experience scenario-specific effects

```python
# Example: Morning scenario at School Junction (intersection_2)
# Currently: speed multiplier = 0.88 (global)
# Should be: distance to school_1 is ~26 meters → speed multiplier = 0.75-0.85
#           because school dropoff dominates morning dynamics at this intersection
```

**Impact**: Recommendations would be more targeted to actual neighborhood behavior

---

### Gap 2: Facility-Based Intervention Weighting
**Current**: All interventions have static multipliers  
**Desired**: Multipliers vary based on which facilities are near the signal

```python
# Example: school_zone_slowdown at School Junction (near school_1, kindergarten_1)
# Currently: speed always 0.90, waiting always 0.82, access always 1.12
# Should scale based on:
#   - Distance to school_1 and kindergarten_1 (closer = more extreme reduction)
#   - Time of day (morning priority > evening)
#   - Facility type sensitivity (school > admin > market)
```

**Impact**: System would recognize that school-zone interventions are most effective near actual schools

---

### Gap 3: Accessibility Scoring Is Generic
**Current**: accessibility_score = 100 - (waiting * 0.55) - (speed_deficit * 0.38)  
**Desired**: accessibility_score considers facility-specific mobility needs

```python
# Current formula doesn't distinguish:
# - School zone access (needs pedestrian safety, not just short waits)
# - Clinic access (needs reliable transit, not just traffic speed)
# - Market access (needs curb turnover, not just throughput)
# - Park access (needs slow, calm traffic, not speed)

# Should weight accessibility differently:
# - Near school: prioritize pedestrian_delay and safety (noise reduction)
# - Near clinic: prioritize reliable transit (bus_priority impact)
# - Near market: prioritize curb management and local street calm
# - Near park: prioritize speed reduction and noise reduction
```

**Impact**: "Access" metric would truly reflect what residents in each sub-corridor care about

---

### Gap 4: Intervention Selection Lacks Neighborhood Narratives
**Current**: System picks "best" intervention based on score; description is generic  
**Desired**: Description explains why this intervention is good for THIS neighborhood

```python
# Current description for pedestrian_priority:
"This intervention gives pedestrians and school-access trips a safer, more predictable crossing window."

# Could be neighborhood-specific:
# At Main Square (market nearby): "This intervention is key for market access—shoppers need safe crossing and smooth pedestrian flow."
# At School Junction: "This intervention directly supports school dropoff safety, reducing pedestrian delays by ~3 seconds."
# At Clinic Roundabout: "This intervention improves clinic access for elderly residents and patients on foot."
```

**Impact**: Stakeholders understand the recommendation in the context of their neighborhood's specific facilities

---

### Gap 5: No Facility-Specific Peak Times
**Current**: Three fixed scenarios (morning/evening/midday) apply to all facilities  
**Desired**: Each facility type has a demand profile

```python
# Example demand curves (% of daily peak traffic):
school_1:          0% | 30% | 90% | 10% | 85% | 40% | 0%  (7am-1pm-4pm focus)
clinic_1:          5% | 20% | 100% | 40% | 30% | 10% | 0%  (midday peak)
market_1:          10% | 30% | 80% | 50% | 70% | 40% | 5%  (midday + evening)
bus_stop_1:        80% | 40% | 30% | 60% | 85% | 50% | 20% (morning + evening focus)
park_1:            20% | 10% | 30% | 20% | 15% | 50% | 60% (afternoon/evening)

# Impact: morning scenario could be split into:
# - morning_school_peak (7-8am): school zone slowdown more effective
# - morning_commute_peak (8-9am): bus priority more effective
```

**Impact**: Interventions can be timed to match facility-specific demand patterns

---

### Gap 6: Intersection Context Not Reflected in Modifiers
**Current**: Intersection names exist (School Junction, Clinic Roundabout, Market Edge) but are cosmetic  
**Desired**: Intersection function informs scenario and intervention logic

```python
# Current structure:
INTERSECTIONS = [
  {"id": "intersection_1", "name": "Main Square", "coords": [...], "traffic_light_ids": [...]},
  {"id": "intersection_2", "name": "School Junction", "coords": [...], "traffic_light_ids": [...]},
]

# Could add functional context:
INTERSECTIONS = [
  {
    "id": "intersection_2", 
    "name": "School Junction", 
    "coords": [...], 
    "traffic_light_ids": [...],
    "primary_function": "school_access",
    "nearby_facilities": ["school_1", "kindergarten_1"],
    "critical_times": {"morning": [7, 8, 9], "afternoon": [14, 15, 16]},
    "sensitivity_profile": {
      "speed_reduction": 0.9,  # School zones prioritize safety
      "pedestrian_focus": true,
      "noise_sensitivity": true
    }
  }
]

# Usage in scenario modifier:
# If intersction.primary_function == "school_access" AND time in critical_times:
#   Apply school-specific modifiers (more aggressive access improvements)
```

**Impact**: Scenario modifiers and interventions become context-aware

---

## 5. RECOMMENDATIONS FOR IMPROVED NEIGHBORHOOD GROUNDING

### Recommendation 1: Proximity-Weighted Intervention Multipliers

**Current Code Location**: `_estimate_candidate_metrics()`

**Change**: Make multipliers distance-aware

```python
def _get_proximity_adjusted_multipliers(
    intervention_type: str, 
    signal_coords: tuple[float, float],
    facilities: list[dict],
    scenario: str
) -> dict[str, float]:
    """Adjust intervention multipliers based on proximity to relevant facilities."""
    
    base_multipliers = {
        "extend_green": {"speed": 1.12, "waiting": 0.80, ...},
        "bus_priority": {"speed": 1.18, "waiting": 0.76, ...},
        "school_zone_slowdown": {"speed": 0.90, "waiting": 0.82, ...},
        # ... others
    }
    
    multipliers = base_multipliers[intervention_type].copy()
    
    # School zone slowdown → check distance to school/kindergarten
    if intervention_type == "school_zone_slowdown":
        schools = [f for f in facilities if f["type"] in ["school", "kindergarten"]]
        for school in schools:
            distance = haversine_distance(signal_coords, school["coords"])
            if distance < 100:  # Very close
                multipliers["speed"] = 0.80  # More aggressive slowdown
                multipliers["access"] = 1.20  # Higher access improvement
            elif distance < 300:
                multipliers["speed"] = 0.85
                multipliers["access"] = 1.15
    
    # Pedestrian priority → higher impact near markets, parks, clinics
    if intervention_type == "pedestrian_priority":
        pedestrian_facilities = [f for f in facilities 
                                if f["type"] in ["market", "park", "clinic"]]
        for facility in pedestrian_facilities:
            distance = haversine_distance(signal_coords, facility["coords"])
            if distance < 150:
                multipliers["pedestrian"] = 0.60  # Better pedestrian outcomes
                multipliers["access"] = 1.25
    
    # Bus priority → higher impact near bus stops
    if intervention_type == "bus_priority":
        bus_stops = [f for f in facilities if f["type"] == "bus_stop"]
        for stop in bus_stops:
            distance = haversine_distance(signal_coords, stop["coords"])
            if distance < 200:
                multipliers["speed"] = 1.25  # More benefit to bus flow
                multipliers["waiting"] = 0.70
    
    # Apply scenario modifier on top
    scenario_mod = _scenario_modifier(scenario)
    return {k: v * scenario_mod.get(k, 1.0) for k, v in multipliers.items()}
```

**Benefits**:
- School zone slowdown is most aggressive near actual schools
- Bus priority activated near bus stops
- Pedestrian priority maximized in market/park areas
- Interventions become location-specific

---

### Recommendation 2: Facility-Aware Accessibility Scoring

**Current Code Location**: `_compute_metrics()` accessibility calculation

**Change**: Calculate accessibility by facility type, then weight by distance

```python
def _compute_facility_aware_accessibility(
    metrics: dict,
    signal_coords: tuple[float, float],
    facilities: list[dict]
) -> dict[str, float]:
    """Assess how well each facility type is served by current conditions."""
    
    waiting = metrics["average_waiting_seconds"]
    speed = metrics["average_speed_kmh"]
    pedestrian_delay = metrics["pedestrian_delay_seconds"]
    noise = metrics["noise_db"]
    
    # Baseline accessibility formula
    base_access = 100 - (waiting * 0.55) - (max(0, 60 - speed) * 0.38)
    
    facility_access = {}
    
    for facility in facilities:
        distance = haversine_distance(signal_coords, facility["coords"])
        decay = max(0.3, 1.0 - (distance / 1000))  # Impact decays with distance
        ftype = facility["type"]
        
        # School/kindergarten: prioritize pedestrian safety and low noise
        if ftype in ["school", "kindergarten"]:
            school_access = (
                100 
                - (pedestrian_delay * 0.6)  # Pedestrian safety is critical
                - (max(0, noise - 60) * 0.5)  # Noise reduction important
                - (max(0, 60 - speed) * 0.2)  # But not at cost of walkability
            )
            facility_access[facility["id"]] = school_access * decay
        
        # Clinic: prioritize reliable waiting times and transit
        elif ftype == "clinic":
            clinic_access = (
                100 
                - (waiting * 0.65)  # Reliability critical for patients
                - (max(0, 60 - speed) * 0.15)  # Moderate speed focus
            )
            facility_access[facility["id"]] = clinic_access * decay
        
        # Market: prioritize curb turnover (low waiting) and pedestrian flow
        elif ftype == "market":
            market_access = (
                100 
                - (waiting * 0.60)  # Turnover critical
                - (pedestrian_delay * 0.30)  # Pedestrian flow matters
            )
            facility_access[facility["id"]] = market_access * decay
        
        # Park: prioritize calm environment (speed + noise)
        elif ftype == "park":
            park_access = (
                100 
                - (max(0, 60 - speed) * 0.40)  # Calm atmosphere
                - (max(0, noise - 60) * 0.40)  # Quiet environment
            )
            facility_access[facility["id"]] = park_access * decay
        
        # Bus stop: prioritize speed and reliability
        elif ftype == "bus_stop":
            bus_access = (
                100 
                - (waiting * 0.50)  # Reliability
                - (max(0, 60 - speed) * 0.30)  # Speed for connections
            )
            facility_access[facility["id"]] = bus_access * decay
        
        # Administrative/public: general accessibility
        else:
            facility_access[facility["id"]] = base_access * decay
    
    return facility_access  # Returns dict of facility_id: accessibility_score
```

**Benefits**:
- Accessibility score reflects what each facility type actually needs
- Interventions can be evaluated by "how well do we serve schools/clinics/markets"
- More nuanced than single global accessibility number

---

### Recommendation 3: Facility-Specific Scenario Profiles

**Current Code Location**: `_scenario_modifier()`

**Change**: Expand to include facility-aware timing

```python
def _scenario_modifier(scenario: str, signal_coords: tuple[float, float] = None, facilities: list[dict] = None):
    """Adjust metrics based on time-of-day and facility context."""
    
    # Baseline scenarios (current implementation)
    base_scenarios = {
        "morning": {"speed": 0.88, "waiting": 1.2, "vehicle": 1.18, "noise": 1.08, "access": 0.92},
        "evening": {"speed": 0.9, "waiting": 1.15, "vehicle": 1.12, "noise": 1.04, "access": 0.95},
        "midday": {"speed": 1.0, "waiting": 1.0, "vehicle": 1.0, "noise": 1.0, "access": 1.0}
    }
    
    modifiers = base_scenarios.get(scenario, base_scenarios["midday"]).copy()
    
    # If facility context is provided, adjust for facility-specific demand
    if signal_coords and facilities:
        nearby_schools = [f for f in facilities 
                         if f["type"] in ["school", "kindergarten"]
                         and haversine_distance(signal_coords, f["coords"]) < 300]
        
        if nearby_schools and scenario == "morning":
            # Morning school peak (7-9am): even worse access, higher waiting
            modifiers["waiting"] = 1.35  # More congestion near schools
            modifiers["access"] = 0.80  # Lower access
            modifiers["pedestrian_delay"] = 1.3  # More pedestrian crowding
        
        nearby_markets = [f for f in facilities 
                         if f["type"] == "market"
                         and haversine_distance(signal_coords, f["coords"]) < 300]
        
        if nearby_markets and scenario == "midday":
            # Market peak (11am-1pm): midday surge
            modifiers["waiting"] = 1.25
            modifiers["vehicle"] = 1.15
            modifiers["access"] = 0.85
        
        nearby_clinics = [f for f in facilities 
                         if f["type"] == "clinic"
                         and haversine_distance(signal_coords, f["coords"]) < 300]
        
        if nearby_clinics:
            # Clinics steady throughout day; less scenario variance
            modifiers["waiting"] = modifiers["waiting"] * 0.95  # More stable
            modifiers["access"] = modifiers["access"] * 1.05  # Better maintained
    
    return modifiers
```

**Benefits**:
- Captures facility-specific demand curves
- Morning scenario can be refined near schools vs. markets
- Access scoring reflects facility-specific volatility

---

### Recommendation 4: Enhanced Intersection Context

**Change**: Add facility context to INTERSECTIONS structure in mahalla_data.py

```python
INTERSECTIONS = [
    {
        "id": "intersection_1",
        "name": "Main Square",
        "coords": [41.3168, 69.2666],
        "traffic_light_ids": ["cluster_1"],
        "primary_function": "central_hub",
        "nearby_facilities": ["market_1", "facility_2"],  # Community center
        "demand_profile": {
            "morning": 0.7,    # 70% of network average
            "midday": 1.0,
            "evening": 0.8
        },
        "accessibility_priorities": ["pedestrian", "market_access", "equity"]
    },
    {
        "id": "intersection_2",
        "name": "School Junction",
        "coords": [41.3182, 69.2684],
        "traffic_light_ids": ["cluster_2"],
        "primary_function": "school_access",
        "nearby_facilities": ["school_1", "kindergarten_1"],
        "demand_profile": {
            "morning": 1.3,    # 130% of average (school peak)
            "midday": 0.6,
            "evening": 1.2     # Afternoon pickup peak
        },
        "accessibility_priorities": ["pedestrian_safety", "school_access", "speed_calming"]
    },
    # ... etc
]
```

**Usage in code**:

```python
def get_effective_scenario_modifier(intersection_id: str, scenario: str, facilities: list[dict]):
    intersection = find_intersection(intersection_id)
    base_modifier = _scenario_modifier(scenario)
    
    # Scale by facility-specific demand profile
    demand_factor = intersection.get("demand_profile", {}).get(scenario, 1.0)
    
    return {
        k: v * demand_factor 
        for k, v in base_modifier.items()
    }
```

**Benefits**:
- Intersection function is explicit and used in calculations
- Demand curves can be facility-aware
- Accessibility priorities guide recommendation generation

---

### Recommendation 5: Neighborhood-Grounded Intervention Descriptions

**Current Code Location**: `optimize_interventions()` description building

**Change**: Generate descriptions that reference specific facilities

```python
def _generate_facility_aware_description(
    intervention: dict,
    baseline: dict,
    delta: dict,
    signal_id: str,
    intersections: list[dict],
    facilities: list[dict]
) -> str:
    """Create a description that connects intervention to neighborhood context."""
    
    intersection = find_intersection_by_signal(signal_id, intersections)
    if not intersection:
        return _generic_description(intervention)
    
    nearby = intersection.get("nearby_facilities", [])
    func = intersection.get("primary_function", "local_mobility")
    name = intersection.get("name", "this intersection")
    
    action_type = intervention["type"]
    
    if action_type == "school_zone_slowdown" and any(
        f["type"] in ["school", "kindergarten"] for f in facilities 
        if f["id"] in nearby
    ):
        school_name = next(
            (f["name"] for f in facilities if f["id"] in nearby and f["type"] in ["school", "kindergarten"]),
            "the school"
        )
        return (
            f"Calm traffic at {name} to support safe access to {school_name}. "
            f"This intervention reduces vehicle speeds by ~10% and significantly improves pedestrian safety. "
            f"Expected: {abs(delta['pedestrian_delay_seconds']):.1f}s reduction in pedestrian delays, "
            f"{abs(delta['noise_db']):.1f}dB quieter environment."
        )
    
    elif action_type == "pedestrian_priority" and any(
        f["type"] in ["market", "park"] for f in facilities 
        if f["id"] in nearby
    ):
        location_type = next(
            (f["type"] for f in facilities if f["id"] in nearby and f["type"] in ["market", "park"]),
            "pedestrian area"
        )
        location_name = next(
            (f["name"] for f in facilities if f["id"] in nearby and f["type"] in ["market", "park"]),
            location_type
        )
        return (
            f"Prioritize pedestrian crossing at {name} for {location_name} access. "
            f"This intervention gives foot traffic a safer, predictable window and reduces crowding. "
            f"Expected: {abs(delta['pedestrian_delay_seconds']):.1f}s faster crossing, "
            f"{delta['accessibility_score']:.1f}% improvement in local access score."
        )
    
    elif action_type == "bus_priority" and any(
        f["type"] == "bus_stop" for f in facilities 
        if f["id"] in nearby
    ):
        return (
            f"Prioritize transit at {name} to strengthen bus-corridor performance. "
            f"This intervention improves public transport reliability without blocking local traffic. "
            f"Expected: {abs(delta['average_waiting_seconds']):.1f}s reduction in typical wait times, "
            f"better connectivity for transit-dependent residents."
        )
    
    elif action_type == "extend_green":
        return (
            f"Extend green signal time at {name} to improve throughput. "
            f"This reduces average waiting time by {abs(delta['average_waiting_seconds']):.1f}s "
            f"while maintaining safe pedestrian crossing intervals. "
            f"Secondary benefit: {abs(delta['co2_kg']):.2f}kg reduction in CO2 from reduced idling."
        )
    
    # Fallback to generic description
    return _generic_description(intervention)

# Usage in optimize_interventions():
candidate["description"] = _generate_facility_aware_description(
    entry, baseline, delta, signal_id, INTERSECTIONS, FACILITIES
)
```

**Benefits**:
- Recommendations feel local and grounded
- Stakeholders understand why intervention targets this specific intersection
- Descriptions highlight facility-specific benefits

---

### Recommendation 6: Multi-Facility Impact Assessment

**New Function**: Add to sumo_runner.py

```python
def _assess_intervention_by_facility(
    metrics: dict[str, Any],
    facilities: list[dict],
    signal_coords: tuple[float, float],
    baseline_metrics: dict[str, Any]
) -> dict[str, dict]:
    """Evaluate intervention impact on access to each facility type."""
    
    facility_impact = {}
    
    for facility in facilities:
        fid = facility["id"]
        fname = facility["name"]
        ftype = facility["type"]
        distance = haversine_distance(signal_coords, facility["coords"])
        
        # Distance decay: impact strongest within 300m, fades beyond
        impact_factor = max(0, 1.0 - (distance / 500))
        
        if impact_factor < 0.1:
            facility_impact[fid] = {
                "name": fname,
                "type": ftype,
                "distance": distance,
                "impact_factor": 0.0,  # Too far
                "status": "not affected"
            }
            continue
        
        # Compute facility-specific accessibility deltas
        facility_wait_delta = (metrics["average_waiting_seconds"] - baseline_metrics["average_waiting_seconds"]) * impact_factor
        facility_speed_delta = (metrics["average_speed_kmh"] - baseline_metrics["average_speed_kmh"]) * impact_factor
        facility_ped_delta = (metrics["pedestrian_delay_seconds"] - baseline_metrics["pedestrian_delay_seconds"]) * impact_factor
        facility_noise_delta = (metrics["noise_db"] - baseline_metrics["noise_db"]) * impact_factor
        
        # Determine if impact is positive or negative for this facility type
        quality = "improved"
        if ftype in ["school", "kindergarten"]:
            # Schools value low noise + safe pedestrian environment
            school_score = -facility_ped_delta - (facility_noise_delta * 0.5)
            quality = "significantly improved" if school_score > 2 else "improved" if school_score > 0 else "unchanged"
        elif ftype == "clinic":
            # Clinics value reliability (low waiting)
            clinic_score = -facility_wait_delta
            quality = "significantly improved" if clinic_score > 5 else "improved" if clinic_score > 0 else "unchanged"
        elif ftype in ["market", "park"]:
            # Markets/parks value pedestrian flow + calm
            ped_score = -facility_ped_delta - (facility_noise_delta * 0.3)
            quality = "significantly improved" if ped_score > 2 else "improved" if ped_score > 0 else "unchanged"
        
        facility_impact[fid] = {
            "name": fname,
            "type": ftype,
            "distance": round(distance, 1),
            "impact_factor": round(impact_factor, 2),
            "quality": quality,
            "waiting_delta": round(facility_wait_delta, 2),
            "speed_delta": round(facility_speed_delta, 2),
            "pedestrian_delta": round(facility_ped_delta, 2),
            "noise_delta": round(facility_noise_delta, 2),
        }
    
    return facility_impact
```

**Usage**: Return facility_impact as part of candidate object

```python
candidate = {
    # ... existing fields
    "facility_impact": _assess_intervention_by_facility(
        metrics, FACILITIES, signal_coords, baseline
    ),
    "summary": f"This intervention most benefits {impact_summary_text}",
}
```

**Benefits**:
- Stakeholders see facility-by-facility impact
- Can answer: "How does this help school access? Clinic access? Market vitality?"
- More transparent than single-number score

---

## 6. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Low Risk, High Impact)
1. **Add facility context to INTERSECTIONS** (mahalla_data.py)
   - Add `primary_function` and `nearby_facilities` fields
   - Add `accessibility_priorities` list
   - Minimal code changes, purely data enrichment

2. **Facility-aware descriptions** (sumo_runner.py)
   - Implement `_generate_facility_aware_description()`
   - Reference actual facilities in intervention text
   - No metric changes, just better narratives

### Phase 2: Metric Refinement (Medium Risk, High Impact)
3. **Facility-specific accessibility scoring** (sumo_runner.py)
   - Implement `_compute_facility_aware_accessibility()`
   - Return dict of facility_id → accessibility_score
   - Update candidate object to include per-facility scores

4. **Facility impact assessment** (sumo_runner.py)
   - Implement `_assess_intervention_by_facility()`
   - Show which facilities benefit most from each intervention

### Phase 3: Proximity Awareness (Medium Risk, High Impact)
5. **Proximity-weighted multipliers** (sumo_runner.py)
   - Implement `_get_proximity_adjusted_multipliers()`
   - Modify `_estimate_candidate_metrics()` to use proximity-aware multipliers
   - Test that school-zone interventions are more aggressive near schools

### Phase 4: Advanced Contextualization (Higher Risk, Highest Impact)
6. **Facility-specific scenario profiles** (sumo_runner.py)
   - Enhance `_scenario_modifier()` to accept facility context
   - Implement facility-specific demand curves
   - Requires testing to ensure scenarios remain realistic

---

## 7. SUCCESS CRITERIA

### Before Improvements
- ❌ System doesn't distinguish between School Junction and Market Edge for school-zone slowdown
- ❌ Interventions use generic multipliers regardless of location
- ❌ "Accessibility" is a single number, not facility-aware
- ❌ Recommendations don't reference specific facilities in the mahalla

### After Phase 1
- ✅ Recommendations mention specific facilities ("improves access to District School")
- ✅ Intersection context is structured and available for future use
- ✅ Stakeholders immediately see which facilities each intervention helps

### After Phase 2
- ✅ Accessibility scores are facility-specific and transparent
- ✅ Can answer "how does this help school access vs. clinic access?"
- ✅ Impact assessment shows which facility types benefit most

### After Phase 3
- ✅ School-zone slowdown is more aggressive near schools
- ✅ Bus priority is more effective near bus stops
- ✅ Pedestrian priority is maximized near markets/parks

### After Phase 4
- ✅ Morning scenario reflects school-specific demand surge
- ✅ Midday scenario captures market peak
- ✅ Evening scenario reflects home-return and recreational patterns
- ✅ Scenarios adapt based on signal location relative to facilities

---

## 8. SUMMARY TABLE: Gaps vs. Solutions

| Gap | Current State | Proposed Solution | Impact |
|-----|---------------|-------------------|--------|
| Interventions ignore facility location | "school_zone_slowdown" uses same multipliers everywhere | Proximity-weighted multipliers scale effect by distance to facilities | School interventions most aggressive near schools |
| Accessibility is generic | Single accessibility_score applies to all facility types | Facility-specific accessibility scoring (school needs ≠ clinic needs) | Transparent about which facilities each intervention serves |
| Scenario modifiers are uniform | Morning slowdown applies everywhere | Facility-aware demand profiles (school 7-8am peak, market 11am-1pm peak) | Recommendations match actual neighborhood dynamics |
| Intersection context is cosmetic | Names exist but unused in logic | Functional enrichment (primary_function, nearby_facilities, priorities) | Enables location-aware recommendations |
| Recommendations are generic | "safe, more predictable crossing window" everywhere | Facility-grounded narratives ("improves access to District School") | Stakeholders connect recommendation to their neighborhood |
| No impact visibility by facility | Only aggregate metrics returned | Per-facility impact assessment (which facilities benefit, by how much) | Transparent tradeoff analysis |

---

## 9. EXAMPLE: Before & After

### Before Improvements

**Baseline**: Morning scenario at School Junction (near school_1, kindergarten_1)
```
Speed: 15.8 km/h (×0.88 morning modifier)
Waiting: 28.3s (×1.2 morning modifier)
Accessibility: 72.4%
```

**Intervention**: school_zone_slowdown (5s adjustment, bus_stop_1 is 500m away)
```
Speed: 14.2 km/h (×0.90 from multiplier, ×0.88 scenario)
Waiting: 23.2s (×0.82 from multiplier, ×1.2 scenario)
Pedestrian Delay: 12.1s (×0.74 from multiplier)
Accessibility: 81.3%
Description: "This intervention reduces risk in the most sensitive local area by creating calmer traffic and better visibility."
```

**Problem**: Multipliers don't reflect that this IS a sensitive school area, right next to school_1 and kindergarten_1

---

### After Improvements

**Baseline**: Morning scenario at School Junction
```
Speed: 15.8 km/h (×0.88 morning)
Waiting: 28.3s (×1.2 morning)
Accessibility by facility:
  - school_1 (26m away): 68.2% (school-focused scoring: emphasizes pedestrian safety)
  - kindergarten_1 (42m away): 71.1%
  - park_1 (600m away): 75.3% (distance decay applied)
```

**Intervention**: school_zone_slowdown (5s adjustment, proximity-weighted)
```
Proximity to school_1: 26m → impact_factor = 0.95 (very close, max effect)
Proximity to kindergarten_1: 42m → impact_factor = 0.93

Adjusted multipliers (proximity-aware):
  Base school_zone_slowdown: speed=0.90, pedestrian=0.74
  Proximity adjustment: speed→0.82, pedestrian→0.65 (more aggressive due to proximity)
  Scenario application: ×0.88 morning modifier
  
Final metrics:
  Speed: 12.8 km/h (×0.82 ×0.88)
  Waiting: 23.8s (×0.82 from multiplier ×1.2 morning)
  Pedestrian Delay: 8.3s (×0.65 from proximity-adjusted multiplier)
  
Accessibility by facility:
  - school_1: 79.4% (+11.2%) ✨ School access significantly improves
  - kindergarten_1: 82.1% (+11.0%) ✨
  - park_1: 76.8% (+1.5%) (distant, minimal effect)
  
Description: "Calm traffic at School Junction to support safe access to District School and Kindergarten #4. 
This intervention reduces vehicle speeds by ~17% in the school zone and significantly improves pedestrian safety. 
Expected: 3.8s reduction in pedestrian delays, 2.2dB quieter environment. 
School access improves by 11%, while broader corridor remains accessible."
```

**Benefit**: Stakeholders understand:
1. *Why* this intervention is recommended (proximity to school_1 and kindergarten_1)
2. *Who* benefits most (school/kindergarten users, less impact on distant park)
3. *What* the neighborhood experience changes (17% speed reduction in school zone)
4. *How much* each facility type improves (11% for schools, 1.5% for park)

---

## Conclusion

The current implementation provides a solid foundation with clear facility definitions, multi-objective optimization, and multiple scenario contexts. However, the gap between rich spatial data (facilities, intersections) and algorithmic usage (generic scenario modifiers, location-agnostic multipliers) creates an unrealistic feel.

**Key insight**: The system knows WHAT facilities exist and WHERE they are, but doesn't USE that information to adjust how traffic flows around them.

**Path forward**: Progressively integrate facility context into scenario modifiers, intervention weighting, accessibility scoring, and recommendation narratives. This transforms the system from "generic traffic optimization" to "neighborhood-aware mobility planning"—the core value of MahallaMind.

**Timeline**: Phases 1–2 (neighborhood-grounded narratives + facility-specific accessibility) can be implemented in 2–3 days with high immediate user-facing value. Phases 3–4 (proximity weighting + scenario adaptation) require more testing but unlock the full potential of the facility data.
