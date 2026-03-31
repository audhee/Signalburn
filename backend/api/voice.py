from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Configure the SDK. Ensure you have GEMINI_API_KEY in your .env file
API_KEY = os.getenv("GEMINI_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)

class VoicePromptPayload(BaseModel):
    text: str
    context: str = ""

@router.post("/process")
def process_voice_prompt(payload: VoicePromptPayload):
    if not API_KEY:
        # Fallback response if API key is not configured for easy testing
        return {
            "response": "Received your voice prompt, but the GEMINI_API_KEY is not configured on the server. Please add it to your .env file.",
            "status": "warning"
        }
        
    try:
        # Using Gemini-1.5-pro or gemini-pro depending on what is available
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Build prompt
        full_prompt = payload.text
        if payload.context:
            full_prompt = f"Context: {payload.context}\nUser Voice Input: {payload.text}\nRespond as a helpful, concise AI emergency voice agent."
            
        response = model.generate_content(full_prompt)
        
        return {
            "response": response.text,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with AI model: {str(e)}")
