from typing import List, Any
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_course
from app.schemas.course import CourseCreate, CourseResponse, CourseMaterialResponse
from app.schemas.user import UserResponse
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.document_processor import DocumentProcessor
from app.services.embeddings import generate_embedding

router = APIRouter()

@router.post("/", response_model=CourseResponse)
async def create_new_course(
    *,
    db: AsyncSession = Depends(get_db),
    course_in: CourseCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new course. Only Teachers and Admins can create courses.
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if course with same code exists
    course_exists = await crud_course.get_course_by_code(db, code=course_in.code)
    if course_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course with code '{course_in.code}' already exists.",
        )

    course = await crud_course.create_course(db=db, course=course_in, teacher_id=current_user.id)
    return course

@router.get("/", response_model=List[CourseResponse])
async def read_courses(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve courses.
    """
    courses = await crud_course.get_courses(db, skip=skip, limit=limit)
    return courses

@router.get("/my-courses", response_model=List[CourseResponse])
async def read_my_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve courses created by the current teacher.
    """
    print(f"DEBUG: User {current_user.email} Role: {current_user.role} (Type: {type(current_user.role)})")
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail=f"User is not a teacher. Role: {current_user.role}")
        
    courses = await crud_course.get_courses_by_teacher(db, teacher_id=current_user.id)
    return courses

@router.get("/{course_id}", response_model=CourseResponse)
async def read_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get course by ID.
    """
    course = await crud_course.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.post("/{course_id}/materials", response_model=CourseMaterialResponse)
async def upload_material(
    course_id: int,
    file: UploadFile = File(...),
    title: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload course material (PDF/Text). 
    Extracts text, generates summary and embeddings, and saves to DB.
    """
    course = await crud_course.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 1. Extract Text
    try:
        text_content = await DocumentProcessor.extract_text_from_file(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
    
    # 2. Generate Embedding (using first 8000 chars for now as summary/context)
    summary_text = text_content[:8000] 
    try:
        embedding = await generate_embedding(summary_text)
    except Exception as e:
        # Fallback if AI service fails (or no key)
        print(f"Embedding generation failed: {e}")
        embedding = [0.0] * 1536 # Empty vector

    # 3. Save to DB
    # TODO: Save file to disk/S3. For now using fake path logic.
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}" 
    with open(file_path, "wb") as f:
        f.write(await file.read())
        await file.seek(0) # Reset if needed, but we already read content for extraction

    material = await crud_course.add_course_material(
        db=db,
        course_id=course_id,
        title=title,
        file_path=file_path,
        file_type=file.content_type,
        summary=summary_text[:1000],
        # embedding=embedding
    )
    return material
