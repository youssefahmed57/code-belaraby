#!/bin/bash
# PostgreSQL Restore Script (Linux/macOS)
if [ -z "$1" ]; then
    echo "Usage: ./restore_db.sh <backup_file.sql>"
    exit 1
fi
echo "Restoring PostgreSQL database from $1..."
docker exec -i code_journey_postgres psql -U postgres -d code_journey_db < "$1"
echo "PostgreSQL database restored successfully!"
