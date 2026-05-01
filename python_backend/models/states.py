"""
Pydantic models for all game states in ClinicaQuest
Includes common fields abstraction to avoid repetition
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional, Literal, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid


class TutorResponse(BaseModel):
    """Response from tutor agent. Includes optional action flags for quiz/quest."""
    response: str
    sources: List[str] = Field(default_factory=list)
    generate_quiz: bool = False
    play_quest: bool = False
    user_performance_analysis: Optional[Dict[str, Any]] = None


# Backward compatibility
RAGResponse = TutorResponse
    
# ============================================
# USER DETAILS
# ============================================
class UserDetails(BaseModel):
    """User context for game personalization"""
    user_id: str
    profession: Optional[str] = None
    field_of_study: Optional[str] = None
    model_config = ConfigDict(extra="allow")


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
    score: float = Field(ge=0, le=10, description="Score out of 10 (float value)")
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
    RELATIVE = "Patient's Relative"
    SPECIALIST = "Specialist"
    RESEARCHER = "Researcher"
    ADMINISTRATOR = "Administrator"
    FAMILY_MEMBER = "Family Member"
    COLLEAGUE = "Colleague"

class DifficultyLevel(str, Enum):
    Easy = "Easy"
    Medium = "Medium"
    Hard = "Hard"
    Extreme = "Extreme"
    Fiendish = "Fiendish"
    Impossible = "Impossible"
    

# ============================================
# NPC STATE
# ============================================
class NPCState(CommonFields, extra="allow"):
    """State for Non-Playable Characters"""
    model_config = ConfigDict(extra="allow")
    npc_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    case_id: str
    name: str = Field(description="Full Name of the NPC")
    role: NPCRole # e.g., "Nurse", "Patient", "Specialist"
    age: str
    gender: str
    personality_description: str
    # clinical_case_description: str = None # The illness/condition this NPC represents
    examination_findings: Dict[str, Any] = Field(description="Examination findings if role is Patient")
    # diagnosis: Optional[str] = None
    tone: str = Field(default="professional", description="Communication tone: friendly, professional, anxious, etc.")
    mood: str = Field(default="neutral")
    available: bool = True
    clue_level: int = Field(default=0, ge=0, le=3, description="""The level of clue this NPC can give (0-3). 0=no clue, 1=subtle hint, 
                2=more direct clue, 3=can be more explicit. Only for patient and healthcare professional directly involved in patient care.""")
    
# ============================================
# CASE STATE
# ============================================

class ClinicalCaseMetadata(BaseModel):
    """Metadata for clinical case generation/escalation"""
    model_config = ConfigDict(extra="allow")

    case_number: int
    profession: str
    clinical_setting: str
    subject: str
    subtopic: str
    diagnosis: str
    difficulty_level: DifficultyLevel
    n_escalations: int = Field(default=0, ge=0, le=10, description="Number of times case has been escalated")
    previous_cases_summary: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    
class CaseState(CommonFields):
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
    npc_roles: Optional[List[NPCRole]] = Field(default_factory=list, description="List of NPC roles for this case")
    n_changes: int = Field(default=0, ge=0, description="Number of times case has changed")
    max_clinical_changes: int = Field(default=10, ge=3, le=15, description="Max times case can change")
    time_limit_seconds: int = Field(default=300, description="Time limit for this case")
    time_remaining_seconds: int = Field(default=300)
    clue_used: bool = Field(default=False, description="Whether user has used clue button")
    penalty_applied: bool = Field(default=False, description="Whether penalty was applied for using clue")
    case_metadata: Optional[ClinicalCaseMetadata] = Field(default=None, description="Metadata for case generation")
    npc_states: Optional[List[NPCState]] = Field(default=None, description="NPCs attached to this case")


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
    world_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    world_description: str
    profession: str #
    clinical_setting: str #
    subject: str #
    era: str #
    natural_conditions: str#
    nation_type: str #
    economic_advantage: str #
    location: str
    hospital_name: Optional[str] = Field(default ="",description="Name of the hospital. if not applicable based on the setting/era, use something similar that was used in that era.")
    department: Optional[str] = Field(default ="",description="Name of the department. if not applicable based on the setting/era, use something similar that was used in that era.")
    additional_context: Dict[str, Any] = Field(default_factory=dict)


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
    total_cases: int = Field(default=30, ge=1, le=50)
    max_clinical_changes: int = Field(default=5, ge=3, le=12)
    time_limit_per_case: int = Field(default=300, description="Seconds per case")
    difficulty: Optional[str] = Field(default=None, description="beginner, intermediate, advanced")
    from_document: bool = Field(default=False)
    document_id: Optional[str] = None
    dice_enabled: bool = Field(default=False, description="Toggle dice-roll mechanic on answer submission")
    

class Options(Enum):
    A: str = 'A'
    B: str = 'B'
    C: str = 'C'
    D: str = 'D'
    E:Optional[str] = 'E'
    
class QuizQuestion(BaseModel, extra="allow"):    
    question: str
    type: Literal['multiple_choice', 'open_ended', 'true_false']  # "multiple_choice" or "open_ended"
    options: Optional[List[str]] = None
    correct_answer: Union[str, Options]
    difficulty_level: DifficultyLevel
    explanation: str
    score: Optional[int] = Field(description="Score according to importance of fundamentally understanding the question.", default=None, ge=0, le=10)

class Quiz(BaseModel):
    id: str
    title: str
    questions: List[QuizQuestion]
    timeLimit: int
    totalQuestions: int
    source: Literal['AI_knowledge', 'document']


class OpenEndedAnswer(BaseModel):
    """Model for scoring open-ended answers"""
    score: float  # 0-10
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    # correct_elements: List[str]
    # missing_elements: List[str]
class AchievementGenerationOutput(BaseModel):
    """Output from achievement sub-agent"""
    achievements: List[Achievement] = Field(default_factory=list)


class GameStateUpdateOutput(BaseModel):
    """Output when updating a game state for next case generation"""
    difficulty_level: DifficultyLevel
    case_metadata: Optional[ClinicalCaseMetadata] = None


class PreviousCases(BaseModel):
    """Container for previous cases to prevent duplicates"""
    cases: List[Dict[str, Any]] = Field(default_factory=list)
    n_cases_generated: int = Field(default=0)
    current_difficulty_level: DifficultyLevel = Field(default=DifficultyLevel.Medium)
    
    def get_previous_difficulty_levels(self) -> List[DifficultyLevel]:
        """List of difficulty levels from previous cases."""
        return [
            c['difficulty_level']
            for c in self.cases
        ]
    
    def add_case(self, case: CaseState):
        self.cases.append({"case_state_id": case.case_state_id, 'difficulty_level': case.case_metadata.difficulty_level, "clinical_case_scenario_description": case.clinical_case_scenario_description, "diagnosis": case.diagnosis, "question": case.question})
        self.n_cases_generated += 1
        return self
    
    def get_case(self, index: int) -> Optional[Dict[str, Any]]:
        if 0 <= index < len(self.cases):
            return self.cases[index]
        return None
    
    def get_all_cases(self) -> List[Dict[str, Any]]:
        return self.cases
    
    def get_summary_for_metadata(self) -> List[Dict[str, str]]:
        """Get summary of cases for ClinicalCaseMetadata"""
        return self.cases

# ============================================
# GAME STATE (Main State)
# ============================================
class GameState(CommonFields, extra='allow'):
    """Main game state containing all sub-states"""
    game_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_config: GameConfig  # Store game config as object instead of individual fields
    difficulty_level: DifficultyLevel
    case_metadata: ClinicalCaseMetadata
    
    # Game progression
    current_case_number: int = Field(default=1, ge=1, le=50)
    total_cases: int = Field(default=30, ge=1, le=50)
    user_performance: List[PerformanceAnalysis] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)
    previous_cases: Optional[PreviousCases] = Field(default=None, description="For checkpoint resumption")
    
    # Metadata
    started_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    is_demo: bool = Field(default=False)
    demo_limits: Optional[Dict[str, int]] = Field(default=None, description="Demo mode limits")

class DiceEffectRequest(BaseModel):
    game_state: GameState
    dice_result: int = Field(ge=0, le=10, description="Roll outcome 0-10 for escalation modifier")
    
class SaveGameRequest(BaseModel):
    game_state: GameState
    