from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.otp_service import generate_otp, verify_otp

router = APIRouter()

class RequestOTPPayload(BaseModel):
    phone_number: str

class VerifyOTPPayload(BaseModel):
    phone_number: str
    user_otp: str

@router.post("/request-otp")
def request_otp(payload: RequestOTPPayload):
    if not payload.phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")
        
    generate_otp(payload.phone_number)
    return {"message": "OTP sent successfully"}

@router.post("/verify-otp")
def verify_otp_endpoint(payload: VerifyOTPPayload):
    is_valid = verify_otp(payload.phone_number, payload.user_otp)
    
    if is_valid:
        # In a real app, generate and return a JWT token here
        return {"message": "Authentication successful", "token": "mock_jwt_token_12345"}
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
