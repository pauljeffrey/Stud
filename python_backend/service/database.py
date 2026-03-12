"""
Database Service Interface
Provides a clean API for reading and writing to all database tables
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from supabase import create_client, Client
from config import config
import json
import uuid


class DatabaseService:
    """
    Database service for interacting with Supabase tables
    Provides typed methods for all CRUD operations
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        self.client: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_SERVICE_ROLE_KEY
        )
    
    # ============================================
    # USER OPERATIONS
    # ============================================
    
    def create_user(
        self,
        email: str,
        password_hash: str,
        name: str,
        profession: Optional[str] = None,
        age: Optional[int] = None,
        avatar_url: Optional[str] = None,
        bio: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new user"""
        result = self.client.table("users").insert({
            "email": email,
            "password_hash": password_hash,
            "name": name,
            "profession": profession,
            "age": age,
            "avatar_url": avatar_url,
            "bio": bio,
            "is_active": True
        }).execute()
        return result.data[0] if result.data else {}
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        result = self.client.table("users").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        result = self.client.table("users").select("*").eq("email", email).execute()
        return result.data[0] if result.data else None
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        result = self.client.table("users").update(updates).eq("id", user_id).execute()
        return result.data[0] if result.data else {}
    
    # ============================================
    # GAME STATE OPERATIONS
    # ============================================
    
    def create_game_state(
        self,
        user_id: str,
        case_id: str,
        state: Dict[str, Any],
        is_demo: bool = False,
        scenario_type: str = "standard",
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new game state"""
        game_id = str(uuid.uuid4())
        result = self.client.table("game_states").insert({
            "id": game_id,
            "user_id": user_id,
            "case_id": case_id,
            "state": state,
            "is_demo": is_demo,
            "scenario_type": scenario_type,
            "document_id": document_id,
            "is_active": True
        }).execute()
        return result.data[0] if result.data else {}
    
    def get_game_state(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get game state by ID"""
        result = self.client.table("game_states").select("*").eq("id", game_id).execute()
        return result.data[0] if result.data else None
    
    def get_user_game_states(
        self,
        user_id: str,
        limit: int = 10,
        is_active: Optional[bool] = None,
        is_demo: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get user's game states"""
        query = self.client.table("game_states").select("*").eq("user_id", user_id)
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        if is_demo is not None:
            query = query.eq("is_demo", is_demo)
        
        result = query.order("updated_at", desc=True).limit(limit).execute()
        return result.data or []
    
    def update_game_state(self, game_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update game state"""
        updates["updated_at"] = datetime.now().isoformat()
        result = self.client.table("game_states").update(updates).eq("id", game_id).execute()
        return result.data[0] if result.data else {}
    
    def delete_game_state(self, game_id: str) -> bool:
        """Delete game state"""
        result = self.client.table("game_states").delete().eq("id", game_id).execute()
        return len(result.data) > 0
    
    def complete_game_state(self, game_id: str) -> Dict[str, Any]:
        """Mark game state as completed"""
        return self.update_game_state(game_id, {
            "completed_at": datetime.now().isoformat(),
            "is_active": False
        })
    
    # ============================================
    # GAME CHECKPOINT OPERATIONS
    # ============================================
    
    def create_checkpoint(
        self,
        user_id: str,
        game_state_id: str,
        checkpoint_id: str,
        checkpoint_name: str,
        state: Dict[str, Any],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a game checkpoint"""
        result = self.client.table("game_checkpoints").insert({
            "user_id": user_id,
            "game_state_id": game_state_id,
            "checkpoint_id": checkpoint_id,
            "checkpoint_name": checkpoint_name,
            "state": state,
            "description": description
        }).execute()
        return result.data[0] if result.data else {}
    
    def get_checkpoints(self, game_state_id: str) -> List[Dict[str, Any]]:
        """Get all checkpoints for a game state"""
        result = self.client.table("game_checkpoints").select("*").eq(
            "game_state_id", game_state_id
        ).order("created_at", desc=True).execute()
        return result.data or []
    
    # ============================================
    # GAME STATISTICS OPERATIONS
    # ============================================
    
    def get_game_statistics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's game statistics"""
        result = self.client.table("game_statistics").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    
    def update_game_statistics(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update game statistics"""
        result = self.client.table("game_statistics").upsert({
            "user_id": user_id,
            **updates,
            "updated_at": datetime.now().isoformat()
        }).execute()
        return result.data[0] if result.data else {}
    
    # ============================================
    # USER PERFORMANCE OPERATIONS
    # ============================================
    
    def create_user_performance(
        self,
        user_id: str,
        game_id: str,
        clinical_state_id: str,
        score: float,
        analysis: str,
        strengths: List[str],
        weaknesses: List[str]
    ) -> Dict[str, Any]:
        """Create user performance record"""
        result = self.client.table("user_performance").insert({
            "user_id": user_id,
            "game_id": game_id,
            "clinical_state_id": clinical_state_id,
            "score": score,
            "analysis": analysis,
            "strengths": json.dumps(strengths),
            "weaknesses": json.dumps(weaknesses)
        }).execute()
        return result.data[0] if result.data else {}
    
    def get_user_performance(self, user_id: str, game_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user performance records"""
        query = self.client.table("user_performance").select("*").eq("user_id", user_id)
        if game_id:
            query = query.eq("game_id", game_id)
        result = query.order("timestamp", desc=True).execute()
        return result.data or []
    
    # ============================================
    # QUIZ OPERATIONS
    # ============================================
    
    def create_quiz(
        self,
        user_id: str,
        title: str,
        questions: List[Dict[str, Any]],
        quiz_type: str,
        time_limit: int,
        total_questions: int,
        source: str = "ai_knowledge",
        document_id: Optional[str] = None,
        difficulty: str = "intermediate"
    ) -> Dict[str, Any]:
        """Create a quiz"""
        quiz_id = str(uuid.uuid4())
        result = self.client.table("quizzes").insert({
            "id": quiz_id,
            "user_id": user_id,
            "title": title,
            "questions": json.dumps(questions),
            "quiz_type": quiz_type,
            "time_limit": time_limit,
            "total_questions": total_questions,
            "source": source,
            "document_id": document_id,
            "difficulty": difficulty
        }).execute()
        return result.data[0] if result.data else {}
    
    def get_quiz(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """Get quiz by ID"""
        result = self.client.table("quizzes").select("*").eq("id", quiz_id).execute()
        return result.data[0] if result.data else None
    
    def get_user_quizzes(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's quizzes"""
        result = self.client.table("quizzes").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    
    def create_quiz_result(
        self,
        user_id: str,
        quiz_id: str,
        answers: Dict[str, Any],
        scores: Dict[str, float],
        total_score: float,
        time_spent: int
    ) -> Dict[str, Any]:
        """Create quiz result"""
        result = self.client.table("quiz_results").insert({
            "user_id": user_id,
            "quiz_id": quiz_id,
            "answers": json.dumps(answers),
            "scores": json.dumps(scores),
            "score": int(total_score),
            "total_score": total_score,
            "time_spent": time_spent
        }).execute()
        return result.data[0] if result.data else {}
    
    def get_quiz_results(self, user_id: str, quiz_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get quiz results"""
        query = self.client.table("quiz_results").select("*, quizzes(*)").eq("user_id", user_id)
        if quiz_id:
            query = query.eq("quiz_id", quiz_id)
        result = query.order("completed_at", desc=True).limit(limit).execute()
        return result.data or []
    
    def get_quiz_statistics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's quiz statistics"""
        result = self.client.table("quiz_statistics").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    
    # ============================================
    # DOCUMENT OPERATIONS
    # ============================================
    
    def create_document(
        self,
        user_id: str,
        name: str,
        file_name: str,
        file_type: str,
        file_size: int,
        content: Optional[str] = None,
        pinecone_index_name: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a document record"""
        if expires_at is None:
            expires_at = datetime.now().timestamp() + (2 * 60 * 60)  # 2 hours from now
        
        result = self.client.table("documents").insert({
            "user_id": user_id,
            "name": name,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "content": content[:10000] if content else None,  # First 10k chars
            "pinecone_index_name": pinecone_index_name,
            "pinecone_index_expires_at": expires_at.isoformat() if isinstance(expires_at, datetime) else expires_at,
            "processed": False,
            "processing_status": "pending"
        }).execute()
        return result.data[0] if result.data else {}
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        result = self.client.table("documents").select("*").eq("id", document_id).execute()
        return result.data[0] if result.data else None
    
    def get_user_documents(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's documents"""
        result = self.client.table("documents").select("*").eq(
            "user_id", user_id
        ).order("uploaded_at", desc=True).limit(limit).execute()
        return result.data or []
    
    def update_document(self, document_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update document"""
        result = self.client.table("documents").update(updates).eq("id", document_id).execute()
        return result.data[0] if result.data else {}
    
    def mark_document_processed(
        self,
        document_id: str,
        chunk_count: int,
        pinecone_index_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark document as processed"""
        return self.update_document(document_id, {
            "processed": True,
            "processing_status": "completed",
            "chunk_count": chunk_count,
            "pinecone_index_name": pinecone_index_name,
            "processed_at": datetime.now().isoformat()
        })
    
    # ============================================
    # LEARNING CHAT OPERATIONS
    # ============================================
    
    def create_chat_message(
        self,
        user_id: str,
        document_id: str,
        role: str,
        content: str,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a chat message"""
        result = self.client.table("learning_chat_history").insert({
            "user_id": user_id,
            "document_id": document_id,
            "role": role,
            "content": content,
            "sources": json.dumps(sources or [])
        }).execute()
        return result.data[0] if result.data else {}
    
    def get_chat_history(
        self,
        user_id: str,
        document_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get chat history"""
        result = self.client.table("learning_chat_history").select("*").eq(
            "user_id", user_id
        ).eq("document_id", document_id).order("created_at", desc=False).limit(limit).execute()
        return result.data or []
    
    # ============================================
    # ACHIEVEMENT OPERATIONS
    # ============================================
    
    def create_achievement(
        self,
        user_id: str,
        game_id: Optional[str],
        achievement_type: str,
        title: str,
        description: Optional[str] = None,
        value: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create an achievement"""
        result = self.client.table("achievements").insert({
            "user_id": user_id,
            "game_id": game_id,
            "type": achievement_type,
            "title": title,
            "description": description,
            "value": value
        }).execute()
        return result.data[0] if result.data else {}
    
    def get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's achievements"""
        result = self.client.table("achievements").select("*").eq(
            "user_id", user_id
        ).order("timestamp", desc=True).execute()
        return result.data or []
    
    # ============================================
    # USER PROGRESSION OPERATIONS
    # ============================================
    
    def get_user_progression(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user progression"""
        result = self.client.table("user_progression").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    
    def update_user_progression(
        self,
        user_id: str,
        level: Optional[int] = None,
        experience_points: Optional[int] = None,
        total_quests_completed: Optional[int] = None,
        total_quizzes_completed: Optional[int] = None,
        total_learning_hours: Optional[float] = None
    ) -> Dict[str, Any]:
        """Update user progression"""
        updates = {}
        if level is not None:
            updates["level"] = level
        if experience_points is not None:
            updates["experience_points"] = experience_points
        if total_quests_completed is not None:
            updates["total_quests_completed"] = total_quests_completed
        if total_quizzes_completed is not None:
            updates["total_quizzes_completed"] = total_quizzes_completed
        if total_learning_hours is not None:
            updates["total_learning_hours"] = total_learning_hours
        
        result = self.client.table("user_progression").upsert({
            "user_id": user_id,
            **updates,
            "updated_at": datetime.now().isoformat()
        }).execute()
        return result.data[0] if result.data else {}
    
    # ============================================
    # GAME CREATION LOG OPERATIONS
    # ============================================
    
    def log_game_creation(
        self,
        user_id: str,
        game_state_id: str,
        scenario_type: str = "standard",
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log game creation"""
        result = self.client.table("game_creation_log").insert({
            "user_id": user_id,
            "game_state_id": game_state_id,
            "scenario_type": scenario_type,
            "document_id": document_id
        }).execute()
        return result.data[0] if result.data else {}


# Global instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get or create global database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
