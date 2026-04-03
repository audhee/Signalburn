from pydantic import BaseModel
from typing import Optional

class VoicePromptPayload(BaseModel):
    text: str
    context: str = ""
    language: str = "en"          # detected language code

class VoiceAudioPayload(BaseModel):
    """Used when frontend sends audio file path or base64"""
    audio_path: str
    language_code: str = "hi-IN"  # for Sarvam TTS response

class HealthQueryResponse(BaseModel):
    response: str
    status: str
    language: str
    rag_context_used: bool