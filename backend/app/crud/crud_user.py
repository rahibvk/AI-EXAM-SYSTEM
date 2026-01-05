"""
User CRUD Operations

Purpose:
    Handles Create, Read, Update, Delete operations for the User model.
    Includes authentication logic (password verification).
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieves a user by their email address."""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """
    Creates a new user.
    Hashes the password before storing it in the database.
    """
    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def authenticate(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Verifies user credentials.
    Returns: User object if valid, None otherwise.
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
