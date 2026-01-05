import asyncio
import asyncpg
from urllib.parse import quote_plus

async def list_tables():
    user = "postgres"
    password = "Musrah@12"
    db = "postgres"
    port = 5432
    
    encoded_password = quote_plus(password)
    dsn = f"postgresql://{user}:{encoded_password}@localhost:{port}/{db}"
    
    print(f"Connecting to {db} on port {port}...")
    try:
        conn = await asyncpg.connect(dsn)
        print("Connected successfully!")
        
        rows = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        print(f"\nFound {len(rows)} tables:")
        for row in rows:
            print(f"- {row['table_name']}")
            
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_tables())
