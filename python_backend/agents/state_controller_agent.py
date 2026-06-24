"""
State Controller Agent for Stud
Solely responsible for escalating or de-escalating clinical cases
Controls the degree of randomness and speed of escalation/de-escalation
"""
from __future__ import annotations

import logging
from typing import Optional

from pydantic_ai import Agent, RunContext
import json
import random

from agents.agents import get_state_controller_model
from models.states import CaseState, PerformanceAnalysis, StateChangeResponse, ClinicalCaseMetadata

logger = logging.getLogger(__name__)


def _state_controller_tool_fns(ctrl: "StateControllerAgent"):
    async def compute_escalation_intensity(
        ctx: RunContext[None],
        current_changes: int,
        max_changes: int,
        user_performance_score: float,
    ) -> str:
        """Speed from progress + performance, combined with RNG for escalation_intensity (0–1). Call before finalizing the case update."""
        speed = ctrl.calculate_escalation_speed(current_changes, max_changes, user_performance_score)
        r, u = random.random(), random.random()
        blend = r * 0.55 + u * 0.45
        intensity = max(0.0, min(1.0, blend * speed / 1.8))
        return json.dumps({
            "speed_multiplier": round(speed, 4),
            "escalation_intensity": round(intensity, 4),
            "rng": [round(r, 4), round(u, 4)],
        })

    async def time_urgency_note(
        ctx: RunContext[None],
        time_remaining_seconds: int,
        time_limit_seconds: int,
    ) -> str:
        """How pressed for time the team is (urgency 0–1); use to tune pacing."""
        if time_limit_seconds <= 0:
            return json.dumps({"urgency": 1.0})
        urg = 1.0 - (time_remaining_seconds / time_limit_seconds)
        return json.dumps({"urgency": round(max(0.0, min(1.0, urg)), 3)})

    return [compute_escalation_intensity, time_urgency_note]


