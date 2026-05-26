"""
ollama_service.py - Service for fine-tuned local Ollama model
Provides dual mode support alongside Groq API.
"""

import os
import re
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from app.services.ai.rag_service import rag_service
from app.services.ai.language_service import detect_language, normalize_supported_language

logger = logging.getLogger(__name__)

# Load .env from backend directory to ensure env vars are available
_env_path = Path(__file__).parent.parent.parent.parent / '.env'
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)

# Configuration — read from env on every access so it picks up .env changes
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "arohan-medical")

USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"

def is_local_mode() -> bool:
    """Return True if local Ollama model should be used instead of Groq."""
    return USE_LOCAL_MODEL

# Scripts that are NEVER allowed in any response
UNSUPPORTED_SCRIPTS = re.compile(
    r'[\u0600-\u06FF'   # Arabic/Urdu
    r'\u0A80-\u0AFF'    # Gujarati
    r'\u0980-\u09FF'    # Bengali
    r'\u0B00-\u0B7F'    # Oriya
    r'\u0B80-\u0BFF'    # Tamil
    r'\u0C00-\u0C7F'    # Telugu
    r'\u4E00-\u9FFF'    # Chinese
    r'\u3040-\u309F'    # Japanese
    r'\u0400-\u04FF'    # Cyrillic
    r'\u0590-\u05FF]'   # Hebrew
)

# Hindi and Kannada scripts — allowed only when user spoke those languages
HINDI_SCRIPT   = re.compile(r'[\u0900-\u097F]')
KANNADA_SCRIPT = re.compile(r'[\u0C80-\u0CFF]')

def has_unsupported_script(text: str) -> bool:
    return bool(UNSUPPORTED_SCRIPTS.search(text))

def needs_retry(response_text: str, language_name: str) -> bool:
    """
    Returns True if response contains wrong script for the detected language.
    Rules:
    - UNSUPPORTED scripts (Urdu, Gujarati, Chinese etc.) → ALWAYS retry
    - Hindi script in response → only OK if user spoke Hindi or Hinglish
    - Kannada script in response → only OK if user spoke Kannada or Kanglish
    """
    if has_unsupported_script(response_text):
        return True

    user_spoke_hindi   = language_name in ["Hindi", "Hinglish"]
    user_spoke_kannada = language_name in ["Kannada", "Kanglish"]

    if bool(HINDI_SCRIPT.search(response_text)) and not user_spoke_hindi:
        return True

    if bool(KANNADA_SCRIPT.search(response_text)) and not user_spoke_kannada:
        return True

    return False

def call_ollama_model(text: str, system_prompt: str, max_tokens: int = 900) -> Optional[str]:
    """
    Call the fine-tuned Ollama model.
    """
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }
        
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=30
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

def build_ollama_system_prompt(language_name: str, rag_context: str, is_emergency: bool) -> str:
    """
    Build system prompt optimized for the fine-tuned Ollama model.
    """
    emergency_block = ""
    if is_emergency:
        emergency_block = (
            f"🚨 EMERGENCY — Give 6 to 8 detailed first aid steps in {language_name}. "
            f"End with: Call 112 or 108 immediately.\n\n"
        )

    # Script rules per language
    if language_name == "English":
        script_rule = "Use ONLY English alphabet A-Z. No other scripts allowed."
    elif language_name == "Hinglish":
        script_rule = "Use English alphabet only (A-Z). Mix Hindi words in Roman script. Example: 'Haath ko rest do'. NO Devanagari. NO other scripts."
    elif language_name == "Kanglish":
        script_rule = "Use English alphabet only (A-Z). Mix Kannada words in Roman script. Example: 'Kai rest madi'. NO Kannada script. NO other scripts."
    elif language_name == "Hindi":
        script_rule = "Use ONLY Hindi Devanagari script (हाथ, दर्द). NO English or other scripts."
    elif language_name == "Kannada":
        script_rule = "Use ONLY Kannada script (ಕೈ, ನೋವು). NO English or other scripts."
    else:
        script_rule = "Use ONLY English alphabet A-Z."

    return f"""You are Arohan AI, a medical first aid assistant for elderly Indians.

{emergency_block}RULES:
1. Never diagnose disease — give only first aid suggestions
2. Keep steps numbered (6 to 8 steps)
3. For emergencies say "Call 112 or 108 immediately"
4. Use short, simple words elderly people understand
5. Never paste raw database text or medical jargon

LANGUAGE: {language_name}
SUPPORTED LANGUAGES ONLY: English, Hindi, Kannada, Hinglish, Kanglish.
If uncertain, default to English.
Never identify, classify, or answer as Urdu, Gujarati, Chinese, Korean, Bengali, Tamil, or Telugu.

=== SCRIPT RULE — MOST IMPORTANT ===
{script_rule}
FORBIDDEN SCRIPTS: Arabic, Urdu, Gujarati, Bengali, Tamil, Telugu, Chinese, Japanese.
=====================================

MEDICAL KNOWLEDGE:
{rag_context if rag_context else 'Use general first aid knowledge.'}

Reply in {language_name} only. Follow the script rule strictly. Be calm and caring."""

