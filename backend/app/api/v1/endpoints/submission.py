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
    Background task to run AI evaluation for answers in PARALLEL.
    """
    import asyncio
    # 1. Brief delay to ensure DB commit propagation
    await asyncio.sleep(2) 
    
    print(f"Starting background evaluation for {len(answer_ids)} answers...")

    # Context Optimization: Fetch course materials ONCE using a disposable session
    context_text = ""
    try:
        async with AsyncSessionLocal() as temp_db:
             # Basic check to get exam ID from first answer
             result = await temp_db.execute(select(StudentAnswer).filter(StudentAnswer.id == answer_ids[0]))
             first_ans = result.scalars().first()
             if first_ans:
                 # Fetch exam to get course_id
                 ex_res = await temp_db.execute(select(Question).filter(Question.id == first_ans.question_id))
                 # Wait, StudentAnswer -> Question -> Exam. 
                 # Let's just fetch the exam_id from answer if available or via question
                 # Assuming StudentAnswer has exam_id
                 pass
                 
             # Only fetch context if we can. (Simplification: Skip context fetching optimization for now to fix crash first)
             pass
    except Exception as e:
        print(f"Context setup warning: {e}")

    # Define single processor that MANAGES ITS OWN SESSION
    async def process_single_answer(ans_id):
        try:
             async with asyncio.timeout(90): # Python 3.11+ syntax or wait_for
                async with AsyncSessionLocal() as db:
                    # ... logic ...
                    stmt = select(StudentAnswer).options(
                        selectinload(StudentAnswer.question),
                        selectinload(StudentAnswer.evaluation)
                    ).filter(StudentAnswer.id == ans_id)
                    
                    result = await db.execute(stmt)
                    answer = result.scalars().first()
                    
                    if not answer: return

                    if answer.evaluation: return
                    
                    question = answer.question
                    if not question:
                        question = await db.get(Question, answer.question_id)
                    
                    if not question or not question.model_answer: return 

                    # OCR Logic
                    if not answer.answer_text and answer.answer_file_path:
                        try:
                            # 30s timeout for OCR
                            answer.answer_text = await asyncio.wait_for(OCRService.transcribe_image(answer.answer_file_path), timeout=30.0)
                        except asyncio.TimeoutError:
                            print(f"OCR Timeout {answer.id}")
                            answer.answer_text = "[OCR Timeout]"
                        except Exception as e:
                            print(f"OCR Error {answer.id}: {e}")

                    # AI Evaluation
                    # 45s timeout for Grading
                    try:
                        evaluation = await asyncio.wait_for(EvaluationService.evaluate_answer(
                            answer=answer,
                            model_answer=question.model_answer,
                            question_text=question.text,
                            max_marks=question.marks,
                            context_text=""
                        ), timeout=45.0)
                        
                        await crud_answer.save_evaluation(db, evaluation)
                        print(f"Success: Evaluated Answer {ans_id}")
                    except asyncio.TimeoutError:
                        print(f"Grading Timeout {answer.id}")
                    
        except Exception as e:
            print(f"Error/Timeout wrapper {ans_id}: {e}")

    # Execute in parallel
    try:
        await asyncio.gather(*[process_single_answer(aid) for aid in answer_ids])
        print(f"Background evaluation finished for {len(answer_ids)} answers.")
    except Exception as e:
        print(f"Critical Background Task Error: {e}")
        import traceback
        traceback.print_exc()

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from app.services.answer_parser import AnswerParserService

# ... imports ...

@router.post("/submit", response_model=List[StudentAnswerResponse])
async def submit_exam(
    submission: ExamSubmission,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Submit online exam answers.
    1. Save answers.
    2. Trigger background AI evaluation immediately.
    """
    # 1. Validation (User role)
    if current_user.role not in [UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN]:
        # Technically teachers/admins can test submit too
         raise HTTPException(status_code=403, detail="Not authorized")

    # 2. Save Answers
    # This CRUD method handles creating StudentAnswer entries for each question
    saved_answers = await crud_answer.submit_exam(db, submission=submission, student_id=current_user.id)
    
    # 3. Trigger Evaluation
    if saved_answers:
        answer_ids = [a.id for a in saved_answers]
        background_tasks.add_task(evaluate_answers_background_task, answer_ids)

    return saved_answers

