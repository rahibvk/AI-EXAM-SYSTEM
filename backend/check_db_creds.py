import asyncio
import asyncpg
from urllib.parse import quote_plus

async def check_creds(user, password, db, port=5432):
    encoded_password = quote_plus(password)
    dsn = f"postgresql://{user}:{encoded_password}@localhost:{port}/{db}"
    print(f"Testing {user}:{password}@{db} on port {port} ... ", end="")
    try:
        conn = await asyncpg.connect(dsn)
        await conn.close()
        print("SUCCESS!")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

async def main():
    # Common local credentials to test
    creds = [
        ("postgres", "postgres", "postgres"),
        ("postgres", "password", "postgres"),
        ("postgres", "1234", "postgres"),
        ("admin", "admin", "postgres"),
        ("postgres", "Musrah@12", "postgres"), # User's previous attempt
    ]
    
    for user, pwd, db in creds:
        if await check_creds(user, pwd, db):
            print(f"\nFOUND VALID CREDENTIALS:\nUser: {user}\nPassword: {pwd}\nDB: {db}")
            return

if __name__ == "__main__":
    asyncio.run(main())
