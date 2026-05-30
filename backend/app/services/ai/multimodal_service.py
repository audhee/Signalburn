"""
multimodal_service.py - Image/Video analysis for Arohan
Images: Groq Vision API (llama-4-scout)
Videos: Frame extraction via OpenCV → Groq Vision analysis
Documents: Text-based fallback via Groq LLM
"""

from groq import Groq
from app.core.config import settings
from app.services.ai.rag_service import rag_service
from app.services.ai.language_service import detect_language
import logging
import base64
import os
import tempfile

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
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/rtf", "text/rtf"
}

ALL_SUPPORTED_TYPES = IMAGE_TYPES | VIDEO_TYPES | DOCUMENT_TYPES

# Groq model for vision tasks
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_VISION_FALLBACK = "meta-llama/llama-4-scout-17b-16e-instruct"

# Maximum image size in bytes (Groq limit is 4MB for base64 images)
MAX_IMAGE_SIZE_BYTES = 4 * 1024 * 1024

# Maximum frames to extract from video
MAX_VIDEO_FRAMES = 3

# Maximum video file size (50MB)
MAX_VIDEO_SIZE_BYTES = 50 * 1024 * 1024


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


def is_image_file(filename: str) -> bool:
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    return ext in {"jpg", "jpeg", "png", "webp", "heic", "heif", "gif", "bmp"}


# ==================== PROMPT BUILDER ====================

def build_multimodal_prompt(
    user_text: str,
    media_type: str,
    rag_context: str,
    language_name: str
) -> str:
    """Builds the system prompt for multimodal analysis."""

    return f"""You are Arohan, a helpful AI health assistant for elderly patients in India.

CRITICAL: You MUST analyze the image below. DO NOT say you cannot see it. You CAN see it. Describe exactly what you see.

Image shows a wound, injury, rash, or medical concern.

ANALYSIS INSTRUCTIONS:
1. Describe the injury, wound, or skin condition you see in the image.
2. Assess severity in one word: minor / moderate / severe / emergency.
3. Provide simple numbered first aid steps.
4. Mention if it looks infected (redness, swelling, pus, etc.).
5. If it looks like a medical emergency (severe bleeding, deep wound, burns, fractures, unconsciousness), say: "Please call 112 immediately."
6. Be calm, caring, and clear. The response will be spoken aloud as voice.
7. Do NOT use any symbols, asterisks, hashes, or markdown formatting. Use plain text only.

LANGUAGE RULE — VERY IMPORTANT:
The user spoke/wrote in {language_name}. You MUST reply in EXACTLY that language.
- If they used Kannada-English mix, reply in Kannada-English mix.
- If they used Hindi, reply in Hindi only.
- If they used pure English, reply in English only.
- Never switch to a different language.

First Aid and Health Knowledge Base:
{rag_context}

User's message: {user_text if user_text else 'No additional text provided.'}"""


# ==================== SEVERITY EXTRACTOR ====================

def extract_severity(response_text: str) -> str:
    """Extracts severity level from response text."""
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


# ==================== GROQ VISION HELPER ====================

def _call_groq_vision(
    system_prompt: str,
    image_base64: str,
    mime_type: str,
    model_name: str = GROQ_VISION_MODEL
) -> str:
    """Call Groq vision API with a base64-encoded image."""
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured")

    client = Groq(api_key=settings.GROQ_API_KEY)

    data_url = f"data:{mime_type};base64,{image_base64}"

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url,
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        max_tokens=1024,
        temperature=0.3
    )

    return response.choices[0].message.content


# ==================== VIDEO FRAME EXTRACTOR ====================

