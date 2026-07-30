"""
Cleanup API endpoints
For manual cleanup triggers and monitoring. Admin-only: these force-expire
other users' documents/game state, so they require the internal secret header
rather than being open to any caller.
"""
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from configs.config import config
from service.cleanup_service import get_cleanup_service

router = APIRouter()


def _require_internal_secret(x_internal_secret: str = Header(None)) -> None:
    if not config.SECRET_KEY or x_internal_secret != config.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Not authorized")


@router.post("/cleanup/documents")
async def cleanup_expired_documents(
    background_tasks: BackgroundTasks, x_internal_secret: str = Header(None)
):
    """Manually trigger cleanup of expired documents (admin-only)"""
    _require_internal_secret(x_internal_secret)
    cleanup_service = get_cleanup_service()
    result = await cleanup_service.cleanup_expired_documents()
    return result


@router.post("/cleanup/game-states")
async def cleanup_old_game_states(days: int = 7, x_internal_secret: str = Header(None)):
    """Clean up old game states (admin-only)"""
    _require_internal_secret(x_internal_secret)
    cleanup_service = get_cleanup_service()
    result = await cleanup_service.cleanup_old_game_states(days=days)
    return result
