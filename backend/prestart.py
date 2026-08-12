import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("prestart")

def main():
    logger.info("Initializing database migrations and bootstrapping seed data...")
    try:
        from app.db.seed import seed_db, upgrade_schema_to_head
        upgrade_schema_to_head()
        seed_db()
        logger.info("Database bootstrap completed successfully.")
    except Exception as e:
        logger.error(f"Error during prestart database bootstrap: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
