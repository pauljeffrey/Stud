"""
Refactored Game Master Agent for ClinicaQuest
Responsible for generating clinical cases, managing achievements, and orchestrating game flow
Handles 20-50 unique clinical cases per adventure
"""
from typing import Optional, List, Dict, Any
from pydantic_ai import Agent
import os
import json
import uuid
from datetime import datetime

from config import config
from agents.base_agent import BaseAgent
from agents.agents import get_game_master_model
from models.states import (
    GameState, GameWorldModel, CaseState, NPCState, 
    Achievement, AchievementType, PerformanceAnalysis, GameConfig,
    ClinicalCaseMetadata
)
from agents.game_world_agent import get_game_world_agent
from agents.state_controller_agent import get_state_controller_agent
from agents.npc_agent import get_npc_agent


class GameMasterAgent(BaseAgent):
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
        super().__init__(model_name, api_key, provider)
        
        # Initialize agent using the pattern from agents.py
        # Note: We use GameState as output_type for consistency, but individual methods may return different types
        model = get_game_master_model(model_name, api_key)
        self.agent = Agent(
            model,
            system_prompt="""
            You are the Game Master for Stud. You generate clinical cases, manage user achievements,
            and dynamically control the game world based on user performance.
            
            You coordinate with other agents to create an engaging medical education experience.
            Generate 20-50 unique clinical cases per adventure covering various aspects of clinical practice
            including ethics, counseling, behavioral issues, and communication challenges.
            """,
            output_type=GameState  # Main output type, but individual methods may return other types
        )
        
        # Separate agent for chat (returns string)
        self.chat_agent = Agent(
            model,
            system_prompt="""
            You are the Game Master for Stud. Provide guidance, hints, and encouragement to players.
            Stay in character and be helpful but don't give away answers directly.
            """,
            output_type=str
        )
        
        # Get other agents
        self.game_world_agent = get_game_world_agent(model_name, api_key, provider)
        self.state_controller = get_state_controller_agent(model_name, api_key, provider)
        self.npc_agent = get_npc_agent(model_name, api_key, provider)
    
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Reinitialize the model"""
        super()._reinitialize_model(model_name, api_key)
        model = get_game_master_model(self.model_name, self.api_key)
        self.agent = Agent(
            model,
            system_prompt="""
            You are the Game Master for Stud. You generate clinical cases, manage user achievements,
            and dynamically control the game world based on user performance.
            
            You coordinate with other agents to create an engaging medical education experience.
            Generate 20-50 unique clinical cases per adventure covering various aspects of clinical practice
            including ethics, counseling, behavioral issues, and communication challenges.
            """,
            output_type=GameState
        )
        self.chat_agent = Agent(
            model,
            system_prompt="""
            You are the Game Master for Stud. Provide guidance, hints, and encouragement to players.
            Stay in character and be helpful but don't give away answers directly.
            """,
            output_type=str
        )
    
    async def initialize_game(self, game_config: GameConfig, user_id: str, is_demo: bool = False) -> GameState:
        """
        Initialize a new game adventure
        
        Args:
            game_config: Game configuration
            user_id: User ID
            is_demo: Whether this is a demo game
            
        Returns:
            Initialized GameState
        """
        # Create game world
        game_world = await self.game_world_agent.create_world(game_config)
        
        # Generate first clinical case (no previous cases)
        try:
            case_state = await self._generate_clinical_case(
                game_config=game_config,
                case_number=1,
                user_id=user_id,
                game_world=game_world,
                previous_cases=None
            )
        except Exception as e:
            raise Exception(f"Failed to generate first clinical case: {str(e)}")
        
        # Create NPCs for this case (all at once)
        try:
            npc_states = await self.npc_agent.generate_all_npcs_for_case(
                case_state=case_state,
                game_world=game_world
            )
        except Exception as e:
            raise Exception(f"Failed to generate NPCs: {str(e)}")
        
        # Create initial game state (agent already returns GameState, but we need to set IDs and config)
        # The agent's output_type is GameState, so result.output is already a GameState-like object
        # However, we need to ensure all fields are properly set
        try:
            # Use agent output directly since output_type=GameState
            # But we still need to set IDs and game_config
            game_state = GameState(
                game_id=str(uuid.uuid4()),
                user_id=user_id,
                case_id=str(uuid.uuid4()),
                game_world=game_world,
                case_state=case_state,
                game_config=game_config,  # Store config as object
                current_case_number=1,
                total_cases=game_config.total_cases,
                is_demo=is_demo,
                demo_limits={"max_cases": 3, "max_changes_per_case": 3} if is_demo else None
            )
            
            # Set NPCs in case_state
            case_state.npc_states = npc_states
            
            return game_state
        except Exception as e:
            raise Exception(f"Failed to create game state: {str(e)}")
    
    async def _generate_clinical_case(
        self,
        game_config: GameConfig,
        case_number: int,
        user_id: str,
        game_world: GameWorldModel,
        previous_cases: Optional[List[CaseState]] = None
    ) -> CaseState:
        """Generate a clinical case scenario"""
        
        # Build previous cases context to prevent duplicates
        previous_cases_context = ""
        if previous_cases:
            previous_cases_list = []
            for prev_case in previous_cases:
                previous_cases_list.append({
                    "scenario": prev_case.clinical_case_scenario_description[:200],
                    "diagnosis": prev_case.diagnosis or "Unknown",
                    "question": prev_case.question[:200]
                })
            previous_cases_context = f"""
        
        PREVIOUS CASES (DO NOT REPEAT THESE):
        {json.dumps(previous_cases_list, indent=2)}
        
        IMPORTANT: Generate a completely NEW and UNIQUE case that is different from all previous cases.
        Do not reuse scenarios, diagnoses, or questions from the previous cases listed above.
        """
        
        prompt = f"""
        Generate clinical case #{case_number} for a medical education role-playing game.
        
        Game World Context:
        - Profession: {game_config.profession}
        - Clinical Setting: {game_config.clinical_setting}
        - Subject Focus: {game_config.subject}
        - Era: {game_config.era}
        - World Description: {game_world.world_description[:500]}
        {previous_cases_context}
        
        Case Requirements:
        - Should cover aspects relevant to {game_config.profession} practice
        - Can include: ethics, counseling, behavioral issues, communication challenges, clinical skills, difficult patients, difficult work colleagues etc.
        - Difficulty should progress appropriately (case #{case_number} of {game_config.total_cases})
        - Must be medically accurate and educational
        - MUST be unique and different from previous cases
        
        Generate a complete clinical case with:
        1. clinical_case_scenario_description: Detailed scenario narrative
        2. question: The main clinical question/challenge
        3. investigations: Physical examination findings (dict)
        4. scan_images: Lab/imaging results (dict)
        5. options: Multiple choice options (if applicable, else null)
        6. answer: Correct answer/diagnosis
        7. reason_for_answer: Explanation of why this is correct
        8. clue: A helpful clue for the user
        9. max_clinical_changes: Number between 5-15 for state controller
        10. time_limit_seconds: Appropriate time limit
        
        Return a complete CaseState object.
        """
        
        try:
            result = await self.agent.run(prompt)
            # Agent output_type is GameState, but we're generating CaseState
            # So we need to extract the case_state from result or handle it differently
            # Actually, the agent's output_type should be CaseState for this method
            # But since the agent is initialized with GameState, we need to handle this
            
            # For now, result.output should be a dict-like object we can convert to CaseState
            case_data = result.output if hasattr(result, 'output') else result
            
            # Create CaseState - agent returns the structure, we just need to set IDs and metadata
            case_state = CaseState(
                case_state_id=str(uuid.uuid4()),
                user_id=user_id,
                case_id=str(uuid.uuid4()),
                clinical_case_scenario_description=case_data.get("clinical_case_scenario_description", "") if isinstance(case_data, dict) else getattr(case_data, "clinical_case_scenario_description", ""),
                question=case_data.get("question", "") if isinstance(case_data, dict) else getattr(case_data, "question", ""),
                diagnosis=case_data.get("answer") if isinstance(case_data, dict) else getattr(case_data, "answer", None),
                investigations=case_data.get("investigations", {}) if isinstance(case_data, dict) else getattr(case_data, "investigations", {}),
                scan_images=case_data.get("scan_images", {}) if isinstance(case_data, dict) else getattr(case_data, "scan_images", {}),
                options=case_data.get("options") if isinstance(case_data, dict) else getattr(case_data, "options", None),
                answer=case_data.get("answer") if isinstance(case_data, dict) else getattr(case_data, "answer", None),
                reason_for_answer=case_data.get("reason_for_answer") if isinstance(case_data, dict) else getattr(case_data, "reason_for_answer", None),
                clue=case_data.get("clue") if isinstance(case_data, dict) else getattr(case_data, "clue", None),
                max_clinical_changes=case_data.get("max_clinical_changes", 10) if isinstance(case_data, dict) else getattr(case_data, "max_clinical_changes", 10),
                time_limit_seconds=case_data.get("time_limit_seconds", 300) if isinstance(case_data, dict) else getattr(case_data, "time_limit_seconds", 300),
                time_remaining_seconds=case_data.get("time_limit_seconds", 300) if isinstance(case_data, dict) else getattr(case_data, "time_limit_seconds", 300),
                profession=game_config.profession,
                clinical_setting=game_config.clinical_setting,
                subject=game_config.subject,
                era=game_config.era,
                natural_conditions=game_config.natural_conditions,
                nation_type=game_config.nation_type,
                economic_advantage=game_config.economic_advantage,
                case_metadata=ClinicalCaseMetadata(
                    case_number=case_number,
                    profession=game_config.profession,
                    clinical_setting=game_config.clinical_setting,
                    subject=game_config.subject,
                    era=game_config.era,
                    natural_conditions=game_config.natural_conditions,
                    nation_type=game_config.nation_type,
                    economic_advantage=game_config.economic_advantage,
                    difficulty_level=game_config.difficulty,
                    previous_cases=[
                        {
                            "scenario": pc.clinical_case_scenario_description[:200],
                            "diagnosis": pc.diagnosis or "Unknown",
                            "question": pc.question[:200]
                        } for pc in (previous_cases or [])
                    ]
                )
            )
            
            return case_state
        except Exception as e:
            raise Exception(f"Failed to generate clinical case: {str(e)}")
    
    # Removed _create_npcs_for_case - NPC agent now handles all NPC generation
    
    async def handoff_from_state_controller(
        self,
        game_state: GameState,
        final_performance: PerformanceAnalysis
    ) -> GameState:
        """
        Handle handoff from State Controller when max_clinical_changes is reached
        Uses overall user performance to:
        1. Update game world dynamically
        2. Generate new achievements
        3. Create next clinical scenario
        """
        # Add performance to history
        game_state.user_performance.append(final_performance)
        
        # Calculate overall performance
        if game_state.user_performance:
            avg_score = sum(p.score for p in game_state.user_performance) / len(game_state.user_performance)
        else:
            avg_score = 5.0
        
        # Generate achievements based on performance
        achievements = await self._generate_achievements(game_state, avg_score)
        game_state.achievements.extend(achievements)
        
        # Update game world based on performance
        game_state.game_world = await self._update_game_world(game_state, avg_score)
        
        # Generate next case if not at limit
        if game_state.current_case_number < game_state.total_cases:
            game_state.current_case_number += 1
            
            # Collect previous cases to prevent duplicates
            previous_cases = []
            # Get previous cases from user_performance (they contain case_state_id references)
            # In a full implementation, you'd fetch previous case states from database
            # For now, we'll use the current case as reference
            
            try:
                # Create next case using game_config from game_state
                next_case = await self._generate_clinical_case(
                    game_config=game_state.game_config,
                    case_number=game_state.current_case_number,
                    user_id=game_state.user_id,
                    game_world=game_state.game_world,
                    previous_cases=[game_state.case_state]  # Include current case to avoid repetition
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
    
    async def _generate_achievements(
        self,
        game_state: GameState,
        avg_score: float
    ) -> List[Achievement]:
        """Generate achievements based on user performance"""
        
        achievements = []
        
        # High performance achievements
        if avg_score >= 8.0:
            achievements.append(Achievement(
                type=AchievementType.PROMOTION,
                title="Outstanding Performance",
                description=f"Promoted to Senior {game_state.profession}",
                value=None
            ))
        
        if avg_score >= 7.0:
            achievements.append(Achievement(
                type=AchievementType.FINANCIAL_REWARD,
                title="Performance Bonus",
                description="Received bonus for excellent clinical performance",
                value=5000.0
            ))
        
        # Milestone achievements
        if game_state.current_case_number == 10:
            achievements.append(Achievement(
                type=AchievementType.CERTIFICATION,
                title="10 Cases Mastered",
                description="Completed 10 clinical cases successfully",
                value=None
            ))
        
        if game_state.current_case_number == game_state.total_cases:
            achievements.append(Achievement(
                type=AchievementType.CAREER_GROWTH,
                title="Adventure Complete",
                description=f"Completed all {game_state.total_cases} cases in this adventure",
                value=None
            ))
        
        return achievements
    
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
        - Hospital: {game_state.game_world.hospital_name}
        - Department: {game_state.game_world.department}
        
        User Performance:
        - Average Score: {avg_score}/10
        - Cases Completed: {game_state.current_case_number}/{game_state.total_cases}
        - Achievements: {len(game_state.achievements)}
        
        Update the world to reflect:
        1. Improved resources if performance is high
        2. New challenges if performance is low
        3. Career progression based on achievements
        
        Return updated GameWorldModel as JSON.
        """
        
        try:
            result = await self.agent.run(prompt)
            # Agent output_type is GameState, so result.output should be GameState-like
            # Extract game_world from it or use the output directly
            world_data = result.output if hasattr(result, 'output') else result
            
            # If agent returns GameState, extract game_world
            if hasattr(world_data, 'game_world'):
                return world_data.game_world
            elif isinstance(world_data, dict):
                # Update world model from dict
                updated_world = game_state.game_world.model_copy(deep=True)
                if "world_description" in world_data:
                    updated_world.world_description = world_data["world_description"]
                if "hospital_name" in world_data:
                    updated_world.hospital_name = world_data.get("hospital_name")
                if "department" in world_data:
                    updated_world.department = world_data.get("department")
                if "additional_context" in world_data:
                    updated_world.additional_context.update(world_data["additional_context"])
                return updated_world
            else:
                # Return original if update fails
                return game_state.game_world
        except Exception as e:
            # If update fails, return original world
            print(f"Failed to update game world: {e}")
            return game_state.game_world
    
    async def chat_with_game_master(
        self,
        game_state: GameState,
        user_message: str
    ) -> str:
        """Handle chat with game master"""
        
        context = f"""
        You are the Game Master for Stud. The user is playing a medical education game.
        
        Current Game State:
        - Case #{game_state.current_case_number}/{game_state.total_cases}
        - Scenario: {game_state.case_state.clinical_case_scenario_description[:300]}
        - User Performance: {len(game_state.user_performance)} cases completed
        
        User's Message: {user_message}
        
        Respond as the Game Master, providing guidance, hints, or encouragement.
        Stay in character and be helpful but don't give away answers directly.
        """
        
        try:
            result = await self.chat_agent.run(context)
            return result.output if hasattr(result, 'output') else str(result)
        except Exception as e:
            raise Exception(f"Failed to get game master response: {str(e)}")


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