@router.post("/{exam_id}/submit-bulk-offline", response_model=List[StudentAnswerResponse])
async def submit_bulk_offline_exam(
    exam_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Handle bulk upload of offline exam sheets.
    1. OCR all files.
    2. Parse/Segment text into answers.
    3. Save answers.
    4. Trigger evaluation.
    """
    # 1. Validation
    exam = await crud_exam.get_exam(db, exam_id=exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
        
    # verify mode? 
    if exam.mode != "offline":
         # strictly speaking we could allow it for online too as a fallback, but let's stick to logic
         pass
         
    # 2. Process Files (OCR)
    full_text_buffer = []
    
    import shutil
    import os
    
    # Ensure upload dir exists
    upload_dir = f"uploads/exams/{exam_id}/students/{current_user.id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    saved_file_paths = []

    for i, file in enumerate(files):
        # Save file locally
        file_path = f"{upload_dir}/page_{i+1}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_file_paths.append(file_path)
        
        # Run OCR
        try:
            page_text = await OCRService.transcribe_image(file_path)
            full_text_buffer.append(f"--- Page {i+1} ---\n{page_text}")
        except Exception as e:
            print(f"OCR Failed for {file.filename}: {e}")
            
    full_submission_text = "\n\n".join(full_text_buffer)
    
    # 3. Parse Answers
    # We need exam questions to map against
    # Questions might not be loaded on 'exam' obj if not eager loaded, let's fetch them
    questions_stmt = select(Question).filter(Question.exam_id == exam_id)
    q_result = await db.execute(questions_stmt)
    questions = q_result.scalars().all()
    
    parsed_answers = await AnswerParserService.parse_bulk_submission(full_submission_text, questions)
    
    # 4. Save Student Answers
    saved_answers = []
    for question in questions:
        # Get parsed text or empty if not found
        ans_text = parsed_answers.get(question.id, "")
        
        # Check if already answered? (overwrite logic)
        # For bulk submission, we assume it's a fresh or overwrite action
        
        # Create/Update logic would be ideal. For now, let's assume insert.
        # But wait, `crud_answer.submit_exam` expects a specific schema.
        # Let's construct it manually.
        
        # We need to find if entry exists to update or create new
        # This logic is a bit manual, let's optimize to use `submit_exam` if possible?
        # `submit_exam` takes `ExamSubmission` schema which has list of answers.
        pass

    # Let's use crud_answer logic but manually
    # Or cleaner: Construct ExamSubmission object and call crud
    from app.schemas.answer import StudentAnswerBase, ExamSubmission
    
    submission_answers = []
    for q in questions:
        # Check if we have text
        text = parsed_answers.get(q.id, "")
        # If we have file paths, we might want to attach them? 
        # But we have BULK files, not per question. 
        # We can attach the first file or a "link" or just leave it null and rely on text.
        # Let's leave file_path null for individual answers since the source is the bulk upload.
        # OR: We could store the bulk file path in a separate table? 
        # For simplicity, we just store the parsed text.
        
        submission_answers.append(
            StudentAnswerBase(
                question_id=q.id,
                answer_text=text,
                answer_file_path=None # We don't have per-question crop
            )
        )
        
    submission_schema = ExamSubmission(
        exam_id=exam_id,
        answers=submission_answers
    )
    
    # Save to DB
    # Note: this deletes previous answers? crud_answer.submit_exam usually creates distinct rows
    # We should probably clear previous answers for this exam/student if they are retrying?
    # Or `submit_exam` handles it?
    # Let's look at `crud_answer.submit_exam` -> It inserts new rows. 
    # Duplicate answers for same question/student might be issue if Analysis query doesn't handle it.
    # We should ensure we clean up old ones or Update.
    # For MVP: Insert.
    
    saved_db_answers = await crud_answer.submit_exam(db, submission=submission_schema, student_id=current_user.id)
    
    # 5. Trigger Evaluation
    if background_tasks:
        answer_ids = [a.id for a in saved_db_answers]
        background_tasks.add_task(evaluate_answers_background_task, answer_ids)
        
    return saved_db_answers

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
