"""User notifications — currently used for background job completion
(document ingestion, topic-focused quiz generation). Polled by the frontend
since there's no push/WebSocket transport in this deployment."""
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.auth_deps import get_current_user_id
from service.database import get_database_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/notifications")
async def list_notifications(
    unread_only: bool = False,
    user_id: str = Depends(get_current_user_id),
):
    db = get_database_service()
    try:
        rows = await db.list_notifications(user_id, unread_only=unread_only)
        unread_count = len(rows) if unread_only else sum(1 for r in rows if not r.get("read"))
        return {"success": True, "notifications": rows, "unread_count": unread_count}
    except Exception:
        logger.exception("Failed to list notifications")
        raise HTTPException(status_code=500, detail="Failed to list notifications")


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
):
    db = get_database_service()
    try:
        await db.mark_notification_read(user_id, notification_id)
        return {"success": True}
    except Exception:
        logger.exception("Failed to mark notification read")
        raise HTTPException(status_code=500, detail="Failed to mark notification read")


@router.post("/notifications/read-all")
async def mark_all_notifications_read(user_id: str = Depends(get_current_user_id)):
    db = get_database_service()
    try:
        await db.mark_all_notifications_read(user_id)
        return {"success": True}
    except Exception:
        logger.exception("Failed to mark all notifications read")
        raise HTTPException(status_code=500, detail="Failed to mark all notifications read")
