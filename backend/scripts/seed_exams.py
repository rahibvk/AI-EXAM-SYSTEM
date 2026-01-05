"""
Exam Seeder

Purpose:
    Creates two sample exams for the FIRST course found in the DB:
    1. 'Fresh Active Exam': Online, 1 hour duration, currently active.
    2. 'Fresh Upcoming Exam': Online, 2 hours duration, starting tomorrow.
    
    Used to quickly populate a course with testable content.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy.future import select

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.exam import Exam, ExamMode
from app.models.course import Course

async def seed_exams():
    """
    Seeds Active and Upcoming exams.
    """
    async with AsyncSessionLocal() as session:
        # Get the first course (assuming at least one exists)
        result = await session.execute(select(Course))
        course = result.scalars().first()
        
        if not course:
            print("No courses found. Cannot create exams.")
            return

        print(f"Adding exams to Course: {course.title} (ID: {course.id})")
        
        now = datetime.now()
        
        # 1. Create an Active Exam (Started 30 mins ago, Ends 30 mins from now)
        active_exam = Exam(
            course_id=course.id,
            title="Fresh Active Exam",
            description="This exam is currently active.",
            start_time=now - timedelta(minutes=30),
            end_time=now + timedelta(minutes=30),
            duration_minutes=60,
            mode=ExamMode.ONLINE,
            total_marks=50,
            passing_marks=20
        )
        
        # 2. Create an Upcoming Exam (Starts tomorrow)
        upcoming_exam = Exam(
            course_id=course.id,
            title="Fresh Upcoming Exam",
            description="This exam starts tomorrow.",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2),
            duration_minutes=120,
            mode=ExamMode.ONLINE,
            total_marks=100,
            passing_marks=40
        )
        
        session.add(active_exam)
        session.add(upcoming_exam)
        await session.commit()
        
        print("Successfully added 'Fresh Active Exam' and 'Fresh Upcoming Exam'.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_exams())
