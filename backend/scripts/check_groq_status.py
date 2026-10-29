import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

key = os.getenv("GROQ_API_KEY", "")
is_configured = bool(key and len(key.strip()) > 8)

print(f"ENV_PATH_EXISTS: {env_path.exists()}")
print(f"IS_CONFIGURED: {is_configured}")
if is_configured:
    print(f"KEY_LENGTH: {len(key.strip())}")
    print(f"STARTS_WITH_GSK: {key.strip().startswith('gsk_')}")
else:
    print("STATUS: GROQ_API_KEY is not configured (empty or absent).")
