"""
llm_service.py - Arohan AI Text Generation
Uses Groq llama-3.3-70b-versatile
Responds in SAME language as user query.
3-layer script protection — no wrong language passes through.
"""

import os
import re
import logging
from groq import Groq
from app.services.ai.rag_service import rag_service
from app.services.ai.language_service import detect_language, normalize_supported_language
from app.services.ai.ollama_service import process_voice_with_ollama, USE_LOCAL_MODEL
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Lazy-loaded Groq client — reads env var on first use so config.py's load_dotenv() runs first
_groq_client = None

def _get_groq_client():
    """Return the Groq client, initializing it lazily on first call."""
    global _groq_client
    if _groq_client is None:
        # Explicitly load .env in case config.py hasn't initialized yet
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            _groq_client = Groq(api_key=api_key)
            logger.info("Groq client initialized (lazy)")
        else:
            logger.warning("GROQ_API_KEY not found — using fallback responses")
    return _groq_client

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


def process_voice_with_llm(text: str, context: str = "", language: str = "en", rag_source: str = "all") -> dict:
    """
    Process voice input using either fine-tuned Ollama model or Groq API based on configuration.
    
    Uses dual mode:
    - If USE_LOCAL_MODEL=true: Uses fine-tuned Ollama model
    - If USE_LOCAL_MODEL=false: Uses Groq API (existing behavior)
    """
    if USE_LOCAL_MODEL:
        logger.info("Using fine-tuned Ollama model")
        return process_voice_with_ollama(text, context, language, rag_source)

    requested_lang = normalize_supported_language(language)
    lang_info      = detect_language(text)
    language_code = lang_info["language_code"]
    language_name = lang_info["language_name"]
    is_emergency  = lang_info["is_emergency"]

    if context and requested_lang["language_name"] in ["English", "Hindi", "Kannada", "Hinglish", "Kanglish"]:
        language_code = requested_lang["language_code"]
        language_name = requested_lang["language_name"]

    logger.info(f"Language: {language_name} | Emergency: {is_emergency}")

    rag_context_raw = rag_service.retrieve_context(text, k=5, source=rag_source)
    rag_context     = rag_context_raw[:2000] if rag_context_raw else ""

    groq_client = _get_groq_client()
    if not groq_client:
        logger.error("GROQ_API_KEY not configured")
        return fallback_response(language_code, is_emergency)

    system_prompt = build_system_prompt(language_name, rag_context, is_emergency)

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": text}
            ],
            temperature=0.1,
            max_tokens=900,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.3,
        )

        response_text = response.choices[0].message.content.strip()

        # Layer 2 — check if wrong script detected
        if needs_retry(response_text, language_name):
            logger.warning(f"Wrong script for {language_name}. Retrying...")
            response_text = force_language_retry(text, rag_context, language_name, is_emergency)

        response_text = post_process(response_text, is_emergency)
        logger.info(f"Response: {response_text[:100]}...")

        return {
            "response_text": response_text,
            "language_code": language_code
        }

    except Exception as e:
        logger.error(f"Groq failed: {e}")
        return fallback_response(language_code, is_emergency)


def force_language_retry(text: str, rag_context: str, language_name: str, is_emergency: bool) -> str:
    """
    Layer 2 retry — ultra strict prompt for correct language.
    If still wrong → Layer 3 hardcoded fallback.
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

        retry = _get_groq_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": strict_prompt},
                {"role": "user",   "content": f"Patient complaint: {text}"}
            ],
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
                "3. Kapde dhile karo.\n"
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


def build_system_prompt(
    language_name: str,
    rag_context: str,
    is_emergency: bool
) -> str:

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

    return f"""You are Arohan AI, a calm medical first aid assistant for elderly Indians.

{emergency_block}RULES (Anisha's medical_safe template):
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

EXAMPLES:

User: "my nose is bleeding"
Response:
"For a nosebleed:
1. Sit upright and lean slightly forward.
2. Pinch the soft part of your nose firmly.
3. Hold for 10-15 minutes without releasing.
4. Breathe through your mouth calmly.
5. Apply cold cloth to bridge of nose.
6. Do not blow your nose for 15 minutes after bleeding stops.
Call 112 if bleeding does not stop after 20 minutes."

User (Hinglish): "mera haath is paining"
Response:
"Haath ke dard ke liye:
1. Haath ko rest do — use mat karo.
2. Ice ko kapde mein wrap karke 15 minute lagao.
3. Haath ko dil se upar uthao.
4. Zyada dard ho toh paracetamol lo.
5. 2 din mein theek na ho toh doctor ko dikhaao."

User (Kannada): "ನನ್ನ ಕೈ ನೋಯುತ್ತಿದೆ"
Response:
"ಕೈ ನೋವಿಗೆ:
1. ಕೈಗೆ ವಿಶ್ರಾಂತಿ ಕೊಡಿ.
2. ಐಸ್ ಅನ್ನು ಬಟ್ಟೆಯಲ್ಲಿ ಸುತ್ತಿ 15 ನಿಮಿಷ ಹಚ್ಚಿ.
3. ಕೈಯನ್ನು ಎದೆಗಿಂತ ಮೇಲೆ ಎತ್ತಿ.
4. ನೋವು ಜಾಸ್ತಿ ಇದ್ದರೆ ಪ್ಯಾರಾಸಿಟಮಾಲ್ ತೆಗೆದುಕೊಳ್ಳಿ.
5. 2 ದಿನದಲ್ಲಿ ಸರಿಯಾಗದಿದ್ದರೆ ಆಸ್ಪತ್ರೆಗೆ ಹೋಗಿ."

User (Kanglish): "my kai is paining"
Response:
"Kai novu ge:
1. Kai rest madi — use madabedi.
2. Ice cloth nalli sulidu 15 nimisha hachi.
3. Kai hrudaya matte mele elu.
4. Thumba novu idre paracetamol tago.
5. 2 dina inda mele aagilla andre doctor hatra hogo."

User (Hindi): "मेरा हाथ दर्द कर रहा है"
Response:
"हाथ के दर्द के लिए:
1. हाथ को आराम दें।
2. बर्फ को कपड़े में लपेटकर 15 मिनट लगाएं।
3. हाथ को दिल से ऊपर उठाएं।
4. ज्यादा दर्द हो तो पैरासिटामोल लें।
5. 2 दिन में ठीक न हो तो डॉक्टर को दिखाएं।"

MEDICAL KNOWLEDGE:
{rag_context if rag_context else 'Use general first aid knowledge.'}

Reply in {language_name} only. Follow the script rule strictly. Be calm and caring."""


def post_process(response_text: str, is_emergency: bool) -> str:
    if is_emergency and not response_text.startswith("🚨"):
        response_text = "🚨 " + response_text
    return response_text


def fallback_response(language_code: str, is_emergency: bool) -> dict:
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

