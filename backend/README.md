# TripGenie-AI Backend (Python FastAPI)

This is the high-performance Python FastAPI backend for **TripGenie-AI**, powering structured travel itinerary generation.

---

## Architecture Overview (Phase 1 & Phase 2 Complete)

- **Framework**: FastAPI + Uvicorn with auto-reload
- **Validation**: Pydantic v2 schemas strictly aligned with Skill Wallet specifications
- **Storage**: Local SQLite database (`backend/data/tripgenie.db`) for 100% free offline trip persistence (CRUD)
- **Gazetteer**: 68,811 worldwide cities & countries (`backend/data/places.db`) indexed with SQLite FTS & prefix B-Trees (<2ms latency)
- **AI Engine (Groq Cloud Free Tier)**:
  - **Primary Model**: `llama-3.3-70b-versatile` (Meta LLaMA 3.3 70B, 128k context, strict JSON mode)
  - **Fallback Model**: `llama-3.1-8b-instant` (Meta LLaMA 3.1 8B, high throughput)
  - **Adaptive Mock Fallback**: 100% functional offline mock generator if `GROQ_API_KEY` is not configured, expired, or rate-limited
  - **Zero Paid Subscriptions**: 100% free tier. No credit card or billing setup required.
- **Skill Wallet Output Guarantee**:
  - Trip overview and destination summary
  - Day-by-day itinerary with exact timings (Morning, Afternoon, Evening) and structured activities
  - Suggested attractions, landmarks, and regional dining/food options
  - Itemized estimated cost breakdown and total budget calculation
  - Curated accommodation suggestions tailored to destination and budget tier
  - Commuting & local transit recommendations
  - Practical cultural etiquette and packing tips
  - Clear disclaimer that prices, opening hours, and schedules are estimates (no invented bookings)
  - Full localization in English (`en`), Hindi (`hi`), Spanish (`es`), and French (`fr`)
- **CORS**: Preconfigured for `http://localhost:5173` and `http://127.0.0.1:5173`

---

## Directory Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py       # GET /api/health and POST /api/itinerary/generate
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Environment settings and CORS config
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # TripRequest, TripResponse, DayPlan, DayActivity
│   ├── services/
│   │   ├── __init__.py
│   │   └── mock_generator.py  # Adaptive fallback itinerary generator
│   ├── __init__.py
│   └── main.py                # FastAPI app entry point with CORS middleware
├── .env.example               # Template environment configuration
├── requirements.txt           # Python dependencies
└── README.md
```

---

## Quickstart (Windows PowerShell)

### 1. Activate the Virtual Environment

```powershell
cd D:\TripGenie-AI\backend
.\.venv\Scripts\Activate.ps1
```

*(If script execution is disabled in PowerShell, activate with: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` or directly invoke `.\.venv\Scripts\python.exe`)*

### 2. Install Dependencies (if not already installed)

```powershell
pip install -r requirements.txt
```

### 3. Configure Free API Keys (Optional)

TripGenie-AI works completely out-of-the-box in **Adaptive Mock Mode** and **Local SQLite Storage** without any external keys or network calls. To connect real AI and Cloud Storage:

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `backend/.env` in your text editor and set your free placeholders:
   ```env
   # Free Groq API Key (https://console.groq.com)
   GROQ_API_KEY=your_groq_api_key_placeholder

   # Free Supabase Project (https://database.new)
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_placeholder
   ```
3. Save the file. The backend server automatically detects changes and upgrades from Mock Mode to Live Groq AI (`llama-3.3-70b-versatile`) and Supabase Cloud storage with automatic local SQLite fallback.

*Security Note: Never paste or commit your real API keys or service-role keys. `backend/.env` is strictly excluded by `.gitignore`.*

### 4. Start the FastAPI Development Server

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## Testing the Endpoints

### Health Check:
Open in browser or run in terminal:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get
```

### Interactive Swagger Docs:
Open `http://127.0.0.1:8000/docs` in your browser.

### Test Itinerary Generation:
```powershell
$body = @{
    destination = "Manali"
    startDate = "2026-06-01"
    endDate = "2026-06-04"
    durationDays = 3
    budget = "moderate"
    travelerType = "couple"
    travelersCount = 2
    interests = @("nature", "adventure")
    pace = "balanced"
    language = "en"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/itinerary/generate" -Method Post -Body $body -ContentType "application/json"
```
