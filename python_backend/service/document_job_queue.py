"""
Document-game job queue: Redis list in production, asyncio.Queue locally.
Workers call dequeue_document_game_job; API uses enqueue_document_game_job.
On failure after max attempts, jobs move to the DLQ list (same Redis key + ":dlq").
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
_JOB_MAX_ATTEMPTS = max(1, int(os.getenv("DOCUMENT_GAME_JOB_MAX_ATTEMPTS", "3") or 3))
_local: Optional[asyncio.Queue] = None


def _queue_name() -> str:
    return getattr(config, "DOCUMENT_GAME_QUEUE_KEY", "jobs:document_game") or "jobs:document_game"


def _dlq_name() -> str:
    return f"{_queue_name()}:dlq"


def _get_local() -> asyncio.Queue:
    global _local
    if _local is None:
        _local = asyncio.Queue()
    return _local


def _normalize_job(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Support legacy messages that stored only {id, payload}."""
    if isinstance(raw.get("payload"), dict):
        return {
            "id": raw.get("id") or f"dgj_{uuid.uuid4().hex[:16]}",
            "payload": raw["payload"],
            "attempt": int(raw.get("attempt") or 0),
        }
    return {
        "id": raw.get("id") or f"dgj_{uuid.uuid4().hex[:16]}",
        "payload": raw,
        "attempt": int(raw.get("attempt") or 0),
    }


async def enqueue_document_game_job(
    payload: Dict[str, Any],
    job_id: Optional[str] = None,
) -> str:
    job_id = job_id or f"dgj_{uuid.uuid4().hex[:16]}"
    body = json.dumps({"id": job_id, "payload": payload, "attempt": 0}, default=str)
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
                return _normalize_job(json.loads(out[1]))
            except Exception as e:
                logger.debug("document_job_queue blpop: %s", e)
    try:
        item = await asyncio.wait_for(
            _get_local().get(), timeout=max(0.1, block_ms / 1000.0)
        )
        return _normalize_job(json.loads(item))
    except (asyncio.TimeoutError, json.JSONDecodeError, TypeError):
        return None


async def requeue_or_dead_letter(job: Dict[str, Any], error: str) -> None:
    """
    After a failed processing attempt: re-enqueue with attempt+1 or push to DLQ.
    Workers should call this in an except block.
    """
    norm = _normalize_job(job)
    attempt = int(norm.get("attempt") or 0) + 1
    payload = norm.get("payload")
    job_id = norm.get("id")
    if attempt >= _JOB_MAX_ATTEMPTS:
        body = json.dumps(
            {"id": job_id, "payload": payload, "attempt": attempt, "error": error},
            default=str,
        )
        if _USE_REDIS:
            r = await get_redis_service()
            await r._ensure_connected()
            if r.client:
                try:
                    await r.client.rpush(_dlq_name(), body)
                    return
                except Exception as e:
                    logger.warning("document_job_queue dlq rpush: %s", e)
        logger.error("document_game job dead-lettered (no Redis): id=%s err=%s", job_id, error)
        return
    body = json.dumps({"id": job_id, "payload": payload, "attempt": attempt}, default=str)
    if _USE_REDIS:
        r = await get_redis_service()
        await r._ensure_connected()
        if r.client:
            try:
                await r.client.rpush(_queue_name(), body)
                return
            except Exception as e:
                logger.warning("document_job_queue requeue rpush: %s", e)
    await _get_local().put(body)
