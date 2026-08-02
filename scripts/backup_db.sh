#!/bin/bash
# PostgreSQL Backup Script (Linux/macOS)
BACKUP_FILE="code_journey_backup_$(date +%Y%m%d_%H%M%S).sql"
echo "Creating PostgreSQL backup..."
docker exec code_journey_postgres pg_dump -U postgres -d code_journey_db > "$BACKUP_FILE"
echo "Backup created at $BACKUP_FILE"
