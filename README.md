# TripGenie-AI: Intelligent Autonomous Travel Planner

TripGenie-AI is an agentic, AI-powered travel itinerary planner built with **React (Vite + Tailwind CSS)** and a high-performance **Python FastAPI backend**. It generates structured, itemized, and culturally grounded multi-day travel itineraries worldwide.

---

## Key Features

- **Global Destination Autocomplete**: Search across **68,813 worldwide cities, regions, and countries** powered by an embedded local SQLite gazetteer ([GeoNames CC BY 4.0](backend/data/PLACES_LICENSING.md)). Zero external API calls, sub-2ms query latency. Free text entry is also fully supported for off-the-beaten-path locations.
- **Fast LPU AI Generation (Groq Cloud)**: Queries `llama-3.3-70b-versatile` in strict JSON mode for sub-2-second complete multi-day itineraries, including daytime sequencing, local transport recommendations, itemized budget breakdowns, and safety tips.
- **Dual-Engine Persistence (Cloud + Local Fallback)**:
  - **Primary**: Supabase Cloud PostgreSQL with Row-Level Security (RLS) and multi-tenant isolation.
  - **Automatic Fallback**: Local SQLite database (`backend/data/tripgenie.db`). If the internet drops or Supabase is unconfigured, saving and loading continue seamlessly without errors.
- **Client-Side Guest Session Isolation**: Unauthenticated visitors are automatically assigned an isolated persistent UUID (`guest-<uuid>`), preventing visitors from viewing or modifying each other's itineraries.
- **Multilingual Support**: Real-time localization across 4 languages: English (`en`), Hindi (`hi`), Spanish (`es`), and French (`fr`).
- **Strictly ₹0 Budget / Free Tiers**: Requires zero paid subscriptions, zero credit cards, and zero billing setup.

---

## Architecture Overview

```text
TripGenie-AI/
├── src/                          # React + Vite + Tailwind CSS frontend
│   ├── components/               # Trip planner form, cinematic background, modals
│   ├── locales/                  # i18n dictionaries (en, hi, es, fr)
│   └── utils/                    # Guest identity manager, date/cost formatters
├── backend/                      # Python FastAPI backend
│   ├── app/
│   │   ├── api/endpoints.py      # Health, itinerary generation, destination search, trip CRUD
│   │   ├── core/config.py        # Environment variables & CORS settings
│   │   ├── db/storage.py         # Dual-engine storage adapter (Supabase + SQLite fallback)
│   │   ├── models/schemas.py     # Pydantic v2 validation models
│   │   └── services/             # Groq AI service, Places gazetteer, Mock fallback
│   ├── data/
│   │   ├── places.db             # 68k GeoNames gazetteer database (CC BY 4.0)
│   │   └── PLACES_LICENSING.md   # GeoNames attribution and licensing terms
│   ├── supabase_schema.sql       # Idempotent Supabase PostgreSQL schema with RLS
│   ├── requirements.txt          # Python dependencies
│   └── .env.example              # Sanitized configuration template (placeholders only)
└── .gitignore                    # Watertight exclusion of secrets, .venv, node_modules, and DBs
```

---

## Getting Started

### 1. Prerequisites

- **Node.js**: v18 or later
- **Python**: v3.10 or later
- **Git**

---

### 2. Backend Setup

1. **Navigate to the backend directory and activate your virtual environment**:
   ```bash
   cd backend
   python -m venv .venv
   ```
   - **Windows PowerShell**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     source .venv/bin/activate
     ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Open `backend/.env` and insert your free keys (never commit this file):
   ```env
   # Server Configuration
   ENVIRONMENT=development
   DEBUG=True
   CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

   # Groq API Key (Free tier at https://console.groq.com)
   # Leave blank to use the built-in offline mock generator
   GROQ_API_KEY=gsk_your_groq_api_key_placeholder

   # Optional Unsplash Key (Free tier at https://unsplash.com/developers)
   UNSPLASH_ACCESS_KEY=your_unsplash_key_placeholder

   # Supabase Configuration (Free tier at https://database.new)
   # Leave blank to persist trips locally in SQLite (backend/data/tripgenie.db)
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret-key-placeholder
   ```

4. **(Optional) Configure Supabase Cloud**:
   - Create a free project at [database.new](https://database.new).
   - In your Supabase Dashboard, open **SQL Editor**, paste the contents of `backend/supabase_schema.sql`, and click **Run**.
   - Under **Project Settings > API**, copy your **Project URL** and **`service_role` secret key** into `backend/.env`.

5. **Start the Backend Server**:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend will be live at `http://127.0.0.1:8000`. Test health at `http://127.0.0.1:8000/api/health`.

---

### 3. Frontend Setup

1. **In the root directory, install npm packages**:
   ```bash
   npm install
   ```

2. **Run the Vite development server**:
   ```bash
   npm run dev
   ```
   The application will be accessible at `http://localhost:5173`.

---

### 4. Running Quality & Verification Checks

```bash
# 1. Run backend unit & integration tests (29 tests)
python -m pytest backend/tests/test_api.py -v

# 2. Run frontend lint check
npm run lint

# 3. Run production build
npm run build
```

---

## Security Model & Data Privacy

- **Zero Secret Exposure**: `.env` and `*.env` files are strictly excluded by `.gitignore`. The frontend contains no database keys or secrets.
- **Tenant Isolation**: Each user or guest visitor is segregated by client-side guest UUID or authenticated Supabase user ID. Cross-tenant access attempts receive `403 Forbidden`.
- **Public PostgREST Access Revoked**: In `backend/supabase_schema.sql`, all table permissions for the public `anon` role are explicitly revoked. Direct unauthenticated REST queries cannot read, modify, or delete stored trips.

---

## License

- Code: MIT License
- Geographic Data: [GeoNames](https://www.geonames.org/) under [Creative Commons Attribution 4.0 License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). See [backend/data/PLACES_LICENSING.md](backend/data/PLACES_LICENSING.md).
