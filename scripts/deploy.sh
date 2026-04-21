#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "==> Building Docker images..."
docker compose build

echo "==> Starting database and cache services..."
docker compose up -d db redis

echo "==> Waiting for PostgreSQL to become healthy..."
for i in {1..30}; do
  if docker compose exec -T db pg_isready -U "${POSTGRES_USER:-limbu_user}" -d "${POSTGRES_DB:-limbu_db}" >/dev/null 2>&1; then
    echo "PostgreSQL is healthy."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "PostgreSQL health check failed."
    exit 1
  fi
  sleep 2
done

echo "==> Waiting for Redis to become healthy..."
for i in {1..30}; do
  if docker compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "Redis is healthy."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Redis health check failed."
    exit 1
  fi
  sleep 2
done

echo "==> Running database migrations/init script..."
docker compose run --rm web python scripts/init_db.py

echo "==> Starting all services..."
docker compose up -d

echo "==> Running application health checks..."
for i in {1..30}; do
  if curl -fsS "http://localhost:5000/" >/dev/null && curl -fsS "http://localhost:5000/api/dictionary/search?q=hello" >/dev/null; then
    echo "Application health checks passed."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Application health checks failed."
    docker compose logs web --tail=100
    exit 1
  fi
  sleep 2
done

echo "==> Deployment completed successfully."
