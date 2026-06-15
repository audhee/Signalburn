"""
ollama_service.py — Service for fine-tuned local Ollama model
⚠️  DISABLED — This module is no longer used in the active pipeline.
All responses now come from Groq LLM + sashwat_optimized RAG only.

Kept for future reference. Do NOT delete.
To re-enable: set USE_LOCAL_MODEL=True in config.py and uncomment
the Ollama branch in llm_service.py.

Refactored to use shared prompt_utils.py and centralized config.py Settings.
"""

import logging
import os
import re
import requests
from collections import Counter
from typing import Dict, Any, Optional

from app.core.config import settings
from app.services.ai.rag_service import rag_service
from app.services.ai.language_service import detect_language, normalize_supported_language
from app.services.ai.prompt_utils import (
    has_unsupported_script,
    needs_retry,
    get_hardcoded_response,
    post_process,
    fallback_response,
    build_system_prompt,
    get_script_rule,
)

logger = logging.getLogger(__name__)

# Module-level aliases so test.py and other modules can import directly
USE_LOCAL_MODEL = settings.USE_LOCAL_MODEL
OLLAMA_URL = settings.OLLAMA_URL


def is_local_mode() -> bool:
    """Return True if local Ollama model should be used instead of Groq."""
    return settings.USE_LOCAL_MODEL


def _is_degenerate_response(text: str) -> bool:
    """Detect looping/degenerate model output.
    Checks if the response repeats the same phrase or sentence multiple times.
    """
    if not text:
        return True
    # Check if a sentence or phrase repeats 3+ times
    sentences = re.split(r'[.!?]\s+', text)
    if len(sentences) > 2:
        normalized = [s.strip().lower()[:60] for s in sentences if len(s.strip()) > 10]
        if normalized:
            most_common_count = Counter(normalized).most_common(1)[0][1]
            if most_common_count >= 3:
                logger.warning(f"Degenerate response detected: phrase repeats {most_common_count} times")
                return True
    return False


def call_ollama_model(text: str, system_prompt: str, num_predict: int = 400) -> Optional[str]:
    """Call the fine-tuned Ollama model with optimized settings for low latency."""
    try:
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.8,
                "repeat_penalty": 1.4,
                "num_predict": num_predict,
                "num_thread": min(os.cpu_count() or 4, 8),
            },
        }

        response = requests.post(
            f"{settings.OLLAMA_URL}/api/chat",
            json=payload,
            timeout=180,
        )

        if response.status_code == 200:
            result = response.json()
            content = result["message"]["content"].strip()
            if _is_degenerate_response(content):
                logger.warning("Ollama returned degenerate/looping response")
                return None
            return content
        else:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Ollama unexpected error: {e}")
        return None


def process_voice_with_ollama(
    text: str, context: str = "", language: str = "en", rag_source: str = "sashwat_optimized",
    prefetched_rag_context: str = "",
) -> Dict[str, Any]:
    """
    Process voice input using the fine-tuned Ollama model + sashwat_optimized RAG.
    Uses shared prompt_utils.build_system_prompt() for consistency with Groq path.

    If prefetched_rag_context is provided, skips internal RAG retrieval
    and uses the given context directly (avoids double-RAG for /chat endpoint).
    """
    if not settings.USE_LOCAL_MODEL:
        # Return consistent dict shape so callers accessing ["response_text"] don't crash
        return {"error": "Local model not enabled", "response_text": "", "language_code": language or "hi-IN"}

    # Language detection
    requested_lang = normalize_supported_language(language)
    lang_info = detect_language(text)
    language_code = lang_info["language_code"]
    language_name = lang_info["language_name"]
    is_emergency = lang_info["is_emergency"]

    if context and requested_lang["language_name"] in [
        "English", "Hindi", "Kannada", "Hinglish", "Kanglish"
    ]:
        language_code = requested_lang["language_code"]
        language_name = requested_lang["language_name"]

    logger.info(f"Ollama Language: {language_name} | Emergency: {is_emergency}")

    # RAG context — use prefetched if provided, otherwise retrieve
    # Truncate to 3000 chars: enough for first-aid, fast enough for CPU inference
    if prefetched_rag_context:
        rag_context = prefetched_rag_context[:3000]
    else:
        rag_context_raw = rag_service.retrieve_context(text, k=3, source=rag_source)
        rag_context = rag_context_raw[:3000] if rag_context_raw else ""

    # Build system prompt (shared with llm_service.py Groq path)
    system_prompt = build_system_prompt(language_name, rag_context, is_emergency)

    # Build messages content — merge conversation context with latest text if available
    if context:
        user_content = (
            f"Patient details (conversation so far):\n{context[:1500]}\n\n"
            f"Latest response from patient:\n{text}"
        )
    else:
        user_content = text

    # Call Ollama model
    response_text = call_ollama_model(user_content, system_prompt)

    if not response_text:
        logger.warning("Ollama model returned empty/degenerate response — falling back to Groq")
        # Fallback to Groq cloud when Ollama fails
        try:
            from app.services.ai.llm_service import _process_voice_with_groq
            fallback_result = _process_voice_with_groq(
                text, context, language, "sashwat_optimized", prefetched_rag_context
            )
            fallback_result["model_used"] = "groq-fallback"
            return fallback_result
        except Exception as groq_err:
            logger.error(f"Groq fallback also failed: {groq_err}")
            return {
                "error": "ollama_unavailable",
                "response_text": get_hardcoded_response(is_emergency, language_name),
                "language_code": language_code,
                "model_used": "hardcoded-fallback",
            }

    # Language validation
    if needs_retry(response_text, language_name):
        logger.warning(f"Wrong script for {language_name}. Retrying with Ollama...")
        response_text = force_language_retry_with_ollama(
            text, rag_context, language_name, is_emergency
        )

        if needs_retry(response_text, language_name):
            logger.error("Still wrong after retry. Using hardcoded fallback.")
            response_text = get_hardcoded_response(is_emergency, language_name)

    response_text = post_process(response_text, is_emergency)
    logger.info(f"Ollama Response: {response_text[:100]}...")

    return {
        "response_text": response_text,
        "language_code": language_code,
        "model_used": "ollama-arohan-medical",
    }


def force_language_retry_with_ollama(
    text: str, rag_context: str, language_name: str, is_emergency: bool
) -> str:
    """Force language retry with Ollama model."""
    try:
        script_rule = get_script_rule(language_name)
        strict_prompt = (
            f"You are a medical first aid assistant.\n"
            f"LANGUAGE: {language_name}\n"
            f"SCRIPT RULE: {script_rule}\n"
            f"FORBIDDEN: Arabic, Urdu, Gujarati, Bengali, Tamil, Telugu, Chinese, Japanese scripts.\n\n"
            f"Give 6 to 8 numbered first aid steps in {language_name} only.\n"
            f"No introduction. Just numbered steps."
        )

        response = call_ollama_model(f"Patient complaint: {text}", strict_prompt)
        result = response if response else ""

        if needs_retry(result, language_name):
            logger.error("Still wrong after retry. Using hardcoded fallback.")
            return get_hardcoded_response(is_emergency, language_name)

        return result

    except Exception as e:
        logger.error(f"Force retry failed: {e}")
        return get_hardcoded_response(is_emergency, language_name)
