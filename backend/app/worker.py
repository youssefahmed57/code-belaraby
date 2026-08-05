import os
import json
import time
import redis
import logging
from app.core.config import settings
from app.services.execution_service import ExecutionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("execution-worker")

def process_queue():
    logger.info("Starting Execution Worker connected to Redis...")
    redis_client = redis.Redis.from_url(settings.REDIS_URL)

    while True:
        try:
            # BLPOP blocks until a job arrives on 'code_execution_queue'
            job_data = redis_client.blpop("code_execution_queue", timeout=5)
            if not job_data:
                continue

            queue_name, raw_payload = job_data
            payload = json.loads(raw_payload.decode("utf-8"))
            job_id = payload.get("job_id")
            language = payload.get("language")
            code = payload.get("code")
            stdin = payload.get("stdin", "")
            time_limit = payload.get("time_limit", 2.0)

            logger.info(f"Processing execution job {job_id} for language: {language}")
            result = ExecutionService.run_code_sync(
                language=language,
                code=code,
                stdin=stdin,
                time_limit=time_limit
            )

            # Store result in Redis for 60 seconds
            redis_client.setex(f"job_result:{job_id}", 60, json.dumps(result))
            logger.info(f"Completed job {job_id} with status: {result.get('status')}")

        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    process_queue()
