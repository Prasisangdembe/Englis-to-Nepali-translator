#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_ROOT}"

echo "==> Checking Python installation..."
if ! command -v python >/dev/null 2>&1; then
  echo "Python is not installed or not in PATH."
  exit 1
fi
python --version

echo "==> Checking Docker installation..."
if command -v docker >/dev/null 2>&1; then
  docker --version || true
else
  echo "Docker not found. Local Python run will still work."
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "Docker Compose detected."
else
  echo "Docker Compose not detected. Skipping container checks."
fi

echo "==> Creating virtual environment..."
python -m venv .venv

echo "==> Installing dependencies..."
if [ -f ".venv/bin/activate" ]; then
  # Linux/macOS
  source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
  # Windows Git Bash / similar
  source .venv/Scripts/activate
else
  echo "Could not find virtual environment activate script."
  exit 1
fi

pip install --upgrade pip
pip install -r requirements.txt

echo "==> Initializing database..."
python main.py init-db

echo "==> Starting application in development mode..."
python main.py run-dev
