import re
import logging

logger = logging.getLogger(__name__)

KANNADA_PATTERN = re.compile(r'[\u0C80-\u0CFF]')
HINDI_PATTERN   = re.compile(r'[\u0900-\u097F]')

EMERGENCY_KEYWORDS = [
    "stroke", "heart attack", "unconscious", "not breathing", "chest pain",
    "seizure", "fits", "overdose", "poisoning", "severe bleeding", "choking",
    "drowning", "electric shock", "anaphylaxis", "allergic reaction",
    "dil ka dora", "behosh", "sans nahi", "hemorrhage", "haemorrhage"
]

HINDI_ROMAN_WORDS = [
    "mera", "meri", "mere", "aur", "hai", "hain", "nahi", "kya",
    "kar", "raha", "rahi", "tha", "thi", "woh", "yeh", "tum",
    "aap", "main", "hum", "uska", "unka", "dard", "bukhar",
    "haath", "pair", "pet", "sar", "khoon", "dawa", "cheez"
]

KANNADA_ROMAN_WORDS = [
    "nanna", "nanu", "nimma", "avaru", "illi", "alli", "hogi",
    "banni", "thumba", "swalpa", "novedu", "novedutte", "kai",
    "kalu", "tale", "hotte", "bekku", "beda", "ide", "illa",
    "enu", "yenu", "yaake", "hege", "onde", "eradu", "madappa"
]


def detect_language(text: str) -> dict:
    has_kannada = bool(KANNADA_PATTERN.search(text))
    has_hindi   = bool(HINDI_PATTERN.search(text))
    has_english = bool(re.search(r'[a-zA-Z]', text))
    words_lower = text.lower().split()
    text_lower  = text.lower()

    # Emergency detection
    is_emergency = any(kw in text_lower for kw in EMERGENCY_KEYWORDS)

    # Language detection
    if has_kannada and has_english:
        lang_name = "Kanglish"
        lang_code = "kn-IN"
    elif has_hindi and has_english:
        lang_name = "Hinglish"
        lang_code = "hi-IN"
    elif has_kannada:
        lang_name = "Kannada"
        lang_code = "kn-IN"
    elif has_hindi:
        lang_name = "Hindi"
        lang_code = "hi-IN"
    else:
        hindi_count   = sum(1 for w in words_lower if w in HINDI_ROMAN_WORDS)
        kannada_count = sum(1 for w in words_lower if w in KANNADA_ROMAN_WORDS)
        if hindi_count >= 2:
            lang_name = "Hinglish"
            lang_code = "hi-IN"
        elif kannada_count >= 2:
            lang_name = "Kanglish"
            lang_code = "kn-IN"
        else:
            lang_name = "English"
            lang_code = "en-IN"

    instruction = (
        "IMPORTANT: Always write your response in English (Roman alphabet only). "
        "Never use Devanagari, Kannada, Gujarati, Bengali, Urdu or any other script. "
        "If user spoke Hinglish or Kanglish, reply in simple friendly English."
    )

    logger.info(f"Language: {lang_name} ({lang_code}) | Emergency: {is_emergency}")

    return {
        "language_code": lang_code,
        "language_name": lang_name,
        "instruction":   instruction,
        "is_emergency":  is_emergency,
    }