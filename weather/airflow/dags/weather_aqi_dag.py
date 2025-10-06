from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import psycopg2
import os
import logging

# API kalitlari (docker-compose.yml dagi env orqali keladi)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
AQI_API_TOKEN = os.getenv("AQI_API_TOKEN")

# Postgres ulanish sozlamalari
DB_HOST = "postgres"
DB_NAME = "weather_db"
DB_USER = "airflow"
DB_PASS = "airflow"

# Shahar nomi (xohlasangiz Toshkentni o'zgartiring)
CITY = "Tashkent"

def fetch_weather(**context):
    """OpenWeather API orqali ob-havo olish"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric&lang=uz"
    response = requests.get(url)
    data = response.json()
    logging.info(f"Weather data: {data}")

    context['ti'].xcom_push(key='weather', value=data)

def fetch_aqi(**context):
    """AQICN API orqali havo sifati olish"""
    url = f"http://api.waqi.info/feed/{CITY}/?token={AQI_API_TOKEN}"
    response = requests.get(url)
    data = response.json()
    logging.info(f"AQI data: {data}")

    context['ti'].xcom_push(key='aqi', value=data)

def save_to_postgres(**context):
    """Olingan ma’lumotlarni Postgresga yozish"""
    weather = context['ti'].xcom_pull(task_ids='fetch_weather', key='weather')
    aqi = context['ti'].xcom_pull(task_ids='fetch_aqi', key='aqi')

    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()

    temperature = weather['main']['temp']
    humidity = weather['main']['humidity']
    description = weather['weather'][0]['description']
    aqi_value = aqi['data']['aqi'] if 'data' in aqi and aqi['data'] else None

    cur.execute(
        """
        INSERT INTO weather_data (city, temperature, humidity, description, aqi, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (CITY, temperature, humidity, description, aqi_value, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()

# DAG sozlamalari
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'weather_aqi_dag',
    default_args=default_args,
    description='OpenWeather + AQI ma’lumotlarini olib Postgresga yozish',
    schedule_interval=timedelta(minutes=30),  # har 30 daqiqada ishlaydi
    start_date=datetime(2025, 9, 3),
    catchup=False,
    tags=['weather', 'aqi'],
) as dag:

    task_fetch_weather = PythonOperator(
        task_id='fetch_weather',
        python_callable=fetch_weather,
        provide_context=True,
    )

    task_fetch_aqi = PythonOperator(
        task_id='fetch_aqi',
        python_callable=fetch_aqi,
        provide_context=True,
    )

    task_save = PythonOperator(
        task_id='save_to_postgres',
        python_callable=save_to_postgres,
        provide_context=True,
    )

    [task_fetch_weather, task_fetch_aqi] >> task_save
