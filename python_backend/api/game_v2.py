"""
Refactored Game API endpoints for Stud
Integrates with new agent architecture and state models
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import json
import asyncio
from datetime import datetime
import uuid

from models.states import GameState, GameConfig, CaseState, PerformanceAnalysis, Achievement, UserDetails
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


async def _sb(fn):
    """Run a blocking Supabase call on the default thread executor."""
    return await asyncio.to_thread(fn)


async def get_redis():
    """Return the shared async Redis client (or None if not configured)."""
    service = await get_redis_service()
    await service._ensure_connected()
    return service.client


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
async def initialize_game(request: InitializeGameRequest):
    """
    Initialize a new game adventure
    Creates game world, first case, and NPCs
    """
    try:
        # Get user ID from session or create demo session ID
        user_id = None
        if request.is_demo:
            # For demo, use session-based ID (from request headers or generate)
            # This allows multiple demo users without conflicts
            import hashlib
            from fastapi import Request
            # In a real implementation, get session ID from request headers or cookies
            # For now, generate a demo session ID
            demo_session_id = request.model_dump().get("session_id") or f"demo_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
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
            except Exception as e:
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
            # Get user ID from request (passed by frontend when logged in) or placeholder
            user_id = request.user_id or "user_123"
        
        # Get game master agent (singleton pattern - reuses instance)
        try:
            game_master = get_game_master_agent(
                model_name=request.model_name,
                api_key=request.api_key,
                provider=request.provider or "google"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize game master agent: {str(e)}")
        
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
            game_world, game_state, case_state, npc_states, previous_cases = await game_master.initialize_game(
                game_config=request.game_config,
                user_id=user_id,
                is_demo=request.is_demo,
                user_details=user_details,
                initial_difficulty=initial_difficulty
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize game: {str(e)}")
        
        # Save complete session state to Redis
        try:
            from service.redis_service import get_redis_service
            redis_service = await get_redis_service()
            await redis_service.save_game_session_state(
                user_id=user_id,
                session_id=game_state.game_id,
                game_world=game_world.model_dump(mode="json", default=str),
                game_state=game_state.model_dump(mode="json", default=str),
                case_state=case_state.model_dump(mode="json", default=str),
                npc_states=[npc.model_dump(mode="json", default=str) for npc in npc_states],
                previous_cases=previous_cases.model_dump(mode="json", default=str) if previous_cases else None,
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
            print(f"Redis cache error (non-critical): {e}")
        
        # Save to Supabase with error handling
        try:
            insert_payload = {
                "id": game_state.game_id,
                "user_id": game_state.user_id,
                "case_id": game_state.case_id,
                "state": game_state.model_dump(mode="json", default=str),
                "is_demo": request.is_demo,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            await _sb(lambda: supabase.table("game_states").insert(insert_payload).execute())
            
            # Save previous cases to prevent duplicates
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
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save game state: {str(e)}")
        
        return {
            "success": True,
            "game_state": game_state.model_dump(mode="json", default=str),
            "game_world": game_world.model_dump(mode="json", default=str),
            "case_state": case_state.model_dump(mode="json", default=str),
            "npc_states": [npc.model_dump(mode="json", default=str) for npc in npc_states]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize game: {str(e)}")


@router.post("/game/master-chat")
async def game_master_chat(request: GameMasterChatRequest):
    """Chat with the Game Master"""
    
    async def generate_response():
        try:
            # Parse game state
            game_state = GameState(**request.game_state)
            
            # Get game master agent
            game_master = get_game_master_agent(
                model_name=request.model_name,
                api_key=request.api_key,
                provider=request.provider or "google"
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
            
            # Stream response
            words = response.split()
            for i, word in enumerate(words):
                chunk = {
                    "content": word + " ",
                    "complete": i == len(words) - 1,
                    "updated_game_state": game_state.model_dump(mode="json", default=str) if i == len(words) - 1 else None
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.03)
                
        except Exception as e:
            error_chunk = {"error": str(e), "complete": True}
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
            game_state = GameState(**request.game_state)
            
            # Find NPC from case state's npc_states list
            npc_states = game_state.case_state.npc_states or []
            npc_state = None
            for npc in npc_states:
                if npc.npc_id == request.npc_id:
                    npc_state = npc
                    break
            
            if not npc_state:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            # Get NPC agent
            npc_agent = get_npc_agent(
                model_name=request.model_name,
                api_key=request.api_key,
                provider=request.provider or "google"
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
            error_chunk = {"error": str(e), "complete": True}
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
        game_state = GameState(**request.game_state)
        
        game_master = get_game_master_agent(
            model_name=request.model_name,
            api_key=request.api_key,
            provider=request.provider or "google"
        )
        latest_performance = game_state.user_performance[-1] if game_state.user_performance else None
        case_metadata = getattr(game_state, "case_metadata", None) or getattr(game_state.case_state, "case_metadata", None)

        model_answer = getattr(game_state.case_state, "answer", None) if game_state.case_state else None
        try:
            state_change = await game_master.update_clinical_case(
                current_case_state=game_state.case_state,
                case_metadata=case_metadata,
                user_performance=latest_performance,
                time_elapsed=request.time_elapsed,
                clue_used=request.clue_used,
                user_answer=request.user_answer,
                model_answer=model_answer,
                existing_npc_states=getattr(game_state.case_state, "npc_states", None),
                game_world=game_state.game_world,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update case state: {str(e)}")
        
        # Update game state
        game_state.case_state = state_change.updated_case_state
        game_state.last_updated = datetime.now()
        
        # Check if max changes reached (handoff to game master)
        if game_state.case_state.n_changes >= game_state.case_state.max_clinical_changes:
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
            game_state = await game_master.handoff_from_state_controller(
                game_state=game_state,
                final_performance=latest_performance
            )
        
        # Update cache and database with error handling
        try:
            redis_conn = await get_redis()
            if redis_conn:
                await redis_conn.setex(
                    f"gs:{game_state.game_id}",
                    3600,
                    json.dumps(game_state.model_dump(), default=str)
                )
        except Exception as e:
            print(f"Redis cache error (non-critical): {e}")
        
        try:
            update_payload = {
                "state": game_state.model_dump(mode="json", default=str),
                "updated_at": datetime.now().isoformat(),
            }
            await _sb(
                lambda: supabase.table("game_states")
                .update(update_payload)
                .eq("id", game_state.game_id)
                .execute()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save game state: {str(e)}")
        
        return {
            "success": True,
            "game_state": game_state.model_dump(mode="json", default=str),
            "state_change": {
                "escalation_level": state_change.escalation_level,
                "change_description": state_change.change_description,
                "penalty_applied": state_change.penalty_applied
            },
            "handoff_occurred": game_state.case_state.n_changes >= game_state.case_state.max_clinical_changes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update state: {str(e)}")


@router.post("/game/use-clue")
async def use_clue(request: UseClueRequest):
    """Use a clue (triggers penalty)"""
    try:
        # Parse game state
        game_state = GameState(**request.game_state)
        
        # Mark clue as used
        game_state.case_state.clue_used = True
        
        # Update state (will apply penalty)
        update_request = UpdateCaseStateRequest(
            game_state=request.game_state,
            clue_used=True,
            user_answer=request.user_answer,
            model_name=request.model_name,
            api_key=request.api_key,
            provider=request.provider
        )
        
        return await update_case_state(update_request)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to use clue: {str(e)}")


@router.post("/game/submit-answer")
async def submit_answer(request: SubmitAnswerRequest):
    """Submit answer and get performance analysis"""
    try:
        # Parse game state
        game_state = GameState(**request.game_state)
        
        # Analyze performance
        performance = await _analyze_performance(
            game_state,
            request.answer,
            request.time_taken,
            request.model_name,
            request.api_key,
            request.provider
        )
        
        # Add to performance history
        game_state.user_performance.append(performance)

        # Apply dice-roll modifier if enabled
        dice_effect_desc = None
        if getattr(game_state.game_config, "dice_enabled", False) and request.dice_result is not None:
            dr = max(0, min(10, request.dice_result))
            try:
                game_master = get_game_master_agent(
                    model_name=request.model_name,
                    api_key=request.api_key,
                    provider=request.provider or "google",
                )
                state_change = await game_master.update_clinical_case(
                    current_case_state=game_state.case_state,
                    case_metadata=getattr(game_state, "case_metadata", None),
                    user_performance=performance,
                    user_answer=request.answer,
                    model_answer=getattr(game_state.case_state, "answer", None),
                    dice_result=dr,
                    existing_npc_states=getattr(game_state.case_state, "npc_states", None),
                    game_world=game_state.game_world,
                )
                game_state.case_state = state_change.updated_case_state
                dice_effect_desc = state_change.change_description
            except Exception as dice_err:
                print(f"Dice effect error (non-critical): {dice_err}")

        # Award XP for completing a case: 50-100 based on performance score (0-10 scale)
        user_id = game_state.user_id
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
                print(f"Error awarding game XP: {xp_err}")
        
        # Update cache and database with error handling
        try:
            redis_conn = await get_redis()
            if redis_conn:
                await redis_conn.setex(
                    f"gs:{game_state.game_id}",
                    3600,
                    json.dumps(game_state.model_dump(), default=str)
                )
        except Exception as e:
            print(f"Redis cache error (non-critical): {e}")
        
        try:
            update_payload = {
                "state": game_state.model_dump(mode="json", default=str),
                "updated_at": datetime.now().isoformat(),
            }
            await _sb(
                lambda: supabase.table("game_states")
                .update(update_payload)
                .eq("id", game_state.game_id)
                .execute()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save game state: {str(e)}")
        
        resp = {
            "success": True,
            "performance": performance.model_dump(mode="json", default=str),
            "game_state": game_state.model_dump(mode="json", default=str),
        }
        if dice_effect_desc:
            resp["dice_effect"] = dice_effect_desc
        return resp

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.post("/game/dice-effect")
async def apply_dice_effect(request: Dict[str, Any]):
    """Apply a standalone dice-roll effect to the current case state (toggleable)."""
    try:
        game_state = GameState(**request.get("game_state", {}))
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
                "state": game_state.model_dump(mode="json", default=str),
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
            "game_state": game_state.model_dump(mode="json", default=str),
            "dice_result": dice_result,
            "change_description": state_change.change_description,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dice effect failed: {str(e)}")


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
            print(f"Redis read error (non-critical): {e}")
        
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
            raise HTTPException(status_code=500, detail=f"Failed to read from database: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get game: {str(e)}")


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
            print(f"Redis delete error (non-critical): {e}")
        
        # Delete from Supabase with error handling
        try:
            await _sb(
                lambda: supabase.table("game_states").delete().eq("id", game_id).execute()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete from database: {str(e)}")
        
        return {"success": True, "message": "Game deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete game: {str(e)}")


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
    from pydantic_ai.models.gemini import GeminiModel
    from pydantic_ai.providers.google_gla import GoogleGLAProvider
    from pydantic_ai.models.openai import OpenAIModel
    
    # Initialize model
    if provider.lower() == "openai":
        model = OpenAIModel(model_name or "gpt-4", api_key=api_key)
    else:
        model = GeminiModel(
            model_name or "gemini-2.0-flash-exp",
            provider=GoogleGLAProvider(api_key=api_key)
        )
    
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
    """
    Save game state to Supabase
    Note: This is redundant with /game/initialize which already saves the game.
    Keeping for backward compatibility but consider using initialize endpoint instead.
    """
    try:
        # Parse game state
        game_state = GameState(**request.game_state)
        user_id = request.user_id or game_state.user_id
        
        # Save to Supabase
        gs_payload = {
            "id": game_state.game_id,
            "user_id": user_id,
            "case_id": game_state.case_id,
            "state": game_state.model_dump(mode="json", default=str),
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        creation_payload = {
            "user_id": user_id,
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
        
        # Cache in Redis
        redis_conn = await get_redis()
        if redis_conn:
            await redis_conn.setex(
                f"gs:{game_state.game_id}",
                3600,
                json.dumps(game_state.model_dump(), default=str)
            )
        
        return {
            "success": True,
            "message": "Game saved successfully",
            "game_state_id": game_state.game_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save game: {str(e)}")


@router.post("/game/save-checkpoint")
async def save_checkpoint(
    user_id: str,
    game_state_id: str,
    checkpoint_name: str,
    checkpoint_id: Optional[str] = None,
    description: Optional[str] = None
):
    """Save a game checkpoint"""
    try:
        # Get current game state
        game_state_result = await _sb(
            lambda: supabase.table("game_states").select("*").eq("id", game_state_id).execute()
        )
        if not game_state_result.data:
            raise HTTPException(status_code=404, detail="Game state not found")
        
        checkpoint_id = checkpoint_id or f"checkpoint-{datetime.now().timestamp()}"
        
        checkpoint_payload = {
            "user_id": user_id,
            "game_state_id": game_state_id,
            "checkpoint_id": checkpoint_id,
            "checkpoint_name": checkpoint_name,
            "state": game_state_result.data[0]["state"],
            "description": description,
            "created_at": datetime.now().isoformat(),
        }
        await _sb(
            lambda: supabase.table("game_checkpoints").insert(checkpoint_payload).execute()
        )
        
        return {"success": True, "checkpoint_id": checkpoint_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save checkpoint: {str(e)}")
