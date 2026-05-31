"""
language_service.py - Enhanced Language Detection
Handles: Hindi, Kannada, English, Hinglish, Kanglish, Urdu, Short inputs
"""

import re
import logging

logger = logging.getLogger(__name__)

# Unicode patterns
KANNADA_PATTERN   = re.compile(r'[\u0C80-\u0CFF]')
HINDI_PATTERN     = re.compile(r'[\u0900-\u097F]')
URDU_PATTERN      = re.compile(r'[\u0600-\u06FF]')
TELUGU_PATTERN    = re.compile(r'[\u0C00-\u0C7F]')
TAMIL_PATTERN     = re.compile(r'[\u0B80-\u0BFF]')
MALAYALAM_PATTERN = re.compile(r'[\u0D00-\u0D7F]')

# Common Hinglish words
HINGLISH_WORDS = {
    "mujhe", "mere", "meri", "mera", "tum", "tumhara", "aap", "aapka", "main", "mein", "hum",
    "hai", "hain", "ho", "hua", "hoga", "karo", "karna", "kiya", "bolo", "batao", "samjho",
    "kya", "kaise", "kab", "kahan", "kyu", "kaun", "kitna", "nahi", "haan", "theek", "accha",
    "bahut", "thoda", "zyada", "lekin", "par", "aur", "toh", "bhi", "hi", "se", "ko", "ka", "ki",
    "abhi", "pehle", "baad", "andar", "bahar", "upar", "neeche",
    "doctor", "dard", "chot", "khoon", "sar", "pet", "haath", "paer", "dawai", "ilaaj", "tabiyat",
    "saans", "saans lena", "saans nahi", "breathing", "cant", "cannot", "able",
}

# Common Kanglish words
KANGLISH_WORDS = {
    "naanu", "nanna", "nimma", "neenu", "avanu", "avalu", "avaru", "ivaru",
    "yenu", "enu", "yelli", "elli", "yaake", "yake", "yaavaga", "yaava", "hege",
    "ide", "illa", "ideya", "alla", "hogu", "banni", "tago", "kodi", "beda", "beku",
    "chennagide", "chennagidini", "dina", "ratri", "beligge", "sanjee",
    "thumba", "thumbaa", "swalpa", "jasti", "kasta", "sahaya", "mado", "madu",
    "gottu", "gottilla", "gotta", "tilidu", "tiliyala",
    "nodu", "nodri", "kelsa", "oota", "neeru", "hanebaraha",
    "tale", "talevatu", "jvara", "jwara", "kush", "kushi", "noppi", "noppigalu",
    "kaalu", "kaal", "aata", "aagide", "aagithu", "mari", "madi", "aayithu",
}

# Emergency keywords (any language)
EMERGENCY_WORDS = {
    "cant breathe", "cannot breathe", "not breathing", "choking", "heart attack",
    "unconscious", "bleeding heavily", "blood everywhere", "dying", "emergency",
    "112", "108", "ambulance", "hospital", "dying", "critical", "severe",
    "saans nahi", "saans", "breathing problem", "chest pain", "heart pain",
    "blood pressure high", "180/120", "stroke", "paralysis",
}


def detect_language(text: str) -> dict:
    """
    Detects language with better handling for short inputs and emergencies.
    """
    if not text or not text.strip():
        return {
            "language_code": "en-IN",
            "language_name": "English",
            "instruction": "Reply in simple English only.",
            "is_emergency": False
        }

    text_lower = text.lower().strip()
    words = set(re.findall(r'\b\w+\b', text_lower))

    # ── Check for EMERGENCY first ─────────────────────────────────────────
    emergency_hits = words.intersection(EMERGENCY_WORDS)
    is_emergency = len(emergency_hits) >= 1 or any(word in text_lower for word in EMERGENCY_WORDS)

    # ── Check native scripts ────────────────────────────────────────────────
    if KANNADA_PATTERN.search(text):
        return {
            "language_code": "kn-IN",
            "language_name": "Kannada",
            "instruction": "Reply in pure Kannada language only. Use Kannada script (ಕನ್ನಡ).",
            "is_emergency": is_emergency
        }

    if HINDI_PATTERN.search(text):
        return {
            "language_code": "hi-IN",
            "language_name": "Hindi",
            "instruction": "Reply in pure Hindi language only. Use Devanagari script (हिंदी).",
            "is_emergency": is_emergency
        }

    if URDU_PATTERN.search(text):
        return {
            "language_code": "hi-IN",
            "language_name": "Hindi-Urdu",
            "instruction": "Reply in Hindi-Urdu mixed language. Use simple words.",
            "is_emergency": is_emergency
        }

    # ── Check for mixed languages in English script ───────────────────────
    kannada_hits = words.intersection(KANGLISH_WORDS)
    hindi_hits = words.intersection(HINGLISH_WORDS)

    # Pure Kanglish
    if kannada_hits and len(kannada_hits) >= 2 and not hindi_hits:
        return {
            "language_code": "kn-IN",
            "language_name": "Kannada-English mix",
            "instruction": (
                "Reply in Kannada-English mixed language (Kanglish). "
                "Example: 'Nimage first aid beku, swalpa wait maadi.' "
                "NEVER use pure English sentences."
            ),
            "is_emergency": is_emergency
        }

    # Pure Hinglish
    if hindi_hits and len(hindi_hits) >= 2 and not kannada_hits:
        return {
            "language_code": "hi-IN",
            "language_name": "Hindi-English mix",
            "instruction": (
                "Reply in Hindi-English mixed language (Hinglish). "
                "Example: 'Aapko first aid chahiye, thoda rest karo.' "
                "NEVER use pure English sentences."
            ),
            "is_emergency": is_emergency
        }

    # Mixed Kannada-Hindi
    if kannada_hits and hindi_hits:
        return {
            "language_code": "kn-IN",
            "language_name": "Kannada-Hindi mix",
            "instruction": (
                "Reply in Kannada-Hindi mixed language. "
                "Example: 'Nanna tale dard ide, yenu madi?' "
                "NEVER use pure English sentences."
            ),
            "is_emergency": is_emergency
        }

    # ── Short inputs / Acknowledgments ──────────────────────────────────────
    short_inputs = {"oke", "ok", "okay", "haan", "han", "hmm", "yes", "no", "thanks", "thank you"}
    if text_lower in short_inputs or len(text_lower) < 10:
        return {
            "language_code": "en-IN",
            "language_name": "English",
            "instruction": "Reply with a friendly greeting asking how you can help today.",
            "is_emergency": False
        }

    # ── Default English ───────────────────────────────────────────────────
    return {
        "language_code": "en-IN",
        "language_name": "English",
        "instruction": "Reply in simple English only.",
        "is_emergency": is_emergency
    }