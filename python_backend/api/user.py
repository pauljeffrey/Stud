"""
User API endpoints
Profile, statistics, recent activities, and game/quiz history.
JWT/auth helpers come from `api.auth_deps` (single source of truth).
All Supabase calls run on the default thread executor so they don't
block the FastAPI event loop under high concurrency.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.auth_deps import get_current_user_id, invalidate_user_cache
from service.database import get_database_service
from service.crypto_service import encrypt_field, decrypt_field

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_thread(fn, *args, **kwargs):
    """Shorthand for asyncio.to_thread to keep Supabase queries off the event loop."""
    return asyncio.to_thread(fn, *args, **kwargs)


@router.get("/user/stats")
async def get_user_stats(user_id: str = Depends(get_current_user_id)):
    """Get user statistics and overview."""
    db = get_database_service()
    client = db.client
    try:
        user = await db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        async def _first(table: str, default: Dict[str, Any]) -> Dict[str, Any]:
            try:
                rows = await _to_thread(
                    lambda: client.table(table).select("*").eq("user_id", user_id).execute().data
                )
                return rows[0] if rows else default
            except Exception:
                return default

        game_stats, quiz_stats, progression, achievements = await asyncio.gather(
            _first("game_statistics", {
                "games_created": 0, "games_played": 0, "games_completed": 0,
                "total_score": 0, "average_score": 0, "highest_score": 0,
            }),
            _first("quiz_statistics", {
                "quizzes_taken": 0, "quizzes_passed": 0,
                "total_score": 0, "average_score": 0, "highest_score": 0,
            }),
            _first("user_progression", {"level": 1, "experience_points": 0}),
            _to_thread(
                lambda: client.table("achievements").select("*").eq("user_id", user_id).execute().data or []
            ),
        )

        level = progression.get("level", 1)
        xp = progression.get("experience_points", 0)
        return {
            "success": True,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "profession": user.get("profession"),
            },
            "stats": {
                "totalQuests": game_stats.get("games_created", 0),
                "completedQuests": game_stats.get("games_completed", 0),
                "totalQuizzes": quiz_stats.get("quizzes_taken", 0),
                "averageScore": float(quiz_stats.get("average_score") or 0),
                "timeSpent": (game_stats.get("total_time_played", 0) or 0) // 60,
                "currentLevel": level,
                "experiencePoints": xp,
                "totalXP": xp,
                "xpToNextLevel": max(0, (level * 1000) - xp),
            },
            "achievements": achievements,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch user stats")
        raise HTTPException(status_code=500, detail="Failed to fetch user stats")


@router.get("/user/recent-games")
async def get_recent_games(
    limit: int = 5,
    user_id: str = Depends(get_current_user_id),
):
    """Get user's recent active games."""
    db = get_database_service()
    try:
        rows = await _to_thread(
            lambda: db.client.table("game_states")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
            .data or []
        )
        games = []
        for game in rows:
            state = game.get("state") or {}
            games.append({
                "id": game["id"],
                "game_id": state.get("game_id"),
                "case_id": game.get("case_id"),
                "current_case_number": state.get("current_case_number", 1),
                "total_cases": state.get("total_cases", 1),
                "created_at": game.get("created_at"),
                "updated_at": game.get("updated_at"),
                "completed_at": game.get("completed_at"),
                "is_completed": game.get("completed_at") is not None,
            })
        return {"success": True, "games": games}
    except Exception as e:
        logger.exception("Failed to fetch recent games")
        raise HTTPException(status_code=500, detail="Failed to fetch recent games")


