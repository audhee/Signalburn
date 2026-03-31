from pydantic import BaseModel

class VoicePromptPayload(BaseModel):
    text: str
    context: str = ""
