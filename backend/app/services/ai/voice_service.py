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

KANNADA_SCRIPT_PATTERN = re.compile(r"[\u0C80-\u0CFF]")
HINDI_SCRIPT_PATTERN = re.compile(r"[\u0900-\u097F]")


def _has_expected_script(text: str, normalized_lang: str) -> bool:
    value = (text or "").strip()
    if normalized_lang.startswith("kn"):
        return bool(KANNADA_SCRIPT_PATTERN.search(value))
    if normalized_lang.startswith("hi"):
        return bool(HINDI_SCRIPT_PATTERN.search(value))
    return bool(value)


def _normalize_short_locked_transcript(transcript: str, normalized_lang: str) -> str:
    value = (transcript or "").strip()
    if not value:
        return value

    normalized_value = re.sub(r"[^\w\u0900-\u097F\u0C80-\u0CFF]+", "", value).lower()

    if normalized_lang.startswith("hi"):
        hindi_yes_variants = {
            "नमस्ते", "नमस्कार", "namaste", "namaskar", "haan", "han", "ha",
        }
        if normalized_value in hindi_yes_variants:
            return "हाँ"

    return value


def _convert_transcript_to_locked_script(transcript: str, normalized_lang: str) -> str:
    value = (transcript or "").strip()
    if not value or not groq_client:
        return value

    if normalized_lang.startswith("kn"):
        system_prompt = (
            "Convert the user's transcript into Kannada script only. "
            "Preserve meaning, keep it short, and do not translate to English. "
            "Return only Kannada script text."
        )
    elif normalized_lang.startswith("hi"):
        system_prompt = (
            "Convert the user's transcript into Hindi Devanagari script only. "
            "Preserve meaning, keep it short, and do not translate to English. "
            "Return only Hindi script text."
        )
    else:
        return value

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": value},
            ],
            temperature=0.0,
            max_tokens=120,
        )
        converted = response.choices[0].message.content.strip()
        return converted or value
    except Exception as exc:
        logger.error("Locked-script conversion failed: %s", exc)
        return value


def _build_stt_request_kwargs(normalized_lang: str, retry_strict: bool = False) -> dict:
    request_kwargs = {
        "model": "whisper-large-v3",
        "response_format": "text",
    }

    if normalized_lang.startswith("hi"):
        request_kwargs["language"] = "hi"
        request_kwargs["prompt"] = (
            "Transcribe exactly what is spoken. "
            "This audio is in Hindi. Output only Hindi in Devanagari script. "
            "Do not translate to English. Do not romanize. Do not use Urdu script. "
            "Short answers like yes/no must stay exact, for example 'हाँ', 'नहीं', 'ठीक'. "
            "Do not expand a short reply into a greeting like नमस्ते."
        )
        if retry_strict:
            request_kwargs["prompt"] += (
                " Return only Devanagari characters for the spoken answer. "
                "If a word is unclear, still keep the answer in Hindi script."
            )
    elif normalized_lang.startswith("kn"):
        request_kwargs["language"] = "kn"
        request_kwargs["prompt"] = (
            "Transcribe exactly what is spoken. "
            "This audio is in Kannada. Output only Kannada in Kannada script. "
            "Do not translate to English. Do not romanize. Do not use any other script."
        )
        if retry_strict:
            request_kwargs["prompt"] += (
                " Return only Kannada script for the spoken answer. "
                "If a word is unclear, still keep the answer in Kannada script."
            )
    elif normalized_lang.startswith("en"):
        request_kwargs["language"] = "en"
        request_kwargs["prompt"] = (
            "Transcribe exactly what is spoken in English. "
            "Do not translate and do not add extra words."
        )

    return request_kwargs


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

        normalized_lang = (language_code or "").strip().lower()
        request_kwargs = _build_stt_request_kwargs(normalized_lang, retry_strict=False)

        with open(audio_file_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=audio_file,
                **request_kwargs
            )

        transcript = transcription.strip()
        transcript = _normalize_short_locked_transcript(transcript, normalized_lang)

        # If a locked Hindi/Kannada answer comes back without the expected
        # script, retry once with a stricter instruction before giving up.
        if normalized_lang and not _has_expected_script(transcript, normalized_lang):
            logger.warning("STT returned unexpected script for %s. Retrying with stricter prompt.", normalized_lang)
            retry_kwargs = _build_stt_request_kwargs(normalized_lang, retry_strict=True)
            with open(audio_file_path, "rb") as audio_file:
                retry_transcription = groq_client.audio.transcriptions.create(
                    file=audio_file,
                    **retry_kwargs
                )
            retry_text = retry_transcription.strip()
            if retry_text:
                transcript = retry_text
                transcript = _normalize_short_locked_transcript(transcript, normalized_lang)

        if normalized_lang and not _has_expected_script(transcript, normalized_lang):
            logger.warning("STT still returned unexpected script for %s. Converting transcript to locked script.", normalized_lang)
            converted = _convert_transcript_to_locked_script(transcript, normalized_lang)
            if converted:
                transcript = converted
                transcript = _normalize_short_locked_transcript(transcript, normalized_lang)

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
