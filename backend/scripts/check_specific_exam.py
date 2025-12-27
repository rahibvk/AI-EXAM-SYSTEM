import asyncio
import os
import sys
from sqlalchemy.future import select

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.exam import Exam

async def check_specific_exam():
    async with AsyncSessionLocal() as session:
        # Check for 'testextamnot'
        result = await session.execute(
            select(Exam).filter(Exam.title.ilike("%testextamnot%"))
        )
        exams = result.scalars().all()
        
        if not exams:
            print("No exam found with title similar to 'testextamnot'.")
            return

        for exam in exams:
            print(f"ID: {exam.id}")
            print(f"Title: {exam.title}")
            print(f"Start: {exam.start_time}")
            print(f"End:   {exam.end_time}")
            print(f"Total Marks: {exam.total_marks}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_specific_exam())
