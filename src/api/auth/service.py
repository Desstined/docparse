from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from src.api.auth.utils import get_current_active_user
from src.api.auth.service import create_access_token
from src.api.config import settings

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({
        "exp": expire,
        "scopes": ["documents:read", "documents:write"]  # Add default scopes
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt 