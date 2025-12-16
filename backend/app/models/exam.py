from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class QuestionType(str, enum.Enum):
    SUBJECTIVE = "subjective"
    OBJECTIVE = "objective" # MCQ potential

class ExamMode(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"

class Exam(Base):
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)
    
    mode = Column(String, default=ExamMode.ONLINE) # "online" or "offline"
    
    total_marks = Column(Float)
    passing_marks = Column(Float)
    
    course = relationship("Course", backref="exams")

class Question(Base):
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exam.id"), nullable=False)
    text = Column(Text, nullable=False)
    question_type = Column(String, default=QuestionType.SUBJECTIVE)
    marks = Column(Float, nullable=False)
    
    # AI will use this for evaluation
    model_answer = Column(Text)
    
    exam = relationship("Exam", backref="questions")
