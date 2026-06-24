"""
Game World Agent for Stud
Creates comprehensive world models based on user configuration or random initialization
"""
from typing import Optional
from pydantic_ai import Agent
from agents.agents import get_game_world_model_model
from models.states import GameWorldModel, GameConfig
import os
import json
import random
import uuid

from configs.config import config
from configs.game_config import (
    PROFESSIONS, ERAS, NATURAL_CONDITIONS, NATIONS,
    ECONOMIC_ADVANTAGES, MODES, get_subjects_for_profession,
)


class GameWorldAgent:
    """
    Game World Agent responsible for creating comprehensive game worlds
    based on configuration or random initialization
    """
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, provider: str = "google"):
        """
        Initialize the Game World Agent
        
        Args:
            model_name: Name of the AI model to use
            api_key: API key for the model
            provider: "google" or "openai"
        """
        self._model_name = model_name
        self._api_key = api_key

        model = get_game_world_model_model(model_name, api_key)
        
        self.agent_system_prompt = """
            You are the Game World Model for Stud. Create concise, immersive medical-education settings.
            
            BREVITY RULES (strict):
            - world_description: 2-3 short sentences only (setting, mood, key constraint)
            - hospital_name and department: brief labels
            - additional_context: bullet-style facts, max 4 items, one line each
            """
        self.agent = Agent(
            model,
            system_prompt=self.agent_system_prompt,
            output_type=GameWorldModel
        )
    
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        if model_name is not None:
            self._model_name = model_name
        if api_key is not None:
            self._api_key = api_key
        model = get_game_world_model_model(self._model_name, self._api_key)
        self.agent = Agent(
            model,
            system_prompt=self.agent_system_prompt,
            output_type=GameWorldModel
        )
    
    def _randomize_config(self, config: GameConfig) -> GameConfig:
        """Randomize any None values in the config"""
        if not config.profession:
            config.profession = random.choice(PROFESSIONS)
        
        if not config.clinical_setting:
            config.clinical_setting = random.choice(MODES)
        
        if not config.subject:
            subjects = get_subjects_for_profession(config.profession)
            config.subject = random.choice(subjects) if subjects else "general"
        
        if not config.era:
            config.era = random.choice(ERAS)
        
        if not config.natural_conditions:
            config.natural_conditions = random.choice(NATURAL_CONDITIONS)
        
        if not config.nation_type:
            config.nation_type = random.choice(NATIONS)
        
        if not config.economic_advantage:
            config.economic_advantage = random.choice(ECONOMIC_ADVANTAGES)
        
        return config
    
    async def create_world(self, game_config: GameConfig) -> GameWorldModel:
        """
        Create a comprehensive game world based on configuration
        
        Args:
            game_config: Game configuration (will be randomized if values are None)
            
        Returns:
            GameWorldModel with complete world description
        """
        # Randomize any None values
        game_config = self._randomize_config(game_config)
        
        # Build prompt for world creation
        prompt = f"""
        Create a concise world model for a medical education role-playing game.
        
        Configuration:
        - Profession: {game_config.profession}
        - Clinical Setting: {game_config.clinical_setting}
        - Medical Subject Focus: {game_config.subject}
        - Historical Era: {game_config.era}
        - Natural Conditions: {game_config.natural_conditions}
        - Nation Type: {game_config.nation_type}
        - Economic Advantage: {game_config.economic_advantage}
        
        Keep output SHORT:
        1. world_description — 2-3 sentences max
        2. hospital_name and department — brief
        3. additional_context — up to 4 one-line facts (resources, staffing, demographics, constraints)
        
        Generate a complete GameWorldModel with all fields filled.
        """
        
        # Get AI response
        result = await self.agent.run(prompt)
        world_model = result.output
        
        # Ensure world_id is set
        if not world_model.world_id:
            world_model.world_id = str(uuid.uuid4())
        
        return world_model

    async def run(self, prompt: str) -> GameWorldModel:
        """Run agent with custom prompt (e.g. for world updates)."""
        result = await self.agent.run(prompt)
        world_model = result.output
        if world_model.world_id is None or not world_model.world_id:
            world_model.world_id = str(uuid.uuid4())
        return world_model


# Global instance
_game_world_agent_instance: Optional[GameWorldAgent] = None


def get_game_world_agent(
    model_name: Optional[str] = None, 
    api_key: Optional[str] = None,
    provider: str = "google"
) -> GameWorldAgent:
    """Get or create the global Game World Agent instance"""
    global _game_world_agent_instance
    if _game_world_agent_instance is None:
        _game_world_agent_instance = GameWorldAgent(model_name, api_key, provider)
    return _game_world_agent_instance
