"""
Stud AI Service - FastAPI entrypoint.

Bootstraps configuration, verifies external dependencies (Supabase + optional
Redis/Pinecone), starts the periodic cleanup worker, and registers all routers.
"""
import asyncio
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth_router
from api.cleanup import router as cleanup_router
from api.game_v2 import router as game_v2_router
from api.learning import router as learning_router
from api.quiz import router as quiz_router
from api.user import router as user_router
from configs.config import config
from service.database import get_database_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _allowed_origins() -> List[str]:
    """Derive CORS origins. Defaults to '*' for dev; comma-separated env override for prod."""
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if not raw:
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def _verify_supabase() -> None:
    """Hit Supabase once, with backoff for cold-start (5xx) responses."""
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_URL and SERVICE_ROLE_KEY are required")

    db = get_database_service()
    delays = (2, 4, 8, 16, 32)
    last_err: Exception | None = None
    for attempt, delay in enumerate((0,) + delays):
        if delay:
            logger.warning("Retrying Supabase connection in %ss (attempt %s)", delay, attempt + 1)
            time.sleep(delay)
        try:
            db.client.table("users").select("id").limit(1).execute()
            logger.info("Supabase connection OK")
            return
        except Exception as e:  # pragma: no cover - depends on remote
            err = str(e)
            last_err = e
            if any(code in err for code in ("520", "521", "522", "524")):
                continue
            raise
    raise RuntimeError(f"Supabase unreachable after retries: {last_err}")


async def _verify_redis() -> None:
    if not config.REDIS_URL:
        logger.warning("REDIS_URL not set - caching/queues disabled")
        return
    try:
        import redis.asyncio as redis_async
        client = await redis_async.from_url(config.REDIS_URL)
        await client.ping()
        await client.close()
        logger.info("Redis connection OK (%s:%s)", config.REDIS_HOST, config.REDIS_PORT)
    except Exception as e:
        logger.warning("Redis unavailable (continuing without cache): %s", e)


def _ensure_dirs() -> None:
    for path in (
        getattr(config, "UPLOAD_FOLDER", "/tmp/uploads"),
        getattr(config, "IMAGE_TEMP_DIR", "/tmp/images"),
    ):
        os.makedirs(path, exist_ok=True)


async def _initialize() -> None:
    if not config.SECRET_KEY:
        raise RuntimeError("SECRET_KEY is required for JWT authentication")
    _verify_supabase()
    await _verify_redis()
    _ensure_dirs()
    if not (config.GOOGLE_API_KEY or config.OPENAI_API_KEY):
        logger.warning("No AI API keys configured - some features will be disabled")


def _configure_thread_pool() -> None:
    """Size the default asyncio thread executor for high concurrency.

    Every Supabase call goes through ``asyncio.to_thread`` so the executor's
    cap = max in-flight DB queries per worker. Default is min(32, cpu+4),
    which throttles us long before 50k concurrent users.
    """
    from concurrent.futures import ThreadPoolExecutor

    workers = int(os.getenv("DB_THREAD_POOL_SIZE", "256") or 256)
    loop = asyncio.get_running_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=workers))
    logger.info("Default thread executor sized for %s workers", workers)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _configure_thread_pool()
    await _initialize()
    from service.cleanup_service import run_cleanup_task
    cleanup_task = asyncio.create_task(run_cleanup_task())
    logger.info("Background cleanup task started")
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("Stud AI Service shutting down")


app = FastAPI(
    title="Stud AI Service",
    description="Backend API for the Stud medical education platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router, tag in (
    (auth_router, "Authentication"),
    (user_router, "User"),
    (quiz_router, "Quiz"),
    (learning_router, "Learning"),
    (game_v2_router, "Game"),
    (cleanup_router, "Cleanup"),
):
    app.include_router(router, prefix="/api", tags=[tag])


@app.get("/")
async def root():
    return {
        "message": "Stud AI Service is running",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {"docs": "/docs", "health": "/health", "api": "/api"},
    }


@app.get("/health")
async def health_check():
    try:
        client = get_database_service().client
        await asyncio.to_thread(
            lambda: client.table("users").select("id").limit(1).execute()
        )
        return {
            "status": "healthy",
            "service": "Stud AI Service",
            "database": "connected",
            "version": "1.0.0",
        }
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return {
            "status": "unhealthy",
            "service": "Stud AI Service",
            "database": "disconnected",
            "error": str(e),
        }, 503


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
