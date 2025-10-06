from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # React dev server
    allow_methods=["*"],  # GET, POST, OPTIONS...
    allow_headers=["*"],
)

# Fake data va model
np.random.seed(42)
n_samples = 500
data = pd.DataFrame({
    'temperature': np.random.normal(1600, 50, n_samples),
    'alloy_carbon': np.random.normal(0.3, 0.05, n_samples),
    'alloy_silicon': np.random.normal(0.2, 0.03, n_samples),
    'alloy_manganese': np.random.normal(0.8, 0.1, n_samples),
})
data['quality_score'] = (
    0.5 * data['temperature']/2000 +
    0.3 * data['alloy_carbon']/0.5 +
    0.1 * data['alloy_silicon']/0.3 +
    0.1 * data['alloy_manganese']/1.0
) * 100 + np.random.normal(0, 2, n_samples)

X = data[['temperature', 'alloy_carbon', 'alloy_silicon', 'alloy_manganese']]
y = data['quality_score']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=4, random_state=42)
model.fit(X_train, y_train)

# Request body
class InputData(BaseModel):
    temperature_min: float
    temperature_max: float

@app.post("/predict")
def predict(input: InputData):
    filtered = data[(data['temperature'] >= input.temperature_min) &
                    (data['temperature'] <= input.temperature_max)].copy()
    filtered['predicted_quality'] = model.predict(filtered[['temperature','alloy_carbon','alloy_silicon','alloy_manganese']])
    return filtered.to_dict(orient="records")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8002, reload=True)
