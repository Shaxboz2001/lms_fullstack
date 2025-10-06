import os
import random
from faker import Faker
import psycopg2

fake = Faker()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME", "bank_db"),
    user=os.getenv("DB_USER", "bank_user"),
    password=os.getenv("DB_PASS", "password123"),
    host=os.getenv("DB_HOST", "db"),
    port=5432,
)
cur = conn.cursor()

print("🌱 Generating data...")

# Clients
for _ in range(1000):
    cur.execute(
        "INSERT INTO clients (name, birth_date, region) VALUES (%s, %s, %s)",
        (fake.name(), fake.date_of_birth(minimum_age=18, maximum_age=80), fake.city())
    )

# Accounts
cur.execute("SELECT id FROM clients")
client_ids = [row[0] for row in cur.fetchall()]
for client_id in client_ids:
    for _ in range(random.randint(1, 3)):
        cur.execute(
            "INSERT INTO accounts (client_id, balance, open_date) VALUES (%s, %s, %s)",
            (client_id, round(random.uniform(100, 10000), 2), fake.date_this_decade())
        )

# Transactions
cur.execute("SELECT id FROM accounts")
account_ids = [row[0] for row in cur.fetchall()]
for account_id in account_ids:
    for _ in range(random.randint(10, 30)):
        cur.execute(
            "INSERT INTO transactions (account_id, amount, date, type) VALUES (%s, %s, %s, %s)",
            (account_id, round(random.uniform(-500, 5000), 2), fake.date_this_year(), random.choice(["deposit", "withdrawal"]))
        )

conn.commit()
cur.close()
conn.close()
print("✅ Data seeding completed!")
