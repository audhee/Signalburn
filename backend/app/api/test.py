"""
Test API endpoint for dual mode verification
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.ai.llm_service import process_voice_with_llm
from app.services.ai.rag_service import rag_service

router = APIRouter()

class TestRequest(BaseModel):
    text: str
    language: str = "en"
    rag_source: str = "all"

class TestResponse(BaseModel):
    response: str
    language: str
    model_used: str
    mode: str

@router.post("/test", response_model=TestResponse)
async def test_llm(request: TestRequest):
    """
    Test endpoint to verify both Groq and Ollama models work correctly.
    """
    try:
        # Call the LLM service
        result = process_voice_with_llm(
            text=request.text,
            language=request.language,
            rag_source=request.rag_source
        )
        
        # Determine which model was used
        from app.services.ai.ollama_service import USE_LOCAL_MODEL
        model_used = "arohan-medical (Ollama)" if USE_LOCAL_MODEL else "llama-3.3-70b-versatile (Groq)"
        mode = "LOCAL" if USE_LOCAL_MODEL else "CLOUD"
        
        return TestResponse(
            response=result["response_text"],
            language=result["language_code"],
            model_used=model_used,
            mode=mode
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Health check endpoint for model availability
    """
    try:
        from app.services.ai.ollama_service import USE_LOCAL_MODEL, OLLAMA_URL
        
        if USE_LOCAL_MODEL:
            # Check if Ollama is available
            import requests
            try:
                response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
                models = response.json().get("models", [])
                ollama_available = len(models) > 0
                return {
                    "status": "healthy",
                    "model_mode": "LOCAL",
                    "ollama_available": ollama_available,
                    "ollama_url": OLLAMA_URL,
                    "models_available": models
                }
            except:
                return {
                    "status": "unhealthy",
                    "model_mode": "LOCAL",
                    "error": "Ollama not available"
                }
        else:
            # Check if Groq API key is set (lazy init)
            from app.services.ai.llm_service import _get_groq_client
            groq_available = _get_groq_client() is not None
            return {
                "status": "healthy" if groq_available else "unhealthy",
                "model_mode": "CLOUD",
                "groq_available": groq_available
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }