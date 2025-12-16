from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_answer
from app.models.user import User

llm_chat = ChatOpenAI(model="gpt-4o", temperature=0.7)

class ChatService:
    @staticmethod
    async def chat_with_student(
        db: AsyncSession,
        student_id: int,
        message: str
    ) -> str:
        # 1. Fetch Student Context (Last few evaluations)
        # In a real system, we'd use vector search over their specific history or a specific exam context
        # For MVP, let's just fetch their recent answers to give the AI some context.
        
        # Hypothetical: Fetch all answers for this student (limit 10 for context window)
        # This is a bit expensive, but gives "Why did I lose marks" ability.
        # Ideally, the user passes `exam_id` in the chat request to narrow scope.
        
        system_prompt = """
        You are a helpful AI Tutor. 
        You have access to the student's recent performance and exam results.
        Answer their questions constructively.
        If they ask about marks, explain based on the feedback provided in the evaluations.
        Suggest improvements.
        """
        
        # We can't fetch EVERYTHING. Let's assume generic chat for now unless they mention a specific exam.
        # Improving logic: Check if message contains "exam" or "marks".
        
        context = "Student's Recent Performance Context:\n"
        # TODO: Add logic to fetch recent graded answers
        
        user_prompt = f"{context}\n\nStudent Question: {message}"
        
        response = await llm_chat.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        return response.content
