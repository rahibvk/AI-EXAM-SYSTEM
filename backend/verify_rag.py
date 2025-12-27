import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        try:
            # Check Extension
            result = await db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            ext = result.fetchone()
            print(f"PgVector Extension: {'INSTALLED' if ext else 'MISSING'}")

            # Check Table
            result = await db.execute(text("SELECT to_regclass('public.course_material_chunk')"))
            table = result.scalar()
            print(f"RAG Chunk Table: {'EXISTS' if table else 'MISSING'}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
