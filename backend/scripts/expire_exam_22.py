"""
Force Expire Exam 22

Purpose:
    Specific utility to mark Exam ID 22 as expired (ended yesterday).
    Used for testing the "Missed Exam" status logic on the frontend.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy.future import select

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.exam import Exam

async def expire_exam_22():
    """
    Updates Exam 22 start/end times to the past.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Exam).filter(Exam.id == 22))
        exam = result.scalars().first()
        
        if not exam:
            print("Exam 22 not found.")
            return

        print(f"Updating Exam {exam.id} ({exam.title})...")
        
        # Set to ended yesterday
        now = datetime.now()
        exam.start_time = now - timedelta(days=2)
        exam.end_time = now - timedelta(days=1)
        
        await session.commit()
        print(f"Updated: Start={exam.start_time}, End={exam.end_time}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(expire_exam_22())
