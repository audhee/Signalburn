"""
vision_service.py - Image/Video Analysis for Wound/Injury Detection
Uses Gemini 1.5 Flash (multimodal) for image/video understanding
"""

import os
import logging
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)


def analyze_image(image_path: str, user_query: str = "") -> dict:
    """
    Analyzes an image of wound/injury using Gemini Vision.

    Args:
        image_path: Path to uploaded image file
        user_query: Optional text description from user

    Returns:
        dict with:
            - description: What AI sees
            - wound_type: Classified wound type
            - severity: minor/moderate/major
            - confidence: 0-1 confidence score
    """
    try:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")

        model = genai.GenerativeModel('gemini-1.5-flash')

        # Read image bytes
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # Determine MIME type
        ext = image_path.split(".")[-1].lower()
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        # Build analysis prompt
        prompt = """You are a medical image analysis assistant. Analyze this image of a wound or injury.

Describe what you see in detail:
1. What type of wound is this? (cut, burn, bruise, abrasion, puncture, etc.)
2. How severe does it appear? (minor, moderate, major)
3. Is there bleeding? How much?
4. Where on the body is this located?
5. Any signs of infection? (redness, swelling, pus)

Respond in this exact format:
WOUND_TYPE: [type]
SEVERITY: [minor/moderate/major]
BLEEDING: [none/light/moderate/heavy]
LOCATION: [body part]
INFECTION_SIGNS: [yes/no, describe if yes]
DESCRIPTION: [detailed description of what you see]"""

        # Call Gemini Vision
        response = model.generate_content([
            prompt,
            genai.Part.from_data(data=image_bytes, mime_type=mime_type)
        ])

        # Parse response
        result = parse_vision_response(response.text)
        logger.info(f"🔍 Image analyzed: {result['wound_type']} | Severity: {result['severity']}")
        
        return result

    except Exception as e:
        logger.error(f"❌ Image analysis failed: {e}")
        raise


def analyze_video(video_path: str, user_query: str = "") -> dict:
    """
    Analyzes a video of wound/injury using Gemini Vision.
    Extracts key frames and analyzes them.
    """
    try:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")

        model = genai.GenerativeModel('gemini-1.5-flash')

        # Read video bytes
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        # Determine MIME type
        ext = video_path.split(".")[-1].lower()
        mime_map = {
            "mp4": "video/mp4",
            "mov": "video/quicktime",
            "avi": "video/x-msvideo",
            "webm": "video/webm",
        }
        mime_type = mime_map.get(ext, "video/mp4")

        prompt = """You are a medical video analysis assistant. Analyze this video of a wound or injury.

Describe what you see:
1. What type of wound/injury is shown?
2. How severe does it appear? (minor, moderate, major)
3. Is there bleeding? How much?
4. Where on the body is this located?
5. Any signs of infection or complications?

Respond in this exact format:
WOUND_TYPE: [type]
SEVERITY: [minor/moderate/major]
BLEEDING: [none/light/moderate/heavy]
LOCATION: [body part]
INFECTION_SIGNS: [yes/no, describe if yes]
DESCRIPTION: [detailed description]"""

        response = model.generate_content([
            prompt,
            genai.Part.from_data(data=video_bytes, mime_type=mime_type)
        ])

        result = parse_vision_response(response.text)
        logger.info(f"🎥 Video analyzed: {result['wound_type']} | Severity: {result['severity']}")
        
        return result

    except Exception as e:
        logger.error(f"❌ Video analysis failed: {e}")
        raise


def parse_vision_response(response_text: str) -> dict:
    """
    Parses Gemini Vision response into structured dict.
    """
    result = {
        "description": "",
        "wound_type": "unknown",
        "severity": "unknown",
        "confidence": 0.7
    }

    lines = response_text.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        if line.startswith("WOUND_TYPE:"):
            result["wound_type"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("SEVERITY:"):
            result["severity"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("DESCRIPTION:"):
            result["description"] = line.split(":", 1)[1].strip()
        elif line.startswith("BLEEDING:"):
            result["bleeding"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("LOCATION:"):
            result["location"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("INFECTION_SIGNS:"):
            result["infection_signs"] = line.split(":", 1)[1].strip()

    # If no description found, use full text
    if not result["description"]:
        result["description"] = response_text

    # Determine confidence based on clarity
    if result["wound_type"] != "unknown" and result["severity"] != "unknown":
        result["confidence"] = 0.85
    else:
        result["confidence"] = 0.5

    return result