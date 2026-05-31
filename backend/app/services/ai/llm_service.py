"""
llm_service.py - Arohan AI Text Generation
Uses Groq llama-3.3-70b-versatile with emergency detection
"""

import os
import logging
from groq import Groq
from app.services.ai.rag_service import rag_service
from app.services.ai.language_service import detect_language

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client  = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def process_voice_with_llm(text: str, context: str = "", language: str = "en") -> dict:

    # Step 1: Detect language + emergency
    lang_info     = detect_language(text)
    language_code = lang_info["language_code"]
    language_name = lang_info["language_name"]
    instruction   = lang_info["instruction"]
    is_emergency  = lang_info["is_emergency"]

    logger.info(f"🌐 Language: {language_name} | Emergency: {is_emergency}")

    # Step 2: Get RAG context — more chunks, more detail
    rag_context_raw = rag_service.retrieve_context(text, k=5)
    rag_context     = rag_context_raw[:2000] if rag_context_raw else ""

    logger.info(f"📚 RAG context: {len(rag_context)} chars")

    if not groq_client:
        logger.error("❌ GROQ_API_KEY not configured")
        return fallback_response(language_name, rag_context, is_emergency)

    # Step 3: Build prompt
    system_prompt = build_system_prompt(
        language_name, instruction, rag_context, context, is_emergency
    )

    logger.info(f"📋 Prompt: {len(system_prompt)} chars | Query: {text[:50]}")

    # Step 4: Call Groq
    try:
        logger.info("🤖 Calling Groq llama-3.3-70b-versatile...")

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
        response_text = post_process(response_text, language_name, is_emergency)

        logger.info(f"✅ Groq response: {response_text[:100]}...")

        return {
            "response_text": response_text,
            "language_code": language_code
        }

    except Exception as e:
        logger.error(f"❌ Groq failed: {type(e).__name__}: {e}")

        # Retry with shorter context
        try:
            short_prompt = build_system_prompt(
                language_name, instruction, rag_context[:500], "", is_emergency
            )
            retry = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": short_prompt},
                    {"role": "user",   "content": text}
                ],
                temperature=0.1,
                max_tokens=600,
            )
            response_text = retry.choices[0].message.content.strip()
            response_text = post_process(response_text, language_name, is_emergency)
            logger.info(f"✅ Groq retry succeeded: {response_text[:80]}")
            return {
                "response_text": response_text,
                "language_code": language_code
            }

        except Exception as retry_error:
            logger.error(f"❌ Groq retry also failed: {retry_error}")
            return fallback_response(language_name, rag_context, is_emergency)


