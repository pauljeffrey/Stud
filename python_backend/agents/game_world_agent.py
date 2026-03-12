"""
Game World Agent for Stud
Creates comprehensive world models based on user configuration or random initialization
"""
from typing import Optional
from pydantic_ai import Agent
from agents.base_agent import BaseAgent
from agents.agents import get_game_world_model_model
from models.states import GameWorldModel, GameConfig
import os
import json
import random
import uuid

from config import config
from game_config import (
    PROFESSIONS, ERAS, NATURAL_CONDITIONS, NATIONS, 
    ECONOMIC_ADVANTAGES, MODES, AREAS, get_subjects_for_profession
)
from game_config import get_random_attributes


class GameWorldAgent(BaseAgent):
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
        super().__init__(model_name, api_key, provider)
        
        # Initialize agent using the pattern from agents.py
        model = get_game_world_model_model(model_name, api_key)
        self.agent = Agent(
            model,
            system_prompt="""
            You are the Game World Model for Stud. You create comprehensive, immersive game worlds
            for medical education role-playing games based on configuration parameters.
            
            Generate detailed world descriptions that include:
            - Rich, immersive world_description that sets the scene
            - Appropriate hospital_name and department based on the setting
            - Additional_context with relevant details about resources, staffing, demographics, etc.
            
            Make the world feel alive, realistic, and educational.
            """,
            output_type=GameWorldModel
        )
    
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Reinitialize the model"""
        super()._reinitialize_model(model_name, api_key)
        model = get_game_world_model_model(self.model_name, self.api_key)
        self.agent = Agent(
            model,
            system_prompt="""
            You are the Game World Model for Stud. You create comprehensive, immersive game worlds
            for medical education role-playing games based on configuration parameters.
            
            Generate detailed world descriptions that include:
            - Rich, immersive world_description that sets the scene
            - Appropriate hospital_name and department based on the setting
            - Additional_context with relevant details about resources, staffing, demographics, etc.
            
            Make the world feel alive, realistic, and educational.
            """,
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
            config.subject = random.choice(subjects) if subjects else "general medicine"
        
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
        Create a comprehensive, immersive game world for a medical education role-playing game.
        
        Configuration:
        - Profession: {game_config.profession}
        - Clinical Setting: {game_config.clinical_setting}
        - Medical Subject Focus: {game_config.subject}
        - Historical Era: {game_config.era}
        - Natural Conditions: {game_config.natural_conditions}
        - Nation Type: {game_config.nation_type}
        - Economic Advantage: {game_config.economic_advantage}
        
        Create a detailed world model that includes:
        1. A rich, immersive world_description that sets the scene
        2. Appropriate hospital_name and department based on the setting
        3. Additional_context with relevant details about:
           - Available medical equipment and resources
           - Staffing levels and expertise
           - Patient demographics
           - Environmental factors
           - Cultural and social context
           - Economic constraints or advantages
           - Historical medical practices (if applicable)
        
        Make the world feel alive, realistic, and educational. The world should provide context
        for why certain medical decisions are made and what resources are available.
        
        Generate a complete GameWorldModel with all fields filled.
        """
        
        # Get AI response
        result = await self.agent.run(prompt)
        world_model = result.output
        
        # Ensure world_id is set
        if not world_model.world_id:
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
