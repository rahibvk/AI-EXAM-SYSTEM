"""
Authentication Endpoints

Purpose:
    Handles User Login and Registration.

Endpoints:
    - POST /login: Authenticates credentials and returns a JWT Bearer token.
    - POST /register: Creates a new user account.
    - GET /me: Returns the current logged-in user's profile.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core import security
from app.crud import crud_user
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Validates email/password and returns a JWT.
    """
    print(f"DEBUG: Login attempt for {form_data.username}")
    try:
        user = await crud_user.authenticate(
            db, email=form_data.username, password=form_data.password
        )
        if not user:
            print(f"DEBUG: Login failed - incorrect credentials for {form_data.username}")
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        
        access_token_expires = timedelta(minutes=30)
        access_token = security.create_access_token(
            subject=user.email, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print(f"DEBUG: Login exception: {e}")
        raise e

@router.post("/register", response_model=UserResponse)
async def register_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
):
    """
    Create new user.
    Checks if email already exists before creating.
    """
    user = await crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = await crud_user.create_user(db, user_in=user_in)
    return user

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(deps.get_current_active_user)):
    """
    Get current user.
    Used by frontend to validate session and get user role/id.
    """
    return current_user