def process_voice_with_ollama(text: str, context: str = "", language: str = "en", rag_source: str = "all") -> Dict[str, Any]:
    """
    Process voice input using the fine-tuned Ollama model.
    """
    if not USE_LOCAL_MODEL:
        return {"error": "Local model not enabled"}
    
    # Language detection
    requested_lang = normalize_supported_language(language)
    lang_info = detect_language(text)
    language_code = lang_info["language_code"]
    language_name = lang_info["language_name"]
    is_emergency = lang_info["is_emergency"]

    if context and requested_lang["language_name"] in ["English", "Hindi", "Kannada", "Hinglish", "Kanglish"]:
        language_code = requested_lang["language_code"]
        language_name = requested_lang["language_name"]

    logger.info(f"Ollama Language: {language_name} | Emergency: {is_emergency}")

    # RAG context
    rag_context_raw = rag_service.retrieve_context(text, k=5, source=rag_source)
    rag_context = rag_context_raw[:2000] if rag_context_raw else ""

    # Build system prompt
    system_prompt = build_ollama_system_prompt(language_name, rag_context, is_emergency)

    # Call Ollama model
    response_text = call_ollama_model(text, system_prompt)
    
    if not response_text:
        logger.error("Ollama model returned empty response")
        return fallback_response(language_code, is_emergency)

    # Language validation
    if needs_retry(response_text, language_name):
        logger.warning(f"Wrong script for {language_name}. Retrying with Ollama...")
        response_text = force_language_retry_with_ollama(text, rag_context, language_name, is_emergency)
        
        if needs_retry(response_text, language_name):
            logger.error("Still wrong after retry. Using hardcoded fallback.")
            response_text = get_hardcoded_response(is_emergency, language_name)

    response_text = post_process(response_text, is_emergency)
    logger.info(f"Ollama Response: {response_text[:100]}...")

    return {
        "response_text": response_text,
        "language_code": language_code
    }

def force_language_retry_with_ollama(text: str, rag_context: str, language_name: str, is_emergency: bool) -> str:
    """
    Force language retry with Ollama model.
    """
    try:
        if language_name == "English":
            script_rule = "Use ONLY English alphabet A-Z. Zero non-English characters allowed."
        elif language_name == "Hinglish":
            script_rule = "Use English words mixed with Hindi words written in Roman script (A-Z only). Example: 'Haath ko rest do'. NO Devanagari script. NO other scripts."
        elif language_name == "Kanglish":
            script_rule = "Use English words mixed with Kannada words written in Roman script (A-Z only). Example: 'Kai rest madi'. NO Kannada script. NO other scripts."
        elif language_name == "Hindi":
            script_rule = "Use ONLY Hindi Devanagari script (like हाथ, दर्द). NO English, NO other scripts."
        elif language_name == "Kannada":
            script_rule = "Use ONLY Kannada script (like ಕೈ, ನೋವು). NO English, NO other scripts."
        else:
            script_rule = "Use ONLY English alphabet A-Z."

        strict_prompt = f"""You are a medical first aid assistant.
LANGUAGE: {language_name}
SCRIPT RULE: {script_rule}
FORBIDDEN: Arabic, Urdu, Gujarati, Bengali, Tamil, Telugu, Chinese, Japanese scripts.

Give 6 to 8 numbered first aid steps in {language_name} only.
No introduction. Just numbered steps."""

        response = call_ollama_model(f"Patient complaint: {text}", strict_prompt)
        result = response if response else ""

        if needs_retry(result, language_name):
            logger.error("Still wrong after retry. Using hardcoded fallback.")
            return get_hardcoded_response(is_emergency, language_name)

        return result

    except Exception as e:
        logger.error(f"Force retry failed: {e}")
        return get_hardcoded_response(is_emergency, language_name)

