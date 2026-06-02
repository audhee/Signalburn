import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("SARVAM_API_KEY")
print("Sarvam key found:", key[:15] if key else "NOT FOUND")

url = "https://api.sarvam.ai/text-to-speech"

payload = {
    "inputs": ["Hello, this is a test from Arohan app."],
    "target_language_code": "en-IN",
    "speaker": "meera",
    "pace": 1.0,
    "enable_preprocessing": True,
}

headers = {
    "api-subscription-key": key,
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print("Status code:", response.status_code)
print("Response:", response.text[:200])

if response.status_code == 200:
    audio_data = response.json()["audios"][0]
    audio_bytes = base64.b64decode(audio_data)
    print("Audio bytes received:", len(audio_bytes))
    print("✅ Sarvam TTS is working!")
else:
    print("❌ Sarvam TTS failed!")