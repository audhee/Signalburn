import re
import string
import logging

logger = logging.getLogger(__name__)

KANNADA_PATTERN = re.compile(r'[\u0C80-\u0CFF]')
HINDI_PATTERN   = re.compile(r'[\u0900-\u097F]')
ASCII_PATTERN   = re.compile(r'[a-zA-Z]')

# Scripts we do not support as independent language outputs.
# If they appear in model output or user input, we still map back into one
# of the 5 supported modes instead of inventing a new language.
UNSUPPORTED_SCRIPT_PATTERN = re.compile(
    r'[\u0600-\u06FF'   # Arabic / Urdu
    r'\u0A80-\u0AFF'    # Gujarati
    r'\u0980-\u09FF'    # Bengali
    r'\u0B80-\u0BFF'    # Tamil
    r'\u0C00-\u0C7F'    # Telugu
    r'\u4E00-\u9FFF'    # Chinese
    r'\u3040-\u30FF'    # Japanese
    r'\uAC00-\uD7AF]'   # Korean
)

EMERGENCY_KEYWORDS = [
    "stroke", "heart attack", "unconscious", "not breathing", "chest pain",
    "seizure", "fits", "overdose", "poisoning", "severe bleeding", "choking",
    "drowning", "electric shock", "anaphylaxis", "allergic reaction",
    "dil ka dora", "behosh", "sans nahi", "hemorrhage", "haemorrhage"
]

HINDI_ROMAN_WORDS = [
    "mera", "meri", "mere", "aur", "hai", "hain", "nahi", "kya",
    "kar", "raha", "rahi", "tha", "thi", "woh", "yeh", "tum",
    "aap", "hum", "uska", "unka", "dard", "bukhar",
    "haath", "pair", "pet", "sar", "khoon", "dawa", "cheez",
    "aagya", "gaya", "aaya", "diya", "liya", "kiya",
    "hoga", "hoon",
    "kuch", "koi", "bahut", "thoda", "sab",
    "apna", "apni", "usne", "usko",
    "kare", "karta", "karti", "karo",
    "ja", "jao", "aa", "aao",
    "de", "le", "lo",
    "accha", "theek", "samajh",
    "yaha", "waha", "kab", "kyu", "kaise", "kitna",
    "par", "lekin", "kyuki",
    "dekh", "bada", "chota", "jaldi",
    "andar", "bahar", "upar", "neeche",
    "aaj", "kal", "din", "raat", "subah",
    "mila", "mili", "chahiye", "sakta", "sakti",
    "wala", "wali", "wale",
    "hona", "karna", "lagna",
    "bola", "boli", "bolo",
    "rakha", "rakho",
    "pada", "padi",
]

KANNADA_ROMAN_WORDS = [
    # Pronouns & particles
    "nanna", "nanu", "nanage", "nimma", "nimge", "avaru",
    "illi", "alli", "hogi", "banni",
    # Common verbs & verb roots
    "beku", "beda", "bekku", "bedava", "bedi",
    "madi", "maadi", "madu", "madbeku", "madoke",
    "hogu", "bartini", "bande", "bandide", "barutte",
    "nodi", "nodappa",
    "helu", "heli", "helappa", "helbeku",
    "kelu", "keli", "kelbeku",
    "tago", "tagondu", "tagobeku",
    "haku", "hakbeku",
    "kodi", "kodbeku",
    # Descriptors & adjectives
    "thumba", "swalpa", "novedu", "novedutte", "sari",
    "chennagi", "olleya", "olle",
    # Body parts
    "kai", "kalu", "tale", "hotte", "bayi", "kivi",
    "mukha", "bitta", "hedaru", "noyi",
    # Existence & identity
    "ide", "illa", "ideya", "ittu",
    "enu", "yenu", "yaake", "yake", "hege",
    "ondu", "onde", "eradu", "mooru",
    "madappa", "taale", "tal",
    # Misc common
    "sakka", "benki",
]

SUPPORTED_LANGUAGE_CODES = {"en-IN", "hi-IN", "kn-IN"}
SUPPORTED_LANGUAGE_NAMES = {"English", "Hindi", "Kannada", "Hinglish", "Kanglish"}


