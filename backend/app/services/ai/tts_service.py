"""
tts_service.py - Unified Text-to-Speech for Arohan
Tries Sarvam AI first (if credits available), falls back to free edge-tts.
Supports English, Hindi, Kannada, and mixed Hinglish/Kanglish.
"""

import os
import base64
import logging
import io
import asyncio

import requests
from app.core.config import settings

logger = logging.getLogger(__name__)


# ==================== VOICE MAPPING ====================

# edge-tts voice names for Indian languages
EDGE_VOICE_MAP = {
    "hi-IN": "hi-IN-SwaraNeural",      # Hindi (India)
    "kn-IN": "kn-IN-SapnaNeural",      # Kannada (India)
    "en-IN": "en-IN-NeerjaNeural",     # English (India)
    "en-US": "en-US-JennyNeural",      # English (US) — fallback
}

# Sarvam speaker mapping
SARVAM_SPEAKER = "anushka"


# ==================== SARVAM TTS (primary) ====================

def _sarvam_tts(text: str, language_code: str) -> bytes | None:
    """Try Sarvam AI TTS. Returns bytes or None on failure."""
    sarvam_api_key = settings.SARVAM_API_KEY or os.getenv("SARVAM_API_KEY")
    if not sarvam_api_key:
        logger.warning("Sarvam TTS: No API key configured")
        return None

    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": sarvam_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": [text],
        "target_language_code": language_code,
        "speaker": SARVAM_SPEAKER,
        "pace": 1.0,
        "enable_preprocessing": True,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            data = response.json()
            audios = data.get("audios", [])
            if audios:
                audio_bytes = base64.b64decode(audios[0])
                logger.info(f"Sarvam TTS: {len(audio_bytes)} bytes for '{language_code}'")
                return audio_bytes
            else:
                logger.warning("Sarvam TTS: No audio in response")
                return None
        elif response.status_code == 402:
            logger.warning(f"Sarvam TTS: Insufficient credits (402)")
            return None
        else:
            logger.warning(f"Sarvam TTS: HTTP {response.status_code} — {response.text[:100]}")
            return None
    except Exception as e:
        logger.warning(f"Sarvam TTS failed: {e}")
        return None


# ==================== EDGE TTS (free fallback) ====================

def _edge_tts(text: str, language_code: str) -> bytes | None:
    """Use free edge-tts as fallback. Supports Indian languages."""
    try:
        import edge_tts

        # Pick the best voice for the language
        voice = EDGE_VOICE_MAP.get(language_code, EDGE_VOICE_MAP.get("en-IN"))
        if not voice:
            voice = "en-IN-NeerjaNeural"

        logger.info(f"edge-tts: Using voice '{voice}' for '{language_code}'")

        # Run async edge-tts in a synchronous context
        async def _synthesize() -> bytes:
            communicate = edge_tts.Communicate(text, voice)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data

        audio_bytes = asyncio.run(_synthesize())
        logger.info(f"edge-tts: {len(audio_bytes)} bytes for '{language_code}'")
        return audio_bytes

    except Exception as e:
        logger.error(f"edge-tts failed: {e}")
        return None


# ==================== TEXT CLEANING (strip markdown/symbols) ====================

