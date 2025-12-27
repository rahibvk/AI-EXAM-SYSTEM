import asyncio
import os
import sys
from sqlalchemy.future import select

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.exam import Exam

async def delete_test_exams():
    async with AsyncSessionLocal() as session:
        # Find exams with specific titles
        titles_to_delete = [
            "Fresh Active Exam",
            "Fresh Upcoming Exam",
            "Long Duration Active Exam"
        ]
        
        result = await session.execute(
            select(Exam).filter(Exam.title.in_(titles_to_delete))
        )
        exams = result.scalars().all()
        
        if not exams:
            print("No test exams found to delete.")
            return

        print(f"Found {len(exams)} test exams. Deleting...")
        for exam in exams:
            print(f"Deleting: {exam.title} (ID: {exam.id})")
            await session.delete(exam)
            
        await session.commit()
        print("Deletion complete.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(delete_test_exams())
