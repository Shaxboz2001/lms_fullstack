from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
import os
import logging

app = FastAPI(title="O'zbekiston Ob-havo va AQI API")

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # ruxsat etilgan domenlar
    allow_credentials=True,
    allow_methods=["*"],    # GET, POST, PUT, DELETE va hok.
    allow_headers=["*"],    # barcha headerlarga ruxsat
)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logging.warning("DATABASE_URL muhit o'zgaruvchisi o'rnatilmagan.")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL yo'q. docker-compose yoki konteyner env ni tekshiring.")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

@app.get("/health")
def health():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        logging.exception("Health check failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/db")
def debug_db():
    """Diagnostic — jadvaldagi son va 5 ta sample row qaytaradi."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT count(*) AS cnt FROM weather_data;")
        cnt = cur.fetchone().get("cnt")
        cur.execute("SELECT city, temperature, humidity, description, aqi, timestamp FROM weather_data ORDER BY timestamp DESC LIMIT 5;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"count": cnt, "sample": rows}
    except Exception as e:
        logging.exception("debug_db xato")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/weather/all")
def get_all_weather():
    """Har bir shahar uchun eng yangi yozuvni qaytaradi (case-insensitive)."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT ON (LOWER(TRIM(city))) city, temperature, humidity, description, aqi, timestamp
            FROM weather_data
            ORDER BY LOWER(TRIM(city)), timestamp DESC;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        logging.exception("get_all_weather SQL xatosi")
        raise HTTPException(status_code=500, detail=str(e))

    if not rows:
        # Frontend qulayligi uchun bo'sh ro'yxat qaytamiz
        return []

    result = []
    for r in rows:
        ts = r.get("timestamp")
        if ts:
            try:
                ts = ts.strftime("%Y-%m-%d %H:%M")
            except Exception:
                ts = str(ts)
        result.append({
            "shahar": r.get("city"),
            "harorat": f"{r.get('temperature')} °C" if r.get("temperature") is not None else None,
            "namlik": f"{r.get('humidity')} %" if r.get("humidity") is not None else None,
            "tavsif": r.get("description"),
            "AQI": r.get("aqi"),
            "yangilangan_vaqt": ts,
        })

    return result
@app.get("/weather/{city}")
def get_weather(city: str):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT city, temperature, humidity, description, aqi, timestamp
            FROM weather_data
            WHERE LOWER(TRIM(city)) = LOWER(TRIM(%s))
            ORDER BY timestamp DESC
            LIMIT 1
        """, (city,))
        row = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        logging.exception("get_weather SQL xatosi")
        raise HTTPException(status_code=500, detail=str(e))

    if not row:
        return {"xato": f"{city} uchun ma'lumot topilmadi"}

    ts = row.get("timestamp")
    if ts is not None:
        try:
            ts = ts.strftime("%Y-%m-%d %H:%M")
        except Exception:
            ts = str(ts)

    return {
        "shahar": row.get("city"),
        "harorat": f"{row.get('temperature')} °C" if row.get("temperature") is not None else None,
        "namlik": f"{row.get('humidity')} %" if row.get("humidity") is not None else None,
        "tavsif": row.get("description"),
        "AQI": row.get("aqi"),
        "yangilangan_vaqt": ts,
    }


