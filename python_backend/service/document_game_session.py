"""
Mediquest document session cursor: ordered_game_ids, current_index, document_id, mode.
Redis with TTL when available; in-process fallback for local dev.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from configs import config
from service.redis_service import get_redis_service

logger = logging.getLogger(__name__)

_PREFIX = "doc_mq_sess"
_MEM: Dict[str, Dict[str, Any]] = {}


def _redis_key(adventure_id: str) -> str:
    return f"{_PREFIX}:{adventure_id}"


async def load_mediquest_session(adventure_id: str) -> Optional[Dict[str, Any]]:
    k = _redis_key(adventure_id)
    r = await get_redis_service()
    data = await r.get(k)
    if isinstance(data, dict):
        return data
    return _MEM.get(adventure_id)


async def save_mediquest_session(
    adventure_id: str,
    *,
    document_id: str,
    ordered_game_ids: List[str],
    current_index: int = 0,
    mode: Optional[Dict[str, Any]] = None,
    stages: Optional[List[str]] = None,
    artifact_uri: Optional[str] = None,
) -> bool:
    payload: Dict[str, Any] = {
        "document_id": document_id,
        "ordered_game_ids": list(ordered_game_ids),
        "current_index": int(current_index),
        "mode": mode or {},
        "stages": stages or [],
        "artifact_uri": artifact_uri,
    }
    ttl = int(
        getattr(config, "DOCUMENT_GAME_JOB_REDIS_TTL", 7 * 24 * 3600) or 7 * 24 * 3600
    )
    r = await get_redis_service()
    if await r.set_with_ttl(_redis_key(adventure_id), payload, ttl):
        return True
    _MEM[adventure_id] = payload
    return True
