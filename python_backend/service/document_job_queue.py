"""
Document-game job queue: Redis list in production, asyncio.Queue locally.
Workers call dequeue_document_game_job; API uses enqueue_document_game_job.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

from configs import config
from service.redis_service import get_redis_service

logger = logging.getLogger(__name__)

_USE_REDIS = os.getenv("DOCUMENT_GAME_JOBS_IN_REDIS", "1").lower() not in (
    "0",
    "false",
    "no",
)
_local: Optional[asyncio.Queue] = None


def _queue_name() -> str:
    return getattr(config, "DOCUMENT_GAME_QUEUE_KEY", "jobs:document_game") or "jobs:document_game"


def _get_local() -> asyncio.Queue:
    global _local
    if _local is None:
        _local = asyncio.Queue()
    return _local


async def enqueue_document_game_job(
    payload: Dict[str, Any],
    job_id: Optional[str] = None,
) -> str:
    job_id = job_id or f"dgj_{uuid.uuid4().hex[:16]}"
    body = json.dumps({"id": job_id, "payload": payload}, default=str)
    if _USE_REDIS:
        r = await get_redis_service()
        await r._ensure_connected()
        if r.client:
            try:
                await r.client.rpush(_queue_name(), body)
                return job_id
            except Exception as e:
                logger.warning("document_job_queue rpush: %s", e)
    await _get_local().put(body)
    return job_id


async def dequeue_document_game_job(
    block_ms: int = 5000,
) -> Optional[Dict[str, Any]]:
    if _USE_REDIS:
        r = await get_redis_service()
        await r._ensure_connected()
        if r.client:
            try:
                t = max(1, int(block_ms / 1000))
                out = await r.client.blpop(_queue_name(), timeout=t)
                if not out:
                    return None
                return json.loads(out[1])
            except Exception as e:
                logger.debug("document_job_queue blpop: %s", e)
    try:
        item = await asyncio.wait_for(
            _get_local().get(), timeout=max(0.1, block_ms / 1000.0)
        )
        return json.loads(item)
    except (asyncio.TimeoutError, json.JSONDecodeError, TypeError):
        return None
