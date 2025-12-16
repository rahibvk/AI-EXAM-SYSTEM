from typing import Any
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.services.chat_service import ChatService

router = APIRouter()

@router.post("/message")
async def chat_message(
    message: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Chat with the AI Assistant.
    """
    response = await ChatService.chat_with_student(db, current_user.id, message)
    return {"response": response}
