# Deployment Guide

## Overview

This guide covers production-style deployment for the English to Limbu Translation System using Docker, PostgreSQL, Redis, and Gunicorn.

Core deployment artifacts:

- `Dockerfile`
- `docker-compose.yml`
- `scripts/deploy.sh`
- `scripts/backup.sh`
- `.env.example` (copy to `.env`)

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- Linux/macOS shell (or WSL on Windows) for `.sh` scripts
- Open ports:
  - `5000` (web app)
  - `5432` (PostgreSQL)
  - `6379` (Redis)

## 1) Configure Environment

Create runtime environment file:

```bash
cp .env.example .env
```

Recommended production updates:

- `DEBUG=False`
- strong `API_KEY`
- secure DB credentials
- proper `DATABASE_URL` and `REDIS_URL`
- log settings (`LOG_LEVEL`, `LOG_FILE`)

## 2) Build and Start Services

### Option A: Automated deploy script (recommended)

```bash
bash scripts/deploy.sh
```

What it does:

1. builds images
2. starts PostgreSQL + Redis
3. waits for health checks
4. runs DB init/seed script
5. starts all services
6. verifies app health endpoints

### Option B: Manual deployment

```bash
docker compose build
docker compose up -d db redis
docker compose run --rm web python scripts/init_db.py
docker compose up -d
```

## 3) Verify Deployment

Check service status:

```bash
docker compose ps
```

Check logs:

```bash
docker compose logs -f web
```

Health checks:

```bash
curl -f http://localhost:5000/
curl -f "http://localhost:5000/api/dictionary/search?q=hello"
```

## 4) Production Runtime Notes

- Web app runs via Gunicorn:
  - `gunicorn --bind 0.0.0.0:5000 api.app:app`
- For higher throughput, consider adding:
  - Gunicorn workers (e.g., `--workers 2` or higher)
  - reverse proxy (Nginx/Caddy) with TLS
  - external Redis storage for limiter + cache consistency

## 5) Database Initialization and Seeding

`scripts/init_db.py` performs:

- table creation
- dictionary seed (50+ words)
- sample parallel sentence seed

Run again safely; it skips existing seed entries.

## 6) Backup and Recovery

Create backups:

```bash
bash scripts/backup.sh
```

Backups include:

- PostgreSQL SQL dump
- `data/` archive (feedback and local runtime data)

Suggested strategy:

- daily backup job (cron/CI runner)
- upload backup artifacts to off-site storage

## 7) Scaling and Hardening Checklist

- place app behind HTTPS reverse proxy
- restrict DB/Redis network exposure
- rotate secrets and credentials
- enable centralized logs/monitoring
- configure Redis-backed Flask-Limiter storage
- set up DB migrations workflow (Alembic)
- add readiness/liveness probes in orchestrated environments

## 8) Common Operational Commands

Restart web service:

```bash
docker compose restart web
```

Rebuild web image after code changes:

```bash
docker compose build web && docker compose up -d web
```

Run tests inside local environment:

```bash
pytest
```

## 9) Troubleshooting

- App not reachable:
  - check `docker compose ps`
  - inspect `docker compose logs web`
- DB connection issues:
  - verify `DATABASE_URL`
  - ensure `db` service is healthy
- Rate-limit behavior inconsistent across replicas:
  - configure shared limiter storage in Redis
- Missing dependencies:
  - rebuild image with `docker compose build --no-cache`

## 10) Deployment Targets

### Local Machine (one command)

From project root:

```bash
bash setup.sh
```

What this does:

1. verifies Python installation
2. checks Docker availability
3. creates `.venv`
4. installs dependencies
5. initializes DB via `python main.py init-db`
6. starts app in dev mode via `python main.py run-dev`

Alternative with Make:

```bash
make install
make run
```

### Docker

Use Docker Compose:

```bash
docker compose up --build
```

Or use automated deployment:

```bash
make deploy
# or
bash scripts/deploy.sh
```

### Heroku (with Procfile)

This repo includes `Procfile`:

```text
web: gunicorn api.app:app --bind 0.0.0.0:$PORT
```

Deployment steps:

1. Install Heroku CLI and login:
   - `heroku login`
2. Create app:
   - `heroku create <your-app-name>`
3. Set required environment variables:
   - `heroku config:set DEBUG=False`
   - `heroku config:set DATABASE_URL=<your-postgres-url>`
   - `heroku config:set REDIS_URL=<your-redis-url>`
4. (Optional) provision addons:
   - `heroku addons:create heroku-postgresql:hobby-dev`
   - `heroku addons:create heroku-redis:hobby-dev`
5. Deploy:
   - `git push heroku main`
6. Initialize DB:
   - `heroku run python main.py init-db`

### AWS / Google Cloud

#### Option A: Container-based (recommended)

1. Build container image from `Dockerfile`.
2. Push to container registry:
   - AWS ECR or Google Artifact Registry
3. Deploy to managed container runtime:
   - AWS ECS/Fargate, EKS, or App Runner
   - Google Cloud Run or GKE
4. Configure environment variables (`DEBUG=False`, `DATABASE_URL`, `REDIS_URL`, etc.).
5. Use managed PostgreSQL and Redis:
   - AWS RDS + ElastiCache
   - Google Cloud SQL + Memorystore
6. Run one-time DB init task:
   - `python main.py init-db`

#### Option B: VM-based

1. Provision VM (EC2 / Compute Engine).
2. Install Docker + Docker Compose.
3. Clone repository.
4. Configure `.env`.
5. Run:
   - `docker compose up -d --build`
6. Put app behind reverse proxy (Nginx) with TLS.
