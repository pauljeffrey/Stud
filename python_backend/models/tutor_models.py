"""Learning domain models: curriculum, study plan, enrollment."""
from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional, Union
import uuid

from pydantic import BaseModel, Field


class CurriculumModule(BaseModel):
    module_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    objectives: List[str] = Field(default_factory=list)
    content_ids: List[str] = Field(default_factory=list)
    estimated_minutes: int = 30
    is_completed: bool = False


class Curriculum(BaseModel):
    """High-level academic framework for a document or subject."""

    curriculum_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    title: str
    description: str = ""
    modules: List[CurriculumModule] = Field(default_factory=list)
    difficulty_level: str = "Intermediate"
    is_completed: bool = False


class DailyTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    module_id: str = ""
    title: str = ""
    is_completed: bool = False
    scheduled_date: Optional[date] = None
    actual_completion_date: Optional[datetime] = None


class StudyPlan(BaseModel):
    """Personalized roadmap through a curriculum."""

    plan_id: str
    user_id: str
    curriculum_id: str
    start_date: date
    target_end_date: date
    daily_schedule: List[DailyTask] = Field(default_factory=list)
    pace_preference: str = "balanced"
    current_progress_percentage: float = 0.0


class UserEnrollment(BaseModel):
    """Links a user to a curriculum + study plan + document."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    curriculum_id: str
    study_plan_id: str
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    document_id: Union[uuid.UUID, str]
