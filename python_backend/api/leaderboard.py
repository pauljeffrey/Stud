"""Public leaderboard: real per-user XP/game/quiz stats, ranked. No auth
required to view (matches other public read endpoints); if a JWT is present
the caller's own rank is also returned."""
import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException

from api.auth_deps import decode_jwt_user_id
from service.database import get_database_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/leaderboard")
async def get_leaderboard(
    category: str = "overall",
    period: str = "all_time",
    authorization: Optional[str] = Header(None),
):
    """category: overall|games|quizzes|learning. period is accepted but not
    yet used to window results — all rankings are all-time for now."""
    db = get_database_service()
    client = db.client
    try:
        rows = await db.list_leaderboard_rows(limit=100)
        user_ids = [r["user_id"] for r in rows if r.get("user_id")]

        game_map: Dict[str, Dict[str, Any]] = {}
        quiz_map: Dict[str, Dict[str, Any]] = {}
        if user_ids:
            def _fetch_game():
                return client.table("game_statistics").select("*").in_("user_id", user_ids).execute().data or []

            def _fetch_quiz():
                return client.table("quiz_statistics").select("*").in_("user_id", user_ids).execute().data or []

            game_rows, quiz_rows = await asyncio.gather(
                asyncio.to_thread(_fetch_game), asyncio.to_thread(_fetch_quiz)
            )
            game_map = {r["user_id"]: r for r in game_rows}
            quiz_map = {r["user_id"]: r for r in quiz_rows}

        entries = []
        for r in rows:
            uid = r.get("user_id")
            user_row = r.get("users") or {}
            gs = game_map.get(uid, {})
            qs = quiz_map.get(uid, {})
            entries.append({
                "userId": uid,
                "userName": user_row.get("name") or "Anonymous",
                "avatarUrl": user_row.get("avatar_url"),
                "score": int(r.get("experience_points") or 0),
                "level": int(r.get("level") or 1),
                "xp": int(r.get("experience_points") or 0),
                "gamesCompleted": int(gs.get("games_completed") or 0),
                "quizzesCompleted": int(qs.get("quizzes_taken") or 0),
                "averageScore": round(float(qs.get("average_score") or 0)),
            })

        if category == "games":
            entries.sort(key=lambda e: e["gamesCompleted"], reverse=True)
        elif category == "quizzes":
            entries.sort(key=lambda e: e["quizzesCompleted"], reverse=True)
        elif category == "learning":
            entries.sort(key=lambda e: e["averageScore"], reverse=True)
        else:
            entries.sort(key=lambda e: e["xp"], reverse=True)

        for i, e in enumerate(entries):
            e["rank"] = i + 1

        user_rank = None
        current_user_id = decode_jwt_user_id(authorization)
        if current_user_id:
            user_rank = next((e["rank"] for e in entries if e["userId"] == current_user_id), None)

        return {"success": True, "leaderboard": entries, "userRank": user_rank}
    except Exception:
        logger.exception("Failed to fetch leaderboard")
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard")
