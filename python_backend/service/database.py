"""
Database Service Interface
Async-safe wrapper around the synchronous supabase-py client.

Every method offloads the blocking Supabase HTTP call to the default
asyncio thread executor via ``asyncio.to_thread``. This prevents the
FastAPI event loop from stalling when the request volume is high
(target: 50k concurrent users behind N gunicorn workers).
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import uuid

from supabase import create_client, Client

from configs.config import config


class DatabaseService:
    """Async-safe Supabase service. All public methods are coroutines."""

    def __init__(self) -> None:
        self.client: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_SERVICE_ROLE_KEY,
        )

    # ------------------------------------------------------------------
    # USER OPERATIONS
    # ------------------------------------------------------------------
    async def create_user(
        self,
        email: str,
        password_hash: str,
        name: str,
        profession: Optional[str] = None,
        age: Optional[int] = None,
        avatar_url: Optional[str] = None,
        bio: Optional[str] = None,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("users").insert({
                "email": email,
                "password_hash": password_hash,
                "name": name,
                "profession": profession,
                "age": age,
                "avatar_url": avatar_url,
                "bio": bio,
                "is_active": True,
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = self.client.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = self.client.table("users").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("users").update(updates).eq("id", user_id).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # GAME STATE OPERATIONS
    # ------------------------------------------------------------------
    async def create_game_state(
        self,
        user_id: str,
        case_id: str,
        state: Dict[str, Any],
        is_demo: bool = False,
        scenario_type: str = "standard",
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        game_id = str(uuid.uuid4())

        def _do() -> Dict[str, Any]:
            result = self.client.table("game_states").insert({
                "id": game_id,
                "user_id": user_id,
                "case_id": case_id,
                "state": state,
                "is_demo": is_demo,
                "scenario_type": scenario_type,
                "document_id": document_id,
                "is_active": True,
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_game_state(self, game_id: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = self.client.table("game_states").select("*").eq("id", game_id).execute()
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def get_user_game_states(
        self,
        user_id: str,
        limit: int = 10,
        is_active: Optional[bool] = None,
        is_demo: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            query = self.client.table("game_states").select("*").eq("user_id", user_id)
            if is_active is not None:
                query = query.eq("is_active", is_active)
            if is_demo is not None:
                query = query.eq("is_demo", is_demo)
            result = query.order("updated_at", desc=True).limit(limit).execute()
            return result.data or []
        return await asyncio.to_thread(_do)

    async def update_game_state(self, game_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        updates = {**updates, "updated_at": datetime.now().isoformat()}

        def _do() -> Dict[str, Any]:
            result = self.client.table("game_states").update(updates).eq("id", game_id).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def delete_game_state(self, game_id: str) -> bool:
        def _do() -> bool:
            result = self.client.table("game_states").delete().eq("id", game_id).execute()
            return len(result.data) > 0
        return await asyncio.to_thread(_do)

    async def delete_demo_game_states_older_than(self, cutoff_iso: str) -> int:
        """Delete demo rows with updated_at strictly before cutoff_iso."""
        def _do() -> int:
            sel = (
                self.client.table("game_states")
                .select("id")
                .eq("is_demo", True)
                .lt("updated_at", cutoff_iso)
                .execute()
            )
            ids = [row["id"] for row in (sel.data or [])]
            if not ids:
                return 0
            self.client.table("game_states").delete().in_("id", ids).execute()
            return len(ids)
        return await asyncio.to_thread(_do)

    async def complete_game_state(self, game_id: str) -> Dict[str, Any]:
        return await self.update_game_state(game_id, {
            "completed_at": datetime.now().isoformat(),
            "is_active": False,
        })

    # ------------------------------------------------------------------
    # GAME CHECKPOINT OPERATIONS
    # ------------------------------------------------------------------
    async def create_checkpoint(
        self,
        user_id: str,
        game_state_id: str,
        checkpoint_id: str,
        checkpoint_name: str,
        state: Dict[str, Any],
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("game_checkpoints").insert({
                "user_id": user_id,
                "game_state_id": game_state_id,
                "checkpoint_id": checkpoint_id,
                "checkpoint_name": checkpoint_name,
                "state": state,
                "description": description,
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_checkpoints(self, game_state_id: str) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            result = (
                self.client.table("game_checkpoints")
                .select("*")
                .eq("game_state_id", game_state_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # GAME STATISTICS OPERATIONS
    # ------------------------------------------------------------------
    async def get_game_statistics(self, user_id: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = self.client.table("game_statistics").select("*").eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def update_game_statistics(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("game_statistics").upsert({
                "user_id": user_id,
                **updates,
                "updated_at": datetime.now().isoformat(),
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # USER PERFORMANCE OPERATIONS
    # ------------------------------------------------------------------
    async def create_user_performance(
        self,
        user_id: str,
        game_id: str,
        clinical_state_id: str,
        score: float,
        analysis: str,
        strengths: List[str],
        weaknesses: List[str],
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("user_performance").insert({
                "user_id": user_id,
                "game_id": game_id,
                "clinical_state_id": clinical_state_id,
                "score": score,
                "analysis": analysis,
                "strengths": json.dumps(strengths),
                "weaknesses": json.dumps(weaknesses),
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_user_performance(
        self, user_id: str, game_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            query = self.client.table("user_performance").select("*").eq("user_id", user_id)
            if game_id:
                query = query.eq("game_id", game_id)
            result = query.order("timestamp", desc=True).execute()
            return result.data or []
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # QUIZ OPERATIONS
    # ------------------------------------------------------------------
    async def create_quiz(
        self,
        user_id: str,
        title: str,
        questions: List[Dict[str, Any]],
        quiz_type: str,
        time_limit: int,
        total_questions: int,
        source: str = "ai_knowledge",
        document_id: Optional[str] = None,
        difficulty: str = "intermediate",
    ) -> Dict[str, Any]:
        quiz_id = str(uuid.uuid4())

        def _do() -> Dict[str, Any]:
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
                "difficulty": difficulty,
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_quiz(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = self.client.table("quizzes").select("*").eq("id", quiz_id).execute()
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def get_user_quizzes(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            result = (
                self.client.table("quizzes")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        return await asyncio.to_thread(_do)

    async def create_quiz_result(
        self,
        user_id: str,
        quiz_id: str,
        answers: Dict[str, Any],
        scores: Dict[str, float],
        total_score: float,
        time_spent: int,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("quiz_results").insert({
                "user_id": user_id,
                "quiz_id": quiz_id,
                "answers": json.dumps(answers),
                "scores": json.dumps(scores),
                "score": int(total_score),
                "total_score": total_score,
                "time_spent": time_spent,
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_quiz_results(
        self, user_id: str, quiz_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            query = (
                self.client.table("quiz_results")
                .select("*, quizzes(*)")
                .eq("user_id", user_id)
            )
            if quiz_id:
                query = query.eq("quiz_id", quiz_id)
            result = query.order("completed_at", desc=True).limit(limit).execute()
            return result.data or []
        return await asyncio.to_thread(_do)

    async def get_quiz_statistics(self, user_id: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = self.client.table("quiz_statistics").select("*").eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # DOCUMENT OPERATIONS
    # ------------------------------------------------------------------
    async def create_document(
        self,
        user_id: str,
        name: str,
        file_name: str,
        file_type: str,
        file_size: int,
        content: Optional[str] = None,
        pinecone_index_name: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        s3_key: Optional[str] = None,
        document_id: Optional[str] = None,
        content_hash: Optional[str] = None,
        ingest_version: int = 1,
    ) -> Dict[str, Any]:
        """Create a document record. Pass document_id to preserve idempotent client IDs."""
        if expires_at is None:
            expires_at = datetime.now() + timedelta(hours=2)
        if isinstance(expires_at, (int, float)):
            expires_at = datetime.fromtimestamp(expires_at)
        if not document_id:
            document_id = str(uuid.uuid4())

        row: Dict[str, Any] = {
            "id": document_id,
            "user_id": user_id,
            "name": name,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "content": content[:10000] if content else None,
            "pinecone_index_name": pinecone_index_name,
            "pinecone_index_expires_at": (
                expires_at.isoformat() if isinstance(expires_at, datetime) else expires_at
            ),
            "s3_key": s3_key,
            "processed": False,
            "processing_status": (
                f"pending_v{ingest_version}_h{content_hash[:16]}"
                if content_hash
                else "pending"
            ),
            "uploaded_at": datetime.now().isoformat(),
        }

        def _do() -> Dict[str, Any]:
            result = self.client.table("documents").insert(row).execute()
            return result.data[0] if result.data else {"id": document_id}
        return await asyncio.to_thread(_do)

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = self.client.table("documents").select("*").eq("id", document_id).execute()
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def get_document_by_file_name(
        self, file_name: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            query = self.client.table("documents").select("*").eq("file_name", file_name)
            if user_id:
                query = query.eq("user_id", user_id)
            result = query.order("uploaded_at", desc=True).limit(1).execute()
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def get_user_documents(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            result = (
                self.client.table("documents")
                .select("*")
                .eq("user_id", user_id)
                .order("uploaded_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        return await asyncio.to_thread(_do)

    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("documents").update(updates).eq("id", document_id).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def mark_document_processed(
        self,
        document_id: str,
        chunk_count: int,
        pinecone_index_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self.update_document(document_id, {
            "processed": True,
            "processing_status": "completed",
            "chunk_count": chunk_count,
            "pinecone_index_name": pinecone_index_name,
            "processed_at": datetime.now().isoformat(),
        })

    async def replace_document_chunks(
        self, document_id: str, rows: List[Dict[str, Any]]
    ) -> None:
        """Batched replace of document_chunks for one document."""
        if not rows:
            return

        def _do() -> None:
            self.client.table("document_chunks").delete().eq("document_id", document_id).execute()
            for i in range(0, len(rows), 80):
                batch = rows[i : i + 80]
                self.client.table("document_chunks").insert(batch).execute()
        await asyncio.to_thread(_do)

    async def get_document_chunks_adjacent(
        self,
        document_id: str,
        chunk_index: int,
        before: int = 1,
        after: int = 1,
    ) -> List[Dict[str, Any]]:
        """Fetch persisted chunks [chunk_index - before, chunk_index + after]."""
        lo = max(0, chunk_index - before)
        hi = chunk_index + after

        def _do() -> List[Dict[str, Any]]:
            result = (
                self.client.table("document_chunks")
                .select("chunk_index, content, metadata")
                .eq("document_id", document_id)
                .gte("chunk_index", lo)
                .lte("chunk_index", hi)
                .order("chunk_index", desc=False)
                .execute()
            )
            return result.data or []
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # LEARNING CHAT OPERATIONS
    # ------------------------------------------------------------------
    async def create_chat_message(
        self,
        user_id: str,
        document_id: str,
        role: str,
        content: str,
        sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("learning_chat_history").insert({
                "user_id": user_id,
                "document_id": document_id,
                "role": role,
                "content": content,
                "sources": json.dumps(sources or []),
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_chat_history(
        self, user_id: str, document_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            result = (
                self.client.table("learning_chat_history")
                .select("*")
                .eq("user_id", user_id)
                .eq("document_id", document_id)
                .order("created_at", desc=False)
                .limit(limit)
                .execute()
            )
            return result.data or []
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # ACHIEVEMENT OPERATIONS
    # ------------------------------------------------------------------
    async def create_achievement(
        self,
        user_id: str,
        game_id: Optional[str],
        achievement_type: str,
        title: str,
        description: Optional[str] = None,
        value: Optional[float] = None,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("achievements").insert({
                "user_id": user_id,
                "game_id": game_id,
                "type": achievement_type,
                "title": title,
                "description": description,
                "value": value,
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            result = (
                self.client.table("achievements")
                .select("*")
                .eq("user_id", user_id)
                .order("timestamp", desc=True)
                .execute()
            )
            return result.data or []
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # USER PROGRESSION OPERATIONS
    # ------------------------------------------------------------------
    async def get_user_progression(self, user_id: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = self.client.table("user_progression").select("*").eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def update_user_progression(
        self,
        user_id: str,
        level: Optional[int] = None,
        experience_points: Optional[int] = None,
        total_quests_completed: Optional[int] = None,
        total_quizzes_completed: Optional[int] = None,
        total_learning_hours: Optional[float] = None,
    ) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
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
        payload = {
            "user_id": user_id,
            **updates,
            "updated_at": datetime.now().isoformat(),
        }

        def _do() -> Dict[str, Any]:
            result = self.client.table("user_progression").upsert(payload).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def add_experience_points(
        self,
        user_id: str,
        xp_amount: int,
        total_quests_delta: int = 0,
        total_quizzes_delta: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """Add XP and update counters. Recalculates level."""
        current = await self.get_user_progression(user_id)
        if not current:
            seed = {
                "user_id": user_id,
                "level": 1,
                "experience_points": 0,
                "total_quests_completed": 0,
                "total_quizzes_completed": 0,
                "updated_at": datetime.now().isoformat(),
            }
            await asyncio.to_thread(
                lambda: self.client.table("user_progression").upsert(seed).execute()
            )
            current = await self.get_user_progression(user_id)
        if not current:
            return None

        cur_xp = int(current.get("experience_points") or 0)
        cur_quests = int(current.get("total_quests_completed") or 0)
        cur_quizzes = int(current.get("total_quizzes_completed") or 0)

        new_xp = cur_xp + xp_amount
        new_level = (new_xp // 1000) + 1
        new_quests = cur_quests + total_quests_delta
        new_quizzes = cur_quizzes + total_quizzes_delta

        return await self.update_user_progression(
            user_id=user_id,
            level=new_level,
            experience_points=new_xp,
            total_quests_completed=new_quests,
            total_quizzes_completed=new_quizzes,
        )

    # ------------------------------------------------------------------
    # GAME CREATION LOG OPERATIONS
    # ------------------------------------------------------------------
    async def log_game_creation(
        self,
        user_id: str,
        game_state_id: str,
        scenario_type: str = "standard",
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("game_creation_log").insert({
                "user_id": user_id,
                "game_state_id": game_state_id,
                "scenario_type": scenario_type,
                "document_id": document_id,
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # CHAT HISTORY OPERATIONS
    # ------------------------------------------------------------------
    async def create_game_master_chat_message(
        self,
        user_id: str,
        game_id: str,
        session_id: str,
        role: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        parent_message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("game_master_chat_history").insert({
                "user_id": user_id,
                "game_id": game_id,
                "session_id": session_id,
                "role": role,
                "message": message,
                "message_metadata": metadata or {},
                "parent_message_id": parent_message_id,
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_game_master_chat_history(
        self,
        user_id: str,
        game_id: str,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            query = (
                self.client.table("game_master_chat_history")
                .select("*")
                .eq("user_id", user_id)
                .eq("game_id", game_id)
            )
            if session_id:
                query = query.eq("session_id", session_id)
            result = query.order("created_at", desc=False).limit(limit).execute()
            return result.data or []
        return await asyncio.to_thread(_do)

    async def create_npc_chat_message(
        self,
        user_id: str,
        game_id: str,
        npc_id: str,
        session_id: str,
        role: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        parent_message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("npc_chat_history").insert({
                "user_id": user_id,
                "game_id": game_id,
                "npc_id": npc_id,
                "session_id": session_id,
                "role": role,
                "message": message,
                "message_metadata": metadata or {},
                "parent_message_id": parent_message_id,
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_npc_chat_history(
        self,
        user_id: str,
        game_id: str,
        npc_id: str,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            query = (
                self.client.table("npc_chat_history")
                .select("*")
                .eq("user_id", user_id)
                .eq("game_id", game_id)
                .eq("npc_id", npc_id)
            )
            if session_id:
                query = query.eq("session_id", session_id)
            result = query.order("created_at", desc=False).limit(limit).execute()
            return result.data or []
        return await asyncio.to_thread(_do)

    async def create_tutor_chat_message(
        self,
        user_id: str,
        document_id: str,
        session_id: str,
        role: str,
        message: str,
        sources: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("tutor_chat_history").insert({
                "user_id": user_id,
                "document_id": document_id,
                "session_id": session_id,
                "role": role,
                "message": message,
                "sources": sources or [],
                "message_metadata": metadata or {},
                "parent_message_id": parent_message_id,
            }).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_tutor_chat_history(
        self,
        user_id: str,
        document_id: str,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            query = (
                self.client.table("tutor_chat_history")
                .select("*")
                .eq("user_id", user_id)
                .eq("document_id", document_id)
            )
            if session_id:
                query = query.eq("session_id", session_id)
            result = query.order("created_at", desc=False).limit(limit).execute()
            return result.data or []
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # PREVIOUS CASES OPERATIONS
    # ------------------------------------------------------------------
    async def save_previous_case(
        self,
        game_id: str,
        case_state_id: str,
        case_number: int,
        scenario_summary: str,
        diagnosis: Optional[str],
        question_summary: str,
        difficulty_level: str,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = self.client.table("game_previous_cases").upsert(
                {
                    "game_id": game_id,
                    "case_state_id": case_state_id,
                    "case_number": case_number,
                    "scenario_summary": scenario_summary[:200],
                    "diagnosis": diagnosis,
                    "question_summary": question_summary[:200],
                    "difficulty_level": difficulty_level,
                },
                on_conflict="game_id,case_state_id",
            ).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_previous_cases(self, game_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            result = (
                self.client.table("game_previous_cases")
                .select("*")
                .eq("game_id", game_id)
                .order("case_number", desc=False)
                .limit(limit)
                .execute()
            )
            return result.data or []
        return await asyncio.to_thread(_do)

    # ------------------------------------------------------------------
    # LEARNING: CURRICULUM, STUDY PLAN, ENROLLMENT
    # ------------------------------------------------------------------
    async def get_curriculum(self, curriculum_id: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = (
                self.client.table("curricula")
                .select("*")
                .eq("id", curriculum_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def get_curriculum_by_user_document(
        self, user_id: str, document_id: str
    ) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = (
                self.client.table("curricula")
                .select("*")
                .eq("user_id", user_id)
                .eq("document_id", document_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def upsert_curriculum(
        self,
        user_id: str,
        document_id: str,
        title: str,
        description: str,
        difficulty_level: str,
        modules: List[Dict[str, Any]],
        is_completed: bool = False,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "title": title,
            "description": description,
            "difficulty_level": difficulty_level,
            "modules": modules,
            "is_completed": is_completed,
            "updated_at": datetime.now().isoformat(),
        }
        existing = await self.get_curriculum_by_user_document(user_id, document_id)

        def _do() -> Dict[str, Any]:
            if existing:
                result = (
                    self.client.table("curricula")
                    .update(payload)
                    .eq("id", existing["id"])
                    .execute()
                )
            else:
                payload["user_id"] = user_id
                payload["document_id"] = document_id
                result = self.client.table("curricula").insert(payload).execute()
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def create_study_plan_row(
        self,
        user_id: str,
        curriculum_id: str,
        start_date: str,
        target_end_date: str,
        daily_schedule: List[Dict[str, Any]],
        pace_preference: str = "balanced",
        progress: float = 0.0,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = (
                self.client.table("study_plans")
                .insert({
                    "user_id": user_id,
                    "curriculum_id": curriculum_id,
                    "start_date": start_date,
                    "target_end_date": target_end_date,
                    "daily_schedule": daily_schedule,
                    "pace_preference": pace_preference,
                    "current_progress_percentage": progress,
                })
                .execute()
            )
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_study_plan(self, study_plan_id: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = (
                self.client.table("study_plans")
                .select("*")
                .eq("id", study_plan_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def get_study_plan_by_user_curriculum(
        self, user_id: str, curriculum_id: str
    ) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = (
                self.client.table("study_plans")
                .select("*")
                .eq("user_id", user_id)
                .eq("curriculum_id", curriculum_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def update_study_plan_schedule(
        self, study_plan_id: str, daily_schedule: List[Dict[str, Any]], progress: float
    ) -> Dict[str, Any]:
        payload = {
            "daily_schedule": daily_schedule,
            "current_progress_percentage": progress,
            "updated_at": datetime.now().isoformat(),
        }

        def _do() -> Dict[str, Any]:
            result = (
                self.client.table("study_plans")
                .update(payload)
                .eq("id", study_plan_id)
                .execute()
            )
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def create_user_enrollment_row(
        self,
        user_id: str,
        curriculum_id: str,
        study_plan_id: str,
        document_id: str,
    ) -> Dict[str, Any]:
        def _do() -> Dict[str, Any]:
            result = (
                self.client.table("user_enrollments")
                .insert({
                    "user_id": user_id,
                    "curriculum_id": curriculum_id,
                    "study_plan_id": study_plan_id,
                    "document_id": document_id,
                    "last_accessed": datetime.now().isoformat(),
                })
                .execute()
            )
            return result.data[0] if result.data else {}
        return await asyncio.to_thread(_do)

    async def get_user_enrollment(self, enrollment_id: str) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = (
                self.client.table("user_enrollments")
                .select("*")
                .eq("id", enrollment_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def get_enrollment_by_user_document(
        self, user_id: str, document_id: str
    ) -> Optional[Dict[str, Any]]:
        def _do() -> Optional[Dict[str, Any]]:
            result = (
                self.client.table("user_enrollments")
                .select("*")
                .eq("user_id", user_id)
                .eq("document_id", document_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        return await asyncio.to_thread(_do)

    async def list_user_enrollments(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List enrollments enriched with curriculum + document metadata.

        Bulk-fetches curricula and documents with two extra round-trips instead of
        N per row to keep this fast under load.
        """
        def _fetch_rows() -> List[Dict[str, Any]]:
            result = (
                self.client.table("user_enrollments")
                .select("*")
                .eq("user_id", user_id)
                .order("last_accessed", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []

        rows = await asyncio.to_thread(_fetch_rows)
        if not rows:
            return []

        curriculum_ids = list({r["curriculum_id"] for r in rows if r.get("curriculum_id")})
        document_ids = list({r["document_id"] for r in rows if r.get("document_id")})

        def _bulk() -> Dict[str, Dict[str, Any]]:
            cur_map: Dict[str, Dict[str, Any]] = {}
            doc_map: Dict[str, Dict[str, Any]] = {}
            if curriculum_ids:
                cur = (
                    self.client.table("curricula")
                    .select("id, title, difficulty_level, description")
                    .in_("id", curriculum_ids)
                    .execute()
                )
                for c in cur.data or []:
                    cur_map[c["id"]] = c
            if document_ids:
                doc = (
                    self.client.table("documents")
                    .select("id, file_name, name")
                    .in_("id", document_ids)
                    .execute()
                )
                for d in doc.data or []:
                    doc_map[d["id"]] = d
            return {"curricula": cur_map, "documents": doc_map}

        meta = await asyncio.to_thread(_bulk)
        cur_map = meta["curricula"]
        doc_map = meta["documents"]

        for r in rows:
            c = cur_map.get(r.get("curriculum_id", ""))
            if c:
                r["curriculum_title"] = c.get("title", "Learning path")
                r["difficulty_level"] = c.get("difficulty_level")
                r["curriculum_description"] = c.get("description", "")
            else:
                r["curriculum_title"] = "Learning path"
            d = doc_map.get(r.get("document_id", ""))
            if d:
                r["file_name"] = d.get("file_name") or d.get("name", "")
        return rows

    async def touch_enrollment(self, enrollment_id: str) -> None:
        def _do() -> None:
            self.client.table("user_enrollments").update(
                {"last_accessed": datetime.now().isoformat()}
            ).eq("id", enrollment_id).execute()
        await asyncio.to_thread(_do)

    async def mark_study_plan_task_completed(
        self, study_plan_id: str, task_id: str
    ) -> bool:
        """Mark a daily task as completed inside a study plan's schedule."""
        sp = await self.get_study_plan(study_plan_id)
        if not sp:
            return False
        schedule = sp.get("daily_schedule") or []
        if isinstance(schedule, str):
            schedule = json.loads(schedule)
        found = False
        for task in schedule:
            if task.get("task_id") == task_id:
                task["is_completed"] = True
                task["actual_completion_date"] = datetime.now().isoformat()
                found = True
                break
        if not found:
            return False
        completed = sum(1 for t in schedule if t.get("is_completed"))
        progress = (completed / len(schedule) * 100) if schedule else 0
        payload = {
            "daily_schedule": schedule,
            "current_progress_percentage": round(progress, 1),
            "updated_at": datetime.now().isoformat(),
        }

        def _do() -> None:
            self.client.table("study_plans").update(payload).eq("id", study_plan_id).execute()
        await asyncio.to_thread(_do)
        return True


# Global instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get or create the global async-safe database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
