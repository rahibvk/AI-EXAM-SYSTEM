"""
Course CRUD Operations

Purpose:
    Handles creation and retrieval of Courses and Course Materials.

Special Logic:
    - **Physical File Deletion**: When deleting a CourseMaterial, also removes the file from disk (see `delete_course_material`).
    - **RAG Cleanup**: Explicitly deletes associated `CourseMaterialChunk` rows before deleting the material to handle CASCADE issues gracefully.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.course import Course, CourseMaterial
from app.schemas.course import CourseCreate, CourseUpdate

async def create_course(db: AsyncSession, course: CourseCreate, teacher_id: int) -> Course:
    """Creates a new course and links it to the teacher."""
    db_course = Course(**course.dict(), teacher_id=teacher_id)
    db.add(db_course)
    await db.commit()
    await db.refresh(db_course)
    
    # Re-fetch with eager loading to prevent MissingGreenlet error during serialization
    # Pydantic will access .materials, so we must ensure it's loaded asynchronously
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.materials))
        .filter(Course.id == db_course.id)
    )
    return result.scalars().first()

async def get_courses(db: AsyncSession, skip: int = 0, limit: int = 100, student_id: Optional[int] = None) -> List[Course]:
    """
    Retrieves a list of courses.
    Optional: Filter by Student ID (fetching only enrolled courses).
    """
    stmt = select(Course).options(selectinload(Course.materials))
    
    if student_id:
        # Filter by enrollment
        from app.models.course import student_courses
        stmt = stmt.join(student_courses, student_courses.c.course_id == Course.id).filter(student_courses.c.student_id == student_id)
        
    result = await db.execute(stmt.offset(skip).limit(limit))
    return result.scalars().all()

async def get_course(db: AsyncSession, course_id: int) -> Optional[Course]:
    result = await db.execute(select(Course).options(selectinload(Course.materials)).filter(Course.id == course_id))
    return result.scalars().first()

async def get_course_by_code(db: AsyncSession, code: str) -> Optional[Course]:
    result = await db.execute(select(Course).filter(Course.code == code))
    return result.scalars().first()

async def get_courses_by_teacher(db: AsyncSession, teacher_id: int) -> List[Course]:
    result = await db.execute(select(Course).options(selectinload(Course.materials)).filter(Course.teacher_id == teacher_id))
    return result.scalars().all()

async def add_course_material(
    db: AsyncSession, 
    course_id: int, 
    title: str, 
    file_path: str,
    file_type: str,
    summary: str,
    # embedding: list[float]
) -> CourseMaterial:
    """Records a file upload in the database."""
    db_material = CourseMaterial(
        course_id=course_id,
        title=title,
        file_path=file_path,
        file_type=file_type,
        content_summary=summary,
        # embedding=embedding
    )
    db.add(db_material)
    await db.commit()
    await db.refresh(db_material)
    return db_material

async def update_course(db: AsyncSession, course_id: int, course_in: CourseUpdate) -> Optional[Course]:
    db_course = await get_course(db, course_id)
    if not db_course:
        return None
    
    update_data = course_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_course, field, value)
        
    db.add(db_course)
    await db.commit()
    await db.refresh(db_course)
    return db_course

async def delete_course(db: AsyncSession, course_id: int) -> Optional[Course]:
    db_course = await get_course(db, course_id)
    if not db_course:
        return None
        
    await db.delete(db_course)
    await db.commit()
    return db_course

async def get_course_material(db: AsyncSession, material_id: int) -> Optional[CourseMaterial]:
    result = await db.execute(select(CourseMaterial).filter(CourseMaterial.id == material_id))
    return result.scalars().first()

async def delete_course_material(db: AsyncSession, material_id: int) -> Optional[CourseMaterial]:
    """
    Deleting a material involves thorough cleanup:
    1. Disk cleanup (removing the physical file).
    2. RAG cleanup (removing related vector chunks).
    3. DB Record removal.
    """
    db_material = await get_course_material(db, material_id)
    if not db_material:
        return None
        
    # Delete physical file
    import os
    if db_material.file_path and os.path.exists(db_material.file_path):
        try:
            os.remove(db_material.file_path)
            print(f"Deleted file: {db_material.file_path}")
        except Exception as e:
            print(f"Error deleting file {db_material.file_path}: {e}")

    # Explicitly delete associated chunks (RAG) to prevent Foreign Key errors
    # Use nested transaction (SAVEPOINT) so if this fails (e.g. table missing), it doesn't abort the main transaction
    try:
        from app.models.course import CourseMaterialChunk
        from sqlalchemy import delete
        
        # Check if table exists/query safely using savepoint
        async with db.begin_nested():
            stmt = delete(CourseMaterialChunk).where(CourseMaterialChunk.material_id == material_id)
            await db.execute(stmt)
            
    except Exception as e:
        print(f"Warning: Could not delete chunks (Safe to ignore if RAG not initialized): {e}")

    # Use Core SQL delete for the material itself to bypass ORM 'delete-orphan' cascade
    # (which would otherwise try to SELECT from the missing chunk table and crash)
    from app.models.course import CourseMaterial
    stmt_material = delete(CourseMaterial).where(CourseMaterial.id == material_id)
    await db.execute(stmt_material)
    
    await db.commit()
    return db_material
