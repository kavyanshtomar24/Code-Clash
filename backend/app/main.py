"""
FastAPI application entry point.

Creates the ASGI application, registers middleware, includes versioned
routers, and runs startup tasks (database init + optional seeding).
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.middleware import RequestLoggingMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import async_session_maker, init_db
from app.websocket.battle_ws import router as ws_router

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


async def _battle_expiry_loop() -> None:
    """Background task that expires timed-out battles every 30 seconds."""
    from app.services.battle_service import check_and_expire_battles

    while True:
        try:
            async with async_session_maker() as session:
                await check_and_expire_battles(session)
        except Exception:
            logger.warning("Battle expiry check failed", exc_info=True)
        await asyncio.sleep(30)


async def _embedded_judge_worker() -> None:
    """Run judge queue consumer inside the API process (dev / single-node deploy)."""
    from app.services.judge_worker import worker_loop

    await worker_loop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hooks."""
    logger.info("Starting CP & DSA Platform API …")

    await init_db()
    logger.info("Database tables ensured")

    try:
        from app.db.seed import seed_database

        async with async_session_maker() as session:
            await seed_database(session)
    except Exception:
        logger.warning("Seed skipped or failed", exc_info=True)

    background_tasks = [
        asyncio.create_task(_battle_expiry_loop()),
    ]
    if settings.JUDGE_ENABLED and settings.JUDGE_EMBEDDED_WORKER:
        background_tasks.append(asyncio.create_task(_embedded_judge_worker()))

    yield

    for task in background_tasks:
        task.cancel()

    from app.services.cache_service import cache_service

    await cache_service.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title="CodeClash — CP & DSA Platform",
    description=(
        "Full-stack Competitive Programming & DSA practice platform "
        "with real-time battles, analytics, and Codeforces integration."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_v1_router)
app.include_router(ws_router)


@app.api_route("/", methods=["GET", "HEAD"], tags=["Health"])
async def root():
    """Health-check endpoint."""
    return {"status": "healthy", "version": "1.0.0", "service": "codeclash-api"}
