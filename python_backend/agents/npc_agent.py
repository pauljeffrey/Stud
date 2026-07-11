"""
NPC Agent for Stud
Non-playable characters that help users identify symptoms and problems
NPCs take on the character of the illness/condition provided by game master or state controller
"""
import asyncio
from typing import Optional, List, Dict, Any
from pydantic_ai import Agent
import os
import json
import random
import uuid

from configs.config import config
from agents.agents import get_npc_model
from models.states import NPCState, CaseState, GameWorldModel, NPCRole
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ModelRequest, UserPromptPart, SystemPromptPart
from utils import (
    process_chat_history_for_model_inference,
    save_chat_history_to_storage
)
from typing import Union


def _dump_json(value) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value or {}, indent=2)


def finalize_npc_states(npc_states: List[NPCState], case_state: CaseState) -> List[NPCState]:
    """Ensure NPC ids and case linkage after generation."""
    if not isinstance(npc_states, list):
        npc_states = [npc_states] if isinstance(npc_states, NPCState) else []
    for npc in npc_states:
        if not getattr(npc, "npc_id", None):
            npc.npc_id = str(uuid.uuid4())
        if not getattr(npc, "case_id", None):
            npc.case_id = case_state.case_id
    return npc_states


class NPCAgent:
    """
    NPC Agent responsible for creating and managing non-playable characters
    NPCs help users by providing clues, symptoms, and guidance based on their condition
    """
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, provider: str = "google"):
        """
        Initialize the NPC Agent
        
        Args:
            model_name: Name of the AI model to use
            api_key: API key for the model
            provider: "google" or "openai"
        """
        
        # Initialize agent using the pattern from agents.py
        model = get_npc_model(model_name, api_key)
        self.npc_system_prompt = """
        You are an NPC in Stud. You will be given a character name and role.
            Respond authentically as that character would, considering:
            1. Their professional role and expertise level
            2. Their current emotional state and situation
            3. Realistic medical knowledge for their position
            4. Appropriate bedside manner and communication style
            
            Stay in character and provide realistic responses that advance the medical scenario.
            """
            
        self.npc_generator_system_prompt = """
        You are an NPC generator for Stud, an engaging and fun medical role-playing game. You generate all relevant NPCs for a clinical case
        based on the npc roles,case description, diagnosis, investigations, and game world configuration.
        
        Give each NPC appropriate personality, tone, and characteristics based on:
        - The clinical condition
        - The game world context
        - Their professional role
        - The scenario's emotional context
        - The NPC roles provided
        
        Return a list of NPCState objects.
        """
        
        self.agent = Agent(
            model,
            system_prompt=self.npc_system_prompt,
            output_type=NPCState
        )
        
        # Agent for generating all NPCs at once
        self.npc_generator_agent = Agent(
            model,
            system_prompt=self.npc_generator_system_prompt,
            output_type=List[NPCState]
        )
    
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Reinitialize the model"""
        
        model = get_npc_model(self.model_name, self.api_key)
        self.agent = Agent(
            model,
            system_prompt=self.npc_system_prompt,
            output_type=NPCState
        )
        self.npc_generator_agent = Agent(
            model,
            system_prompt=self.npc_generator_system_prompt,
            output_type=List[NPCState]
        )
    
    async def generate_all_npcs_for_case(
        self,
        case_state: CaseState,
        game_world: GameWorldModel
    ) -> List[NPCState]:
        """
        Generate all NPCs for a clinical case in one API call
        
        Args:
            case_state: Current case state
            game_world: Game world model with configuration
            
        Returns:
            List of NPCState objects
        """
        
        prompt = f"""
        Generate all relevant NPCs for this clinical case:
        
        Clinical Case:
        - Description: {case_state.clinical_case_scenario_description}
        - Diagnosis: {case_state.diagnosis or "Being investigated"}
        - Question: {case_state.question}
        - Investigations: {_dump_json(case_state.investigations)}
        
        Game World Context:
        - Profession: {case_state.profession}
        - Clinical Setting: {case_state.clinical_setting}
        - Subject: {case_state.subject}
        - Era: {case_state.era} 
        - Natural Conditions: {case_state.natural_conditions}
        - Nation Type: {case_state.nation_type}
        - Economic Advantage: {case_state.economic_advantage}
        - Location: {game_world.location}
        - Hospital: {game_world.hospital_name}
        - Department: {game_world.department}
        - Additional Context: {json.dumps(game_world.additional_context, indent=2)}
        
        For each NPC, provide:
        - Appropriate name, age, gender
        - Role and personality description (can be a negative one)
        - Tone and mood based on condition
        - Examination findings if role is Patient
        - Realistic characteristics for their position
        
        Minimum NPCs to generate (You can add more if you think it's necessary or FUN): {case_state.npc_roles}
        if NPC Roles are not provided, return a list of all possible NPCs (given the case and world description) with their appropriate roles.
        Think carefully about the NPCs you generate and their relationships to the case and world description.
        """
        
        try:
            result = await self.npc_generator_agent.run(prompt)
            npc_states = result.output
            
            if isinstance(npc_states, list):
                return finalize_npc_states(npc_states, case_state)
            elif isinstance(npc_states, NPCState):
                # Single NPC returned, wrap in list
                npc_states.npc_id = str(uuid.uuid4())
                # npc_states.user_id = case_state.user_id
                npc_states.case_id = case_state.case_id
                return [npc_states]
            else:
                # Fallback: create at least a Patient NPC
                return [self.create_npc_from_case(case_state, "Patient")]
        except Exception as e:
            # Fallback to creating NPCs manually if agent fails
            print(f"NPC generation agent failed: {e}, using fallback method")
            extra_roles = ['Patient', 'Specialist', 'Relative', 'Nurse']
            # Create extra NPCs in parallel
            extra_npcs = await asyncio.gather(
                *[asyncio.to_thread(self.create_npc_from_case, case_state, role) for role in extra_roles]
            )
            return list(extra_npcs)

    def create_npc_from_case(
        self,
        case_state: CaseState,
        npc_role: str = "Patient",
        npc_name: Optional[str] = None
    ) -> NPCState:
        """
        Create an NPC based on the clinical case

        Args:
            case_state: Current case state
            npc_role: Role of the NPC (Patient, Nurse, Specialist, Emergency Nurse, etc.)
            npc_name: Optional name for the NPC

        Returns:
            NPCState configured for this case
        """
        clinical_description = case_state.clinical_case_scenario_description
        investigations = case_state.investigations or {}
        if "acute" in clinical_description.lower() or "severe" in clinical_description.lower() or "emergency" in clinical_description.lower():
            tone = "anxious"
            mood = "distressed"
        elif "chronic" in clinical_description.lower():
            tone = "resigned"
            mood = "tired"
        else:
            tone = "cooperative"
            mood = "neutral"

        role_enum = self._role_to_npc_enum(npc_role) if npc_role != "Patient" else NPCRole.PATIENT
        gender = random.choice(["Male", "Female", "Other"])
        display_name = npc_name or self._generate_npc_name(npc_role, gender)

        npc_state = NPCState(
            npc_id=str(uuid.uuid4()),
            case_id=case_state.case_id,
            name=display_name,
            role=role_enum,
            age=str(random.randint(25, 75)),
            gender=gender,
            personality_description=f"A {npc_role.lower()} in this scenario. "
                                f"Characterized by {tone} communication style.",
            examination_findings=investigations.copy() if isinstance(investigations, dict) else {},
            tone=tone,
            mood=mood,
            available=True,
            clue_level=0
        )
        
        # npc_state.user_id = case_state.user_id
        return npc_state
    
    def _role_to_npc_enum(self, role: str) -> NPCRole:
        """Convert role string to NPCRole enum"""
        if role.lower() == "patient":
            return NPCRole.PATIENT
        elif role.lower() == "nurse":
            return NPCRole.NURSE
        elif role.lower() == "specialist":
            return NPCRole.SPECIALIST
        elif role.lower() == "relative":
            return NPCRole.RELATIVE
        elif role.lower() == "nurse":
            return NPCRole.NURSE
        elif role.lower() == "specialist":
            return NPCRole.SPECIALIST
        else:
            return NPCRole.PATIENT
    
    async def chat_with_npc(
        self,
        npc_state: NPCState,
        user_message: str,
        case_state: CaseState,
        game_world: GameWorldModel,
        chat_history: Any = None
    ) -> str:
        """
        Generate NPC response to user message
        
        Args:
            npc_state: Current NPC state
            user_message: User's message/question
            case_state: Current case state for context
            chat_history: Previous chat messages
            
        Returns:
            NPC's response
        """
        if chat_history is None:
            chat_history = []
        
        if npc_state.role == NPCRole.PATIENT and npc_state.examination_findings:
            examination_findings = f"""
            - Examination Findings: {json.dumps(npc_state.examination_findings)}
            """
        else:
            examination_findings = ""
        
        if npc_state.role in [NPCRole.PATIENT, NPCRole.NURSE, NPCRole.SPECIALIST]:
            clue_level_description = f"""
            - Clue Level: {npc_state.clue_level}/3
            - Level 0-1: Give subtle hints about symptoms
            - Level 2: Provide more direct clues
            - Level 3: Can be more explicit (but still in character)
            """
        else:
            clue_level_description = ""
        
        system_prompt = f"""
            You are {npc_state.name}, a {npc_state.role} and non-playable character in Stud, a medical education role-playing game.
            
            World Info:
            world_description: {game_world.world_description}
            clinical_setting: {game_world.clinical_setting}
            era: {game_world.era}
            natural_conditions: {game_world.natural_conditions}
            location: {game_world.location}
            hospital_name: {game_world.hospital_name}
            department: {game_world.department}
            
            Your Character:
            - Role: {npc_state.role}
            - Personality: {npc_state.personality_description}
            - Tone: {npc_state.tone}
            - Mood: {npc_state.mood}
            
            Your Purpose:
            Help the user (player) understand case condition better.
            Stay in character! Respond as this person would, given their role, condition and personality.
            Play the role appropriately.
            {clue_level_description}
            
        Case Context:
        - Clinical Case Scenario Description: {case_state.clinical_case_scenario_description}
        - Diagnosis: {case_state.diagnosis or "Being investigated"}
        {examination_findings}
        - Question: {case_state.question}
        
        Respond as {npc_state.name}, staying true to your character, condition, and personality.
        Help the healthcare professional understand your condition through natural conversation.
        **You must not provide the answer to the question directly no matter what.**
            """
        
        # Create agent for this specific NPC
        agent = Agent(
            get_npc_model(self.model_name, self.api_key),
            system_prompt=system_prompt,
            output_type=str,
            history_processors=[]
        )
        chat_history = process_chat_history_for_model_inference(chat_history)
        
        try:
            # Get AI response
            result = await agent.run(user_message, message_history=chat_history)
            response = result
            
            # Update chat history
            if chat_history:
                chat_history.append(ModelRequest(parts=[UserPromptPart(content=user_message)]))
                chat_history.append(ModelResponse(parts=[TextPart(content=response)]))
            else:
                chat_history = [
                    ModelRequest(parts=[SystemPromptPart(content=system_prompt)]),
                    ModelRequest(parts=[UserPromptPart(content=user_message)]),
                    ModelResponse(parts=[TextPart(content=response)])
                ]
            
            # Save chat history to storage (background job)
            await save_chat_history_to_storage(
                chat_history=chat_history,
                user_id=npc_state.user_id,
                conversation_id=npc_state.case_id,  # Use case_id as session_id
                chat_type="npc",
                npc_id=str(npc_state.npc_id),
                background=True
            )
            
            return response, chat_history
        except Exception as e:
            print(f"NPC chat failed: {e}")
            return "Sorry, I'm having trouble responding. Please try again later.", chat_history

    async def update_npcs_for_case(
        self,
        npc_states: List[NPCState],
        case_state: CaseState,
        escalation_delta: float,
        game_world: GameWorldModel,
        change_description: str = "",
    ) -> List[NPCState]:
        """Refresh NPC mood/tone/personality when the case escalates or de-escalates."""
        if not npc_states or abs(escalation_delta) < 1e-6:
            return npc_states
        compact = [
            {"npc_id": str(n.npc_id), "name": n.name, "role": str(n.role), "gender": n.gender,
             "mood": n.mood, "tone": n.tone, "personality_description": n.personality_description[:400]}
            for n in npc_states
        ]
        prompt = f"""Clinical case just shifted (escalation_delta {escalation_delta:+.2f}; negative = calmer, positive = more acute).
Brief change: {change_description[:400]}
Case excerpt: {case_state.clinical_case_scenario_description[:700]}
Setting: {game_world.hospital_name or ''} / {game_world.department or ''}
Return exactly {len(npc_states)} NPCs in the SAME order. Preserve each npc_id, name, role, gender, age, case_id, examination_findings, clue_level, available.
Only update mood, tone, personality_description to match the new clinical tension.
NPCs: {json.dumps(compact, default=str)[:12000]}"""
        try:
            result = await self.npc_generator_agent.run(prompt)
            out = result.output
            if isinstance(out, list) and len(out) == len(npc_states):
                merged: List[NPCState] = []
                for old, new in zip(npc_states, out):
                    merged.append(old.model_copy(update={
                        "mood": new.mood,
                        "tone": new.tone,
                        "personality_description": new.personality_description,
                    }))
                return merged
        except Exception as e:
            print(f"update_npcs_for_case: {e}")
        return npc_states

    def _generate_npc_name(self, role: str, gender: str = "Other") -> str:
        """Generate a plausible name for NPC based on role and gender."""
        m_first = ["James", "Michael", "David", "William", "John", "Robert", "Daniel", "Matthew"]
        f_first = ["Sarah", "Emily", "Jessica", "Amanda", "Jennifer", "Elizabeth", "Maria", "Laura"]
        n_first = ["Alex", "Jordan", "Taylor", "Casey", "Riley", "Morgan"]
        last = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Martinez", "Wilson"]
        g = (gender or "Other").strip().lower()
        if g == "male":
            first_pool = m_first
        elif g == "female":
            first_pool = f_first
        else:
            first_pool = m_first + f_first + n_first
        if role.lower() == "patient":
            return f"{random.choice(first_pool)} {random.choice(last)}"
        if "nurse" in role.lower():
            return f"Nurse {random.choice(first_pool)}"
        if "doctor" in role.lower() or "specialist" in role.lower():
            return f"Dr. {random.choice(last)}"
        return f"{random.choice(first_pool)} {random.choice(last)}"


# Global instance
_npc_agent_instance: Optional[NPCAgent] = None


def get_npc_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google"
) -> NPCAgent:
    """Get or create the global NPC Agent instance"""
    global _npc_agent_instance
    if _npc_agent_instance is None:
        _npc_agent_instance = NPCAgent(model_name, api_key, provider)
    return _npc_agent_instance
