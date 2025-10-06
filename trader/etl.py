import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


# =====================
# 1. Ko'rsatkichlar ro'yxati
# =====================
INDICATORS = {
    "inflation": "FP.CPI.TOTL.ZG",                 # Inflyatsiya (yillik %)
    "gdp": "NY.GDP.MKTP.CD",                       # YaIM (USD)
    "population": "SP.POP.TOTL",                   # Aholi soni
    "exports": "NE.EXP.GNFS.ZS",                   # Eksport (% of GDP)
    "imports": "NE.IMP.GNFS.ZS",                   # Import (% of GDP)
    "education": "SE.XPD.TOTL.GD.ZS",              # Ta'lim xarajatlari (% of GDP)
    "unemployment": "SL.UEM.TOTL.ZS",              # Ishsizlik (% of total labor force)
}


# =====================
# 2. API'dan ma'lumot olish
# =====================
def fetch_indicator(indicator_code, indicator_name):
    url = f"https://api.worldbank.org/v2/country/uzb/indicator/{indicator_code}?date=2000:2025&format=json&per_page=1000"
    print(f"📥 {indicator_name} ({indicator_code}) ma'lumotlarini yuklab olish...")

    res = requests.get(url)
    res.raise_for_status()
    data = res.json()

    if len(data) < 2 or data[1] is None:
        print(f"⚠️ {indicator_name} uchun ma'lumot topilmadi")
        return pd.DataFrame()

    df = pd.json_normalize(data[1])
    df = df[["date", "value"]]
    df = df.rename(columns={"value": indicator_name})
    df = df.sort_values("date")

    return df


def fetch_all_data():
    dfs = []
    for name, code in INDICATORS.items():
        df = fetch_indicator(code, name)
        if not df.empty:
            dfs.append(df.set_index("date"))

    # barcha ma'lumotlarni year bo'yicha birlashtirish
    final_df = pd.concat(dfs, axis=1).reset_index()
    final_df["year"] = final_df["date"].astype(int)
    final_df = final_df.drop(columns=["date"], errors="ignore")

    # Null qiymatlarni o'rtacha bilan to'ldirish
    final_df = final_df.sort_values("year")
    final_df = final_df.fillna(final_df.mean(numeric_only=True))

    print("✅ Barcha ma'lumotlar birlashtirildi")
    return final_df


# =====================
# 3. PostgreSQL ga yozish
# =====================
def load_to_postgres(df):
    print("💾 PostgreSQL ga yozilmoqda...")

    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="2001",
        port=5432
    )
    cur = conn.cursor()

    # jadval yaratish (agar mavjud bo'lmasa)
    # jadval yaratish (agar mavjud bo'lmasa)
    cur.execute("""
          CREATE TABLE IF NOT EXISTS worldbank_uzb (
              year INT PRIMARY KEY,
              inflation NUMERIC,
              gdp NUMERIC,
              population BIGINT,
              exports NUMERIC,
              imports NUMERIC,
              education NUMERIC,
              unemployment NUMERIC
          )
      """)

    records = [
        (
            int(row["year"]),
            float(row["inflation"]) if not pd.isna(row.get("inflation")) else None,
            float(row["gdp"]) if not pd.isna(row.get("gdp")) else None,
            int(row["population"]) if not pd.isna(row.get("population")) else None,
            float(row["exports"]) if not pd.isna(row.get("exports")) else None,
            float(row["imports"]) if not pd.isna(row.get("imports")) else None,
            float(row["education"]) if not pd.isna(row.get("education")) else None,
            float(row["unemployment"]) if not pd.isna(row.get("unemployment")) else None,
        )
        for _, row in df.iterrows()
    ]

    insert_query = """
          INSERT INTO worldbank_uzb (year, inflation, gdp, population, exports, imports, education, unemployment)
          VALUES %s
          ON CONFLICT (year) DO UPDATE SET 
              inflation = EXCLUDED.inflation,
              gdp = EXCLUDED.gdp,
              population = EXCLUDED.population,
              exports = EXCLUDED.exports,
              imports = EXCLUDED.imports,
              education = EXCLUDED.education,
              unemployment = EXCLUDED.unemployment
      """
    execute_values(cur, insert_query, records)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ PostgreSQL ga yozildi")


# =====================
# 4. Main function
# =====================
def main():
    df = fetch_all_data()

    # CSV saqlash
    df.to_csv("worldbank_uzb.csv", index=False)
    print("💾 CSV fayl yaratildi: worldbank_uzb.csv")

    # PostgreSQL ga yozish
    load_to_postgres(df)


if __name__ == "__main__":
    main()
