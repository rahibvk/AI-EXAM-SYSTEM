from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from app.models.base import Base

class StudentAnswer(Base):
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exam.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False)
    
    answer_text = Column(Text) # For typed answers
    answer_file_path = Column(String) # For handwritten uploads
    
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    exam = relationship("Exam")
    student = relationship("User")
    question = relationship("Question")

class Evaluation(Base):
    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("studentanswer.id"), unique=True, nullable=False)
    
    marks_awarded = Column(Float, nullable=False)
    feedback = Column(Text)
    ai_explanation = Column(Text)
    confidence_score = Column(Float) # 0.0 to 1.0
    
    # QA / Manual Review Fields
    review_requested = Column(Boolean, default=False)
    student_comment = Column(Text, nullable=True)
    teacher_comment = Column(Text, nullable=True)
    
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    
    answer = relationship("StudentAnswer", backref=backref("evaluation", uselist=False))
