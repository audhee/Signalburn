import jwt
from datetime import datetime, timedelta
from app.core.config import settings

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Encodes a payload into a JWT using the application's secret key."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    """Decodes a JWT and returns the payload. Returns None if invalid or expired."""
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded_token
    except jwt.PyJWTError:
        return None
