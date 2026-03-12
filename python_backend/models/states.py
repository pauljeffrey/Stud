"""
Pydantic models for all game states in ClinicaQuest
Includes common fields abstraction to avoid repetition
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class QuizQuestion(BaseModel):
    question: str
    type: str
    options: Optional[List[str]] = None
    correct_answer: str
    clue: str
    explanation: str

class Quiz(BaseModel):
    id: str
    title: str
    questions: List[QuizQuestion]
    timeLimit: int
    totalQuestions: int
    
    
class RAGResponse(BaseModel):
    response: str
    sources: List[str]
    
# ============================================
# COMMON FIELDS ABSTRACTION
# ============================================
class CommonFields(BaseModel):
    """Common fields shared across multiple states"""
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: str
    case_id: str
    profession: Optional[str] = None
    clinical_setting: Optional[str] = None
    subject: Optional[str] = None
    era: Optional[str] = None
    natural_conditions: Optional[str] = None
    nation_type: Optional[str] = None
    economic_advantage: Optional[str] = None


# ============================================
# ACHIEVEMENT TYPES
# ============================================
class AchievementType(str, Enum):
    CAREER_GROWTH = "career_growth"
    PROMOTION = "promotion"
    FINANCIAL_REWARD = "financial_reward"
    LEADERSHIP_ROLE = "leadership_role"
    TRANSFER = "transfer"
    CERTIFICATION = "certification"
    RECOGNITION = "recognition"
    SKILL_MASTERY = "skill_mastery"


class Achievement(BaseModel):
    """User achievement model"""
    type: AchievementType
    title: str
    description: str
    value: Optional[float] = None  # For financial rewards, etc.
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================
# USER PERFORMANCE TRACKING
# ============================================
class PerformanceAnalysis(BaseModel):
    """Analysis of user performance for a clinical state"""
    score: float = Field(ge=0, le=10, description="Score out of 10")
    analysis: str = Field(description="Concise analysis of user's performance")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    clinical_state_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

class Vitals(BaseModel):
    heartRate: int
    bloodPressure: str
    temperature: float
    respiratoryRate: int
    oxygenSaturation: int

class Investigation(BaseModel):
    type: str
    result: Dict[str, Any]

class Investigations(BaseModel):
    result: List[Investigation]

class ScanImage(BaseModel):
    type: str
    report: str

class ScanImages(BaseModel):
    result: List[ScanImage]
    

class NPCRole(str, Enum):
    NURSE = "Nurse"
    PATIENT = "Patient"
    SPECIALIST = "Specialist"
    RESEARCHER = "Researcher"
    ADMINISTRATOR = "Administrator"

# ============================================
# NPC STATE
# ============================================
class NPCState(BaseModel, CommonFields):
    """State for Non-Playable Characters"""
    name: str
    role: NPCRole # e.g., "Nurse", "Patient", "Specialist"
    age: str
    gender: str
    personality_description: str
    clinical_case_description: str  # The illness/condition this NPC represents
    examination_findings: Dict[str, Any] = Field(default_factory=dict)
    diagnosis: Optional[str] = None
    tone: str = Field(default="professional", description="Communication tone: friendly, professional, anxious, etc.")
    mood: str = Field(default="neutral")
    available: bool = True
    clue_level: int = Field(default=0, ge=0, le=3, description="How many clues this NPC has given")

class DiceEffectRequest(BaseModel):
    game_state: GameState
    dice_result: int
    
class SaveGameRequest(BaseModel):
    game_state: GameState
    
# ============================================
# CASE STATE
# ============================================
class ClinicalCaseMetadata(BaseModel):
    """Metadata for clinical case generation/escalation"""
    case_number: int
    profession: str
    clinical_setting: str
    subject: str
    era: str
    natural_conditions: str
    nation_type: str
    economic_advantage: str
    difficulty_level: Optional[str] = None
    previous_cases: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of previous cases with scenario, diagnosis, and question to prevent duplicates"
    )


class CaseState(BaseModel, CommonFields):
    """State for clinical case scenarios"""
    case_state_id: str
    clinical_case_scenario_description: str
    question: str
    diagnosis: Optional[str] = None
    investigations: Optional[Investigations] = Field(default_factory=dict)
    scan_images: Optional[ScanImages] = Field(default_factory=dict)
    options: Optional[List[str]] = Field(description="provide options if multi-choice. if not, user will answer open-endedly")  # For multiple choice questions
    answer: Optional[str] = None
    reason_for_answer: Optional[str] = None
    clue: Optional[str] = None
    npc: Optional[NPCState] = None  # Single NPC reference (will be replaced with list)
    npc_states: Optional[List[NPCState]] = Field(default_factory=list, description="List of NPCs for this case")
    n_changes: int = Field(default=0, ge=0, description="Number of times case has changed")
    max_clinical_changes: int = Field(default=10, ge=5, le=15, description="Max times case can change")
    time_limit_seconds: int = Field(default=300, description="Time limit for this case")
    time_remaining_seconds: int = Field(default=300)
    clue_used: bool = Field(default=False, description="Whether user has used clue button")
    penalty_applied: bool = Field(default=False, description="Whether penalty was applied for using clue")
    case_metadata: Optional[ClinicalCaseMetadata] = Field(default=None, description="Metadata for case generation")


class StateChangeResponse(BaseModel):
    """Response from State Controller Agent when updating case state"""
    updated_case_state: CaseState
    escalation_level: float = Field(ge=0.0, le=1.0, description="Escalation level: 0.0=stable, 1.0=critical")
    change_description: str
    penalty_applied: bool = Field(default=False)


# ============================================
# GAME WORLD STATE
# ============================================
class GameWorldModel(BaseModel):
    """Game world description and configuration"""
    world_id: str
    world_description: str
    profession: str
    clinical_setting: str
    subject: str
    era: str
    natural_conditions: str
    nation_type: str
    economic_advantage: str
    location: str
    hospital_name: Optional[str] = None
    department: Optional[str] = None
    additional_context: Dict[str, Any] = Field(default_factory=dict)


# ============================================
# GAME STATE (Main State)
# ============================================
class GameState(BaseModel, CommonFields):
    """Main game state containing all sub-states"""
    game_id: str
    game_world: GameWorldModel
    case_state: CaseState
    game_config: GameConfig  # Store game config as object instead of individual fields
    
    # Game progression
    current_case_number: int = Field(default=1, ge=1, le=50)
    total_cases: int = Field(default=30, ge=20, le=50)
    user_performance: List[PerformanceAnalysis] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)
    
    # Metadata
    started_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    is_demo: bool = Field(default=False)
    demo_limits: Optional[Dict[str, int]] = Field(default=None, description="Demo mode limits")


# ============================================
# GAME CONFIGURATION
# ============================================
class GameConfig(BaseModel):
    """Configuration for game initialization"""
    profession: Optional[str] = None
    clinical_setting: Optional[str] = None
    subject: Optional[str] = None
    era: Optional[str] = None
    natural_conditions: Optional[str] = None
    nation_type: Optional[str] = None
    economic_advantage: Optional[str] = None
    total_cases: int = Field(default=30, ge=20, le=50)
    max_clinical_changes: int = Field(default=5, ge=5, le=12)
    time_limit_per_case: int = Field(default=300, description="Seconds per case")
    difficulty: Optional[str] = Field(default=None, description="beginner, intermediate, advanced")
    from_document: bool = Field(default=False)
    document_id: Optional[str] = None
    document_content: Optional[str] = None


class GameProgress(BaseModel):
    current_phase: str
    completed_actions: List[str]
    score: int
    time_elapsed: int
    dice_rolls: int
    last_dice_result: int