def clean_text_for_tts(text: str) -> str:
    """
    Strip markdown formatting and symbols that TTS would read aloud.
    Removes asterisks, hashes, backticks, underscores, links, and other symbols.
    This is aggressively designed to prevent TTS from reading symbols like
    'astress' (asterisk), 'hash', 'underscore', etc.
    """
    import re
    
    # Remove image/audio/video markers like ![alt](url), [audio](url)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    # Remove markdown links [text](url) → just text
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    # Remove bold/italic markers: **text** or *text* or __text__ or _text_
    text = re.sub(r'\*{1,3}([^*]*)\*{1,3}', r'\1', text)  # allow empty content between *
    text = re.sub(r'_{1,3}([^_]*?)_{1,3}', r'\1', text)
    # Remove heading hashes: ### text → text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove backticks (inline and block) — keep the content, just remove the backtick markers
    text = re.sub(r'`{1,3}([^`]*?)`{1,3}', r'\1', text)
    # Remove bullet markers: -, *, + at start of lines (including with spaces before)
    text = re.sub(r'^[\s]*[-*+•·]{1,3}\s+', '', text, flags=re.MULTILINE)
    # Remove horizontal rules ---, ___, ***
    text = re.sub(r'^[\s]*[-*_]{3,}[\s]*$', '', text, flags=re.MULTILINE)
    # Remove blockquote markers >
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    # Remove table separators like |---|---|
    text = re.sub(r'^[\s]*[|\s][-]+[|\s][-]+[|\s].*$', '', text, flags=re.MULTILINE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # ===== AGGRESSIVE SYMBOL STRIPPING FOR TTS =====
    # Remove ALL remaining asterisks (these are what TTS reads as 'astress')
    text = text.replace('*', '')
    # Remove all hashes (TTS reads as 'hash')
    text = text.replace('#', '')
    # Remove all tildes
    text = text.replace('~', '')
    # Remove all backticks (already handled above but catch any remaining)
    text = text.replace('`', '')
    # Remove all carets
    text = text.replace('^', '')
    # Remove pipe characters
    text = text.replace('|', '')
    # Remove underscore (if any remaining after the paired removal)
    text = text.replace('_', '')
    
    # Normalize whitespace: collapse multiple spaces
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove empty/whitespace-only lines
    lines = [line for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    text = text.strip()
    
    # If after cleaning we have nothing, return original
    if not text:
        return text
    
    return text


# ==================== UNIFIED TTS ====================

def synthesize_speech(text: str, language_code: str = "hi-IN") -> bytes:
    """
    Unified TTS: tries Sarvam AI first, falls back to edge-tts.
    Strips markdown/symbols from text before sending to TTS.
    Returns raw audio bytes (WAV format from edge-tts, or raw from Sarvam).
    Returns empty bytes if all TTS fails.
    """
    if not text or not text.strip():
        logger.warning("TTS: Empty text, skipping")
        return b""

    # Clean text: remove markdown symbols that TTS would read aloud
    cleaned_text = clean_text_for_tts(text)
    if not cleaned_text:
        logger.warning("TTS: Text became empty after cleaning, using original")
        cleaned_text = text
    
    logger.info(f"TTS: Cleaned text from {len(text)} to {len(cleaned_text)} chars")

    # 1. Try Sarvam AI (paid, higher quality)
    audio = _sarvam_tts(cleaned_text, language_code)
    if audio:
        return audio

    # 2. Fallback to edge-tts (free, good quality)
    logger.info("TTS: Sarvam failed, falling back to edge-tts")
    audio = _edge_tts(cleaned_text, language_code)
    if audio:
        return audio

    # 3. All TTS failed
    logger.error("TTS: All methods failed — no audio generated")
    return b""


# ==================== SPLIT-AND-SYNTHESIZE (for long text) ====================

def synthesize_long_speech(text: str, language_code: str = "hi-IN") -> bytes:
    """
    Splits long text into chunks and synthesizes each one.
    Returns concatenated audio bytes.
    Used for long first-aid instructions.
    """
    from app.services.ai.voice_service import split_into_chunks

    chunks = split_into_chunks(text, max_len=450)
    all_audio = b""

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        audio = synthesize_speech(chunk, language_code)
        if audio:
            all_audio += audio
        logger.info(f"TTS chunk {i+1}/{len(chunks)}: {len(audio)} bytes")

    if not all_audio:
        logger.error("Long TTS: All chunks failed")
        return b""

    logger.info(f"Long TTS: {len(all_audio)} total bytes across {len(chunks)} chunks")
    return all_audio
