import uuid
from fastapi import APIRouter, HTTPException
from twilio.base.exceptions import TwilioRestException
from app.models.auth_models import RequestOTPPayload, VerifyOTPPayload
from app.services.auth.auth_service import generate_otp, verify_otp

router = APIRouter()


@router.post("/request-otp")
def request_otp(payload: RequestOTPPayload):
    if not payload.phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")

    try:
        generate_otp(payload.phone_number)
        return {"message": "OTP sent successfully via SMS"}
    except ValueError as e:
        # Twilio credentials not configured
        raise HTTPException(status_code=500, detail=str(e))
    except TwilioRestException as e:
        # Twilio API-level error (invalid number, trial limits, etc.)
        raise HTTPException(status_code=502, detail=f"SMS delivery failed: {e.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error sending OTP: {str(e)}")


@router.post("/verify-otp")
def verify_otp_endpoint(payload: VerifyOTPPayload):
    if not payload.phone_number or not payload.user_otp:
        raise HTTPException(status_code=400, detail="Phone number and OTP are required")

    is_valid = verify_otp(payload.phone_number, payload.user_otp)

    if is_valid:
        # Generate a unique session token for this user
        # TODO: Replace with a signed JWT token in production
        session_token = str(uuid.uuid4())
        return {
            "message": "Authentication successful",
            "token": session_token,
            "phone_number": payload.phone_number,
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP. Please try again.")
