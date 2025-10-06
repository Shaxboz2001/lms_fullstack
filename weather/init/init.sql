CREATE TABLE IF NOT EXISTS weather (
    id SERIAL PRIMARY KEY,
    city VARCHAR(50),
    temperature FLOAT,
    humidity INT,
    description VARCHAR(100),
    aqi INT,
    pm25 FLOAT,
    pm10 FLOAT,
    ts TIMESTAMP
);
