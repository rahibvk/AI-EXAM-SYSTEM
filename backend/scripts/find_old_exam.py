import asyncio
import sys
import os

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.exam import Exam
from sqlalchemy import select

async def find_exam():
    async with AsyncSessionLocal() as db:
        query = select(Exam).where(Exam.title.ilike("%12/27/2025%"))
        result = await db.execute(query)
        exams = result.scalars().all()
        
        print(f"Found {len(exams)} exams.")
        for e in exams:
            print(f"ID: {e.id}, Title: {e.title}, Start: {e.start_time}, End: {e.end_time}")

if __name__ == "__main__":
    asyncio.run(find_exam())
