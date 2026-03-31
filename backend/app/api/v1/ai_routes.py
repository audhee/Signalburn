from fastapi import APIRouter, HTTPException
from app.models.ai_models import VoicePromptPayload
from app.services.ai.llm_service import process_voice_with_llm
from app.core.config import settings

router = APIRouter()

@router.post("/process")
def process_voice_prompt(payload: VoicePromptPayload):
    try:
        response_text = process_voice_with_llm(payload.text, payload.context)
        
        status_type = "success" if settings.GEMINI_API_KEY else "warning"
        
        return {
            "response": response_text,
            "status": status_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with AI model: {str(e)}")
