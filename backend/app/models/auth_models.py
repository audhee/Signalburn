from pydantic import BaseModel

class RequestOTPPayload(BaseModel):
    phone_number: str

class VerifyOTPPayload(BaseModel):
    phone_number: str
    user_otp: str
