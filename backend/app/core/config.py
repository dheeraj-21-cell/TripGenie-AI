import os
import json
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Automatically look for .env in backend directory or project root
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BACKEND_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()  # Fallback to root or default environment

class Settings:
    PROJECT_NAME: str = "TripGenie-AI Backend"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # CORS origins: defaults to local Vite frontend ports
    _raw_cors = os.getenv("CORS_ORIGINS", '["http://localhost:5173", "http://127.0.0.1:5173"]')
    try:
        CORS_ORIGINS: List[str] = json.loads(_raw_cors) if _raw_cors.strip().startswith("[") else [o.strip() for o in _raw_cors.split(",")]
    except Exception:
        CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # External APIs (100% Free Tier - Zero payment or subscriptions required)
    @property
    def GROQ_API_KEY(self) -> Optional[str]:
        key = os.getenv("GROQ_API_KEY")
        if (not key or not key.strip()) and env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            key = os.getenv("GROQ_API_KEY")
        return key.strip() if (key and key.strip()) else None

    @property
    def UNSPLASH_ACCESS_KEY(self) -> Optional[str]:
        key = os.getenv("UNSPLASH_ACCESS_KEY")
        if (not key or not key.strip()) and env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            key = os.getenv("UNSPLASH_ACCESS_KEY")
        return key.strip() if (key and key.strip()) else None

    @property
    def is_groq_available(self) -> bool:
        k = self.GROQ_API_KEY
        return bool(k and len(k) > 8)

    # Supabase Configuration (100% Free Plan - https://supabase.com)
    @property
    def SUPABASE_URL(self) -> Optional[str]:
        val = os.getenv("SUPABASE_URL")
        if (not val or not val.strip()) and env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            val = os.getenv("SUPABASE_URL")
        return val.strip() if (val and val.strip()) else None

    @property
    def SUPABASE_ANON_KEY(self) -> Optional[str]:
        val = os.getenv("SUPABASE_ANON_KEY")
        if (not val or not val.strip()) and env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            val = os.getenv("SUPABASE_ANON_KEY")
        return val.strip() if (val and val.strip()) else None

    @property
    def SUPABASE_SERVICE_ROLE_KEY(self) -> Optional[str]:
        val = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if (not val or not val.strip()) and env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            val = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        return val.strip() if (val and val.strip()) else None

    @property
    def is_supabase_available(self) -> bool:
        url = self.SUPABASE_URL
        key = self.SUPABASE_ANON_KEY or self.SUPABASE_SERVICE_ROLE_KEY
        return bool(url and key and url.startswith("https://") and len(key) > 20)

settings = Settings()
