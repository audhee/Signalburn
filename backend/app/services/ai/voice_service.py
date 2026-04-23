import os
import requests
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# --- Gemini 2.0 Flash: Speech to Text (Free tier, new google-genai SDK) ---

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribes audio file to text using Google Gemini 2.0 Flash.
    Uses the new google-genai SDK (v1 API — not the deprecated google.generativeai).
    Supports Indian languages: Hindi, Kannada, Telugu, Tamil, Malayalam, English.
    """
    try:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")

        client = genai.Client(api_key=gemini_api_key)

        # Determine MIME type from file extension
        ext = audio_file_path.split(".")[-1].lower()
        mime_map = {
            "m4a":  "audio/mp4",
            "mp4":  "audio/mp4",
            "mp3":  "audio/mpeg",
            "wav":  "audio/wav",
            "ogg":  "audio/ogg",
            "webm": "audio/webm",
        }
        mime_type = mime_map.get(ext, "audio/mp4")

        with open(audio_file_path, "rb") as f:
            audio_bytes = f.read()

        prompt = (
            "Listen to this audio carefully. "
            "Transcribe EXACTLY what is spoken — in the original language "
            "(Hindi, Kannada, Telugu, Tamil, Malayalam, or English). "
            "Output ONLY the spoken words in plain text. "
            "No translation, no formatting, no explanation."
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                prompt,
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            ],
        )

        transcript = response.text.strip()
        logger.info(f"Gemini STT transcription: {transcript[:100]}")
        return transcript

    except Exception as e:
        logger.error(f"Gemini transcription failed: {e}")
        raise


# --- Sarvam AI: Text to Indian Voice ---


def text_to_indian_voice(text: str, language_code: str = "hi-IN") -> bytes:
    """
    Converts text to natural Indian voice using Sarvam AI TTS.
    Returns audio bytes.

    Supported language codes:
        hi-IN  → Hindi
        kn-IN  → Kannada
        ta-IN  → Tamil
        te-IN  → Telugu
        ml-IN  → Malayalam
        en-IN  → English (Indian accent)
    """
    try:
        sarvam_api_key = os.getenv("SARVAM_API_KEY")
        if not sarvam_api_key:
            raise ValueError("SARVAM_API_KEY not set in environment")

        url = "https://api.sarvam.ai/text-to-speech"

        payload = {
            "inputs": [text],
            "target_language_code": language_code,
            "speaker": "meera",       # natural female Indian voice
            "pace": 1.0,
            "enable_preprocessing": True,
        }

        headers = {
            "api-subscription-key": sarvam_api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        # Sarvam returns base64 encoded audio
        import base64
        audio_data = response.json()["audios"][0]
        audio_bytes = base64.b64decode(audio_data)

        logger.info(f"Sarvam TTS successful for language: {language_code}")
        return audio_bytes

    except Exception as e:
        logger.error(f"Sarvam TTS failed: {e}")
        raise