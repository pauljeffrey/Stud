"""
Refactored Game API endpoints for Stud
Integrates with new agent architecture and state models
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import json
import asyncio
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

from models.states import GameState, GameConfig, CaseState, PerformanceAnalysis, Achievement, UserDetails
from models.api_requests import (
    SaveCheckpointRequest,
    MigrateDemoGameRequest,
    CheckpointListResponse,
    summarize_checkpoint_row,
)
from api.game_state_utils import parse_client_game_state, find_npc
from agents.game_world_agent import get_game_world_agent
from agents.game_master import get_game_master_agent
from agents.npc_agent import get_npc_agent
from configs.config import config
from service.database import get_database_service
from service.redis_service import get_redis_service
from http_constants import SSE_STREAM_HEADERS

router = APIRouter()

# Reuse the global Supabase client (single connection per process)
supabase = get_database_service().client


def _valid_uuid(value: Optional[str]) -> Optional[str]:
    """Return a canonical UUID string, or None if the value is not a valid UUID."""
    if not value:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError):
        return None


async def _sb(fn):
    """Run a blocking Supabase call on the default thread executor."""
    return await asyncio.to_thread(fn)


async def get_redis():
    """Return the shared async Redis client (or None if not configured)."""
    service = await get_redis_service()
    await service._ensure_connected()
    return service.client


def _sse_error_message(exc: Exception) -> str:
    """Clean, user-facing message for an SSE error chunk.

    HTTPExceptions raised inside a StreamingResponse generator can't change
    the already-sent HTTP status code, so they're surfaced as an `error`
    field in the SSE payload instead — but str(HTTPException) renders as
    "400: {'code': ..., 'message': ...}", which is not fit for display.
    """
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            return str(detail.get("message") or detail)
        return str(detail)
    return str(exc)


async def _cache_game_state(game_state: GameState) -> None:
    try:
        redis_conn = await get_redis()
        if redis_conn:
            await redis_conn.setex(
                f"gs:{game_state.game_id}",
                3600,
                json.dumps(game_state.model_dump(mode="json")),
            )
    except Exception as exc:
        logger.debug("Redis cache skipped: %s", exc)


async def _persist_game_state_update(game_state: GameState) -> None:
    db_user_id = _valid_uuid(game_state.user_id)
    if not db_user_id:
        return
    try:
        update_payload = {
            "state": game_state.model_dump(mode="json"),
            "updated_at": datetime.now().isoformat(),
        }
        await _sb(
            lambda: supabase.table("game_states")
            .update(update_payload)
            .eq("id", game_state.game_id)
            .execute()
        )
    except Exception as exc:
        logger.warning("DB update skipped for game %s: %s", game_state.game_id, exc)


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================
class InitializeGameRequest(BaseModel):
    game_config: GameConfig
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"
    is_demo: bool = False
    user_id: Optional[str] = None  # For registered users, passed from frontend
    initial_difficulty: Optional[str] = None  # For demo mode: "Easy", "Medium", "Hard", etc.
    session_id: Optional[str] = None  # Demo session ID


class GameMasterChatRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    user_message: str
    user_id: Optional[str] = None  # Will use game_state.user_id if not provided
    session_id: Optional[str] = None  # Will use game_state.game_id if not provided
    chat_history: Optional[List[Dict[str, Any]]] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class NPCChatRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    npc_id: str
    user_message: str
    user_id: Optional[str] = None  # Will use game_state.user_id if not provided
    session_id: Optional[str] = None  # Will use game_state.game_id if not provided
    chat_history: Optional[List[Dict[str, Any]]] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class UpdateCaseStateRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    time_elapsed: int = 0
    clue_used: bool = False
    user_answer: Optional[str] = None  # User's answer (if provided before escalating)
    dice_result: Optional[int] = None  # 0-10; only applied when game_config.dice_enabled
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class SubmitAnswerRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    answer: str
    time_taken: int
    dice_result: Optional[int] = None  # 0-10; only used when game_config.dice_enabled
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class UseClueRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    user_answer: Optional[str] = None  # User's provisional answer (if any)
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class SaveGameRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    user_id: Optional[str] = None


# ============================================
# API ENDPOINTS
# ============================================

@router.get("/game/settings")
async def get_game_settings():
    """
    Return game settings: unique config fields and their potential values.
    Used by frontend to let users optionally select values for each field.
    """
    from configs.game_config import (
        PROFESSIONS,
        MODES,
        ERAS,
        NATURAL_CONDITIONS,
        NATIONS,
        ECONOMIC_ADVANTAGES,
    )
    return {
        "success": True,
        "settings": {
            "profession": {
                "label": "Profession",
                "values": PROFESSIONS,
            },
            "clinical_setting": {
                "label": "Clinical Setting",
                "values": MODES,
            },
            "era": {
                "label": "Historical Era",
                "values": ERAS,
            },
            "natural_conditions": {
                "label": "Natural Conditions",
                "values": NATURAL_CONDITIONS,
            },
            "nation_type": {
                "label": "Nation Type",
                "values": NATIONS,
            },
            "economic_advantage": {
                "label": "Economic Advantage",
                "values": ECONOMIC_ADVANTAGES,
            },
        },
        "subject_depends_on": "profession",  # subject values come from profession
    }


@router.post("/game/initialize")
async def initialize_game(
    request: InitializeGameRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Initialize a new game adventure
    Creates game world, first case, and NPCs
    """
    try:
        # Get user ID from session or create demo session ID
        user_id = None
        if request.is_demo:
            import hashlib

            raw_session = request.session_id or hashlib.md5(
                str(datetime.now()).encode()
            ).hexdigest()[:8]
            demo_session_id = raw_session.removeprefix("demo_")
            user_id = f"demo_{demo_session_id}"

            # Check if this demo session already has a game
            try:
                redis_conn = await get_redis()
                if redis_conn:
                    existing = await redis_conn.get(f"dg:{demo_session_id}")
                    if existing:
                        raise HTTPException(
                            status_code=400,
                            detail="Demo game already exists for this session. Please register for full access."
                        )
            except HTTPException:
                raise
            except Exception:
                # If Redis fails, check database
                try:
                    existing_demo = await _sb(
                        lambda: supabase.table("game_states").select("*").eq(
                            "user_id", user_id
                        ).eq("is_demo", True).execute()
                    )
                    if existing_demo.data:
                        raise HTTPException(
                            status_code=400,
                            detail="Demo game already exists for this session. Please register for full access."
                        )
                except HTTPException:
                    raise
                except Exception:
                    pass  # Continue if check fails
        else:
            from api.auth_deps import decode_jwt_user_id

            jwt_uid = decode_jwt_user_id(authorization)
            user_id = _valid_uuid(jwt_uid) or _valid_uuid(request.user_id)
            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required to start a registered game",
                )
        
        # Resolve AI credentials: demo may fall back to platform .env; registered users must supply valid keys
        from service.model_credentials import resolve_game_credentials

        try:
            resolved_creds = resolve_game_credentials(
                is_demo=request.is_demo,
                model_name=request.model_name,
                api_key=request.api_key,
                provider=request.provider or "google",
            )
        except ValueError as cred_err:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_API_CREDENTIALS",
                    "message": str(cred_err),
                },
            )

        # Fresh agent instance so per-request credentials are honoured
        import agents.game_master as gm_module
        gm_module._game_master_instance = None

        try:
            game_master = get_game_master_agent(
                model_name=resolved_creds.model_name,
                api_key=resolved_creds.api_key,
                provider=resolved_creds.provider,
            )
        except Exception as e:
            logger.exception("Failed to initialize game master agent")
            raise HTTPException(status_code=500, detail="Failed to initialize game master agent")
        
        # Get initial difficulty level (for demo mode)
        initial_difficulty = None
        if request.is_demo and hasattr(request, 'initial_difficulty'):
            from models.states import DifficultyLevel
            try:
                initial_difficulty = DifficultyLevel(request.initial_difficulty)
            except:
                initial_difficulty = None
        
        user_details = UserDetails(user_id=user_id) if user_id else None
        try:
            game_world, game_state, case_state, npc_states, previous_cases = await asyncio.wait_for(
                game_master.initialize_game(
                    game_config=request.game_config,
                    user_id=user_id,
                    is_demo=request.is_demo,
                    user_details=user_details,
                    initial_difficulty=initial_difficulty
                ),
                timeout=config.AGENT_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.error("initialize_game timed out after %ss", config.AGENT_TIMEOUT)
            raise HTTPException(
                status_code=504,
                detail="Game creation is taking longer than expected. Please try again.",
            )
        except Exception as e:
            logger.exception("initialize_game agent call failed")
            raise HTTPException(status_code=500, detail="Failed to initialize game. Please try again.")
        
        # Save complete session state to Redis
        try:
            from service.redis_service import get_redis_service
            redis_service = await get_redis_service()
            await redis_service.save_game_session_state(
                user_id=user_id,
                session_id=game_state.game_id,
                game_world=game_world.model_dump(mode="json"),
                game_state=game_state.model_dump(mode="json"),
                case_state=case_state.model_dump(mode="json"),
                npc_states=[npc.model_dump(mode="json") for npc in npc_states],
                previous_cases=previous_cases.model_dump(mode="json") if previous_cases else None,
                ttl=3600
            )
            
            if request.is_demo:
                await redis_service.set_with_ttl(
                    f"dg:{demo_session_id}",
                    game_state.game_id,
                    3600
                )
        except Exception as e:
            # Log error but continue - Redis is optional
            logger.warning(f"Redis cache error (non-critical): {e}")
        
        # Persist to Supabase in the background — Redis already holds the full state,
        # so the response can be returned immediately without waiting for DB writes.
        async def _persist_to_db():
            try:
                # Demo / anonymous sessions live in Redis only — user_id is not a UUID.
                if request.is_demo:
                    return
                db_user_id = _valid_uuid(game_state.user_id)
                if not db_user_id:
                    logger.warning(
                        "Skipping DB persist for game %s — invalid user_id %r",
                        game_state.game_id,
                        game_state.user_id,
                    )
                    return

                insert_payload = {
                    "id": game_state.game_id,
                    "user_id": db_user_id,
                    "case_id": game_state.case_id,
                    "state": game_state.model_dump(mode="json"),
                    "is_demo": request.is_demo,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
                await _sb(lambda: supabase.table("game_states").insert(insert_payload).execute())

                try:
                    from service.database import get_database_service
                    await get_database_service().record_game_stat(db_user_id, created=1, played=1)
                except Exception:
                    logger.warning("Failed to record game_statistics for %s", db_user_id)

                if previous_cases:
                    from service.database import get_database_service
                    db_service = get_database_service()
                    for case in previous_cases.cases:
                        await db_service.save_previous_case(
                            game_id=game_state.game_id,
                            case_state_id=case.case_state_id,
                            case_number=previous_cases.cases.index(case) + 1,
                            scenario_summary=case.clinical_case_scenario_description[:200],
                            diagnosis=case.diagnosis,
                            question_summary=case.question[:200],
                            difficulty_level=str(game_state.difficulty_level)
                        )
            except Exception:
                logger.exception("Background DB persist failed for game %s", game_state.game_id)

        asyncio.create_task(_persist_to_db())

        await _cache_game_state(game_state)

        return {
            "success": True,
            "game_state": game_state.model_dump(mode="json"),
            "game_world": game_world.model_dump(mode="json"),
            "case_state": case_state.model_dump(mode="json"),
            "npc_states": [npc.model_dump(mode="json") for npc in npc_states],
            "used_platform_default": resolved_creds.used_platform_default,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to initialize game")
        raise HTTPException(status_code=500, detail="Failed to initialize game")


def _resolve_chat_credentials(
    model_name: Optional[str],
    api_key: Optional[str],
    provider: Optional[str],
    *,
    is_demo: bool,
):
    from service.model_credentials import resolve_game_credentials

    return resolve_game_credentials(
        is_demo=is_demo,
        model_name=model_name,
        api_key=api_key,
        provider=provider or "google",
    )


@router.post("/game/master-chat")
async def game_master_chat(request: GameMasterChatRequest):
    """Chat with the Game Master"""
    
    async def generate_response():
        try:
            game_state = parse_client_game_state(request.game_state)
            is_demo = bool(game_state.is_demo)

            try:
                creds = _resolve_chat_credentials(
                    request.model_name,
                    request.api_key,
                    request.provider,
                    is_demo=is_demo,
                )
            except ValueError as cred_err:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_API_CREDENTIALS", "message": str(cred_err)},
                )

            game_master = get_game_master_agent(
                model_name=creds.model_name,
                api_key=creds.api_key,
                provider=creds.provider,
            )
            
            # Get user_id and session_id from request or game_state
            user_id = getattr(request, 'user_id', None) or game_state.user_id
            session_id = getattr(request, 'session_id', None) or game_state.game_id
            
            # Get chat history from storage
            from utils import get_chat_history_from_storage
            chat_history = await get_chat_history_from_storage(
                user_id=user_id,
                conversation_id=session_id,
                chat_type="game_master"
            )
            
            # Get response (includes chat history retrieval and storage)
            response, updated_chat_history = await game_master.chat_with_game_master(
                game_state=game_state,
                user_message=request.user_message,
                user_id=user_id,
                session_id=session_id,
                chat_history=chat_history or request.chat_history
            )
            
            # Note: Chat history should be managed by the frontend or stored separately
            # GameState model doesn't include chat_history fields
            
            # Stream response in small chunks to mimic token-by-token output
            chunk_size = 4
            text = response or ""
            total = max(1, (len(text) + chunk_size - 1) // chunk_size)
            for i, start in enumerate(range(0, len(text), chunk_size)):
                piece = text[start : start + chunk_size]
                is_last = i == total - 1
                chunk = {
                    "content": piece,
                    "complete": is_last,
                    "updated_game_state": game_state.model_dump(mode="json") if is_last else None,
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.02)

        except Exception as e:
            error_chunk = {"error": _sse_error_message(e), "complete": True}
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers=dict(SSE_STREAM_HEADERS),
    )


@router.post("/game/npc-chat")
async def npc_chat(request: NPCChatRequest):
    """Chat with an NPC"""
    
    async def generate_response():
        try:
            # Parse game state
            game_state = parse_client_game_state(request.game_state)
            is_demo = bool(game_state.is_demo)

            try:
                creds = _resolve_chat_credentials(
                    request.model_name,
                    request.api_key,
                    request.provider,
                    is_demo=is_demo,
                )
            except ValueError as cred_err:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_API_CREDENTIALS", "message": str(cred_err)},
                )

            npc_state = find_npc(
                (game_state.case_state.npc_states if game_state.case_state else None)
                or request.game_state.get("npc_states"),
                request.npc_id,
            )
            
            if not npc_state:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            npc_agent = get_npc_agent(
                model_name=creds.model_name,
                api_key=creds.api_key,
                provider=creds.provider,
            )
            
            # Get user_id and session_id
            user_id = getattr(request, 'user_id', None) or game_state.user_id
            session_id = getattr(request, 'session_id', None) or game_state.game_id
            
            # Get chat history from storage
            from utils import get_chat_history_from_storage
            chat_history = await get_chat_history_from_storage(
                user_id=user_id,
                conversation_id=session_id,
                chat_type="npc",
                npc_id=str(request.npc_id)
            )
            
            # Get response
            response, updated_chat_history = await npc_agent.chat_with_npc(
                npc_state=npc_state,
                user_message=request.user_message,
                case_state=game_state.case_state,
                chat_history=chat_history or request.chat_history or []
            )
            
            # Stream response
            words = response.split()
            for i, word in enumerate(words):
                chunk = {
                    "content": word + " ",
                    "complete": i == len(words) - 1,
                    "npc_id": request.npc_id
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.03)

        except Exception as e:
            error_chunk = {"error": _sse_error_message(e), "complete": True}
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers=dict(SSE_STREAM_HEADERS),
    )