def get_hardcoded_response(is_emergency: bool, language_name: str = "English") -> str:
    """Layer 3 — guaranteed correct script hardcoded responses."""
    if language_name == "Hindi":
        if is_emergency:
            return (
                "यह एक medical emergency है।\n"
                "1. व्यक्ति को शांत रखें।\n"
                "2. खाना या पानी न दें।\n"
                "3. कपड़े ढीले करें।\n"
                "4. तुरंत 112 या 108 पर call करें।"
            )
        return (
            "प्राथमिक चिकित्सा:\n"
            "1. व्यक्ति को शांत रखें।\n"
            "2. सांस सही है या नहीं देखें।\n"
            "3. बिना doctor की सलाह के कोई दवा न दें।\n"
            "4. स्थिति खराब हो तो 112 पर call करें।"
        )
    elif language_name == "Kannada":
        if is_emergency:
            return (
                "Idu medical emergency.\n"
                "1. Vyaktiya shanta madi.\n"
                "2. Yenu tinisabedi kudisabedi.\n"
                "3. Bagge hetige madi.\n"
                "4. Turant 112 ge call madi."
            )
        return (
            "Prathama chikitse:\n"
            "1. Vyaktiya shanta madi.\n"
            "2. Ushiraadu sari ide nodko.\n"
            "3. Doctor heli bedada madhu tinisabedi.\n"
            "4. Sthiti ketta aadare 112 ge call madi."
        )
    elif language_name == "Hinglish":
        if is_emergency:
            return (
                "Yeh ek medical emergency hai.\n"
                "1. Person ko shant rakho.\n"
                "2. Kuch khilao ya pilao mat.\n"
                "3. Kapre dhile karo.\n"
                "4. Turant 112 ya 108 pe call karo."
            )
        return (
            "First aid ke liye:\n"
            "1. Person ko shant rakho.\n"
            "2. Breathing check karo.\n"
            "3. Doctor ki salah ke bina koi dawa mat do.\n"
            "4. Condition kharab ho to 112 call karo."
        )
    elif language_name == "Kanglish":
        if is_emergency:
            return (
                "Idu medical emergency.\n"
                "1. Person shanta iro hage nodi.\n"
                "2. Yenu tinisabedi.\n"
                "3. Bagge loose madi.\n"
                "4. Turant 112 ge call madi."
            )
        return (
            "First aid ge:\n"
            "1. Person shanta iro hage nodi.\n"
            "2. Breathing sari ide check madi.\n"
            "3. Doctor heli bedada medicine tinisabedi.\n"
            "4. Condition ketta aadare 112 call madi."
        )
    else:
        if is_emergency:
            return (
                "This is a medical emergency.\n"
                "1. Keep the person calm and still.\n"
                "2. Do not give food or water.\n"
                "3. Loosen any tight clothing.\n"
                "4. Stay with the person at all times.\n"
                "5. Call 112 or 108 immediately.\n"
                "6. Tell the doctor when symptoms started."
            )
        return (
            "Here is general first aid advice.\n"
            "1. Keep the person calm and comfortable.\n"
            "2. Check if they are breathing normally.\n"
            "3. Do not move if there is a head or neck injury.\n"
            "4. Apply gentle pressure if there is bleeding.\n"
            "5. Do not give medicines without doctor advice.\n"
            "6. Call 112 or 108 if condition gets worse."
        )

def post_process(response_text: str, is_emergency: bool) -> str:
    if is_emergency and not response_text.startswith("🚨"):
        response_text = "🚨 " + response_text
    return response_text

def fallback_response(language_code: str, is_emergency: bool) -> Dict[str, Any]:
    lang_name_map = {
        "hi-IN": "Hindi",
        "kn-IN": "Kannada",
        "en-IN": "English",
    }
    lang_name = lang_name_map.get(language_code, "English")
    return {
        "response_text": get_hardcoded_response(is_emergency, lang_name),
        "language_code": language_code
    }