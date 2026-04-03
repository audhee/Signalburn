import os
import requests
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# --- Whisper: Speech to Text ---

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribes audio file to text using OpenAI Whisper.
    Supports all Indian languages automatically.
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                # No language specified — Whisper auto-detects Indian languages
            )

        logger.info(f"Whisper transcription: {transcript.text[:100]}")
        return transcript.text

    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
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