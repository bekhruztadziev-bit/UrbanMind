# MahallaMind Deployment Guide

## Quick Start (Local Development)

### Prerequisites
- Python 3.14+
- Node.js 20+ with npm
- SUMO 1.27.1 installed
- Git

### 1. Clone & Setup Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Required
SUMO_HOME=C:/Users/user/Downloads/sumo-win64-1.27.1/sumo-1.27.1

# Optional: Override default scenario
# SUMO_SCENARIO_PATH=path/to/custom/scenario.sumocfg

# Optional: AI explanation layer
# GEMINI_API_KEY=your-gemini-api-key
# AI_MODEL=gemini-2.0-flash
```

### 3. Start Backend

```bash
cd backend
set SUMO_HOME=C:/Users/user/Downloads/sumo-win64-1.27.1/sumo-1.27.1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at `http://localhost:8000/api`

### 4. Setup & Start Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Frontend will be available at `http://localhost:5173`

---

## Architecture Overview

```
MahallaMind/
├── backend/                          # FastAPI server
│   ├── app/
│   │   ├── main.py                  # API endpoints
│   │   ├── services/
│   │   │   ├── sumo_runner.py       # SUMO simulation & optimization
│   │   │   ├── ai.py                # Explanation layer
│   │   │   ├── mahalla_data.py      # Neighborhood context
│   │   │   ├── insights.py          # Text generation
│   │   │   └── [others]
│   ├── sim/mahalla-scenario/        # SUMO scenario files
│   ├── requirements.txt             # Python dependencies
│   └── test_*.py                    # Backend tests
│
├── frontend/                         # Vite + React app
│   ├── src/
│   │   ├── App.jsx                  # Main dashboard
│   │   ├── api.js                   # Backend API client
│   │   ├── App.css                  # Styling
│   │   └── [assets/components]
│   ├── package.json                 # Node dependencies
│   ├── vite.config.js               # Build config
│   └── dist/                        # Production build output
│
├── README.md                        # Product overview
├── AGENTS.md                        # Development context
├── DEMO_GUIDE.md                    # Demo instructions
└── [this file]
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Root info |
| `/api/health` | GET | Service health check |
| `/api/mahalla` | GET | Neighborhood data (roads, intersections, facilities) |
| `/api/metrics` | POST | Run baseline simulation |
| `/api/optimize` | POST | Compare interventions and return best recommendation |
| `/api/summary` | GET | Product positioning text |

### Example Requests

**Health check:**
```bash
curl http://localhost:8000/api/health
```

**Get neighborhood data:**
```bash
curl http://localhost:8000/api/mahalla
```

**Run simulation:**
```bash
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{"steps": 300, "scenario": "midday"}'
```

**Optimize:**
```bash
curl -X POST http://localhost:8000/api/optimize \
  -H "Content-Type: application/json" \
  -d '{"steps": 300, "scenario": "morning"}'
```

---

## Production Deployment Checklist

### Backend Deployment

- [ ] SUMO installed and `SUMO_HOME` verified on deployment machine
- [ ] Python 3.14+ installed
- [ ] `.env` file configured with production values
- [ ] Database/logging setup (if adding persistence)
- [ ] Start with a process manager (systemd, supervisord, PM2)
- [ ] Use a production ASGI server (Gunicorn, Hypercorn, Daphne)
- [ ] Enable CORS for your frontend domain
- [ ] Set up monitoring/alerting for backend health
- [ ] Configure log aggregation
- [ ] Test `/api/health` endpoint from deployment network

**Example production startup:**
```bash
cd backend
gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend Deployment

- [ ] Run `npm run build` to generate production bundle
- [ ] Serve `dist/` folder with a static web server (Nginx, Apache, S3+CloudFront)
- [ ] Set API proxy to point to production backend
- [ ] Enable gzip compression
- [ ] Set cache headers on immutable assets
- [ ] Configure CSP headers (OpenStreetMap, Leaflet CDN)
- [ ] Enable HTTPS/TLS

