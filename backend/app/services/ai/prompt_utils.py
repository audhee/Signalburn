"""
prompt_utils.py -- Shared Prompt Utilities for Arohan AI Services
Provides language validation, hardcoded fallback responses, and system prompt builder.
Used by llm_service.py (Groq). ollama_service.py (Ollama local model) is disabled.
"""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# --- Script Detection Regexes ---

# --- First-Aid Scope Guardrail ---

# Chronic / out-of-scope conditions that the chatbot must NOT answer
CHRONIC_CONDITIONS = [
    "cancer", "diabetes", "tumor", "tumour", "chemotherapy",
    "heart disease", "stroke treatment", "hypertension",
    "kidney failure", "liver failure", "hiv", "aids",
    "autoimmune", "arthritis", "alzheimer", "parkinson",
    "epilepsy", "leukemia", "lymphoma", "sickle cell",
    "cystic fibrosis", "multiple sclerosis", "dialysis",
    "chemo", "radiotherapy", "palliative",
]

# Broader non-first-aid topics
NON_FIRST_AID_TOPICS = [
    "diet plan", "weight loss", "weight gain", "lose weight", "gain weight",
    "exercise routine", "workout", "protein shake", "vitamin supplement",
    "cosmetic", "beauty", "skincare routine", "hair loss",
    "pregnancy advice", "fertility", "sexual health",
    "mental health therapy", "depression treatment",
    "anxiety treatment", "counseling", "psychiatrist",
    "surgery recommendation", "surgery cost",
    "medicine dosage", "prescription", "drug interaction",
    "insurance", "hospital bill", "medical report",
    "what is my diagnosis", "diagnose me",
]


# Medical / first-aid keywords — if NONE of these appear in the query,
# the query is NOT a first-aid question.
MEDICAL_KEYWORDS = [
    # Symptoms & emergencies
    "pain", "bleeding", "cut", "wound", "burn", "fracture", "broken",
    "sprain", "swelling", "bruise", "scar", "injury", "accident",
    "fall", "fainted", "unconscious", "breathing", "breath",
    "choking", "dizzy", "vomit", "fever", "infection",
    "allergic", "allergy", "rash", "sting", "bite", "snake",
    "scorpion", "dog bite", "insect",
    # Body parts
    "head", "chest", "stomach", "back", "neck", "arm", "leg",
    "eye", "ear", "nose", "throat", "hand", "foot", "knee",
    "shoulder", "hip", "finger", "toe",
    # First-aid actions
    "first aid", "cpr", "compress", "bandage", "tourniquet",
    "splint", "antiseptic", "disinfect", "clean wound",
    # Emergency keywords
    "emergency", "urgent", "hospital", "doctor", "ambulance",
    "112", "108", "poisoning", "drowning", "electric shock",
    "heat stroke", "hypothermia", "stroke", "seizure",
    "heart attack", "cardiac", "choking", "airway",
    # Medical conditions (acute)
    "asthma", "diabetes" , "epilepsy", "hypoglycemia",
    "low sugar", "high sugar", "blood pressure",
]

