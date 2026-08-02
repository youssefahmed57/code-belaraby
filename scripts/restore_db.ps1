# PostgreSQL Restore Script for Code Journey Academy
param (
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

if (-not (Test-Path $BackupFile)) {
    Write-Error "Backup file not found at: $BackupFile"
    exit 1
}

Write-Host "Restoring PostgreSQL database from $BackupFile..." -ForegroundColor Yellow
Get-Content $BackupFile | docker exec -i code_journey_postgres psql -U postgres -d code_journey_db
Write-Host "PostgreSQL database restored successfully!" -ForegroundColor Green
