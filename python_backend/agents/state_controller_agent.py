"""
State Controller Agent for Stud
Solely responsible for escalating or de-escalating clinical cases
Controls the degree of randomness and speed of escalation/de-escalation
"""
from typing import Optional, Dict, Any
from pydantic_ai import Agent
import os
import json

from config import config
from agents.base_agent import BaseAgent
from agents.agents import get_state_controller_model
from models.states import CaseState, PerformanceAnalysis, StateChangeResponse, ClinicalCaseMetadata


class StateControllerAgent(BaseAgent):
    """
    State Controller Agent responsible for dynamically changing clinical cases
    Escalates or de-escalates based on user performance and time
    """
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, provider: str = "google"):
        """
        Initialize the State Controller Agent
        
        Args:
            model_name: Name of the AI model to use
            api_key: API key for the model
            provider: "google" or "openai"
        """
        super().__init__(model_name, api_key, provider)
        
        # Initialize agent using the pattern from agents.py
        model = get_state_controller_model(model_name, api_key)
        self.agent = Agent(
            model,
            system_prompt="""
            You are the State Controller for Stud. You are solely responsible for escalating or de-escalating
            clinical cases. You control the degree of randomness and speed of escalation/de-escalation.
            
            Based on user performance, time elapsed, and whether clues were used, dynamically update
            the clinical case state to create an engaging and educational experience.
            """,
            output_type=CaseState
        )
    
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Reinitialize the model"""
        super()._reinitialize_model(model_name, api_key)
        model = get_state_controller_model(self.model_name, self.api_key)
        self.agent = Agent(
            model,
            system_prompt="""
            You are the State Controller for Stud. You are solely responsible for escalating or de-escalating
            clinical cases. You control the degree of randomness and speed of escalation/de-escalation.
            
            Based on user performance, time elapsed, and whether clues were used, dynamically update
            the clinical case state to create an engaging and educational experience.
            """,
            output_type=CaseState
        )
    
    async def update_case_state(
        self,
        current_case_state: CaseState,
        case_metadata: Optional[ClinicalCaseMetadata] = None,
        user_performance: Optional[PerformanceAnalysis] = None,
        time_elapsed: int = 0,
        clue_used: bool = False
    ) -> StateChangeResponse:
        """
        Update case state by escalating or de-escalating
        
        Args:
            current_case_state: Current case state
            user_performance: User's performance analysis (if available)
            time_elapsed: Time elapsed since case started (seconds)
            clue_used: Whether user used a clue (triggers penalty)
            
        Returns:
            StateChangeResponse with updated case state
        """
        # Check if max changes reached
        if current_case_state.n_changes >= current_case_state.max_clinical_changes:
            # Return unchanged state - handoff to game master
            return StateChangeResponse(
                updated_case_state=current_case_state,
                escalation_level=1.0,
                change_description="Maximum clinical changes reached. Case ready for handoff to Game Master.",
                penalty_applied=False
            )
        
        # Build context for state change using case metadata
        metadata_context = ""
        if case_metadata:
            metadata_context = f"""
        Case Metadata:
        - Case Number: {case_metadata.case_number}
        - Profession: {case_metadata.profession}
        - Clinical Setting: {case_metadata.clinical_setting}
        - Subject: {case_metadata.subject}
        - Era: {case_metadata.era}
        - Difficulty Level: {case_metadata.difficulty_level or 'intermediate'}
        """
        
        # Build context for state change
        context = f"""
        Current Case State:
        - Case ID: {current_case_state.case_state_id}
        - Scenario: {current_case_state.clinical_case_scenario_description[:500]}
        - Current Diagnosis: {current_case_state.diagnosis or 'Not yet diagnosed'}
        - Examination Findings: {json.dumps(current_case_state.investigations or {})}
        - Investigation Results: {json.dumps(current_case_state.scan_images or {})}
        - Number of Changes: {current_case_state.n_changes}/{current_case_state.max_clinical_changes}
        - Time Elapsed: {time_elapsed} seconds
        - Time Remaining: {current_case_state.time_remaining_seconds} seconds
        - Clue Used: {clue_used}
        {metadata_context}
        """
        
        if user_performance:
            context += f"""
        User Performance:
        - Score: {user_performance.score}/10
        - Analysis: {user_performance.analysis}
        - Strengths: {', '.join(user_performance.strengths)}
        - Weaknesses: {', '.join(user_performance.weaknesses)}
            """
        
        context += f"""
        
        Based on the current state, user performance, and time elapsed, determine if the case should:
        1. ESCALATE (worsen) - patient condition deteriorates, new symptoms appear, complications arise
        2. DE-ESCALATE (improve) - patient responds to treatment, condition stabilizes
        3. MAINTAIN (no change) - stable condition, waiting for next intervention
        
        If clue_used is True, apply a penalty by escalating the case and reducing time.
        
        Generate an updated case state with:
        - Updated clinical_case_scenario_description (reflect the change)
        - Updated investigations (new or changed findings)
        - Updated scan_images (if new tests were ordered)
        - Updated diagnosis (if diagnosis becomes clearer)
        - Incremented n_changes
        - Updated time_remaining_seconds (reduce if penalty applied)
        
        Also provide:
        - escalation_level: float between 0.0 (stable) and 1.0 (critical)
        - change_description: Brief description of what changed and why
        
        Return updated CaseState.
        """
        
        # Get AI response with error handling
        try:
            result = await self.agent.run(context)
            # Agent output_type is CaseState, so result.output should be CaseState
            updated_case = result.output if hasattr(result, 'output') else result
            
            # Ensure it's a CaseState object
            if not isinstance(updated_case, CaseState):
                # If agent returns dict, convert to CaseState
                if isinstance(updated_case, dict):
                    # Merge with current case state
                    updated_case = current_case_state.model_copy(deep=True)
                    updated_case.update(**updated_case)
                else:
                    # Fallback: return current state with incremented changes
                    updated_case = current_case_state.model_copy(deep=True)
            
            # Update case state
            updated_case.n_changes = current_case_state.n_changes + 1
            updated_case.clue_used = clue_used or current_case_state.clue_used
            
            # Preserve metadata if it exists
            if current_case_state.case_metadata:
                updated_case.case_metadata = current_case_state.case_metadata
        except Exception as e:
            # If agent fails, return current state with incremented changes
            print(f"State controller agent failed: {e}")
            updated_case = current_case_state.model_copy(deep=True)
            updated_case.n_changes = current_case_state.n_changes + 1
            updated_case.clue_used = clue_used or current_case_state.clue_used
        
        # Apply penalty if clue was used
        penalty_applied = False
        if clue_used and not current_case_state.penalty_applied:
            updated_case.penalty_applied = True
            updated_case.time_remaining_seconds = max(60, updated_case.time_remaining_seconds - 60)  # Reduce by 60 seconds
            penalty_applied = True
        
        # Calculate escalation level based on changes
        escalation_level = min(1.0, updated_case.n_changes / updated_case.max_clinical_changes)
        change_description = f"Case state updated (change #{updated_case.n_changes})"
        
        return StateChangeResponse(
            updated_case_state=updated_case,
            escalation_level=escalation_level,
            change_description=change_description,
            penalty_applied=penalty_applied
        )
    
    def calculate_escalation_speed(
        self,
        current_changes: int,
        max_changes: int,
        user_performance_score: float
    ) -> float:
        """
        Calculate how fast the case should escalate/de-escalate
        
        Args:
            current_changes: Current number of changes
            max_changes: Maximum allowed changes
            user_performance_score: User's performance score (0-10)
            
        Returns:
            Speed multiplier (0.5 = slow, 1.0 = normal, 2.0 = fast)
        """
        # Base speed on progress through case
        progress = current_changes / max_changes if max_changes > 0 else 0
        
        # Adjust based on performance
        # Lower performance = faster escalation (more challenging)
        # Higher performance = slower escalation (reward good play)
        performance_factor = 1.0 - (user_performance_score / 10.0) * 0.3
        
        # Speed increases as case progresses
        speed = 0.5 + (progress * 0.5) + performance_factor
        
        return max(0.5, min(2.0, speed))


# Global instance
_state_controller_instance: Optional[StateControllerAgent] = None


def get_state_controller_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google"
) -> StateControllerAgent:
    """Get or create the global State Controller Agent instance"""
    global _state_controller_instance
    if _state_controller_instance is None:
        _state_controller_instance = StateControllerAgent(model_name, api_key, provider)
    return _state_controller_instance
