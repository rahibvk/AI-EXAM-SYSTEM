from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.api import deps
from app.crud import crud_answer, crud_exam
from app.schemas.answer import ExamSubmission, StudentAnswerResponse, EvaluationResponse
from app.db.session import get_db, AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.answer import StudentAnswer
from app.services.evaluation_service import EvaluationService
from app.services.ocr_service import OCRService
from app.models.exam import Question

router = APIRouter()

async def evaluate_answers_background_task(answer_ids: List[int]):
    """
    Background task to run AI evaluation for specfic answers.
    Uses its own DB session.
    """
    with open("debug_eval.log", "a") as f:
        f.write(f"STARTING EVALUATION for IDs: {answer_ids}\n")
    
    print(f"Starting background evaluation for {len(answer_ids)} answers...")
    async with AsyncSessionLocal() as db:
        try:
            # Fetch answers with questions loaded
            stmt = select(StudentAnswer).options(
                selectinload(StudentAnswer.question),
                selectinload(StudentAnswer.exam),
                selectinload(StudentAnswer.evaluation)
            ).filter(StudentAnswer.id.in_(answer_ids))
            
            result = await db.execute(stmt)
            answers = result.scalars().all()
            
            with open("debug_eval.log", "a") as f:
                f.write(f"Fetched {len(answers)} answers from DB.\n")

            # Context Optimization: Fetch course materials ONCE
            if not answers:
                print("Background Evaluation: No answers found matching IDs.")
                return

            # Assume all answers belong to same course/exam for this batch
            first_exam_id = answers[0].exam_id
            
            # Fetch Course Materials for Context
            exam_obj = answers[0].exam
            if not exam_obj:
                 # Fallback fetch
                 with open("debug_eval.log", "a") as f:
                     f.write(f"Exam object missing, fetching fallback for ID {first_exam_id}\n")
                 exam_stmt = select(crud_exam.Exam).filter(crud_exam.Exam.id == first_exam_id)
                 exam_res = await db.execute(exam_stmt)
                 exam_obj = exam_res.scalar_one_or_none()
            
            context_text = ""
            if exam_obj:
                 try:
                     from app.models.course import CourseMaterial
                     mat_stmt = select(CourseMaterial).filter(CourseMaterial.course_id == exam_obj.course_id)
                     mat_res = await db.execute(mat_stmt)
                     materials = mat_res.scalars().all()
                     # Build context string
                     context_text = "\n\n".join([f"--- Material: {m.title} ---\n{m.content_summary}..." for m in materials])
                     print(f"Background Evaluation: Loaded context from {len(materials)} materials.")
                     with open("debug_eval.log", "a") as f:
                         f.write(f"Loaded context with {len(materials)} materials.\n")
                 except Exception as context_err:
                     print(f"Background Evaluation Context Error: {context_err}")
                     with open("debug_eval.log", "a") as f:
                         f.write(f"Error loading context: {context_err}\n")

            for answer in answers:
                if answer.evaluation:
                    with open("debug_eval.log", "a") as f:
                        f.write(f"Answer {answer.id} already evaluated. Skipping.\n")
                    continue
                
                question = answer.question
                if not question or not question.model_answer:
                    # Try manual fetch if eager load failed
                    question = await db.get(Question, answer.question_id)
                
                if not question or not question.model_answer:
                    with open("debug_eval.log", "a") as f:
                        f.write(f"Question or model answer missing for Answer {answer.id}. Skipping.\n")
                    continue
                
                # OCR Logic
                if not answer.answer_text and answer.answer_file_path:
                    try:
                        print(f"Running OCR for answer {answer.id}")
                        transcribed_text = await OCRService.transcribe_image(answer.answer_file_path)
                        answer.answer_text = transcribed_text
                        db.add(answer)
                        await db.commit()
                        with open("debug_eval.log", "a") as f:
                            f.write(f"OCR executed for Answer {answer.id}\n")
                    except Exception as e:
                        print(f"OCR Failed for {answer.id}: {e}")
                
                # AI Evaluation
                try:
                    with open("debug_eval.log", "a") as f:
                        f.write(f"Calling EvaluationService for Answer {answer.id}\n")
                    
                    evaluation = await EvaluationService.evaluate_answer(
                        answer=answer,
                        model_answer=question.model_answer,
                        question_text=question.text,
                        max_marks=question.marks,
                        context_text=context_text # Pass the context!
                    )
                    await crud_answer.save_evaluation(db, evaluation)
                    print(f"Evaluated answer {answer.id}")
                    with open("debug_eval.log", "a") as f:
                        f.write(f"Successfully evaluated Answer {answer.id}\n")
                except Exception as e:
                    print(f"Evaluation Failed for {answer.id}: {e}")
                    with open("debug_eval.log", "a") as f:
                        f.write(f"FAILED to evaluate Answer {answer.id}: {e}\n")
                    
        except Exception as e:
            import traceback
            print(f"Background Task Failed CRITICALLY: {e}")
            traceback.print_exc()
            with open("debug_eval.log", "a") as f:
                f.write(f"CRITICAL ERROR in background task: {e}\n")