@router.post("/game/update-state")
async def update_case_state(request: UpdateCaseStateRequest):
    """
    Update case state (escalate/de-escalate)
    Called by State Controller Agent
    """
    try:
        # Parse game state
        game_state = parse_client_game_state(request.game_state)
        
        game_master = get_game_master_agent(
            model_name=request.model_name,
            api_key=request.api_key,
            provider=request.provider or "google"
        )
        latest_performance = game_state.user_performance[-1] if game_state.user_performance else None
        case_metadata = getattr(game_state, "case_metadata", None) or getattr(game_state.case_state, "case_metadata", None)

        model_answer = getattr(game_state.case_state, "answer", None) if game_state.case_state else None
        dice_result = None
        if getattr(game_state.game_config, "dice_enabled", False) and request.dice_result is not None:
            dice_result = max(0, min(10, request.dice_result))
        try:
            state_change = await asyncio.wait_for(
                game_master.update_clinical_case(
                    current_case_state=game_state.case_state,
                    case_metadata=case_metadata,
                    user_performance=latest_performance,
                    time_elapsed=request.time_elapsed,
                    clue_used=request.clue_used,
                    user_answer=request.user_answer,
                    model_answer=model_answer,
                    dice_result=dice_result,
                    existing_npc_states=getattr(game_state.case_state, "npc_states", None),
                    game_world=game_state.game_world,
                ),
                timeout=config.AGENT_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.error("update_case_state timed out after %ss", config.AGENT_TIMEOUT)
            raise HTTPException(status_code=504, detail="Case update is taking longer than expected. Please try again.")
        except Exception as e:
            logger.exception("Failed to update case state")
            raise HTTPException(status_code=500, detail="Failed to update case state")
        
        # Update game state
        game_state.case_state = state_change.updated_case_state
        game_state.last_updated = datetime.now()
        
        # Check if max changes reached (handoff to game master)
        handoff_occurred = game_state.case_state.n_changes >= game_state.case_state.max_clinical_changes
        cases_remaining_before_handoff = game_state.current_case_number < game_state.total_cases
        if handoff_occurred:
            # Get latest performance for handoff
            latest_performance = None
            if game_state.user_performance:
                latest_performance = game_state.user_performance[-1]
            else:
                # Create a default performance if none exists
                latest_performance = PerformanceAnalysis(
                    clinical_state_id=game_state.case_state.case_state_id,
                    score=5.0,
                    analysis="Case completed",
                    strengths=[],
                    weaknesses=[]
                )
            
            # Handoff to game master
            game_master = get_game_master_agent(
                model_name=request.model_name,
                api_key=request.api_key,
                provider=request.provider or "google"
            )
            try:
                game_state = await asyncio.wait_for(
                    game_master.handoff_from_state_controller(
                        game_state=game_state,
                        final_performance=latest_performance
                    ),
                    timeout=config.AGENT_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.error("handoff_from_state_controller timed out after %ss", config.AGENT_TIMEOUT)
                raise HTTPException(status_code=504, detail="Generating the next case is taking longer than expected. Please try again.")
            except HTTPException:
                raise
            except Exception:
                logger.exception("handoff_from_state_controller failed")
                raise HTTPException(status_code=500, detail="Failed to generate the next case")

        await _cache_game_state(game_state)
        await _persist_game_state_update(game_state)

        # Quest is complete when a handoff happened but there was no next
        # case to generate (we were already on the last case).
        quest_complete = handoff_occurred and not cases_remaining_before_handoff

        if quest_complete:
            db_user_id = _valid_uuid(game_state.user_id)
            if db_user_id:
                try:
                    avg_score_10 = (
                        sum(p.score for p in game_state.user_performance) / len(game_state.user_performance)
                        if game_state.user_performance else 0.0
                    )
                    await get_database_service().record_game_stat(
                        db_user_id, completed=1, score_pct=min(100.0, max(0.0, avg_score_10 * 10))
                    )
                except Exception:
                    logger.warning("Failed to record game completion stat for %s", db_user_id)

        return {
            "success": True,
            "game_state": game_state.model_dump(mode="json"),
            "state_change": {
                "escalation_level": state_change.escalation_level,
                "change_description": state_change.change_description,
                "penalty_applied": state_change.penalty_applied
            },
            "handoff_occurred": handoff_occurred,
            "quest_complete": quest_complete,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update state")
        raise HTTPException(status_code=500, detail="Failed to update state")


@router.post("/game/use-clue")
async def use_clue(request: UseClueRequest):
    """Use a clue (triggers penalty)"""
    try:
        # Parse game state
        game_state = parse_client_game_state(request.game_state)
        
        # Mark clue as used
        game_state.case_state.clue_used = True
        
        # Update state (will apply penalty)
        update_request = UpdateCaseStateRequest(
            game_state=game_state.model_dump(mode="json"),
            clue_used=True,
            user_answer=request.user_answer,
            model_name=request.model_name,
            api_key=request.api_key,
            provider=request.provider
        )
        
        return await update_case_state(update_request)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to use clue")
        raise HTTPException(status_code=500, detail="Failed to use clue")


@router.post("/game/submit-answer")
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit an answer: score it, then escalate/de-escalate the clinical case
    based on the result and hand off to the next case once
    max_clinical_changes is reached (delegates to update_case_state, the
    same path "Use Clue" uses, so a case actually progresses on every
    answer instead of only when a clue is used).
    """
    try:
        # Parse game state
        game_state = parse_client_game_state(request.game_state)

        # Analyze performance
        performance = await _analyze_performance(
            game_state,
            request.answer,
            request.time_taken,
            request.model_name,
            request.api_key,
            request.provider
        )

        # Add to performance history so update_case_state picks it up as the
        # latest performance for escalation/handoff decisions.
        game_state.user_performance.append(performance)

        update_request = UpdateCaseStateRequest(
            game_state=game_state.model_dump(mode="json"),
            time_elapsed=request.time_taken,
            clue_used=False,
            user_answer=request.answer,
            dice_result=request.dice_result,
            model_name=request.model_name,
            api_key=request.api_key,
            provider=request.provider,
        )
        update_result = await update_case_state(update_request)
        updated_game_state = update_result["game_state"]

        # Award XP for the answered case: 50-100 based on performance score (0-10 scale)
        user_id = updated_game_state.get("user_id")
        if user_id and not str(user_id).startswith("demo_"):
            try:
                from service.database import get_database_service
                score = float(getattr(performance, "score", 5) or 5)
                score = min(10, max(0, score))
                xp = int(50 + (score / 10) * 50)
                db_service = get_database_service()
                await db_service.add_experience_points(
                    user_id=user_id,
                    xp_amount=xp,
                    total_quests_delta=1
                )
            except Exception as xp_err:
                logger.warning(f"Error awarding game XP: {xp_err}")

        resp = {
            "success": True,
            "performance": performance.model_dump(mode="json"),
            "game_state": updated_game_state,
            "state_change": update_result.get("state_change"),
            "handoff_occurred": update_result.get("handoff_occurred", False),
            "quest_complete": update_result.get("quest_complete", False),
        }
        state_change = update_result.get("state_change") or {}
        if request.dice_result is not None and state_change.get("change_description"):
            resp["dice_effect"] = state_change["change_description"]
        return resp

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to submit answer")
        raise HTTPException(status_code=500, detail="Failed to submit answer")


@router.post("/game/dice-effect")
async def apply_dice_effect(request: Dict[str, Any]):
    """Apply a standalone dice-roll effect to the current case state (toggleable)."""
    try:
        game_state = parse_client_game_state(request.get("game_state", {}))
        raw = request.get("dice_result")
        if raw is None:
            raw = request.get("diceResult", 5)
        try:
            dice_result = int(raw)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="dice_result must be an integer 0-10")
        if not (0 <= dice_result <= 10):
            raise HTTPException(status_code=400, detail="dice_result must be 0-10")

        game_master = get_game_master_agent()
        state_change = await game_master.update_clinical_case(
            current_case_state=game_state.case_state,
            case_metadata=getattr(game_state, "case_metadata", None),
            model_answer=getattr(game_state.case_state, "answer", None),
            dice_result=dice_result,
            existing_npc_states=getattr(game_state.case_state, "npc_states", None),
            game_world=game_state.game_world,
        )
        game_state.case_state = state_change.updated_case_state
        game_state.last_updated = datetime.now()

        try:
            update_payload = {
                "state": game_state.model_dump(mode="json"),
                "updated_at": datetime.now().isoformat(),
            }
            await _sb(
                lambda: supabase.table("game_states")
                .update(update_payload)
                .eq("id", game_state.game_id)
                .execute()
            )
        except Exception:
            pass

        return {
            "success": True,
            "game_state": game_state.model_dump(mode="json"),
            "dice_result": dice_result,
            "change_description": state_change.change_description,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Dice effect failed")
        raise HTTPException(status_code=500, detail="Dice effect failed")


@router.get("/game/{game_id}")
async def get_game_state(game_id: str):
    """Get game state by ID"""
    try:
        # Try Redis first with error handling
        try:
            redis_conn = await get_redis()
            if redis_conn:
                cached = await redis_conn.get(f"gs:{game_id}")
                if cached:
                    return {"success": True, "game_state": json.loads(cached)}
        except Exception as e:
            logger.warning(f"Redis read error (non-critical): {e}")
        
        # Fallback to Supabase with error handling
        try:
            result = await _sb(
                lambda: supabase.table("game_states").select("*").eq("id", game_id).execute()
            )
            if not result.data:
                raise HTTPException(status_code=404, detail="Game not found")
            
            return {
                "success": True,
                "game_state": result.data[0]["state"]
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed to read from database")
            raise HTTPException(status_code=500, detail="Failed to read from database")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get game")
        raise HTTPException(status_code=500, detail="Failed to get game")


@router.delete("/game/{game_id}")
async def delete_game(game_id: str):
    """Delete a game"""
    try:
        # Delete from Redis with error handling
        try:
            redis_conn = await get_redis()
            if redis_conn:
                await redis_conn.delete(f"gs:{game_id}")
        except Exception as e:
            logger.warning(f"Redis delete error (non-critical): {e}")
        
        # Delete from Supabase with error handling
        try:
            await _sb(
                lambda: supabase.table("game_states").delete().eq("id", game_id).execute()
            )
        except Exception as e:
            logger.exception("Failed to delete from database")
            raise HTTPException(status_code=500, detail="Failed to delete from database")
        
        return {"success": True, "message": "Game deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete game")
        raise HTTPException(status_code=500, detail="Failed to delete game")


# ============================================
# HELPER FUNCTIONS
# ============================================

async def _analyze_performance(
    game_state: GameState,
    user_answer: str,
    time_taken: int,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google"
) -> PerformanceAnalysis:
    """Analyze user performance for a case"""
    from pydantic_ai import Agent
    from model import select_model_with_fallback
    from configs.config import config

    resolved_name = model_name or config.GAME_MASTER_MODEL_NAME or "meta-llama/llama-3.3-70b-instruct:free"

    model, _ = select_model_with_fallback(resolved_name, api_key)

    agent = Agent(
        model,
        system_prompt="You are a medical education performance analyzer. Evaluate answers and provide scores (0-10) with detailed analysis.",
        output_type=PerformanceAnalysis
    )
    
    prompt = f"""
    Analyze the user's performance for this clinical case:
    
    Case Question: {game_state.case_state.question}
    Correct Answer: {game_state.case_state.answer}
    User Answer: {user_answer}
    Time Taken: {time_taken} seconds
    Time Limit: {game_state.case_state.time_limit_seconds} seconds
    Clue Used: {game_state.case_state.clue_used}
    
    Provide:
    1. Score (0-10) based on accuracy, completeness, and time efficiency
    2. Concise analysis of performance
    3. List of strengths
    4. List of weaknesses
    
    Apply penalty if clue was used.
    """
    
    try:
        result = await agent.run(prompt)
        performance = result.output if hasattr(result, 'output') else result
        
        # Ensure it's a PerformanceAnalysis object
        if not isinstance(performance, PerformanceAnalysis):
            # If dict, convert
            if isinstance(performance, dict):
                performance = PerformanceAnalysis(**performance)
            else:
                raise ValueError("Agent did not return valid PerformanceAnalysis")
        
        # Set clinical_state_id
        performance.clinical_state_id = game_state.case_state.case_state_id
        
        return performance
    except Exception as e:
        raise Exception(f"Failed to analyze performance: {str(e)}")

@router.post("/game/save")
async def save_game(request: SaveGameRequest):
    """Persist game state to Supabase (registered users) or Redis (demo)."""
    try:
        game_state = parse_client_game_state(request.game_state)
        user_id = request.user_id or game_state.user_id
        is_demo = bool(game_state.is_demo or (user_id and str(user_id).startswith("demo_")))

        await _cache_game_state(game_state)

        if is_demo:
            return {
                "success": True,
                "message": "Demo game cached successfully",
                "game_state_id": game_state.game_id,
            }

        db_user_id = _valid_uuid(user_id)
        if not db_user_id:
            raise HTTPException(status_code=400, detail="Valid user_id required to save game")

        gs_payload = {
            "id": game_state.game_id,
            "user_id": db_user_id,
            "case_id": game_state.case_id,
            "state": game_state.model_dump(mode="json"),
            "is_active": True,
            "is_demo": False,
            "updated_at": datetime.now().isoformat(),
        }
        creation_payload = {
            "user_id": db_user_id,
            "game_state_id": game_state.game_id,
            "scenario_type": "standard",
            "created_at": datetime.now().isoformat(),
        }

        async def _upsert_and_log():
            def _work():
                supabase.table("game_states").upsert(gs_payload, on_conflict="id").execute()
                existing = (
                    supabase.table("game_creation_log")
                    .select("id")
                    .eq("game_state_id", game_state.game_id)
                    .limit(1)
                    .execute()
                )
                if not existing.data:
                    supabase.table("game_creation_log").insert(creation_payload).execute()

            return await _sb(_work)

        await _upsert_and_log()

        return {
            "success": True,
            "message": "Game saved successfully",
            "game_state_id": game_state.game_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("save_game failed for game %s", getattr(request, "game_state", {}).get("game_id"))
        raise HTTPException(status_code=500, detail="Failed to save game")


@router.post("/game/save-checkpoint")
async def save_checkpoint(
    request: SaveCheckpointRequest,
    authorization: Optional[str] = Header(None),
):
    """Save a game checkpoint for the authenticated user."""
    from api.auth_deps import decode_jwt_user_id

    user_id = _valid_uuid(decode_jwt_user_id(authorization))
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        game_state_result = await _sb(
            lambda: supabase.table("game_states")
            .select("state")
            .eq("id", request.game_state_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if not game_state_result.data:
            raise HTTPException(status_code=404, detail="Game state not found")

        checkpoint_id = request.checkpoint_id or f"checkpoint-{datetime.now().timestamp()}"
        state_snapshot = game_state_result.data[0]["state"]

        db_service = get_database_service()
        await db_service.create_checkpoint(
            user_id=user_id,
            game_state_id=request.game_state_id,
            checkpoint_id=checkpoint_id,
            checkpoint_name=request.checkpoint_name,
            state=state_snapshot,
            description=request.description,
        )

        return {"success": True, "checkpoint_id": checkpoint_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to save checkpoint")
        raise HTTPException(status_code=500, detail="Failed to save checkpoint")


@router.get("/game/checkpoints")
async def list_checkpoints(authorization: Optional[str] = Header(None)):
    """List all checkpoints for the authenticated user."""
    from api.auth_deps import decode_jwt_user_id

    user_id = _valid_uuid(decode_jwt_user_id(authorization))
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        db_service = get_database_service()
        rows = await db_service.list_user_checkpoints(user_id)
        summaries = [summarize_checkpoint_row(row) for row in rows]
        return CheckpointListResponse(checkpoints=summaries).model_dump(mode="json")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to list checkpoints")
        raise HTTPException(status_code=500, detail="Failed to list checkpoints")


@router.get("/game/checkpoints/{checkpoint_id}")
async def get_checkpoint(checkpoint_id: str, authorization: Optional[str] = Header(None)):
    """Fetch the full saved game state for one checkpoint, to resume play."""
    from api.auth_deps import decode_jwt_user_id

    user_id = _valid_uuid(decode_jwt_user_id(authorization))
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        db_service = get_database_service()
        row = await db_service.get_checkpoint(user_id, checkpoint_id)
        if not row:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        return {"success": True, "game_state": row.get("state") or {}}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to load checkpoint")
        raise HTTPException(status_code=500, detail="Failed to load checkpoint")


@router.delete("/game/checkpoints/{checkpoint_id}")
async def delete_checkpoint(checkpoint_id: str, authorization: Optional[str] = Header(None)):
    """Delete a checkpoint owned by the authenticated user."""
    from api.auth_deps import decode_jwt_user_id

    user_id = _valid_uuid(decode_jwt_user_id(authorization))
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        db_service = get_database_service()
        deleted = await db_service.delete_checkpoint(user_id, checkpoint_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete checkpoint")
        raise HTTPException(status_code=500, detail="Failed to delete checkpoint")


@router.post("/game/migrate-demo")
async def migrate_demo_game(
    request: MigrateDemoGameRequest,
    authorization: Optional[str] = Header(None),
):
    """Attach a demo Redis session to a registered user account."""
    from api.auth_deps import decode_jwt_user_id

    user_id = _valid_uuid(decode_jwt_user_id(authorization))
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    demo_session_id = request.demo_session_id.removeprefix("demo_")
    demo_user_id = f"demo_{demo_session_id}"

    try:
        redis_service = await get_redis_service()
        session = await redis_service.get_game_session_state(demo_user_id, request.game_id)
        if not session:
            raise HTTPException(status_code=404, detail="Demo game state not found in cache")

        state_payload = {
            **session["game_state"],
            "game_world": session["game_world"],
            "case_state": session["case_state"],
            "npc_states": session["npc_states"],
        }
        if session.get("previous_cases"):
            state_payload["previous_cases"] = session["previous_cases"]

        game_state = parse_client_game_state(state_payload)
        game_state.user_id = user_id
        game_state.is_demo = False
        game_state.demo_limits = None

        insert_payload = {
            "id": game_state.game_id,
            "user_id": user_id,
            "case_id": game_state.case_id,
            "state": game_state.model_dump(mode="json"),
            "is_demo": False,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        await _sb(lambda: supabase.table("game_states").upsert(insert_payload, on_conflict="id").execute())
        await _cache_game_state(game_state)

        redis_conn = await get_redis()
        if redis_conn:
            await redis_conn.delete(f"dg:{demo_session_id}")

        return {"success": True, "game_id": game_state.game_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to migrate demo game")
        raise HTTPException(status_code=500, detail="Failed to migrate demo game")
