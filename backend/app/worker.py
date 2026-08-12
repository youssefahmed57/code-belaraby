import asyncio
import json
import logging
import time

import redis

from app.core.config import settings
from app.services.execution_service import ExecutionProviderUnavailable, ExecutionService


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("execution-worker")


def process_queue() -> None:
    logger.info("Starting execution worker...")
    redis_client = redis.Redis.from_url(settings.REDIS_URL)

    while True:
        try:
            job_data = redis_client.blpop("code_execution_queue", timeout=5)
            if not job_data:
                continue

            _, raw_payload = job_data
            payload = json.loads(raw_payload.decode("utf-8"))
            job_id = payload.get("job_id")
            language = payload.get("language")
            code = payload.get("code")
            stdin = payload.get("stdin", "")
            time_limit = payload.get("time_limit", 2.0)

            logger.info("Processing execution job %s for %s", job_id, language)
            try:
                result = asyncio.run(
                    ExecutionService.run_code(
                        language=language,
                        code=code,
                        stdin=stdin,
                        time_limit=time_limit,
                    )
                )
            except (ExecutionProviderUnavailable, RuntimeError) as exc:
                result = {
                    "status": "Internal Error",
                    "stdout": "",
                    "stderr": str(exc),
                    "execution_time_seconds": 0.0,
                    "memory_used_kb": 0,
                }

            redis_client.setex(f"job_result:{job_id}", 60, json.dumps(result))
            logger.info("Completed job %s with status %s", job_id, result.get("status"))
        except Exception as exc:
            logger.error("Worker error: %s", exc)
            time.sleep(1)


if __name__ == "__main__":
    process_queue()