def _extract_video_frames(video_bytes: bytes, filename: str, max_frames: int = MAX_VIDEO_FRAMES) -> list[dict]:
    """
    Extract key frames from a video using OpenCV.
    Returns list of dicts: [{'bytes': ..., 'mime_type': 'image/jpeg'}, ...]
    Returns empty list if extraction fails.
    """
    tmp_path = None
    try:
        # Save video bytes to temp file
        suffix = os.path.splitext(filename)[1] if "." in filename else ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        import cv2
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            logger.error(f"[Video] Could not open video: {filename}")
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        logger.info(f"[Video] {filename}: {total_frames} frames, {fps:.1f} fps, {duration:.1f}s")

        if total_frames <= 0:
            cap.release()
            return []

        # Pick frames: first frame, middle frame, last frame
        frame_positions = [0]
        if total_frames > 1:
            frame_positions.append(total_frames // 2)
        if total_frames > 2:
            frame_positions.append(total_frames - 1)

        # Limit to max_frames
        frame_positions = frame_positions[:max_frames]

        frames = []
        for pos in frame_positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            if ret:
                # Encode frame as JPEG bytes
                success, jpeg_bytes = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if success:
                    frames.append({
                        'bytes': jpeg_bytes.tobytes(),
                        'mime_type': 'image/jpeg',
                        'frame_num': pos
                    })
                    logger.info(f"[Video] Extracted frame {pos}/{total_frames} ({len(jpeg_bytes)} bytes)")

        cap.release()
        logger.info(f"[Video] Extracted {len(frames)} frames from '{filename}'")
        return frames

    except ImportError:
        logger.error("[Video] OpenCV (cv2) is not installed. Cannot extract video frames.")
        return []
    except Exception as e:
        logger.error(f"[Video] Frame extraction failed: {e}")
        return []
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass


# ==================== IMAGE ANALYZER ====================

def _analyze_image(system_prompt: str, file_bytes: bytes, mime_type: str, filename: str) -> dict:
    """Analyze a single image via Groq vision."""
    # Validate file size
    if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
        return {
            "response_text": f"Image too large ({len(file_bytes)/(1024*1024):.1f}MB). Please upload a smaller image (under 4MB).",
            "language_code": "en-IN",
            "severity": "unknown"
        }

    try:
        image_base64 = base64.b64encode(file_bytes).decode("utf-8")
        logger.info(f"[Multimodal] Calling Groq Vision ({GROQ_VISION_MODEL}) for '{filename}'...")
        try:
            response_text = _call_groq_vision(system_prompt, image_base64, mime_type, GROQ_VISION_MODEL)
        except Exception as primary_err:
            logger.warning(f"[Multimodal] Primary model failed: {primary_err}, trying fallback...")
            response_text = _call_groq_vision(system_prompt, image_base64, mime_type, GROQ_VISION_FALLBACK)
        logger.info(f"[Multimodal] Groq response for '{filename}': {response_text[:100]}...")
        severity = extract_severity(response_text)

        return {
            "response_text": response_text,
            "language_code": None,  # filled in by caller
            "severity": severity
        }

    except Exception as e:
        logger.error(f"[Multimodal] Groq Vision API call failed: {e}")
        return {
            "response_text": f"Sorry, I could not analyze the image at this moment. Please try again or describe the issue in text.",
            "language_code": None,
            "severity": "unknown"
        }


# ==================== VIDEO ANALYZER ====================

def _build_video_prompt(
    user_text: str,
    rag_context: str,
    language_name: str,
    frame_count: int
) -> str:
    """Build a specialised prompt for video analysis."""
    prompt = f"""You are Arohan, a helpful AI health assistant for elderly patients in India.

CRITICAL: You MUST analyze the video frames below. DO NOT say you cannot see them. You CAN see the frames. Describe exactly what you see in each frame.

Video shows a wound, injury, or medical concern.

ANALYSIS INSTRUCTIONS:
1. Describe the injury, wound, or skin condition you see in the video frames.
2. Assess severity in one word: minor / moderate / severe / emergency.
3. Provide simple numbered first aid steps.
4. Mention if it looks infected (redness, swelling, pus, etc.).
5. If it looks like a medical emergency (severe bleeding, deep wound, burns, fractures), say: "Please call 112 immediately."
6. Be calm, caring, and clear. The response will be spoken aloud as voice.
7. Do NOT use any symbols, asterisks, hashes, or markdown formatting. Use plain text only.

LANGUAGE RULE — VERY IMPORTANT:
The user spoke/wrote in {language_name}. You MUST reply in EXACTLY that language.
- If they used Kannada-English mix, reply in Kannada-English mix.
- If they used Hindi, reply in Hindi only.
- If they used pure English, reply in English only.
- Never switch to a different language.

First Aid and Health Knowledge Base:
{rag_context}

User's message: {user_text if user_text else 'No additional text provided.'}"""
    return prompt


def _analyze_video(
    system_prompt: str,
    frames: list[dict],
    language_code: str,
    user_text: str,
    rag_context: str,
    language_name: str
) -> dict:
    """Analyze video frames via Groq vision. Sends frames as separate images."""
    if not frames:
        logger.warning("[Video] No frames to analyze")
        return {
            "response_text": "Could not extract frames from the video. Please upload an image instead.",
            "language_code": language_code,
            "severity": "unknown"
        }

    try:
        # Build content array with text + all frame images
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured")

        client = Groq(api_key=settings.GROQ_API_KEY)

        # Build content parts: text first, then each frame as image_url
        content_parts = [{"type": "text", "text": system_prompt}]

        for i, frame in enumerate(frames):
            img_b64 = base64.b64encode(frame['bytes']).decode("utf-8")
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{frame['mime_type']};base64,{img_b64}",
                    "detail": "high"
                }
            })

        try:
            response = client.chat.completions.create(
                model=GROQ_VISION_MODEL,
                messages=[{"role": "user", "content": content_parts}],
                max_tokens=1024,
                temperature=0.3
            )
        except Exception as primary_err:
            logger.warning(f"[Video] Primary model failed: {primary_err}, trying fallback...")
            response = client.chat.completions.create(
                model=GROQ_VISION_FALLBACK,
                messages=[{"role": "user", "content": content_parts}],
                max_tokens=1024,
                temperature=0.3
            )

        response_text = response.choices[0].message.content
        logger.info(f"[Video] Groq analysis complete: {response_text[:100]}...")
        severity = extract_severity(response_text)

        return {
            "response_text": response_text,
            "language_code": language_code,
            "severity": severity
        }

    except Exception as e:
        logger.error(f"[Video] Groq analysis failed: {e}")
        return {
            "response_text": f"Sorry, I could not analyze the video at this moment. Please try again or upload an image instead.",
            "language_code": language_code,
            "severity": "unknown"
        }


