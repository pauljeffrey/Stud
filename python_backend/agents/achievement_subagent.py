"""
Achievement sub-agent: intelligently generates achievements from user performance,
previous achievements, and game context.
"""
from typing import List, Optional

from pydantic_ai import Agent
from agents.agents import get_achievement_model
from models.states import (
    Achievement,
    AchievementType,
    AchievementGenerationOutput,
    DifficultyLevel,
)


ACHIEVEMENT_SYSTEM_PROMPT = """You are an achievement designer for a clinical/medical/healthcare simulation game.
Generate 0-4 achievements based on the user's performance and game progress.
Achievements should feel earned, varied, and meaningful.
Use types: PROMOTION, FINANCIAL_REWARD, CERTIFICATION, CAREER_GROWTH (local, regional, national, international).
For FINANCIAL_REWARD, set value to a plausible bonus (e.g. 1000-10000).
Avoid duplicating previous achievements."""


async def generate_achievements(
    avg_score: float,
    user_performance_scores: List[float],
    previous_achievements: List[Achievement],
    current_case_number: int,
    total_cases: int,
    difficulty_level: DifficultyLevel,
    profession: Optional[str] = None,
) -> AchievementGenerationOutput:
    """Generate achievements via LLM sub-agent."""
    model = get_achievement_model()
    agent = Agent(
        model,
        system_prompt=ACHIEVEMENT_SYSTEM_PROMPT,
        output_type=AchievementGenerationOutput,
    )
    prompt = f"""
**USER's CURRENT GAME STATISTICS**
Given:
- avg_score: {avg_score}
- scores: {user_performance_scores}
- previous_achievements: {[a.title for a in previous_achievements]}
- case {current_case_number} of {total_cases}
- difficulty: {difficulty_level.value}
- profession: {profession or 'Healthcare Professional'}

Generate 0-4 achievements. Avoid repeating previous achievements."""
    try:
        result = await agent.run(prompt)
        out = result.output
        return out if isinstance(out, AchievementGenerationOutput) else AchievementGenerationOutput(achievements=previous_achievements)
    except Exception:
        return AchievementGenerationOutput(achievements=previous_achievements)
