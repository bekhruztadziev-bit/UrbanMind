import sys
import os
import json
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.simulation.experiment_runner import run_experiment
from app.services.simulation.session import run_simulation
from app.services.simulation.interventions import get_candidate_interventions
from app.services.simulation.session import _scenario_signal_selection
from app.services.simulation.metrics import calculate_metrics

def check_determinism(simulated_ids):
    print("--- Running Determinism Verification ---")
    signal_id, phase_index = _scenario_signal_selection()
    cands = get_candidate_interventions(signal_id, phase_index)
    
    # find school zone
    sz = next(c for c in cands if c.get("type") == "school_zone_slowdown")
    
    req = {
        "steps": 300,
        "scenario": "midday",
        "intervention": sz,
        "traffic_multiplier": 1.2
    }
    
    print("Run A...")
    raw_a = run_simulation(req)
    metrics_a = calculate_metrics(raw_a)
    
    print("Run B...")
    raw_b = run_simulation(req)
    metrics_b = calculate_metrics(raw_b)
    
    is_identical = True
    for k in metrics_a:
        if metrics_a[k] != metrics_b.get(k):
            print(f"Mismatch in {k}: A={metrics_a[k]} B={metrics_b.get(k)}")
            is_identical = False
            
    print(f"Run A == Run B: {'YES' if is_identical else 'NO'}")
    return is_identical

def main():
    signal_id, phase_index = _scenario_signal_selection()
    cands = get_candidate_interventions(signal_id, phase_index)
    
    simulated_ids = []
    for c in cands:
        if c.get("evaluation_mode") == "SIMULATED":
            cand_id = f"{c['type']}_{c.get('seconds', 0)}s_{c['category']}"
            simulated_ids.append(cand_id)
            
    print(f"Found SIMULATED IDs: {simulated_ids}")
    
    # 1. Check determinism first
    is_identical = check_determinism(simulated_ids)
    
    # 2. Run the main experiment
    traffic_levels = [0.8, 1.0, 1.2, 1.4]
    
    req = {
        "name": "Validation Experiment 001",
        "traffic_levels": traffic_levels,
        "intervention_ids": simulated_ids,
        "duration": 300, # Use standard duration
    }
    
    print("Starting experiment...")
    start_time = time.time()
    result = run_experiment(req)
    end_time = time.time()
    
    runtime = end_time - start_time
    print(f"Experiment finished in {runtime:.2f} seconds.")
    
    result["determinism_verified"] = is_identical
    result["experiment_runtime"] = runtime
    
    with open("validation_experiment_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        
    print("Results saved to validation_experiment_results.json")
    
if __name__ == "__main__":
    main()
