from app.services.sumo_runner import run_simulation


if __name__ == "__main__":
    result = run_simulation(steps=100)

    print("\n========== MAHALLAMIND SUMO TEST ==========")

    for key, value in result.items():
        print(f"{key}: {value}")

    print("===========================================")