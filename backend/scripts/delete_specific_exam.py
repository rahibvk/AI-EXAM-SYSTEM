"""
Specific Exam Deletion Tool

Purpose:
    Deletes a single exam by ID, along with all associated Questions.
    Cascades deletion manually since we might not have DB-level cascade configured for everything.
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.exam import Exam, Question
from sqlalchemy import select, delete

async def delete_exam(exam_id):
    """
    Deletes Exam and its Questions.
    Args:
        exam_id (int): DB ID of the exam.
    """
    async with AsyncSessionLocal() as db:
        # Check if exists
        query = select(Exam).where(Exam.id == exam_id)
        result = await db.execute(query)
        exam = result.scalar_one_or_none()
        
        if exam:
            print(f"found Exam ID {exam.id}: {exam.title}")
            
            # Delete associated questions first
            print("Deleting associated questions...")
            delete_q = delete(Question).where(Question.exam_id == exam_id)
            await db.execute(delete_q)
            
            print(f"Deleting Exam...")
            await db.delete(exam)
            await db.commit()
            print("Deletion successful.")
        else:
            print(f"Exam ID {exam_id} not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_specific_exam.py <exam_id>")
    else:
        asyncio.run(delete_exam(int(sys.argv[1])))
