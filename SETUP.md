# MahallaMind — Local Setup Instructions

**Last Updated**: 2026-08-15

This guide walks through setting up MahallaMind for local development and testing.

---

## Prerequisites

### System Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18+)
- **RAM**: 4GB minimum (8GB recommended for SUMO simulations)
- **Disk**: 2GB free space

### Software Requirements
- **Python**: 3.14+ (for backend)
- **Node.js**: 20+ (for frontend)
- **SUMO**: 1.27.1+ (optional, for real traffic simulation)
- **Git**: For version control

### Verify Installations
```bash
# Check Python
python --version  # Should show 3.14 or higher

# Check Node.js
node --version    # Should show 20 or higher
npm --version     # Should show 10 or higher

# Check SUMO (optional)
sumo --version    # If installed
```

---

## Quick Start (5 minutes)

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/mahallamind.git
cd mahallamind
```

### Step 2: Setup Backend
```bash
cd backend
python -m venv .venv

# Windows:
.\.venv\Scripts\activate.bat

# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### Step 3: Setup Frontend
```bash
cd ../frontend
npm install
```

### Step 4: Run Locally
```bash
# Terminal 1: Backend
cd backend
.\.venv\Scripts\activate.bat  # Windows
# OR: source .venv/bin/activate  # macOS/Linux
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev -- --host 0.0.0.0
```

### Step 5: Open Browser
Navigate to: `http://localhost:5173`

---

## Detailed Setup Guide

### Backend Setup (Detailed)

#### 1. Create Python Virtual Environment
```bash
cd backend
python -m venv .venv
```

#### 2. Activate Virtual Environment
**Windows (PowerShell)**:
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**:
```cmd
.\.venv\Scripts\activate.bat
```

**macOS/Linux**:
```bash
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

#### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected packages**:
- fastapi — Web framework
- uvicorn — ASGI server
- python-dotenv — Environment variable management
- traci, sumolib — SUMO Python bindings
- google-generativeai — Optional AI library
- pydantic-settings — Configuration management
- psutil — System utilities

#### 4. Create Environment File
Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env  # or copy .env.example .env on Windows
```

Then edit `.env`:
```env
# Required: Point to your SUMO installation
SUMO_HOME=C:/Users/YourUser/Downloads/sumo-win64-1.27.1/sumo-1.27.1

# Optional: Use custom SUMO scenario
# SUMO_SCENARIO_PATH=backend/sim/mahalla-scenario

# Optional: Add your Gemini API key for AI explanations
# GEMINI_API_KEY=your-api-key-here
# GOOGLE_API_KEY=your-api-key-here
# AI_MODEL=gemini-2.0-flash
```

**Note**: Without `SUMO_HOME`, the backend will work with fallback data but simulations won't run.

#### 5. Test Backend
```bash
cd backend
python -m pytest test_api.py -v
python -m pytest test_sumo_runner.py -v
```

#### 6. Start Backend Server
```bash
cd backend
python -m uvicorn app.main:app --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Test endpoints**:
```bash
# In another terminal:
curl http://localhost:8000/api/health
curl http://localhost:8000/api/mahalla
```

---

### Frontend Setup (Detailed)

#### 1. Install Node Dependencies
```bash
cd frontend
npm install
```

**Expected**: Creates `node_modules/` folder (~400MB).

#### 2. Verify Installation
```bash
npm --version    # Should show version 10+
node --version   # Should show version 20+
```

#### 3. Build for Production (Test)
```bash
npm run build
```

**Expected output**:
- `dist/` folder created
- Build time: ~200-300ms
- Output: `index.html`, `CSS`, `JavaScript` files

#### 4. Start Development Server
```bash
npm run dev -- --host 0.0.0.0
```

**Expected output**:
```
VITE v8.2.0  ready in 123 ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

#### 5. Open in Browser
Navigate to: `http://localhost:5173`

**Expected**: 
- Map loads with neighborhood
- "Analyze" button works
- "Optimize" button works (if backend is running)

---

## Environment Variables Explained

### Backend Environment Variables

| Variable | Purpose | Required | Default | Example |
|----------|---------|----------|---------|---------|
| `SUMO_HOME` | Path to SUMO installation | Optional* | None | `C:/sumo-win64-1.27.1/sumo-1.27.1` |
| `SUMO_SCENARIO_PATH` | Path to SUMO scenario files | No | `backend/sim/mahalla-scenario` | Same |
| `GEMINI_API_KEY` | Google Gemini API key | No | None | `AQ.Ab8RN...` |
| `GOOGLE_API_KEY` | Alternative Google API key | No | None | `AIza...` |
| `AI_MODEL` | AI model to use | No | `gemini-2.0-flash` | `gemini-pro` |

*`SUMO_HOME` is optional. Without it, simulations will use fallback data.

### Finding SUMO_HOME

After installing SUMO, find the path:

**Windows**:
```powershell
# SUMO usually installs to:
C:\Users\YourUsername\Downloads\sumo-win64-1.27.1\sumo-1.27.1

# Verify with:
dir "C:\Users\YourUsername\Downloads\sumo-win64-1.27.1\sumo-1.27.1\bin\sumo.exe"
```

