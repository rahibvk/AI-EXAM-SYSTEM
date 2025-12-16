from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.exam import QuestionType

class QuestionBase(BaseModel):
    text: str
    question_type: QuestionType = QuestionType.SUBJECTIVE
    marks: float
    model_answer: Optional[str] = None

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: int
    exam_id: int
    
    class Config:
        from_attributes = True

class ExamBase(BaseModel):
    title: str
    description: Optional[str] = None
    course_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    mode: Optional[str] = "online"
    total_marks: Optional[float] = None
    passing_marks: Optional[float] = None

class ExamCreate(ExamBase):
    questions: List[QuestionCreate] = []

class ExamSummary(ExamBase):
    id: int
    
    class Config:
        from_attributes = True

class ExamResponse(ExamBase):
    id: int
    questions: List[QuestionResponse] = []
    
    class Config:
        from_attributes = True
