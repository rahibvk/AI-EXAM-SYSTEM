"""
Security & Authentication Utilities

Purpose:
    Handles password hashing (Bcrypt) and JWT Token generation/validation.

Dependencies:
    - passlib: For secure password hashing.
    - python-jose: For encoding/decoding JSON Web Tokens (JWT).

Security Note:
    - The SECRET_KEY is currently hardcoded. In Production, this MUST be moved to environment variables.
"""
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password Hashing Context
# Uses bcrypt which is standard for secure password storage.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    Generates a JWT Access Token.
    
    Inputs:
        subject: The user identifier (e.g., User ID or Email) to encode in the token.
        expires_delta: Optional custom expiration time.

    Outputs:
        str: Encoded JWT string.

    Defaults:
        - If no expiration is provided, defaults to 24 hours (1440 minutes).
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=1440) # Default 24 hours
    
    to_encode = {"exp": expire, "sub": str(subject)}
    # WARNING: Secret Key should be unique per environment and private
    encoded_jwt = jwt.encode(to_encode, "SECRET_KEY_CHANGE_ME", algorithm=ALGORITHM) # TODO: Move secret to settings
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a password using bcrypt (computationally expensive to prevent checking)."""
    return pwd_context.hash(password)
