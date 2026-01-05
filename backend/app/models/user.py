"""
User Model

Purpose:
    Represents the system users (Students, Teachers, Admins).
    Stores authentication details and role information.
"""
from sqlalchemy import Column, Integer, String, Enum
from app.models.base import Base
import enum

class UserRole(str, enum.Enum):
    """Enumeration of available user roles."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class User(Base):
    """
    User Table.
    
    Attributes:
        id (int): Primary Key.
        full_name (str): User's real name.
        email (str): Unique login email.
        hashed_password (str): Bcrypt hash of password.
        role (str): Role string (defaults to 'student').
    """
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default=UserRole.STUDENT)