**macOS**:
```bash
# SUMO usually installs to:
/opt/sumo-1.27.1

# Verify with:
ls /opt/sumo-1.27.1/bin/sumo
```

**Linux**:
```bash
# Install via package manager:
sudo apt-get install sumo sumo-tools sumo-doc

# Then find:
which sumo
```

---

## Running the Full Application

### Method 1: Two Terminal Windows (Development)

**Terminal 1 - Backend**:
```bash
cd backend
source .venv/bin/activate  # or .\.venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

**Browser**: http://localhost:5173

### Method 2: Using Process Manager

**For Windows (PowerShell)**:
```powershell
# Install PM2
npm install -g pm2

# Start both services
pm2 start backend/.venv/Scripts/python.exe -- -m uvicorn app.main:app --port 8000
pm2 start frontend/node_modules/.bin/vite -- --host
```

**For macOS/Linux**:
```bash
# Install PM2
npm install -g pm2

# Start services
pm2 start backend/.venv/bin/python -- -m uvicorn app.main:app --port 8000
pm2 start 'cd frontend && npm run dev'

# Monitor
pm2 logs
```

---

## Testing

### Unit Tests (Backend)
```bash
cd backend
python -m pytest test_api.py -v
python -m pytest test_sumo_runner.py -v
python -m pytest test_insights.py -v
python -m pytest test_mahalla_context.py -v
```

### Linting (Frontend)
```bash
cd frontend
npm run lint
```

### Integration Test (Manual)
1. Start backend and frontend (see "Running the Full Application")
2. Open `http://localhost:5173` in browser
3. Test these flows:

**Test 1: Offline Mode**
- Stop backend server
- Refresh browser → Should show fallback map
- Map should work without backend

**Test 2: Analyze**
- Start backend
- Refresh browser
- Click "Analyze" button
- Metrics should appear in sidebar
- Map should show baseline data

**Test 3: Optimize**
- Click "Optimize" button
- Wait 30-60 seconds (if SUMO is running)
- "Candidates" section should show 7 interventions
- "Recommended" should highlight the best one

**Test 4: Scenario Switching**
- Click "Scenario" dropdown
- Select "morning", "midday", or "evening"
- Click "Analyze" again
- Metrics should change based on scenario

**Test 5: Language Toggle**
- Click language flag (top right)
- UI should switch to Russian
- Click again → Switch back to English

---

## Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: 
```bash
# Ensure venv is activated
source .venv/bin/activate  # macOS/Linux
# OR
.\.venv\Scripts\activate.bat  # Windows

# Reinstall requirements
pip install -r requirements.txt
```

---

### Backend Won't Connect to SUMO

**Error**: `OSError: SUMO_HOME environment variable not set`

**Solution**:
```bash
# Set SUMO_HOME in .env file
SUMO_HOME=C:/Users/YourUser/Downloads/sumo-win64-1.27.1/sumo-1.27.1

# Or set as system environment variable and restart terminal
# Windows: setx SUMO_HOME "C:/path/to/sumo"
# macOS/Linux: export SUMO_HOME=/path/to/sumo
```

Without SUMO, simulations use fallback data — app still works!

---

### Frontend Won't Build

**Error**: `npm ERR! code ERESOLVE`

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json  # macOS/Linux
# OR
rmdir /s node_modules ; del package-lock.json  # Windows

npm install
```

---

### Port 8000 (Backend) or 5173 (Frontend) Already in Use

**Solution**: 
```bash
# Change backend port:
python -m uvicorn app.main:app --port 8001

# Change frontend port:
npm run dev -- --port 5174
```

---

### API Call Fails with CORS Error

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**: 
CORS is already enabled in backend, but make sure:
1. Backend is running on `http://localhost:8000`
2. Frontend is running on `http://localhost:5173`
3. Browser console shows the actual error

---

## Next Steps

### After Successful Local Setup
1. ✅ Local development working
2. → Follow `DEPLOYMENT.md` for production setup
3. → Read `DEMO_GUIDE.md` for demonstration walkthrough
4. → Explore `AGENTS.md` for architecture details

### Ready to Deploy?
See `GITHUB_AND_DEPLOYMENT.md` for:
- GitHub upload checklist
- Frontend hosting (Netlify, Vercel, etc.)
- Backend deployment (Railway, VPS, etc.)

---

## Getting Help

- **Setup Issues**: Check troubleshooting section above
- **Architecture Questions**: See `AGENTS.md`
- **API Documentation**: See `DEPLOYMENT.md` → API Endpoints
- **Demo Walkthrough**: See `DEMO_GUIDE.md`

---

## Quick Reference

```bash
# Backend startup (one command)
cd backend && python -m venv .venv && .\.venv\Scripts\activate.bat && pip install -r requirements.txt && python -m uvicorn app.main:app --reload

# Frontend startup (one command)
cd frontend && npm install && npm run dev -- --host 0.0.0.0

# Test backend
curl http://localhost:8000/api/health

# Test frontend
open http://localhost:5173
```

---

*Setup guide for MahallaMind MVP*  
*For latest instructions, see the GitHub repository*
