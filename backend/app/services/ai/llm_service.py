import google.generativeai as genai
from app.core.config import settings

def process_voice_with_llm(text: str, context: str = "") -> str:
    """Processes voice transcript using Gemini."""
    if not settings.GEMINI_API_KEY:
        return "Received your voice prompt, but the GEMINI_API_KEY is not configured on the server. Please add it to your .env file."
        
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Build prompt
    full_prompt = text
    if context:
        full_prompt = f"Context: {context}\nUser Voice Input: {text}\nRespond as a helpful, concise AI emergency voice agent."
        
    response = model.generate_content(full_prompt)
    return response.text