def build_system_prompt(
    language_name: str,
    instruction: str,
    rag_context: str,
    extra_context: str,
    is_emergency: bool
) -> str:

    emergency_block = ""
    if is_emergency:
        emergency_block = """
╔══════════════════════════════════════════════════════════════════╗
║  🚨 EMERGENCY DETECTED                                          ║
║  Give 6-8 detailed first aid steps from the knowledge base      ║
║  End with: "Call 112 or 108 immediately if condition is severe" ║
║  NEVER just say "Call 112" — always give first aid steps first  ║
╚══════════════════════════════════════════════════════════════════╝
"""

    return f"""You are Arohan, a health assistant for elderly Indians.

{emergency_block}

╔══════════════════════════════════════════════════════════════════╗
║  REPLY IN EXACTLY THIS LANGUAGE: {language_name}                 ║
╚══════════════════════════════════════════════════════════════════╝

{instruction}

═══════════════════════════════════════════════════════════════════

EXAMPLES:

User: "Oke" or "Ok"
✅ "Hello! How can I help you today?" (English)
✅ "Namaste! Aapki kya takleef hai?" (Hinglish)

User (English): "my nose is bleeding"
✅ CORRECT — Give 6+ steps:
"For a nosebleed:
1. Sit upright, lean slightly forward — never tilt head back.
2. Pinch the soft part of your nose firmly.
3. Hold pressure for 10-15 minutes without releasing.
4. Breathe through your mouth calmly.
5. Apply a cold cloth or ice pack to the bridge of your nose.
6. Do not blow your nose for 15 minutes after bleeding stops.
7. Avoid hot drinks or spicy food for several hours.
Call 112 if bleeding does not stop after 20 minutes."

User (English): "i got stroke"
✅ CORRECT — Give 6+ steps:
"🚨 Stroke signs are serious. Act immediately:
1. Call 112 or 108 right away — every minute matters.
2. Note the exact time symptoms started.
3. Help the person lie down safely on their side.
4. Do not give food, water, or any medicines.
5. Loosen tight clothing around neck and chest.
6. Stay with the person and keep them calm.
7. Do not let the person fall asleep.
8. Tell the doctor exactly when symptoms started."

User (English): "i got cut on my head"
✅ CORRECT — Give 6+ steps:
"For a head cut:
1. Apply firm pressure with a clean cloth for 10-15 minutes.
2. Do not lift the cloth — add more on top if soaked.
3. Keep the person sitting or lying still.
4. Once bleeding slows, gently clean with cool water.
5. Apply antiseptic like Betadine or Savlon.
6. Cover with a sterile bandage or gauze.
7. Check for signs of concussion — dizziness, confusion, vomiting.
Call 112 if bleeding does not stop or person feels dizzy."

═══════════════════════════════════════════════════════════════════

MEDICAL KNOWLEDGE (use as reference, do NOT copy word for word):
{rag_context if rag_context else 'Use general first aid knowledge.'}

RULES:
- Reply ONLY in {language_name}
- NEVER paste raw database text — rephrase it clearly
- NEVER start with "Based on our database" or "How can I help" for injury queries
- Give MINIMUM 6 numbered steps for every injury or symptom
- For emergencies: give all steps first, mention Call 112 at the END
- Use simple words — no medical jargon
- Be caring and calm
- Maximum response: 10 points
"""


def post_process(response_text: str, language_name: str, is_emergency: bool) -> str:
    if is_emergency and not response_text.startswith("🚨"):
        response_text = "🚨 " + response_text

    if "English" not in language_name:
        response_text = response_text.replace(
            "Please consult a doctor for confirmation.", ""
        ).strip()
        response_text = response_text.replace(
            "Please consult a doctor.", ""
        ).strip()

    return response_text


def fallback_response(language_name: str, rag_context: str, is_emergency: bool) -> dict:
    responses = {
        "English": {
            "emergency": "🚨 This sounds serious. Call 112 or 108 immediately.",
            "normal":    "Based on our medical database:\n\n"
        },
        "Hindi": {
            "emergency": "🚨 Yeh gambhir hai. Turant 112 ya 108 pe call karein.",
            "normal":    "Hamare medical database mein yeh mila:\n\n"
        },
        "Hindi-English mix": {
            "emergency": "🚨 Yeh serious hai. Turant 112 call karo.",
            "normal":    "Hamare database ke hisaab se:\n\n"
        },
        "Kannada": {
            "emergency": "🚨 Idhu gambheera. TURANT 112 annu call maadi.",
            "normal":    "Namma medical database nalli sikithu:\n\n"
        },
        "Kannada-English mix": {
            "emergency": "🚨 Idhu serious. TURANT 112 call maadi.",
            "normal":    "Namma database nalli sikithu:\n\n"
        },
        "Kannada-Hindi mix": {
            "emergency": "🚨 Yeh serious hai. Turant 112 call maadi.",
            "normal":    "Namma database nalli sikithu:\n\n"
        },
        "Hindi-Urdu": {
            "emergency": "🚨 Yeh khatarnak hai. Foran 112 pe call karein.",
            "normal":    "Hamare database mein yeh mila:\n\n"
        },
    }

    lang_key      = language_name if language_name in responses else "English"
    type_key      = "emergency" if is_emergency else "normal"
    response_text = responses[lang_key][type_key]

    if rag_context and not is_emergency:
        response_text += rag_context.strip()[:800]

    lang_code_map = {
        "English":             "en-IN",
        "Hindi":               "hi-IN",
        "Hindi-English mix":   "hi-IN",
        "Hindi-Urdu":          "hi-IN",
        "Kannada":             "kn-IN",
        "Kannada-English mix": "kn-IN",
        "Kannada-Hindi mix":   "kn-IN",
    }

    return {
        "response_text": response_text,
        "language_code": lang_code_map.get(language_name, "en-IN")
    }