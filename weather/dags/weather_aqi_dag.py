from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import psycopg2
import os
import logging

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
AQI_API_TOKEN = os.getenv("AQI_API_TOKEN")

DB_HOST = "postgres"
DB_NAME = "weather_db"
DB_USER = "airflow"
DB_PASS = "airflow"

# O‘zbekiston viloyat markazlari
CITIES = [
    "Tashkent", "Andijan", "Namangan", "Fergana",
    "Samarkand", "Bukhara", "Navoiy", "Urgench",
    "Qarshi", "Termez", "Jizzakh", "Gulistan"
]

def fetch_and_save(city):
    """Shahar bo‘yicha ob-havo va AQI ma’lumotlarini olib Postgresga saqlash"""
    try:
        # OpenWeather
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=uz"
        weather = requests.get(weather_url).json()

        # AQICN
        aqi_url = f"https://api.waqi.info/feed/Tashkent/?token={AQI_API_TOKEN}"
        aqi = requests.get(aqi_url).json()

        if "main" not in weather:
            logging.error(f"{city} uchun ob-havo topilmadi")
            return
        if "data" not in aqi:
            logging.error(f"{city} uchun AQI topilmadi")
            return

        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS weather_data (
                id SERIAL PRIMARY KEY,
                city VARCHAR(50),
                temperature FLOAT,
                humidity FLOAT,
                description TEXT,
                aqi INT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            INSERT INTO weather_data (city, temperature, humidity, description, aqi)
            VALUES (%s, %s, %s, %s, %s);
        """, (
            weather["name"],
            weather["main"]["temp"],
            weather["main"]["humidity"],
            weather["weather"][0]["description"],
            aqi["data"].get("aqi")
        ))

        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"✅ {city} saqlandi")

    except Exception as e:
        logging.error(f"{city} uchun xato: {e}")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'uz_weather_aqi_dag',
    default_args=default_args,
    description="O‘zbekiston viloyatlari uchun ob-havo + AQI",
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2025, 9, 3),
    catchup=False,
    tags=['weather', 'aqi'],
) as dag:

    for city in CITIES:
        PythonOperator(
            task_id=f"fetch_{city.lower()}",
            python_callable=fetch_and_save,
            op_args=[city],
        )
