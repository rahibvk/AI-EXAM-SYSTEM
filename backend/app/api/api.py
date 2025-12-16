from fastapi import APIRouter
from app.api.v1.endpoints import auth, courses, exams, submission, chat, users

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(exams.router, prefix="/exams", tags=["exams"])
api_router.include_router(submission.router, prefix="/submissions", tags=["submissions"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