@router.get("/user/recent-quizzes")
async def get_recent_quizzes(
    limit: int = 5,
    user_id: str = Depends(get_current_user_id),
):
    """Get user's recent quiz results."""
    db = get_database_service()
    try:
        rows = await _to_thread(
            lambda: db.client.table("quiz_results")
            .select("*, quizzes(*)")
            .eq("user_id", user_id)
            .order("completed_at", desc=True)
            .limit(limit)
            .execute()
            .data or []
        )
        quizzes = []
        for r in rows:
            quiz = r.get("quizzes") or {}
            quizzes.append({
                "id": r["id"],
                "quiz_id": r.get("quiz_id"),
                "title": quiz.get("title", "Untitled Quiz"),
                "score": r.get("score", 0),
                "time_spent": r.get("time_spent", 0),
                "completed_at": r.get("completed_at"),
            })
        return {"success": True, "quizzes": quizzes}
    except Exception as e:
        logger.exception("Failed to fetch recent quizzes")
        raise HTTPException(status_code=500, detail="Failed to fetch recent quizzes")


@router.get("/user/recent-activities")
async def get_recent_activities(
    limit: int = 10,
    user_id: str = Depends(get_current_user_id),
):
    """Mixed feed of recent games and quizzes (best-effort)."""
    db = get_database_service()
    client = db.client

    async def _games() -> List[Dict[str, Any]]:
        try:
            rows = await _to_thread(
                lambda: client.table("game_states")
                .select("id, case_id, updated_at, completed_at")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .limit(limit)
                .execute()
                .data or []
            )
            return [
                {
                    "type": "game",
                    "id": g["id"],
                    "title": f"Game: {g.get('case_id', 'Unknown Case')}",
                    "timestamp": g.get("updated_at"),
                    "completed": g.get("completed_at") is not None,
                }
                for g in rows
            ]
        except Exception:
            return []

    async def _quizzes() -> List[Dict[str, Any]]:
        try:
            rows = await _to_thread(
                lambda: client.table("quiz_results")
                .select("id, quiz_id, score, completed_at")
                .eq("user_id", user_id)
                .order("completed_at", desc=True)
                .limit(limit)
                .execute()
                .data or []
            )
        except Exception:
            return []
        if not rows:
            return []
        # Bulk-fetch quiz titles in one round trip rather than N.
        qids = list({r["quiz_id"] for r in rows if r.get("quiz_id")})
        title_map: Dict[str, str] = {}
        if qids:
            try:
                titles = await _to_thread(
                    lambda: client.table("quizzes")
                    .select("id, title")
                    .in_("id", qids)
                    .execute()
                    .data or []
                )
                title_map = {t["id"]: t.get("title", "Untitled") for t in titles}
            except Exception:
                pass
        return [
            {
                "type": "quiz",
                "id": q["id"],
                "title": f"Quiz: {title_map.get(q.get('quiz_id', ''), 'Quiz')}",
                "score": q.get("score"),
                "timestamp": q.get("completed_at"),
                "completed": True,
            }
            for q in rows
        ]

    games, quizzes = await asyncio.gather(_games(), _quizzes())
    activities = [*games, *quizzes]
    activities.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return {"success": True, "activities": activities[:limit]}


class ApiSettingsUpdate(BaseModel):
    provider: Optional[str] = None
    modelName: Optional[str] = None
    apiKey: Optional[str] = None


@router.get("/user/settings")
async def get_user_settings(user_id: str = Depends(get_current_user_id)):
    """Get user's API settings (AI model config). API key is decrypted before returning."""
    db = get_database_service()
    try:
        rows = await _to_thread(
            lambda: db.client.table("users").select("api_settings").eq("id", user_id).execute().data
        )
        if not rows:
            raise HTTPException(status_code=404, detail="User not found")
        settings: dict = dict(rows[0].get("api_settings") or {})
        # Decrypt API key before returning to the client
        if settings.get("apiKey"):
            settings["apiKey"] = decrypt_field(settings["apiKey"])
        return {"success": True, "settings": settings}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch settings")
        raise HTTPException(status_code=500, detail="Failed to fetch settings")


