from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import psycopg2
import uuid
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🔓 CORS (frontend uchun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pending_requests = {}

# 🔌 PostgreSQL ulanish
conn = psycopg2.connect(
    dbname="weighing_db",
    user="postgres",
    password="1017",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# 📦 Jadval
cursor.execute("""
CREATE TABLE IF NOT EXISTS cars (
    id SERIAL PRIMARY KEY,
    car_number VARCHAR(50),
    weight VARCHAR(50),
    channel_name VARCHAR(50),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


class WeightResponse(BaseModel):
    request_id: str
    channel_name: str
    weight: str


def detect_status(channel_name: str) -> str:
    """Channel nomidan statusni aniqlash (kirdi/chiqdi)."""
    name = channel_name.lower()
    if "kirish" in name or "вход" in name:
        return "kirdi"
    elif "chiqish" in name or "выход" in name:
        return "chiqdi"
    return "noma'lum"


@app.post("/car_number")
async def get_car_number(request: Request):
    data = await request.json()
    print("🔹 Macroscopdan kelgan:", data)

    car_number = (
        data.get("car_number")
        or (data.get("Event") or {}).get("PlateText")
        or data.get("PlateText")
    )
    channel_name = data.get("ChannelName")

    if not car_number or not channel_name:
        return JSONResponse(status_code=400, content={"message": "car_number yoki channel_name topilmadi"})

    request_id = str(uuid.uuid4())
    pending_requests[request_id] = {
        "car_number": car_number,
        "channel_name": channel_name
    }

    return {"message": "So‘rov yuborildi", "request_id": request_id}


@app.get("/weight_request")
async def weight_request():
    if not pending_requests:
        return JSONResponse(status_code=204, content={})

    request_id, data = next(iter(pending_requests.items()))
    return {"request_id": request_id, "channel_name": data["channel_name"]}


@app.post("/weight_response")
async def weight_response(resp: WeightResponse):
    car_number = pending_requests.get(resp.request_id, {}).get("car_number")
    if not car_number:
        return JSONResponse(status_code=404, content={"message": "Request ID topilmadi"})

    status = detect_status(resp.channel_name)

    # 🔎 Oxirgi yozuvni tekshirish
    cursor.execute(
        "SELECT status FROM cars WHERE car_number=%s ORDER BY created_at DESC LIMIT 1",
        (car_number,)
    )
    last_row = cursor.fetchone()

    if last_row:
        last_status = last_row[0]
        if last_status == "kirdi" and status == "kirdi":
            pending_requests.pop(resp.request_id, None)
            return {"message": "Mashina allaqachon ichkarida"}
        if last_status == "chiqdi" and status == "chiqdi":
            pending_requests.pop(resp.request_id, None)
            return {"message": "Mashina allaqachon tashqarida"}

    # ✅ Vaznni tekshirish
    if resp.weight and resp.weight.isdigit() and int(resp.weight) > 0:
        cursor.execute(
            "INSERT INTO cars (car_number, weight, channel_name, status) VALUES (%s, %s, %s, %s)",
            (car_number, resp.weight, resp.channel_name, status)
        )
        conn.commit()
        message = f"{car_number} yozildi: {status}, {resp.weight}kg"
    else:
        message = "Og‘irlik 0 yoki noto‘g‘ri, yozilmadi"

    pending_requests.pop(resp.request_id, None)
    return {"message": message}


@app.get("/cars")
async def get_cars():
    cursor.execute("SELECT id, car_number, weight, channel_name, status, created_at FROM cars ORDER BY created_at DESC LIMIT 20")
    rows = cursor.fetchall()

    cars = []
    for r in rows:
        cars.append({
            "id": r[0],
            "car_number": r[1],
            "weight": r[2],
            "channel_name": r[3],
            "status": r[4],
            "created_at": r[5].strftime("%Y-%m-%d %H:%M:%S")
        })
    return {"cars": cars}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="172.16.7.26", port=8000)
