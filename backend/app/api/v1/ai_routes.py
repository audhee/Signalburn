"""
ai_routes.py - Arohan AI API Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from app.models.ai_models import VoicePromptPayload
from app.services.ai.llm_service import process_voice_with_llm
from app.services.ai.voice_service import transcribe_audio, text_to_indian_voice
import tempfile
import os
import base64
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


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
    text    = payload.text.strip()
    context = payload.context.strip()

    # Each answer stored as "Q: question\nA: answer" — split by newline
    lines = [l.strip() for l in context.split("\n") if l.strip()]

    # Count Q: lines = number of answers given so far
    answer_count  = len([l for l in lines if l.startswith("Q: ")])

    # Already asked questions
    already_asked = [l.replace("Q: ", "").strip() for l in lines if l.startswith("Q: ")]

    # Full context for dynamic question detection
    accumulated = text + " " + " ".join([
        l.replace("A: ", "").replace("Q: ", "") for l in lines
    ])

    logger.info(f"Guided query — answer_count: {answer_count}, lines: {len(lines)}")

    # Step 1 — Fixed questions (0, 1, 2)
    if answer_count < len(FIXED_QUESTIONS):
        return JSONResponse(content={
            "success":         True,
            "mode":            "question",
            "question":        FIXED_QUESTIONS[answer_count],
            "question_num":    answer_count + 1,
            "total_questions": MAX_QUESTIONS,
            "audio_base64":    None,
        })

    # Step 2 — Dynamic questions (3, 4)
    dynamic_done = answer_count - len(FIXED_QUESTIONS)
    if dynamic_done < (MAX_QUESTIONS - len(FIXED_QUESTIONS)):
        return JSONResponse(content={
            "success":         True,
            "mode":            "question",
            "question":        get_dynamic_question(accumulated, already_asked),
            "question_num":    answer_count + 1,
            "total_questions": MAX_QUESTIONS,
            "audio_base64":    None,
        })

    # Step 3 — All 5 answered → generate final answer
    full_context = f"Initial complaint: {text}\n\nAdditional details:\n{context}"
    try:
        result        = await run_in_threadpool(process_voice_with_llm, full_context, "", payload.language)
        answer_text   = result["response_text"]
        language_code = result["language_code"]

        audio_b64 = None
        try:
            audio_bytes = await run_in_threadpool(text_to_indian_voice, answer_text, language_code)
            audio_b64   = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"TTS failed: {e}")

        return JSONResponse(content={
            "success":      True,
            "mode":         "answer",
            "response":     answer_text,
            "language":     language_code,
            "audio_base64": audio_b64,
        })

    except Exception as e:
        logger.error(f"Guided query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe-only")
async def transcribe_only(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
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
        return JSONResponse(content={"success": True, "transcription": transcribed_text})

    except Exception as e:
        logger.error(f"Transcribe-only error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.unlink(tmp_path)
            except: pass