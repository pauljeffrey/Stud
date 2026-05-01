"""
Refactored Game Master Agent for ClinicaQuest
Responsible for generating clinical cases, managing achievements, and orchestrating game flow
Handles 20-50 unique clinical cases per adventure
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pydantic_ai import Agent, RunContext
import os
import json
import uuid
from datetime import datetime

try:
    from configs.config import Config
except ImportError:
    class Config:
        GAME_MASTER_NAME = "Game Master"
from agents.agents import get_game_master_model
from models.states import (
    GameState, GameWorldModel, CaseState, NPCState,
    Achievement, AchievementType, PerformanceAnalysis, GameConfig,
    ClinicalCaseMetadata, PreviousCases, DifficultyLevel,
    UserDetails, GameStateUpdateOutput,
)
from agents.achievement_subagent import generate_achievements as generate_achievements_agent
from agents.game_world_agent import get_game_world_agent
from agents.state_controller_agent import get_state_controller_agent
from agents.npc_agent import get_npc_agent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ModelRequest, UserPromptPart, SystemPromptPart
from utils import (
    process_chat_history_for_model_inference,
    save_chat_history_to_storage,
    get_chat_history_from_storage
)
from typing import Union
from configs.config import config
from utils import search_internet


@dataclass
class ChatContext:
    """Dependencies for chat agent tools."""
    game_state: GameState
    user_id: str
    session_id: str


def _case_to_dict(c: CaseState) -> str:
    """Serialize case state for tool output."""
    d = {
        "case_state_id": getattr(c, "case_state_id", ""),
        "scenario": getattr(c, "clinical_case_scenario_description", ""),
        "question": getattr(c, "question", ""),
        "diagnosis": getattr(c, "diagnosis", ""),
        "answer": getattr(c, "answer", ""),
        "reason_for_answer": getattr(c, "reason_for_answer", ""),
        "clue": getattr(c, "clue", ""),
        "n_changes": getattr(c, "n_changes", 0),
        "max_clinical_changes": getattr(c, "max_clinical_changes", 0),
        "clue_used": getattr(c, "clue_used", False),
    }
    return json.dumps(d, indent=2)


def fetch_previous_cases(ctx: RunContext[ChatContext], n_chars: int=150) -> str:
    """Fetch list of previous cases in this game. n_chars is the number of characters to preview the scenario."""
    gs = ctx.deps.game_state
    prev = getattr(gs, "previous_cases", None)
    if not prev or not prev.cases:
        return "No previous cases in this game."
    out = []
    for i, c in enumerate(prev.cases, 1):
        out.append({
            "index": i,
            "case_state_id": getattr(c, "case_state_id", ""),
            "scenario_preview": (c.clinical_case_scenario_description or "")[:n_chars],
            "question_preview": (c.question or "")[:n_chars],
            "diagnosis": c.diagnosis or "N/A",
        })
    return json.dumps(out, indent=2)

class GameMasterAgent:
    """
    Game Master Agent responsible for:
    1. Generating clinical cases (20-50 per adventure)
    2. Managing user achievements (career growth, promotions, etc.)
    3. Dynamically controlling game world based on performance
    4. Handoff coordination with State Controller Agent
    """
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, provider: str = "google"):
        """
        Initialize the Game Master Agent

        Args:
            model_name: Name of the AI model to use
            api_key: API key for the model
            provider: "google" or "openai"
        """
        self.model_name = model_name
        self.api_key = api_key
        self.provider = provider
        model = get_game_master_model(model_name, api_key)
        self.game_master_system_prompt = """
            You are the Game Master for Stud, a medical education role-playing game. You generate clinical case metadata, manage user achievements,
            and dynamically control the game world and events based on user performance using a gamestate.
            
            Given a provided game world, you coordinate with other agents to create a gamified and engaging medical education experience.
            Generate unique clinical cases per adventure covering diverse aspects of the provided user's field/profession/subject of study/document content,
            including OSCEs, ethics, education, clinical skills, counseling, behavioral challenges (difficult patients, relatives, situations or work colleagues), and communication challenges. 
            You intelligently adjust case difficulty depending on user performance and previous cases difficulty level.
            The game world is a realistic representation of the user's environment as you will be provided, and can be updated based on user performance. 
            """
       
        self.agent = Agent(
            model,
            system_prompt=self.game_master_system_prompt,
            output_type=Union[GameState, GameStateUpdateOutput],  # Main output type, but individual methods may return other types
            tools=[fetch_previous_cases]
        )
        
        # Chat agent will be initialized dynamically with game state context
        self.chat_agent = None

        # Get other agents
        self.game_world_agent = get_game_world_agent(model_name, api_key, provider)
        self.state_controller = get_state_controller_agent(model_name, api_key, provider)
        self.npc_agent = get_npc_agent(model_name, api_key, provider)
        self.setup_tools()
        
    def setup_tools(self):
        return
        

    def setup_tools_for_chat_agent(self) -> None:
        """Register tools on chat_agent for contesting answers and fetching game/case data."""
        if self.chat_agent is None:
            return

        @self.chat_agent.tool
        async def get_case_details(ctx: RunContext[ChatContext], case_index: Optional[int] = None, case_state_id: Optional[str] = None) -> str:
            """Return one case by 1-based index or case_state_id; else a compact index map of all cases."""
            gs = ctx.deps.game_state
            prev = getattr(gs, "previous_cases", None)
            past = list(prev.cases) if prev and getattr(prev, "cases", None) else []
            cur = getattr(gs, "case_state", None)
            seen = {str(getattr(c, "case_state_id", "")) for c in past}
            ordered: List[CaseState] = past[:]
            if cur and str(getattr(cur, "case_state_id", "")) not in seen:
                ordered.append(cur)

            if case_state_id:
                for c in ordered:
                    if c and str(getattr(c, "case_state_id", "")) == str(case_state_id):
                        return _case_to_dict(c)
                return json.dumps({"error": "case_state_id not found", "case_state_id": case_state_id})

            if case_index is not None:
                if 1 <= case_index <= len(ordered):
                    return _case_to_dict(ordered[case_index - 1])
                return json.dumps({"error": "case_index out of range", "case_index": case_index, "total": len(ordered)})

            summary = {}
            for i, c in enumerate(ordered, start=1):
                summary[str(i)] = {
                    "case_state_id": getattr(c, "case_state_id", ""),
                    "diagnosis": getattr(c, "diagnosis", None) or "",
                    "question": (getattr(c, "question", None) or "")[:400],
                    "clinical_case_scenario_description": (getattr(c, "clinical_case_scenario_description", None) or "")[:600],
                }
            return json.dumps(summary, indent=2) if summary else "No cases in this session."

        @self.chat_agent.tool
        async def get_all_previous_game_states(ctx: RunContext[ChatContext]) -> str:
            """Get timeline of game progression: cases completed with performance scores and scenario previews."""
            gs = ctx.deps.game_state
            perf = getattr(gs, "user_performance", []) or []
            prev = getattr(gs, "previous_cases", None)
            cases = prev.cases if prev else []
            out = []
            for i, p in enumerate(perf):
                c = cases[i] if i < len(cases) else None
                entry = {
                    "case": i + 1,
                    "score": getattr(p, "score", 0),
                    "analysis": getattr(p, "analysis", ""),
                    "clinical_state_id": getattr(p, "clinical_state_id", ""),
                }
                if c:
                    entry["scenario_preview"] = (getattr(c, "clinical_case_scenario_description", "") or "")[:200]
                    entry["question"] = (getattr(c, "question", "") or "")[:150]
                out.append(entry)
            return json.dumps(out, indent=2) if out else "No completed cases yet."

        @self.chat_agent.tool
        async def get_game_state_details(ctx: RunContext[ChatContext]) -> str:
            """Get current game state summary: case number, difficulty, achievements, performance."""
            gs = ctx.deps.game_state
            return json.dumps({
                "game_id": getattr(gs, "game_id", ""),
                "current_case": getattr(gs, "current_case_number", 0),
                "total_cases": getattr(gs, "total_cases", 0),
                "difficulty": str(getattr(gs, "difficulty_level", "")),
                "achievements": [{"title": a.title, "type": a.type.value} for a in getattr(gs, "achievements", [])],
                "performance_count": len(getattr(gs, "user_performance", [])),
            }, indent=2)

        @self.chat_agent.tool
        async def search_mediquest_sources(ctx: RunContext[ChatContext], query: str, use_internet: bool = False) -> str:
            """
            Search documents used to create this game or the internet. Use when user contests an answer.
            Set use_internet=True to search the web.
            """
            gs = ctx.deps.game_state
            cfg = getattr(gs, "game_config", None)
            doc_id = getattr(cfg, "document_id", None) if cfg else None
            doc_content = getattr(cfg, "document_content", None) if cfg else None

            if use_internet:
                return await search_internet(query, getattr(config, "SERPER_API_KEY", None))

            if doc_id:
                try:
                    from service.document_processor import get_document_processor
                    proc = get_document_processor()
                    results = await proc.search_documents(query=query, document_id=doc_id, top_k=5)
                    if not results:
                        return "No matching content in document."
                    top_idx = int(results[0].get("chunk_index", 0)) if results else 0
                    extra = await proc.get_adjacent_db_chunks(
                        doc_id, top_idx, before=1, after=1
                    )
                    seen = set()
                    parts: List[str] = []
                    for r in results:
                        t = (r.get("content") or "").strip()
                        if t and t not in seen:
                            seen.add(t)
                            parts.append(t)
                    for row in extra:
                        t = (row.get("content") or "").strip()
                        if t and t not in seen:
                            seen.add(t)
                            parts.append(t)
                    return "\n\n---\n\n".join(parts) if parts else "No matching content in document."
                except Exception as e:
                    return f"Document search failed: {e}"

            if doc_content and len(doc_content) > 100:
                q = query.lower()
                parts = doc_content.split()
                matches = []
                for i in range(0, len(parts) - 5):
                    window = " ".join(parts[i : i + 10]).lower()
                    if q in window:
                        matches.append(" ".join(parts[max(0, i - 5) : i + 15]))
                        if len(matches) >= 3:
                            break
                return "\n\n---\n\n".join(matches) if matches else "No matching content in document."

            return "No document source for this game. Use use_internet=True to search the web."
    
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Reinitialize with new user-provided credentials."""
        if model_name is not None:
            self.model_name = model_name
        if api_key is not None:
            self.api_key = api_key
        model = get_game_master_model(self.model_name, self.api_key)
        self.agent = Agent(
            model,
            system_prompt=self.game_master_system_prompt,
            output_type=Union[GameState, GameStateUpdateOutput],
            tools=[fetch_previous_cases]
        )
        self.chat_agent = None
        self.setup_tools()
    
    def _determine_difficulty_level(
        self,
        initial_difficulty: Optional[DifficultyLevel],
        previous_cases: Optional[PreviousCases] = None,
        user_performance: List[PerformanceAnalysis]= None
    ) -> DifficultyLevel:
        """
        Determine difficulty level based on:
        1. Initial difficulty (if provided, especially for demo)
        2. Previous cases difficulty progression
        3. User performance history
        """
        # If we have user performance, adjust difficulty based on average score
        if user_performance:
            avg_score = sum(p.score for p in user_performance) / len(user_performance)
            match avg_score: 
                case avg_score if avg_score >= 9.0:
                    return DifficultyLevel.Impossible
                case score if score >= 7.0:
                    return DifficultyLevel.Fiendish
                case score if score >= 5.0:
                    return DifficultyLevel.Hard
                case score if score >= 3.0:
                    return DifficultyLevel.Medium
                case _:
                    return DifficultyLevel.Easy
                
        # If initial difficulty provided (demo mode), use it
        if initial_difficulty:
            return initial_difficulty
        
        # If we have previous cases, use their difficulty level
        if previous_cases and previous_cases.cases:
            return previous_cases.current_difficulty_level
        
        # Default to Medium
        return DifficultyLevel.Easy
    
    
    async def initialize_game(
        self,
        game_config: GameConfig,
        user_id: str,
        is_demo: bool = False,
        user_details: Optional[Union[UserDetails, dict, str]] = None,
        initial_difficulty: Optional[DifficultyLevel] = None
    ) -> tuple:
        """
        Initialize a new game adventure
        
        Args:
            game_config: Game configuration
            user_id: User ID
            is_demo: Whether this is a demo game
            initial_difficulty: Initial difficulty level (for demo mode selection)
            
        Returns:
            Tuple of (game_world, game_state, case_state, npc_states, previous_cases)
        """
        # Create game world
        game_world = await self.game_world_agent.create_world(game_config)
        
        # Initialize previous cases
        previous_cases = PreviousCases(
            cases=[],
            n_cases_generated=0,
            current_difficulty_level=initial_difficulty or DifficultyLevel.Easy
        )
        
        user_performance: List[PerformanceAnalysis] = []
        difficulty_level = self._determine_difficulty_level(initial_difficulty, previous_cases, user_performance)
        
        user_details_dict = (
            user_details.model_dump() if isinstance(user_details, UserDetails)
            else user_details if isinstance(user_details, dict)
            else {"user id": user_id, "details": str(user_details)}
        ) if user_details else {"user_id": user_id}
        if "user id" not in user_details_dict:
            user_details_dict["user id"] = user_id

        result = await self.agent.run(f""" 
                                Game world: {json.dumps(game_world)}
                                User details: {json.dumps(user_details_dict)}
                                Generate a game state for the game given the above.
                                """)
        
        game_state = result.output
        if is_demo:
            game_state.is_demo = True
            game_state.total_cases = 3
            game_state.game_config = game_state.game_config.model_copy(update={
                "total_cases": 3,
                "max_clinical_changes": 3,
            })
            game_state.demo_limits = {"total_cases": 3, "max_clinical_changes": 3}

        # Generate first clinical case
        try:
            case_state, previous_cases = await self._generate_clinical_case(
                game_config=game_config,
                case_number=1,
                user_id=user_id,
                game_world=game_world,
                case_metadata=game_state.case_metadata,
                previous_cases=previous_cases
            )
        except Exception as e:
            raise Exception(f"Failed to generate first clinical case: {str(e)}")

        if is_demo:
            case_state.max_clinical_changes = 3
        
        # Create NPCs for this case (all at once)
        try:
            npc_states = await self.npc_agent.generate_all_npcs_for_case(
                case_state=case_state,
                game_world=game_world
            )
            case_state.npc_states = npc_states
        except Exception as e:
            raise Exception(f"Failed to generate NPCs: {str(e)}")

        game_state.game_world = game_world
        game_state.case_state = case_state
        game_state.previous_cases = previous_cases
        game_state.user_id = user_id
        return game_world, game_state, case_state, npc_states, previous_cases
        
    
    async def _generate_clinical_case(
        self,
        game_config: GameConfig,
        case_number: int,
        user_id: str,
        game_world: GameWorldModel,
        case_metadata: ClinicalCaseMetadata,
        prev_case_state: CaseState = None,
        previous_cases: Optional[PreviousCases] = None
    ) -> CaseState:
        """Generate a clinical case scenario"""
        
        # Build previous cases context to prevent duplicates
        previous_cases_context = ""
        if previous_cases:
            previous_cases_list = []
            for prev_case in previous_cases.cases:
                previous_cases_list.append({
                    "scenario": prev_case.clinical_case_scenario_description[:200],
                    "diagnosis": prev_case.diagnosis or "Unknown",
                    "question": prev_case.question[:200]
                })
            previous_cases_context = f"""
        
        PREVIOUS CASES (DO NOT REPEAT THESE):
        {json.dumps(previous_cases_list, indent=2)}
        
        IMPORTANT: Generate a completely NEW and UNIQUE case that is different from all previous cases.
        Do not reuse scenarios, exact diagnoses, or questions from the previous cases listed above.
        """
        
        # Build prompt using case_metadata (which already contains previous_cases_summary)
        prompt = f"""
        Generate clinical case #{case_number} for a medical education role-playing game.
        
        Game World Context:
        {game_config.model_dump()}
        
        Game world description: {game_world.world_description}
        
        Case Generation Metadata: 
        - Difficulty Level: {case_metadata.difficulty_level}
        - Case Number: {case_metadata.case_number}
        
        IMPORTANT: Generate a completely NEW and UNIQUE case that is different from all previous cases.
        Do not reuse scenarios, diagnoses, or questions from the previous cases listed above.
        
        Case Requirements:
        - Should cover aspects relevant to {game_config.profession} practice
        - Can include: ethics, counseling, behavioral issues, communication challenges, clinical skills, difficult patients/relatives, difficult work colleagues etc.
        - Difficulty level: {case_metadata.difficulty_level} (adjust complexity accordingly)
        - Must be medically accurate and educational
        - MUST be unique and different from previous cases
        
        {previous_cases_context}
        
        Generate a complete clinical case state     
        
        """
        
        try:
            result = await self.state_controller.run(prompt)
            # For now, result.output should be a dict-like object we can convert to CaseState
            case_state = result.output
            
            # Add case to previous cases
            if previous_cases is None:
                previous_cases = PreviousCases(
                    cases=[],
                    n_cases_generated=1,
                    current_difficulty_level=case_metadata.difficulty_level
                )
            
            previous_cases.add_case(case_state)
            previous_cases.current_difficulty_level = case_metadata.difficulty_level
            
            return case_state, previous_cases
        
        except Exception as e:
            return prev_case_state, previous_cases
    

    async def update_game(
        self,
        game_state: GameState,
        previous_cases: PreviousCases,
        user_performance: List[PerformanceAnalysis],
        achievements: List[Achievement],
        updated_game_world: GameWorldModel,
    ) -> GameState:
        """
        Update game_state for state_controller (case generation, escalation/de-escalation).
        Called by handoff_from_state_controller after updating the game world.
        """
        previous_difficulty_levels = previous_cases.get_previous_difficulty_levels()
        avg_score = (
            sum(p.score for p in user_performance) / len(user_performance)
            if user_performance else 5.0
        )

        prompt = f"""
        Game world description: {updated_game_world.world_description}
        Update game state for next case generation.
        Previous cases: {len(previous_cases.cases)}; difficulty history: {[d.value for d in previous_difficulty_levels]}
        User performance: avg {avg_score:.1f}/10, {len(user_performance)} cases
        Achievements: {[a.title for a in achievements]}
        Game config: {game_state.game_config.model_dump()}
        Current difficulty: {game_state.difficulty_level.value}
        Case {game_state.current_case_number} of {game_state.total_cases}

        Return difficulty_level and case_metadata for the next case. Adjust difficulty based on performance.
        """
        try:
            result = await self.agent.run(prompt)
            out = result.output 
            if isinstance(out, GameStateUpdateOutput):
                game_state.difficulty_level = out.difficulty_level
                if out.case_metadata:
                    game_state.case_metadata = out.case_metadata
            elif isinstance(out, GameState):
                game_state.difficulty_level = out.difficulty_level
                if out.case_metadata:
                    game_state.case_metadata = out.case_metadata
        except Exception:
            pass
        game_state.game_world = updated_game_world
        game_state.last_updated = datetime.now()
        return game_state

    async def update_clinical_case(
        self,
        current_case_state: CaseState,
        case_metadata: Optional[ClinicalCaseMetadata] = None,
        user_performance: Optional[PerformanceAnalysis] = None,
        time_elapsed: int = 0,
        clue_used: bool = False,
        user_answer: Optional[str] = None,
        model_answer: Optional[str] = None,
        dice_result: Optional[int] = None,
        existing_npc_states: Optional[List[NPCState]] = None,
        game_world: Optional[GameWorldModel] = None,
    ):
        """
        Escalate or de-escalate an existing clinical case.
        If dice_result (0-10) is provided, it modifies escalation intensity.
        """
        prev_el_ratio = current_case_state.n_changes / max(1, current_case_state.max_clinical_changes)
        result = await self.state_controller.update_case_state(
            current_case_state=current_case_state,
            case_metadata=case_metadata,
            user_performance=user_performance,
            time_elapsed=time_elapsed,
            clue_used=clue_used,
            user_answer=user_answer,
            model_answer=model_answer,
        )
        if dice_result is not None and 0 <= dice_result <= 10:
            modifier = (dice_result - 5) / 10.0
            result.escalation_level = max(0.0, min(1.0, result.escalation_level + modifier))
        if existing_npc_states and game_world:
            delta = result.escalation_level - prev_el_ratio
            result.updated_case_state.npc_states = await self.npc_agent.update_npcs_for_case(
                existing_npc_states,
                result.updated_case_state,
                delta,
                game_world,
                change_description=result.change_description,
            )
        return result

    async def handoff_from_state_controller(
        self,
        game_state: GameState,
        final_performance: PerformanceAnalysis
    ) -> GameState:
        """
        Handle handoff from State Controller when max_clinical_changes is reached.
        1. Update game world dynamically
        2. Generate achievements via sub-agent
        3. Update game_state via update_game (difficulty, case_metadata)
        4. Create next clinical scenario
        """
        game_state.user_performance.append(final_performance)
        avg_score = (
            sum(p.score for p in game_state.user_performance) / len(game_state.user_performance)
            if game_state.user_performance else 5.0
        )

        achievements_out = await generate_achievements_agent(
            avg_score=avg_score,
            user_performance_scores=[p.score for p in game_state.user_performance],
            previous_achievements=game_state.achievements,
            current_case_number=game_state.current_case_number,
            total_cases=game_state.total_cases,
            difficulty_level=game_state.difficulty_level,
            profession=getattr(game_state.game_config, "profession", None),
        )
        game_state.achievements.extend(achievements_out.achievements)

        updated_world = await self._update_game_world(game_state, avg_score)
        previous_cases = game_state.previous_cases or PreviousCases(
            cases=[],
            n_cases_generated=0,
            current_difficulty_level=game_state.difficulty_level,
        )
        existing_ids = {c.case_state_id for c in previous_cases.cases}
        if game_state.case_state.case_state_id not in existing_ids:
            previous_cases.add_case(game_state.case_state)

        game_state = await self.update_game(
            game_state=game_state,
            previous_cases=previous_cases,
            user_performance=game_state.user_performance,
            achievements=game_state.achievements,
            updated_game_world=updated_world,
        )
        game_state.previous_cases = previous_cases

        # Generate next case if not at limit
        if game_state.current_case_number < game_state.total_cases:
            game_state.current_case_number += 1
            
            # Get previous cases from game state (should be managed externally)
            # For now, create PreviousCases from current case
            previous_cases = PreviousCases(
                cases=[{
                    "case_state_id": game_state.case_state.case_state_id,
                    "clinical_case_scenario_description": game_state.case_state.clinical_case_scenario_description,
                    "diagnosis": game_state.case_state.diagnosis,
                    "question": game_state.case_state.question
                    }],
                n_cases_generated=game_state.current_case_number - 1,
                current_difficulty_level=game_state.difficulty_level
            )
            
            case_metadata = game_state.case_metadata
            case_metadata.previous_cases_summary = previous_cases.get_summary_for_metadata()
            case_metadata.case_number = game_state.current_case_number
            case_metadata.difficulty_level = game_state.difficulty_level

            try:
                # Generate next case
                next_case, previous_cases = await self._generate_clinical_case(
                    game_config=game_state.game_config,
                    case_number=game_state.current_case_number,
                    user_id=game_state.user_id,
                    game_world=game_state.game_world,
                    case_metadata=case_metadata,
                    previous_cases=previous_cases
                )
            except Exception as e:
                raise Exception(f"Failed to generate next case: {str(e)}")
            
            game_state.case_state = next_case
            
            # Generate all NPCs at once
            try:
                npc_states = await self.npc_agent.generate_all_npcs_for_case(
                    case_state=next_case,
                    game_world=game_state.game_world
                )
                game_state.case_state.npc_states = npc_states
            except Exception as e:
                raise Exception(f"Failed to generate NPCs for next case: {str(e)}")
        
        game_state.last_updated = datetime.now()
        
        return game_state
    
    async def _update_game_world(
        self,
        game_state: GameState,
        avg_score: float
    ) -> GameWorldModel:
        """Dynamically update game world based on performance"""
        
        # If performance is high, world improves (better resources, etc.)
        # If performance is low, world becomes more challenging
        
        prompt = f"""
        Update the game world based on user performance.
        
        Current World:
        - Description: {game_state.game_world.world_description[:500]}
        - era: {game_state.game_world.era}
        - natural conditions: {game_state.game_world.natural_conditions}
        - nation type: {game_state.game_world.nation_type}
        - economic advantage: {game_state.game_world.economic_advantage}
        - location: {game_state.game_world.location}
        - Hospital: {game_state.game_world.hospital_name}
        - Department: {game_state.game_world.department}
        
        User Performance:
        - Average Score: {avg_score}/10
        - Cases Completed: {game_state.current_case_number}/{game_state.total_cases}
        - User Achievements: {len(game_state.achievements)}
        
        Update the world to reflect:
        1. Improved resources if performance is high
        2. New challenges if performance is low
        3. Career progression based on achievements
        
        Return updated GameWorldModel as JSON.
        """
        
        try:
            updated = await self.game_world_agent.run(prompt)
            if not isinstance(updated, GameWorldModel):
                return game_state.game_world
            if not updated.world_id:
                updated.world_id = game_state.game_world.world_id
            return updated
        except Exception as e:
            print(f"Failed to update game world: {e}")
            return game_state.game_world
    
    async def chat_with_game_master(
        self,
        game_state: GameState,
        user_message: str,
        user_id: str,
        session_id: str,
        chat_history: Optional[List[Union[ModelRequest, ModelResponse]]] = None
    ) -> tuple[str, List[Union[ModelRequest, ModelResponse]]]:
        """
        Handle chat with game master
        
        Args:
            game_state: Current game state (includes clue usage info)
            user_message: User's message
            user_id: User ID for chat history storage
            session_id: Game session ID
            chat_history: Previous chat history (retrieved from storage)
            
        Returns:
            Tuple of (response, updated_chat_history)
        """
        # Retrieve chat history from storage if not provided
        if chat_history is None:
            chat_history = await get_chat_history_from_storage(
                user_id=user_id,
                conversation_id=session_id,
                chat_type="game_master"
            )
        
        # Build system prompt with game state context (including clue usage)
        system_prompt = f"""
        You are {Config.GAME_MASTER_NAME}, the Game Master for Stud. The user is playing a medical education game with you.
        
        Current Game State:
        - Case #{game_state.current_case_number}/{game_state.total_cases}
        - Scenario: {game_state.case_state.clinical_case_scenario_description}
        - Question: {game_state.case_state.question}
        - Clue Used: {game_state.case_state.clue_used} (if True, user has already used a clue - be more cautious with hints)
        - Difficulty Level: {game_state.difficulty_level}
        - User Performance: {len(game_state.user_performance)} cases completed
        - Time Remaining: {game_state.case_state.time_remaining_seconds} seconds
        
        Respond as the Game Master, providing guidance, hints, or encouragement.
        Stay in character and be helpful but don't give away answers directly.
        If clue_used is True, the user has already received help - adjust your responses accordingly.

        Use your tools to fetch previous cases, case details, escalation info, game state, and search documents/internet.
        Use them when the user contests an answer or asks for evidence.
        """
        
        # Initialize chat history with system prompt if empty
        if not chat_history:
            chat_history = [ModelRequest(parts=[SystemPromptPart(content=system_prompt)])]
        else:
            # Ensure system prompt is first
            if not isinstance(chat_history[0], ModelRequest) or not any(
                isinstance(part, SystemPromptPart) for part in chat_history[0].parts
            ):
                chat_history.insert(0, ModelRequest(parts=[SystemPromptPart(content=system_prompt)]))
        
        # Process chat history for model inference
        chat_history = process_chat_history_for_model_inference(chat_history)
        
        # Create chat agent with current context (recreated each chat so system prompt stays current)
        model = get_game_master_model(self.model_name, self.api_key)
        self.chat_agent = Agent(
            model,
            deps_type=ChatContext,
            system_prompt=system_prompt,
            output_type=str,
        )
        self.setup_tools_for_chat_agent()

        deps = ChatContext(game_state=game_state, user_id=user_id, session_id=session_id)
        try:
            result = await self.chat_agent.run(user_message, deps=deps, message_history=chat_history)
            response = result.output
            
            # Update chat history
            chat_history.append(ModelRequest(parts=[UserPromptPart(content=user_message)]))
            chat_history.append(ModelResponse(parts=[TextPart(content=response)]))
            
            # Save chat history to storage (background job)
            await save_chat_history_to_storage(
                chat_history=chat_history,
                user_id=user_id,
                conversation_id=session_id,
                chat_type="game_master",
                background=True
            )
            
            return response, chat_history
        
        except Exception as e:
            import logging
            logging.error(f"Game master chat error: {e}")
            return "An error occurred while processing your request. Please try again later.", chat_history or []



# Global instance
_game_master_instance: Optional[GameMasterAgent] = None


def get_game_master_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google"
) -> GameMasterAgent:
    """Get or create the global Game Master Agent instance"""
    global _game_master_instance
    if _game_master_instance is None:
        _game_master_instance = GameMasterAgent(model_name, api_key, provider)
    return _game_master_instance
