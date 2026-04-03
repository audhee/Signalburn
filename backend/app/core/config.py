import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")

    def __init__(self):
        if self.GEMINI_API_KEY:
            genai.configure(api_key=self.GEMINI_API_KEY)

settings = Settings()