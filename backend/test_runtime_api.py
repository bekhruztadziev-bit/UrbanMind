import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def make_request(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    body = json.dumps(data).encode("utf-8") if data else None
    try:
        with urllib.request.urlopen(req, data=body, timeout=120) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            return status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"error": content}
    except Exception as e:
        return 500, {"error": str(e)}

def run_all_checks():
    print("=== URBANMIND RUNTIME ENDPOINT VERIFICATION ===")

    # 1. Health
    s, r = make_request("/health")
    print(f"1. /api/health: status={s}, ok={r.get('ok')}")
    assert s == 200 and r.get("ok") is True, f"Health check failed: {r}"

    # 2. Mahalla context
    s, r = make_request("/mahalla")
    print(f"2. /api/mahalla: status={s}, intersections={len(r.get('intersections', []))}, roads={len(r.get('roads', []))}")
    assert s == 200 and len(r.get("intersections", [])) > 0, f"Mahalla check failed: {r}"

    # 3. Baseline Metrics
    s, r = make_request("/metrics", method="POST", data={"scenario": "midday", "traffic_multiplier": 1.0})
    print(f"3. /api/metrics: status={s}, avg_speed={r.get('average_speed_kmh')}, waiting={r.get('average_waiting_seconds')}")
    assert s == 200 and "average_speed_kmh" in r, f"Metrics check failed: {r}"

    # 4. Optimize
    s, r = make_request("/optimize", method="POST", data={"scenario": "midday", "traffic_multiplier": 1.0})
    ranked = r.get("ranked_candidates", [])
    best = r.get("best_candidate", {})
    print(f"4. /api/optimize: status={s}, candidates={len(ranked)}, best={best.get('id')}")
    assert s == 200 and len(ranked) >= 1 and best.get("id"), f"Optimize check failed: {r}"

    # 5. AI Explain Endpoint (Live payload)
    ai_payload = {
        "baseline": r.get("baseline", {}),
        "candidates": ranked,
        "best_candidate": best
    }
    s, ai_res = make_request("/ai/explain", method="POST", data=ai_payload)
    print(f"5. /api/ai/explain: status={s}, provenance='{ai_res.get('provenance')}', status='{ai_res.get('status')}'")
    print(f"   recommendation: {ai_res.get('recommendation')[:60]}...")
    print(f"   tradeoffs count: {len(ai_res.get('tradeoffs', []))}")
    print(f"   confidence: {ai_res.get('confidence')}")
    assert s == 200, f"AI explain status is {s}"
    assert "recommendation" in ai_res and "reasoning" in ai_res, "AI explain missing core keys"
    assert isinstance(ai_res.get("tradeoffs"), list), "Tradeoffs must be a list"
    assert ai_res.get("provenance") == "ANALYTICAL INTERPRETATION", "Provenance mismatch"

    # 6. AI Error & Fallback handling with empty / partial payload
    s, ai_empty = make_request("/ai/explain", method="POST", data={})
    print(f"6. /api/ai/explain (empty payload recovery): status={s}, provenance='{ai_empty.get('provenance')}'")
    assert s == 200, "AI explain should gracefully recover and provide fallback on empty payload"

    # 7. Environment Current
    s, env_res = make_request("/environment/current")
    print(f"7. /api/environment/current: status={s}, aqi={env_res.get('aqi')}, source={env_res.get('source')}")
    assert s == 200 and "aqi" in env_res, f"Environment current check failed: {env_res}"

    # 8. Environment Stations
    s, stations = make_request("/environment/stations")
    stations_list = stations if isinstance(stations, list) else stations.get('stations', [])
    print(f"8. /api/environment/stations: status={s}, stations_count={len(stations_list)}")
    assert s == 200 and len(stations_list) > 0, f"Environment stations check failed: {stations}"

    # 9. Experiments Interventions
    s, interventions = make_request("/experiments/interventions")
    interventions_list = interventions if isinstance(interventions, list) else interventions.get('interventions', [])
    print(f"9. /api/experiments/interventions: status={s}, interventions={len(interventions_list)}")
    assert s == 200 and len(interventions_list) > 0, f"Interventions check failed: {interventions}"

    # 10. Scenario Run
    s, scenario_res = make_request("/scenario/run", method="POST", data={"scenario": "morning", "traffic_multiplier": 1.2, "intervention_id": "extend_green_5s_mobility"})
    print(f"10. /api/scenario/run: status={s}, scenario_speed={scenario_res.get('scenario', {}).get('average_speed_kmh')}")
    assert s == 200 and "scenario" in scenario_res, f"Scenario run check failed: {scenario_res}"

    print("\nALL RUNTIME API ENDPOINTS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    run_all_checks()

