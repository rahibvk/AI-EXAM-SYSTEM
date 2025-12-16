from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
import os

# Ensure API Key is set
# TODO: In real app, might want to allow user to pass key or pull from DB
api_key = os.getenv("OPENAI_API_KEY")
# if not api_key:
#     os.environ["OPENAI_API_KEY"] = "sk-placeholder-replace-me"

# Initialize model only if key looks valid-ish (basic check)
use_mock_embeddings = False
if not api_key or len(api_key) < 10 or api_key.startswith("sk-place") or "change-me" in api_key.lower():
    use_mock_embeddings = True
    embeddings_model = None
else:
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

async def generate_embedding(text: str) -> list[float]:
    try:
        # DEBUG LOGGING
        import os
        key = os.getenv("OPENAI_API_KEY", "")
        if len(key) < 10:
             print(f"DEBUGGING EMBEDDINGS: API Key is missing or invalid: '{key}'")

        if not api_key:
            # Return zero vector if no key
            return [0.0] * 1536
            
        # If use_mock_embeddings is true, this block won't be reached due to the global check
        # If api_key is valid, use the globally initialized embeddings_model
        if use_mock_embeddings: # This check is redundant if the global `use_mock_embeddings` is true
            return [0.0] * 1536
        
        # Use the globally initialized embeddings_model
        return await embeddings_model.aembed_query(text)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Fallback to mock embeddings on error
        return [0.0] * 1536

async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if use_mock_embeddings:
        return [[0.0] * 1536 for _ in texts]
    return await embeddings_model.aembed_documents(texts)
