import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta

# ======================
# 1. Sozlamalar
# ======================
CURRENCIES = ["USD", "EUR", "RUB"]
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"

DB_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "2001",
    "port": 5432
}

# ======================
# 2. API'dan ma'lumot olish
# ======================
def fetch_currency_data(currency: str, start_date: str, end_date: str) -> pd.DataFrame:
    url = f"https://cbu.uz/uzc/arkhiv-kursov-valyut/json/{currency}/{start_date}/{end_date}/"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    # Sana formatini to‘g‘ri o‘qish
    df["date"] = pd.to_datetime(df["Date"], format="%d.%m.%Y", errors="coerce")
    df["rate"] = pd.to_numeric(df["Rate"], errors="coerce")
    df["currency"] = df["Ccy"]

    return df[["date", "currency", "rate"]]


def fetch_all_currencies():
    all_data = []
    for cur in CURRENCIES:
        df = fetch_currency_data(cur, START_DATE, END_DATE)
        if not df.empty:
            all_data.append(df)

    if not all_data:
        raise ValueError("⚠️ Hech qanday ma'lumot topilmadi!")

    final_df = pd.concat(all_data)
    final_df = final_df.sort_values(["date", "currency"]).reset_index(drop=True)
    print("✅ Barcha valyutalar yig‘ildi.")
    return final_df

# ======================
# 3. PostgreSQL ga yozish
# ======================
def save_to_postgres(df):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Jadval yaratish
    cur.execute("""
        CREATE TABLE IF NOT EXISTS currency_rates (
            date DATE,
            currency VARCHAR(10),
            rate NUMERIC,
            PRIMARY KEY (date, currency)
        )
    """)

    records = [
        (row["date"].date(), row["currency"], row["rate"])
        for _, row in df.iterrows()
    ]

    insert_query = """
        INSERT INTO currency_rates (date, currency, rate)
        VALUES %s
        ON CONFLICT (date, currency) DO UPDATE SET
            rate = EXCLUDED.rate
    """
    execute_values(cur, insert_query, records)

    conn.commit()
    cur.close()
    conn.close()
    print("💾 PostgreSQL ga yozildi.")

# ======================
# 4. Main
# ======================
def main():
    df = fetch_all_currencies()

    # CSV saqlash
    df.to_csv("currency_uzbekistan_2025.csv", index=False)
    print("💾 CSV saqlandi: currency_uzbekistan_2025.csv")

    # PostgreSQL ga yozish
    save_to_postgres(df)

if __name__ == "__main__":
    main()
