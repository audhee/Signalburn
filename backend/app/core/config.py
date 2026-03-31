import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    def __init__(self):
        # Configure the SDK. Ensure you have GEMINI_API_KEY in your .env file
        if self.GEMINI_API_KEY:
            genai.configure(api_key=self.GEMINI_API_KEY)

settings = Settings()
