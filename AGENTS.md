# AGENTS.md

## Project purpose
This repo is a hackathon MVP for MahallaMind, a neighborhood mobility intelligence platform. The product combines a Leaflet map, a FastAPI backend, and SUMO-based traffic simulation to analyze local traffic-light interventions and explain the recommended choice.

## Start here
- Product overview: [README.md](README.md)
- Frontend app: [frontend/package.json](frontend/package.json)
- Backend app: [backend/app/main.py](backend/app/main.py)
- Backend tests: [backend/test_api.py](backend/test_api.py)

## Critical environment setup
- SUMO must be installed and `SUMO_HOME` must point to the SUMO install root.
- Typical Windows setup in PowerShell:
  - `$env:SUMO_HOME='C:/Users/user/Downloads/sumo-win64-1.27.1/sumo-1.27.1'`
- If the backend cannot find SUMO, fix the environment before debugging unrelated application logic.

## Commands
### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

### Tests
```bash
cd backend
pytest
```

## Architecture conventions
- Frontend is React + Vite + Leaflet and lives under [frontend/src](frontend/src).
- Backend is FastAPI and lives under [backend/app](backend/app).
- Traffic logic and optimization are centralized in [backend/app/services/sumo_runner.py](backend/app/services/sumo_runner.py).
- AI explanation logic is kept modular in [backend/app/services/ai.py](backend/app/services/ai.py) and should gracefully fall back when provider credentials are missing.
- Keep optimization deterministic and explainable; avoid black-box behavior or opaque UI claims.

## Code-change guidance
- Prefer small, focused changes that preserve the real SUMO-driven data flow.
- When changing simulation output or candidate ranking, validate with backend tests before polishing the UI.
- When updating map visuals, keep the map grounded in the actual neighborhood context instead of using synthetic overlays or artificial analysis meshes.
- If a fix touches both frontend and backend, verify the API contract stays consistent.

## Common pitfalls
- Missing or stale `SUMO_HOME` causes simulation failures unrelated to frontend code.
- Port conflicts and stale local servers can be confusing; prefer checking the active app ports before debugging app logic.
- Do not treat AI output as authoritative; it should explain and contextualize the deterministic optimization result.

## Useful links
- [README.md](README.md)
- [backend/app/main.py](backend/app/main.py)
- [backend/app/services/sumo_runner.py](backend/app/services/sumo_runner.py)
- [backend/app/services/ai.py](backend/app/services/ai.py)
- [frontend/src/App.jsx](frontend/src/App.jsx)