def normalize_supported_language(language_hint: str | None) -> dict:
    """
    Hard-normalize any incoming language hint to one of the 5 supported modes:
    English, Hindi, Kannada, Hinglish, Kanglish.
    """
    hint = (language_hint or "").strip().lower()

    if hint in {"kn-in", "kn", "kannada"}:
        return {"language_code": "kn-IN", "language_name": "Kannada"}
    if hint in {"hi-in", "hi", "hindi"}:
        return {"language_code": "hi-IN", "language_name": "Hindi"}
    if hint in {"en-in", "en", "english"}:
        return {"language_code": "en-IN", "language_name": "English"}
    if hint in {"hinglish", "hindi-english", "hindi english", "hindi+english"}:
        return {"language_code": "hi-IN", "language_name": "Hinglish"}
    if hint in {"kanglish", "kannada-english", "kannada english", "kannada+english"}:
        return {"language_code": "kn-IN", "language_name": "Kanglish"}

    # Unsupported/unknown hints are intentionally collapsed to English.
    return {"language_code": "en-IN", "language_name": "English"}


def sanitize_text_for_language(text: str, language_code: str, fallback: str = "Unclear response") -> str:
    """
    Remove unsupported scripts from transcript text before it is reused as model context.
    This prevents short STT mistakes like Urdu/Korean characters from poisoning the prompt.
    """
    value = (text or "").strip()
    if not value:
        return fallback

    normalized = normalize_supported_language(language_code)
    code = normalized["language_code"]

    # Once a guided session is locked to Hindi or Kannada, we keep only that
    # script so translated English does not leak back into the transcript.
    if code == "hi-IN":
        allowed_pattern = re.compile(r'[^0-9\u0900-\u097F\s.,!?():;+\-/]')
    elif code == "kn-IN":
        allowed_pattern = re.compile(r'[^0-9\u0C80-\u0CFF\s.,!?():;+\-/]')
    else:
        allowed_pattern = re.compile(r'[^0-9a-zA-Z\s.,!?():;+\-/]')

    cleaned = allowed_pattern.sub(" ", value)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # If the original answer had unsupported script and cleaning erased almost
    # everything, replace it with a neutral marker instead of passing garbage.
    if not cleaned or len(cleaned) < 2:
        return fallback

    return cleaned


def detect_language(text: str) -> dict:
    text = (text or "").strip()
    has_kannada = bool(KANNADA_PATTERN.search(text))
    has_hindi   = bool(HINDI_PATTERN.search(text))
    has_english = bool(ASCII_PATTERN.search(text))
    has_unsupported_script = bool(UNSUPPORTED_SCRIPT_PATTERN.search(text))
    # Strip punctuation before splitting so word matching works reliably
    stripped = re.sub(r'[^a-zA-Z\s]', ' ', text.lower())
    words_lower = stripped.split()
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
        # Strip punctuation for accurate word matching (e.g. "ide," -> "ide")
        clean_words = [w.strip(string.punctuation) for w in words_lower]
        hindi_count   = sum(1 for w in clean_words if w in HINDI_ROMAN_WORDS)
        kannada_count = sum(1 for w in clean_words if w in KANNADA_ROMAN_WORDS)

        # Single unmistakeably Indian-language word is enough to detect mixed mode
        if hindi_count >= 1:
            lang_name = "Hinglish"
            lang_code = "hi-IN"
        elif kannada_count >= 1:
            lang_name = "Kanglish"
            lang_code = "kn-IN"
        else:
            lang_name = "English"
            lang_code = "en-IN"

    # Final guardrail:
    # even if unsupported scripts appear in the text, we still collapse the
    # result into one of the supported 5 modes only.
    if has_unsupported_script and lang_name not in SUPPORTED_LANGUAGE_NAMES:
        lang_name = "English"
        lang_code = "en-IN"

    normalized = normalize_supported_language(lang_name)
    lang_name = normalized["language_name"]
    lang_code = normalized["language_code"]

    instruction = (
        "IMPORTANT: The system supports only 5 language modes: English, Hindi, Kannada, Hinglish, Kanglish. "
        "Never classify or reply as Urdu, Gujarati, Chinese, Korean, Bengali, Tamil, Telugu or any other language. "
        "If uncertain, default to English. "
        "If user spoke Hinglish or Kanglish, keep the reply in that same Roman-script mixed style."
    )

    logger.info(f"Language: {lang_name} ({lang_code}) | Emergency: {is_emergency}")

    return {
        "language_code": lang_code,
        "language_name": lang_name,
        "instruction":   instruction,
        "is_emergency":  is_emergency,
    }
