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

from models.states import GameState, GameConfig, CaseState, PerformanceAnalysis, Achievement
from agents.game_world_agent import get_game_world_agent
from agents.game_master import get_game_master_agent
from agents.state_controller_agent import get_state_controller_agent
from agents.npc_agent import get_npc_agent
from agents.dice_agent import get_dice_agent
from config import config
from supabase import create_client, Client
import redis.asyncio as redis

router = APIRouter()

# Initialize Supabase client
supabase: Client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_SERVICE_ROLE_KEY
)

# Initialize Redis client (if available)
redis_client: Optional[redis.Redis] = None

async def get_redis():
    """Get Redis client"""
    global redis_client
    if redis_client is None and config.REDIS_URL:
        redis_client = await redis.from_url(config.REDIS_URL)
    return redis_client


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================
class InitializeGameRequest(BaseModel):
    game_config: GameConfig
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"
    is_demo: bool = False


class GameMasterChatRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    user_message: str
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class NPCChatRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    npc_id: str
    user_message: str
    chat_history: Optional[List[Dict[str, str]]] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class UpdateCaseStateRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    time_elapsed: int = 0
    clue_used: bool = False
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class SubmitAnswerRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    answer: str
    time_taken: int
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class UseClueRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class SaveGameRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    user_id: Optional[str] = None


class DiceEffectRequest(BaseModel):
    game_state: Dict[str, Any]  # GameState as dict
    dice_result: int  # 1-6
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


