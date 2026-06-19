"""Shared auth helpers: JWT, password hashing, request user resolution.

Single source of truth for token verification and user lookup. At scale we cache
the resolved user object in Redis (short TTL) so endpoints that just need user
metadata avoid a Supabase round trip per request.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from configs.config import config
from service.database import get_database_service

logger = logging.getLogger(__name__)

JWT_SECRET = config.SECRET_KEY or "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

USER_CACHE_TTL = 60  # seconds; short cache to absorb burst traffic without staleness

_security = HTTPBearer(auto_error=False)


# ============================================================
# Password helpers
# ============================================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ============================================================
# JWT helpers
# ============================================================

def create_jwt_token(user_id: str, email: str, hours: int = JWT_EXPIRATION_HOURS) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=hours)
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "email": email,
        "exp": int(exp.timestamp()),
        "iat": int(now.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def decode_jwt_user_id(authorization: Optional[str]) -> Optional[str]:
    """Extract user id from a raw `Authorization: Bearer <jwt>` header (best effort)."""
    if not authorization:
        return None
    auth = authorization.strip()
    if not auth.lower().startswith("bearer "):
        return None
    payload = _decode_jwt(auth[7:].strip())
    if not payload:
        return None
    uid = payload.get("sub") or payload.get("user_id")
    return str(uid) if uid else None


def resolve_user_id(authorization: Optional[str], body_user_id: Optional[str]) -> str:
    """Prefer JWT subject; optional body user_id must match if both present."""
    jwt_uid = decode_jwt_user_id(authorization)
    if jwt_uid:
        if body_user_id and str(body_user_id).strip() and str(body_user_id) != jwt_uid:
            raise HTTPException(status_code=403, detail="user_id does not match authenticated user")
        return jwt_uid
    if body_user_id and str(body_user_id).strip():
        return str(body_user_id).strip()
    raise HTTPException(status_code=401, detail="Provide Authorization: Bearer <JWT> or user_id")


def resolve_user_id_or_query(authorization: Optional[str], query_user_id: Optional[str]) -> str:
    jwt_uid = decode_jwt_user_id(authorization)
    if jwt_uid:
        return jwt_uid
    if query_user_id and str(query_user_id).strip():
        return str(query_user_id).strip()
    raise HTTPException(status_code=401, detail="Provide Authorization: Bearer <JWT> or user_id query")


# ============================================================
# FastAPI dependencies
# ============================================================

async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
) -> str:
    """Resolve user_id from Authorization header without hitting the DB."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    payload = _decode_jwt(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    uid = payload.get("sub") or payload.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return str(uid)


async def get_current_user(user_id: str = Depends(get_current_user_id)) -> Dict[str, Any]:
    """Resolve full user row. Cached in Redis (short TTL) for high-concurrency reads."""
    cache_key = f"up:{user_id}"

    # Cache lookup (best-effort; never blocks on Redis failure)
    try:
        from service.redis_service import get_redis_service  # local import avoids cycles
        redis_service = await get_redis_service()
        cached = await redis_service.get(cache_key)
        if isinstance(cached, dict) and cached.get("id"):
            return cached
    except Exception as exc:
        logger.debug("user cache lookup skipped: %s", exc)

    db = get_database_service()
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    try:
        from service.redis_service import get_redis_service
        redis_service = await get_redis_service()
        await redis_service.set_with_ttl(cache_key, user, USER_CACHE_TTL)
    except Exception as exc:
        logger.debug("user cache write skipped: %s", exc)

    return user


async def invalidate_user_cache(user_id: str) -> None:
    """Bust the per-user Redis cache (called from login/logout/profile updates)."""
    try:
        from service.redis_service import get_redis_service
        redis_service = await get_redis_service()
        await redis_service.delete(f"up:{user_id}")
    except Exception as exc:
        logger.debug("user cache invalidate skipped: %s", exc)
