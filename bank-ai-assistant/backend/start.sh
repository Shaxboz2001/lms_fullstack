#!/bin/bash
set -e

echo "⏳ Waiting for Postgres..."
until nc -z db 5435; do
  sleep 1
done
echo "✅ Postgres is up!"

if [ ! -f /app/.seeded ]; then
  echo "🌱 Seeding database..."
  python seed_data.py
  touch /app/.seeded
else
  echo "⚡ Already seeded"
fi

echo "🚀 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
