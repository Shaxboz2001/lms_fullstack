-- Clients jadvali
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    birth_date DATE,
    region VARCHAR(100)
);

-- Accounts jadvali
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    client_id INT REFERENCES clients(id),
    balance NUMERIC,
    open_date DATE
);

-- Transactions jadvali
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    account_id INT REFERENCES accounts(id),
    amount NUMERIC,
    date DATE,
    type VARCHAR(20)
);

-- 1 million mock yozuvlarni yaratish (Postgres generate_series yordamida)

-- Clients (100k)
INSERT INTO clients (name, birth_date, region)
SELECT
    'Client_' || g,
    DATE '1970-01-01' + (random() * 15000)::int,
    (ARRAY['Toshkent viloyati','Samarqand','Buxoro','Andijon','Namangan'])[ceil(random()*5)]
FROM generate_series(1,100000) g;

-- Accounts (300k)
INSERT INTO accounts (client_id, balance, open_date)
SELECT
    (random() * 99999 + 1)::int,
    round((random() * 1000000)::numeric, 2),
    DATE '2000-01-01' + (random() * 9000)::int
FROM generate_series(1,300000);

-- Transactions (600k)
INSERT INTO transactions (account_id, amount, date, type)
SELECT
    (random() * 299999 + 1)::int,
    round((random() * 10000)::numeric, 2),
    DATE '2015-01-01' + (random() * 3000)::int,
    (ARRAY['deposit','withdraw','transfer'])[ceil(random()*3)]
FROM generate_series(1,600000);
