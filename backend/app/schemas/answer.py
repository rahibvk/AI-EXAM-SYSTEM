from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class StudentAnswerBase(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    answer_file_path: Optional[str] = None 

# Initial submission payload (list of answers)
class ExamSubmission(BaseModel):
    exam_id: int
    answers: list[StudentAnswerBase]

class EvaluationResponse(BaseModel):
    marks_awarded: float
    feedback: Optional[str] = None
    ai_explanation: Optional[str] = None
    confidence_score: float
    review_requested: Optional[bool] = False
    student_comment: Optional[str] = None
    teacher_comment: Optional[str] = None

class ReviewRequest(BaseModel):
    student_comment: str

class ManualGradeRequest(BaseModel):
    marks: float
    feedback: str

from app.schemas.user import UserResponse
from app.schemas.exam import ExamSummary, QuestionResponse

class StudentAnswerResponse(StudentAnswerBase):
    id: int
    student_id: int
    exam_id: int
    submitted_at: datetime
    evaluation: Optional[EvaluationResponse] = None
    student: Optional[UserResponse] = None
    exam: Optional[ExamSummary] = None
    question: Optional[QuestionResponse] = None

    class Config:
        from_attributes = True
