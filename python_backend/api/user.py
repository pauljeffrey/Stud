"""
User API endpoints
Handles user profile, statistics, recent activities, and game/quiz history
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from supabase import create_client, Client

from config import config

router = APIRouter()
security = HTTPBearer()

# Initialize Supabase client
supabase: Client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_SERVICE_ROLE_KEY
)

# JWT settings (should match auth.py)
JWT_SECRET = config.SECRET_KEY or "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"


def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract user ID from JWT token"""
    token = credentials.credentials
    payload = verify_jwt_token(token)
    return payload["user_id"]


@router.get("/user/stats")
async def get_user_stats(user_id: str = Depends(get_current_user_id)):
    """Get user statistics and overview"""
    try:
        # Get user info
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = user_result.data[0]
        
        # Get game statistics
        game_stats_result = supabase.table("game_statistics").select("*").eq("user_id", user_id).execute()
        game_stats = game_stats_result.data[0] if game_stats_result.data else {
            "games_created": 0,
            "games_played": 0,
            "games_completed": 0,
            "total_score": 0,
            "average_score": 0,
            "highest_score": 0,
        }
        
        # Get quiz statistics
        quiz_stats_result = supabase.table("quiz_statistics").select("*").eq("user_id", user_id).execute()
        quiz_stats = quiz_stats_result.data[0] if quiz_stats_result.data else {
            "quizzes_taken": 0,
            "quizzes_passed": 0,
            "total_score": 0,
            "average_score": 0,
            "highest_score": 0,
        }
        
        # Get user progression
        progression_result = supabase.table("user_progression").select("*").eq("user_id", user_id).execute()
        progression = progression_result.data[0] if progression_result.data else {
            "level": 1,
            "experience_points": 0,
        }
        
        # Get achievements
        achievements_result = supabase.table("achievements").select("*").eq("user_id", user_id).execute()
        achievements = achievements_result.data or []
        
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
                "averageScore": float(quiz_stats.get("average_score", 0)) if quiz_stats.get("average_score") else 0,
                "timeSpent": game_stats.get("total_time_played", 0) // 60,  # Convert to minutes
                "currentLevel": progression.get("level", 1),
                "experiencePoints": progression.get("experience_points", 0),
                "totalXP": progression.get("experience_points", 0),
                "xpToNextLevel": max(0, (progression.get("level", 1) * 1000) - progression.get("experience_points", 0)),
            },
            "achievements": achievements,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user stats: {str(e)}")


@router.get("/user/recent-games")
async def get_recent_games(
    limit: int = 5,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's recent game states"""
    try:
        result = supabase.table("game_states")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .order("updated_at", desc=True)\
            .limit(limit)\
            .execute()
        
        games = []
        for game in result.data or []:
            state = game.get("state", {})
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
        
        return {
            "success": True,
            "games": games,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent games: {str(e)}")


@router.get("/user/recent-quizzes")
async def get_recent_quizzes(
    limit: int = 5,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's recent quiz results"""
    try:
        result = supabase.table("quiz_results")\
            .select("*, quizzes(*)")\
            .eq("user_id", user_id)\
            .order("completed_at", desc=True)\
            .limit(limit)\
            .execute()
        
        quizzes = []
        for quiz_result in result.data or []:
            quiz = quiz_result.get("quizzes", {})
            quizzes.append({
                "id": quiz_result["id"],
                "quiz_id": quiz_result.get("quiz_id"),
                "title": quiz.get("title", "Untitled Quiz"),
                "score": quiz_result.get("score", 0),
                "time_spent": quiz_result.get("time_spent", 0),
                "completed_at": quiz_result.get("completed_at"),
            })
        
        return {
            "success": True,
            "quizzes": quizzes,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent quizzes: {str(e)}")


@router.get("/user/recent-activities")
async def get_recent_activities(
    limit: int = 10,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's recent activities (games, quizzes, documents)"""
    try:
        activities = []
        
        # Get recent games
        games_result = supabase.table("game_states")\
            .select("id, case_id, updated_at, completed_at, is_active")\
            .eq("user_id", user_id)\
            .order("updated_at", desc=True)\
            .limit(limit)\
            .execute()
        
        for game in games_result.data or []:
            activities.append({
                "type": "game",
                "id": game["id"],
                "title": f"Game: {game.get('case_id', 'Unknown Case')}",
                "timestamp": game.get("updated_at"),
                "completed": game.get("completed_at") is not None,
            })
        
        # Get recent quiz results
        quizzes_result = supabase.table("quiz_results")\
            .select("id, quiz_id, score, completed_at, quizzes(title)")\
            .eq("user_id", user_id)\
            .order("completed_at", desc=True)\
            .limit(limit)\
            .execute()
        
        for quiz in quizzes_result.data or []:
            quiz_data = quiz.get("quizzes", {})
            activities.append({
                "type": "quiz",
                "id": quiz["id"],
                "title": f"Quiz: {quiz_data.get('title', 'Untitled')}",
                "score": quiz.get("score"),
                "timestamp": quiz.get("completed_at"),
                "completed": True,
            })
        
        # Sort by timestamp and limit
        activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        activities = activities[:limit]
        
        return {
            "success": True,
            "activities": activities,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent activities: {str(e)}")
