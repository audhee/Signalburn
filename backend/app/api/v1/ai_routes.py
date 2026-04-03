from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from app.models.ai_models import VoicePromptPayload, HealthQueryResponse
from app.services.ai.llm_service import process_voice_with_llm
from app.services.ai.voice_service import transcribe_audio, text_to_indian_voice
from app.core.config import settings
import tempfile, os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/process", response_model=HealthQueryResponse)
def process_voice_prompt(payload: VoicePromptPayload):
    """
    Takes transcribed text + optional context,
    runs RAG retrieval + Gemini generation,
    returns text response.
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
        logger.error(f"Error in /process: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-query")
async def full_voice_pipeline(
    audio: UploadFile = File(...),
    language_code: str = "hi-IN"
):
    """
    Full pipeline endpoint:
    Audio file → Whisper → RAG + Gemini → Sarvam TTS → Audio response
    """
    try:
        # Save uploaded audio to temp file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{audio.filename.split('.')[-1]}"
        ) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name

        # Step 1: Whisper transcription
        transcribed_text = transcribe_audio(tmp_path)
        os.unlink(tmp_path)  # clean up temp file

        # Step 2: RAG + Gemini
        answer_text = process_voice_with_llm(
            transcribed_text,
            language=language_code
        )

        # Step 3: Sarvam TTS
        audio_bytes = text_to_indian_voice(answer_text, language_code)

        # Return audio directly
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