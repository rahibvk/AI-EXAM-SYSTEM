from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_exam, crud_course
from app.schemas.exam import ExamCreate, ExamResponse, QuestionCreate
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.exam_generator import ExamGeneratorService

router = APIRouter()

@router.get("/{exam_id}/plagiarism", response_model=Any)
async def check_plagiarism(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generate Plagiarism Report for an exam.
    Teacher/Admin only.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    from app.services.plagiarism_service import PlagiarismService
    report = await PlagiarismService.analyze_exam(db, exam_id)
    return report

@router.post("/", response_model=ExamResponse)
async def create_exam(
    *,
    db: AsyncSession = Depends(get_db),
    exam_in: ExamCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new exam with questions.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    
    # Verify course belongs to teacher (optional but good security)
    course = await crud_course.get_course(db, course_id=exam_in.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create exams for this course")

    # Fix Timezone Issue: Convert to naive UTC if aware
    import datetime
    if exam_in.start_time and exam_in.start_time.tzinfo:
        exam_in.start_time = exam_in.start_time.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    
    if exam_in.end_time and exam_in.end_time.tzinfo:
        exam_in.end_time = exam_in.end_time.astimezone(datetime.timezone.utc).replace(tzinfo=None)

    exam = await crud_exam.create_exam(db, exam=exam_in)
    return exam

@router.post("/generate", response_model=List[QuestionCreate])
async def generate_exam_questions(
    course_id: int = Body(...),
    # topic removed
    difficulty: str = Body("Medium"),
    num_questions: int = Body(5), # Total or fallback
    question_type: str = Body("subjective"), # Fallback
    subjective_count: int = Body(0),
    objective_count: int = Body(0),
    total_marks: float = Body(100), # Default 100
    material_ids: List[int] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generate questions using AI based on course materials.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    try:
        questions = await ExamGeneratorService.generate_questions(
            db=db,
            course_id=course_id,
            # topic removed
            difficulty=difficulty,
            num_questions=num_questions,
            question_type=question_type,
            subjective_count=subjective_count,
            objective_count=objective_count,
            total_marks=total_marks,
            material_ids=material_ids
        )
        return questions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{exam_id}", response_model=ExamResponse)
async def read_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get specific exam details.
    """
    exam = await crud_exam.get_exam(db, exam_id=exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
        
    # Security: Access Control for Students
    if current_user.role == UserRole.STUDENT:
        import datetime
        now = datetime.datetime.utcnow()
        
        # Check Start Time
        if exam.start_time and now < exam.start_time:
            # Calculate time remaining
            time_diff = exam.start_time - now
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            raise HTTPException(
                status_code=403, 
                detail=f"Exam has not started yet. Starts in {hours}h {minutes}m."
            )
            
        # Check End Time
        if exam.end_time and now > exam.end_time:
             raise HTTPException(
                status_code=403, 
                detail="Exam validity period has ended."
            )

    return exam

@router.get("/course/{course_id}", response_model=List[ExamResponse])
async def read_exams_by_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    List exams for a specific course.
    """
    exams = await crud_exam.get_exams_by_course(db, course_id=course_id)
    return exams
