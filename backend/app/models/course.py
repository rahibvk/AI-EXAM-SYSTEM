from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
# from pgvector.sqlalchemy import Vector
from app.models.base import Base

class Course(Base):
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    teacher_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    teacher = relationship("User", backref="courses")

class CourseMaterial(Base):
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String) # pdf, ppt, doc, etc.
    content_summary = Column(Text)
    
    # Embedding for RAG (1536 dimensions for OpenAI usually, adjust as needed)
    # embedding = Column(Vector(1536))
    
    course = relationship("Course", backref="materials")
