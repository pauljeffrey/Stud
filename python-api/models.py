from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class PatientInfo(BaseModel):
    name: str
    age: int
    gender: str
    chief_complaint: str
    current_condition: str
    background: str
    vitals: Dict[str, Any]

class GameProgress(BaseModel):
    current_phase: str
    completed_actions: List[str]
    score: int
    time_elapsed: int
    dice_rolls: int
    last_dice_result: int

class NPC(BaseModel):
    name: str
    role: str
    available: bool
    mood: str

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime
    npc_name: Optional[str] = None

class GameState(BaseModel):
    user_id: str
    case_id: str
    current_scenario: str
    patient_info: PatientInfo
    game_progress: GameProgress
    inventory: List[str]
    chat_history: List[ChatMessage]
    npcs: List[NPC]

class GameChatRequest(BaseModel):
    game_state: GameState
    user_message: str

class DiceEffectRequest(BaseModel):
    game_state: GameState
    dice_result: int

class NPCChatRequest(BaseModel):
    game_state: GameState
    npc_name: str

class SaveGameRequest(BaseModel):
    game_state: GameState

class LearningChatRequest(BaseModel):
    document_id: str
    message: str
    chat_history: List[Dict[str, str]]

class UserResponse(BaseModel):
    answer: str
    reason: Optional[str] = None

class Scene(BaseModel):
    description: str

class Scenario(BaseModel):
    scenes: List[Scene]
    
class Investigation(BaseModel):
    type: str
    result: Dict[str, Any]

class Investigations(BaseModel):
    result: List[Investigation]

class ScanImage(BaseModel):
    type: str
    result: Dict[str, Any]
    report: str

class ScanImages(BaseModel):
    result: List[ScanImage]

class PhysiologicSignal(BaseModel):
    type: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class PhysiologicSignals(BaseModel):
    result: List[PhysiologicSignal] = []

class AIResponse(BaseModel):
    scenario: Scenario
    question: str
    options: Optional[List[str]] = None
    answer: str
    clue: str
    blood_investigation: Optional[Investigations] = None
    scan: Optional[ScanImages] = None
    signals: Optional[PhysiologicSignals] = None
    time: str
