"""Public waitlist signup — no auth required, rate-limited."""
import logging

from fastapi import APIRouter, HTTPException, Request

from api.rate_limit import enforce_rate_limit
from configs.config import config
from models.api_requests import WaitlistRequest
from service.database import get_database_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/waitlist")
async def join_waitlist(request: Request, body: WaitlistRequest):
    await enforce_rate_limit(request, "waitlist", config.RATE_LIMIT_PER_MINUTE, 60)
    db = get_database_service()
    email = body.email.strip().lower()

    try:
        if await db.waitlist_email_exists(email):
            return {"success": True, "already_joined": True, "message": "You're already on the waitlist."}

        await db.add_waitlist_entry(
            email=email,
            name=(body.name or "").strip() or None,
            note=(body.note or "").strip() or None,
            source_page=body.source_page,
        )
        return {"success": True, "already_joined": False, "message": "You're on the list!"}
    except Exception as e:
        logger.exception("Failed to add waitlist entry")
        raise HTTPException(status_code=500, detail="Failed to join waitlist. Please try again.")
