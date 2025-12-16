from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.db.session import get_db

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve users.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="The user doesn't have enough privileges")
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()
