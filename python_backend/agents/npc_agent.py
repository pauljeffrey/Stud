"""
NPC Agent for Stud
Non-playable characters that help users identify symptoms and problems
NPCs take on the character of the illness/condition provided by game master or state controller
"""
from typing import Optional, List, Dict, Any
from pydantic_ai import Agent
import os
import json
import random
import uuid

from config import config
from agents.base_agent import BaseAgent
from agents.agents import get_npc_model
from models.states import NPCState, CaseState, GameWorldModel


class NPCAgent(BaseAgent):
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
        super().__init__(model_name, api_key, provider)
        
        # Initialize agent using the pattern from agents.py
        model = get_npc_model(model_name, api_key)
        self.agent = Agent(
            model,
            system_prompt="""
            You are an NPC in Stud. You will be given a character name and role.
            Respond authentically as that character would, considering:
            1. Their professional role and expertise level
            2. Their current emotional state and situation
            3. Realistic medical knowledge for their position
            4. Appropriate bedside manner and communication style
            
            Stay in character and provide realistic responses that advance the medical scenario.
            """,
            output_type=NPCState
        )
        
        # Agent for generating all NPCs at once
        self.npc_generator_agent = Agent(
            model,
            system_prompt="""
            You are an NPC generator for Stud. Generate all relevant NPCs for a clinical case
            based on the case description, diagnosis, investigations, and game world configuration.
            
            Analyze the clinical case to determine which NPCs are needed:
            - Patient (always required)
            - Nurses (based on clinical setting)
            - Specialists (based on diagnosis/subject)
            - Family members (if relevant)
            - Colleagues (if relevant to the scenario)
            
            Give each NPC appropriate personality, tone, and characteristics based on:
            - The clinical condition
            - The game world context
            - Their professional role
            - The scenario's emotional context
            
            Return a list of NPCState objects.
            """,
            output_type=List[NPCState]
        )
    
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Reinitialize the model"""
        super()._reinitialize_model(model_name, api_key)
        model = get_npc_model(self.model_name, self.api_key)
        self.agent = Agent(
            model,
            system_prompt="""
            You are an NPC in Stud. You will be given a character name and role.
            Respond authentically as that character would, considering:
            1. Their professional role and expertise level
            2. Their current emotional state and situation
            3. Realistic medical knowledge for their position
            4. Appropriate bedside manner and communication style
            
            Stay in character and provide realistic responses that advance the medical scenario.
            """,
            output_type=NPCState
        )
        self.npc_generator_agent = Agent(
            model,
            system_prompt="""
            You are an NPC generator for Stud. Generate all relevant NPCs for a clinical case
            based on the case description, diagnosis, investigations, and game world configuration.
            
            Analyze the clinical case to determine which NPCs are needed:
            - Patient (always required)
            - Nurses (based on clinical setting)
            - Specialists (based on diagnosis/subject)
            - Family members (if relevant)
            - Colleagues (if relevant to the scenario)
            
            Give each NPC appropriate personality, tone, and characteristics based on:
            - The clinical condition
            - The game world context
            - Their professional role
            - The scenario's emotional context
            
            Return a list of NPCState objects.
            """,
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
        - Description: {case_state.clinical_case_scenario_description[:500]}
        - Diagnosis: {case_state.diagnosis or "Being investigated"}
        - Question: {case_state.question}
        - Investigations: {json.dumps(case_state.investigations or {}, indent=2)}
        
        Game World Context:
        - Profession: {case_state.profession}
        - Clinical Setting: {case_state.clinical_setting}
        - Subject: {case_state.subject}
        - Era: {case_state.era}
        - Hospital: {game_world.hospital_name}
        - Department: {game_world.department}
        - Additional Context: {json.dumps(game_world.additional_context, indent=2)}
        
        Determine which NPCs are needed:
        1. Patient (always required)
        2. Nurses/Staff based on clinical setting
        3. Specialists based on diagnosis/subject
        4. Family members if relevant
        5. Colleagues if scenario involves workplace dynamics
        
        For each NPC, provide:
        - Appropriate name, age, gender
        - Role and personality description
        - Tone and mood based on condition
        - Examination findings relevant to their role
        - Realistic characteristics for their position
        
        Return a list of NPCState objects with all required fields filled.
        """
        
        try:
            result = await self.npc_generator_agent.run(prompt)
            npc_states = result.output if hasattr(result, 'output') else result
            
            # Ensure it's a list
            if isinstance(npc_states, list):
                # Set common fields for all NPCs
                for npc in npc_states:
                    if not hasattr(npc, 'npc_id') or not npc.npc_id:
                        npc.npc_id = str(uuid.uuid4())
                    if not hasattr(npc, 'user_id') or not npc.user_id:
                        npc.user_id = case_state.user_id
                    if not hasattr(npc, 'case_id') or not npc.case_id:
                        npc.case_id = case_state.case_id
                return npc_states
            elif isinstance(npc_states, NPCState):
                # Single NPC returned, wrap in list
                npc_states.npc_id = str(uuid.uuid4())
                npc_states.user_id = case_state.user_id
                npc_states.case_id = case_state.case_id
                return [npc_states]
            else:
                # Fallback: create at least a Patient NPC
                return [self.create_npc_from_case(case_state, "Patient")]
        except Exception as e:
            # Fallback to creating NPCs manually if agent fails
            print(f"NPC generation agent failed: {e}, using fallback method")
            npcs = [self.create_npc_from_case(case_state, "Patient")]
            
            # Add supporting NPCs based on clinical setting
            if "emergency" in case_state.clinical_setting.lower():
                npcs.append(self.create_npc_from_case(case_state, "Emergency Nurse"))
            elif "icu" in case_state.clinical_setting.lower():
                npcs.append(self.create_npc_from_case(case_state, "ICU Nurse"))
            
            return npcs
    
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
            npc_role: Role of the NPC (Patient, Nurse, Specialist, etc.)
            npc_name: Optional name for the NPC
            
        Returns:
            NPCState configured for this case
        """
        # Extract key information from case
        clinical_description = case_state.clinical_case_scenario_description
        diagnosis = case_state.diagnosis or "Unknown condition"
        investigations = case_state.investigations or {}
        
        # Determine personality and tone based on condition
        if "acute" in clinical_description.lower() or "emergency" in clinical_description.lower():
            tone = "anxious"
            mood = "distressed"
        elif "chronic" in clinical_description.lower():
            tone = "resigned"
            mood = "tired"
        else:
            tone = "cooperative"
            mood = "neutral"
        
        # Create NPC state
        npc_state = NPCState(
            npc_id=str(uuid.uuid4()),
            user_id=case_state.user_id,
            case_id=case_state.case_id,
            name=npc_name or self._generate_npc_name(npc_role),
            role=npc_role,
            age=str(random.randint(25, 75)),
            gender=random.choice(["Male", "Female", "Other"]),
            personality_description=f"A {npc_role.lower()} experiencing {diagnosis}. "
                                f"Characterized by {tone} communication style.",
            clinical_case_description=clinical_description,
            examination_findings=investigations.copy() if isinstance(investigations, dict) else {},
            diagnosis=diagnosis,
            tone=tone,
            mood=mood,
            profession=case_state.profession,
            clinical_setting=case_state.clinical_setting,
            subject=case_state.subject,
            era=case_state.era,
            natural_conditions=case_state.natural_conditions,
            nation_type=case_state.nation_type,
            economic_advantage=case_state.economic_advantage
        )
        
        return npc_state
    
    async def chat_with_npc(
        self,
        npc_state: NPCState,
        user_message: str,
        case_state: CaseState,
        chat_history: List[Dict[str, str]] = None
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
        
        # Create agent for this specific NPC
        agent = Agent(
            get_npc_model(self.model_name, self.api_key),
            system_prompt=f"""
            You are {npc_state.name}, a {npc_state.role} in Stud, a medical education role-playing game.
            
            Your Character:
            - Role: {npc_state.role}
            - Personality: {npc_state.personality_description}
            - Tone: {npc_state.tone}
            - Mood: {npc_state.mood}
            
            Your Condition:
            - Clinical Description: {npc_state.clinical_case_description}
            - Diagnosis: {npc_state.diagnosis or "Being investigated"}
            - Examination Findings: {json.dumps(npc_state.examination_findings)}
            
            Your Purpose:
            Help the healthcare professional (player) identify symptoms, understand your condition,
            and reach a diagnosis or management plan. You can:
            - Describe your symptoms and how you feel
            - Answer questions about your medical history
            - Provide clues about your condition (but don't give away the diagnosis directly)
            - Express concerns or ask questions
            
            Stay in character! Respond as this person would, given their condition and personality.
            Be helpful but realistic - you're experiencing a medical condition, not a medical textbook.
            
            Clue Level: {npc_state.clue_level}/3
            - Level 0-1: Give subtle hints about symptoms
            - Level 2: Provide more direct clues
            - Level 3: Can be more explicit (but still in character)
            """,
            output_type=str
        )
        
        # Build context
        context = f"""
        Case Context:
        - Question: {case_state.question}
        - Current Scenario: {case_state.clinical_case_scenario_description[:300]}
        
        Chat History:
        {self._format_chat_history(chat_history[-5:])}  # Last 5 messages
        
        User's Current Message: {user_message}
        
        Respond as {npc_state.name}, staying true to your character, condition, and personality.
        Help the healthcare professional understand your condition through natural conversation.
        """
        
        # Get AI response
        result = await agent.run(context)
        response = result.output
        
        # Increment clue level if this seems like a clue-giving response
        if any(keyword in response.lower() for keyword in ["symptom", "feel", "notice", "experience", "pain"]):
            npc_state.clue_level = min(3, npc_state.clue_level + 1)
        
        return response
    
    def _generate_npc_name(self, role: str) -> str:
        """Generate appropriate name for NPC based on role"""
        first_names = ["John", "Sarah", "Michael", "Emily", "David", "Jessica", "James", "Amanda"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        
        if role.lower() == "patient":
            return f"{random.choice(first_names)} {random.choice(last_names)}"
        elif "nurse" in role.lower():
            return f"Nurse {random.choice(first_names)}"
        elif "doctor" in role.lower() or "specialist" in role.lower():
            return f"Dr. {random.choice(last_names)}"
        else:
            return role
    
    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """Format chat history for context"""
        if not chat_history:
            return "No previous conversation."
        
        formatted = []
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted)


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
