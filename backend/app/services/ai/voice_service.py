"""
voice_service.py - Speech-to-Text & Text-to-Speech for Arohan
STT: Groq Whisper API
TTS: Sarvam AI (Indian languages)
"""

import os
import re
import base64
import requests
import logging
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client  = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# ═══════════════════════════════════════════════════════════════════════════════
#  SPEECH TO TEXT — Groq Whisper
# ═══════════════════════════════════════════════════════════════════════════════

def transcribe_audio(audio_file_path: str, language_code: str = "") -> str:
    """
    Transcribes audio to text using Groq Whisper API.
    Supports Hindi, Kannada, English, Hinglish, Kanglish.
    """
    try:
        if not groq_client:
            raise ValueError("GROQ_API_KEY not set in environment")

        logger.info(f"Transcribing audio: {audio_file_path}")

        request_kwargs = {
            "model": "whisper-large-v3",
            "response_format": "text",
        }

        normalized_lang = (language_code or "").strip().lower()
        if normalized_lang.startswith("hi"):
            request_kwargs["language"] = "hi"
            request_kwargs["prompt"] = "This audio is in Hindi or Hinglish. Prefer Devanagari or Roman Hindi words, never Urdu."
        elif normalized_lang.startswith("kn"):
            request_kwargs["language"] = "kn"
            request_kwargs["prompt"] = "This audio is in Kannada or Kanglish. Prefer Kannada or Roman Kannada words, never other scripts."
        elif normalized_lang.startswith("en"):
            request_kwargs["language"] = "en"
            request_kwargs["prompt"] = "This audio is in English. Use only English words."

        with open(audio_file_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=audio_file,
                **request_kwargs
            )

        transcript = transcription.strip()
        logger.info(f"Transcribed: {transcript[:100]}...")
        return transcript

    except Exception as e:
        logger.error(f"Groq Whisper STT failed: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════════
#  TEXT TO SPEECH — Sarvam AI (Indian Languages)
# ═══════════════════════════════════════════════════════════════════════════════

def split_into_chunks(text: str, max_len: int = 450) -> list:
    """
    Split text into chunks max 450 chars each.
    Splits at newlines first (preserves numbered points).
    Falls back to word boundary splitting.
    Never cuts mid-word.
    """
    # Split by newlines first — each numbered point on own line
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    chunks  = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            if current.strip():
                chunks.append(current.strip())
            # If single line itself exceeds max_len, split by words
            if len(line) > max_len:
                words        = line.split()
                word_current = ""
                for word in words:
                    if len(word_current) + len(word) + 1 > max_len:
                        if word_current.strip():
                            chunks.append(word_current.strip())
                        word_current = word + " "
                    else:
                        word_current += word + " "
                if word_current.strip():
                    current = word_current
                else:
                    current = ""
            else:
                current = line + " "
        else:
            current += line + " "

    if current.strip():
        chunks.append(current.strip())

    # Fallback — if no newlines found, split by word boundary
    if not chunks:
        words   = text.split()
        current = ""
        for word in words:
            if len(current) + len(word) + 1 > max_len:
                if current.strip():
                    chunks.append(current.strip())
                current = word + " "
            else:
                current += word + " "
        if current.strip():
            chunks.append(current.strip())

    return chunks if chunks else [text[:max_len]]


def text_to_indian_voice(text: str, language_code: str = "hi-IN") -> bytes:
    """
    Converts text to Indian voice using Sarvam AI TTS.
    Splits long text into chunks to read ALL points completely.
    Supported language codes:
        hi-IN → Hindi / Hinglish
        kn-IN → Kannada / Kanglish
        en-IN → English
    """
    try:
        sarvam_api_key = os.getenv("SARVAM_API_KEY")
        if not sarvam_api_key:
            raise ValueError("SARVAM_API_KEY not set in environment")

        chunks = split_into_chunks(text)
        logger.info(f"TTS: {len(chunks)} chunks for {len(text)} chars")

        url     = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": sarvam_api_key,
            "Content-Type":         "application/json"
        }

        all_audio_bytes = b""

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            payload = {
                "inputs":               [chunk],
                "target_language_code": language_code,
                "speaker":              "anushka",
                "pace":                 1.0,
                "enable_preprocessing": True,
            }

            try:
                response = requests.post(
                    url, json=payload, headers=headers, timeout=25
                )
                response.raise_for_status()

                audio_data      = response.json()["audios"][0]
                audio_bytes     = base64.b64decode(audio_data)
                all_audio_bytes += audio_bytes

                logger.info(
                    f"TTS chunk {i+1}/{len(chunks)}: "
                    f"{len(audio_bytes)} bytes — '{chunk[:50]}'"
                )

            except Exception as chunk_err:
                logger.error(f"TTS chunk {i+1} failed: {chunk_err} — skipping")
                continue

        if not all_audio_bytes:
            raise ValueError("All TTS chunks failed — no audio generated")

        logger.info(f"TTS total: {len(all_audio_bytes)} bytes across {len(chunks)} chunks")
        return all_audio_bytes

    except Exception as e:
        logger.error(f"Sarvam TTS failed: {e}")
        raise
