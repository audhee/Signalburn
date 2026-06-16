"""
ai_routes.py - Arohan AI API Routes
Language locked from initial complaint — never re-detected from answers.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from app.models.ai_models import VoicePromptPayload, MultimodalUploadResponse, ChatMessage, ChatHistoryResponse
from app.services.ai.llm_service import process_voice_with_llm
from app.services.ai.voice_service import transcribe_audio
from app.services.ai.speech_service import transcribe_audio as gemini_transcribe
from app.services.ai.language_service import detect_language, normalize_supported_language, sanitize_text_for_language
from app.services.ai.multimodal_service import (
    process_multimodal_query, 
    get_mime_type, 
    is_image, 
    is_video, 
    is_document
)
from app.services.ai.tts_service import synthesize_speech
from app.services.ai.prompt_utils import is_first_aid_query
from app.services.ai.rag_service import rag_service
import tempfile
import os
import base64
import logging
import uuid
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== IN-MEMORY CHAT HISTORY ====================
_chat_sessions: dict = {}

def _get_or_create_session(session_id: str) -> list:
    if session_id not in _chat_sessions:
        _chat_sessions[session_id] = []
    return _chat_sessions[session_id]


def _sanitize_guided_context(context: str, locked_language: str) -> str:
    cleaned_lines = []
    for raw_line in [line.strip() for line in context.split("\n") if line.strip()]:
        if raw_line.startswith("A: "):
            answer = raw_line[3:].strip()
            cleaned_lines.append(f"A: {sanitize_text_for_language(answer, locked_language)}")
        else:
            cleaned_lines.append(raw_line)
    return "\n".join(cleaned_lines)


# ==================== GUIDED QUESTIONS (English only) ====================

FIXED_QUESTIONS = [
    "What happened?",
    "What is the age and gender of the person?",
    "Do they have any medical conditions or take regular medication?",
]


def get_dynamic_question(context: str, already_asked: list) -> str:
    import re
    context_lower = context.lower()
    
    # 1. Stroke / Paralysis
    if re.search(r"\b(stroke|paralysis|numb|droop|slur|facial|speech)\b", context_lower):
        candidates = [
            "Is there weakness or numbness on one side of the body?",
            "Is the person having difficulty speaking or understanding speech?"
        ]
    # 2. Chest Pain / Cardiac / Heart Attack
    elif re.search(r"\b(chest\s*pain|heart\s*attack|cardiac|angina)\b", context_lower):
        candidates = [
            "Is the pain radiating to the arm, neck, or jaw?",
            "Is the person experiencing shortness of breath or sweating?"
        ]
    # 3. Collapse / Unconscious
    elif re.search(r"\b(collapse|unconscious|faint|passed\s*out|responsive)\b", context_lower):
        candidates = ["Is the person breathing properly?", "Is the person conscious?"]
    # 4. Poison / Swallowed
    elif re.search(r"\b(poison|swallowed|toxin|chemical|ingest)\b", context_lower):
        candidates = ["Is the person vomiting?", "Is the person conscious?"]
    # 5. Burn
    elif re.search(r"\b(burn|scald|fire|acid\s*burn)\b", context_lower):
        candidates = ["Is the burn large or deep?", "Is there blistering?"]
    # 6. Bleeding / Cut (with word boundaries to prevent matching 'acute')
    elif re.search(r"\b(bleeding|bleed|cut|cuts|wound|injury|laceration|blood)\b", context_lower):
        candidates = ["Is the bleeding heavy?", "Has it stopped?"]
    # 7. Breathing / Asthma
    elif re.search(r"\b(breathing|breath|asthma|choke|suffocate|wheez)\b", context_lower):
        candidates = ["Is breathing getting worse?", "Is there chest tightness?"]
    # 8. Dizzy / Sweating
    elif re.search(r"\b(dizzy|sweat|giddy|lighthead|weakness)\b", context_lower):
        candidates = ["Is the person feeling weak or about to faint?", "When did this start?"]
    else:
        candidates = ["Is the person conscious?", "Is the person breathing properly?"]
    
    for q in candidates:
        if q not in already_asked:
            return q
    return "When did this start?"


MAX_QUESTIONS = 5


# ==================== CHAT ENDPOINT (Anisha's chatbot guardrail) ====================

class ChatQuery(BaseModel):
    question: str
    language: str = "en"
    rag_source: str = "sashwat_optimized"  # Always use sashwat_optimized RAG


@router.post("/chat")
async def chat(query: ChatQuery):
    """
    Anisha's first-aid chatbot — integrated into Arohan backend.
    Uses existing RAG service for retrieval + guardrail to reject non-first-aid queries.
    Returns {"answer": ...}.
    """
    user_question = query.question.strip()
    if not user_question:
        return {"answer": "Please ask a first-aid related question."}

    # 1. IMMEDIATE GUARDRAIL: Reject chronic / out-of-scope queries
    is_valid, reason = is_first_aid_query(user_question)
    if not is_valid:
        logger.info(f"Chat guardrail blocked: {reason}")
        return {"answer": f"⚠️ {reason}"}

    # 2. RAG retrieval with similarity scores
    try:
        context, scores = await run_in_threadpool(
            rag_service.retrieve_context_with_scores,
            user_question, 5, query.rag_source,
        )
    except Exception as e:
        logger.error(f"RAG retrieval failed in /chat: {e}")
        return {
            "answer": "⚠️ Unable to search medical knowledge base. "
                      "Please try again or consult a doctor."
        }

    # 3. SIMILARITY THRESHOLD CHECK
    # ChromaDB cosine scores: higher = more relevant.
    # Anisha's original used L2 distance > 1.2 → roughly cosine sim < 0.4
    if not context or not scores:
        return {
            "answer": "⚠️ No relevant first-aid information found for your query. "
                      "Please consult a doctor."
        }
    best_score = max(scores)
    if best_score < 0.45:
        logger.info(f"Chat similarity too low: best={best_score:.3f} for '{user_question}'")
        return {
            "answer": "⚠️ This query does not match our first-aid knowledge base. "
                      "No verified emergency guidelines found. Please consult a doctor."
        }

    # 4. Generate response using Groq LLM + sashwat_optimized RAG
    #    Pass prefetched RAG context to avoid double retrieval
    try:
        result = await run_in_threadpool(
            process_voice_with_llm,
            text=user_question,
            context="",
            language=query.language,
            prefetched_rag_context=context,
        )
        answer = result.get("response_text", "")
        if answer:
            return {"answer": answer}
    except Exception as e:
        logger.error(f"LLM generation failed in /chat: {e}")

    # 5. Hardcoded fallback
    return {
        "answer": (
            "⚠️ I could not generate a response. Here is general first-aid advice:\n"
            "1. Keep the person calm and comfortable.\n"
            "2. Check if they are breathing normally.\n"
            "3. Apply gentle pressure if there is bleeding.\n"
            "4. Do not give medicines without doctor advice.\n"
            "5. Call 112 or 108 if condition gets worse."
        )
    }


# ==================== RAG DEBUG ENDPOINT ====================


class RagDebugQuery(BaseModel):
    query: str
    k: int = 5
    source: str = "all"


@router.post("/rag-debug")
async def rag_debug(payload: RagDebugQuery):
    """
    Debug endpoint — returns per-source RAG chunks with similarity scores.
    Use this to inspect which knowledge base(s) contributed what content
    and how relevant each chunk is.

    Args:
        query:  The medical question to search for.
        k:      Number of chunks to retrieve per source (default 5).
        source: RAG source filter — "all", "sashwat_optimized", "arohan", etc.
    """
    query_text = payload.query.strip()
    if not query_text:
        return {"error": "Query cannot be empty."}

    try:
        from fastapi.responses import JSONResponse
        import json

        debug_result = await run_in_threadpool(
            rag_service.retrieve_debug,
            query_text,
            payload.k,
            payload.source,
        )

        logger.error(f"DEBUG RESULT TYPE: {type(debug_result)}")
        logger.error(f"DEBUG RESULT KEYS: {list(debug_result.keys())}")
        logger.error("ABOUT TO SERIALIZE DEBUG RESULT")

        json.dumps(debug_result)

        logger.error("JSON.DUMPS SUCCEEDED")

        return JSONResponse(content=debug_result)

    except Exception as e:
        logger.error(f"RAG DEBUG RETRIEVAL FAILED: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== EXISTING ENDPOINTS (100% UNCHANGED) ====================

@router.post("/process-voice")
async def process_voice_input(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
    language_code: str = Form(default="hi-IN"),
):
    tmp_path = None
    try:
        suffix = ".m4a"
        if audio.filename:
            ext = audio.filename.split(".")[-1]
            suffix = f".{ext}" if ext else ".m4a"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        normalized_language = normalize_supported_language(language_code)["language_code"] if language_code else ""
        
        # Try Groq first, fallback to Gemini
        try:
            transcribed_text = await run_in_threadpool(transcribe_audio, tmp_path, normalized_language)
        except Exception as e:
            logger.warning(f"Groq transcription failed: {e}, trying Gemini fallback...")
            try:
                with open(tmp_path, "rb") as audio_file:
                    transcribed_text = await run_in_threadpool(gemini_transcribe, audio_file, os.path.basename(tmp_path))
            except Exception as gemini_e:
                logger.error(f"Gemini transcription also failed: {gemini_e}")
                transcribed_text = "Could not understand audio. Please try speaking clearly."
        
        if normalized_language:
            transcribed_text = sanitize_text_for_language(
                transcribed_text,
                normalized_language,
                fallback=transcribed_text.strip() or "Unclear response"
            )
        llm_result       = await run_in_threadpool(process_voice_with_llm, transcribed_text, "", language_code, "sashwat_optimized")  # sashwat_optimized RAG only
        answer_text      = llm_result["response_text"]
        detected_lang    = llm_result["language_code"]

        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(synthesize_speech, answer_text, detected_lang)
            audio_b64   = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"TTS failed: {e}")

        return JSONResponse(content={
            "success": True, "input_type": "voice",
            "transcription": transcribed_text, "response": answer_text,
            "language": detected_lang, "session_id": session_id,
            "audio_base64": audio_b64,
        })

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.unlink(tmp_path)
            except: pass


@router.post("/text-query")
async def process_text_input(payload: VoicePromptPayload):
    try:
        llm_result    = await run_in_threadpool(
            process_voice_with_llm,
            payload.text,
            payload.context,
            payload.language,
            "sashwat_optimized",
        )
        answer_text   = llm_result["response_text"]
        detected_lang = llm_result["language_code"]

        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(synthesize_speech, answer_text, detected_lang)
            audio_b64   = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"TTS failed: {e}")

        return JSONResponse(content={
            "success": True, "input_type": "text",
            "transcription": payload.text, "response": answer_text,
            "language": detected_lang, "audio_base64": audio_b64,
        })

    except Exception as e:
        logger.error(f"Error in /text-query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/guided-query")
async def guided_query(payload: VoicePromptPayload):
    """
    Language lock system:
    - First call (no context) → detect language from complaint → lock it → return detected_language
    - All subsequent calls → frontend sends locked language → use it, never re-detect
    """
    text = payload.text.strip()
    raw_context = payload.context.strip()

    if not raw_context:
        lang_info = detect_language(text)
        locked_language = lang_info["language_code"]
        locked_language_name = lang_info["language_name"]
        context = ""
        logger.info(f"Language detected and locked: {locked_language} ({locked_language_name})")
    else:
        locked_language = normalize_supported_language(payload.language)["language_code"]
        locked_language_name = normalize_supported_language(payload.language)["language_name"]
        context = _sanitize_guided_context(raw_context, locked_language)
        logger.info(f"Using locked language: {locked_language} ({locked_language_name})")

    lines         = [l.strip() for l in context.split("\n") if l.strip()]
    answer_count  = len([l for l in lines if l.startswith("Q: ")])
    already_asked = [l.replace("Q: ", "").strip() for l in lines if l.startswith("Q: ")]
    accumulated   = text + " " + " ".join([l.replace("A: ", "").replace("Q: ", "") for l in lines])

    logger.info(f"Guided query - answer_count: {answer_count}")

    # Step 1 — Fixed questions (English only)
    if answer_count < len(FIXED_QUESTIONS):
        question_text = FIXED_QUESTIONS[answer_count]
        # Generate TTS audio for the question
        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(synthesize_speech, question_text, locked_language)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"TTS for question failed: {e}")
        return JSONResponse(content={
            "success":           True,
            "mode":              "question",
            "question":          question_text,
            "question_num":      answer_count + 1,
            "total_questions":   MAX_QUESTIONS,
            "audio_base64":      audio_b64,
            "detected_language": locked_language,
        })

    # Step 2 — Dynamic questions (English only)
    dynamic_done = answer_count - len(FIXED_QUESTIONS)
    if dynamic_done < (MAX_QUESTIONS - len(FIXED_QUESTIONS)):
        question_text = get_dynamic_question(accumulated, already_asked)
        # Generate TTS audio for the question
        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(synthesize_speech, question_text, locked_language)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"TTS for dynamic question failed: {e}")
        return JSONResponse(content={
            "success":           True,
            "mode":              "question",
            "question":          question_text,
            "question_num":      answer_count + 1,
            "total_questions":   MAX_QUESTIONS,
            "audio_base64":      audio_b64,
            "detected_language": locked_language,
        })

    # Step 3 — Final answer (sashwat_optimized RAG only)
    full_context = f"Additional patient details:\n{context}"
    try:
        result        = await run_in_threadpool(
            process_voice_with_llm,
            text,
            full_context,
            locked_language,
            "sashwat_optimized",
        )
        answer_text   = result["response_text"]
        language_code = result["language_code"]

        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(synthesize_speech, answer_text, language_code)
            audio_b64   = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"TTS failed: {e}")

        return JSONResponse(content={
            "success":           True,
            "mode":              "answer",
            "response":          answer_text,
            "language":          language_code,
            "audio_base64":      audio_b64,
            "detected_language": locked_language,
        })

    except Exception as e:
        logger.error(f"Guided query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe-only")
async def transcribe_only(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
    language_code: str = Form(default=""),
):
    tmp_path = None
    try:
        suffix = ".m4a"
        if audio.filename:
            ext = audio.filename.split(".")[-1]
            suffix = f".{ext}" if ext else ".m4a"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        normalized_language = normalize_supported_language(language_code)["language_code"] if language_code else ""
        
        # Try Groq first, fallback to Gemini
        try:
            transcribed_text = await run_in_threadpool(transcribe_audio, tmp_path, normalized_language)
        except Exception as e:
            logger.warning(f"Groq transcription failed: {e}, trying Gemini fallback...")
            try:
                with open(tmp_path, "rb") as audio_file:
                    transcribed_text = await run_in_threadpool(gemini_transcribe, audio_file, os.path.basename(tmp_path))
            except Exception as gemini_e:
                logger.error(f"Gemini transcription also failed: {gemini_e}")
                return JSONResponse(
                    content={
                        "success": False,
                        "error": "Could not transcribe audio. Please try again.",
                        "transcription": "",
                    }
                )
        
        if normalized_language:
            transcribed_text = sanitize_text_for_language(
                transcribed_text,
                normalized_language,
                fallback=transcribed_text.strip() or "Unclear response"
            )
        return JSONResponse(content={"success": True, "transcription": transcribed_text})

    except Exception as e:
        logger.error(f"Transcribe-only error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.unlink(tmp_path)
            except: pass


# ==================== FIXED VISION ENDPOINT ====================




# ==================== NEW MULTIMODAL ENDPOINTS ====================

@router.post("/multimodal-upload")
async def multimodal_upload(
    media: UploadFile = File(...),
    text: str = Form(default=""),
    session_id: str = Form(default=""),
    language_code: str = Form(default=""),
):
    """
    Full multimodal pipeline:
    Upload Image/Video/File + Optional Text → Groq Vision Analysis →
    Severity Classification → First Aid Steps → TTS Audio →
    Returns JSON with base64 audio (web-compatible).
    """
    tmp_path = None
    generated_session = session_id or str(uuid.uuid4())[:8]

    try:
        # Save uploaded file
        suffix = ".jpg"
        if media.filename:
            ext = media.filename.split(".")[-1].lower()
            suffix = f".{ext}"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await media.read()
            tmp.write(content)
            tmp_path = tmp.name

        file_size_mb = len(content) / (1024 * 1024)
        logger.info(f"[{generated_session}] Media uploaded: {media.filename} ({media.content_type}, {file_size_mb:.2f} MB)")

        mime_type = media.content_type
        if not mime_type or mime_type == "application/octet-stream":
            mime_type = get_mime_type(media.filename or "")

        # Call Groq Multimodal Processor
        result = await run_in_threadpool(
            process_multimodal_query,
            text,
            content,
            mime_type,
            media.filename or "unknown",
            ""
        )

        response_text = result["response_text"]
        detected_lang = result["language_code"]
        severity = result["severity"]

        logger.info(f"[{generated_session}] Groq multimodal response: {response_text[:200]}")

        # Extract first aid text (everything after "FIRST AID:") if it exists, otherwise keep full response
        first_aid_text = response_text
        if "FIRST AID:" in response_text:
            first_aid_text = response_text.split("FIRST AID:")[-1].strip()

        # Generate TTS audio
        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(
                synthesize_speech, first_aid_text, detected_lang
            )
            if audio_bytes:
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as tts_err:
            logger.error(f"TTS failed: {tts_err}")

        logger.info(f"[{generated_session}] Severity: {severity}, Audio: {'yes' if audio_b64 else 'no'}")

        # Save to chat history
        chat_history = _get_or_create_session(generated_session)
        timestamp = datetime.now().isoformat()
        chat_history.append({
            "role": "user",
            "content": text if text else f"Uploaded {media.filename}",
            "media_type": mime_type,
            "timestamp": timestamp
        })
        chat_history.append({
            "role": "assistant",
            "content": first_aid_text,
            "media_type": None,
            "timestamp": timestamp
        })

        # Return JSON (web-compatible, no CORS header issues)
        return JSONResponse(content={
            "success": True,
            "response": first_aid_text,
            "severity": severity,
            "language_code": detected_lang,
            "session_id": generated_session,
            "audio_base64": audio_b64,
            "media_filename": media.filename or "unknown",
            "media_type": mime_type,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{generated_session}] Multimodal pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.unlink(tmp_path)
            except: pass


@router.post("/multimodal-text-query", response_model=MultimodalUploadResponse)
async def multimodal_text_query(
    media: UploadFile = File(...),
    text: str = Form(default=""),
    session_id: str = Form(default=""),
):
    """
    Same as multimodal-upload but returns structured Pydantic model.
    Use this when frontend wants to handle TTS itself or show text first.
    """
    tmp_path = None
    generated_session = session_id or str(uuid.uuid4())[:8]

    try:
        mime_type = get_mime_type(media.filename or "")
        if not (is_image(mime_type) or is_video(mime_type) or is_document(mime_type)):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {mime_type}"
            )

        suffix = f".{media.filename.split('.')[-1]}" if media.filename and "." in media.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await media.read()
            tmp.write(content)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            file_bytes = f.read()

        result = await run_in_threadpool(
            process_multimodal_query,
            text,
            file_bytes,
            mime_type,
            media.filename or "unknown",
            ""
        )

        answer_text = result["response_text"]
        detected_language_code = result["language_code"]
        severity = result["severity"]

        # Save to chat history
        chat_history = _get_or_create_session(generated_session)
        timestamp = datetime.now().isoformat()
        
        chat_history.append({
            "role": "user",
            "content": text if text else f"Uploaded {media.filename}",
            "media_url": tmp_path,
            "media_type": mime_type,
            "timestamp": timestamp
        })
        chat_history.append({
            "role": "assistant",
            "content": answer_text,
            "media_url": None,
            "media_type": None,
            "timestamp": timestamp
        })

        return MultimodalUploadResponse(
            response=answer_text,
            transcription=text,
            language=detected_language_code.split("-")[0],
            language_code=detected_language_code,
            severity=severity,
            media_type="image" if is_image(mime_type) else ("video" if is_video(mime_type) else "document"),
            media_filename=media.filename or "unknown",
            rag_context_used=True,
            audio_url=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{generated_session}] Multimodal text query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat-history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """Retrieve chat history for a given session."""
    history = _chat_sessions.get(session_id, [])
    messages = [
        ChatMessage(
            role=msg["role"],
            content=msg["content"],
            media_url=msg.get("media_url"),
            media_type=msg.get("media_type"),
            timestamp=msg.get("timestamp")
        )
        for msg in history
    ]
    return ChatHistoryResponse(session_id=session_id, messages=messages)


@router.delete("/chat-history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session."""
    if session_id in _chat_sessions:
        del _chat_sessions[session_id]
    return {"status": "cleared", "session_id": session_id}


@router.get("/supported-media-types")
async def supported_media_types():
    """Return list of supported media types for frontend reference."""
    return {
        "images": ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"],
        "videos": ["video/mp4", "video/mpeg", "video/mov", "video/avi", "video/x-flv", "video/mpg", "video/webm", "video/wmv", "video/3gpp"],
        "documents": ["application/pdf", "text/plain", "text/csv", "application/json", 
                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                      "application/rtf"]
    }


