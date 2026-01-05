"""
Plagiarism Detection Service

Purpose:
    Identifies potential academic dishonesty by comparing student answers against each other.
    It specifically targets 'subjective' questions where unique written responses are expected.

Key Assumptions:
    - Only compares answers within the same Exam ID.
    - Only checks answers with length > 10 chars to avoid false positives on short phrases.
    - Uses a text similarity threshold (default 40%) to flag suspicious pairs.

Constraints:
    - This is an O(N^2) operation per question, where N is the number of students. 
    - For extremely large classes (>1000), this might need optimization (e.g., locality sensitive hashing).
"""
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
        Calculates the similarity ratio between two text strings.

        Inputs:
            text1 (str): First text content.
            text2 (str): Second text content.

        Outputs:
            float: A value between 0.0 (no match) and 1.0 (perfect match).

        Edge Cases:
            - Returns 0.0 if either text is empty or None.
        """
        """
        SequenceMatcher ratio for text similarity.
        Returns float between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        # Basic normalization using lower() to ensure case-insensitivity
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    @staticmethod
    async def analyze_exam(db: AsyncSession, exam_id: int, threshold: float = 0.40) -> List[Dict[str, Any]]:
        """
        Analyzes an entire exam to detect groups of students with similar answers.

        Inputs:
            db (AsyncSession): Database session.
            exam_id (int): The ID of the exam to checking.
            threshold (float): Similarity percentage (0.0 to 1.0) required to flag a pair. Default 0.40.

        Outputs:
            List[Dict]: A list of 'alerts'. Each alert represents a group of students who copied 
                        for a specific question.

        Side Effects:
            - Performs read-only queries to the database.
            - Does not modify any records.
        """
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
        stmt_a = select(StudentAnswer, User).join(User, StudentAnswer.student_id == User.id).filter(StudentAnswer.question_id.in_(question_ids))
        answers_res = await db.execute(stmt_a)
        results = answers_res.all()
        
        # Organize answers by Question ID to process one question at a time
        answers_by_q = {}
        for ans, student in results:
            # Skip very short answers as they are likely generic (e.g. "Yes", "I agree")
            if not ans.answer_text or len(ans.answer_text.strip()) < 10:
                continue 
                
            if ans.question_id not in answers_by_q:
                answers_by_q[ans.question_id] = []
            answers_by_q[ans.question_id].append({
                "id": ans.id,
                "text": ans.answer_text,
                "student_id": student.id,
                "student_name": student.full_name or student.email
            })
            
        alerts = []
        
        # 3. Group Students by Similarity (Connected Components)
        for q in questions:
            answers = answers_by_q.get(q.id, [])
            n = len(answers)
            if n < 2:
                continue
                
            # Build Graph: Nodes = indices 0..n-1, Edges = similarity >= threshold
            # We use an adjacency list to represent the graph of students who copied from each other.
            adj = {i: [] for i in range(n)}
            all_scores = {} # (i, j) -> score

            for i in range(n):
                for j in range(i + 1, n):
                    a1 = answers[i]
                    a2 = answers[j]
                    
                    if a1["student_id"] == a2["student_id"]:
                        continue
                        
                    score = PlagiarismService.calculate_similarity(a1["text"], a2["text"])
                    if score >= threshold:
                        # If similarity exceeds threshold, we consider them connected (an edge exists)
                        adj[i].append(j)
                        adj[j].append(i)
                        all_scores[tuple(sorted((i, j)))] = score

            # Find Connected Components (DFS/BFS)
            # A component represents a cluster of students where everyone is connected directly or indirectly
            visited = set()
            for i in range(n):
                if i not in visited:
                    component = []
                    stack = [i]
                    visited.add(i)
                    while stack:
                        u = stack.pop()
                        component.append(u)
                        for v in adj[u]:
                            if v not in visited:
                                visited.add(v)
                                stack.append(v)
                    
                    if len(component) > 1:
                        # Process Component (Group of potential cheaters)
                        involved_students = []
                        component_scores = []
                        
                        # Collect scores between members of the component
                        # (Only captured edges in all_scores)
                        for idx_a in range(len(component)):
                            for idx_b in range(idx_a + 1, len(component)):
                                u, v = component[idx_a], component[idx_b]
                                s = all_scores.get(tuple(sorted((u, v))))
                                if s is not None:
                                    component_scores.append(s)

                        max_score = max(component_scores) if component_scores else 0.0
                        
                        for idx in component:
                            involved_students.append({
                                "name": answers[idx]["student_name"],
                                "snippet": answers[idx]["text"][:100] + "..." if len(answers[idx]["text"]) > 100 else answers[idx]["text"],
                            })
                            
                        # Calculate logical question number (1-based index from sorted list)
                        q_num = questions.index(q) + 1
                        
                        alerts.append({
                            "question_id": q.id,
                            "question_number": q_num,
                            "question_text": q.text,
                            "question_marks": q.marks,
                            "students": involved_students,
                            "similarity_score": round(max_score * 100, 1),
                            "group_size": len(component)
                        })
                        
        # Sort by score descending to show worst offenders first
        alerts.sort(key=lambda x: x["similarity_score"], reverse=True)
        return alerts
