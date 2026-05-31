"""
ai_routes.py - Arohan AI API Routes

Accepts BOTH voice and text input, returns TEXT output only.

Pipeline:
    Voice  → Groq Whisper STT → language detection → RAG + Groq LLM → JSON
    Text                       → language detection → RAG + Groq LLM → JSON
"""

import logging
import os
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.models.ai_models import HealthQueryResponse, VoicePromptPayload
from app.services.ai.llm_service import process_voice_with_llm
from app.services.ai.voice_service import transcribe_audio

logger = logging.getLogger(__name__)
router = APIRouter()


# ═════════════════════════════════════════════════════════════════════════════
#  ENDPOINT 1 — VOICE INPUT → TEXT OUTPUT
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/process-voice")
async def process_voice_input(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
    language_code: str = Form(default="hi-IN"),
):
    """
    Accept an audio file, transcribe it with Groq Whisper, generate a text
    answer with Groq LLM + RAG, and return JSON.
    """
    tmp_path = None

    try:
        # 1. Save uploaded audio to a temp file
        suffix = ".m4a"
        if audio.filename:
            ext = audio.filename.rsplit(".", 1)[-1]
            suffix = f".{ext}" if ext else ".m4a"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        logger.info("[%s] Voice input received: %d bytes", session_id, len(content))

        # 2. Groq Whisper STT → text
        transcribed_text = await run_in_threadpool(transcribe_audio, tmp_path)
        logger.info("[%s] Transcribed: %s", session_id, transcribed_text)

        # 3. Groq LLM + RAG → answer text
        llm_result = await run_in_threadpool(
            process_voice_with_llm,
            transcribed_text,
            language=language_code,
        )

        answer_text = llm_result["response_text"]
        detected_lang = llm_result["language_code"]

        logger.info("[%s] AI answer: %s", session_id, answer_text[:80])

        # 4. Return JSON (text only, no audio)
        return JSONResponse(content={
            "success": True,
            "input_type": "voice",
            "transcription": transcribed_text,
            "response": answer_text,
            "language": detected_lang,
            "session_id": session_id,
        })

    except Exception as exc:
        logger.error("[%s] Voice processing error: %s", session_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ═════════════════════════════════════════════════════════════════════════════
#  ENDPOINT 2 — TEXT INPUT → TEXT OUTPUT
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/text-query", response_model=HealthQueryResponse)
async def process_text_input(payload: VoicePromptPayload):
    """
    Accept typed text, generate a text answer with Groq LLM + RAG, and
    return JSON.
    """
    try:
        logger.info("Text query: %s", payload.text[:60])

        llm_result = await run_in_threadpool(
            process_voice_with_llm,
            payload.text,
            payload.context,
            payload.language,
        )

        return HealthQueryResponse(
            response=llm_result["response_text"],
            status="success",
            language=llm_result["language_code"],
            rag_context_used=True,
        )

    except Exception as exc:
        logger.error("Error in /text-query: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))