# Hindi (Devanagari) medical keywords
# Using pure literal Devanagari for reliable substring matching
HINDI_MEDICAL_KEYWORDS = [
    # Symptoms
    '\u0926\u0930\u094d\u0926', '\u092a\u0940\u0921\u093c\u093e',
    '\u0924\u0915\u0932\u0940\u092b', '\u0916\u0942\u0928',
    '\u0918\u093e\u0935', '\u091c\u0916\u094d',
    '\u091c\u0932\u0928\u093e', '\u091c\u0932\u0928',
    '\u092e\u094b\u091a', '\u0938\u0942\u091c\u0928',
    '\u091a\u094b\u091f', '\u0918\u093e\u092f\u0932',
    '\u0926\u0941\u0930\u094d\u0918\u091f\u0928',
    '\u092c\u0947\u0939\u094b\u0936', '\u092c\u0947\u0939\u094b\u0936\u0940',
    '\u092c\u0941\u0916\u093e\u0930', '\u091c\u094d\u0935\u0930',
    '\u0921\u0902\u0915', '\u0921\u0938\u0928\u093e',
    '\u0938\u093e\u0902\u092a', '\u092c\u093f\u091a\u094d\u092e\u0942',
    '\u0909\u0932\u094d\u091f\u0940',
    # Body parts
    '\u0938\u093f\u0930', '\u091b\u093e\u0924\u0940',
    '\u092a\u0947\u091f', '\u0939\u093e\u0925',
    '\u0906\u0902\u0916', '\u0915\u093e\u0928',
    '\u0917\u0932\u093e', '\u091a\u0939\u0930\u0940',
    '\u092a\u0947\u091f', '\u0926\u093e\u0902\u0924',
    # Emergency
    '\u0906\u092a\u093e\u0924\u0915\u093e\u0932',
    '\u0907\u092e\u0930\u091c\u0947\u0902\u0938\u0940',
    '\u0905\u0938\u094d\u092a\u0924\u093e\u0932',
    '\u0921\u0949\u0915\u094d\u091f\u0930',
    '\u090f\u092e\u094d\u092c\u094d\u0932\u0947\u0902\u0938',
    '\u091c\u0939\u0930', '\u091c\u0939\u0930 \u0921\u0939\u0928\u093e',
    '\u0921\u0942\u092c\u0928\u093e',
    '\u0926\u093f\u0932 \u0915\u093e \u0926\u094c\u0930\u093e',
    '\u0932\u0915\u0935\u093e', '\u092a\u094d\u0930\u093e\u0925\u092e\u093f\u0915 \u0909\u092a\u091a\u093e\u0930',
    '\u092a\u091f\u094d\u0938\u0940',
]

# Kannada medical keywords
# Using pure literal Kannada for reliable substring matching
KANNADA_MEDICAL_KEYWORDS = [
    # Symptoms
    '\u0ca8\u0cb3\u0cc1', '\u0ca8\u0cb3\u0cbe',
    '\u0cb0\u0c95\u0ccd\u0c97\u0cc1\u0cb5\u0cc2',
    '\u0c97\u0cbe\u0caf', '\u0c97\u0cbe\u0caf\u0cb5\u0cbe\u0c97\u0cc1',
    '\u0cb8\u0cc1\u0c9f\u0ccd\u0c9f\u0cc1',
    '\u0cc2\u0ca4', '\u0c9a\u0cc0\u0caf\u0cc6',
    '\u0c89\u0cb8\u0cbf\u0cb0\u0cbe\u0c9f',
    '\u0c9a\u0cb2\u0ccd\u0cb2\u0cc1',
    '\u0cac\u0cc1\u0d16\u0cb0', '\u0c9c\u0ccd\u0cb5\u0cb0',
    '\u0ca1\u0c82\u0c95', '\u0c95\u0c9a\u0ccd\u0ccd\u0cc1',
    '\u0cb9\u0cbe\u0cb5\u0cc1',
    # Body parts
    '\u0ca4\u0cb2\u0cc6', '\u0cc7\u0ca6\u0cc6',
    '\u0cb9\u0cc1\u0c95\u0ccd', '\u0c95\u0c95\u0ccd\u0ca8\u0ccd\u0ca8\u0cc1',
    '\u0c95\u0cbf\u0cb5\u0cbf', '\u0c97\u0c82\u0c9f\u0cb2\u0cc1',
    # Emergency
    '\u0ca4\u0cc1\u0cb0\u0ccd\u0ca4\u0cc1',
    '\u0c86\u0cb8\u0ccd\u0caa\u0ca4\u0ccd\u0cb0\u0cc6',
    '\u0cb5\u0cc8\u0ca6\u0ccd\u0caf',
    '\u0ca8\u0cbe\u0caf', '\u0ca1\u0cc2\u0cac\u0cc1',
    '\u0cb9\u0cc3\u0ca6\u0caf\u0cbe\u0c98\u0cbe\u0caf\u0ca4',
    '\u0cb2\u0c95\u0cb5\u0cbe',
    # General medical
    '\u0c97\u0cbe\u0caf',    '\u0cb8\u0cc1\u0c9f\u0ccd\u0c9f\u0cc1',
    '\u0c9c\u0cbe\u0cb5\u0cc6', '\u0c86\u0c97\u0cc1',
    '\u0cb5\u0cbf\u0cb7 \u0c9f\u0cc6\u0c97\u0cc6\u0ca6\u0cc1',
    '\u0cb8\u0cbe\u0c82\u0c95\u0cc6 \u0c95\u0ca3\u0ccd\u0ca8\u0cc1',
]

