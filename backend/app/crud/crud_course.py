from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.course import Course, CourseMaterial
from app.schemas.course import CourseCreate

async def create_course(db: AsyncSession, course: CourseCreate, teacher_id: int) -> Course:
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

async def get_courses(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Course]:
    result = await db.execute(select(Course).options(selectinload(Course.materials)).offset(skip).limit(limit))
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
