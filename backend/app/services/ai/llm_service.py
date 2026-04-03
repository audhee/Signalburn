import google.generativeai as genai
from app.core.config import settings
from app.services.ai.rag_service import rag_service
import logging

logger = logging.getLogger(__name__)

def process_voice_with_llm(text: str, context: str = "", language: str = "en") -> str:
    """
    Processes user query using Gemini with RAG context injected.
    text     → transcribed user query (from Whisper)
    context  → optional extra context passed from frontend
    language → detected language code for response language
    """
    if not settings.GEMINI_API_KEY:
        return "GEMINI_API_KEY is not configured on the server."

    # Retrieve relevant health knowledge from ChromaDB
    rag_context = rag_service.retrieve_context(text, k=3)

    # Build the system prompt
    system_prompt = f"""You are Arohan, a helpful AI health assistant for elderly patients in India.
You have access to a health knowledge base. Use it to give accurate, caring, and concise answers.
Always respond in the same language the user spoke in.
If the situation seems like a medical emergency, always tell the user to call 112 immediately.
Keep your response short and clear — the user will hear this as voice output.

Health Knowledge Base (use this to answer):
{rag_context}

Additional context from device: {context if context else 'None'}
"""

    user_message = f"User asked: {text}"

    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(f"{system_prompt}\n\n{user_message}")
        logger.info(f"Gemini response generated for query: '{text[:50]}'")
        return response.text

    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise