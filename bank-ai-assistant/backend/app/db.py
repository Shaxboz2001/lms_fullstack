# backend/app/db.py
import os
import asyncpg

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "bank_db")
DB_USER = os.getenv("DB_USER", "bank_user")
DB_PASS = os.getenv("DB_PASS", "password123")
DB_PORT = int(os.getenv("DB_PORT", "5432"))

async def run_query(sql: str):
    """
    Async tarzda SQLni bajaradi va rows list of dict qaytaradi.
    Agar xato bo'lsa {"error": "..."} qaytaradi.
    """
    if not sql:
        return {"error": "Empty SQL"}

    conn = None
    try:
        conn = await asyncpg.connect(
            host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
        print("Running SQL:\n", sql)
        rows = await conn.fetch(sql)
        result = [dict(r) for r in rows]
        print(f"Rows returned: {len(result)}")
        return result
    except Exception as e:
        print("DB error:", e)
        return {"error": str(e)}
    finally:
        if conn:
            await conn.close()
