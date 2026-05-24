import google.generativeai as genai
from app.core.config import settings
from app.services.ai.rag_service import rag_service
from app.services.ai.language_service import detect_language
import logging
import base64
import os

logger = logging.getLogger(__name__)

# ==================== SUPPORTED MIME TYPES ====================

IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"
}
VIDEO_TYPES = {
    "video/mp4", "video/mpeg", "video/mov", "video/avi", "video/x-flv",
    "video/mpg", "video/webm", "video/wmv", "video/3gpp"
}
DOCUMENT_TYPES = {
    "application/pdf", "text/plain", "text/csv", "application/json",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",   # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",         # .xlsx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "application/rtf", "text/rtf"
}

# Combined for quick lookup
ALL_SUPPORTED_TYPES = IMAGE_TYPES | VIDEO_TYPES | DOCUMENT_TYPES


# ==================== MIME TYPE HELPERS ====================

def get_mime_type(filename: str) -> str:
    """Guess MIME type from filename extension."""
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    mapping = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "webp": "image/webp", "heic": "image/heic", "heif": "image/heif",
        "mp4": "video/mp4", "mpeg": "video/mpeg", "mov": "video/mov",
        "avi": "video/avi", "flv": "video/x-flv", "mpg": "video/mpg",
        "webm": "video/webm", "wmv": "video/wmv", "3gp": "video/3gpp",
        "pdf": "application/pdf", "txt": "text/plain", "csv": "text/csv",
        "json": "application/json",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "rtf": "application/rtf",
    }
    return mapping.get(ext, "application/octet-stream")


def is_image(mime: str) -> bool:
    return mime in IMAGE_TYPES


def is_video(mime: str) -> bool:
    return mime in VIDEO_TYPES


def is_document(mime: str) -> bool:
    return mime in DOCUMENT_TYPES


def is_supported_media(mime: str) -> bool:
    return mime in ALL_SUPPORTED_TYPES


# ==================== PROMPT BUILDER ====================

def build_multimodal_prompt(
    user_text: str,
    media_type: str,
    rag_context: str,
    language_name: str
) -> str:
    """Builds the system prompt for Gemini multimodal analysis."""
    
    return f"""You are Arohan, a helpful AI health assistant for elderly patients in India.
You are analyzing a {media_type} that the user has uploaded — likely showing a wound, injury, rash, or medical concern.

LANGUAGE RULE — VERY IMPORTANT:
The user spoke/wrote in {language_name}. You MUST reply in EXACTLY that language.
- If they used Kannada-English mix, reply in Kannada-English mix.
- If they used Hindi, reply in Hindi only.
- If they used pure English, reply in English only.
- Never switch to a different language.

ANALYSIS INSTRUCTIONS:
1. Look carefully at the uploaded {media_type}.
2. Describe what you see clearly.
3. If it appears to be a wound, injury, rash, or skin condition:
   - Assess severity (minor / moderate / severe / emergency).
   - Provide numbered first aid steps.
   - Mention if it looks infected (redness, swelling, pus, etc.).
4. If it looks like a medical emergency (severe bleeding, deep wound, burns, fractures, unconsciousness), say: "Please call 112 immediately."
5. Be calm, caring, and clear. The response will be spoken aloud as voice.

First Aid and Health Knowledge Base:
{rag_context}

User's message: {user_text if user_text else 'No additional text provided.'}"""


# ==================== SEVERITY EXTRACTOR ====================

def extract_severity(response_text: str) -> str:
    """Extracts severity level from Gemini response text."""
    lower_text = response_text.lower()
    
    emergency_keywords = ["emergency", "call 112", "severe", "critical", "immediate", "urgent", "life-threatening"]
    moderate_keywords = ["moderate", "see a doctor", "consult", "clinic", "hospital", "medical attention"]
    minor_keywords = ["minor", "small", "mild", "home care", "first aid", "self-care", "home treatment"]
    
    if any(word in lower_text for word in emergency_keywords):
        return "emergency"
    elif any(word in lower_text for word in moderate_keywords):
        return "moderate"
    elif any(word in lower_text for word in minor_keywords):
        return "minor"
    
    return "unknown"


# ==================== MAIN MULTIMODAL PROCESSOR ====================

def process_multimodal_query(
    text: str,
    file_bytes: bytes,
    mime_type: str,
    filename: str,
    context: str = ""
) -> dict:
    """
    Processes user query with uploaded media using Gemini multimodal.
    Returns dict with response_text, language_code, and severity.
    
    Uses google.generativeai (old SDK) with proper Part objects.
    """
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not configured")
        return {
            "response_text": "GEMINI_API_KEY is not configured on the server.",
            "language_code": "en-IN",
            "severity": "unknown"
        }

    # Validate file size (Gemini inline limit is ~20MB total per request)
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > 20:
        logger.warning(f"File too large: {file_size_mb:.1f}MB. Gemini inline limit is ~20MB.")
        return {
            "response_text": f"File too large ({file_size_mb:.1f}MB). Please upload a smaller file (under 20MB).",
            "language_code": "en-IN",
            "severity": "unknown"
        }

    # Detect language from user's text
    lang_info = detect_language(text)
    language_code = lang_info["language_code"]
    language_name = lang_info["language_name"]
    logger.info(f"[Multimodal] Detected language: {language_name} → {language_code}")

    # Get RAG context
    rag_context = rag_service.retrieve_context(text, k=3)
    
    # Build the prompt
    system_prompt = build_multimodal_prompt(text, mime_type, rag_context, language_name)

    try:
        model = genai.GenerativeModel('gemini-1.5-pro')

        # Create the image/video part using proper genai Part object
        # For the old google.generativeai SDK, we use genai.Part.from_data()
        media_part = genai.Part.from_data(
            data=file_bytes,
            mime_type=mime_type
        )

        # Create content with text prompt + media
        contents = [
            system_prompt,           # text prompt first
            media_part               # media part second
        ]

        # Generate content
        response = model.generate_content(contents)
        response_text = response.text

        logger.info(f"[Multimodal] Gemini response for '{filename}': {response_text[:100]}...")

        # Extract severity
        severity = extract_severity(response_text)

        return {
            "response_text": response_text,
            "language_code": language_code,
            "severity": severity
        }

    except Exception as e:
        logger.error(f"[Multimodal] Gemini API call failed: {e}")
        # Return a graceful fallback instead of crashing
        return {
            "response_text": f"Sorry, I could not analyze the {mime_type} at this moment. Please try again or describe the issue in text.",
            "language_code": language_code,
            "severity": "unknown"
        }
