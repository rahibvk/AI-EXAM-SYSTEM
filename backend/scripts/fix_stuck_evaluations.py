"""
Evaluation Recovery Script

Purpose:
    Identifies and fixes "stuck" evaluations (Student Answers with no corresponding Evaluation).
    1. Scans for answers missing an evaluation.
    2. RETRIES OCR if text is missing.
    3. RETRIES AI Grading.
    
    This is critical for recovering from background task failures (e.g. server restart during grading).
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add parent dir to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env vars
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from app.db.session import AsyncSessionLocal
from app.models.answer import StudentAnswer, Evaluation
from app.models.exam import Question
from app.services.evaluation_service import EvaluationService
from app.services.ocr_service import OCRService
from app.crud import crud_answer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def fix_stuck_evaluations():
    """
    Main recovery loop.
    Scanning -> OCR -> AI Grading -> Save.
    """
    print("Scanning for stuck evaluations...")
    async with AsyncSessionLocal() as db:
        # Find answers with NO evaluation using LEFT JOIN
        stmt = select(StudentAnswer).outerjoin(Evaluation).where(Evaluation.id == None)
        
        # We need to load question to grade it
        stmt = stmt.options(selectinload(StudentAnswer.question))
        
        result = await db.execute(stmt)
        pending_answers = result.scalars().all()
        
        print(f"Found {len(pending_answers)} pending answers.")
        
        if not pending_answers:
            return

        for answer in pending_answers:
            print(f"Reprocessing Answer ID {answer.id}...")
            try:
                question = await db.get(Question, answer.question_id)
                if not question or not question.model_answer:
                    print(f"Skipping {answer.id}: No question/model answer")
                    continue
                
                # 1. OCR if needed
                if not answer.answer_text and answer.answer_file_path:
                    try:
                        print(f" - Running OCR...")
                        import os
                        # Fix path if needed. Assuming relative to backend root or absolute
                        # If file path stored as 'uploads/...', ensure we look there.
                        # Docker/Local path issue might exist.
                        if os.path.exists(answer.answer_file_path):
                            text = await OCRService.transcribe_image(answer.answer_file_path)
                            answer.answer_text = text
                            db.add(answer)
                            await db.commit()
                        else:
                             print(f" - File not found: {answer.answer_file_path}")
                    except Exception as e:
                        print(f" - OCR Failed: {e}")

                # 2. Evaluate
                print(" - Running AI Evaluation...")
                evaluation = await EvaluationService.evaluate_answer(
                    answer=answer,
                    model_answer=question.model_answer,
                    question_text=question.text,
                    max_marks=question.marks
                )
                
                await crud_answer.save_evaluation(db, evaluation)
                print(" - Success!")
                
            except Exception as e:
                print(f"Failed to process {answer.id}: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(fix_stuck_evaluations())
