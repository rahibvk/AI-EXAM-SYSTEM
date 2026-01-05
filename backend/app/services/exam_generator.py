"""
Exam Generator Service

Purpose:
    Generates high-quality exam questions using Generative AI (LLM) and RAG (Retrieval-Augmented Generation).
    It acts as an "AI Professor" that reads course materials and creates unique questions.

Key Assumptions:
    - Course materials are already chunked and embedded in the database (for RAG).
    - OpenAI API key is configured and valid.
    - If RAG fails or finds no context, it falls back to a "Mock" mode to ensure the user always gets a result.

Links:
    - Uses OpenAI GPT-4o for generation.
    - Uses LangChain for prompt management.
"""
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
        # topic removed
        difficulty: str,
        num_questions: int, # Deprecated/Total count
        question_type: str = "subjective", # Deprecated
        subjective_count: int = 0,
        objective_count: int = 0,
        total_marks: float = 100,
        material_ids: list[int] = None
    ) -> list[QuestionCreate]:
        """
        Orchestrates the generation of exam questions.

        Inputs:
            db: Database session.
            course_id: The course to generate questions for.
            difficulty: "Easy", "Medium", "Hard".
            subjective_count: Number of essay/text questions.
            objective_count: Number of multiple-choice questions.
            total_marks: Total score for the exam (e.g., 100).
            material_ids: Optional list of specific documents to focus on.

        Outputs:
            list[QuestionCreate]: A list of question objects ready to be saved to the DB.

        Side Effects:
            - Calls external OpenAI API.
            - Reads course materials and embeddings from DB.
        """
        
        # 0. Mock Fallback Helper
        def get_mock_questions(count_subj, count_obj, available_materials=None):
            # Extract titles if materials are provided
            topics = []
            if available_materials and len(available_materials) > 0:
                topics = [m.title for m in available_materials]
            
            # Fallback if no materials or list empty
            if not topics:
                topics = ["General Course Concept"]
            
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

        # 1. Retrieve Context (Hybrid RAG + Fallback)
        try:
            # DEBUG: Check API Key Status
            import os
            key = os.getenv("OPENAI_API_KEY", "")
            if len(key) <= 5:
                print(f"DEBUG: API Key is missing or too short: '{key}'")

            materials = [] # Init to avoid UnboundLocalError if RAG path is taken
            context_text = ""
            topic_context = "General Course Content"
            
            # A. Try RAG (Vector Search)
            try:
                from app.models.course import CourseMaterialChunk
                
                # Create a generic query since we lack specific topic input
                query_vec = await generate_embedding("Key concepts, definitions, and important exam topics")
                
                stmt = select(CourseMaterialChunk).join(CourseMaterial).filter(CourseMaterial.course_id == course_id)
                if material_ids:
                    stmt = stmt.filter(CourseMaterial.id.in_(material_ids))
                
                # Fetch all chunks (filtering by similarity in Python because pgvector is missing)
                result = await db.execute(stmt)
                all_chunks = result.scalars().all()
                
                # Manual Cosine Similarity
                import math
                def cosine_similarity(v1, v2):
                    if not v1 or not v2: return 0.0
                    dot = sum(a*b for a, b in zip(v1, v2))
                    norm1 = math.sqrt(sum(a*a for a in v1))
                    norm2 = math.sqrt(sum(b*b for b in v2))
                    return dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

                # Score and Sort
                scored_chunks = []
                target_vec = query_vec
                for chunk in all_chunks:
                    if chunk.embedding:
                        # chunk.embedding is ARRAY(Float), usually a list in python
                        score = cosine_similarity(target_vec, chunk.embedding)
                        scored_chunks.append((score, chunk))
                
                # Top 8
                scored_chunks.sort(key=lambda x: x[0], reverse=True)
                chunks = [c for s, c in scored_chunks[:8]]
                
                if chunks:
                    print(f"\n[RAG SYSTEM] SUCCESS: Retrieved {len(chunks)} relevant chunks via Cosine Similarity.")
                    print(f"[RAG SYSTEM] Context injected into LLM.\n")
                    context_text = "\n---\n".join([f"Relevant Excerpt:\n{c.chunk_text}" for c in chunks])
                    topic_context = "AI-Selected Relevant Material"
            except Exception as vector_err:
                 print(f"[RAG SYSTEM] RETRIEVAL ERROR: {vector_err}")
                 chunks = []

            # B. Fallback: Full Text Context Injection (if RAG returned nothing)
            if not context_text:
                print("\n[RAG SYSTEM] No relevant chunks found. FALLING BACK to Full Document Injection.\n")
                materials = []
                if material_ids and len(material_ids) > 0:
                    stmt = select(CourseMaterial).filter(CourseMaterial.id.in_(material_ids))
                    result = await db.execute(stmt)
                    materials = result.scalars().all()
                else:
                    stmt = select(CourseMaterial).filter(CourseMaterial.course_id == course_id)
                    result = await db.execute(stmt)
                    materials = result.scalars().all()
                
                if not materials:
                     print("No materials found, returning mocks.")
                     return get_mock_questions(subjective_count or num_questions, objective_count, available_materials=None)
                
                # Prepare context text from first 5 docs
                context_text = "\n\n".join([f"Material '{m.title}':\n{m.content_summary}" for m in materials[:5]])
                topic_context = materials[0].title if materials else "Class Content"

        except Exception as e:
            print(f"Error fetching materials: {e}")
            return get_mock_questions(subjective_count or num_questions, objective_count)
        
        # Infer topic from materials
        topic_context = materials[0].title if materials else "Class Content"
        
        # Calculate totals
        if subjective_count == 0 and objective_count == 0:
             if question_type == "subjective":
                 subjective_count = num_questions
             else:
                 objective_count = num_questions
        
        total_questions = subjective_count + objective_count
        
        # --- Integer Mark Distribution Algorithm ---
        # The goal is to split 'total_marks' (e.g. 100) into integers across questions.
        # We assign weights (Subjective=4x, Objective=1x) to determine relative value.
        
        # 1. Determine base integer marks
        weight_subj = 4
        weight_obj = 1
        total_units = (subjective_count * weight_subj) + (objective_count * weight_obj)
        if total_units == 0: total_units = 1
        
        base_unit_val = total_marks / total_units
        
        # Calculate base integer scores
        score_obj = max(1, int(round(base_unit_val * weight_obj)))
        score_subj = max(1, int(round(base_unit_val * weight_subj)))
        
        # 2. Create list of marks
        subj_marks_list = [score_subj] * subjective_count
        obj_marks_list = [score_obj] * objective_count
        
        # 3. Calculate current sum and difference
        # Because of rounding, the sum might not equal total_marks exactly.
        current_sum = sum(subj_marks_list) + sum(obj_marks_list)
        diff = int(total_marks - current_sum)
        
        # 4. Distribute difference to Subjective questions first
        # We greedily add/remove 1 point from questions until the diff is 0.
        if subjective_count > 0:
            # Distribute diff 1 by 1
            idx = 0
            while diff != 0:
                if diff > 0:
                    subj_marks_list[idx % subjective_count] += 1
                    diff -= 1
                else:
                    if subj_marks_list[idx % subjective_count] > 1: # Don't go below 1
                        subj_marks_list[idx % subjective_count] -= 1
                        diff += 1
                    else:
                        # If we can't reduce subj, try obj? Or just break to avoid infinite loop
                        break 
                idx += 1
        elif objective_count > 0:
             # If only objective, distribute diff there
             idx = 0
             while diff != 0:
                if diff > 0:
                    obj_marks_list[idx % objective_count] += 1
                    diff -= 1
                else:
                    if obj_marks_list[idx % objective_count] > 1:
                        obj_marks_list[idx % objective_count] -= 1
                        diff += 1
                    else:
                        break
                idx += 1
                
        # Format lists for Prompt
        subj_marks_str = ", ".join(map(str, subj_marks_list))
        obj_marks_str = ", ".join(map(str, obj_marks_list))

        # 2. Prompt Engineering
        # We instruct the LLM to strictly follow the calculated mark distribution.
        system_prompt = f"""
        You are an expert professor designing a high-quality exam. Your task is to generate {total_questions} UNIQUE and DIVERSE questions using the course material.

        Requirements:
        1. **Quantity & Structure**:
           - **Subjective Questions**: {subjective_count} questions.
             - Assign these EXACT keys marks: [{subj_marks_str}].
           - **Objective Questions**: {objective_count} questions.
             - Assign these EXACT marks: [{obj_marks_str}].
           - Total Marks: {total_marks}.
        
        2. **Mark Allocation (STRICT)**:
           - You MUST use the specific mark values provided above in respective order.
           - Ensure the final sum is EXACTLY {total_marks}.

        3. **Content & Quality**:
           - Difficulty: {difficulty}.
           - Topic Context: {topic_context}.
           - **DIVERSITY**: Do NOT repeat concepts. Cover different aspects of the material.
           - **UNIQUENESS**: Each question must look at the topic from a different angle (definitions, applications, comparisons, analysis).
           - Use the provided Context Material as the source of truth.

        4. **Format**:
           - Return strictly a JSON array.
           - For Objective (MCQ), provide 4 distinct options and clearly mark the correct model answer.
        
        Format Example:
        [
            {{
                "text": "Analyze the relationship between X and Y mentioned in the text.",
                "marks": 10,
                "model_answer": "X influences Y by...",
                "question_type": "subjective"
            }},
            {{
                "text": "Which of the following is NOT a characteristic of Z?",
                "marks": 5,
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
            return get_mock_questions(subjective_count, objective_count, available_materials=materials)

