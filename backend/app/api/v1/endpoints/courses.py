from typing import List, Any
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_course
from app.schemas.course import CourseCreate, CourseResponse, CourseMaterialResponse, CourseUpdate
from app.schemas.user import UserResponse
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.course import Course, student_courses
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
    student_id = None
    if current_user.role == UserRole.STUDENT:
        student_id = current_user.id
        
    courses = await crud_course.get_courses(db, skip=skip, limit=limit, student_id=student_id)
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

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_in: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update course details.
    """
    course = await crud_course.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    course = await crud_course.update_course(db, course_id=course_id, course_in=course_in)
    return course

@router.delete("/{course_id}", response_model=CourseResponse)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a course.
    """
    course = await crud_course.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    course = await crud_course.delete_course(db, course_id=course_id)
    return course

@router.post("/{course_id}/materials", response_model=CourseMaterialResponse)
async def upload_material(
    course_id: int,
    background_tasks: BackgroundTasks,
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

    # 4. RAG: Queue Background Task (Non-blocking)
    background_tasks.add_task(process_rag_ingestion, material.id, text_content)

    return material

# --- Background Worker ---
async def process_rag_ingestion(material_id: int, text_content: str):
    """
    Background Task: Chunk text, generate embeddings, and save to DB.
    Uses its own DB session to avoid detached instance errors.
    """
    from app.db.session import AsyncSessionLocal
    from app.models.course import CourseMaterialChunk
    from app.services.embeddings import generate_embeddings
    
    print(f"RAG Background: Starting ingestion for Material {material_id}...")
    
    async with AsyncSessionLocal() as db:
        try:
            chunks = DocumentProcessor.chunk_text(text_content)
            if not chunks:
                return

            # Generate embeddings in batch
            embeddings_list = await generate_embeddings(chunks)
            
            chunk_objs = []
            for text, vector in zip(chunks, embeddings_list):
                chunk_objs.append(CourseMaterialChunk(
                    material_id=material_id, 
                    chunk_text=text,
                    embedding=vector
                ))
            
            if chunk_objs:
                db.add_all(chunk_objs)
                await db.commit()
                print(f"RAG Background: Successfully saved {len(chunk_objs)} chunks for Material {material_id}.")
                
        except Exception as e:
            print(f"RAG Background Error: Failed to process Material {material_id}: {e}")
            await db.rollback()

@router.delete("/{course_id}/materials/{material_id}", response_model=CourseMaterialResponse)
async def delete_material(
    course_id: int,
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a course material.
    """
    course = await crud_course.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    material = await crud_course.get_course_material(db, material_id=material_id)
    if not material or material.course_id != course_id:
        raise HTTPException(status_code=404, detail="Material not found")

    material = await crud_course.delete_course_material(db, material_id=material_id)
    return material

from app.schemas.course import StudentEnrollmentRequest

@router.post("/{course_id}/students", response_model=UserResponse)
async def add_student_to_course(
    course_id: int,
    enrollment: StudentEnrollmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    print(f"DEBUG: Attempting to enroll email: {enrollment.email} to course {course_id}")
    
    course = await crud_course.get_course(db, course_id=course_id)
    if not course:
        print("DEBUG: Course not found")
        raise HTTPException(status_code=404, detail="Course not found")
        
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and course.teacher_id != current_user.id:
        print("DEBUG: Authorization failed")
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Find student by email
    from sqlalchemy.future import select
    result = await db.execute(select(User).filter(User.email == enrollment.email))
    student = result.scalar_one_or_none()
    
    if not student:
        print(f"DEBUG: Student not found for email {enrollment.email}")
        raise HTTPException(status_code=404, detail="Student with this email not found")
        
    if student.role != UserRole.STUDENT:
        print(f"DEBUG: User {student.email} is not a student")
        raise HTTPException(status_code=400, detail="User is not a student")
        
    # Check if already enrolled
    stmt = select(User).join(Course.students).filter(Course.id == course_id, User.id == student.id)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        print("DEBUG: Already enrolled")
        raise HTTPException(status_code=400, detail="Student is already enrolled")
    
    # Add relation via direct Insert (more stable with AsyncSession)
    print("DEBUG: Inserting into student_courses...")
    from app.models.course import student_courses
    from sqlalchemy import insert
    
    try:
        stmt = insert(student_courses).values(student_id=student.id, course_id=course_id)
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        print(f"DEBUG: Insert failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")
        
    print("DEBUG: Enrollment successful")
    return student

@router.delete("/{course_id}/students/{student_id}", response_model=Any)
async def remove_student_from_course(
    course_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Remove a student from the course.
    """
    course = await crud_course.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Direct delete from association table
    print(f"DEBUG: Removing student {student_id} from course {course_id}")
    from app.models.course import student_courses
    from sqlalchemy import delete
    
    try:
        stmt = delete(student_courses).where(
            student_courses.c.student_id == student_id,
            student_courses.c.course_id == course_id
        )
        result = await db.execute(stmt)
        await db.commit()
        
        if result.rowcount == 0:
             print("DEBUG: Student not found in course (rowcount 0)")
             raise HTTPException(status_code=404, detail="Student not found in this course")
             
    except Exception as e:
        print(f"DEBUG: Remove failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Removal failed: {str(e)}")
    
    print("DEBUG: Removal successful")
    return {"message": "Student removed successfully"}

@router.get("/{course_id}/students", response_model=List[UserResponse])
async def get_course_students(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all students enrolled in a specific course.
    """
    try:
        from app.models.course import student_courses
        from sqlalchemy.future import select
        
        # Verify course exists
        course = await crud_course.get_course(db, course_id=course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
            
        if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and course.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        # Select Users joined with student_courses
        stmt = (
            select(User)
            .join(student_courses, student_courses.c.student_id == User.id)
            .filter(student_courses.c.course_id == course_id)
        )
        
        result = await db.execute(stmt)
        students = result.scalars().all()
        return students
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"DEBUG: get_course_students failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch students: {str(e)}")
