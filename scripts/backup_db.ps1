# PostgreSQL Backup Script for Code Journey Academy
param (
    [string]$BackupFile = "code_journey_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
)

Write-Host "Creating PostgreSQL backup from Docker container..." -ForegroundColor Green
docker exec code_journey_postgres pg_dump -U postgres -d code_journey_db -F p > $BackupFile
Write-Host "Backup created successfully at: $BackupFile" -ForegroundColor Cyan
