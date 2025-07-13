from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class UserResponse(BaseModel):
    answer: str
    reason: Optional[str] = None

class Scene(BaseModel):
    description: str

class Scenario(BaseModel):
    scenes: List[Scene]
    
# Pydantic Model for Game Scenario Output
class GameScenario(BaseModel):
    game_scenario: Scenario
    country_situation: str
    metadata: dict
    objective: str

class Investigation(BaseModel):
    type: str  # e.g., "full blood count", "lft", etc.
    result: Dict[str, Any]

class Investigations(BaseModel):
    result: List[Investigation]

class ScanImage(BaseModel):
    type: str  # e.g., "USS", "CT scan", etc.
    result: Dict[str, Any]  # Image object in the best format
    report: str  # Report of the image

class ScanImages(BaseModel):
    result: List[ScanImage]

class PhysiologicSignal(BaseModel):
    type: Optional[str] = None  # e.g., "ECG", "EEG", etc.
    result: Optional[Dict[str, Any]] = None

class PhysiologicSignals(BaseModel):
    result: List[PhysiologicSignal] = []

class AIResponse(BaseModel):
    scenario: GameScenario
    question: str
    options: Optional[List[str]] = None
    answer: str
    clue: str
    blood_investigation: Optional[Investigations] = None
    scan: Optional[ScanImages] = None
    signals: Optional[PhysiologicSignals] = None
    time: str  # Time in seconds string for countdown timer in frontend

class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class GameState(BaseModel):
    user_id: str
    case_id: str
    messages: List[Message] = []
    current_scenario: Optional[Scenario] = None
    current_question: Optional[str] = None
    options: Optional[List[str]] = None
    time_remaining: int = 600  # Default 10 minutes
    checkpoint: Optional[str] = None
    lifelines_used: Dict[str, bool] = Field(default_factory=lambda: {
        "friend": False,
        "clue": False,
        "eliminate": False
    })
    score: int = 0
    quiz_type: Optional[str] = None  # "open", "true_false", "multichoice"
    num_questions: Optional[int] = None
    current_question_index: int = 0
    total_questions: Optional[int] = None

class GameRequest(BaseModel):
    game_state: GameState
    user_response: Optional[UserResponse] = None

class GameResponse(BaseModel):
    game_state: GameState
    response: AIResponse
    
class NPC(BaseModel):
    name: str
    sex: str
    role: str  # e.g., "doctor", "nurse", etc.
    description: str
    behaviour_rules: Dict[str, Any]  # Rules for NPC behaviour
    dialogue: List[str]  # Possible dialogues or interactions with the NPC