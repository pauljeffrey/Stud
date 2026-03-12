"""
Dice Agent for Stud
Responsible for applying dice roll effects to medical scenarios
Based on dice result (1-6), modifies the scenario dramatically and realistically
"""
from typing import Optional
from pydantic_ai import Agent
from agents.base_agent import BaseAgent
from agents.agents import get_dice_model
from models.states import GameState


class DiceAgent(BaseAgent):
    """
    Dice Agent responsible for applying dice roll effects to medical scenarios
    Creates dramatic, realistic changes based on dice results (1-6)
    """
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, provider: str = "google"):
        """
        Initialize the Dice Agent
        
        Args:
            model_name: Name of the AI model to use
            api_key: API key for the model
            provider: "google" or "openai"
        """
        super().__init__(model_name, api_key, provider)
        
        # Initialize agent using the pattern from agents.py
        model = get_dice_model(model_name, api_key)
        self.agent = Agent(
            model,
            system_prompt="""
            You are responsible for applying dice roll effects to medical scenarios in Stud.
            Based on the dice result (1-6), modify the scenario dramatically and realistically:
            
            Dice Results:
            1-2: Complications arise (patient condition worsens, equipment fails, new symptoms appear, etc.)
            3-4: Moderate changes (new symptoms appear, test results delayed, minor complications, etc.)
            5-6: Favorable developments (patient responds well, help arrives, condition improves, etc.)
            
            Describe the change dramatically and realistically, maintaining medical accuracy.
            Your response should be a concise description (2-4 sentences) of what happened.
            Make it engaging and educational while staying medically accurate.
            """,
            output_type=str
        )
    
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Reinitialize the model"""
        super()._reinitialize_model(model_name, api_key)
        model = get_dice_model(self.model_name, self.api_key)
        self.agent = Agent(
            model,
            system_prompt="""
            You are responsible for applying dice roll effects to medical scenarios in Stud.
            Based on the dice result (1-6), modify the scenario dramatically and realistically:
            
            Dice Results:
            1-2: Complications arise (patient condition worsens, equipment fails, new symptoms appear, etc.)
            3-4: Moderate changes (new symptoms appear, test results delayed, minor complications, etc.)
            5-6: Favorable developments (patient responds well, help arrives, condition improves, etc.)
            
            Describe the change dramatically and realistically, maintaining medical accuracy.
            Your response should be a concise description (2-4 sentences) of what happened.
            Make it engaging and educational while staying medically accurate.
            """,
            output_type=str
        )
    
    async def generate_dice_effect(
        self,
        game_state: GameState,
        dice_result: int
    ) -> str:
        """
        Generate dice effect description based on dice roll
        
        Args:
            game_state: Current game state
            dice_result: Dice roll result (1-6)
            
        Returns:
            Description of the dice effect
        """
        if not (1 <= dice_result <= 6):
            raise ValueError("Dice result must be between 1 and 6")
        
        # Build context
        context = f"""
        Current Medical Scenario:
        - Case: {game_state.case_state.clinical_case_scenario_description[:500]}
        - Question: {game_state.case_state.question}
        - Current Diagnosis: {game_state.case_state.diagnosis or "Being investigated"}
        - Clinical Setting: {game_state.clinical_setting}
        - Profession: {game_state.profession}
        
        Dice Roll Result: {dice_result}
        
        Based on this dice roll, describe what happens next in the scenario.
        Make it dramatic, realistic, and medically accurate.
        
        Dice Result Interpretation:
        - 1-2: Negative/Complications (worsening condition, equipment failure, etc.)
        - 3-4: Neutral/Moderate changes (new information, delays, minor issues)
        - 5-6: Positive/Favorable (improvement, help arrives, breakthrough)
        
        Provide a concise, engaging description (2-4 sentences) of the dice effect.
        """
        
        # Get AI response
        result = await self.agent.run(context)
        effect_description = result.output
        
        return effect_description


# Global instance
_dice_agent_instance: Optional[DiceAgent] = None


def get_dice_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google"
) -> DiceAgent:
    """Get or create the global Dice Agent instance"""
    global _dice_agent_instance
    if _dice_agent_instance is None:
        _dice_agent_instance = DiceAgent(model_name, api_key, provider)
    return _dice_agent_instance
