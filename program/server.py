from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import torch, cv2, io, numpy as np
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metall defekt modelini yuklash
model = torch.hub.load("ultralytics/yolov5", "custom", path="best.pt", source="local")

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    results = model(img)
    img_result = results.render()[0]

    _, buf = cv2.imencode(".jpg", img_result)
    byte_io = io.BytesIO(buf.tobytes())
    byte_io.seek(0)

    return StreamingResponse(byte_io, media_type="image/jpeg")
