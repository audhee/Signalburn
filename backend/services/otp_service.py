import random
import time

# In-memory storage for development: { phone_number: {"otp": "123456", "expires_at": 1690000000} }
OTP_STORE = {}

def generate_otp(phone_number: str) -> str:
    # Generate 6 digit OTP
    otp = str(random.randint(100000, 999999))
    # Expires in 5 minutes
    expires_at = time.time() + 300 
    
    OTP_STORE[phone_number] = {"otp": otp, "expires_at": expires_at}
    
    # In a real app, integrate Twilio, Firebase or Fast2SMS here.
    print(f"\n==========================================")
    print(f"DEV MOCK SMS: OTP for {phone_number} is {otp}")
    print(f"==========================================\n")
    
    return otp

def verify_otp(phone_number: str, user_otp: str) -> bool:
    record = OTP_STORE.get(phone_number)
    
    if not record:
        return False
        
    if time.time() > record["expires_at"]:
        del OTP_STORE[phone_number]
        return False
        
    if record["otp"] == user_otp:
        # OTP verified, remove it
        del OTP_STORE[phone_number]
        return True
        
    return False
