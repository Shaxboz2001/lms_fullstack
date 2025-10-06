import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    dbname="ecommerce_db",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS market_prices (
    id SERIAL PRIMARY KEY,
    product_name TEXT,
    brand TEXT,
    category TEXT,
    price BIGINT,
    market TEXT,
    scrape_date TIMESTAMP DEFAULT NOW()
)
""")
conn.commit()

def insert_product(product):
    cursor.execute("""
        INSERT INTO market_prices (product_name, brand, category, price, market, scrape_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        product["product_name"],
        product["brand"],
        product["category"],
        product["price"],
        product["market"],
        datetime.now()
    ))
    conn.commit()

def close_db():
    cursor.close()
    conn.close()
