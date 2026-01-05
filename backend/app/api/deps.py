"""
API Dependencies

Purpose:
    Reusable dependencies for FastAPI Routes.
    Primary use is Authentication (User Injection).

Flow:
    1. Extracts Bearer Token from Header (`oauth2_scheme`).
    2. Decodes JWT to get Email.
    3. Fetches User from DB.
    4. Injects `current_user` into the route function.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core import security
from app.core.config import settings
from app.crud import crud_user
from app.models.user import User
from app.schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Validates the JWT token and returns the current user.
    Raises 401 Unauthorized if invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # TODO: Move secret to settings and use same as security.py
        payload = jwt.decode(token, "SECRET_KEY_CHANGE_ME", algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await crud_user.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """wrapper to check if user is active (logic can be expanded properly later)."""
    # Check if active if you had an is_active field
    return current_user
