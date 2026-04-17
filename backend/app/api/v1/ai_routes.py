from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from app.models.ai_models import VoicePromptPayload, HealthQueryResponse
from app.services.ai.llm_service import process_voice_with_llm
from app.services.ai.voice_service import transcribe_audio, text_to_indian_voice
from app.core.config import settings
import tempfile, os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/process")
async def process_voice_audio(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
    language_code: str = Form(default="hi-IN"),
):
    """
    Full voice pipeline endpoint (called by the React Native app):
    Multipart audio file → Whisper STT → RAG + Gemini → Sarvam TTS → Audio response
    """
    try:
        # Step 1: Save uploaded audio to a temp file
        suffix = ".m4a"
        if audio.filename:
            ext = audio.filename.split(".")[-1]
            suffix = f".{ext}" if ext else ".m4a"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        logger.info(f"[{session_id}] Audio saved to {tmp_path} ({len(content)} bytes)")

        # Step 2: Transcribe audio → text
        transcribed_text = transcribe_audio(tmp_path)
        os.unlink(tmp_path)  # clean up temp file immediately
        logger.info(f"[{session_id}] Transcribed: {transcribed_text}")

        # Step 3: RAG + Gemini → answer text
        answer_text = process_voice_with_llm(
            transcribed_text,
            language=language_code
        )
        logger.info(f"[{session_id}] LLM answer: {answer_text[:80]}...")

        # Step 4: Sarvam TTS → audio bytes
        audio_bytes = text_to_indian_voice(answer_text, language_code)
        logger.info(f"[{session_id}] TTS audio: {len(audio_bytes)} bytes")

        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "X-Transcription": transcribed_text[:200],   # truncate for header safety
                "X-Answer-Text": answer_text[:200],
                "X-Session-Id": session_id,
            }
        )

    except Exception as e:
        logger.error(f"[{session_id}] Voice pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-query")
async def full_voice_pipeline(
    audio: UploadFile = File(...),
    language_code: str = "hi-IN"
):
    """
    Legacy full pipeline endpoint (kept for compatibility).
    """
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{audio.filename.split('.')[-1]}"
        ) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name

        transcribed_text = transcribe_audio(tmp_path)
        os.unlink(tmp_path)

        answer_text = process_voice_with_llm(
            transcribed_text,
            language=language_code
        )

        audio_bytes = text_to_indian_voice(answer_text, language_code)

        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "X-Transcription": transcribed_text,
                "X-Answer-Text": answer_text
            }
        )

    except Exception as e:
        logger.error(f"Error in /voice-query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text-query", response_model=HealthQueryResponse)
def process_text_prompt(payload: VoicePromptPayload):
    """
    Text-only endpoint for when you already have transcribed text.
    """
    try:
        response_text = process_voice_with_llm(
            payload.text,
            payload.context,
            payload.language
        )
        return HealthQueryResponse(
            response=response_text,
            status="success" if settings.GEMINI_API_KEY else "warning",
            language=payload.language,
            rag_context_used=True
        )
    except Exception as e:
        logger.error(f"Error in /text-query: {e}")
        raise HTTPException(status_code=500, detail=str(e))