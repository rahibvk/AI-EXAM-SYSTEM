import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.models.answer import StudentAnswer, Evaluation

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.3) # Lower temp for grading consistency

class EvaluationService:
    @staticmethod
    async def evaluate_answer(
        answer: StudentAnswer,
        model_answer: str,
        question_text: str,
        max_marks: float,
        context_text: str = ""
    ) -> Evaluation:
        
        system_prompt = f"""
        You are an expert examiner. Your task is to evaluate a student's answer against a model answer for a given question.
        
        Question: {question_text}
        Max Marks: {max_marks}
        Model Answer: {model_answer}
        
        Course Material Context (Use for verification):
        {context_text[:2000]}... (truncated)
        
        Provide:
        1. Marks awarded (float, 0 to {max_marks})
        2. Brief feedback explaining the deduction (if any) or praise.
        3. Confidence score (0.0 to 1.0) on your grading accuracy.
        4. Detailed explanation of the logic.
        
        Return STRICT JSON format:
        {{
            "marks_awarded": 4.5,
            "feedback": "...",
            "confidence_score": 0.95,
            "ai_explanation": "..."
        }}
        """
        
        user_prompt = f"Student Answer:\n{answer.answer_text}"
        
        # Call LLM
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Parse Response
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            data = json.loads(content)
            
            evaluation = Evaluation(
                answer_id=answer.id,
                marks_awarded=float(data.get("marks_awarded", 0)),
                feedback=data.get("feedback", ""),
                ai_explanation=data.get("ai_explanation", ""),
                confidence_score=float(data.get("confidence_score", 0.0))
            )
            return evaluation
            
        except Exception as e:
            print(f"Error parsing Grading AI response: {content}")
            # Fallback evaluation
            return Evaluation(
                answer_id=answer.id,
                marks_awarded=0,
                feedback="Error in AI evaluation. Please upgrade manually.",
                ai_explanation=str(e),
                confidence_score=0.0
            )
