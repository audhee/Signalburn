from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.utils.security import decode_access_token
from app.services.user.user_service import UserService
from app.models.db_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/fake-token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Validates the bearer token attached to the request, and returns the User object.
    Raises a 401 Unauthorized if the token is invalid, expired, or the user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
        
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception
        
    user = UserService.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
        
    return user