# Hinglish / Kanglish transliterated keywords (Roman script)
# These catch queries written in Roman letters with Hindi/Kannada words
TRANSLITERATED_KEYWORDS = [
    # Common Hindi/Roman medical terms
    "dard", "dard ho raha", "dard hai",
    "khoon", "khoon beh raha", "khoon beh rahe",
    "chot", "chot lagi",
    "ghaav", "ghaav ho gaya",
    "jal gaya", "jala hua", "jalan",
    "toot gaya", "toota hua", "fracture hua",
    "moch aayi", "moch",
    "sujan", "soojh gaya", "sujh gaya",
    "behosh", "behosh ho gaya", "baisosh",
    "saans", "saans lene mein",
    "chakkar", "chakkar aa rahe",
    "ulti", "ulti ho rahi",
    "bukhar", "bukhar hai", "bukhar aa raha",
    "saanp", "saanp ne kaat liya", "saanp ne dasa",
    "bichhoo", "bichhoo ne dasa", "bichhoo ne kaata",
    "seene mein dard", "chati mein dard",
    "pet mein dard", "pet dard",
    "sir dard", "sir mein dard",
    "aankh", "kaan", "gala",
    "haath", "paon",
    "emergency", "hospital", "doctor",
    "ambulance", "aspatal", "asptal",
    "jharu", "daag", "rash",
    "bukhar", "tap",
    "daant", "daant lag gayi",
    "kaat liya", "kaat liye", "kutta kaat liya",
    "gir gaya", "gir ke", "gira hua",
    "gira",    "girna",
    # Kanglish / Kannada transliterations (Roman script)
    "novu", "novu aagide", "novu aagtide",
    "raktasravava", "rakta",
    "gaaya", "gaaya aagide",
    "suttikollu", "suttu",
    "muritu",
    "oota",
    "prajne illa",
    "usirata",
    "talisuttu",
    "vaanti",
    "jvar", "jwara",
    "haavu kacci", "haavu hulu",
    "talleya novu", "ede novu",
    "hotte novu", "kai novu",
    "kannu", "kivi", "gantalu",
    "turtu", "aspatriye", "vaidya",
    "visha", "hadayaaghaata",
    "maadbeku", "en maadbeku", "aadmeelu",
]




def is_first_aid_query(query: str) -> tuple:
    """
    Chatbot guardrail — strict.
    Only first-aid / emergency queries pass.
    Returns (is_valid: bool, reason: str).
    """
    q = query.lower().strip()

    if not q:
        return (True, "")  # empty handled by caller

    # 1. Chronic condition check (block)
    for condition in CHRONIC_CONDITIONS:
        if condition in q:
            return (
                False,
                f"This condition ({condition}) falls outside of immediate first-aid. "
                "No verified emergency guidelines found in our knowledge base. "
                "Please consult a doctor."
            )

    # 2. Non first-aid topic check (block)
    for topic in NON_FIRST_AID_TOPICS:
        if topic in q:
            return (
                False,
                f"This query is about {topic}, which is outside the scope of "
                "immediate first-aid guidance. Please consult a healthcare professional."
            )

    # 3. Positive check — query MUST contain at least one medical keyword
    #    This catches everything else (philosophy, cooking, travel, etc.)
    #    Detect script and check appropriate keyword lists
    has_hindi = bool(HINDI_SCRIPT.search(q))
    has_kannada = bool(KANNADA_SCRIPT.search(q))

    has_medical_keyword = any(kw in q for kw in MEDICAL_KEYWORDS)

    if not has_medical_keyword and has_hindi:
        has_medical_keyword = any(kw in q for kw in HINDI_MEDICAL_KEYWORDS)

    if not has_medical_keyword and has_kannada:
        has_medical_keyword = any(kw in q for kw in KANNADA_MEDICAL_KEYWORDS)

    if not has_medical_keyword:
        has_medical_keyword = any(kw in q for kw in TRANSLITERATED_KEYWORDS)

    if not has_medical_keyword:
        return (
            False,
            "This query does not appear to be about first-aid or a medical emergency. "
            "I can only help with immediate first-aid guidance. "
            "Please consult a doctor for other questions."
        )

    return (True, "")


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
