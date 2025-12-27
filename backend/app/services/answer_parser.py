from typing import List, Dict
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.models.exam import Question

class AnswerParserService:
    @staticmethod
    async def parse_bulk_submission(full_text: str, questions: List[Question]) -> Dict[int, str]:
        """
        Analyzes the full text of an exam submission and maps segments to question IDs.
        
        Args:
            full_text: The entire OCR'd text from student's answer sheets.
            questions: List of Question objects for the exam.
            
        Returns:
            Dictionary mapping Question ID (int) -> Answer Text (str)
        """
        
        # summary of questions for the prompt
        questions_summary = "\n".join([
            f"Q{i+1} (ID: {q.id}): {q.text[:100]}..." 
            for i, q in enumerate(questions)
        ])
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
            You are an expert exam proctor and text analyzer. 
            Your task is to take a raw, unstructured text (OCR output from a student's handwritten exam) and segment it into individual answers corresponding to the exam questions.
            
            You will be provided with:
            1. The List of Questions in the exam.
            2. The Raw Student Submission Text.
            
            Rules:
            - The student might write "Answer 1", "1)", "Q1", or just write the answer content.
            - Use the semantic content of the answer to match it to the correct question if numbering is unclear.
            - If an answer is missing, do not include it in the output.
            - Return PURE JSON format mapping Question ID to the Answer Text.
            - Format: {{ "question_id": "answer_text", ... }}
            
            Why this is important: We need to grade these answers individually.
            """),
            ("user", """
            --- Exam Questions ---
            {questions_summary}
            
            --- Student Raw Submission ---
            {full_text}
            
            --- Task ---
            Return the JSON mapping Question IDs to Answer Texts.
            """)
        ])
        
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        chain = prompt_template | llm
        
        try:
            response = await chain.ainvoke({
                "questions_summary": questions_summary,
                "full_text": full_text
            })
            
            # Clean up json string
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            mapping = json.loads(content)
            
            # Type conversion keys to int
            return {int(k): str(v) for k, v in mapping.items()}
            
        except Exception as e:
            print(f"Answer Parsing Failed: {e}")
            # Fallback: Can't map? mapping might be empty.
            # In real prod, might try regex or heuristic fallback.
            return {}