@router.put("/user/settings")
async def update_user_settings(
    payload: ApiSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Merge-update user's API settings. API key is encrypted before storage."""
    db = get_database_service()
    try:
        rows = await _to_thread(
            lambda: db.client.table("users").select("api_settings").eq("id", user_id).execute().data
        )
        if not rows:
            raise HTTPException(status_code=404, detail="User not found")
        current = rows[0].get("api_settings") or {}
        updates = {k: v for k, v in payload.model_dump(exclude_none=True).items() if v is not None}
        # Encrypt the API key before merging into storage
        if "apiKey" in updates and updates["apiKey"]:
            updates["apiKey"] = encrypt_field(updates["apiKey"])
        new_settings = {**current, **updates}
        await db.update_user(user_id, {
            "api_settings": new_settings,
            "updated_at": datetime.now().isoformat(),
        })
        await invalidate_user_cache(user_id)
        # Return decrypted settings to the client
        display_settings = dict(new_settings)
        if display_settings.get("apiKey"):
            display_settings["apiKey"] = decrypt_field(display_settings["apiKey"])
        return {"success": True, "settings": display_settings}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update settings")
        raise HTTPException(status_code=500, detail="Failed to update settings")


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    profession: Optional[str] = None
    bio: Optional[str] = None
    age: Optional[int] = None
    email: Optional[str] = None


_PROFILE_PUBLIC_FIELDS = ("id", "email", "name", "profession", "age", "avatar_url", "bio", "created_at")


@router.put("/user/profile")
async def update_profile(payload: ProfileUpdate, user_id: str = Depends(get_current_user_id)):
    """Update editable profile fields."""
    db = get_database_service()
    try:
        updates = payload.model_dump(exclude_none=True)
        if updates:
            updates["updated_at"] = datetime.now().isoformat()
            try:
                await db.update_user(user_id, updates)
            except Exception as e:
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    raise HTTPException(status_code=400, detail="That email is already in use")
                raise
            await invalidate_user_cache(user_id)

        user = await db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "user": {k: user.get(k) for k in _PROFILE_PUBLIC_FIELDS}}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update profile")
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.get("/user/achievements")
async def get_achievements(user_id: str = Depends(get_current_user_id)):
    """Real achievements: each definition's criteria checked against the
    user's current stats. Newly-met criteria are persisted to
    user_achievements so unlocked_at stays stable across requests."""
    db = get_database_service()
    try:
        defs, game_stats, quiz_stats, progression, docs, unlocks = await asyncio.gather(
            db.list_achievement_definitions(),
            db.get_game_statistics(user_id),
            db.get_quiz_statistics(user_id),
            db.get_user_progression(user_id),
            db.get_user_documents(user_id, limit=1000),
            db.get_user_achievement_unlocks(user_id),
        )
        game_stats = game_stats or {}
        quiz_stats = quiz_stats or {}
        progression = progression or {}

        stats = {
            "games_completed": int(game_stats.get("games_completed") or 0),
            "games_created": int(game_stats.get("games_created") or 0),
            "quizzes_taken": int(quiz_stats.get("quizzes_taken") or 0),
            "quizzes_passed": int(quiz_stats.get("quizzes_passed") or 0),
            "quiz_highest_score": float(quiz_stats.get("highest_score") or 0),
            "total_learning_hours": float(progression.get("total_learning_hours") or 0),
            "documents_uploaded": len(docs),
        }

        result = []
        for d in defs:
            criteria = d.get("criteria") or {}
            metric = criteria.get("metric")
            threshold = criteria.get("threshold", 1)
            current_value = stats.get(metric, 0)
            now_unlocked = current_value >= threshold

            existing = unlocks.get(d["id"])
            was_unlocked = bool(existing and existing.get("unlocked"))
            earned_at = existing.get("unlocked_at") if existing else None

            if now_unlocked and not was_unlocked:
                earned_at = datetime.now().isoformat()
                try:
                    await db.upsert_user_achievement_unlock(
                        user_id, d["id"], {"value": current_value}, True
                    )
                except Exception:
                    logger.warning("Failed to persist achievement unlock %s for %s", d["id"], user_id)

            result.append({
                "id": d["id"],
                "name": d["name"],
                "description": d["description"],
                "icon": d["icon"],
                "earned": now_unlocked,
                "earnedAt": earned_at,
                "rarity": d.get("rarity", "common"),
                "category": d.get("category", "game"),
                "points": d.get("points", 0),
                "progress": None if now_unlocked else min(current_value, threshold),
                "maxProgress": None if now_unlocked else threshold,
            })

        return result
    except Exception:
        logger.exception("Failed to fetch achievements")
        raise HTTPException(status_code=500, detail="Failed to fetch achievements")


