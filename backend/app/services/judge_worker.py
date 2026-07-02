"""
Judge worker — consumes the Redis submission queue and evaluates code.

Run as a standalone process:
    python -m app.services.judge_worker
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

from app.config import settings
from app.services.cache_service import cache_service
from app.services.judge_service import process_submission_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


async def worker_loop() -> None:
    """Blocking consumer loop for the judge queue."""
    logger.info("Judge worker started — listening on %s", settings.JUDGE_QUEUE_KEY)
    while True:
        raw = await cache_service.brpop(settings.JUDGE_QUEUE_KEY, timeout=5)
        if not raw:
            await asyncio.sleep(0.1)
            continue
        try:
            task = json.loads(raw)
            submission_id = uuid.UUID(task["submission_id"])
            await process_submission_task(submission_id)
        except Exception:
            logger.exception("Failed to process judge task: %s", raw)


def main() -> None:
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
