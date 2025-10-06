import requests
import pandas as pd
from sqlalchemy import create_engine, text
from statsmodels.tsa.arima.model import ARIMA

# 🔗 Postgres ulanish
DB_URL = "postgresql+psycopg2://postgres:2001@localhost:5432/postgres"
engine = create_engine(DB_URL)


# 📥 Markaziy Bank API’dan ma’lumot olish
def fetch_cbu(currency="USD", start="2025-01-01", end="2025-09-01"):
    url = f"https://cbu.uz/uzc/arkhiv-kursov-valyut/json/{currency}/{start}/{end}/"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return []


# 💾 Postgres’ga yozish
def save_to_postgres(data, currency):
    df = pd.DataFrame(data)
    if df.empty:
        print(f"[INFO] {currency} uchun yangi ma’lumot yo‘q.")
        return

    df["date"] = pd.to_datetime(df["Date"], format="%d.%m.%Y")
    df["value"] = df["Rate"].astype(float)
    df["currency"] = currency  # 🔑 currency ustuni qo‘shildi

    df = df[["date", "value", "currency"]]

    # append qilamiz
    df.to_sql("exchange_rates", engine, if_exists="append", index=False)
    print(f"💾 {currency} uchun ma’lumot saqlandi.")


# 📤 Postgres’dan o‘qish
def load_from_postgres(currency="USD"):
    query = text("""
        SELECT date, value, currency
        FROM exchange_rates
        WHERE currency = :cur
        ORDER BY date
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"cur": currency}, parse_dates=["date"])
    return df


# 📈 ARIMA bilan prognoz
def forecast(df, steps=7):
    model = ARIMA(df["value"], order=(2, 1, 2))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=steps)
    return forecast


# 🔄 To‘liq jarayon
def run_forecast(currency="USD"):
    print(f"▶️ {currency} uchun ma’lumot olinmoqda...")
    try:
        df = load_from_postgres(currency)
        if df.empty:
            print(f"[WARN] {currency} bo‘yicha ma’lumot topilmadi.")
            return None
        preds = forecast(df)
        print(f"✅ {currency} prognoz: {preds.tolist()}")
        return preds
    except Exception as e:
        print(f"[WARN] {currency} bilan ishlashda xato: {e}")
        return None


if __name__ == "__main__":
    print("=== Valyuta prognoz boshlanmoqda ===")

    # Agar jadval bo‘sh bo‘lsa, avval ma’lumot yig‘amiz
    for cur in ["USD", "EUR", "RUB"]:
        data = fetch_cbu(cur, "2025-01-01", "2025-09-01")
        save_to_postgres(data, cur)

    # Prognoz
    for cur in ["USD", "EUR", "RUB"]:
        run_forecast(cur)

    print("=== Tugadi ===")
