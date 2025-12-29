import logging
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.exam import Exam, Question
from app.models.answer import StudentAnswer, Evaluation
from app.services.ocr_service import OCRService
from app.services.answer_parser import AnswerParserService
from app.services.evaluation_service import EvaluationService
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from fastapi import UploadFile

logger = logging.getLogger(__name__)

class BulkGradingService:
    
    @staticmethod
    async def process_bulk_upload(
        db: AsyncSession, 
        exam_id: int, 
        file: UploadFile
    ) -> dict:
        """
        Phase 1: Analyze file
        1. OCR -> Text
        2. Identify Student
        3. Parse Answers
        Returns data for teacher confirmation.
        """
        try:
            # 1. Read Content
            content = await file.read()
            full_text = ""
            filename = file.filename.lower()
            
            if filename.endswith(".pdf"):
                import fitz # PyMuPDF
                with fitz.open(stream=content, filetype="pdf") as doc:
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        # Increase resolution (zoom x2) for better OCR
                        mat = fitz.Matrix(2, 2)
                        pix = page.get_pixmap(matrix=mat)
                        img_bytes = pix.tobytes("png")
                        page_text = await OCRService.transcribe_bytes(img_bytes)
                        full_text += f"\n--- Page {page_num+1} ---\n{page_text}"
            else:
                full_text = await OCRService.transcribe_bytes(content)
            
            # 2. Identify Student
            course_id = (await db.get(Exam, exam_id)).course_id
            student = await BulkGradingService._identify_student(db, full_text, course_id)
            
            # 3. Fetch Exam Questions
            result = await db.execute(select(Question).filter(Question.exam_id == exam_id))
            questions = result.scalars().all()
            
            # 4. Parse Answers
            answers_map = await AnswerParserService.parse_bulk_submission(full_text, questions)
            
            # DEBUG: Write logs to inspect what went wrong
            try:
                with open("debug_ocr.txt", "w", encoding="utf-8") as f:
                    f.write(full_text)
                import json
                with open("debug_parsed.json", "w", encoding="utf-8") as f:
                    json.dump(answers_map, f, indent=2)
                with open("debug_metadata.txt", "w", encoding="utf-8") as f:
                    f.write(f"Exam ID: {exam_id}\n")
                    f.write(f"Questions Found: {[q.id for q in questions]}\n")
            except Exception as e:
                print(f"Debug logging failed: {e}")
            
            return {
                "filename": file.filename,
                "status": "ready_for_review" if student else "action_required",
                "student": {
                    "id": student.id,
                    "name": student.full_name,
                    "email": student.email
                } if student else None,
                "extracted_data": {
                    "answers": answers_map
                }
            }

        except Exception as e:
            logger.error(f"Bulk processing error: {e}")
            return {
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            }

    @staticmethod
    async def confirm_grading(
        db: AsyncSession,
        exam_id: int,
        student_id: int,
        answers: dict
    ) -> dict:
        """
        Phase 2: Save & Evaluate (Parallelized)
        """
        try:
            import asyncio
            import datetime
            
            result = await db.execute(select(Question).filter(Question.exam_id == exam_id))
            questions = result.scalars().all()
            
            # 1. Prepare & Save Answers
            student_answers = []
            valid_pairs = [] # (Question, StudentAnswer)
            
            for q in questions:
                # Handle string/int key mismatch
                ans_text = answers.get(str(q.id)) or answers.get(q.id, "")
                if not ans_text:
                    continue
                    
                answer_record = StudentAnswer(
                    exam_id=exam_id,
                    student_id=student_id,
                    question_id=q.id,
                    answer_text=ans_text,
                    submitted_at=datetime.datetime.now()
                )
                student_answers.append(answer_record)
                valid_pairs.append((q, answer_record))

            if not student_answers:
                # Fetch student name just to be safe/consistent
                student = await db.get(User, student_id)
                return {
                    "status": "success", 
                    "score": 0, 
                    "student": student.full_name if student else "Unknown"
                }

            # Batch save answers to generate IDs
            db.add_all(student_answers)
            await db.commit()
            
            # Refresh to ensure IDs are available
            for a in student_answers:
                await db.refresh(a)

            # 2. Parallel Evaluation
            # EvaluationService.evaluate_answer(answer, model_answer, question_text, max_marks)
            tasks = []
            for q, ans_record in valid_pairs:
                tasks.append(
                    EvaluationService.evaluate_answer(
                        answer=ans_record,
                        model_answer=q.model_answer,
                        question_text=q.text,
                        max_marks=q.marks
                    )
                )
            
            # Run all LLM calls concurrently
            evaluations = await asyncio.gather(*tasks)
            
            # 3. Save Evaluations
            total_score = 0
            for ev in evaluations:
                db.add(ev)
                total_score += ev.marks_awarded
            
            await db.commit()
            
            # Fetch student name
            student = await db.get(User, student_id)
            return {
                "status": "success",
                "student": student.full_name if student else "Unknown",
                "score": total_score
            }
            
        except Exception as e:
            logger.error(f"Confirmation error: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    async def _identify_student(db: AsyncSession, text: str, course_id: int) -> Optional[User]:
        """
        Uses LLM to find the student name in the text, then fuzzy matches against DB students.
        """
        # Fetch all students in the course (via enrollment mechanism - assuming access to user list)
        # For MVP, let's fetch ALL users who are 'STUDENT'
        # In prod, filter by Course Enrollment
        from app.models.user import UserRole
        result = await db.execute(select(User).filter(User.role == UserRole.STUDENT))
        students = result.scalars().all()
        
        student_names = [f"{s.full_name} (ID: {s.email})" for s in students]
        names_list_str = "\n".join(student_names)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are an assistant identifying a student from their handwritten exam paper.
            
            1. Look for a Name, Roll Number, or Email at the top of the OCR text.
            2. Compare it against the provided List of Enrolled Students.
            3. Return the EXACT Email of the matching student from the list.
            4. If no clear match is found, return "NONE".
            """),
            ("user", """
            --- Enrolled Students ---
            {names_list}
            
            --- OCR Text Segment (Top 500 chars) ---
            {text_segment}
            
            --- Task ---
            Return the Email of the student.
            """)
        ])
        
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        chain = prompt | llm
        
        try:
            # Only send top 1000 chars to save tokens, usually name is at top
            response = await chain.ainvoke({
                "names_list": names_list_str,
                "text_segment": text[:1000]
            })
            
            match_email = response.content.strip()
            
            if match_email == "NONE":
                return None
                
            # Find the user object
            for s in students:
                if s.email.lower() == match_email.lower():
                    return s
                if s.email in match_email: # Fuzzy containment
                    return s
            
            return None
            
        except Exception:
            return None
