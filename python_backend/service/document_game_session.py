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

# Short prefix: was "doc_mq_sess"
_PREFIX = "dms"
_MEM: Dict[str, Dict[str, Any]] = {}

# Short field names stored in Redis:
#   did = document_id
#   ogi = ordered_game_ids
#   ci  = current_index
#   md  = mode
#   sg  = stages
#   au  = artifact_uri


def _redis_key(adventure_id: str) -> str:
    return f"{_PREFIX}:{adventure_id}"


def _expand(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Expand short field names back to descriptive names for callers."""
    return {
        "document_id":       raw.get("did", raw.get("document_id")),
        "ordered_game_ids":  raw.get("ogi", raw.get("ordered_game_ids")),
        "current_index":     raw.get("ci",  raw.get("current_index")),
        "mode":              raw.get("md",  raw.get("mode")),
        "stages":            raw.get("sg",  raw.get("stages")),
        "artifact_uri":      raw.get("au",  raw.get("artifact_uri")),
    }


async def load_mediquest_session(adventure_id: str) -> Optional[Dict[str, Any]]:
    k = _redis_key(adventure_id)
    r = await get_redis_service()
    data = await r.get(k)
    if isinstance(data, dict):
        return _expand(data)
    mem = _MEM.get(adventure_id)
    return _expand(mem) if mem else None


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
        "did": document_id,
        "ogi": list(ordered_game_ids),
        "ci":  int(current_index),
        "md":  mode or {},
        "sg":  stages or [],
        "au":  artifact_uri,
    }
    ttl = int(
        getattr(config, "DOCUMENT_GAME_JOB_REDIS_TTL", 7 * 24 * 3600) or 7 * 24 * 3600
    )
    r = await get_redis_service()
    if await r.set_with_ttl(_redis_key(adventure_id), payload, ttl):
        return True
    _MEM[adventure_id] = payload
    return True
