import sys
import os
import json
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import traci
from app.services.simulation.session import _ensure_sumo_ready, _apply_intervention, _traci_lock, SUMO_BINARY, SUMOCFG, _scenario_signal_selection
from app.services.simulation.metrics import calculate_metrics
from app.services.simulation.interventions import get_candidate_interventions

def custom_run_simulation(request, warmup_steps=0):
    _ensure_sumo_ready()
    
    steps = request.get("steps", 300)
    scenario = request.get("scenario", "midday")
    intervention = request.get("intervention")
    traffic_multiplier = request.get("traffic_multiplier", 1.0)
    seed = request.get("seed")

    sumo_cmd = [str(SUMO_BINARY), "-c", str(SUMOCFG), "--no-step-log", "--duration-log.disable"]
    if traffic_multiplier != 1.0:
        sumo_cmd.extend(["--scale", str(traffic_multiplier)])
    if seed is not None:
        sumo_cmd.extend(["--seed", str(seed)])
        
    with _traci_lock:
        connected = False
        try:
            traci.start(sumo_cmd)
            connected = True

            if intervention:
                _apply_intervention(intervention)

            total_speed = 0.0
            total_waiting = 0.0
            samples = 0
            max_vehicle_count = 0
            
            # for warm up
            wu_total_speed = 0.0
            wu_total_waiting = 0.0
            wu_samples = 0
            wu_max_vehicle_count = 0

            traffic_lights = traci.trafficlight.getIDList()

            for i in range(steps):
                traci.simulationStep()
                
                vehicle_ids = traci.vehicle.getIDList()
                vehicle_count = len(vehicle_ids)
                
                max_vehicle_count = max(max_vehicle_count, vehicle_count)
                if i >= warmup_steps:
                    wu_max_vehicle_count = max(wu_max_vehicle_count, vehicle_count)

                if vehicle_ids:
                    for vehicle_id in vehicle_ids:
                        spd = traci.vehicle.getSpeed(vehicle_id)
                        wt = traci.vehicle.getAccumulatedWaitingTime(vehicle_id)
                        total_speed += spd
                        total_waiting += wt
                        samples += 1
                        
                        if i >= warmup_steps:
                            wu_total_speed += spd
                            wu_total_waiting += wt
                            wu_samples += 1

            full_result = {
                "steps": steps, "scenario": scenario, "simulation_time_seconds": float(traci.simulation.getTime()),
                "traffic_light_count": len(traffic_lights), "traffic_light_ids": list(traffic_lights),
                "total_speed": total_speed, "total_waiting": total_waiting, "samples": samples,
                "max_vehicle_count": max_vehicle_count,
            }
            wu_result = {
                "steps": steps - warmup_steps, "scenario": scenario, "simulation_time_seconds": float(traci.simulation.getTime()) - warmup_steps,
                "traffic_light_count": len(traffic_lights), "traffic_light_ids": list(traffic_lights),
                "total_speed": wu_total_speed, "total_waiting": wu_total_waiting, "samples": wu_samples,
                "max_vehicle_count": wu_max_vehicle_count,
            }
            return full_result, wu_result
        finally:
            if connected:
                try: traci.close()
                except Exception: pass

def main():
    results = {}
    start_time = time.time()
    
    # 1. Demand Sweep (Controls)
    print("--- 1. Demand Sweep ---")
    demand_levels = [0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8]
    demand_sweep = {}
    for tl in demand_levels:
        req = {"steps": 300, "traffic_multiplier": tl}
        raw_full, _ = custom_run_simulation(req)
        metrics = calculate_metrics(raw_full)
        demand_sweep[str(tl)] = {"raw": raw_full, "metrics": metrics}
    results["demand_sweep"] = demand_sweep
    
    # 2. Horizon Sweep (Controls)
    print("--- 2. Horizon Sweep ---")
    horizons = [300, 600, 900, 1800]
    h_demand_levels = [0.8, 1.0, 1.2, 1.4]
    horizon_sweep = {}
    for hz in horizons:
        horizon_sweep[str(hz)] = {}
        for tl in h_demand_levels:
            req = {"steps": hz, "traffic_multiplier": tl}
            raw_full, _ = custom_run_simulation(req)
            metrics = calculate_metrics(raw_full)
            horizon_sweep[str(hz)][str(tl)] = {"raw": raw_full, "metrics": metrics}
    results["horizon_sweep"] = horizon_sweep
    
    # 3. Warm-up Analysis
    print("--- 3. Warm-up Analysis ---")
    # Take 300 steps with 100 step warmup, and 600 steps with 200 step warmup
    warmup_analysis = {}
    for tl in [1.0, 1.4]:
        req = {"steps": 300, "traffic_multiplier": tl}
        full, wu = custom_run_simulation(req, warmup_steps=100)
        warmup_analysis[f"300_{tl}"] = {"full": calculate_metrics(full), "warmup_100": calculate_metrics(wu)}
        
        req = {"steps": 600, "traffic_multiplier": tl}
        full, wu = custom_run_simulation(req, warmup_steps=200)
        warmup_analysis[f"600_{tl}"] = {"full": calculate_metrics(full), "warmup_200": calculate_metrics(wu)}
    results["warmup_analysis"] = warmup_analysis
    
    # 4. Repeated-seed pilot
    print("--- 4. Repeated-seed pilot ---")
    signal_id, phase_index = _scenario_signal_selection()
    cands = get_candidate_interventions(signal_id, phase_index)
    iv_sig = next(c for c in cands if c.get("type") == "reduce_green")
    iv_tc = next(c for c in cands if c.get("type") == "school_zone_slowdown")
    
    seeds = [42, 101, 202, 303, 404]
    seed_pilot = {}
    for tl in [1.0, 1.2, 1.4]:
        seed_pilot[str(tl)] = {}
        for seed in seeds:
            seed_pilot[str(tl)][str(seed)] = {}
            # Control
            req_c = {"steps": 300, "traffic_multiplier": tl, "seed": seed}
            raw_c, _ = custom_run_simulation(req_c)
            seed_pilot[str(tl)][str(seed)]["control"] = calculate_metrics(raw_c)["average_waiting_seconds"]
            
            # Sig -5
            req_s = {"steps": 300, "traffic_multiplier": tl, "seed": seed, "intervention": iv_sig}
            raw_s, _ = custom_run_simulation(req_s)
            seed_pilot[str(tl)][str(seed)]["sig_minus_5"] = calculate_metrics(raw_s)["average_waiting_seconds"]
            
            # TC
            req_t = {"steps": 300, "traffic_multiplier": tl, "seed": seed, "intervention": iv_tc}
            raw_t, _ = custom_run_simulation(req_t)
            seed_pilot[str(tl)][str(seed)]["traffic_calming"] = calculate_metrics(raw_t)["average_waiting_seconds"]
    
    results["seed_pilot"] = seed_pilot

    end_time = time.time()
    results["runtime"] = end_time - start_time
    with open("diagnostic_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"Done. Saved to diagnostic_results.json in {results['runtime']:.2f}s")

if __name__ == "__main__":
    main()
