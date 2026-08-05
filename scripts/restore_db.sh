#!/bin/bash
set -e

BACKUP_FILE=$1
ENV=${2:-staging}

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: ./scripts/restore_db.sh <path_to_sql_file> [environment]"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file '$BACKUP_FILE' does not exist."
  exit 1
fi

CONTAINER="code_journey_postgres"
DB_NAME="code_journey_db"
DB_USER="postgres"

echo "=== WARNING: Restoring database will overwrite current database $DB_NAME in $ENV ==="
read -p "Are you sure you want to proceed? (y/N) " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "Restoration cancelled."
  exit 0
fi

echo "Restoring database from $BACKUP_FILE..."
cat $BACKUP_FILE | docker exec -i $CONTAINER psql -U $DB_USER -d $DB_NAME

echo "=== Database Restore Complete! ==="
