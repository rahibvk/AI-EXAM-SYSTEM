import asyncio
import asyncpg
from urllib.parse import quote_plus
from datetime import datetime

async def check_activity():
    user = "postgres"
    password = "Musrah@12"
    db = "postgres"
    port = 5432
    
    encoded_password = quote_plus(password)
    dsn = f"postgresql://{user}:{encoded_password}@localhost:{port}/{db}"
    
    try:
        conn = await asyncpg.connect(dsn)
        print(f"Connected to {db} on port {port} at {datetime.now()}\n")
        
        # Query active connections
        rows = await conn.fetch("""
            SELECT 
                pid, 
                usename, 
                client_addr, 
                backend_start, 
                state, 
                query 
            FROM pg_stat_activity 
            WHERE datname = 'postgres'
            ORDER BY backend_start DESC;
        """)
        
        print(f"{'PID':<8} | {'User':<10} | {'Client':<15} | {'Connected Since':<25} | {'State':<10}")
        print("-" * 80)
        
        for row in rows:
            pid = str(row['pid'])
            usename = str(row['usename'])
            client = str(row['client_addr']) if row['client_addr'] else "Local/Internal"
            time = row['backend_start'].strftime("%Y-%m-%d %H:%M:%S")
            state = str(row['state'])
            
            print(f"{pid:<8} | {usename:<10} | {client:<15} | {time:<25} | {state:<10}")

        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_activity())
