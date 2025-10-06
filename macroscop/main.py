from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import psycopg2
import uuid
from fastapi.middleware.cors import CORSMiddleware

# App yaratgandan keyin qo‘shing
app = FastAPI()

# 🔹 CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend qayerdan kelishini yozish mumkin, masalan ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# So‘rovlarni saqlash uchun vaqtinchalik storage
pending_requests = {}

# PostgreSQL ulanish
conn = psycopg2.connect(
    dbname="weighting_db",
    user="postgres",
    password="2001",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Ma'lumotlar bazasi jadvali
cursor.execute("""
CREATE TABLE IF NOT EXISTS cars (
    id SERIAL PRIMARY KEY,
    car_number VARCHAR(50),
    weight VARCHAR(50),
    channel_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


class WeightResponse(BaseModel):
    request_id: str
    channel_name: str
    weight: str


@app.post("/car_number")
async def get_car_number(request: Request):
    data = await request.json()
    print("🔹 Macroscopdan kelgan:", data)

    car_number = (
        data.get("car_number")
        or (data.get("Event") or {}).get("PlateText")
        or data.get("PlateText")
    )
    channel_name = data.get("channel_name")

    if not car_number or not channel_name:
        return JSONResponse(status_code=400, content={"message": "car_number yoki channel_name topilmadi"})

    # Request ID yaratamiz
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

    request_id, data = pending_requests.popitem()
    return {"request_id": request_id, "channel_name": data["channel_name"]}


@app.post("/weight_response")
async def weight_response(resp: WeightResponse):
    # Pendingdan car_number olish
    car_number = pending_requests.get(resp.request_id, {}).get("car_number")

    # Bazaga yozish
    cursor.execute(
        "INSERT INTO cars (car_number, weight, channel_name) VALUES (%s, %s, %s)",
        (car_number, resp.weight, resp.channel_name)
    )
    conn.commit()

    return {"message": "OK"}


# 🔹 Yangi endpoint frontend uchun
@app.get("/cars")
async def get_cars():
    cursor.execute("SELECT id, car_number, weight, channel_name, created_at FROM cars ORDER BY created_at DESC LIMIT 20")
    rows = cursor.fetchall()

    cars = []
    for r in rows:
        cars.append({
            "id": r[0],
            "car_number": r[1],
            "weight": r[2],
            "channel_name": r[3],
            "created_at": r[4].strftime("%Y-%m-%d %H:%M:%S")
        })
    return {"cars": cars}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)