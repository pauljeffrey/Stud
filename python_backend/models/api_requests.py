"""Typed HTTP request/response payloads for API boundaries."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class ScoreOpenAnswerRequest(BaseModel):
    question: str
    correct_answer: str
    user_answer: str
    explanation: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "google"


class SaveCheckpointRequest(BaseModel):
    game_state_id: str
    checkpoint_name: str
    checkpoint_id: Optional[str] = None
    description: Optional[str] = None


class MigrateDemoGameRequest(BaseModel):
    demo_session_id: str
    game_id: str


class WaitlistRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    note: Optional[str] = None
    source_page: Optional[str] = None


class CheckpointSummary(BaseModel):
    id: str
    checkpointId: str
    checkpointName: str
    gameStateId: str
    description: Optional[str] = None
    scenario: str = ""
    patientName: str = ""
    score: int = 0
    phase: str = ""
    createdAt: str


class CheckpointListResponse(BaseModel):
    checkpoints: List[CheckpointSummary] = Field(default_factory=list)


def summarize_checkpoint_row(row: Dict[str, Any]) -> CheckpointSummary:
    """Map a Supabase checkpoint row to the shape the frontend expects."""
    state = row.get("state") or {}
    case_state = state.get("case_state") or {}
    scenario = (
        case_state.get("clinical_case_scenario_description")
        or state.get("scenario")
        or ""
    )
    npc_states = case_state.get("npc_states") or []
    patient_name = ""
    for npc in npc_states:
        if isinstance(npc, dict) and npc.get("role") in ("Patient", "patient"):
            patient_name = npc.get("name") or ""
            break

    performance = state.get("user_performance") or []
    score = 0
    if performance:
        last = performance[-1]
        if isinstance(last, dict):
            score = int(last.get("score", 0) * 10)

    return CheckpointSummary(
        id=str(row.get("id", "")),
        checkpointId=row.get("checkpoint_id", ""),
        checkpointName=row.get("checkpoint_name") or "Checkpoint",
        gameStateId=str(row.get("game_state_id", "")),
        description=row.get("description"),
        scenario=scenario[:200],
        patientName=patient_name,
        score=score,
        phase=state.get("phase") or f"Case {state.get('current_case_number', 1)}",
        createdAt=row.get("created_at") or "",
    )
