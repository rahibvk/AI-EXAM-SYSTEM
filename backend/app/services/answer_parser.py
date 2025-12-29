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
            Your task is to take a raw, unstructured OCR text from a handwritten exam and segment it into individual answers corresponding to the exam questions.
            
            You will be provided with:
            1. The List of Questions in the exam (Keys are Question IDs).
            2. The Raw Student Submission Text (concatenated pages).
            
            CRITICAL RULES:
            1. **EXTRACT ALL ANSWERS**: The document contains multiple answers. Find them all.
            2. **Map Index to ID**: The `questions_summary` lists "Q1 (ID: 123)". If the student writes "1. The answer is...", map it to ID `123`.
            3. **Implicit Order**: If no numbers are present, assume the paragraphs appear in Question order (Q1, then Q2, etc.).
            4. **Output format**: JSON with Question ID (int) as keys. e.g. {{ "123": "Answer text" }}
            5. **Clean Text**: Capture the full answer text for each question.
            
            Return PURE JSON only.
            """),
            ("user", """
            --- Database Questions (Index -> ID) ---
            {questions_summary}
            
            --- Student Handwritten Text (OCR) ---
            {full_text}
            
            --- Task ---
            Map encoded answers to Question IDs. Return JSON.
            """)
        ])
        
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        chain = prompt_template | llm
        
        try:
            response = await chain.ainvoke({
                "questions_summary": questions_summary,
                "full_text": full_text
            })
            
            content = response.content.strip()
            
            # Robust JSON extraction using regex
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            mapping = json.loads(content)
            
            # Type conversion keys to int
            return {int(k): str(v) for k, v in mapping.items()}
            
        except Exception as e:
            print(f"Answer Parsing Failed: {e}")
            print(f"Raw LLM Output: {response.content if 'response' in locals() else 'No response'}")
            return {}
