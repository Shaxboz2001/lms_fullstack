import asyncio
import websockets
import json
import psycopg2
from psycopg2.extras import RealDictCursor

# 🔑 PostgreSQL sozlamalari
DB_CONFIG = {
    "dbname": "scale_db",
    "user": "postgres",
    "password": "your_password",
    "host": "localhost",
    "port": 5432,
}

# 🚀 Postgresga ulanish
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# 🔧 Jadvalni yaratish (agar mavjud bo‘lmasa)
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scale_data (
            id SERIAL PRIMARY KEY,
            scale_name TEXT,
            weight NUMERIC,
            ts TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

async def save_to_db(message: str):
    try:
        data = json.loads(message)
        scale = data.get("scale")
        weight = data.get("weight")
        timestamp = data.get("timestamp")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO scale_data (scale_name, weight, ts) VALUES (%s, %s, %s)",
            (scale, weight, timestamp),
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"💾 Saqlandi: {scale} | {weight} | {timestamp}")
    except Exception as e:
        print(f"❌ DB xato: {e}")

async def handler(websocket):
    async for message in websocket:
        print(f"📥 Qabul qilindi: {message}")
        await save_to_db(message)

async def main():
    init_db()
    async with websockets.serve(handler, "localhost", 8000):
        print("✅ WebSocket server 8000-portda ishlayapti (Postgres bilan)")
        await asyncio.Future()  # serverni cheksiz ishlatish

if __name__ == "__main__":
    asyncio.run(main())