@router.post("/submit", response_model=List[StudentAnswerResponse])
async def submit_exam_answers(
    *,
    db: AsyncSession = Depends(get_db),
    submission: ExamSubmission,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks
) -> Any:
    """
    Submit answers for an exam.
    """
    # Validate exam exists
    exam = await crud_exam.get_exam(db, exam_id=submission.exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Save answers
    answers = await crud_answer.submit_exam(db, submission=submission, student_id=current_user.id)
    
    # Trigger Background Evaluation
    answer_ids = [a.id for a in answers]
    background_tasks.add_task(evaluate_answers_background_task, answer_ids)
    
    return answers

@router.get("/{exam_id}/my-answers", response_model=List[StudentAnswerResponse])
async def read_my_answers(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    answers = await crud_answer.get_student_answers(db, exam_id=exam_id, student_id=current_user.id)
    return answers

@router.get("/{exam_id}/all", response_model=List[StudentAnswerResponse])
async def read_all_submissions(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all student submissions for a specific exam.
    Only Teachers/Admins.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    answers = await crud_answer.get_all_exam_submissions(db, exam_id=exam_id)
    return answers


async def run_evaluation_task(db: AsyncSession, answer_ids: List[int]):
    # This is a background task helper. 
    # In real world, use Celery/Redis Queue.
    # Because db session in background task is tricky with simple Dependency, 
    # we usually need a fresh session context manager here.
    pass 

@router.get("/me", response_model=List[StudentAnswerResponse])
async def read_my_submission_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all past submissions for the current student.
    """
    answers = await crud_answer.get_student_history(db, student_id=current_user.id)
    return answers


@router.post("/{exam_id}/evaluate", response_model=Any)
async def evaluate_exam_submissions(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Trigger AI evaluation for all answers in an exam.
    Only Teacher/Admin.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Fetch all answers for exam
    submissions = await crud_answer.get_all_exam_submissions(db, exam_id=exam_id)
    
    evaluated_count = 0
    for answer in submissions:
        # Skip if already evaluated
        if answer.evaluation:
            continue
            
        # Get question details (need to lazy load or join)
        # Note: In `get_all_exam_submissions` we didn't eager load question.
        # We need question model answer and text.
        
        # Force refresh/fetch question (inefficient loop n+1 but okay for MVP)
        # Better: Join Question in the initial query. 
        # For now, let's fetch it if missing.
        if not answer.question:
             # This attribute might be missing if not loaded. 
             # Let's rely on `await db.get(Question, answer.question_id)`
             question = await db.get(Question, answer.question_id)
        else:
            question = answer.question
            
        if not question or not question.model_answer:
            continue
            
        # Check if answer needs OCR
        if not answer.answer_text and answer.answer_file_path:
            print(f"Running OCR for answer {answer.id}")
            # Ensure path is valid/exists. 
            # In a real app, might need to download from S3 if path is a URL.
            # Here assuming local path as per our upload logic (which we haven't built for answers yet, but will assume generic 'uploads/')
            try:
                transcribed_text = await OCRService.transcribe_image(answer.answer_file_path)
                answer.answer_text = transcribed_text
                # Update DB with transcribed text so we don't re-run
                db.add(answer)
                await db.commit() 
            except Exception as e:
                print(f"OCR skipped/failed: {e}")
                
        # Perform Evaluation
        evaluation = await EvaluationService.evaluate_answer(
            answer=answer,
            model_answer=question.model_answer,
            question_text=question.text,
            max_marks=question.marks
        )
        await crud_answer.save_evaluation(db, evaluation)
        evaluated_count += 1

    return {"message": f"Evaluations completed for {evaluated_count} answers."}
from app.schemas.answer import ReviewRequest, ManualGradeRequest

@router.get("/pending-reviews", response_model=List[StudentAnswerResponse])
async def read_pending_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all pending reviews. Only accessible by teachers/admins.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    reviews = await crud_answer.get_pending_reviews(db)
    return reviews

@router.post("/{answer_id}/request-review", response_model=Any)
async def request_manual_review(
    answer_id: int,
    review_req: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Student requests manual review for an answer.
    """
    # Verify ownership
    answer = await db.get(StudentAnswer, answer_id)
    if not answer or answer.student_id != current_user.id:
        raise HTTPException(status_code=404, detail="Answer not found")
        
    await crud_answer.request_review(db, answer_id, review_req.student_comment)
    return {"message": "Review requested successfully"}

@router.post("/{answer_id}/manual-grade", response_model=Any)
async def submit_manual_grade(
    answer_id: int,
    grade_req: ManualGradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Teacher updates grade manually.
    """
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await crud_answer.update_manual_grade(db, answer_id, grade_req.marks, grade_req.feedback)
    return {"message": "Grade updated successfully"}
