import sys
from app.services.simulation.service import run_metrics_workflow


if __name__ == "__main__":
    result = run_metrics_workflow(steps=100)

    print("\n========== MAHALLAMIND SUMO TEST ==========")

    for key, value in result.items():
        print(f"{key}: {value}")

    assert result.get("mean_completed_vehicle_waiting_seconds") is not None, "Completed-trip wait missing!"
    assert result.get("mean_active_vehicle_waiting_seconds") is not None, "Active-vehicle wait missing!"

    print("===========================================")