@router.get("/user/analytics")
async def get_analytics(
    time_range: str = Query("30d", alias="range"),
    user_id: str = Depends(get_current_user_id),
):
    """Real usage analytics from game_statistics/quiz_statistics/user_progression,
    plus date-windowed activity counts. `range` currently only affects nothing
    in the lifetime totals (those are always all-time); weekly/monthly buckets
    are always computed for their respective fixed windows."""
    db = get_database_service()
    client = db.client
    try:
        game_stats, quiz_stats, progression, docs = await asyncio.gather(
            db.get_game_statistics(user_id),
            db.get_quiz_statistics(user_id),
            db.get_user_progression(user_id),
            db.get_user_documents(user_id, limit=1000),
        )
        game_stats = game_stats or {}
        quiz_stats = quiz_stats or {}
        progression = progression or {}

        now = datetime.now()
        week_ago = (now - timedelta(days=7)).isoformat()
        month_ago = (now - timedelta(days=30)).isoformat()

        async def _rows_since(table: str, ts_col: str, since_iso: str) -> List[Dict[str, Any]]:
            try:
                return await _to_thread(
                    lambda: client.table(table).select(ts_col)
                    .eq("user_id", user_id).gte(ts_col, since_iso).execute().data or []
                )
            except Exception:
                return []

        week_games, week_quizzes, month_games, month_quizzes = await asyncio.gather(
            _rows_since("game_creation_log", "created_at", week_ago),
            _rows_since("quiz_results", "completed_at", week_ago),
            _rows_since("game_creation_log", "created_at", month_ago),
            _rows_since("quiz_results", "completed_at", month_ago),
        )

        try:
            recent_results = await _to_thread(
                lambda: client.table("quiz_results")
                .select("total_score, completed_at")
                .eq("user_id", user_id)
                .order("completed_at", desc=True)
                .limit(7)
                .execute().data or []
            )
        except Exception:
            recent_results = []
        score_trend = [
            round(float(r.get("total_score") or 0) * 10) for r in reversed(recent_results)
        ] or [0]

        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        activity_by_day = []
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            games_count = sum(1 for g in week_games if str(g.get("created_at") or "").startswith(day_str))
            quizzes_count = sum(1 for q in week_quizzes if str(q.get("completed_at") or "").startswith(day_str))
            activity_by_day.append({
                "day": day_labels[day.weekday()],
                "games": games_count,
                "quizzes": quizzes_count,
                "learning": 0,
            })

        return {
            "totalGames": int(game_stats.get("games_created") or 0),
            "totalQuizzes": int(quiz_stats.get("quizzes_taken") or 0),
            "totalLearningHours": float(progression.get("total_learning_hours") or 0),
            "averageScore": round(float(quiz_stats.get("average_score") or 0)),
            "gamesCreated": int(game_stats.get("games_created") or 0),
            "gamesPlayed": int(game_stats.get("games_played") or 0),
            "gamesCompleted": int(game_stats.get("games_completed") or 0),
            "quizzesTaken": int(quiz_stats.get("quizzes_taken") or 0),
            "quizzesPassed": int(quiz_stats.get("quizzes_passed") or 0),
            "documentsUploaded": len(docs),
            "apiRequests": 0,
            "weeklyStats": {"games": len(week_games), "quizzes": len(week_quizzes), "learningHours": 0},
            "monthlyStats": {"games": len(month_games), "quizzes": len(month_quizzes), "learningHours": 0},
            "scoreTrend": score_trend,
            "activityByDay": activity_by_day,
        }
    except Exception:
        logger.exception("Failed to fetch analytics")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")
