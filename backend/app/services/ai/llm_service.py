"""
llm_service.py — Arohan AI Text Generation (Groq API)
Uses Groq llama-3.1-8b-instant for low-latency first-aid responses.
Uses sashwat_optimized RAG for context retrieval.
Responds in SAME language as user query.
3-layer script protection — no wrong language passes through.

NOTE: Fine-tuned Ollama model is DISABLED. All responses come from
Groq LLM + sashwat_optimized RAG only. See ollama_service.py for
the disabled code (kept for future reference).
"""

import os
import logging
from groq import Groq

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

# Lazy-loaded Groq client — reads env var on first use so config.py's load_dotenv() runs first
_groq_client = None


def _get_groq_client():
    """Return the Groq client, initializing it lazily on first call."""
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
        if api_key:
            _groq_client = Groq(api_key=api_key)
            logger.info("Groq client initialized (lazy)")
        else:
            logger.warning("GROQ_API_KEY not found — using fallback responses")
    return _groq_client


def process_voice_with_llm(
    text: str, context: str = "", language: str = "en", rag_source: str = "sashwat_optimized",
    prefetched_rag_context: str = "",
) -> dict:
    """
    Process voice input using Groq API + sashwat_optimized RAG.

    The fine-tuned Ollama model is DISABLED. All responses are generated
    by Groq LLM using context retrieved exclusively from sashwat_optimized RAG.

    If prefetched_rag_context is provided, skips the internal RAG retrieval
    and uses the given context directly (avoids double-RAG for /chat endpoint).
    """
    # Always use Groq — fine-tuned model is disabled
    return _process_voice_with_groq(text, context, language, "sashwat_optimized", prefetched_rag_context)


def _process_voice_with_groq(
    text: str, context: str = "", language: str = "en", rag_source: str = "all",
    prefetched_rag_context: str = "",
) -> dict:
    """Primary cloud inference path using Groq LLM + sashwat_optimized RAG."""

    requested_lang = normalize_supported_language(language)
    lang_info = detect_language(text)
    language_code = lang_info["language_code"]
    language_name = lang_info["language_name"]
    is_emergency = lang_info["is_emergency"]

    # Language resolution priority:
    # 1. Auto-detection result (most accurate for mixed scripts like Hinglish/Kanglish)
    # 2. Frontend-specified language (for guided queries or when auto-detect returns English)
    if language_name in ["Hinglish", "Kanglish"]:
        # Auto-detect found a mixed mode — always prefer it over frontend hint
        pass
    elif context and requested_lang["language_name"] in [
        "English", "Hindi", "Kannada", "Hinglish", "Kanglish"
    ]:
        language_code = requested_lang["language_code"]
        language_name = requested_lang["language_name"]
    elif language_name == "English" and requested_lang["language_name"] != "English":
        # Auto-detect returned English but frontend specified another language
        language_code = requested_lang["language_code"]
        language_name = requested_lang["language_name"]

    logger.info(f"Language: {language_name} | Emergency: {is_emergency}")

    # Use prefetched RAG context if provided (avoids double-RAG for /chat endpoint)
    # Truncate to 3000 chars for faster prompt processing
    if prefetched_rag_context:
        rag_context = prefetched_rag_context[:3000]
    else:
        rag_context_raw = rag_service.retrieve_context(text, k=3, source=rag_source)
        rag_context = rag_context_raw[:3000] if rag_context_raw else ""

    groq_client = _get_groq_client()
    if not groq_client:
        logger.error("GROQ_API_KEY not configured")
        return fallback_response(language_code, is_emergency)

    system_prompt = build_system_prompt(language_name, rag_context, is_emergency)

    # Build messages array — merge conversation context with latest text into one user message
    if context and "Additional patient details:" not in text:
        user_content = (
            f"Patient details (conversation so far):\n{context[:4000]}\n\n"
            f"Latest response from patient:\n{text}"
        )
    else:
        user_content = text

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.1,
            max_tokens=700,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.3,
        )

        response_text = response.choices[0].message.content.strip()

        # Layer 2 — check if wrong script detected
        if needs_retry(response_text, language_name):
            logger.warning(f"Wrong script for {language_name}. Retrying...")
            response_text = force_language_retry(
                text, rag_context, language_name, is_emergency, context
            )

        response_text = post_process(response_text, is_emergency)
        logger.info(f"Response: {response_text[:100]}...")

        return {
            "response_text": response_text,
            "language_code": language_code,
        }

    except Exception as e:
        logger.error(f"Groq failed: {e}")
        return fallback_response(language_code, is_emergency)


def force_language_retry(
    text: str,
    rag_context: str,
    language_name: str,
    is_emergency: bool,
    prior_context: str = "",
) -> str:
    """
    Layer 2 retry — ultra strict prompt for correct language.
    If still wrong → Layer 3 hardcoded fallback.
    """
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

        # Build retry messages with prior context if available
        retry_messages = [{"role": "system", "content": strict_prompt}]
        if prior_context and "Additional patient details:" not in text:
            retry_messages.append(
                {"role": "user", "content": f"Conversation so far:\n{prior_context[:3000]}"}
            )
        retry_messages.append({"role": "user", "content": f"Patient complaint: {text}"})

        retry = _get_groq_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=retry_messages,
            temperature=0.0,
            max_tokens=700,
        )
        result = retry.choices[0].message.content.strip()

        # Layer 3 — if STILL wrong, use hardcoded
        if needs_retry(result, language_name):
            logger.error("Still wrong after retry. Using hardcoded fallback.")
            return get_hardcoded_response(is_emergency, language_name)

        return result

    except Exception as e:
        logger.error(f"Force retry failed: {e}")
        return get_hardcoded_response(is_emergency, language_name)
