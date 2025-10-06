# Toza Havo Uzbekistan 🌍

Data Engineering portfolio project for Uzbekistan's air quality & weather monitoring.

## Components
- Airflow: ETL pipeline for collecting weather data (OpenWeather API)
- PostgreSQL: Data storage
- FastAPI: REST API
- Metabase: Dashboard/Visualization

## Run
1. Clone repo
2. Provide environment variables (you can create a `.env` file):
   ```bash
   POSTGRES_USER=weather
   POSTGRES_PASSWORD=weather
   POSTGRES_DB=weather
   WEATHER_API_KEY=your_openweather_key
   AQI_API_TOKEN=your_waqi_token
   ```
3. Start the stack with Docker:
   ```bash
   docker compose up -d --build
   ```
4. Access:
   - Airflow: `http://localhost:8082`
   - API health: `http://localhost:8000/health`
   - API weather: `http://localhost:8000/weather`
   - API AQI: `http://localhost:8000/aqi`
   - pgAdmin: `http://localhost:5050` (email: `admin@example.com`, password: `admin`)

Tables are auto-created from `db/schema.sql` on first Postgres start.

### pgAdmin orqali ulanish
1. `http://localhost:5050` oching va (email `admin@example.com`, parol `admin`) bilan kiring.
2. “Add New Server” → Connection:
   - Host name/address: `postgres`
   - Port: `5432`
   - Maintenance DB: `weather`
   - Username: `weather`
   - Password: `weather`
