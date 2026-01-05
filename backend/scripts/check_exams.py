"""
Exam Lister Script

Purpose:
    Connects to the database and prints a list of all exams.
    Used to quickly verify database content without using the API or frontend.
"""
import asyncio
import os
import sys
from sqlalchemy.future import select

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.exam import Exam

async def check_exams():
    """
    Fetches and prints ID, Title, Start Time, and End Time for all exams.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Exam))
        exams = result.scalars().all()
        
        print(f"Found {len(exams)} exams:")
        for exam in exams:
            print(f"ID: {exam.id}, Title: {exam.title}, Start: {exam.start_time}, End: {exam.end_time}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_exams())
