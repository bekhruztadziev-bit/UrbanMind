import json
import os

with open("validation_experiment_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Interventions
# extend_green_5s_signal_timing
# reduce_green_-5s_signal_timing
# school_zone_slowdown_0s_safety

interventions = {
    "extend_green_5s_signal_timing": "Signal +5s",
    "reduce_green_-5s_signal_timing": "Signal -5s",
    "school_zone_slowdown_0s_safety": "Traffic-calming speed restriction"
}

metrics = {
    "average_waiting_seconds": "Waiting time (s)",
    "average_speed_kmh": "Average speed (km/h)",
    "max_vehicle_count": "Peak vehicles",
    "co2_kg": "CO₂ (kg)",
    "nox_g": "NOₓ (g)",
    "noise_db": "Noise (dB)",
    "pedestrian_delay_seconds": "Pedestrian delay (s)",
    "accessibility_score": "Accessibility score"
}

conditions = data["conditions"]

out = []
out.append("# UrbanMind v2 Validation Experiment 001\n")

out.append("## Research question")
out.append("> **How does the effectiveness of the three simulation-backed UrbanMind interventions change as traffic demand increases?**")
out.append("> Which intervention performs best at different traffic-demand levels, and does the relative effectiveness of each intervention remain stable as demand increases?\n")
out.append("This is a **deterministic comparative simulation analysis**, not a statistically powered field experiment.\n")

out.append("## Experimental design")
out.append("- **Traffic levels**: 0.8×, 1.0×, 1.2×, 1.4×")
out.append("- **Interventions**: Signal +5s, Signal -5s, Traffic-calming speed restriction")
out.append("- **Duration**: 300 steps")
out.append("- **Controls**: Same-demand baseline for each level")
out.append("- **Seed/configuration**: Deterministic SUMO standard configuration\n")

out.append("## Intervention definitions")
out.append("- **Signal +5s**: Extends the green phase duration of the target intersection by 5 seconds using TraCI.")
out.append("- **Signal -5s**: Reduces the green phase duration of the target intersection by 5 seconds using TraCI.")
out.append("- **Traffic-calming speed restriction**: A simulated safety measure. At runtime, TraCI selects residential lanes with limits between 21 and 50 km/h and overrides them to 20 km/h (5.5 m/s). It does not explicitly model new pedestrian demand or individual speed bumps.\n")

out.append("## Results\n")

for metric_key, metric_label in metrics.items():
    out.append(f"### {metric_label}")
    out.append("| Demand | Intervention | Control | Intervention | Δ | % Δ |")
    out.append("| ------ | ------------ | ------: | -----------: | -: | --: |")
    
    for tl in [0.8, 1.0, 1.2, 1.4]:
        for iv_id, iv_label in interventions.items():
            # find condition
            cond = next((c for c in conditions if c["traffic_multiplier"] == tl and c["intervention_id"] == iv_id), None)
            if not cond: continue
            
            ctrl_val = cond["control_metrics"].get(metric_key, 0)
            scen_val = cond["scenario_metrics"].get(metric_key, 0)
            delta = cond["metric_deltas"].get(metric_key, {}).get("absolute", 0)
            pct = cond["metric_deltas"].get(metric_key, {}).get("percentage", 0)
            
            out.append(f"| {tl}× | {iv_label} | {ctrl_val} | {scen_val} | {delta} | {pct}% |")
    out.append("\n")

out.append("## Primary analysis (Waiting time)")
out.append("Waiting time is the primary measure of effectiveness. Lower is better (negative Δ is effective).\n")

# Wait time robust check
effective_counts = {iv: 0 for iv in interventions}
for tl in [0.8, 1.0, 1.2, 1.4]:
    for iv_id, iv_label in interventions.items():
        cond = next((c for c in conditions if c["traffic_multiplier"] == tl and c["intervention_id"] == iv_id), None)
        if cond and cond["metric_deltas"]["average_waiting_seconds"]["absolute"] < 0:
            effective_counts[iv_id] += 1

out.append("## Robustness summary")
for iv_id, iv_label in interventions.items():
    out.append(f"**{iv_label}**\nEffective at: {effective_counts[iv_id]} / 4 demand levels")
out.append("\n")

out.append("## Demand-response analysis")
# Just leave this to manual writeup or generate basic trends
for iv_id, iv_label in interventions.items():
    pcts = []
    for tl in [0.8, 1.0, 1.2, 1.4]:
        cond = next((c for c in conditions if c["traffic_multiplier"] == tl and c["intervention_id"] == iv_id), None)
        if cond:
            pcts.append(cond["metric_deltas"]["average_waiting_seconds"]["percentage"])
    out.append(f"**{iv_label}**: Wait time % changes across demand (0.8x -> 1.4x): {pcts}\n")

out.append("## Reproducibility information")
out.append(f"- **Experiment ID**: {data.get('experiment_id')}")
out.append(f"- **Date/Time**: {data.get('created_at')}")
out.append(f"- **Duration**: {data.get('duration')} steps")
out.append(f"- **Determinism Verified**: {'YES' if data.get('determinism_verified') else 'NO'}")
out.append(f"- **Runtime**: {data.get('experiment_runtime', 0):.2f}s")
out.append("- **SUMO Version**: 1.27.1")
out.append("- **Canonical Scenario**: `mahalla-scenario`")
out.append("\n")

out.append("## Limitations")
out.append("- **SUMO model vs reality**: Vehicles perfectly comply; does not model complex behavioral responses.")
out.append("- **Deterministic single-seed experiment**: Results represent a single simulation path, not a statistically robust distribution.")
out.append("- **Absence of explicit pedestrian demand**: Cannot natively test active mobility effects.")
out.append("- **Absence of bus/parking behavior**: Missing transit mapping limits evaluating multi-modal shifts.")
out.append("- **Traffic-demand scaling assumptions**: Uniform scaling multiplier does not perfectly reflect real peak-hour directional flow shifts.")
out.append("\n")

out.append("## Future experimental improvements")
out.append("- Multiple seeds and repeated trials for statistical inference.")
out.append("- Longer simulation horizons (e.g., full 24-hour profiles).")
out.append("- Calibrated emission models using localized vehicle fleets.")
out.append("- Richer demand data integrating transit and pedestrians.")
out.append("- Real-world field validation to anchor simulation estimates.\n")

os.makedirs("../docs/experiments", exist_ok=True)
with open("../docs/experiments/urbanmind_v2_validation_001.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
