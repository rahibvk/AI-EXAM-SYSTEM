"""
Exam CRUD Operations

Purpose:
    Handles lifecycle of Exams and their Questions.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.exam import Exam, Question
from app.schemas.exam import ExamCreate, QuestionCreate

async def create_exam(db: AsyncSession, exam: ExamCreate) -> Exam:
    """
    Creates an Exam and its associated Questions in a single transaction.
    """
    # 1. Create Exam
    db_exam = Exam(
        title=exam.title,
        description=exam.description,
        course_id=exam.course_id,
        start_time=exam.start_time,
        end_time=exam.end_time,
        duration_minutes=exam.duration_minutes,
        total_marks=exam.total_marks,
        passing_marks=exam.passing_marks,
        mode=exam.mode
    )
    db.add(db_exam)
    await db.commit()
    await db.refresh(db_exam)
    
    # 2. Add Questions
    for q in exam.questions:
        db_question = Question(
            exam_id=db_exam.id,
            text=q.text,
            question_type=q.question_type,
            marks=q.marks,
            model_answer=q.model_answer
        )
        db.add(db_question)
    
    await db.commit()
    
    # Reload with questions to return full object
    result = await db.execute(select(Exam).options(selectinload(Exam.questions)).filter(Exam.id == db_exam.id))
    return result.scalars().first()

async def get_exams_by_course(db: AsyncSession, course_id: int) -> List[Exam]:
    """Fetches all exams for a given course, including questions."""
    result = await db.execute(select(Exam).options(selectinload(Exam.questions)).filter(Exam.course_id == course_id))
    return result.scalars().all()

async def get_exam(db: AsyncSession, exam_id: int) -> Optional[Exam]:
    """Fetches a single exam by ID, including questions."""
    result = await db.execute(select(Exam).options(selectinload(Exam.questions)).filter(Exam.id == exam_id))
    return result.scalars().first()

async def delete_exam(db: AsyncSession, exam_id: int) -> Optional[Exam]:
    """Deletes an exam and its questions (via cascade)."""
    exam = await get_exam(db, exam_id)
    if exam:
        await db.delete(exam)
        await db.commit()
    return exam
