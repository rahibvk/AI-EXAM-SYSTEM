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

async def seed_long_exam():
    async with AsyncSessionLocal() as session:
        # Get the first course
        result = await session.execute(select(Course))
        course = result.scalars().first()
        
        if not course:
            print("No courses found.")
            return

        now = datetime.now()
        print(f"Current Server Time: {now}")
        
        # Create an Always Active Exam (Started yesterday, Ends next week)
        long_exam = Exam(
            course_id=course.id,
            title="Long Duration Active Exam",
            description="This exam is active for a whole week.",
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=7),
            duration_minutes=60,
            mode=ExamMode.ONLINE,
            total_marks=100,
            passing_marks=40
        )
        
        session.add(long_exam)
        await session.commit()
        
        print(f"Created '{long_exam.title}':")
        print(f"Start: {long_exam.start_time}")
        print(f"End:   {long_exam.end_time}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_long_exam())