**Example Nginx config snippet:**
```nginx
server {
  listen 443 ssl http2;
  server_name mahalla.example.com;

  root /var/www/mahallamind/dist;
  index index.html;

  location /api {
    proxy_pass http://backend:8000/api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  location ~* \.(js|css|png|jpg|gif|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }

  location / {
    try_files $uri /index.html;
  }
}
```

---

## Scaling Considerations

### Simulation Bottleneck
- **Current**: Single SUMO process per optimization request (~30-60 seconds per run)
- **Improvement**: Queue-based job system (Celery, RQ) for parallel optimizations
- **Monitoring**: Track simulation job queue depth and completion time

### Data Caching
- Cache `/api/mahalla` results (neighborhood data doesn't change frequently)
- Cache baseline metrics for a given scenario for 1-5 minutes
- Invalidate on demand if input data changes

### Database Integration (Future)
- Store optimization results and explanations for audit trail
- Enable historical comparison ("what was recommended in June?")
- Integrate real sensor data (if available) to validate simulation vs. reality

---

## Testing

### Backend Tests
```bash
cd backend
pytest test_api.py -v
pytest test_sumo_runner.py -v
```

### Frontend Build Validation
```bash
cd frontend
npm run build
npm run lint
```

### Manual Integration Test
1. Start backend: `python -m uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Open browser: `http://localhost:5173`
4. Click **Analyze** → verify metrics appear
5. Click **Optimize** → verify candidates and recommendation
6. Switch language to Russian → verify translation
7. Open FAQ page → verify content
8. Offline mode: Stop backend, refresh frontend → verify fallback data

---

## Monitoring & Logging

### Key Metrics to Track
- **Backend response times**: `/api/metrics` and `/api/optimize` latency
- **Simulation completion rate**: % of optimizations that complete successfully
- **Error rates**: Backend 5xx errors, SUMO simulation failures
- **User engagement**: Page views, scenario selections, optimization runs

### Log Aggregation
Example using Python logging:
```python
import logging
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  handlers=[
    logging.FileHandler('mahallamind.log'),
    logging.StreamHandler()
  ]
)
```

---

## Troubleshooting

### "SUMO_HOME is not set"
- Verify environment variable: `echo $SUMO_HOME` (Linux/Mac) or `echo %SUMO_HOME%` (Windows)
- Ensure path exists: `ls $SUMO_HOME/bin/sumo` (or `.exe` on Windows)

### "SUMO network file not found"
- Check scenario path: `backend/sim/mahalla-scenario/osm.net.xml.gz` should exist
- Ensure SUMO scenario was built correctly

### "Backend unavailable" in frontend
- Check if backend is running: `curl http://localhost:8000/api/health`
- Verify CORS is enabled (FastAPI middleware in `main.py`)
- Check network connectivity if not on localhost

### Slow simulation times
- SUMO is I/O and CPU intensive
- Reduce `steps` parameter (default 300) to speed up for testing
- Consider upgrading to a machine with more cores for production

---

## Production Hardening

- [ ] Add rate limiting to API endpoints
- [ ] Implement request authentication (optional but recommended for shared deployments)
- [ ] Validate all input parameters (scenario, steps, etc.)
- [ ] Add request/response logging for audit trail
- [ ] Set up alerts for:
  - Backend crashes
  - SUMO simulation failures
  - API response time > 5 minutes
  - Error rate > 1%

---

## License & Credits

**MahallaMind** is a hackathon MVP developed for neighborhood mobility intelligence.

- **Map & GIS**: OpenStreetMap, Leaflet, react-leaflet
- **Simulation**: SUMO (Simulation of Urban Mobility)
- **Framework**: React, Vite, FastAPI
- **AI**: Google Gemini (optional explanation layer)

---

## Support & Feedback

For issues, feature requests, or deployment help:
- Check AGENTS.md for architecture context
- Review DEMO_GUIDE.md for usage patterns
- Inspect backend logs for simulation errors
- Validate frontend console (F12) for client-side errors

---

*Last updated: 2026-08-15*
*Deployment guide for MahallaMind MVP*
