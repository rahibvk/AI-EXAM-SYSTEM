import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.course import CourseMaterial
from app.schemas.exam import QuestionCreate
from app.services.embeddings import generate_embedding

# Initialize LLM lazily
# llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

class ExamGeneratorService:
    @staticmethod
    async def generate_questions(
        db: AsyncSession,
        course_id: int,
        topic: str,
        difficulty: str,
        num_questions: int, # Deprecated/Total count
        question_type: str = "subjective", # Deprecated
        subjective_count: int = 0,
        objective_count: int = 0,
        material_ids: list[int] = None
    ) -> list[QuestionCreate]:
        
        # 0. Mock Fallback Helper
        def get_mock_questions(count_subj, count_obj, topic_label, available_materials=None):
            # Extract titles if materials are provided
            topics = []
            if available_materials and len(available_materials) > 0:
                topics = [m.title for m in available_materials]
            
            # Fallback if no materials or list empty
            if not topics:
                topics = [topic_label if topic_label else "General Course Concept"]
            
            mocks = []
            
            # Templates for variety
            subj_templates = [
                f"Explain the core concepts of '{{topic}}' in detail.",
                f"Analyze the impact of '{{topic}}' in a real-world scenario.",
                f"Compare and contrast different approaches within '{{topic}}'.",
                f"Discuss the advantages and disadvantages of '{{topic}}'.",
                f"Describe the historical evolution of '{{topic}}'.",
                f"How does '{{topic}}' relate to other key course themes?"
            ]
            
            obj_templates = [
                f"Which of the following is a primary characteristic of '{{topic}}'?",
                f"What is the main function of '{{topic}}'?",
                f"Which statement best describes '{{topic}}'?",
                f"Identify the incorrect statement regarding '{{topic}}'.",
                f"In the context of '{{topic}}', what does X represent?"
            ]

            for i in range(count_subj):
                # Cycle through templates
                template = subj_templates[i % len(subj_templates)]
                # Cycle through available topics/materials
                current_topic = topics[i % len(topics)]
                
                q_text = template.format(topic=current_topic)
                
                mocks.append(QuestionCreate(
                    text=f"{q_text} (Mock Q{i+1})",
                    marks=5,
                    model_answer=f"Model answer for: {q_text}",
                    question_type="subjective"
                ))
            
            for i in range(count_obj):
                template = obj_templates[i % len(obj_templates)]
                # Cycle through available topics/materials (offset by subj count for variety)
                current_topic = topics[(i + count_subj) % len(topics)]
                
                q_text = template.format(topic=current_topic)
                
                mocks.append(QuestionCreate(
                    text=f"{q_text} (Mock MCQ Q{i+1})",
                    marks=2,
                    model_answer="Option A",
                    question_type="objective", 
                ))
            return mocks

        # 1. Retrieve Context
        try:
            # DEBUG: Check API Key Status
            import os
            key = os.getenv("OPENAI_API_KEY", "")
            if len(key) > 5:
                # print(f"DEBUG: Using API Key starting with: {key[:8]}...")
                pass
            else:
                print(f"DEBUG: API Key is missing or too short: '{key}'")

            materials = []
            if material_ids and len(material_ids) > 0:
                stmt = select(CourseMaterial).filter(CourseMaterial.id.in_(material_ids))
                result = await db.execute(stmt)
                materials = result.scalars().all()
            elif topic:
                 # RAG Search
                try:
                    query_embedding = await generate_embedding(topic)
                    # Use all course materials for now
                    stmt = select(CourseMaterial).filter(CourseMaterial.course_id == course_id)
                    result = await db.execute(stmt)
                    materials = result.scalars().all()
                except Exception:
                    # RAG failed (e.g. key error in embeddings) -> Fallback to searching all by course ID
                    stmt = select(CourseMaterial).filter(CourseMaterial.course_id == course_id)
                    result = await db.execute(stmt)
                    materials = result.scalars().all()
            else:
                stmt = select(CourseMaterial).filter(CourseMaterial.course_id == course_id)
                result = await db.execute(stmt)
                materials = result.scalars().all()
                
                if not topic:
                    topic = "General Knowledge from Course Materials"
                    
        except Exception as e:
            print(f"Error fetching materials: {e}")
            fallback_topic = topic if topic else "General Course Content"
            return get_mock_questions(subjective_count or num_questions, objective_count, fallback_topic)

        if not materials:
             print("No materials found, returning mocks.")
             return get_mock_questions(subjective_count or num_questions, objective_count, topic or "Empty Course")
            
        # Prepare context text
        context_text = "\n\n".join([f"Material '{m.title}':\n{m.content_summary}" for m in materials[:5]])
        
        # Infer topic for prompt if empty
        if not topic:
             # Just use the title of the first material as a hint
             topic = materials[0].title if materials else "General Context"
        
        # Calculate totals
        if subjective_count == 0 and objective_count == 0:
             if question_type == "subjective":
                 subjective_count = num_questions
             else:
                 objective_count = num_questions
        
        total_questions = subjective_count + objective_count

        # 2. Prompt Engineering
        system_prompt = f"""
        You are an expert professor designing a high-quality exam. Your task is to generate {total_questions} UNIQUE and DIVERSE questions based on the provided course material.

        Requirements:
        1. **Quantity & Type**:
           - EXACTLY {subjective_count} Subjective questions (Short/Long answer).
           - EXACTLY {objective_count} Objective questions (Multiple Choice).
           - Total: {total_questions} questions.
        
        2. **Content & Quality**:
           - Difficulty: {difficulty}.
           - Topic Focus: {topic}.
           - **DIVERSITY**: Do NOT repeat concepts. Cover different aspects of the material.
           - **UNIQUENESS**: Each question must look at the topic from a different angle (definitions, applications, comparisons, analysis).
           - Use the provided Context Material as the source of truth.

        3. **Format**:
           - Return strictly a JSON array.
           - For Objective (MCQ), provide 4 distinct options and clearly mark the correct model answer.
        
        Format Example:
        [
            {{
                "text": "Analyze the relationship between X and Y mentioned in the text.",
                "marks": 5,
                "model_answer": "X influences Y by...",
                "question_type": "subjective"
            }},
            {{
                "text": "Which of the following is NOT a characteristic of Z?",
                "marks": 2,
                "model_answer": "Option B",
                "question_type": "objective",
                "options": ["Option A", "Option B", "Option C", "Option D"]
            }}
        ]
        """
        
        user_prompt = f"Context Material:\n{context_text}"
        
        # 3. Call LLM
        try:
            # Init here to catch auth errors
            llm_instance = ChatOpenAI(model="gpt-4o", temperature=0.7)
            
            response = await llm_instance.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            # 4. Parse Response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            questions_data = json.loads(content)
            
            questions = []
            for q in questions_data:
                q_type = q.get('question_type', question_type)
                q_text = q['text']
                if q_type == 'objective' and 'options' in q:
                    options_str = "\n".join([f"- {opt}" for opt in q['options']])
                    q_text = f"{q_text}\n\nOptions:\n{options_str}"

                questions.append(QuestionCreate(
                    text=q_text,
                    marks=q.get('marks', 5),
                    model_answer=q.get('model_answer', ''),
                    question_type=q_type
                ))
            return questions
            
        except Exception as e:
            print(f"AI Generation Failed: {e}")
            print("Falling back to MOCK questions.")
            return get_mock_questions(subjective_count, objective_count, topic, available_materials=materials)
