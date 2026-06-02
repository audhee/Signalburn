"""
prompt_utils.py -- Shared Prompt Utilities for Arohan AI Services
Provides language validation, hardcoded fallback responses, and system prompt builder.
Used by both llm_service.py (Groq) and ollama_service.py (Ollama local model).
"""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# --- Script Detection Regexes ---

UNSUPPORTED_SCRIPTS = re.compile(
    r"[\u0600-\u06FF"   # Arabic/Urdu
    r"\u0A80-\u0AFF"    # Gujarati
    r"\u0980-\u09FF"    # Bengali
    r"\u0B00-\u0B7F"    # Oriya
    r"\u0B80-\u0BFF"    # Tamil
    r"\u0C00-\u0C7F"    # Telugu
    r"\u4E00-\u9FFF"    # Chinese
    r"\u3040-\u309F"    # Japanese
    r"\u0400-\u04FF"    # Cyrillic
    r"\u0590-\u05FF]"   # Hebrew
)

HINDI_SCRIPT   = re.compile(r"[\u0900-\u097F]")
KANNADA_SCRIPT = re.compile(r"[\u0C80-\u0CFF]")


def has_unsupported_script(text: str) -> bool:
    return bool(UNSUPPORTED_SCRIPTS.search(text))


def needs_retry(response_text: str, language_name: str) -> bool:
    if has_unsupported_script(response_text):
        return True
    user_spoke_hindi = language_name in ["Hindi", "Hinglish"]
    user_spoke_kannada = language_name in ["Kannada", "Kanglish"]
    if bool(HINDI_SCRIPT.search(response_text)) and not user_spoke_hindi:
        return True
    if bool(KANNADA_SCRIPT.search(response_text)) and not user_spoke_kannada:
        return True
    return False


# --- Hardcoded Fallback Responses (Layer 3 Safety Net) ---

HARDCODED_EMERGENCY_ENGLISH = (
    "This is a medical emergency.\n"
    "1. Keep the person calm and still.\n"
    "2. Do not give food or water.\n"
    "3. Loosen any tight clothing.\n"
    "4. Stay with the person at all times.\n"
    "5. Call 112 or 108 immediately.\n"
    "6. Tell the doctor when symptoms started."
)

HARDCODED_GENERAL_ENGLISH = (
    "Here is general first aid advice.\n"
    "1. Keep the person calm and comfortable.\n"
    "2. Check if they are breathing normally.\n"
    "3. Do not move if there is a head or neck injury.\n"
    "4. Apply gentle pressure if there is bleeding.\n"
    "5. Do not give medicines without doctor advice.\n"
    "6. Call 112 or 108 if condition gets worse."
)

ENGLISH_RESPONSES = {
    "emergency": HARDCODED_EMERGENCY_ENGLISH,
    "general": HARDCODED_GENERAL_ENGLISH,
}


def get_hardcoded_response(is_emergency: bool, language_name: str = "English") -> str:
    if language_name == "English":
        return HARDCODED_EMERGENCY_ENGLISH if is_emergency else HARDCODED_GENERAL_ENGLISH
    return HARDCODED_EMERGENCY_ENGLISH if is_emergency else HARDCODED_GENERAL_ENGLISH


def post_process(response_text: str, is_emergency: bool) -> str:
    if is_emergency and not response_text.startswith("\U0001f6a8"):
        response_text = "\U0001f6a8 " + response_text
    return response_text


def fallback_response(language_code: str, is_emergency: bool) -> Dict[str, Any]:
    lang_name_map = {"hi-IN": "Hindi", "kn-IN": "Kannada", "en-IN": "English"}
    lang_name = lang_name_map.get(language_code, "English")
    return {
        "response_text": get_hardcoded_response(is_emergency, lang_name),
        "language_code": language_code
    }


def get_script_rule(language_name: str) -> str:
    if language_name == "English":
        return "Use ONLY English alphabet A-Z. No other scripts allowed."
    elif language_name == "Hinglish":
        return ("Use English alphabet only (A-Z). Use ENGLISH grammar with a few Hindi words "
                "mixed in. Example: 'Give rest to your haath' NOT 'Haath ko rest do'. "
                "Keep English sentence structure. NO Devanagari. NO other scripts.")
    elif language_name == "Kanglish":
        return ("Use English alphabet only (A-Z). Use ENGLISH grammar with a few Kannada words "
                "mixed in. Example: 'Give rest to your kai' NOT 'Kai rest madi'. "
                "Keep English sentence structure. NO Kannada script. NO other scripts.")
    elif language_name == "Hindi":
        return "Use ONLY Hindi Devanagari script. NO English or other scripts."
    elif language_name == "Kannada":
        return "Use ONLY Kannada script. NO English or other scripts."
    else:
        return "Use ONLY English alphabet A-Z."


def build_system_prompt(
    language_name: str,
    rag_context: str,
    is_emergency: bool,
    service_name: str = "Arohan AI",
) -> str:
    emergency_block = ""
    if is_emergency:
        emergency_block = (
            "EMERGENCY -- Give 6 to 8 detailed first aid steps in " + language_name + ". "
            "End with: Call 112 or 108 immediately.\n\n"
        )
    script_rule = get_script_rule(language_name)
    rag_section = rag_context if rag_context else (
        "You have access to medical first aid knowledge for specific conditions.\n"
        "If the patient describes a SPECIFIC condition (e.g. scorpion sting, snake bite, "
        "deep cut with spurting blood, severe bleeding, animal bite, burn, fracture, "
        "allergic reaction, insect sting, heat stroke, hypothermia, drowning, poisoning, "
        "electric shock), give specific, targeted first aid steps for that exact condition "
        "even though the knowledge base has no matching document. Use your medical training "
        "to provide accurate, safe first aid.\n"
        "If the condition does not match a specific condition, give general first aid advice."
    )
    return (
        "You are " + service_name + ", a calm medical first aid assistant for elderly Indians.\n\n"
        + emergency_block
        + "RULES (Anisha's medical_safe template):\n"
        "1. Never diagnose disease -- give only first aid suggestions\n"
        "2. Keep steps numbered (6 to 8 steps)\n"
        "3. For emergencies say \"Call 112 or 108 immediately\"\n"
        "4. Use short, simple words elderly people understand\n"
        "5. Never paste raw database text or medical jargon\n\n"
        "LANGUAGE: " + language_name + "\n"
        "SUPPORTED LANGUAGES ONLY: English, Hindi, Kannada, Hinglish, Kanglish.\n"
        "If uncertain, default to English.\n"
        "Never identify, classify, or answer as Urdu, Gujarati, Chinese, Korean, "
        "Bengali, Tamil, or Telugu.\n\n"
        "=== SCRIPT RULE -- MOST IMPORTANT ===\n"
        + script_rule + "\n"
        "FORBIDDEN SCRIPTS: Arabic, Urdu, Gujarati, Bengali, Tamil, Telugu, "
        "Chinese, Japanese.\n"
        "=====================================\n\n"
        "MEDICAL KNOWLEDGE:\n"
        + rag_section + "\n\n"
        "Reply in " + language_name + " only. Follow the script rule strictly. Be calm and caring."
    )
