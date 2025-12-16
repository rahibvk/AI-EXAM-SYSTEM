import asyncio
import asyncpg

async def check_creds(user, password, db):
    dsn = f"postgresql://{user}:{password}@localhost:5432/{db}"
    print(f"Testing {user}:{password}@{db} ... ", end="")
    try:
        conn = await asyncpg.connect(dsn)
        await conn.close()
        print("SUCCESS!")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

async def main():
    creds = [
        ("postgres", "Musrah@12", "postgres"),
        ("postgres", "Musrah%4012", "postgres"),
        ("postgres", "password", "postgres"),
        ("postgres", "postgres", "postgres"),
        ("postgres", "1234", "postgres"),
        ("admin", "password", "postgres"),
         ("postgres", "Musrah@12", "exam_evaluation_db"), # Case where DB exists
    ]
    
    for user, pwd, db in creds:
        if await check_creds(user, pwd, db):
            print(f"\nFOUND VALID CREDENTIALS:\nUser: {user}\nPassword: {pwd}\nDB: {db}")
            return

if __name__ == "__main__":
    asyncio.run(main())
