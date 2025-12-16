from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.answer import StudentAnswer, Evaluation
from app.schemas.answer import ExamSubmission, StudentAnswerBase

async def submit_exam(db: AsyncSession, submission: ExamSubmission, student_id: int) -> List[StudentAnswer]:
    saved_answers = []
    for ans in submission.answers:
        db_ans = StudentAnswer(
            exam_id=submission.exam_id,
            student_id=student_id,
            question_id=ans.question_id,
            answer_text=ans.answer_text,
            answer_file_path=ans.answer_file_path
        )
        db.add(db_ans)
        saved_answers.append(db_ans)
    
    await db.commit()
    await db.commit()
    
    # Re-fetch to get relationships (evaluation) loaded and avoid MissingGreenlet error
    return await get_student_answers(db, submission.exam_id, student_id)

async def get_student_answers(db: AsyncSession, exam_id: int, student_id: int) -> List[StudentAnswer]:
    result = await db.execute(
        select(StudentAnswer)
        .options(
            selectinload(StudentAnswer.evaluation),
            selectinload(StudentAnswer.student),
            selectinload(StudentAnswer.exam),
            selectinload(StudentAnswer.question)
        )
        .filter(StudentAnswer.exam_id == exam_id, StudentAnswer.student_id == student_id)
    )
    return result.scalars().all()

async def get_all_exam_submissions(db: AsyncSession, exam_id: int) -> List[StudentAnswer]:
    result = await db.execute(
        select(StudentAnswer)
        .options(
            selectinload(StudentAnswer.evaluation),
            selectinload(StudentAnswer.student),
            selectinload(StudentAnswer.exam),
            selectinload(StudentAnswer.question)
        )
        .filter(StudentAnswer.exam_id == exam_id)
    )
    return result.scalars().all()

async def save_evaluation(db: AsyncSession, evaluation: Evaluation) -> Evaluation:
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation
async def get_student_history(db: AsyncSession, student_id: int) -> List[StudentAnswer]:
    result = await db.execute(
        select(StudentAnswer)
        .options(
            selectinload(StudentAnswer.evaluation),
            selectinload(StudentAnswer.exam),
            selectinload(StudentAnswer.question)
        )
        .filter(StudentAnswer.student_id == student_id)
        .order_by(StudentAnswer.submitted_at.desc())
    )
    return result.scalars().all()

async def request_review(db: AsyncSession, answer_id: int, student_comment: str):
    stmt = select(Evaluation).where(Evaluation.answer_id == answer_id)
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()
    
    if evaluation:
        evaluation.review_requested = True
        evaluation.student_comment = student_comment
        await db.commit()
        await db.refresh(evaluation)
    return evaluation

async def update_manual_grade(db: AsyncSession, answer_id: int, marks: float, feedback: str):
    stmt = select(Evaluation).where(Evaluation.answer_id == answer_id)
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()
    
    if evaluation:
        evaluation.marks_awarded = marks
        evaluation.teacher_comment = feedback
        evaluation.review_requested = False # Mark review as done
        await db.commit()
        await db.refresh(evaluation)
    return evaluation

async def get_pending_reviews(db: AsyncSession) -> List[StudentAnswer]:
    """
    Fetch all answers where a review is requested.
    Eager load relative data for display.
    """
    result = await db.execute(
        select(StudentAnswer)
        .join(Evaluation)
        .where(Evaluation.review_requested == True)
        .options(
            selectinload(StudentAnswer.evaluation),
            selectinload(StudentAnswer.student),
            selectinload(StudentAnswer.exam),
            selectinload(StudentAnswer.question)
        )
        .order_by(Evaluation.evaluated_at.desc())
    )
    return result.scalars().all()
