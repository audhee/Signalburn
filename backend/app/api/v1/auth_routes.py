import uuid
from fastapi import APIRouter, HTTPException
from app.utils.security import create_access_token
from twilio.base.exceptions import TwilioRestException
from app.models.auth_models import RequestOTPPayload, VerifyOTPPayload
from app.services.auth.auth_service import generate_otp, verify_otp, DatabaseUnavailableError, RateLimitExceededError, _standardize_phone
from app.db.dependencies import get_db
from app.services.user.user_service import UserService
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter()


@router.post("/request-otp")
def request_otp(payload: RequestOTPPayload):
    if not payload.phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")

    try:
        generate_otp(payload.phone_number)
        return {"message": "OTP sent successfully via SMS"}
    except RateLimitExceededError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except DatabaseUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except TwilioRestException as e:
        raise HTTPException(status_code=502, detail=f"SMS delivery failed: {e.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error sending OTP: {str(e)}")


@router.post("/verify-otp")
def verify_otp_endpoint(payload: VerifyOTPPayload, db: Session = Depends(get_db)):
    if not payload.phone_number or not payload.user_otp:
        raise HTTPException(status_code=400, detail="Phone number and OTP are required")

    try:
        is_valid = verify_otp(payload.phone_number, payload.user_otp)
    except DatabaseUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if is_valid:
        formatted_num = _standardize_phone(payload.phone_number)
        
        # PostgreSQL Service Layer UPSERT
        try:
            user = UserService.upsert_user(db, formatted_num)
        except Exception as e:
            # If postgres is down, we don't necessarily want to block login if OTP works,
            # but ideally we log it. For now, raise 503 so frontend catches it.
            raise HTTPException(status_code=503, detail=f"Database provisioning failed: {str(e)}")

        access_token = create_access_token({"sub": str(user.id)})
        return {
            "message": "Authentication successful",
            "access_token": access_token,
            "token_type": "bearer",
            "phone_number": formatted_num,
            "user_id": user.id
        }
    else:
        raise HTTPException(status_code=401, detail="Incorrect OTP. Please try again.")
