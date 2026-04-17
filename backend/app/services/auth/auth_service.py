import random
import time
import os
from dotenv import load_dotenv

# ============================================================
# TWILIO IMPORTS — commented out to save SMS quota during dev
# Uncomment when you want real SMS OTP
# ------------------------------------------------------------
# from twilio.rest import Client
# from twilio.base.exceptions import TwilioRestException
# ============================================================

load_dotenv()

# Twilio credentials loaded from .env
# (kept here for when you switch back to real SMS)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# In-memory OTP store: { phone_number: {"otp": "123456", "expires_at": 1690000000} }
# For production, swap this with Redis
OTP_STORE = {}

# ============================================================
# DEV MODE FLAG — set to True to use fixed OTP 123456
#                 set to False to use real Twilio SMS
# ============================================================
DEV_MODE = True
DEV_OTP  = "123456"
# ============================================================


# def _get_twilio_client() -> Client:
#     """Initialize and return a Twilio REST client."""
#     if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
#         raise ValueError(
#             "Twilio credentials not found. "
#             "Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in backend/.env"
#         )
#     return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def generate_otp(phone_number: str) -> str:
    """Generate OTP and either send via Twilio (DEV_MODE=False) or use fixed 123456 (DEV_MODE=True)."""

    if DEV_MODE:
        # ---- DEV MODE: fixed OTP, no SMS sent ----
        otp = DEV_OTP
        expires_at = time.time() + 30
        OTP_STORE[phone_number] = {"otp": otp, "expires_at": expires_at}
        print(f"[DEV MODE] OTP for {phone_number} is: {otp} (no SMS sent)")
        return otp

    # ---- PRODUCTION: real Twilio SMS ----
    # otp = str(random.randint(100000, 999999))
    # expires_at = time.time() + 300
    # OTP_STORE[phone_number] = {"otp": otp, "expires_at": expires_at}
    #
    # formatted_number = phone_number if phone_number.startswith("+") else f"+91{phone_number}"
    # client = _get_twilio_client()
    # message = client.messages.create(
    #     body=f"Your Arohan emergency app OTP is: {otp}. Valid for 5 minutes. Do not share this with anyone.",
    #     from_=TWILIO_PHONE_NUMBER,
    #     to=formatted_number,
    # )
    # print(f"[Twilio] SMS sent to {formatted_number} | SID: {message.sid} | Status: {message.status}")
    # return otp


def verify_otp(phone_number: str, user_otp: str) -> bool:
    """Verify the OTP provided by the user against the stored OTP."""

    # DEV MODE: accept the fixed OTP directly — no store lookup needed
    if DEV_MODE:
        result = user_otp == DEV_OTP
        print(f"[DEV MODE] OTP check for {phone_number}: entered='{user_otp}' → {'✅ OK' if result else '❌ Wrong'}")
        return result

    # PRODUCTION: check the store
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