# ==================== TEXT-ONLY ANALYZER (for documents) ====================

def _analyze_document(
    system_prompt: str,
    mime_type: str,
    filename: str,
    user_text: str,
    language_code: str
) -> dict:
    """Analyze document-type uploads using text-only Groq."""
    if not settings.GROQ_API_KEY:
        return {
            "response_text": "GROQ_API_KEY is not configured on the server.",
            "language_code": language_code,
            "severity": "unknown"
        }

    client = Groq(api_key=settings.GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"The user uploaded a {mime_type} file named '{filename}'. "
                                            f"Since I cannot view it directly, please provide general first-aid guidance "
                                            f"based on the user's description: {user_text if user_text else 'No description provided.'}"}
            ],
            max_tokens=1024,
            temperature=0.3
        )

        response_text = response.choices[0].message.content
        severity = extract_severity(response_text)

        return {
            "response_text": response_text,
            "language_code": language_code,
            "severity": severity
        }

    except Exception as e:
        logger.error(f"[Multimodal] Groq text-only call failed: {e}")
        return {
            "response_text": f"Sorry, I could not process the {mime_type} at this moment. Please try again or describe the issue in text.",
            "language_code": language_code,
            "severity": "unknown"
        }


# ==================== MAIN MULTIMODAL PROCESSOR ====================

def process_multimodal_query(
    text: str,
    file_bytes: bytes,
    mime_type: str,
    filename: str,
    context: str = ""
) -> dict:
    """
    Processes user query with uploaded media using Groq.
    - Images: Direct Groq Vision analysis
    - Videos: Frame extraction + Groq Vision analysis
    - Documents: Text-only LLM fallback
    Returns dict with response_text, language_code, and severity.
    """
    if not settings.GROQ_API_KEY:
        logger.error("GROQ_API_KEY is not configured")
        return {
            "response_text": "GROQ_API_KEY is not configured on the server.",
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

    if mime_type.startswith("image/"):
        # ── IMAGE ANALYSIS ──────────────────────────────────
        system_prompt = build_multimodal_prompt(text, mime_type, rag_context, language_name)
        result = _analyze_image(system_prompt, file_bytes, mime_type, filename)
        result["language_code"] = language_code
        return result

    elif mime_type.startswith("video/"):
        # ── VIDEO ANALYSIS ──────────────────────────────────
        # Validate file size
        if len(file_bytes) > MAX_VIDEO_SIZE_BYTES:
            return {
                "response_text": f"Video too large ({len(file_bytes)/(1024*1024):.1f}MB). Please upload a smaller video (under 50MB).",
                "language_code": language_code,
                "severity": "unknown"
            }

        # Extract frames from video
        frames = _extract_video_frames(file_bytes, filename)

        if not frames:
            return {
                "response_text": "Could not extract frames from the video. Please upload an image of the injury instead.",
                "language_code": language_code,
                "severity": "unknown"
            }

        # Build video-specific prompt
        video_prompt = _build_video_prompt(text, rag_context, language_name, len(frames))

        # Analyze frames via Groq vision
        return _analyze_video(video_prompt, frames, language_code, text, rag_context, language_name)

    else:
        # ── DOCUMENT / TEXT ANALYSIS ────────────────────────
        logger.info(f"[Multimodal] Non-media upload ({mime_type}), using text-only analysis.")
        system_prompt = build_multimodal_prompt(text, mime_type, rag_context, language_name)
        return _analyze_document(system_prompt, mime_type, filename, text, language_code)
