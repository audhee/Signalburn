"""
voice_service.py - Speech-to-Text for Arohan
Uses Groq Whisper API — free tier, no quota issues
"""

import os
import logging

from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # ensure .env is loaded before reading GROQ_API_KEY

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe an audio file to text using Groq Whisper.

    Supports Hindi, Kannada, Telugu, Tamil, Malayalam, English,
    as well as code-mixed varieties (Hinglish, Kanglish).

    Args:
        audio_file_path: Path to the audio file (.m4a, .mp3, .wav, etc.)

    Returns:
        Transcribed text in the original language.
    """
    if not groq_client:
        raise ValueError("GROQ_API_KEY not set in environment")

    logger.info("Processing audio: %s", audio_file_path)

    with open(audio_file_path, "rb") as audio_file:
        transcription = groq_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file,
            response_format="text",
        )

    transcript = transcription.strip()
    logger.info("Transcribed (%d chars): %s", len(transcript), transcript[:120])
    return transcript