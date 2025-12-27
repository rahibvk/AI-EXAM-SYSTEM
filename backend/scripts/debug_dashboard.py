import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.exam import Exam
from app.models.course import Course

async def debug_dashboard():
    async with AsyncSessionLocal() as session:
        # 1. Fetch All Courses (simulating frontend /courses)
        result = await session.execute(select(Course))
        courses = result.scalars().all()
        print(f"Found {len(courses)} courses.")

        now = datetime.now()
        print(f"Server Time: {now}")

        for course in courses:
            print(f"--- Course: {course.title} (ID: {course.id}) ---")
            
            # 2. Fetch Exams for Course (simulating /exams/course/{id})
            result = await session.execute(
                select(Exam).filter(Exam.course_id == course.id)
            )
            exams = result.scalars().all()
            print(f"    Found {len(exams)} exams.")

            for exam in exams:
                status = "UNKNOWN"
                if not exam.start_time or not exam.end_time:
                     status = "ACTIVE (No Dates)"
                else:
                    start = exam.start_time
                    end = exam.end_time
                    
                    if now > end:
                        status = "MISSED (Expired)"
                    elif now < start:
                        status = "UPCOMING"
                    else:
                        status = "ACTIVE"
                
                print(f"    - Exam: {exam.title} (ID: {exam.id}) | {start} -> {end} | Status: {status}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_dashboard())
