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
        Process a single uploaded answer sheet:
        1. OCR -> Text
        2. Extract Student Name -> Find User
        3. Parse Answers
        4. Evaluate & Save
        """
        try:
            # 1. Read & OCR
            content = await file.read()
            # Basic check for image vs PDF (OCRService currently envisions images, 
            # if PDF assume first page or convert - simplicity for now: assume image)
            
            # TODO: Handle PDF conversion if needed, but for now assuming images (jpg/png)
            full_text = await OCRService.transcribe_bytes(content)
            
            # 2. Identify Student
            course_id = (await db.get(Exam, exam_id)).course_id
            student = await BulkGradingService._identify_student(db, full_text, course_id)
            
            if not student:
                return {
                    "filename": file.filename,
                    "status": "failed",
                    "error": "Could not identify student from the paper."
                }
                
            # 3. Fetch Exam Questions
            result = await db.execute(select(Question).filter(Question.exam_id == exam_id))
            questions = result.scalars().all()
            
            # 4. Parse Answers
            answers_map = await AnswerParserService.parse_bulk_submission(full_text, questions)
            
            # 5. Save & Evaluate Each Answer
            # In our schema, we don't have a single "Submission" parent object yet.
            # We save individual StudentAnswer records.
            # Ideally, we should check if answers already exist for this student/exam and clear them, similar to online submit.
            # For now, we'll append/overwrite.
            
            total_score = 0
            
            for q in questions:
                ans_text = answers_map.get(q.id, "")
                if not ans_text:
                    continue
                    
                # Store Answer
                answer_record = StudentAnswer(
                    exam_id=exam_id,
                    student_id=student.id,
                    question_id=q.id,
                    answer_text=ans_text,
                    submitted_at=logging.datetime.datetime.now()
                )
                db.add(answer_record)
                await db.commit()
                await db.refresh(answer_record)
                
                # Evaluate
                evaluation = await EvaluationService.evaluate_answer(
                    question_text=q.text,
                    model_answer=q.model_answer,
                    student_answer=ans_text,
                    max_marks=q.marks
                )
                
                # Save Evaluation
                eval_record = Evaluation(
                    answer_id=answer_record.id,
                    marks_awarded=evaluation["marks"],
                    feedback=evaluation["feedback"],
                    confidence_score=evaluation.get("confidence", 0.8)
                )
                db.add(eval_record)
                total_score += evaluation["marks"]
            
            await db.commit()
            
            return {
                "filename": file.filename,
                "status": "success",
                "student": student.full_name,
                "score": total_score
            }

        except Exception as e:
            logger.error(f"Bulk processing error: {e}")
            return {
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            }

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
