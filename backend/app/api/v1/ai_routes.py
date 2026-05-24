"""
ai_routes.py - Arohan AI API Routes
Language locked from initial complaint — never re-detected from answers.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, Response
from fastapi.concurrency import run_in_threadpool
from app.models.ai_models import VoicePromptPayload, MultimodalUploadResponse, ChatMessage, ChatHistoryResponse
from app.services.ai.llm_service import process_voice_with_llm
from app.services.ai.voice_service import transcribe_audio, text_to_indian_voice
from app.services.ai.language_service import detect_language, normalize_supported_language, sanitize_text_for_language
from app.services.ai.multimodal_service import (
    process_multimodal_query, 
    get_mime_type, 
    is_image, 
    is_video, 
    is_document,
    build_multimodal_prompt
)
from app.services.ai.tts_service import synthesize_speech
import tempfile
import os
import base64
import logging
import uuid
from datetime import datetime

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


# ==================== EXISTING HELPERS (UNCHANGED) ====================

def get_dynamic_question(context: str, already_asked: list) -> str:
    context_lower = context.lower()
    if "collapse" in context_lower or "unconscious" in context_lower:
        candidates = ["Is the person breathing properly?", "Is the person conscious?"]
    elif "poison" in context_lower or "swallowed" in context_lower:
        candidates = ["Is the person vomiting?", "Is the person conscious?"]
    elif "burn" in context_lower:
        candidates = ["Is the burn large or deep?", "Is there blistering?"]
    elif "bleeding" in context_lower or "cut" in context_lower:
        candidates = ["Is the bleeding heavy?", "Has it stopped?"]
    elif "breathing" in context_lower or "asthma" in context_lower:
        candidates = ["Is breathing getting worse?", "Is there chest tightness?"]
    elif "dizzy" in context_lower or "sweating" in context_lower:
        candidates = ["Is the person feeling weak or about to faint?", "When did this start?"]
    else:
        candidates = ["Is the person conscious?", "Is the person breathing properly?"]
    for q in candidates:
        if q not in already_asked:
            return q
    return "When did this start?"


FIXED_QUESTIONS = [
    "What happened?",
    "What is the age and gender of the person?",
    "Do they have any medical conditions or take regular medication?",
]
MAX_QUESTIONS = 5


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

        transcribed_text = await run_in_threadpool(transcribe_audio, tmp_path)
        llm_result       = await run_in_threadpool(process_voice_with_llm, transcribed_text, "", language_code)
        answer_text      = llm_result["response_text"]
        detected_lang    = llm_result["language_code"]

        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(text_to_indian_voice, answer_text, detected_lang)
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
        llm_result    = await run_in_threadpool(process_voice_with_llm, payload.text, payload.context, payload.language)
        answer_text   = llm_result["response_text"]
        detected_lang = llm_result["language_code"]

        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(text_to_indian_voice, answer_text, detected_lang)
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
        context = ""
        logger.info(f"Language detected and locked: {locked_language}")
    else:
        locked_language = normalize_supported_language(payload.language)["language_code"]
        context = _sanitize_guided_context(raw_context, locked_language)
        logger.info(f"Using locked language: {locked_language}")

    lines         = [l.strip() for l in context.split("\n") if l.strip()]
    answer_count  = len([l for l in lines if l.startswith("Q: ")])
    already_asked = [l.replace("Q: ", "").strip() for l in lines if l.startswith("Q: ")]
    accumulated   = text + " " + " ".join([l.replace("A: ", "").replace("Q: ", "") for l in lines])

    logger.info(f"Guided query - answer_count: {answer_count}")

    # Step 1 — Fixed questions
    if answer_count < len(FIXED_QUESTIONS):
        return JSONResponse(content={
            "success":           True,
            "mode":              "question",
            "question":          FIXED_QUESTIONS[answer_count],
            "question_num":      answer_count + 1,
            "total_questions":   MAX_QUESTIONS,
            "audio_base64":      None,
            "detected_language": locked_language,
        })

    # Step 2 — Dynamic questions
    dynamic_done = answer_count - len(FIXED_QUESTIONS)
    if dynamic_done < (MAX_QUESTIONS - len(FIXED_QUESTIONS)):
        return JSONResponse(content={
            "success":           True,
            "mode":              "question",
            "question":          get_dynamic_question(accumulated, already_asked),
            "question_num":      answer_count + 1,
            "total_questions":   MAX_QUESTIONS,
            "audio_base64":      None,
            "detected_language": locked_language,
        })

    # Step 3 — Final answer
    full_context = f"Additional patient details:\n{context}"
    try:
        result        = await run_in_threadpool(process_voice_with_llm, text, full_context, locked_language)
        answer_text   = result["response_text"]
        language_code = result["language_code"]

        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(text_to_indian_voice, answer_text, language_code)
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
        transcribed_text = await run_in_threadpool(transcribe_audio, tmp_path, normalized_language)
        if normalized_language:
            transcribed_text = sanitize_text_for_language(transcribed_text, normalized_language)
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
    Upload Image/Video/File + Optional Text → Gemini Vision Analysis →
    Severity Classification → First Aid Steps → TTS Audio →
    Returns JSON with base64 audio (web-compatible).
    """
    tmp_path = None
    generated_session = session_id or str(uuid.uuid4())[:8]

    try:
        from groq import Groq
        
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        if not GROQ_API_KEY:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
        
        groq_client = Groq(api_key=GROQ_API_KEY)

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

        # Read bytes and encode as base64 for Groq Vision
        with open(tmp_path, "rb") as f:
            media_bytes = f.read()

        mime_type = media.content_type or "image/jpeg"
        image_b64 = base64.b64encode(media_bytes).decode("utf-8")
        image_data_url = f"data:{mime_type};base64,{image_b64}"

        # Build prompt for Groq Vision
        user_complaint = text.strip() if text.strip() else "Please analyze this injury"

        vision_prompt = f"""You are a medical first-aid assistant analyzing an injury image.

User complaint: {user_complaint}

Analyze the image and provide:
1. SEVERITY: classify as exactly one of: emergency, moderate, minor
2. FIRST AID: give 6 to 8 clear numbered first aid steps

Format your response EXACTLY like this:
SEVERITY: minor
FIRST AID:
1. Step one
2. Step two
...

Rules:
- emergency = severe bleeding, deep wounds, unconscious, broken bones visible, burns covering large area
- moderate = moderate wounds, sprains, small burns, cuts needing stitches
- minor = small cuts, bruises, mild abrasions
- Always give practical first aid steps
- Keep steps simple and clear
- End with: Call 112 if condition worsens"""

        # Call Groq Vision (Llama 4 Scout — free tier multimodal)
        response = await run_in_threadpool(
            lambda: groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_data_url}
                            }
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=1024,
            )
        )

        response_text = response.choices[0].message.content.strip()
        logger.info(f"[{generated_session}] Groq vision response: {response_text[:200]}")

        # Parse severity from response
        severity = "minor"
        response_lower = response_text.lower()
        if "severity: emergency" in response_lower:
            severity = "emergency"
        elif "severity: moderate" in response_lower:
            severity = "moderate"
        elif "severity: minor" in response_lower:
            severity = "minor"

        # Extract first aid text (everything after "FIRST AID:")
        first_aid_text = response_text
        if "FIRST AID:" in response_text:
            first_aid_text = response_text.split("FIRST AID:")[-1].strip()

        # Generate TTS audio
        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(
                text_to_indian_voice, first_aid_text, "en-IN"
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
            "language_code": "en-IN",
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


