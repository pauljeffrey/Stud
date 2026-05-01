"""
Authentication API endpoints
Handles user registration, login, session management, and password reset.

All Supabase queries are dispatched via ``asyncio.to_thread`` so the event loop
stays free for other requests; this is the hottest path under high concurrency.
JWT/password helpers and user resolution live in `api.auth_deps`.
"""
import asyncio
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, field_validator

from api.auth_deps import (
    JWT_EXPIRATION_HOURS,
    create_jwt_token,
    get_current_user,
    hash_password,
    invalidate_user_cache,
    verify_password,
)
from service.database import get_database_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# Schemas
# ============================================================
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    user_type: Optional[str] = None  # 'professional' | 'student'
    profession: Optional[str] = None
    profession_other: Optional[str] = None
    age: Optional[int] = None

    @field_validator("age", mode="before")
    @classmethod
    def coerce_age(cls, v):
        if v is None or v == "" or (isinstance(v, str) and not v.strip()):
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v

    @field_validator("profession", "user_type", "profession_other", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


# ============================================================
# Helpers
# ============================================================
def _now() -> str:
    return datetime.now().isoformat()


def _public_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "profession": user.get("profession"),
        "user_type": user.get("user_type"),
        "age": user.get("age"),
        "avatar_url": user.get("avatar_url"),
        "bio": user.get("bio"),
    }


async def _create_session(client, user_id: str) -> str:
    """Persist a session row off the event loop and return the opaque token."""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(hours=JWT_EXPIRATION_HOURS)).isoformat()
    payload = {
        "user_id": user_id,
        "session_token": token,
        "expires_at": expires_at,
        "created_at": _now(),
    }
    await asyncio.to_thread(
        lambda: client.table("user_sessions").insert(payload).execute()
    )
    return token


# ============================================================
# Routes
# ============================================================
@router.post("/auth/register")
async def register(request: RegisterRequest):
    db = get_database_service()
    client = db.client
    try:
        existing = await asyncio.to_thread(
            lambda: client.table("users").select("id").eq("email", request.email).execute().data
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        profession_value = (
            (request.profession_other or request.profession)
            if request.profession == "other"
            else request.profession
        )

        user_id = str(uuid.uuid4())
        user_data: Dict[str, Any] = {
            "id": user_id,
            "email": request.email,
            "password_hash": hash_password(request.password),
            "name": request.name,
            "age": request.age,
            "created_at": _now(),
            "updated_at": _now(),
        }
        if request.user_type:
            user_data["user_type"] = request.user_type
        if profession_value:
            user_data["profession"] = profession_value

        result = await asyncio.to_thread(
            lambda: client.table("users").insert(user_data).execute().data
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create user")

        # Companion rows (best-effort; failures must not block signup).
        async def _seed(table: str, payload: Dict[str, Any]) -> None:
            try:
                await asyncio.to_thread(
                    lambda: client.table(table).insert(payload).execute()
                )
            except Exception as e:
                logger.warning("init %s row failed for %s: %s", table, user_id, e)

        await asyncio.gather(
            _seed("user_progression", {"user_id": user_id, "level": 1, "experience_points": 0}),
            _seed("game_statistics", {"user_id": user_id, "games_created": 0, "games_played": 0}),
            _seed("quiz_statistics", {"user_id": user_id, "quizzes_taken": 0, "quizzes_passed": 0}),
        )

        token = create_jwt_token(user_id, request.email)
        session_token = await _create_session(client, user_id)

        return {
            "success": True,
            "message": "User registered successfully",
            "user": {
                "id": user_id,
                "email": request.email,
                "name": request.name,
                "user_type": request.user_type,
                "profession": profession_value,
            },
            "token": token,
            "session_token": session_token,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Registration failed")
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")


@router.post("/auth/login")
async def login(request: LoginRequest):
    db = get_database_service()
    client = db.client
    try:
        rows = await asyncio.to_thread(
            lambda: client.table("users").select("*").eq("email", request.email).execute().data
        )
        if not rows:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user = rows[0]
        # bcrypt verification is CPU-bound; keep it off the event loop too.
        if not await asyncio.to_thread(verify_password, request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Account is deactivated")

        user_id = user["id"]
        await asyncio.to_thread(
            lambda: client.table("users")
            .update({"last_login": _now()})
            .eq("id", user_id)
            .execute()
        )
        await invalidate_user_cache(user_id)

        token = create_jwt_token(user_id, request.email)
        session_token = await _create_session(client, user_id)

        return {
            "success": True,
            "message": "Login successful",
            "user": _public_user(user),
            "token": token,
            "session_token": session_token,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Login failed")
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")


@router.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    db = get_database_service()
    try:
        user_id = current_user["id"]
        await asyncio.to_thread(
            lambda: db.client.table("user_sessions").delete().eq("user_id", user_id).execute()
        )
        await invalidate_user_cache(user_id)
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {e}")


@router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {"success": True, "user": _public_user(current_user)}


@router.post("/auth/password-reset")
async def request_password_reset(request: PasswordResetRequest):
    db = get_database_service()
    client = db.client
    try:
        rows = await asyncio.to_thread(
            lambda: client.table("users").select("id").eq("email", request.email).execute().data
        )
        if not rows:
            return {"success": True, "message": "If email exists, reset link has been sent"}

        user_id = rows[0]["id"]
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        await asyncio.to_thread(
            lambda: client.table("users")
            .update(
                {
                    "password_reset_token": reset_token,
                    "password_reset_expires": expires_at.isoformat(),
                }
            )
            .eq("id", user_id)
            .execute()
        )
        # TODO: send email with reset link in production.
        return {
            "success": True,
            "message": "If email exists, reset link has been sent",
            "token": reset_token,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset request failed: {e}")


@router.post("/auth/password-reset/confirm")
async def confirm_password_reset(request: PasswordResetConfirm):
    db = get_database_service()
    client = db.client
    try:
        rows = await asyncio.to_thread(
            lambda: client.table("users")
            .select("*")
            .eq("password_reset_token", request.token)
            .execute()
            .data
        )
        if not rows:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")

        user = rows[0]
        if user.get("password_reset_expires"):
            expires_at = datetime.fromisoformat(
                user["password_reset_expires"].replace("Z", "+00:00")
            )
            if datetime.now(expires_at.tzinfo) > expires_at:
                raise HTTPException(status_code=400, detail="Reset token has expired")

        new_hash = await asyncio.to_thread(hash_password, request.new_password)
        await asyncio.to_thread(
            lambda: client.table("users")
            .update(
                {
                    "password_hash": new_hash,
                    "password_reset_token": None,
                    "password_reset_expires": None,
                    "updated_at": _now(),
                }
            )
            .eq("id", user["id"])
            .execute()
        )
        await invalidate_user_cache(user["id"])

        return {"success": True, "message": "Password reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {e}")
