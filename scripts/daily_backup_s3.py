import os
import sys
import subprocess
import datetime
import logging
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")
RETENTION_DAYS = 7

def run_daily_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"code_belaraby_db_{today_str}.dump"
    backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

    logging.info(f"Starting PostgreSQL backup to {backup_filepath}...")

    # Build pg_dump command from SYNC_DATABASE_URL or DATABASE_URL
    db_url = settings.SYNC_DATABASE_URL or settings.DATABASE_URL
    if db_url.startswith("sqlite"):
        logging.info("SQLite database detected; creating file copy backup.")
        sqlite_file = db_url.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
        backup_filepath = os.path.join(BACKUP_DIR, f"code_belaraby_sqlite_{today_str}.db")
        if os.path.exists(sqlite_file):
            import shutil
            shutil.copy2(sqlite_file, backup_filepath)
            logging.info(f"SQLite backup completed: {backup_filepath}")
            return backup_filepath
        else:
            logging.error(f"SQLite file {sqlite_file} not found.")
            return None

    cmd = ["pg_dump", db_url, "-F", "c", "-b", "-v", "-f", backup_filepath]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info(f"pg_dump completed successfully. Backup file size: {os.path.getsize(backup_filepath)} bytes")
    except Exception as e:
        logging.error(f"Failed to create pg_dump: {e}")
        return None

    # Upload to S3 / Cloudflare R2 if credentials are provided
    if settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY and settings.S3_ENDPOINT_URL:
        try:
            import boto3
            s3 = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY
            )
            s3_key = f"daily_backups/{backup_filename}"
            s3.upload_file(backup_filepath, settings.S3_BUCKET_NAME, s3_key)
            logging.info(f"Uploaded backup to S3 bucket '{settings.S3_BUCKET_NAME}' at '{s3_key}'")
        except Exception as e:
            logging.error(f"S3 backup upload error: {e}")

    # Retention cleanup (Delete backups older than 7 days)
    now_ts = datetime.datetime.now().timestamp()
    for f in os.listdir(BACKUP_DIR):
        fpath = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(fpath):
            file_age_days = (now_ts - os.path.getmtime(fpath)) / 86400
            if file_age_days > RETENTION_DAYS:
                os.remove(fpath)
                logging.info(f"Purged old backup file: {f}")

    return backup_filepath

if __name__ == "__main__":
    run_daily_backup()