class StateControllerAgent:
    """
    State Controller Agent responsible for dynamically changing clinical cases
    Escalates or de-escalates based on user performance and time
    """

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, provider: str = "google"):
        self._model_name = model_name
        self._api_key = api_key
        self._tool_suffix = (
            " TOOLS: Before you finalize the updated CaseState, call `compute_escalation_intensity` with "
            "current n_changes, max_clinical_changes, and the latest performance score (0–10). "
            "Use `escalation_intensity` from the returned JSON to scale how dramatic the clinical narrative change is. "
            "Optionally call `time_urgency_note` with time_remaining_seconds and time_limit_seconds to align tension with time pressure."
        )
        self.system_prompt = """
            You are the State Controller for Stud. You escalate or de-escalate clinical cases based on user performance.
            
            BREVITY: clinical_case_scenario_description must be 3-5 concise sentences. No long paragraphs.
            investigations and scan_images: only key findings, brief values.
            
            CRITICAL: Compare user answer to model answer:
            - Correct → de-escalate or maintain
            - Incorrect → escalate proportionally
            - Partially correct → moderate adjustment
            
            Start updated clinical_case_scenario_description with whether the user's answer was correct.
            """ + self._tool_suffix
        model = get_state_controller_model(model_name, api_key)
        self.agent = Agent(
            model,
            system_prompt=self.system_prompt,
            output_type=CaseState,
            tools=_state_controller_tool_fns(self),
        )
        # Tool-free agent for new case generation — skips escalation tools
        # that would otherwise add 2 extra LLM round-trips on every init call.
        self._generation_agent = Agent(
            model,
            system_prompt=self.system_prompt,
            output_type=CaseState,
        )

    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        if model_name is not None:
            self._model_name = model_name
        if api_key is not None:
            self._api_key = api_key
        model = get_state_controller_model(self._model_name, self._api_key)
        self.agent = Agent(
            model,
            system_prompt=self.system_prompt,
            output_type=CaseState,
            tools=_state_controller_tool_fns(self),
        )
        self._generation_agent = Agent(
            model,
            system_prompt=self.system_prompt,
            output_type=CaseState,
        )

    async def generate_case(self, prompt: str) -> CaseState:
        """Generate a brand-new clinical case from a prompt.

        Uses the tool-free agent so escalation tools are not invoked,
        saving 2 extra LLM round-trips compared to self.agent.
        """
        result = await self._generation_agent.run(prompt)
        return result.output

    async def update_case_state(
        self,
        current_case_state: CaseState,
        case_metadata: Optional[ClinicalCaseMetadata] = None,
        user_performance: Optional[PerformanceAnalysis] = None,
        time_elapsed: int = 0,
        clue_used: bool = False,
        user_answer: Optional[str] = None,
        model_answer: Optional[str] = None,
    ) -> StateChangeResponse:
        if current_case_state.n_changes >= current_case_state.max_clinical_changes:
            return StateChangeResponse(
                updated_case_state=current_case_state,
                escalation_level=1.0,
                change_description="Maximum clinical changes reached. Case ready for handoff to Game Master.",
                penalty_applied=False
            )

        metadata_context = ""
        if case_metadata:
            metadata_context = f"""
        Case Metadata:
        - Case Number: {case_metadata.case_number}
        - Profession: {case_metadata.profession}
        - Clinical Setting: {case_metadata.clinical_setting}
        - Subject: {case_metadata.subject}
        - Era: {case_metadata.era}
        - Difficulty Level: {case_metadata.difficulty_level}

        IMPORTANT: The difficulty level is {case_metadata.difficulty_level}.
        Adjust the escalation/de-escalation intensity accordingly to user's action (or user's answer) and model (correct) answer:
        - 0 - 2: Gradual, manageable changes
        - 2 - 4: More dramatic, challenging changes
        - 4 - 6: Severe, critical escalations with high complexity
        2 - 6 can be multi-disciplinary
        """

        context = f"""
        Current Case State:
        - Case ID: {current_case_state.case_state_id}
        - Scenario: {current_case_state.clinical_case_scenario_description[:500]}
        - Current Diagnosis: {current_case_state.diagnosis or 'Not yet diagnosed'}
        - Examination Findings: {json.dumps(current_case_state.investigations or {})}
        - Investigation Results: {json.dumps(current_case_state.scan_images or {})}
        - Number of Changes: {current_case_state.n_changes} out of {current_case_state.max_clinical_changes}
        - Time Elapsed: {time_elapsed} seconds
        - Time Remaining: {current_case_state.time_remaining_seconds} seconds
        - Clue Used: {clue_used}
        - Model Answer (correct): {model_answer or getattr(current_case_state, 'answer', None) or 'Not yet revealed'}
        - User's Answer: {user_answer or 'Not yet provided'}
        - maximum number of changes you can make: {current_case_state.max_clinical_changes}

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

        perf_score = user_performance.score if user_performance else 5.0
        context += f"""
        For tools: use current_changes={current_case_state.n_changes}, max_changes={current_case_state.max_clinical_changes}, user_performance_score={perf_score:.1f}.
        For time_urgency_note: time_remaining_seconds={current_case_state.time_remaining_seconds}, time_limit_seconds={current_case_state.time_limit_seconds}.

        Based on the current state, user performance, *model answer, user's answer*, and time elapsed, determine if the case should:
        1. ESCALATE (worsen) - patient condition deteriorates, new symptoms appear, complications arise
        2. DE-ESCALATE (improve) - patient responds to treatment, condition stabilizes
        3. MAINTAIN (no change or just natural progression) - stable condition, waiting for next intervention

        If clue_used is True, apply an additional penalty by escalating the case and reducing time.

        Generate an updated case state with:
        - Updated clinical_case_scenario_description: MUST start by stating whether user's answer was correct or not, then reflect the clinical change
        - Updated investigations (new or changed findings)
        - Updated scan_images (if new tests were ordered)
        - Updated diagnosis (if diagnosis becomes clearer)
        - Incremented n_changes
        - Updated time_remaining_seconds (reduce if penalty applied)

        Also provide:
        - escalation_level: float between 0.0 (stable) and 1.0 (critical)
        - change_description: Brief description of what changed and why

        Do not change the case_state_id,  max_clinical_changes if they already exist.
        Return updated CaseState.
        """

        try:
            result = await self.agent.run(context)
            updated_case = result.output

            if not isinstance(updated_case, CaseState):
                if isinstance(updated_case, dict):
                    updated_case = current_case_state.model_copy(deep=True)
                    updated_case.update(**updated_case)
                else:
                    updated_case = current_case_state.model_copy(deep=True)

            updated_case.n_changes = current_case_state.n_changes + 1
            updated_case.clue_used = clue_used or current_case_state.clue_used

            if hasattr(current_case_state, 'case_metadata') and current_case_state.case_metadata:
                updated_case.case_metadata = current_case_state.case_metadata
            elif case_metadata:
                updated_case.case_metadata = case_metadata
        except Exception as e:
            logger.exception("State controller agent failed during update_case_state")
            updated_case = current_case_state.model_copy(deep=True)
            updated_case.n_changes = current_case_state.n_changes + 1
            updated_case.clue_used = clue_used or current_case_state.clue_used

        penalty_applied = False
        if clue_used and not current_case_state.penalty_applied:
            updated_case.penalty_applied = True
            updated_case.time_remaining_seconds = max(60, updated_case.time_remaining_seconds - 30)
            penalty_applied = True

        escalation_level = min(1.0, updated_case.n_changes / max(1, updated_case.max_clinical_changes))
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
        progress = current_changes / max_changes if max_changes > 0 else 0
        performance_factor = 1.0 - (user_performance_score / 10.0) * 0.3
        speed = 0.5 + (progress * 0.5) + performance_factor
        return max(0.5, min(2.0, speed))


_state_controller_instance: Optional[StateControllerAgent] = None


def get_state_controller_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google"
) -> StateControllerAgent:
    global _state_controller_instance
    if _state_controller_instance is None:
        _state_controller_instance = StateControllerAgent(model_name, api_key, provider)
    return _state_controller_instance
