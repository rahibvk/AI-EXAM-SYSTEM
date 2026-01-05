"""
Embeddings Service

Purpose:
    Generates vector embeddings for text using OpenAI's `text-embedding-3-small`.
    These embeddings are stored in PostgreSQL (via pgvector) and used for RAG.

Robustness:
    - **Mock Mode**: If `OPENAI_API_KEY` is missing or invalid, it returns zero-vectors.
      This allows the app to start and run basic CRUD operations/tests without crashing on missing credentials.
"""
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
import os

# Ensure API Key is set
# TODO: In real app, might want to allow user to pass key or pull from DB
api_key = os.getenv("OPENAI_API_KEY")

# Initialize model only if key looks valid-ish (basic check)
use_mock_embeddings = False
if not api_key or len(api_key) < 10 or api_key.startswith("sk-place") or "change-me" in api_key.lower():
    use_mock_embeddings = True
    embeddings_model = None
else:
    # 1536 dimensions for text-embedding-3-small
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

async def generate_embedding(text: str) -> list[float]:
    """
    Generates a single vector embedding for a query string.
    
    Inputs:
        text: The user's query or text snippet.

    Outputs:
        list[float]: A 1536-dimensional vector.
        
    Fallback:
        Returns [0.0]*1536 if API key is invalid or request fails.
    """
    try:
        if use_mock_embeddings or not api_key:
            return [0.0] * 1536
        
        return await embeddings_model.aembed_query(text)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Fallback to mock embeddings on error
        return [0.0] * 1536

async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a batch of documents (more efficient than single calls)."""
    if use_mock_embeddings:
        return [[0.0] * 1536 for _ in texts]
    return await embeddings_model.aembed_documents(texts)
