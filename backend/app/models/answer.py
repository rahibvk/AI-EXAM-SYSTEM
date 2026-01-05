"""
Submission & Evaluation Models

Purpose:
    Stores the actual student work and the subsequent grading result.

Key Logic:
    - **One-to-One**: A `StudentAnswer` has exactly one `Evaluation`.
    - **Review System**: The `Evaluation` table contains flags (`review_requested`) and comments 
      to support the human review workflow.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from app.models.base import Base

class StudentAnswer(Base):
    """
    Stores a student's response to a single question.
    Can be typed text or a reference to a file path (for bulk upload).
    """
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exam.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False)
    
    answer_text = Column(Text) # For typed answers, or parsed text from OCR
    answer_file_path = Column(String) # For handwritten uploads (optional reference)
    
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    exam = relationship("Exam")
    student = relationship("User")
    question = relationship("Question")

class Evaluation(Base):
    """
    Stores the Grading Result for a specific answer.
    Populated by the AI (`evaluation_service.py`) and potentially modified by the teacher.
    """
    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("studentanswer.id"), unique=True, nullable=False)
    
    marks_awarded = Column(Float, nullable=False)
    feedback = Column(Text)
    ai_explanation = Column(Text)
    confidence_score = Column(Float) # 0.0 to 1.0
    
    # QA / Manual Review Fields
    review_requested = Column(Boolean, default=False)
    student_comment = Column(Text, nullable=True) # If student contests the grade
    teacher_comment = Column(Text, nullable=True) # Teacher's final ruling
    
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    
    answer = relationship("StudentAnswer", backref=backref("evaluation", uselist=False))
