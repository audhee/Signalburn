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
import requests
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


def call_ollama_model(text: str, system_prompt: str, max_tokens: int = 900) -> Optional[str]:
    """Call the fine-tuned Ollama model."""
    try:
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        response = requests.post(
            f"{settings.OLLAMA_URL}/api/chat",
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            return result["message"]["content"].strip()
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
    text: str, context: str = "", language: str = "en", rag_source: str = "all"
) -> Dict[str, Any]:
    """
    Process voice input using the fine-tuned Ollama model.
    Uses shared prompt_utils.build_system_prompt() for consistency with Groq path.
    """
    if not settings.USE_LOCAL_MODEL:
        return {"error": "Local model not enabled"}

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

    # RAG context
    rag_context_raw = rag_service.retrieve_context(text, k=5, source=rag_source)
    rag_context = rag_context_raw[:2000] if rag_context_raw else ""

    # Build system prompt (shared with llm_service.py Groq path)
    system_prompt = build_system_prompt(language_name, rag_context, is_emergency)

    # Build messages content — merge conversation context with latest text if available
    if context:
        user_content = (
            f"Patient details (conversation so far):\n{context[:4000]}\n\n"
            f"Latest response from patient:\n{text}"
        )
    else:
        user_content = text

    # Call Ollama model
    response_text = call_ollama_model(user_content, system_prompt)

    if not response_text:
        logger.error("Ollama model returned empty response")
        return {
            "error": "ollama_unavailable",
            "response_text": "",
            "language_code": language_code,
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
