"""
Course & Material Schemas

Purpose:
    Defines the API contract for creating and reading Courses and Materials.
    Used for request validation and response formatting.
"""
from typing import List, Optional
from pydantic import BaseModel

class CourseMaterialBase(BaseModel):
    title: str
    content_summary: Optional[str] = None

class CourseMaterialCreate(CourseMaterialBase):
    pass

class CourseMaterialResponse(CourseMaterialBase):
    """Public CourseMaterial definition."""
    id: int
    file_path: str
    file_type: Optional[str] = None
    
    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    title: str
    code: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None

class CourseResponse(CourseBase):
    """Public Course definition including list of materials."""
    id: int
    teacher_id: int
    materials: List[CourseMaterialResponse] = []
    
    class Config:
        from_attributes = True

class StudentEnrollmentRequest(BaseModel):
    """Payload for manually enrolling a student to a course."""
    email: str
