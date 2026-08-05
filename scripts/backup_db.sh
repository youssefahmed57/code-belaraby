#!/bin/bash
set -e

ENV=${1:-staging}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

mkdir -p $BACKUP_DIR

if [ "$ENV" = "staging" ]; then
  CONTAINER="code_journey_postgres"
  DB_NAME="code_journey_db"
  DB_USER="postgres"
else
  CONTAINER="code_journey_postgres"
  DB_NAME="code_journey_db"
  DB_USER="postgres"
fi

OUTPUT_FILE="$BACKUP_DIR/backup_${ENV}_${TIMESTAMP}.sql"

echo "Creating PostgreSQL backup for $ENV ($DB_NAME)..."
docker exec -t $CONTAINER pg_dump -U $DB_USER $DB_NAME > $OUTPUT_FILE

echo "Database backup successfully created: $OUTPUT_FILE"
