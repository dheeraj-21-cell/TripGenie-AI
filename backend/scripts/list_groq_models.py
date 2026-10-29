import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

key = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=key)

try:
    models = client.models.list()
    print("AVAILABLE_MODELS:")
    for m in models.data:
        print(f" - {m.id} (owned_by: {m.owned_by})")
except Exception as e:
    print(f"ERROR: {type(e).__name__} - {e}")
