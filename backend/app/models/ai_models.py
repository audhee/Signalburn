from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

# ==================== EXISTING MODELS (UNCHANGED) ====================

class VoicePromptPayload(BaseModel):
    text: str
    context: str = ""
    language: str = "en"

class VoiceAudioPayload(BaseModel):
    audio_path: str
    language_code: str = "hi-IN"

class HealthQueryResponse(BaseModel):
    response: str
    transcription: str = ""
    status: str
    language: str
    language_code: str = "en-IN"
    rag_context_used: bool


# ==================== NEW MULTIMODAL MODELS ====================

class MediaType(str, Enum):
    image = "image"
    video = "video"
    document = "document"

class MultimodalUploadResponse(BaseModel):
    response: str
    transcription: str = ""
    language: str
    language_code: str = "en-IN"
    severity: str = "unknown"
    media_type: str = "image"
    media_filename: str = ""
    rag_context_used: bool = True
    audio_url: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    timestamp: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatMessage]