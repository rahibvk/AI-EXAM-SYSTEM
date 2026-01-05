"""
Exam & Question Schemas

Purpose:
    Defines the structure for Exam creation (via API or AI) and retrieval.
    Includes nested models for creating Questions along with the Exam.
"""
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
    """Payload for creating an exam, optionally with initial questions."""
    questions: List[QuestionCreate] = []

class ExamSummary(ExamBase):
    """Simplified Exam view (no questions)."""
    id: int
    
    class Config:
        from_attributes = True

class ExamResponse(ExamBase):
    """Full Exam view including list of questions."""
    id: int
    questions: List[QuestionResponse] = []
    
    class Config:
        from_attributes = True
