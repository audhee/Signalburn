"""import random
import time
import os
from dotenv import load_dotenv

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# In-memory OTP store: { phone_number: {"otp": "123456", "expires_at": 1690000000} }
OTP_STORE = {}

def _get_twilio_client() -> Client:
   # Initialize and return a Twilio REST client
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise ValueError(
            "Twilio credentials not found. "
            "Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in backend/.env"
        )
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def generate_otp(phone_number: str) -> str:
    # Generate a 6-digit OTP and send it via Twilio SMS
    otp = str(random.randint(100000, 999999))
    expires_at = time.time() + 300  # valid for 5 minutes
    OTP_STORE[phone_number] = {"otp": otp, "expires_at": expires_at}

    formatted_number = phone_number if phone_number.startswith("+") else f"+91{phone_number}"
    client = _get_twilio_client()
    message = client.messages.create(
        body=f"Your Arohan OTP is: {otp}. Valid for 5 minutes. Do not share this.",
        from_=TWILIO_PHONE_NUMBER,
        to=formatted_number,
    )
    print(f"[Twilio] SMS sent to {formatted_number} | SID: {message.sid} | Status: {message.status}")
    print(f"[OTP] *** Code for {formatted_number}: {otp} ***")
    return otp


def verify_otp(phone_number: str, user_otp: str) -> bool:
    # Verify the OTP provided by the user against the stored OTP.
    record = OTP_STORE.get(phone_number)

    if not record:
        return False

    if time.time() > record["expires_at"]:
        del OTP_STORE[phone_number]
        return False

    if record["otp"] == user_otp:
        del OTP_STORE[phone_number]
        return True

    return False"""


import random
import time
import os
import redis
import logging
from dotenv import load_dotenv

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Custom Exceptions
class DatabaseUnavailableError(Exception):
    """Raised when Redis is unreachable."""
    pass

class RateLimitExceededError(ValueError):
    """Raised when OTP requests are spammed (cooldown or hourly limit)."""
    pass

# Connect to local Redis for OTP caching and rate limiting
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def _standardize_phone(phone_number: str) -> str:
    """Ensure phone number strictly adheres to +91XXXXXXXXXX format."""
    cleaned = "".join(ch for ch in phone_number.strip() if ch.isdigit() or ch == "+")
    if not cleaned.startswith("+"):
        if len(cleaned) == 10:
            return f"+91{cleaned}"
        else:
            return f"+{cleaned}"
    return cleaned


def _get_twilio_client() -> Client:
    """Initialize and return a Twilio REST client."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise ValueError(
            "Twilio credentials not found. "
            "Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in backend/.env"
        )
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def generate_otp(phone_number: str) -> str:
    """Generate a 6-digit OTP and send it via Twilio SMS, cached in Redis with strict rate limiting."""
    formatted_number = _standardize_phone(phone_number)

    # Dev bypass should work even if Redis/Twilio are unavailable.
    if formatted_number == "+919999999999":
        logger.info(f"Dev bypass OTP generated for {formatted_number}: 123456")
        return "123456"
    
    try:
        # 1. Cooldown Check (60 seconds)
        if redis_client.get(f"{formatted_number}:cooldown"):
            logger.warning(f"Cooldown active for {formatted_number}")
            raise RateLimitExceededError("Please wait 60 seconds before requesting a new OTP.")

        # 2. Hourly Spam Limit Check (5 requests per hour)
        hourly_key = f"{formatted_number}:hourly_count"
        count = redis_client.incr(hourly_key)
        if count == 1:
            redis_client.expire(hourly_key, 3600)  # 1 hour
        if count > 5:
            logger.warning(f"Hourly rate limit exceeded for {formatted_number}")
            raise RateLimitExceededError("Too many OTP requests. Please try again in an hour.")

        otp = str(random.randint(100000, 999999))

        # Explicitly overwrite OTP and reset attempts back to 3
        redis_client.setex(f"{formatted_number}:otp", 300, otp)
        redis_client.setex(f"{formatted_number}:attempts", 300, 3)
        # Set cooldown for 60 seconds
        redis_client.setex(f"{formatted_number}:cooldown", 60, 1)

    except redis.exceptions.RedisError as e:
        logger.error(f"Redis connection failed during generate_otp: {str(e)}")
        raise DatabaseUnavailableError("Authentication service is temporarily unavailable.")

    try:
        client = _get_twilio_client()
        message = client.messages.create(
            body=f"Your Arohan OTP is: {otp}. Valid for 5 minutes. Do not share this.",
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_number,
        )
        logger.info(f"Twilio SMS sent to {formatted_number} | SID: {message.sid} | Status: {message.status}")
    except TwilioRestException as e:
        logger.error(f"Twilio SMS delivery failed for {formatted_number}: {str(e)}")
        raise
        
    return otp


def verify_otp(phone_number: str, user_otp: str) -> bool:
    """Verify the OTP against Redis securely using Atomic DECR."""
    formatted_number = _standardize_phone(phone_number)

    # Dev bypass should verify independently of Redis state.
    if formatted_number == "+919999999999" and user_otp == "123456":
        logger.info(f"Dev bypass OTP verified for {formatted_number}")
        return True
    
    try:
        stored_otp = redis_client.get(f"{formatted_number}:otp")
        
        if not stored_otp:
            logger.warning(f"Verification failed for {formatted_number}: OTP expired or absent.")
            raise ValueError("Invalid or expired OTP. Please try again.")

        if stored_otp == user_otp:
            # Success: Immediately purge keys
            redis_client.delete(f"{formatted_number}:otp")
            redis_client.delete(f"{formatted_number}:attempts")
            # Clear cooldown on success so they can re-login if needed
            redis_client.delete(f"{formatted_number}:cooldown")
            logger.info(f"OTP successfully verified for {formatted_number}")
            return True

        # Failure: Use atomic DECR to prevent race conditions
        attempts_left = redis_client.decr(f"{formatted_number}:attempts")
        
        if attempts_left < 0:
            redis_client.delete(f"{formatted_number}:otp")
            logger.warning(f"Max verification attempts exceeded for {formatted_number}")
            raise ValueError("Maximum attempts exceeded. Please request a new OTP.")
            
        logger.warning(f"Incorrect OTP guess for {formatted_number}. Attempts remaining: {attempts_left}")
        return False
        #.\ngrok http 8000
    except redis.exceptions.RedisError as e:
        logger.error(f"Redis connection failed during verify_otp: {str(e)}")
        raise DatabaseUnavailableError("Authentication service is temporarily unavailable.")

# docker start local-redis
# docker start local-postgres
# cd c:\projects\Arohan\Arohan\backend start_backend.bat
# .\ngrok http 8000
# npx expo start
