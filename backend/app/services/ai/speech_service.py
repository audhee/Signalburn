import google.generativeai as genai
import os
import tempfile
from typing import BinaryIO
from app.core.config import settings

def transcribe_audio(audio_file: BinaryIO, filename: str) -> str:
    """Takes a raw audio stream, uploads to Gemini, and returns transcript.
    Raises ValueError if GEMINI_API_KEY is missing or transcription fails.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured on the server")
        
    try:
        # Gemini 1.5 allows inline binary audio injection directly into the prompt up to 20MB
        audio_bytes = audio_file.read()
        
        # Initialize Gemini Flash (1.5) which has a standard free tier quota
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        
        prompt = "Listen to this audio. Give me the transcription EXACTLY as it is spoken, in the original Indian language or English. Output ONLY the words spoken in plain text, do not add translation or formatting."
        
        response = model.generate_content([
            prompt, 
            {"mime_type": "audio/mp4", "data": audio_bytes}
        ])
        
        transcript = response.text.strip()
        return transcript
    except Exception as e:
        print(f"Error in Gemini transcription: {e}")
        raise ValueError(f"Gemini transcription failed: {e}")
