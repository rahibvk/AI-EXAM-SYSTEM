"""
Database Session Management

Purpose:
    Configures the Async SQLAlchemy Engine and Session Maker.
    Provides the database dependency (`get_db`) used by API endpoints.

Configuration:
    - **Pool Pre-Ping**: Checks connection health before usage (prevents stale connection errors).
    - **Pool Size**: Optimized for local/dev use (20 connections).
    - **Async**: Uses `AsyncSession` for non-blocking I/O.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create Async Engine
# echo=True prints all SQL statements to console (Debugging)
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI, 
    echo=True, 
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600
)

# Create Session Factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    """
    Dependency generator for FastAPI.
    Yields an AsyncSession and ensures it closes after the request.
    """
    async with AsyncSessionLocal() as session:
        yield session
