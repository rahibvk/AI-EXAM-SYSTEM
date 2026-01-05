"""
Evaluation Service

Purpose:
    Provides Automated Grading (Auto-Grading) for student answers using AI.
    It acts as an "AI Examiner" that compares a student's answer against a model answer 
    and assigns a score, feedback, and confidence level.

Key Assumptions:
    - The Model Answer provided by the Exam Generator is the "Ground Truth".
    - The AI can reasonably interpret handwritten text (transcribed via OCR).
    - It handles "Ambiguous" cases by requesting manual review instead of guessing.

Constraints:
    - Dependent on LLM latency.
    - Consistency is handled by setting a low temperature (0.3).
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.models.answer import StudentAnswer, Evaluation

# Initialize LLM
# Lower temperature (0.3) ensures the AI is more deterministic and consistent 
# when grading the same answer multiple times.
llm = ChatOpenAI(model="gpt-4o", temperature=0.3) 

class EvaluationService:
    @staticmethod
    async def evaluate_answer(
        answer: StudentAnswer,
        model_answer: str,
        question_text: str,
        max_marks: float,
        context_text: str = ""
    ) -> Evaluation:
        """
        Evaluates a single student answer against the model answer.

        Inputs:
            answer: The StudentAnswer object containing the student's text.
            model_answer: The correct answer to compare against.
            question_text: The original question.
            max_marks: The maximum score possible for this question.
            context_text: Optional extra context from course materials (rarely used).

        Outputs:
            Evaluation: An object containing marks_awarded, feedback, and metadata.

        Edge Cases:
            - If answer is empty or whitespace -> Returns 0 marks immediately.
            - If answer is "Garbage" (random text) -> AI is instructed to give 0 marks.
        """
        
        # 1. Pre-check: Empty Answer
        if not answer.answer_text or not answer.answer_text.strip():
            return Evaluation(
                answer_id=answer.id,
                marks_awarded=0.0,
                feedback="No answer provided.",
                ai_explanation="Auto-graded: Answer text was empty.",
                confidence_score=1.0,
                review_requested=False
            )
            
        system_prompt = f"""
        You are an expert, strict, and fair specialized examiner. Your task is to evaluate a student's answer against a model answer for a given question.
        
        CRITICAL RULES (READ CAREFULLY):
        1. **Irrelevant/Garbage**: If the answer is random text, greetings, completely unrelated, or garbage characters -> **Award 0 Marks**. Set `review_requested` to **FALSE**. (You are confident it is garbage).
        2. **Empty/Not Found**: If the answer says "Answer not found" -> **Award 0 Marks**, `review_requested` FALSE.
        3. **Valid Attempt**: Grade based on logic.
        4. **Ambiguous**: ONLY set `review_requested` to TRUE if the handwriting/text is *potentially* a correct answer but hard to read, or if you are *unsure*.
        
        --- Context ---
        Question: {question_text}
        Max Marks: {max_marks}
        Model Answer: {model_answer}
        
        Course Material Context (Reference only):
        {context_text[:2000]}
        
        --- Output Requirement ---
        You MUST return valid JSON only. No other text.
        {{
            "marks_awarded": (float, 0 to {max_marks}),
            "feedback": (string, concise explanation for student),
            "ai_explanation": (string, why did you give this grade?),
            "confidence_score": (float, 0.0 to 1.0. If sure it's garbage, use 1.0),
            "review_requested": (boolean, default false. Only true if unsure)
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
                confidence_score=float(data.get("confidence_score", 0.0)),
                review_requested=bool(data.get("review_requested", False))
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
