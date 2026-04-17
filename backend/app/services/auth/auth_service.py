import random
import time
import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()

# Twilio credentials loaded from .env
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# In-memory OTP store: { phone_number: {"otp": "123456", "expires_at": 1690000000} }
# For production, swap this with Redis
OTP_STORE = {}


def _get_twilio_client() -> Client:
    """Initialize and return a Twilio REST client."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise ValueError(
            "Twilio credentials not found. "
            "Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in backend/.env"
        )
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def generate_otp(phone_number: str) -> str:
    """Generate a 6-digit OTP, store it, and send it via Twilio SMS."""
    otp = str(random.randint(100000, 999999))
    expires_at = time.time() + 300  # Valid for 5 minutes

    OTP_STORE[phone_number] = {"otp": otp, "expires_at": expires_at}

    # Format the phone number with country code if not already present
    # Assumes Indian numbers — prepend +91 if no + sign
    formatted_number = phone_number if phone_number.startswith("+") else f"+91{phone_number}"

    client = _get_twilio_client()

    message = client.messages.create(
        body=f"Your Arohan emergency app OTP is: {otp}. Valid for 5 minutes. Do not share this with anyone.",
        from_=TWILIO_PHONE_NUMBER,
        to=formatted_number,
    )

    print(f"[Twilio] SMS sent to {formatted_number} | SID: {message.sid} | Status: {message.status}")

    return otp


def verify_otp(phone_number: str, user_otp: str) -> bool:
    """Verify the OTP provided by the user against the stored OTP."""
    record = OTP_STORE.get(phone_number)

    if not record:
        return False

    if time.time() > record["expires_at"]:
        del OTP_STORE[phone_number]
        return False

    if record["otp"] == user_otp:
        # OTP is valid — remove it so it can't be reused
        del OTP_STORE[phone_number]
        return True

    return False
