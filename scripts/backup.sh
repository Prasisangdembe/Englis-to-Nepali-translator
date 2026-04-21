#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "${BACKUP_DIR}"

DB_BACKUP_FILE="${BACKUP_DIR}/db_${TIMESTAMP}.sql"
DATA_BACKUP_FILE="${BACKUP_DIR}/data_${TIMESTAMP}.tar.gz"

echo "==> Backing up PostgreSQL database to ${DB_BACKUP_FILE}..."
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-limbu_user}" -d "${POSTGRES_DB:-limbu_db}" > "${DB_BACKUP_FILE}"

echo "==> Backing up application data directory to ${DATA_BACKUP_FILE}..."
if [ -d "${PROJECT_ROOT}/data" ]; then
  tar -czf "${DATA_BACKUP_FILE}" -C "${PROJECT_ROOT}" data
else
  echo "No data directory found; creating empty archive placeholder."
  tar -czf "${DATA_BACKUP_FILE}" --files-from /dev/null
fi

echo "==> Backup completed."
echo "Database backup: ${DB_BACKUP_FILE}"
echo "Data backup: ${DATA_BACKUP_FILE}"
