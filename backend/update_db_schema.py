import asyncio
import sys
import os

# Add backend to path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import engine
from app.models.base import Base
# Import all models to ensure they are registered in metadata
from app.models.user import User
from app.models.course import Course, student_courses
from app.models.exam import Exam, Question
from app.models.answer import StudentAnswer, Evaluation

async def create_tables():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_tables())
