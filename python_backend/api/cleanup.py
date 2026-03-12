"""
Cleanup API endpoints
For manual cleanup triggers and monitoring
"""
from fastapi import APIRouter, BackgroundTasks
from service.cleanup_service import get_cleanup_service

router = APIRouter()


@router.post("/cleanup/documents")
async def cleanup_expired_documents(background_tasks: BackgroundTasks):
    """Manually trigger cleanup of expired documents"""
    cleanup_service = get_cleanup_service()
    result = await cleanup_service.cleanup_expired_documents()
    return result


@router.post("/cleanup/game-states")
async def cleanup_old_game_states(days: int = 7):
    """Clean up old game states"""
    cleanup_service = get_cleanup_service()
    result = await cleanup_service.cleanup_old_game_states(days=days)
    return result
