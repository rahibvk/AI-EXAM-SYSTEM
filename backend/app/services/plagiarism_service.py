from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.answer import StudentAnswer
from app.models.exam import Question
from app.models.user import User
import difflib

class PlagiarismService:
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        SequenceMatcher ratio for text similarity.
        Returns float between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        # Basic normalization could happen here
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    @staticmethod
    async def analyze_exam(db: AsyncSession, exam_id: int, threshold: float = 0.40) -> List[Dict[str, Any]]:
        """
        Analyzes all subjective answers for an exam and returns pairs with high similarity.
        """
        
        # 1. Fetch Subjective Questions
        stmt_q = select(Question).filter(Question.exam_id == exam_id, Question.question_type == 'subjective')
        questions_res = await db.execute(stmt_q)
        questions = questions_res.scalars().all()
        
        if not questions:
            return []
            
        question_ids = [q.id for q in questions]
        
        # 2. Fetch Answers for these questions
        # We need student info too, so let's join
        stmt_a = select(StudentAnswer, User).join(User, StudentAnswer.student_id == User.id).filter(StudentAnswer.question_id.in_(question_ids))
        answers_res = await db.execute(stmt_a)
        results = answers_res.all() # list of (StudentAnswer, User) tuples
        
        # Organize by Question ID
        answers_by_q = {}
        for ans, student in results:
            if not ans.answer_text or len(ans.answer_text.strip()) < 10:
                continue # Skip empty or very short answers
                
            if ans.question_id not in answers_by_q:
                answers_by_q[ans.question_id] = []
            answers_by_q[ans.question_id].append({
                "id": ans.id,
                "text": ans.answer_text,
                "student_id": student.id,
                "student_name": student.full_name or student.email
            })
            
        alerts = []
        
        # 3. Compare Pair-wise per Question
        for q in questions:
            answers = answers_by_q.get(q.id, [])
            if len(answers) < 2:
                continue
                
            # Naive O(N^2) comparison - acceptable for typical class sizes (<100)
            n = len(answers)
            for i in range(n):
                for j in range(i + 1, n):
                    a1 = answers[i]
                    a2 = answers[j]
                    
                    # Prevent Comparing same student if they submitted twice (unlikely but safe)
                    if a1["student_id"] == a2["student_id"]:
                        continue
                        
                    score = PlagiarismService.calculate_similarity(a1["text"], a2["text"])
                    
                    if score >= threshold:
                        alerts.append({
                            "question_id": q.id,
                            "question_text": q.text[:50] + "..." if len(q.text) > 50 else q.text,
                            "student_1": a1["student_name"],
                            "student_2": a2["student_name"],
                            "similarity_score": round(score * 100, 1),
                            "snippet_1": a1["text"][:100] + "..." if len(a1["text"]) > 100 else a1["text"],
                            "snippet_2": a2["text"][:100] + "..." if len(a2["text"]) > 100 else a2["text"]
                        })
                        
        # Sort by score descending
        alerts.sort(key=lambda x: x["similarity_score"], reverse=True)
        return alerts
