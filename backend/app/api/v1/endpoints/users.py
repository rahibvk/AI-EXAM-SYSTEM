from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.api import deps
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.db.session import get_db

router = APIRouter()

@router.get("/dashboard-stats")
async def get_teacher_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get dashboard statistics for the logged-in teacher.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    from app.models.course import Course
    from app.models.exam import Exam
    from app.models.answer import StudentAnswer, Evaluation
    
    # 1. Active Courses
    courses_query = select(func.count(Course.id)).filter(Course.teacher_id == current_user.id)
    courses_result = await db.execute(courses_query)
    courses_count = courses_result.scalar() or 0
    
    # 2. Total Students (Unique students enrolled in my courses)
    # Join student_courses -> Course
    from app.models.course import student_courses
    students_query = (
        select(func.count(func.distinct(student_courses.c.student_id)))
        .join(Course, student_courses.c.course_id == Course.id)
        .filter(Course.teacher_id == current_user.id)
    )
    students_result = await db.execute(students_query)
    students_count = students_result.scalar() or 0
    
    # 3. Pending Reviews
    # Pending reviews for exams in my courses
    reviews_query = (
        select(func.count(Evaluation.id))
        .join(StudentAnswer, Evaluation.answer_id == StudentAnswer.id)
        .join(Exam, StudentAnswer.exam_id == Exam.id)
        .join(Course, Exam.course_id == Course.id)
        .filter(Course.teacher_id == current_user.id)
        .filter(Evaluation.review_requested == True)
    )
    reviews_result = await db.execute(reviews_query)
    reviews_count = reviews_result.scalar() or 0
    
    return {
        "courses": courses_count,
        "students": students_count,
        "pending_reviews": reviews_count
    }

@router.get("/my-students", response_model=List[UserResponse])
async def get_my_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get list of students who have submitted answers to the teacher's courses.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Return only students explicitly enrolled in this teacher's courses
    from app.models.course import Course, student_courses
    
    query = (
        select(User)
        .join(student_courses, student_courses.c.student_id == User.id)
        .join(Course, student_courses.c.course_id == Course.id)
        .filter(Course.teacher_id == current_user.id)
        .filter(User.role == UserRole.STUDENT)
        .distinct()
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/search", response_model=List[UserResponse])
async def search_students(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Search for students by name or email.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    query = select(User).filter(
        User.role == UserRole.STUDENT,
        (User.email.ilike(f"%{q}%")) | (User.full_name.ilike(f"%{q}%"))
    ).limit(10)
    
    result = await db.execute(query)
    return result.scalars().all()

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
