"""
User & Authentication Schemas

Purpose:
    Defines Pydantic models for User validation and API request/response structures.
    Includes schemas for Auth Tokens and Login payloads.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class UserBase(BaseModel):
    """Shared properties for User models."""
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.STUDENT

class UserCreate(UserBase):
    """Payload for creating a new user (Registration)."""
    password: str

class UserLogin(BaseModel):
    """Payload for User Login."""
    email: EmailStr
    password: str

class UserResponse(UserBase):
    """Public User definition (excludes password)."""
    id: int
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """JWT Token structure."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Data embedded inside the JWT."""
    email: Optional[str] = None
