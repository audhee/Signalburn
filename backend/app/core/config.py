import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv

# Explicitly load .env from backend directory (reliable on Windows)
_env_path = Path(__file__).parent.parent.parent / '.env'
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    # Fallback: search upward from CWD
    load_dotenv(find_dotenv(usecwd=True))

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    def __init__(self):
        if self.GEMINI_API_KEY:
            genai.configure(api_key=self.GEMINI_API_KEY)

settings = Settings()