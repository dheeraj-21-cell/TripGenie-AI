# 🌍 TripGenie-AI — Personalized Travel Itinerary Planner

**Plan smarter. Travel better. Explore more.**

TripGenie-AI is an AI-powered travel planning application that helps users create personalized multi-day travel plans based on their destination, budget, duration, and preferences.

🌐 **Live Demo:** https://trip-genie-ai-nine.vercel.app/  
💻 **GitHub Repository:** https://github.com/dheeraj-21-cell/TripGenie-AI

## ✨ Features

- **AI-Powered Itinerary Generation:** Generate personalized multi-day travel plans using Groq AI.
- **Global Destination Search:** Search destinations using a local database containing more than 68,000 geographical entries.
- **Budget Planning:** Organize estimated travel expenses into an itemized budget.
- **Daily Travel Plans:** Get structured activities, suggested transport options, and travel tips.
- **Multilingual Interface:** Use the application in English, Hindi, Spanish, and French.
- **Trip Management:** Save, view, edit, and delete saved trips.
- **Day Regeneration:** Regenerate an individual day's itinerary when plans change.
- **Cloud and Local Persistence:** Supabase cloud storage with a local SQLite fallback.
- **Responsive Interface:** A modern, dark-themed interface designed for a smooth user experience.

## 🛠️ Tech Stack

| Component | Technologies |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| AI Integration | Groq API |
| Cloud Database | Supabase (PostgreSQL) |
| Local Database | SQLite |
| Deployment | Vercel, Render |

## 🏗️ Architecture

```text
User
  |
  v
React + Vite Frontend
  |
  v
FastAPI Backend
  |
  +----> Groq AI
  |        |
  |        v
  |    Personalized Itinerary
  |
  +----> Supabase Cloud Database
  |
  +----> SQLite Local Fallback
  |
  v
Frontend Displays the Trip
```

## 🚀 Getting Started

### Prerequisites

Install the following tools before running the project locally:

- Node.js and npm
- Python 3.10 or a compatible version
- Git
- A Groq API key for AI itinerary generation
- A Supabase project for cloud persistence (optional if the local fallback is configured)

### 1. Clone the Repository

```bash
git clone https://github.com/dheeraj-21-cell/TripGenie-AI.git
cd TripGenie-AI
```

### 2. Set Up the Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

**Windows:**

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the environment variables in `backend/.env` according to the project's backend configuration. Keep all API keys and secret credentials private.

Start the backend from the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The backend should be available at:

`http://127.0.0.1:8000`

API documentation:

`http://127.0.0.1:8000/docs`

### 3. Set Up the Frontend

Open another terminal at the project root:

```bash
npm install
```

Create a `.env` file in the project root and configure the backend URL:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open the local URL displayed by Vite, usually:

`http://localhost:5173`

## 🔐 Environment Variables

Configure the required environment variables according to the backend implementation:

- `GROQ_API_KEY` — Groq AI API key
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` — Backend-only Supabase secret
- `VITE_API_URL` — Backend API base URL for the frontend

**Security:** Never commit `.env` files, API keys, service-role credentials, or other secrets to GitHub. Frontend environment variables prefixed with `VITE_` are exposed to the browser, so never put private keys in them.

## 🗺️ Destination Data

The application includes a geographical dataset based on GeoNames data.

GeoNames data is distributed under the **Creative Commons Attribution 4.0 License (CC BY 4.0)**. See the project's `backend/data/PLACES_LICENSING.md` file for attribution and licensing details.

## 🧪 Development Checks

Run the following commands from the project root to check the frontend:

```bash
npm run lint
npm run build
```

Run backend tests using the test configuration and dependencies provided by the project.

## ☁️ Deployment

- **Frontend:** Deployed on Vercel
- **Backend:** Deployed on Render
- **Database:** Supabase with local SQLite fallback

The free Render service may take some time to respond after periods of inactivity.

## 🔮 Future Enhancements

- Integration with live weather information
- Interactive maps and route visualization
- More detailed travel cost estimates
- User authentication and personalized profiles
- Downloadable PDF itineraries

## 👨‍💻 Author

**Dheeraj**

GitHub: [@dheeraj-21-cell](https://github.com/dheeraj-21-cell)

---

⭐ If you find this project interesting, consider starring the repository!

**TripGenie-AI — Your next adventure starts here.**
