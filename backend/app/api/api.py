"""
API Router configuration

Purpose:
    aggregates all Version 1 API endpoints into a single router.
    Prefixes are defined here (e.g. `/courses`, `/exams`).
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, courses, exams, submission, users, bulk_exams

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(exams.router, prefix="/exams", tags=["exams"])
api_router.include_router(bulk_exams.router, prefix="/exams", tags=["exams"])
api_router.include_router(submission.router, prefix="/submissions", tags=["submissions"])

