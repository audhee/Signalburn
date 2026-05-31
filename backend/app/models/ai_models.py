from pydantic import BaseModel
from typing import Optional

class VoicePromptPayload(BaseModel):
    text: str
    context: str = ""
    language: str = "en"

class VoiceAudioPayload(BaseModel):
    audio_path: str
    language_code: str = "hi-IN"

class HealthQueryResponse(BaseModel):
    response: str
    transcription: str = ""      # what Groq Whisper heard from voice
    status: str
    language: str
    language_code: str = "en-IN" # detected language code
    rag_context_used: bool