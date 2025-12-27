from typing import List, Optional
from pydantic import BaseModel

class CourseMaterialBase(BaseModel):
    title: str
    content_summary: Optional[str] = None

class CourseMaterialCreate(CourseMaterialBase):
    pass

class CourseMaterialResponse(CourseMaterialBase):
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
    id: int
    teacher_id: int
    materials: List[CourseMaterialResponse] = []
    
    class Config:
        from_attributes = True