# ============================================
# API ENDPOINTS
# ============================================

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
                    existing = await redis_conn.get(f"demo_game:{demo_session_id}")
                    if existing:
                        raise HTTPException(
                            status_code=400,
                            detail="Demo game already exists for this session. Please register for full access."
                        )
            except Exception as e:
                # If Redis fails, check database
                try:
                    existing_demo = supabase.table("game_states").select("*").eq(
                        "user_id", user_id
                    ).eq("is_demo", True).execute()
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
            # Get user ID from JWT token (implement auth dependency)
            # For now, placeholder - should be: user_id = await get_current_user_id()
            user_id = "user_123"  # TODO: Get from auth
        
        # Get game master agent (singleton pattern - reuses instance)
        try:
            game_master = get_game_master_agent(
                model_name=request.model_name,
                api_key=request.api_key,
                provider=request.provider or "google"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize game master agent: {str(e)}")
        
        # Initialize game with error handling
        try:
            game_state = await game_master.initialize_game(
                game_config=request.game_config,
                user_id=user_id,
                is_demo=request.is_demo
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize game: {str(e)}")
        
        # Cache game state in Redis with error handling
        try:
            redis_conn = await get_redis()
            if redis_conn:
                await redis_conn.setex(
                    f"game_state:{game_state.game_id}",
                    3600,  # 1 hour expiry
                    json.dumps(game_state.model_dump(), default=str)
                )
                if request.is_demo:
                    await redis_conn.setex(
                        f"demo_game:{demo_session_id}",
                        3600,
                        game_state.game_id
                    )
        except Exception as e:
            # Log error but continue - Redis is optional
            print(f"Redis cache error (non-critical): {e}")
        
        # Save to Supabase with error handling
        try:
            supabase.table("game_states").insert({
                "id": game_state.game_id,
                "user_id": game_state.user_id,
                "case_id": game_state.case_id,
                "state": game_state.model_dump(mode="json", default=str),
                "is_demo": request.is_demo,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save game state: {str(e)}")
        
        return {
            "success": True,
            "game_state": game_state.model_dump(mode="json", default=str)
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
            
            # Get response
            response = await game_master.chat_with_game_master(
                game_state=game_state,
                user_message=request.user_message
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
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
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
            
            # Get response
            response = await npc_agent.chat_with_npc(
                npc_state=npc_state,
                user_message=request.user_message,
                case_state=game_state.case_state,
                chat_history=request.chat_history or []
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
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
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
        
        # Get state controller agent
        state_controller = get_state_controller_agent(
            model_name=request.model_name,
            api_key=request.api_key,
            provider=request.provider or "google"
        )
        
        # Get latest performance if available
        latest_performance = None
        if game_state.user_performance:
            latest_performance = game_state.user_performance[-1]
        
        # Update case state with metadata
        try:
            state_change = await state_controller.update_case_state(
                current_case_state=game_state.case_state,
                case_metadata=game_state.case_state.case_metadata,
                user_performance=latest_performance,
                time_elapsed=request.time_elapsed,
                clue_used=request.clue_used
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
                    f"game_state:{game_state.game_id}",
                    3600,
                    json.dumps(game_state.model_dump(), default=str)
                )
        except Exception as e:
            print(f"Redis cache error (non-critical): {e}")
        
        try:
            supabase.table("game_states").update({
                "state": game_state.model_dump(mode="json", default=str),
                "updated_at": datetime.now().isoformat()
            }).eq("id", game_state.game_id).execute()
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
        
        # Update cache and database with error handling
        try:
            redis_conn = await get_redis()
            if redis_conn:
                await redis_conn.setex(
                    f"game_state:{game_state.game_id}",
                    3600,
                    json.dumps(game_state.model_dump(), default=str)
                )
        except Exception as e:
            print(f"Redis cache error (non-critical): {e}")
        
        try:
            supabase.table("game_states").update({
                "state": game_state.model_dump(mode="json", default=str),
                "updated_at": datetime.now().isoformat()
            }).eq("id", game_state.game_id).execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save game state: {str(e)}")
        
        return {
            "success": True,
            "performance": performance.model_dump(mode="json", default=str),
            "game_state": game_state.model_dump(mode="json", default=str)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.get("/game/{game_id}")
async def get_game_state(game_id: str):
    """Get game state by ID"""
    try:
        # Try Redis first with error handling
        try:
            redis_conn = await get_redis()
            if redis_conn:
                cached = await redis_conn.get(f"game_state:{game_id}")
                if cached:
                    return {"success": True, "game_state": json.loads(cached)}
        except Exception as e:
            print(f"Redis read error (non-critical): {e}")
        
        # Fallback to Supabase with error handling
        try:
            result = supabase.table("game_states").select("*").eq("id", game_id).execute()
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
                await redis_conn.delete(f"game_state:{game_id}")
        except Exception as e:
            print(f"Redis delete error (non-critical): {e}")
        
        # Delete from Supabase with error handling
        try:
            supabase.table("game_states").delete().eq("id", game_id).execute()
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
        result = supabase.table("game_states").insert({
            "id": game_state.game_id,
            "user_id": user_id,
            "case_id": game_state.case_id,
            "state": game_state.model_dump(mode="json", default=str),
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }).execute()
        
        # Log game creation
        supabase.table("game_creation_log").insert({
            "user_id": user_id,
            "game_state_id": game_state.game_id,
            "scenario_type": "standard",
            "created_at": datetime.now().isoformat()
        }).execute()
        
        # Cache in Redis
        redis_conn = await get_redis()
        if redis_conn:
            await redis_conn.setex(
                f"game_state:{game_state.game_id}",
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
        game_state_result = supabase.table("game_states").select("*").eq("id", game_state_id).execute()
        if not game_state_result.data:
            raise HTTPException(status_code=404, detail="Game state not found")
        
        checkpoint_id = checkpoint_id or f"checkpoint-{datetime.now().timestamp()}"
        
        result = supabase.table("game_checkpoints").insert({
            "user_id": user_id,
            "game_state_id": game_state_id,
            "checkpoint_id": checkpoint_id,
            "checkpoint_name": checkpoint_name,
            "state": game_state_result.data[0]["state"],
            "description": description,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return {"success": True, "checkpoint_id": checkpoint_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save checkpoint: {str(e)}")

@router.post("/game/dice-effect")
async def apply_dice_effect(request: DiceEffectRequest):
    """
    Apply dice roll effects to the game scenario
    Uses Dice Agent to generate dramatic scenario changes based on dice result (1-6)
    """
    async def generate_effect():
        try:
            # Parse game state
            game_state = GameState(**request.game_state)
            
            # Validate dice result
            if not (1 <= request.dice_result <= 6):
                raise HTTPException(status_code=400, detail="Dice result must be between 1 and 6")
            
            # Get dice agent
            dice_agent = get_dice_agent(
                model_name=request.model_name,
                api_key=request.api_key,
                provider=request.provider or "google"
            )
            
            # Generate dice effect
            effect_description = await dice_agent.generate_dice_effect(
                game_state=game_state,
                dice_result=request.dice_result
            )
            
            # Update case state with dice effect
            game_state.case_state.clinical_case_scenario_description += f"\n\n[Dice Effect] {effect_description}"
            game_state.last_updated = datetime.now()
            
            # Stream the response
            words = effect_description.split()
            for i, word in enumerate(words):
                chunk = {
                    "content": word + " ",
                    "complete": i == len(words) - 1,
                    "dice_result": request.dice_result,
                    "updated_game_state": game_state.model_dump(mode="json", default=str) if i == len(words) - 1 else None
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.03)
                
        except HTTPException:
            raise
        except Exception as e:
            error_chunk = {"error": str(e), "complete": True}
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_effect(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )