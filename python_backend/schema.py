"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any


class LearningChatRequest(BaseModel):
    """Request model for learning chat endpoint"""
    message: str
    document_id: Optional[str] = Field(None, alias="documentId")
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    enrollment_id: Optional[str] = Field(None, alias="enrollmentId")
    chat_history: Optional[List[Dict[str, Any]]] = None
    profession: Optional[str] = None
    subject_of_study: Optional[str] = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def require_document_or_enrollment(self):
        if not self.document_id and not self.enrollment_id:
            raise ValueError("Either documentId or enrollmentId is required")
        return self
