"""
User API endpoints
Profile, statistics, recent activities, and game/quiz history.
JWT/auth helpers come from `api.auth_deps` (single source of truth).
All Supabase calls run on the default thread executor so they don't
block the FastAPI event loop under high concurrency.
"""
import asyncio
from datetime import datetime
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth_deps import get_current_user_id, invalidate_user_cache
from service.database import get_database_service

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
        raise HTTPException(status_code=500, detail=f"Failed to fetch user stats: {e}")


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
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent games: {e}")


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
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent quizzes: {e}")


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
    """Get user's API settings (AI model config)."""
    db = get_database_service()
    try:
        rows = await _to_thread(
            lambda: db.client.table("users").select("api_settings").eq("id", user_id).execute().data
        )
        if not rows:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "settings": rows[0].get("api_settings") or {}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch settings: {e}")


@router.put("/user/settings")
async def update_user_settings(
    payload: ApiSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Merge-update user's API settings."""
    db = get_database_service()
    try:
        rows = await _to_thread(
            lambda: db.client.table("users").select("api_settings").eq("id", user_id).execute().data
        )
        if not rows:
            raise HTTPException(status_code=404, detail="User not found")
        current = rows[0].get("api_settings") or {}
        updates = {k: v for k, v in payload.model_dump(exclude_none=True).items() if v is not None}
        new_settings = {**current, **updates}
        await db.update_user(user_id, {
            "api_settings": new_settings,
            "updated_at": datetime.now().isoformat(),
        })
        await invalidate_user_cache(user_id)
        return {"success": True, "settings": new_settings}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {e}")
